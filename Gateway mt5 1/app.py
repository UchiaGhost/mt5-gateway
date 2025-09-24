#!/usr/bin/env python3
"""
MT5 Flask Gateway - Hauptanwendung
Produktionstaugliches MetaTrader 5 Gateway für n8n Integration
"""

import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

# Projekt-Pfad hinzufügen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_config
from app.security import init_security
from app.mt5 import init_mt5_client
from app.mt5.trading import init_trading_engine
from app.mt5.account import init_account_manager
from app.services.licensing import init_license_manager
from app.services.telemetry import init_telemetry_service
from app.services.settings import init_settings_manager
from app.services.logging import init_logging_service
from app.services.stripe import init_stripe_service
from app.api.routes import api
from app.api.errors import register_error_handlers
from app.ui.routes import ui

def create_app(config_name=None):
    """Erstellt und konfiguriert die Flask-Anwendung"""
    
    # Konfiguration laden
    config = get_config(config_name)
    
    # Flask-App erstellen
    app = Flask(__name__)
    app.config.from_object(config)
    
    # CORS aktivieren
    CORS(app, origins=config.ALLOWED_IPS.split(','))
    
    # Services initialisieren
    init_logging_service(config)
    init_security(config, None)  # Redis optional
    init_settings_manager(config)
    init_license_manager(config)
    init_telemetry_service(config)
    init_stripe_service(config)
    
    # MT5-Services initialisieren
    init_mt5_client(config)
    init_trading_engine(config, None)  # MT5 Client wird später verknüpft
    init_account_manager(None)  # MT5 Client wird später verknüpft
    
    # Error Handler registrieren
    register_error_handlers(app)
    
    # Blueprints registrieren
    app.register_blueprint(api)
    app.register_blueprint(ui)
    
    # MT5-Verbindung initialisieren (falls konfiguriert)
    try:
        from app.mt5 import get_mt5_client
        mt5_client = get_mt5_client()
        if mt5_client and config.MT5_SERVER and config.MT5_LOGIN:
            app.logger.info("Initialisiere MT5-Verbindung...")
            if mt5_client.initialize():
                app.logger.info("MT5-Verbindung erfolgreich hergestellt")
            else:
                app.logger.warning("MT5-Verbindung fehlgeschlagen - Mock-Modus aktiv")
    except Exception as e:
        app.logger.error(f"Fehler bei MT5-Initialisierung: {e}")
    
    return app

def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MT5 Flask Gateway')
    parser.add_argument('--config', default=None, help='Konfigurationsname')
    parser.add_argument('--host', default='0.0.0.0', help='Host-Adresse')
    parser.add_argument('--port', type=int, default=8080, help='Port')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus')
    parser.add_argument('--init-db', action='store_true', help='Datenbank initialisieren')
    parser.add_argument('--create-admin', action='store_true', help='Admin-Benutzer erstellen')
    
    args = parser.parse_args()
    
    # App erstellen
    app = create_app(args.config)
    
    # Datenbank initialisieren
    if args.init_db:
        with app.app_context():
            from app import db
            db.create_all()
            print("Datenbank initialisiert.")
            return
    
    # Admin-Benutzer erstellen
    if args.create_admin:
        with app.app_context():
            from app.models import User
            from app import db
            
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@mt5gateway.com',
                    is_active=True
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("Admin-Benutzer erstellt: admin / admin123")
            else:
                print("Admin-Benutzer existiert bereits.")
            return
    
    # Server starten
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )

if __name__ == '__main__':
    main()
