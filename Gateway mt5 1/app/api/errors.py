"""
API Error Handler für MT5 Flask Gateway
Zentrale Fehlerbehandlung für alle API-Endpunkte
"""

import logging
from flask import jsonify, request
from werkzeug.exceptions import HTTPException
from app.api.schemas import ErrorResponse

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Registriert Error Handler für die Flask-App"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """400 Bad Request"""
        return jsonify(ErrorResponse(
            error="Ungültige Anfrage",
            code=400,
            details={"message": str(error)}
        ).dict()), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """401 Unauthorized"""
        return jsonify(ErrorResponse(
            error="Nicht autorisiert",
            code=401,
            details={"message": "API-Key oder Signatur ungültig"}
        ).dict()), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 Forbidden"""
        return jsonify(ErrorResponse(
            error="Zugriff verweigert",
            code=403,
            details={"message": "Unzureichende Berechtigung"}
        ).dict()), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """404 Not Found"""
        return jsonify(ErrorResponse(
            error="Nicht gefunden",
            code=404,
            details={"message": "Ressource nicht verfügbar"}
        ).dict()), 404
    
    @app.errorhandler(409)
    def conflict(error):
        """409 Conflict"""
        return jsonify(ErrorResponse(
            error="Konflikt",
            code=409,
            details={"message": "Idempotency-Key bereits verwendet"}
        ).dict()), 409
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """422 Unprocessable Entity"""
        return jsonify(ErrorResponse(
            error="Nicht verarbeitbar",
            code=422,
            details={"message": "Geschäftslogik-Fehler"}
        ).dict()), 422
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """429 Too Many Requests"""
        return jsonify(ErrorResponse(
            error="Zu viele Anfragen",
            code=429,
            details={"message": "Rate Limit überschritten"}
        ).dict()), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 Internal Server Error"""
        logger.error(f"Interner Server-Fehler: {error}")
        return jsonify(ErrorResponse(
            error="Interner Server-Fehler",
            code=500,
            details={"message": "Unbekannter Fehler aufgetreten"}
        ).dict()), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """503 Service Unavailable"""
        return jsonify(ErrorResponse(
            error="Service nicht verfügbar",
            code=503,
            details={"message": "MT5-Verbindung oder externe Services nicht verfügbar"}
        ).dict()), 503
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Behandelt HTTP-Exceptions"""
        return jsonify(ErrorResponse(
            error=error.name,
            code=error.code,
            details={"message": error.description}
        ).dict()), error.code
    
    @app.errorhandler(Exception)
    def handle_general_exception(error):
        """Behandelt allgemeine Exceptions"""
        logger.error(f"Unbehandelte Exception: {error}")
        return jsonify(ErrorResponse(
            error="Interner Fehler",
            code=500,
            details={"message": "Unbekannter Fehler aufgetreten"}
        ).dict()), 500
