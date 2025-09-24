"""
Sicherheitsmodul für MT5 Flask Gateway
Implementiert API-Key Authentifizierung, HMAC-Signaturen und Rate Limiting
"""

import hmac
import hashlib
import base64
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import wraps
from flask import request, jsonify, current_app, g
import redis
from app.config import Config

class SecurityError(Exception):
    """Sicherheitsbezogene Fehler"""
    pass

class AuthenticationError(SecurityError):
    """Authentifizierungsfehler"""
    pass

class AuthorizationError(SecurityError):
    """Autorisierungsfehler"""
    pass

class RateLimitError(SecurityError):
    """Rate-Limit-Fehler"""
    pass

class SecurityManager:
    """Zentraler Sicherheitsmanager"""
    
    def __init__(self, config: Config, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis_client = redis_client
        self.nonce_cache: Dict[str, datetime] = {}  # Fallback für Redis
        self.nonce_ttl = 300  # 5 Minuten
    
    def generate_signature(self, secret: str, method: str, path: str, 
                         body: str, timestamp: str, nonce: str) -> str:
        """Generiert HMAC-SHA256 Signatur"""
        message = f"{method.upper()}{path}{body}{timestamp}{nonce}".encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature(self, signature: str, secret: str, method: str, 
                        path: str, body: str, timestamp: str, nonce: str) -> bool:
        """Verifiziert HMAC-Signatur"""
        expected_signature = self.generate_signature(
            secret, method, path, body, timestamp, nonce
        )
        return hmac.compare_digest(signature, expected_signature)
    
    def validate_timestamp(self, timestamp: str, tolerance: int = 300) -> bool:
        """Validiert Zeitstempel (Replay-Schutz)"""
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            return abs(current_time - request_time) <= tolerance
        except (ValueError, TypeError):
            return False
    
    def validate_nonce(self, nonce: str) -> bool:
        """Validiert Nonce (Replay-Schutz)"""
        if len(nonce) < 16:
            return False
        
        # Redis-basierte Validierung
        if self.redis_client:
            try:
                key = f"nonce:{nonce}"
                if self.redis_client.exists(key):
                    return False
                self.redis_client.setex(key, self.nonce_ttl, "1")
                return True
            except redis.RedisError:
                pass
        
        # Fallback: In-Memory-Cache
        if nonce in self.nonce_cache:
            return False
        
        self.nonce_cache[nonce] = datetime.utcnow()
        
        # Cleanup alter Nonces
        cutoff = datetime.utcnow() - timedelta(seconds=self.nonce_ttl)
        self.nonce_cache = {
            k: v for k, v in self.nonce_cache.items() 
            if v > cutoff
        }
        
        return True
    
    def validate_ip(self, ip: str) -> bool:
        """Validiert IP-Adresse gegen Allowlist"""
        allowed_ips = self.config.ALLOWED_IPS.split(',')
        allowed_ips = [ip.strip() for ip in allowed_ips]
        
        # Spezielle IPs
        if '0.0.0.0' in allowed_ips or '*' in allowed_ips:
            return True
        
        return ip in allowed_ips
    
    def check_rate_limit(self, identifier: str, limit: int, window: int = 60) -> bool:
        """Prüft Rate Limit"""
        if not self.redis_client:
            return True  # Kein Rate Limiting ohne Redis
        
        try:
            key = f"rate_limit:{identifier}"
            current = self.redis_client.get(key)
            
            if current is None:
                self.redis_client.setex(key, window, 1)
                return True
            
            if int(current) >= limit:
                return False
            
            self.redis_client.incr(key)
            return True
            
        except redis.RedisError:
            return True  # Bei Redis-Fehlern Rate Limiting deaktivieren
    
    def authenticate_request(self) -> Tuple[bool, Optional[str]]:
        """Authentifiziert API-Request"""
        # Header prüfen
        api_key = request.headers.get('X-API-KEY')
        timestamp = request.headers.get('X-TS')
        nonce = request.headers.get('X-NONCE')
        signature = request.headers.get('X-SIGNATURE')
        
        if not all([api_key, timestamp, nonce, signature]):
            return False, "Fehlende Authentifizierungs-Header"
        
        # API-Key validieren
        if api_key != self.config.API_PUBLIC_KEY:
            return False, "Ungültiger API-Key"
        
        # Zeitstempel validieren
        if not self.validate_timestamp(timestamp):
            return False, "Ungültiger oder abgelaufener Zeitstempel"
        
        # Nonce validieren
        if not self.validate_nonce(nonce):
            return False, "Nonce bereits verwendet oder ungültig"
        
        # IP validieren
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not self.validate_ip(client_ip):
            return False, "IP-Adresse nicht erlaubt"
        
        # Signatur validieren
        body = request.get_data(as_text=True)
        if not self.verify_signature(
            signature, 
            self.config.API_SECRET_KEY,
            request.method,
            request.path,
            body,
            timestamp,
            nonce
        ):
            return False, "Ungültige Signatur"
        
        return True, None

# Globale Sicherheitsinstanz
security_manager: Optional[SecurityManager] = None

def init_security(config: Config, redis_client: Optional[redis.Redis] = None) -> None:
    """Initialisiert den Sicherheitsmanager"""
    global security_manager
    security_manager = SecurityManager(config, redis_client)

def require_auth(f):
    """Decorator für API-Authentifizierung"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not security_manager:
            return jsonify({'error': 'Sicherheitssystem nicht initialisiert'}), 500
        
        # Authentifizierung prüfen
        is_valid, error_msg = security_manager.authenticate_request()
        if not is_valid:
            return jsonify({'error': error_msg}), 401
        
        # Rate Limiting prüfen
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not security_manager.check_rate_limit(
            client_ip, 
            security_manager.config.RATE_LIMIT_PER_MIN
        ):
            return jsonify({'error': 'Rate Limit überschritten'}), 429
        
        # Trace-ID für Logging
        g.trace_id = str(uuid.uuid4())
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_api_key(f):
    """Decorator für einfache API-Key-Authentifizierung (für UI)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key or api_key != current_app.config.get('API_PUBLIC_KEY'):
            return jsonify({'error': 'Ungültiger API-Key'}), 401
        return f(*args, **kwargs)
    
    return decorated_function

def audit_log(action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Audit-Logging für Sicherheitsereignisse"""
    trace_id = getattr(g, 'trace_id', 'unknown')
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'trace_id': trace_id,
        'action': action,
        'ip': client_ip,
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'details': details or {}
    }
    
    current_app.logger.info(f"AUDIT: {json.dumps(log_entry)}")

# Hilfsfunktionen für Tests
def generate_test_signature(secret: str, method: str, path: str, 
                          body: str, timestamp: str, nonce: str) -> str:
    """Generiert Test-Signatur für Unit-Tests"""
    message = f"{method.upper()}{path}{body}{timestamp}{nonce}".encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        message,
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')

def create_test_headers(api_key: str, secret: str, method: str = 'POST', 
                      path: str = '/api/v1/signal', body: str = '{}') -> Dict[str, str]:
    """Erstellt Test-Header für Unit-Tests"""
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())
    signature = generate_test_signature(secret, method, path, body, timestamp, nonce)
    
    return {
        'X-API-KEY': api_key,
        'X-TS': timestamp,
        'X-NONCE': nonce,
        'X-SIGNATURE': signature,
        'Content-Type': 'application/json'
    }
