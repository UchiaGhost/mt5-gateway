"""
MetaTrader 5 Client für MT5 Flask Gateway
Verbindungsmanagement, Heartbeat und Symbol-Pflege
"""

import MetaTrader5 as mt5
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from app.config import Config

@dataclass
class MT5ConnectionInfo:
    """MT5 Verbindungsinformationen"""
    server: str
    login: int
    password: str
    path: str
    timeout: int = 10000

@dataclass
class SymbolInfo:
    """Symbol-Informationen"""
    name: str
    digits: int
    point: float
    tick_value: float
    contract_size: float
    margin_required: float
    spread: int
    is_trade_allowed: bool

class MT5Client:
    """MetaTrader 5 Client"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection_info = MT5ConnectionInfo(
            server=config.MT5_SERVER,
            login=int(config.MT5_LOGIN),
            password=config.MT5_PASSWORD,
            path=config.MT5_PATH
        )
        self.is_connected = False
        self.last_heartbeat = None
        self.symbols_cache: Dict[str, SymbolInfo] = {}
        self.account_info = None
        
    def initialize(self) -> bool:
        """Initialisiert MT5-Verbindung"""
        try:
            # MT5 initialisieren
            if not mt5.initialize(path=self.connection_info.path, 
                                 timeout=self.connection_info.timeout):
                self.logger.error(f"MT5 Initialisierung fehlgeschlagen: {mt5.last_error()}")
                return False
            
            # Login
            if not mt5.login(login=self.connection_info.login,
                            password=self.connection_info.password,
                            server=self.connection_info.server):
                self.logger.error(f"MT5 Login fehlgeschlagen: {mt5.last_error()}")
                return False
            
            # Verbindung testen
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("Keine Kontoinformationen erhalten")
                return False
            
            self.is_connected = True
            self.last_heartbeat = datetime.utcnow()
            self.account_info = account_info
            
            self.logger.info(f"MT5 erfolgreich verbunden: {account_info.login} @ {account_info.server}")
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 Initialisierung fehlgeschlagen: {e}")
            return False
    
    def shutdown(self) -> None:
        """Beendet MT5-Verbindung"""
        try:
            mt5.shutdown()
            self.is_connected = False
            self.logger.info("MT5-Verbindung beendet")
        except Exception as e:
            self.logger.error(f"Fehler beim Beenden der MT5-Verbindung: {e}")
    
    def heartbeat(self) -> bool:
        """Prüft Verbindungsstatus"""
        try:
            if not self.is_connected:
                return False
            
            # Account-Info abrufen
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.warning("MT5 Heartbeat fehlgeschlagen - Verbindung verloren")
                self.is_connected = False
                return False
            
            self.last_heartbeat = datetime.utcnow()
            self.account_info = account_info
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 Heartbeat Fehler: {e}")
            self.is_connected = False
            return False
    
    def reconnect(self) -> bool:
        """Versucht Verbindung wiederherzustellen"""
        self.logger.info("Versuche MT5-Verbindung wiederherzustellen...")
        
        # Kurz warten
        time.sleep(2)
        
        # Neu initialisieren
        return self.initialize()
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Ruft Symbol-Informationen ab"""
        try:
            # Cache prüfen
            if symbol in self.symbols_cache:
                cached_info = self.symbols_cache[symbol]
                # Cache für 5 Minuten gültig
                if datetime.utcnow() - cached_info.get('timestamp', datetime.min) < timedelta(minutes=5):
                    return cached_info['info']
            
            # Symbol-Info von MT5 abrufen
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.error(f"Symbol {symbol} nicht gefunden")
                return None
            
            # Symbol-Info erstellen
            info = SymbolInfo(
                name=symbol,
                digits=symbol_info.digits,
                point=symbol_info.point,
                tick_value=symbol_info.trade_tick_value,
                contract_size=symbol_info.trade_contract_size,
                margin_required=symbol_info.margin_required,
                spread=symbol_info.spread,
                is_trade_allowed=symbol_info.trade_mode & mt5.SYMBOL_TRADE_MODE_FULL
            )
            
            # Cache aktualisieren
            self.symbols_cache[symbol] = {
                'info': info,
                'timestamp': datetime.utcnow()
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Symbol-Info für {symbol}: {e}")
            return None
    
    def subscribe_symbol(self, symbol: str) -> bool:
        """Abonniert Symbol für Preis-Updates"""
        try:
            if not mt5.symbol_select(symbol, True):
                self.logger.error(f"Symbol {symbol} konnte nicht abonniert werden")
                return False
            
            self.logger.info(f"Symbol {symbol} erfolgreich abonniert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abonnieren von {symbol}: {e}")
            return False
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Ruft Kontoinformationen ab"""
        try:
            if not self.heartbeat():
                return None
            
            account = self.account_info
            if account is None:
                return None
            
            return {
                'login': account.login,
                'server': account.server,
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'free_margin': account.margin_free,
                'margin_level': account.margin_level,
                'currency': account.currency,
                'leverage': account.leverage,
                'profit': account.profit,
                'company': account.company,
                'name': account.name,
                'server_time': datetime.fromtimestamp(account.server_time)
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Kontoinformationen: {e}")
            return None
    
    def get_server_time(self) -> Optional[datetime]:
        """Ruft Server-Zeit ab"""
        try:
            time_info = mt5.symbol_info_tick("EURUSD")  # Beliebiges Symbol für Zeit
            if time_info is None:
                return None
            
            return datetime.fromtimestamp(time_info.time)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Server-Zeit: {e}")
            return None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Gibt Verbindungsstatus zurück"""
        return {
            'is_connected': self.is_connected,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'server': self.connection_info.server,
            'login': self.connection_info.login,
            'account_info': self.get_account_info()
        }

# Globale MT5 Client Instanz
mt5_client: Optional[MT5Client] = None

def init_mt5_client(config: Config) -> None:
    """Initialisiert den MT5 Client"""
    global mt5_client
    mt5_client = MT5Client(config)

def get_mt5_client() -> Optional[MT5Client]:
    """Gibt den MT5 Client zurück"""
    return mt5_client
