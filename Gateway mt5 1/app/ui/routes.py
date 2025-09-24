"""
UI-Routen für MT5 Flask Gateway
Web-Interface für Dashboard, Konfiguration, Logs und Lizenzierung
"""

import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.security import require_api_key
from app.services.licensing import get_license_manager
from app.services.settings import get_settings_manager
from app.services.logging import get_logging_service
from app.mt5 import get_mt5_client
from app.mt5.account import get_account_manager

# UI Blueprint erstellen
ui = Blueprint('ui', __name__)
logger = logging.getLogger(__name__)

@ui.route('/')
def index():
    """Hauptdashboard"""
    return render_template('dashboard/index.html')

@ui.route('/config')
@login_required
def config():
    """Konfigurationsseite"""
    return render_template('config/index.html')

@ui.route('/n8n')
@login_required
def n8n():
    """n8n Integration Seite"""
    return render_template('n8n/index.html')

@ui.route('/logs')
@login_required
def logs():
    """Logs-Seite"""
    return render_template('logs/index.html')

@ui.route('/license')
@login_required
def license():
    """Lizenz-Seite"""
    return render_template('license/index.html')

# API-Endpunkte für UI
@ui.route('/api/v1/config')
@require_api_key
def get_config():
    """Gibt aktuelle Konfiguration zurück"""
    try:
        settings_manager = get_settings_manager()
        if not settings_manager:
            return jsonify({'error': 'Settings Manager nicht verfügbar'}), 503
        
        settings = settings_manager.get_settings()
        
        return jsonify({
            'mt5': {
                'server': settings.mt5_server,
                'login': settings.mt5_login,
                'password': settings.mt5_password,
                'path': settings.mt5_path
            },
            'trading': {
                'default_risk_percent': settings.default_risk_percent,
                'max_concurrent_orders': settings.max_concurrent_orders,
                'min_lot_size': settings.min_lot_size,
                'max_lot_size': settings.max_lot_size
            },
            'api': {
                'public_key': settings.api_public_key,
                'secret_key': settings.api_secret_key,
                'allowed_ips': ','.join(settings.allowed_ips),
                'rate_limit': settings.api_rate_limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Konfiguration: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/config/mt5', methods=['POST'])
@require_api_key
def save_mt5_config():
    """Speichert MT5-Konfiguration"""
    try:
        data = request.get_json()
        settings_manager = get_settings_manager()
        if not settings_manager:
            return jsonify({'error': 'Settings Manager nicht verfügbar'}), 503
        
        success = settings_manager.update_settings(
            mt5_server=data.get('server', ''),
            mt5_login=data.get('login', ''),
            mt5_password=data.get('password', ''),
            mt5_path=data.get('path', '')
        )
        
        if success:
            return jsonify({'message': 'MT5-Konfiguration gespeichert'}), 200
        else:
            return jsonify({'error': 'Fehler beim Speichern'}), 500
            
    except Exception as e:
        logger.error(f"Fehler beim Speichern der MT5-Konfiguration: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/config/trading', methods=['POST'])
@require_api_key
def save_trading_config():
    """Speichert Trading-Konfiguration"""
    try:
        data = request.get_json()
        settings_manager = get_settings_manager()
        if not settings_manager:
            return jsonify({'error': 'Settings Manager nicht verfügbar'}), 503
        
        success = settings_manager.update_settings(
            default_risk_percent=float(data.get('default_risk_percent', 1.0)),
            max_concurrent_orders=int(data.get('max_concurrent_orders', 10)),
            min_lot_size=float(data.get('min_lot_size', 0.01)),
            max_lot_size=float(data.get('max_lot_size', 100.0))
        )
        
        if success:
            return jsonify({'message': 'Trading-Konfiguration gespeichert'}), 200
        else:
            return jsonify({'error': 'Fehler beim Speichern'}), 500
            
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Trading-Konfiguration: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/config/api', methods=['POST'])
@require_api_key
def save_api_config():
    """Speichert API-Konfiguration"""
    try:
        data = request.get_json()
        settings_manager = get_settings_manager()
        if not settings_manager:
            return jsonify({'error': 'Settings Manager nicht verfügbar'}), 503
        
        success = settings_manager.update_settings(
            api_public_key=data.get('public_key', ''),
            api_secret_key=data.get('secret_key', ''),
            allowed_ips=data.get('allowed_ips', '').split(','),
            api_rate_limit=int(data.get('rate_limit', 60))
        )
        
        if success:
            return jsonify({'message': 'API-Konfiguration gespeichert'}), 200
        else:
            return jsonify({'error': 'Fehler beim Speichern'}), 500
            
    except Exception as e:
        logger.error(f"Fehler beim Speichern der API-Konfiguration: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/config/api/generate', methods=['POST'])
@require_api_key
def generate_api_keys():
    """Generiert neue API-Keys"""
    try:
        import secrets
        import string
        
        # Öffentlichen Key generieren
        public_key = 'pub_' + ''.join(secrets.choices(string.ascii_letters + string.digits, k=32))
        
        # Geheimen Key generieren
        secret_key = 'sec_' + ''.join(secrets.choices(string.ascii_letters + string.digits, k=64))
        
        return jsonify({
            'public_key': public_key,
            'secret_key': secret_key
        }), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Generieren der API-Keys: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/mt5/test', methods=['POST'])
@require_api_key
def test_mt5_connection():
    """Testet MT5-Verbindung"""
    try:
        data = request.get_json()
        mt5_client = get_mt5_client()
        if not mt5_client:
            return jsonify({'error': 'MT5 Client nicht verfügbar'}), 503
        
        # Temporäre Konfiguration setzen
        mt5_client.connection_info.server = data.get('server', '')
        mt5_client.connection_info.login = int(data.get('login', 0))
        mt5_client.connection_info.password = data.get('password', '')
        mt5_client.connection_info.path = data.get('path', '')
        
        # Verbindung testen
        success = mt5_client.initialize()
        
        if success:
            mt5_client.shutdown()  # Test-Verbindung beenden
            return jsonify({'message': 'MT5-Verbindung erfolgreich'}), 200
        else:
            return jsonify({'error': 'MT5-Verbindung fehlgeschlagen'}), 400
            
    except Exception as e:
        logger.error(f"Fehler beim Testen der MT5-Verbindung: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/license/status')
@require_api_key
def get_license_status():
    """Gibt Lizenz-Status zurück"""
    try:
        license_manager = get_license_manager()
        if not license_manager:
            return jsonify({'error': 'License Manager nicht verfügbar'}), 503
        
        status = license_manager.get_license_status()
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Lizenz-Status: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/license/activate', methods=['POST'])
@require_api_key
def activate_license():
    """Aktiviert Lizenz"""
    try:
        data = request.get_json()
        license_key = data.get('license_key', '')
        
        if not license_key:
            return jsonify({'error': 'Lizenz-Key erforderlich'}), 400
        
        license_manager = get_license_manager()
        if not license_manager:
            return jsonify({'error': 'License Manager nicht verfügbar'}), 503
        
        # Lizenz verifizieren
        success = license_manager.verify_license()
        
        if success:
            return jsonify({'message': 'Lizenz erfolgreich aktiviert'}), 200
        else:
            return jsonify({'error': 'Lizenz-Aktivierung fehlgeschlagen'}), 400
            
    except Exception as e:
        logger.error(f"Fehler bei der Lizenz-Aktivierung: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/logs/files')
@require_api_key
def get_log_files():
    """Gibt verfügbare Log-Dateien zurück"""
    try:
        logging_service = get_logging_service()
        if not logging_service:
            return jsonify({'error': 'Logging Service nicht verfügbar'}), 503
        
        log_files = logging_service.get_log_files()
        return jsonify(log_files), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Log-Dateien: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/logs/view/<filename>')
@require_api_key
def view_log_file(filename):
    """Zeigt Log-Datei-Inhalt"""
    try:
        logging_service = get_logging_service()
        if not logging_service:
            return jsonify({'error': 'Logging Service nicht verfügbar'}), 503
        
        lines = logging_service.read_log_file(filename, 1000)  # Letzte 1000 Zeilen
        content = ''.join(lines)
        
        # Einfache Statistiken
        stats = {
            'total_lines': len(lines),
            'error_lines': len([line for line in lines if 'ERROR' in line]),
            'warning_lines': len([line for line in lines if 'WARNING' in line]),
            'info_lines': len([line for line in lines if 'INFO' in line])
        }
        
        return jsonify({
            'content': content,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen der Log-Datei: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/logs/download/<filename>')
@require_api_key
def download_log_file(filename):
    """Lädt Log-Datei herunter"""
    try:
        from flask import send_file
        import os
        
        log_dir = "logs"
        filepath = os.path.join(log_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Datei nicht gefunden'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Fehler beim Download der Log-Datei: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/logs/search')
@require_api_key
def search_logs():
    """Durchsucht Logs"""
    try:
        query = request.args.get('query', '')
        log_type = request.args.get('log_type', 'all')
        log_level = request.args.get('log_level', 'all')
        
        logging_service = get_logging_service()
        if not logging_service:
            return jsonify({'error': 'Logging Service nicht verfügbar'}), 503
        
        results = logging_service.search_logs(query, log_type)
        
        # Nach Level filtern
        if log_level != 'all':
            results = [r for r in results if r['log_entry']['level'] == log_level]
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Fehler bei der Log-Suche: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@ui.route('/api/v1/logs/stats')
@require_api_key
def get_log_stats():
    """Gibt Log-Statistiken zurück"""
    try:
        logging_service = get_logging_service()
        if not logging_service:
            return jsonify({'error': 'Logging Service nicht verfügbar'}), 503
        
        stats = logging_service.get_log_statistics()
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Log-Statistiken: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500
