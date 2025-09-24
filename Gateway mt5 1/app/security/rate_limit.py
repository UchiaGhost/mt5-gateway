"""
Rate Limiting Implementierung für MT5 Flask Gateway
"""

import time
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, g
import redis
from app.config import Config

class RateLimiter:
    """Rate Limiter mit Redis-Backend"""
    
    def __init__(self, config: Config, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis_client = redis_client
        self.default_limit = config.RATE_LIMIT_PER_MIN
        self.default_window = 60  # Sekunden
    
    def is_allowed(self, identifier: str, limit: Optional[int] = None, 
                  window: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """Prüft ob Request erlaubt ist"""
        limit = limit or self.default_limit
        window = window or self.default_window
        
        if not self.redis_client:
            return True, {'limit': limit, 'remaining': limit, 'reset_time': int(time.time()) + window}
        
        try:
            key = f"rate_limit:{identifier}"
            current_time = int(time.time())
            window_start = current_time - (current_time % window)
            window_key = f"{key}:{window_start}"
            
            # Aktuelle Anzahl der Requests in diesem Fenster
            current_count = self.redis_client.get(window_key)
            if current_count is None:
                current_count = 0
            else:
                current_count = int(current_count)
            
            if current_count >= limit:
                return False, {
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': window_start + window,
                    'retry_after': window_start + window - current_time
                }
            
            # Request zählen
            pipe = self.redis_client.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, window)
            pipe.execute()
            
            return True, {
                'limit': limit,
                'remaining': limit - current_count - 1,
                'reset_time': window_start + window
            }
            
        except redis.RedisError:
            # Bei Redis-Fehlern Rate Limiting deaktivieren
            return True, {'limit': limit, 'remaining': limit, 'reset_time': int(time.time()) + window}
    
    def get_client_identifier(self) -> str:
        """Ermittelt Client-Identifier für Rate Limiting"""
        # IP-Adresse als Basis
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # API-Key falls vorhanden
        api_key = request.headers.get('X-API-KEY')
        if api_key:
            return f"{client_ip}:{api_key}"
        
        return client_ip

# Globale Rate Limiter Instanz
rate_limiter: Optional[RateLimiter] = None

def init_rate_limiter(config: Config, redis_client: Optional[redis.Redis] = None) -> None:
    """Initialisiert den Rate Limiter"""
    global rate_limiter
    rate_limiter = RateLimiter(config, redis_client)

def rate_limit(limit: Optional[int] = None, window: Optional[int] = None):
    """Decorator für Rate Limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not rate_limiter:
                return f(*args, **kwargs)
            
            identifier = rate_limiter.get_client_identifier()
            is_allowed, info = rate_limiter.is_allowed(identifier, limit, window)
            
            if not is_allowed:
                response = jsonify({
                    'error': 'Rate Limit überschritten',
                    'limit': info['limit'],
                    'remaining': info['remaining'],
                    'reset_time': info['reset_time'],
                    'retry_after': info.get('retry_after', 0)
                })
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
                if 'retry_after' in info:
                    response.headers['Retry-After'] = str(info['retry_after'])
                
                return response, 429
            
            # Rate Limit Info an Response anhängen
            g.rate_limit_info = info
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def add_rate_limit_headers(response):
    """Fügt Rate Limit Header zur Response hinzu"""
    if hasattr(g, 'rate_limit_info'):
        info = g.rate_limit_info
        response.headers['X-RateLimit-Limit'] = str(info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
        response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
    
    return response
