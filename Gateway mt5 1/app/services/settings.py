"""
Settings-Service für MT5 Flask Gateway
Persistente App-Einstellungen und Konfigurationsverwaltung
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from app.config import Config

@dataclass
class AppSettings:
    """App-Einstellungen"""
    mt5_server: str
    mt5_login: str
    mt5_password: str
    mt5_path: str
    default_risk_percent: float
    min_lot_size: float
    max_lot_size: float
    lot_step: float
    stop_level_pips: int
    max_concurrent_orders: int
    api_rate_limit: int
    allowed_ips: List[str]
    ui_theme: str
    ui_language: str
    auto_reconnect: bool
    heartbeat_interval: int
    log_level: str
    telemetry_enabled: bool
    license_key: str
    created_at: datetime
    updated_at: datetime

class SettingsManager:
    """Settings-Manager"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.settings_file = "app_settings.json"
        self.settings: Optional[AppSettings] = None
        
        # Standard-Einstellungen
        self.default_settings = AppSettings(
            mt5_server=config.MT5_SERVER,
            mt5_login=config.MT5_LOGIN,
            mt5_password=config.MT5_PASSWORD,
            mt5_path=config.MT5_PATH,
            default_risk_percent=config.DEFAULT_RISK_PERCENT,
            min_lot_size=config.MIN_LOT_SIZE,
            max_lot_size=config.MAX_LOT_SIZE,
            lot_step=config.LOT_STEP,
            stop_level_pips=config.STOP_LEVEL_PIPS,
            max_concurrent_orders=config.MAX_CONCURRENT_ORDERS,
            api_rate_limit=config.RATE_LIMIT_PER_MIN,
            allowed_ips=config.ALLOWED_IPS.split(','),
            ui_theme="light",
            ui_language="de",
            auto_reconnect=True,
            heartbeat_interval=30,
            log_level=config.LOG_LEVEL,
            telemetry_enabled=not config.TELEMETRY_OPTOUT,
            license_key=config.LICENSE_KEY,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Einstellungen laden
        self.load_settings()
    
    def load_settings(self) -> None:
        """Lädt Einstellungen aus Datei"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Datetime-Objekte konvertieren
                data['created_at'] = datetime.fromisoformat(data['created_at'])
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                self.settings = AppSettings(**data)
                self.logger.info("Einstellungen geladen")
            else:
                self.settings = self.default_settings
                self.save_settings()
                self.logger.info("Standard-Einstellungen erstellt")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            self.settings = self.default_settings
    
    def save_settings(self) -> bool:
        """Speichert Einstellungen in Datei"""
        try:
            if not self.settings:
                return False
            
            # Aktualisierungszeit setzen
            self.settings.updated_at = datetime.utcnow()
            
            # In Dictionary konvertieren
            data = asdict(self.settings)
            
            # Datetime-Objekte konvertieren
            data['created_at'] = self.settings.created_at.isoformat()
            data['updated_at'] = self.settings.updated_at.isoformat()
            
            # Speichern
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Einstellungen gespeichert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
            return False
    
    def get_settings(self) -> AppSettings:
        """Gibt aktuelle Einstellungen zurück"""
        if not self.settings:
            self.load_settings()
        return self.settings
    
    def update_settings(self, **kwargs) -> bool:
        """Aktualisiert Einstellungen"""
        try:
            if not self.settings:
                self.load_settings()
            
            # Erlaubte Felder prüfen
            allowed_fields = {
                'mt5_server', 'mt5_login', 'mt5_password', 'mt5_path',
                'default_risk_percent', 'min_lot_size', 'max_lot_size', 'lot_step',
                'stop_level_pips', 'max_concurrent_orders', 'api_rate_limit',
                'allowed_ips', 'ui_theme', 'ui_language', 'auto_reconnect',
                'heartbeat_interval', 'log_level', 'telemetry_enabled', 'license_key'
            }
            
            # Einstellungen aktualisieren
            for key, value in kwargs.items():
                if key in allowed_fields and hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            
            # Speichern
            return self.save_settings()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Einstellungen: {e}")
            return False
    
    def reset_settings(self) -> bool:
        """Setzt Einstellungen auf Standard zurück"""
        try:
            self.settings = self.default_settings
            return self.save_settings()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Zurücksetzen der Einstellungen: {e}")
            return False
    
    def get_setting(self, key: str) -> Any:
        """Gibt einzelne Einstellung zurück"""
        if not self.settings:
            self.load_settings()
        
        return getattr(self.settings, key, None)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Setzt einzelne Einstellung"""
        try:
            if not self.settings:
                self.load_settings()
            
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                return self.save_settings()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der Einstellung {key}: {e}")
            return False
    
    def export_settings(self) -> Dict[str, Any]:
        """Exportiert Einstellungen"""
        if not self.settings:
            self.load_settings()
        
        data = asdict(self.settings)
        data['created_at'] = self.settings.created_at.isoformat()
        data['updated_at'] = self.settings.updated_at.isoformat()
        
        return data
    
    def import_settings(self, data: Dict[str, Any]) -> bool:
        """Importiert Einstellungen"""
        try:
            # Datetime-Objekte konvertieren
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'updated_at' in data:
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            # Einstellungen erstellen
            self.settings = AppSettings(**data)
            
            # Speichern
            return self.save_settings()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Importieren der Einstellungen: {e}")
            return False
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """Gibt Einstellungs-Zusammenfassung zurück"""
        if not self.settings:
            self.load_settings()
        
        return {
            "mt5_configured": bool(self.settings.mt5_server and self.settings.mt5_login),
            "risk_settings": {
                "default_risk_percent": self.settings.default_risk_percent,
                "min_lot_size": self.settings.min_lot_size,
                "max_lot_size": self.settings.max_lot_size,
                "lot_step": self.settings.lot_step
            },
            "trading_limits": {
                "max_concurrent_orders": self.settings.max_concurrent_orders,
                "stop_level_pips": self.settings.stop_level_pips
            },
            "ui_settings": {
                "theme": self.settings.ui_theme,
                "language": self.settings.ui_language
            },
            "system_settings": {
                "auto_reconnect": self.settings.auto_reconnect,
                "heartbeat_interval": self.settings.heartbeat_interval,
                "log_level": self.settings.log_level,
                "telemetry_enabled": self.settings.telemetry_enabled
            },
            "last_updated": self.settings.updated_at.isoformat()
        }

# Globale Settings-Manager Instanz
settings_manager: Optional[SettingsManager] = None

def init_settings_manager(config: Config) -> None:
    """Initialisiert den Settings-Manager"""
    global settings_manager
    settings_manager = SettingsManager(config)

def get_settings_manager() -> Optional[SettingsManager]:
    """Gibt den Settings-Manager zurück"""
    return settings_manager
