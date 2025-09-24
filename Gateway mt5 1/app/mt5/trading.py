"""
MetaTrader 5 Trading Engine für MT5 Flask Gateway
Order-Management, Risikomanagement und Positionsverwaltung
"""

import MetaTrader5 as mt5
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from app.config import Config
from app.mt5 import MT5Client, SymbolInfo

class OrderType(Enum):
    """Order-Typen"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    """Order-Seiten"""
    BUY = "buy"
    SELL = "sell"

@dataclass
class RiskConfig:
    """Risikokonfiguration"""
    percent: float
    fixed_amount: Optional[float] = None
    max_risk_per_trade: float = 2.0

@dataclass
class StopLossConfig:
    """Stop-Loss Konfiguration"""
    pips: Optional[int] = None
    price: Optional[float] = None
    atr_multiplier: Optional[float] = None

@dataclass
class TakeProfitConfig:
    """Take-Profit Konfiguration"""
    pips: Optional[int] = None
    price: Optional[float] = None
    risk_reward_ratio: Optional[float] = None

@dataclass
class TradingSignal:
    """Trading-Signal"""
    strategy: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    risk: RiskConfig
    sl: StopLossConfig
    tp: TakeProfitConfig
    price: Optional[float] = None
    comment: str = ""
    idempotency_key: str = ""
    magic_number: int = 0

@dataclass
class OrderResult:
    """Order-Ergebnis"""
    success: bool
    order_id: Optional[int] = None
    position_id: Optional[int] = None
    executed_price: Optional[float] = None
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    lot_size: Optional[float] = None
    error_message: Optional[str] = None
    server_time: Optional[datetime] = None

class TradingEngine:
    """MetaTrader 5 Trading Engine"""
    
    def __init__(self, config: Config, mt5_client: MT5Client):
        self.config = config
        self.mt5_client = mt5_client
        self.logger = logging.getLogger(__name__)
        self.idempotency_cache: Dict[str, datetime] = {}
        self.idempotency_ttl = 3600  # 1 Stunde
        
    def calculate_lot_size(self, symbol: str, risk_config: RiskConfig, 
                          sl_points: float) -> Optional[float]:
        """Berechnet Lot-Größe basierend auf Risiko"""
        try:
            # Symbol-Info abrufen
            symbol_info = self.mt5_client.get_symbol_info(symbol)
            if not symbol_info:
                return None
            
            # Kontoinformationen abrufen
            account_info = self.mt5_client.get_account_info()
            if not account_info:
                return None
            
            balance = account_info['balance']
            
            # Risikobetrag berechnen
            if risk_config.fixed_amount:
                risk_amount = risk_config.fixed_amount
            else:
                risk_amount = balance * (risk_config.percent / 100)
            
            # Maximales Risiko pro Trade begrenzen
            max_risk = balance * (risk_config.max_risk_per_trade / 100)
            risk_amount = min(risk_amount, max_risk)
            
            # Verlust pro Lot berechnen
            point_value = symbol_info.tick_value * symbol_info.contract_size
            loss_per_lot = sl_points * symbol_info.point * point_value
            
            if loss_per_lot <= 0:
                self.logger.error(f"Ungültiger Verlust pro Lot für {symbol}")
                return None
            
            # Lot-Größe berechnen
            lot_size = risk_amount / loss_per_lot
            
            # Lot-Größe begrenzen
            lot_size = max(lot_size, self.config.MIN_LOT_SIZE)
            lot_size = min(lot_size, self.config.MAX_LOT_SIZE)
            
            # Lot-Step berücksichtigen
            lot_size = round(lot_size / self.config.LOT_STEP) * self.config.LOT_STEP
            
            return lot_size
            
        except Exception as e:
            self.logger.error(f"Fehler bei Lot-Berechnung für {symbol}: {e}")
            return None
    
    def calculate_sl_tp_prices(self, symbol: str, side: OrderSide, 
                              entry_price: float, sl_config: StopLossConfig,
                              tp_config: TakeProfitConfig) -> Tuple[Optional[float], Optional[float]]:
        """Berechnet SL/TP Preise"""
        try:
            symbol_info = self.mt5_client.get_symbol_info(symbol)
            if not symbol_info:
                return None, None
            
            sl_price = None
            tp_price = None
            
            # Stop-Loss berechnen
            if sl_config.pips:
                pip_value = sl_config.pips * symbol_info.point
                if side == OrderSide.BUY:
                    sl_price = entry_price - pip_value
                else:
                    sl_price = entry_price + pip_value
            elif sl_config.price:
                sl_price = sl_config.price
            
            # Take-Profit berechnen
            if tp_config.pips:
                pip_value = tp_config.pips * symbol_info.point
                if side == OrderSide.BUY:
                    tp_price = entry_price + pip_value
                else:
                    tp_price = entry_price - pip_value
            elif tp_config.price:
                tp_price = tp_config.price
            elif tp_config.risk_reward_ratio and sl_price:
                risk = abs(entry_price - sl_price)
                reward = risk * tp_config.risk_reward_ratio
                if side == OrderSide.BUY:
                    tp_price = entry_price + reward
                else:
                    tp_price = entry_price - reward
            
            # Mindestabstand prüfen
            min_distance = self.config.STOP_LEVEL_PIPS * symbol_info.point
            if sl_price and abs(entry_price - sl_price) < min_distance:
                if side == OrderSide.BUY:
                    sl_price = entry_price - min_distance
                else:
                    sl_price = entry_price + min_distance
            
            if tp_price and abs(entry_price - tp_price) < min_distance:
                if side == OrderSide.BUY:
                    tp_price = entry_price + min_distance
                else:
                    tp_price = entry_price - min_distance
            
            return sl_price, tp_price
            
        except Exception as e:
            self.logger.error(f"Fehler bei SL/TP-Berechnung für {symbol}: {e}")
            return None, None
    
    def validate_idempotency(self, idempotency_key: str) -> bool:
        """Validiert Idempotency-Key"""
        if not idempotency_key:
            return True
        
        # Prüfen ob Key bereits verwendet wurde
        if idempotency_key in self.idempotency_cache:
            return False
        
        # Key zur Cache hinzufügen
        self.idempotency_cache[idempotency_key] = datetime.utcnow()
        
        # Alte Keys bereinigen
        cutoff = datetime.utcnow() - timedelta(seconds=self.idempotency_ttl)
        self.idempotency_cache = {
            k: v for k, v in self.idempotency_cache.items() 
            if v > cutoff
        }
        
        return True
    
    def execute_signal(self, signal: TradingSignal) -> OrderResult:
        """Führt Trading-Signal aus"""
        try:
            # Idempotency prüfen
            if not self.validate_idempotency(signal.idempotency_key):
                return OrderResult(
                    success=False,
                    error_message="Idempotency-Key bereits verwendet"
                )
            
            # Symbol abonnieren
            if not self.mt5_client.subscribe_symbol(signal.symbol):
                return OrderResult(
                    success=False,
                    error_message=f"Symbol {signal.symbol} nicht verfügbar"
                )
            
            # Symbol-Info abrufen
            symbol_info = self.mt5_client.get_symbol_info(signal.symbol)
            if not symbol_info:
                return OrderResult(
                    success=False,
                    error_message=f"Symbol-Info für {signal.symbol} nicht verfügbar"
                )
            
            # Aktueller Preis
            tick = mt5.symbol_info_tick(signal.symbol)
            if tick is None:
                return OrderResult(
                    success=False,
                    error_message=f"Aktueller Preis für {signal.symbol} nicht verfügbar"
                )
            
            current_price = tick.ask if signal.side == OrderSide.BUY else tick.bid
            
            # SL-Punkte berechnen
            sl_points = 0
            if signal.sl.pips:
                sl_points = signal.sl.pips
            elif signal.sl.price:
                sl_points = abs(current_price - signal.sl.price) / symbol_info.point
            
            # Lot-Größe berechnen
            lot_size = self.calculate_lot_size(signal.symbol, signal.risk, sl_points)
            if not lot_size:
                return OrderResult(
                    success=False,
                    error_message="Lot-Größe konnte nicht berechnet werden"
                )
            
            # SL/TP Preise berechnen
            sl_price, tp_price = self.calculate_sl_tp_prices(
                signal.symbol, signal.side, current_price, signal.sl, signal.tp
            )
            
            # Order-Parameter erstellen
            order_type = mt5.ORDER_TYPE_BUY if signal.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": signal.symbol,
                "volume": lot_size,
                "type": order_type,
                "price": current_price,
                "sl": sl_price or 0.0,
                "tp": tp_price or 0.0,
                "deviation": 20,
                "magic": signal.magic_number,
                "comment": signal.comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Order senden
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return OrderResult(
                    success=False,
                    error_message=f"Order fehlgeschlagen: {result.comment}"
                )
            
            # Erfolgreiche Ausführung
            return OrderResult(
                success=True,
                order_id=result.order,
                position_id=result.position,
                executed_price=result.price,
                sl_price=sl_price,
                tp_price=tp_price,
                lot_size=lot_size,
                server_time=datetime.fromtimestamp(result.time)
            )
            
        except Exception as e:
            self.logger.error(f"Fehler bei Signal-Ausführung: {e}")
            return OrderResult(
                success=False,
                error_message=f"Interner Fehler: {str(e)}"
            )
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Ruft offene Positionen ab"""
        try:
            positions = mt5.positions_get(symbol=symbol)
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'buy' if pos.type == mt5.POSITION_TYPE_BUY else 'sell',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'comment': pos.comment,
                    'magic': pos.magic,
                    'time': datetime.fromtimestamp(pos.time)
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Positionen: {e}")
            return []
    
    def modify_position(self, ticket: int, sl: Optional[float] = None, 
                       tp: Optional[float] = None) -> bool:
        """Modifiziert Position"""
        try:
            # Position finden
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
            
            pos = position[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": sl or pos.sl,
                "tp": tp or pos.tp,
            }
            
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            self.logger.error(f"Fehler beim Modifizieren der Position {ticket}: {e}")
            return False
    
    def close_position(self, ticket: int, volume: Optional[float] = None) -> bool:
        """Schließt Position"""
        try:
            # Position finden
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
            
            pos = position[0]
            close_volume = volume or pos.volume
            
            # Gegenorder erstellen
            order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": close_volume,
                "type": order_type,
                "position": ticket,
                "deviation": 20,
                "magic": pos.magic,
                "comment": f"Close position {ticket}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            self.logger.error(f"Fehler beim Schließen der Position {ticket}: {e}")
            return False

# Globale Trading Engine Instanz
trading_engine: Optional[TradingEngine] = None

def init_trading_engine(config: Config, mt5_client: MT5Client) -> None:
    """Initialisiert die Trading Engine"""
    global trading_engine
    trading_engine = TradingEngine(config, mt5_client)

def get_trading_engine() -> Optional[TradingEngine]:
    """Gibt die Trading Engine zurück"""
    return trading_engine
