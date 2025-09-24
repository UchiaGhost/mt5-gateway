"""
Konfigurationsmodul für MT5 Flask Gateway
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Basis-Konfiguration"""
    SECRET_KEY: str
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int = 3600
    
    # API-Sicherheit
    API_PUBLIC_KEY: str
    API_SECRET_KEY: str
    ALLOWED_IPS: str = "127.0.0.1,::1"
    RATE_LIMIT_PER_MIN: int = 60
    
    # MT5-Konfiguration
    MT5_SERVER: str
    MT5_LOGIN: str
    MT5_PASSWORD: str
    MT5_PATH: str
    
    # Lizenzierung
    LICENSE_SERVER_URL: str
    LICENSE_KEY: str = ""
    
    # Telemetrie
    TELEMETRY_OPTOUT: bool = False
    
    # UI
    UI_ADMIN_PASSWORD: str
    
    # Server
    PORT: int = 8080
    BIND: str = "0.0.0.0"
    
    # Datenbank
    DATABASE_URL: str
    REDIS_URL: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/mt5_gateway.log"
    MAX_LOG_SIZE: int = 10485760  # 10MB
    BACKUP_COUNT: int = 5
    
    # Stripe
    STRIPE_PUBLIC_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Trading-Limits
    MAX_CONCURRENT_ORDERS: int = 10
    DEFAULT_RISK_PERCENT: float = 1.0
    MIN_LOT_SIZE: float = 0.01
    MAX_LOT_SIZE: float = 100.0
    LOT_STEP: float = 0.01
    STOP_LEVEL_PIPS: int = 5

class DevelopmentConfig(Config):
    """Entwicklungskonfiguration"""
    DEBUG = True
    TESTING = False
    
    def __init__(self):
        super().__init__(
            SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///mt5_gateway_dev.db'),
            API_PUBLIC_KEY=os.getenv('API_PUBLIC_KEY', 'dev_pub_key'),
            API_SECRET_KEY=os.getenv('API_SECRET_KEY', 'dev_sec_key'),
            MT5_SERVER=os.getenv('MT5_SERVER', 'Demo-Server'),
            MT5_LOGIN=os.getenv('MT5_LOGIN', '123456'),
            MT5_PASSWORD=os.getenv('MT5_PASSWORD', 'password'),
            MT5_PATH=os.getenv('MT5_PATH', 'C:\\Program Files\\MetaTrader 5\\terminal64.exe'),
            LICENSE_SERVER_URL=os.getenv('LICENSE_SERVER_URL', 'https://license.example.com'),
            LICENSE_KEY=os.getenv('LICENSE_KEY', ''),
            TELEMETRY_OPTOUT=os.getenv('TELEMETRY_OPTOUT', 'true').lower() == 'true',
            UI_ADMIN_PASSWORD=os.getenv('UI_ADMIN_PASSWORD', 'admin123'),
            PORT=int(os.getenv('PORT', 8080)),
            BIND=os.getenv('BIND', '127.0.0.1'),
            DATABASE_URL=os.getenv('DATABASE_URL', 'sqlite:///mt5_gateway_dev.db'),
            REDIS_URL=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'DEBUG'),
            LOG_FILE=os.getenv('LOG_FILE', 'logs/mt5_gateway_dev.log'),
            MAX_LOG_SIZE=int(os.getenv('MAX_LOG_SIZE', 10485760)),
            BACKUP_COUNT=int(os.getenv('BACKUP_COUNT', 5)),
            STRIPE_PUBLIC_KEY=os.getenv('STRIPE_PUBLIC_KEY', ''),
            STRIPE_SECRET_KEY=os.getenv('STRIPE_SECRET_KEY', ''),
            STRIPE_WEBHOOK_SECRET=os.getenv('STRIPE_WEBHOOK_SECRET', ''),
            MAX_CONCURRENT_ORDERS=int(os.getenv('MAX_CONCURRENT_ORDERS', 10)),
            DEFAULT_RISK_PERCENT=float(os.getenv('DEFAULT_RISK_PERCENT', 1.0)),
            MIN_LOT_SIZE=float(os.getenv('MIN_LOT_SIZE', 0.01)),
            MAX_LOT_SIZE=float(os.getenv('MAX_LOT_SIZE', 100.0)),
            LOT_STEP=float(os.getenv('LOT_STEP', 0.01)),
            STOP_LEVEL_PIPS=int(os.getenv('STOP_LEVEL_PIPS', 5))
        )

class ProductionConfig(Config):
    """Produktionskonfiguration"""
    DEBUG = False
    TESTING = False
    
    def __init__(self):
        super().__init__(
            SECRET_KEY=os.getenv('SECRET_KEY'),
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
            API_PUBLIC_KEY=os.getenv('API_PUBLIC_KEY'),
            API_SECRET_KEY=os.getenv('API_SECRET_KEY'),
            ALLOWED_IPS=os.getenv('ALLOWED_IPS', '127.0.0.1,::1'),
            RATE_LIMIT_PER_MIN=int(os.getenv('RATE_LIMIT_PER_MIN', 60)),
            MT5_SERVER=os.getenv('MT5_SERVER'),
            MT5_LOGIN=os.getenv('MT5_LOGIN'),
            MT5_PASSWORD=os.getenv('MT5_PASSWORD'),
            MT5_PATH=os.getenv('MT5_PATH'),
            LICENSE_SERVER_URL=os.getenv('LICENSE_SERVER_URL'),
            LICENSE_KEY=os.getenv('LICENSE_KEY', ''),
            TELEMETRY_OPTOUT=os.getenv('TELEMETRY_OPTOUT', 'false').lower() == 'true',
            UI_ADMIN_PASSWORD=os.getenv('UI_ADMIN_PASSWORD'),
            PORT=int(os.getenv('PORT', 8080)),
            BIND=os.getenv('BIND', '0.0.0.0'),
            DATABASE_URL=os.getenv('DATABASE_URL'),
            REDIS_URL=os.getenv('REDIS_URL'),
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO'),
            LOG_FILE=os.getenv('LOG_FILE', 'logs/mt5_gateway.log'),
            MAX_LOG_SIZE=int(os.getenv('MAX_LOG_SIZE', 10485760)),
            BACKUP_COUNT=int(os.getenv('BACKUP_COUNT', 5)),
            STRIPE_PUBLIC_KEY=os.getenv('STRIPE_PUBLIC_KEY', ''),
            STRIPE_SECRET_KEY=os.getenv('STRIPE_SECRET_KEY', ''),
            STRIPE_WEBHOOK_SECRET=os.getenv('STRIPE_WEBHOOK_SECRET', ''),
            MAX_CONCURRENT_ORDERS=int(os.getenv('MAX_CONCURRENT_ORDERS', 10)),
            DEFAULT_RISK_PERCENT=float(os.getenv('DEFAULT_RISK_PERCENT', 1.0)),
            MIN_LOT_SIZE=float(os.getenv('MIN_LOT_SIZE', 0.01)),
            MAX_LOT_SIZE=float(os.getenv('MAX_LOT_SIZE', 100.0)),
            LOT_STEP=float(os.getenv('LOT_STEP', 0.01)),
            STOP_LEVEL_PIPS=int(os.getenv('STOP_LEVEL_PIPS', 5))
        )

class TestingConfig(Config):
    """Testkonfiguration"""
    TESTING = True
    DEBUG = True
    
    def __init__(self):
        super().__init__(
            SECRET_KEY='test-secret-key',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            API_PUBLIC_KEY='test_pub_key',
            API_SECRET_KEY='test_sec_key',
            MT5_SERVER='Test-Server',
            MT5_LOGIN='123456',
            MT5_PASSWORD='password',
            MT5_PATH='C:\\Program Files\\MetaTrader 5\\terminal64.exe',
            LICENSE_SERVER_URL='https://test-license.example.com',
            LICENSE_KEY='test_license_key',
            TELEMETRY_OPTOUT=True,
            UI_ADMIN_PASSWORD='test123',
            PORT=8081,
            BIND='127.0.0.1',
            DATABASE_URL='sqlite:///:memory:',
            REDIS_URL='redis://localhost:6379/1',
            LOG_LEVEL='DEBUG',
            LOG_FILE='logs/mt5_gateway_test.log',
            MAX_LOG_SIZE=1048576,  # 1MB
            BACKUP_COUNT=2,
            STRIPE_PUBLIC_KEY='pk_test_xxxxx',
            STRIPE_SECRET_KEY='sk_test_xxxxx',
            STRIPE_WEBHOOK_SECRET='whsec_test_xxxxx',
            MAX_CONCURRENT_ORDERS=5,
            DEFAULT_RISK_PERCENT=0.5,
            MIN_LOT_SIZE=0.01,
            MAX_LOT_SIZE=10.0,
            LOT_STEP=0.01,
            STOP_LEVEL_PIPS=3
        )

# Konfigurationsmapping
config_map: Dict[str, type] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """Gibt die entsprechende Konfiguration zurück"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_class = config_map.get(config_name, DevelopmentConfig)
    return config_class()
