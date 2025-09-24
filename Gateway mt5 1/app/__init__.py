"""
MT5 Flask Gateway - Hauptanwendung
Produktionstaugliches MetaTrader 5 Gateway für n8n Integration
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import redis
from typing import Optional, Dict, Any

# Umgebungsvariablen laden
load_dotenv()

# Flask App initialisieren
app = Flask(__name__)

# Konfiguration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mt5_gateway.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# Erweiterungen initialisieren
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu besuchen.'
csrf = CSRFProtect(app)

# Redis für Rate Limiting und Caching
redis_client: Optional[redis.Redis] = None
try:
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()  # Verbindung testen
except redis.ConnectionError:
    app.logger.warning("Redis nicht verfügbar, verwende In-Memory-Cache")

# Logging konfigurieren
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper())
log_file = os.getenv('LOG_FILE', 'logs/mt5_gateway.log')

# Log-Verzeichnis erstellen
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Logging-Handler konfigurieren
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    log_file, 
    maxBytes=int(os.getenv('MAX_LOG_SIZE', 10485760)),  # 10MB
    backupCount=int(os.getenv('BACKUP_COUNT', 5))
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(log_level)

app.logger.addHandler(file_handler)
app.logger.setLevel(log_level)
app.logger.info('MT5 Flask Gateway gestartet')

# User Model für Admin-Authentifizierung
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    return User.query.get(int(user_id))

# App-Kontext für CLI und Tests
@app.shell_context_processor
def make_shell_context() -> Dict[str, Any]:
    return {
        'db': db, 
        'User': User,
        'app': app
    }

# Globale Template-Variablen
@app.context_processor
def inject_globals() -> Dict[str, Any]:
    return {
        'app_name': 'MT5 Flask Gateway',
        'version': '1.0.0',
        'current_year': datetime.now().year,
        'user': current_user
    }

# Fehlerbehandlung
@app.errorhandler(404)
def not_found_error(error) -> tuple:
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error) -> tuple:
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Hauptroute
@app.route('/')
def index() -> str:
    """Hauptdashboard"""
    return render_template('dashboard/index.html')

# Health Check für Monitoring
@app.route('/health')
def health_check() -> Dict[str, Any]:
    """System Health Check"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'database': 'connected' if db.engine.execute('SELECT 1').scalar() else 'disconnected',
        'redis': 'connected' if redis_client and redis_client.ping() else 'disconnected'
    }
    
    status_code = 200 if health_status['database'] == 'connected' else 503
    return jsonify(health_status), status_code

# CLI-Interface
def create_admin_user() -> None:
    """Erstellt einen Admin-Benutzer für die UI"""
    admin_password = os.getenv('UI_ADMIN_PASSWORD', 'admin123')
    
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@mt5gateway.com',
            is_active=True
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info('Admin-Benutzer erstellt')

def init_app() -> None:
    """Initialisiert die Anwendung"""
    with app.app_context():
        db.create_all()
        create_admin_user()
        app.logger.info('Datenbank und Admin-Benutzer initialisiert')

if __name__ == '__main__':
    init_app()
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('BIND', '0.0.0.0')
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(host=host, port=port, debug=debug)
