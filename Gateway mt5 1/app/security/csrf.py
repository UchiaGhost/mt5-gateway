"""
CSRF-Schutz für MT5 Flask Gateway
"""

from flask_wtf.csrf import CSRFProtect, CSRFError
from flask import request, jsonify, render_template
from functools import wraps

csrf = CSRFProtect()

def init_csrf(app):
    """Initialisiert CSRF-Schutz"""
    csrf.init_app(app)
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Behandelt CSRF-Fehler"""
        if request.is_json:
            return jsonify({'error': 'CSRF-Token ungültig oder fehlt'}), 400
        return render_template('errors/csrf.html'), 400

def csrf_exempt(f):
    """Decorator um CSRF-Schutz für bestimmte Routen zu deaktivieren"""
    f.csrf_exempt = True
    return f

def csrf_required(f):
    """Decorator um CSRF-Schutz explizit zu aktivieren"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # CSRF-Token validieren
        if not csrf.validate_csrf(request.form.get('csrf_token')):
            if request.is_json:
                return jsonify({'error': 'CSRF-Token ungültig'}), 400
            return render_template('errors/csrf.html'), 400
        return f(*args, **kwargs)
    
    return decorated_function
