"""
Mock-Backend für MT5 Flask Gateway
Simuliert MT5-Funktionalität für Tests und Entwicklung
"""

import random
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from app.mt5 import SymbolInfo
from app.mt5.trading import OrderResult, TradingSignal, OrderSide, OrderType

@dataclass
class MockAccountInfo:
    """Mock Konto-Informationen"""
    login: int = 1234567
    server: str = "Mock-Server"
    balance: float = 10000.0
    equity: float = 10000.0
    margin: float = 0.0
    free_margin: float = 10000.0
    margin_level: float = 0.0
    currency: str = "USD"
    leverage: int = 100
    profit: float = 0.0
    company: str = "Mock Broker"
    name: str = "Mock Account"

@dataclass
class MockPosition:
    """Mock Position"""
    ticket: int
    symbol: str
    type: str
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    swap: float
    comment: str
    magic: int
    time: datetime

class MockMT5Client:
    """Mock MT5 Client für Tests"""
    
    def __init__(self):
        self.is_connected = True
        self.last_heartbeat = datetime.utcnow()
        self.account_info = MockAccountInfo()
        self.symbols_cache: Dict[str, SymbolInfo] = {}
        self.positions: List[MockPosition] = []
        self.order_counter = 1000000
        
        # Standard-Symbole initialisieren
        self._init_default_symbols()
    
    def _init_default_symbols(self):
        """Initialisiert Standard-Symbole"""
        symbols = [
            ("EURUSD", 5, 0.00001, 1.0, 100000, 0.0),
            ("GBPUSD", 5, 0.00001, 1.0, 100000, 0.0),
            ("USDJPY", 3, 0.001, 1.0, 100000, 0.0),
            ("AUDUSD", 5, 0.00001, 1.0, 100000, 0.0),
            ("USDCAD", 5, 0.00001, 1.0, 100000, 0.0),
        ]
        
        for symbol, digits, point, tick_value, contract_size, margin_required in symbols:
            self.symbols_cache[symbol] = SymbolInfo(
                name=symbol,
                digits=digits,
                point=point,
                tick_value=tick_value,
                contract_size=contract_size,
                margin_required=margin_required,
                spread=20,
                is_trade_allowed=True
            )
    
    def initialize(self) -> bool:
        """Mock Initialisierung"""
        return True
    
    def shutdown(self) -> None:
        """Mock Shutdown"""
        self.is_connected = False
    
    def heartbeat(self) -> bool:
        """Mock Heartbeat"""
        self.last_heartbeat = datetime.utcnow()
        return True
    
    def reconnect(self) -> bool:
        """Mock Reconnect"""
        self.is_connected = True
        return True
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Mock Symbol-Info"""
        return self.symbols_cache.get(symbol)
    
    def subscribe_symbol(self, symbol: str) -> bool:
        """Mock Symbol-Abonnement"""
        if symbol not in self.symbols_cache:
            # Symbol hinzufügen
            self.symbols_cache[symbol] = SymbolInfo(
                name=symbol,
                digits=5,
                point=0.00001,
                tick_value=1.0,
                contract_size=100000,
                margin_required=0.0,
                spread=20,
                is_trade_allowed=True
            )
        return True
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Mock Konto-Info"""
        return {
            'login': self.account_info.login,
            'server': self.account_info.server,
            'balance': self.account_info.balance,
            'equity': self.account_info.equity,
            'margin': self.account_info.margin,
            'free_margin': self.account_info.free_margin,
            'margin_level': self.account_info.margin_level,
            'currency': self.account_info.currency,
            'leverage': self.account_info.leverage,
            'profit': self.account_info.profit,
            'company': self.account_info.company,
            'name': self.account_info.name,
            'server_time': datetime.utcnow()
        }
    
    def get_server_time(self) -> Optional[datetime]:
        """Mock Server-Zeit"""
        return datetime.utcnow()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Mock Verbindungsstatus"""
        return {
            'is_connected': self.is_connected,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'server': self.account_info.server,
            'login': self.account_info.login,
            'account_info': self.get_account_info()
        }

class MockTradingEngine:
    """Mock Trading Engine für Tests"""
    
    def __init__(self, mock_client: MockMT5Client):
        self.mock_client = mock_client
        self.idempotency_cache: Dict[str, datetime] = {}
        self.idempotency_ttl = 3600
    
    def calculate_lot_size(self, symbol: str, risk_config, sl_points: float) -> Optional[float]:
        """Mock Lot-Berechnung"""
        symbol_info = self.mock_client.get_symbol_info(symbol)
        if not symbol_info:
            return None
        
        account_info = self.mock_client.get_account_info()
        if not account_info:
            return None
        
        balance = account_info['balance']
        risk_amount = balance * (risk_config.percent / 100)
        
        point_value = symbol_info.tick_value * symbol_info.contract_size
        loss_per_lot = sl_points * symbol_info.point * point_value
        
        if loss_per_lot <= 0:
            return None
        
        lot_size = risk_amount / loss_per_lot
        lot_size = max(lot_size, 0.01)  # Min Lot
        lot_size = min(lot_size, 100.0)  # Max Lot
        lot_size = round(lot_size / 0.01) * 0.01  # Lot Step
        
        return lot_size
    
    def calculate_sl_tp_prices(self, symbol: str, side: OrderSide, entry_price: float, 
                              sl_config, tp_config) -> tuple:
        """Mock SL/TP-Berechnung"""
        symbol_info = self.mock_client.get_symbol_info(symbol)
        if not symbol_info:
            return None, None
        
        sl_price = None
        tp_price = None
        
        if sl_config.pips:
            pip_value = sl_config.pips * symbol_info.point
            if side == OrderSide.BUY:
                sl_price = entry_price - pip_value
            else:
                sl_price = entry_price + pip_value
        
        if tp_config.pips:
            pip_value = tp_config.pips * symbol_info.point
            if side == OrderSide.BUY:
                tp_price = entry_price + pip_value
            else:
                tp_price = entry_price - pip_value
        
        return sl_price, tp_price
    
    def validate_idempotency(self, idempotency_key: str) -> bool:
        """Mock Idempotency-Validierung"""
        if not idempotency_key:
            return True
        
        if idempotency_key in self.idempotency_cache:
            return False
        
        self.idempotency_cache[idempotency_key] = datetime.utcnow()
        return True
    
    def execute_signal(self, signal: TradingSignal) -> OrderResult:
        """Mock Signal-Ausführung"""
        # Idempotency prüfen
        if not self.validate_idempotency(signal.idempotency_key):
            return OrderResult(
                success=False,
                error_message="Idempotency-Key bereits verwendet"
            )
        
        # Symbol-Info abrufen
        symbol_info = self.mock_client.get_symbol_info(signal.symbol)
        if not symbol_info:
            return OrderResult(
                success=False,
                error_message=f"Symbol {signal.symbol} nicht verfügbar"
            )
        
        # Mock-Preis generieren
        base_price = 1.1000 if signal.symbol == "EURUSD" else 1.2000
        current_price = base_price + random.uniform(-0.01, 0.01)
        
        # SL-Punkte berechnen
        sl_points = signal.sl.pips or 20
        
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
        
        # Mock-Order erstellen
        order_id = self.mock_client.order_counter
        self.mock_client.order_counter += 1
        
        # Mock-Position erstellen
        position = MockPosition(
            ticket=order_id,
            symbol=signal.symbol,
            type='buy' if signal.side == OrderSide.BUY else 'sell',
            volume=lot_size,
            price_open=current_price,
            price_current=current_price,
            sl=sl_price or 0.0,
            tp=tp_price or 0.0,
            profit=0.0,
            swap=0.0,
            comment=signal.comment,
            magic=signal.magic_number,
            time=datetime.utcnow()
        )
        
        self.mock_client.positions.append(position)
        
        return OrderResult(
            success=True,
            order_id=order_id,
            position_id=order_id,
            executed_price=current_price,
            sl_price=sl_price,
            tp_price=tp_price,
            lot_size=lot_size,
            server_time=datetime.utcnow()
        )
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Mock Positionen abrufen"""
        positions = self.mock_client.positions
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        
        result = []
        for pos in positions:
            result.append({
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': pos.type,
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'swap': pos.swap,
                'comment': pos.comment,
                'magic': pos.magic,
                'time': pos.time
            })
        
        return result
    
    def modify_position(self, ticket: int, sl: Optional[float] = None, 
                       tp: Optional[float] = None) -> bool:
        """Mock Position modifizieren"""
        for pos in self.mock_client.positions:
            if pos.ticket == ticket:
                if sl is not None:
                    pos.sl = sl
                if tp is not None:
                    pos.tp = tp
                return True
        return False
    
    def close_position(self, ticket: int, volume: Optional[float] = None) -> bool:
        """Mock Position schließen"""
        for i, pos in enumerate(self.mock_client.positions):
            if pos.ticket == ticket:
                if volume and volume < pos.volume:
                    pos.volume -= volume
                else:
                    del self.mock_client.positions[i]
                return True
        return False

# Mock-Instanzen für Tests
mock_mt5_client = MockMT5Client()
mock_trading_engine = MockTradingEngine(mock_mt5_client)

def get_mock_mt5_client() -> MockMT5Client:
    """Gibt Mock MT5 Client zurück"""
    return mock_mt5_client

def get_mock_trading_engine() -> MockTradingEngine:
    """Gibt Mock Trading Engine zurück"""
    return mock_trading_engine
