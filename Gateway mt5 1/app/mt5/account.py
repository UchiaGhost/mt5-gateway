"""
MetaTrader 5 Account Management für MT5 Flask Gateway
Kontoinformationen, Margin und Risikomanagement
"""

import MetaTrader5 as mt5
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from app.mt5 import MT5Client

@dataclass
class AccountSummary:
    """Konto-Zusammenfassung"""
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    currency: str
    leverage: int
    profit: float
    company: str
    name: str
    server_time: datetime

@dataclass
class MarginInfo:
    """Margin-Informationen"""
    symbol: str
    margin_required: float
    margin_mode: int
    margin_currency: str
    margin_rate: float

class AccountManager:
    """MetaTrader 5 Account Manager"""
    
    def __init__(self, mt5_client: MT5Client):
        self.mt5_client = mt5_client
        self.logger = logging.getLogger(__name__)
    
    def get_account_summary(self) -> Optional[AccountSummary]:
        """Ruft Konto-Zusammenfassung ab"""
        try:
            account_info = self.mt5_client.get_account_info()
            if not account_info:
                return None
            
            return AccountSummary(
                login=account_info['login'],
                server=account_info['server'],
                balance=account_info['balance'],
                equity=account_info['equity'],
                margin=account_info['margin'],
                free_margin=account_info['free_margin'],
                margin_level=account_info['margin_level'],
                currency=account_info['currency'],
                leverage=account_info['leverage'],
                profit=account_info['profit'],
                company=account_info['company'],
                name=account_info['name'],
                server_time=account_info['server_time']
            )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Konto-Zusammenfassung: {e}")
            return None
    
    def get_margin_info(self, symbol: str) -> Optional[MarginInfo]:
        """Ruft Margin-Informationen für Symbol ab"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return None
            
            return MarginInfo(
                symbol=symbol,
                margin_required=symbol_info.margin_required,
                margin_mode=symbol_info.margin_mode,
                margin_currency=symbol_info.margin_currency,
                margin_rate=symbol_info.margin_rate
            )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Margin-Info für {symbol}: {e}")
            return None
    
    def calculate_margin_required(self, symbol: str, volume: float, 
                                 price: float) -> Optional[float]:
        """Berechnet erforderliche Margin"""
        try:
            margin_info = self.get_margin_info(symbol)
            if not margin_info:
                return None
            
            # Margin basierend auf Margin-Modus berechnen
            if margin_info.margin_mode == mt5.SYMBOL_CALC_MODE_FOREX:
                # Forex: Margin = Contract Size * Volume / Leverage
                account_info = self.get_account_summary()
                if not account_info:
                    return None
                
                leverage = account_info.leverage
                contract_size = mt5.symbol_info(symbol).trade_contract_size
                margin = (contract_size * volume) / leverage
                
            elif margin_info.margin_mode == mt5.SYMBOL_CALC_MODE_FUTURES:
                # Futures: Margin = Contract Size * Volume * Margin Rate
                contract_size = mt5.symbol_info(symbol).trade_contract_size
                margin = contract_size * volume * margin_info.margin_rate
                
            else:
                # Andere Modi: Vereinfachte Berechnung
                margin = margin_info.margin_required * volume
            
            return margin
            
        except Exception as e:
            self.logger.error(f"Fehler bei Margin-Berechnung für {symbol}: {e}")
            return None
    
    def check_margin_sufficient(self, symbol: str, volume: float, 
                               price: float) -> bool:
        """Prüft ob ausreichend Margin verfügbar ist"""
        try:
            account_summary = self.get_account_summary()
            if not account_summary:
                return False
            
            required_margin = self.calculate_margin_required(symbol, volume, price)
            if required_margin is None:
                return False
            
            return account_summary.free_margin >= required_margin
            
        except Exception as e:
            self.logger.error(f"Fehler bei Margin-Prüfung für {symbol}: {e}")
            return False
    
    def get_risk_metrics(self) -> Optional[Dict[str, Any]]:
        """Ruft Risiko-Metriken ab"""
        try:
            account_summary = self.get_account_summary()
            if not account_summary:
                return None
            
            # Risiko-Metriken berechnen
            risk_metrics = {
                'balance': account_summary.balance,
                'equity': account_summary.equity,
                'margin': account_summary.margin,
                'free_margin': account_summary.free_margin,
                'margin_level': account_summary.margin_level,
                'profit': account_summary.profit,
                'profit_percent': (account_summary.profit / account_summary.balance * 100) if account_summary.balance > 0 else 0,
                'margin_used_percent': (account_summary.margin / account_summary.equity * 100) if account_summary.equity > 0 else 0,
                'currency': account_summary.currency,
                'leverage': account_summary.leverage,
                'server_time': account_summary.server_time
            }
            
            # Risiko-Warnungen
            warnings = []
            if account_summary.margin_level < 200:
                warnings.append("Margin Level unter 200%")
            if account_summary.margin_level < 100:
                warnings.append("Margin Call Risiko")
            if account_summary.free_margin < account_summary.balance * 0.1:
                warnings.append("Niedrige freie Margin")
            
            risk_metrics['warnings'] = warnings
            
            return risk_metrics
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Risiko-Metriken: {e}")
            return None
    
    def get_trading_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Ruft Trading-Historie ab"""
        try:
            from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            from_date = from_date.replace(day=from_date.day - days)
            
            deals = mt5.history_deals_get(from_date, datetime.now())
            if deals is None:
                return []
            
            history = []
            for deal in deals:
                history.append({
                    'ticket': deal.ticket,
                    'order': deal.order,
                    'symbol': deal.symbol,
                    'type': 'buy' if deal.type == mt5.DEAL_TYPE_BUY else 'sell',
                    'volume': deal.volume,
                    'price': deal.price,
                    'profit': deal.profit,
                    'swap': deal.swap,
                    'commission': deal.commission,
                    'comment': deal.comment,
                    'magic': deal.magic,
                    'time': datetime.fromtimestamp(deal.time)
                })
            
            return sorted(history, key=lambda x: x['time'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Trading-Historie: {e}")
            return []
    
    def get_order_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Ruft Order-Historie ab"""
        try:
            from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            from_date = from_date.replace(day=from_date.day - days)
            
            orders = mt5.history_orders_get(from_date, datetime.now())
            if orders is None:
                return []
            
            history = []
            for order in orders:
                history.append({
                    'ticket': order.ticket,
                    'symbol': order.symbol,
                    'type': 'buy' if order.type == mt5.ORDER_TYPE_BUY else 'sell',
                    'volume': order.volume,
                    'price_open': order.price_open,
                    'price_current': order.price_current,
                    'sl': order.sl,
                    'tp': order.tp,
                    'state': order.state,
                    'comment': order.comment,
                    'magic': order.magic,
                    'time_setup': datetime.fromtimestamp(order.time_setup),
                    'time_done': datetime.fromtimestamp(order.time_done) if order.time_done > 0 else None
                })
            
            return sorted(history, key=lambda x: x['time_setup'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Order-Historie: {e}")
            return []

# Globale Account Manager Instanz
account_manager: Optional[AccountManager] = None

def init_account_manager(mt5_client: MT5Client) -> None:
    """Initialisiert den Account Manager"""
    global account_manager
    account_manager = AccountManager(mt5_client)

def get_account_manager() -> Optional[AccountManager]:
    """Gibt den Account Manager zurück"""
    return account_manager
