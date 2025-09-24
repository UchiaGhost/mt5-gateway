"""
REST API Routes für MT5 Flask Gateway
Implementiert alle API-Endpunkte für Trading-Signale und Management
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from app.api.schemas import (
    TradingSignalRequest, TradingSignalResponse, OrderRequest, 
    ModifyRequest, CloseRequest, PositionInfo, AccountInfo, 
    SymbolInfo, HealthResponse, ErrorResponse, SuccessResponse
)
from app.security import require_auth, audit_log
from app.mt5 import get_mt5_client
from app.mt5.trading import get_trading_engine, TradingSignal, OrderSide, OrderType, RiskConfig, StopLossConfig, TakeProfitConfig
from app.mt5.account import get_account_manager
from app.services.licensing import get_license_manager

# API Blueprint erstellen
api = Blueprint('api', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)

def handle_api_error(error: Exception, status_code: int = 500) -> tuple:
    """Behandelt API-Fehler"""
    logger.error(f"API Fehler: {error}")
    audit_log("api_error", {"error": str(error), "status_code": status_code})
    
    response = ErrorResponse(
        error=str(error),
        code=status_code
    )
    return jsonify(response.dict()), status_code

@api.route('/signal', methods=['POST'])
@require_auth
def post_signal():
    """Trading-Signal verarbeiten"""
    try:
        # Request validieren
        signal_data = TradingSignalRequest(**request.get_json())
        
        # Lizenz prüfen
        license_manager = get_license_manager()
        if license_manager and not license_manager.is_licensed():
            return jsonify(ErrorResponse(
                error="Lizenz erforderlich",
                code=402
            ).dict()), 402
        
        # Trading Engine abrufen
        trading_engine = get_trading_engine()
        if not trading_engine:
            return jsonify(ErrorResponse(
                error="Trading Engine nicht verfügbar",
                code=503
            ).dict()), 503
        
        # Signal konvertieren
        signal = TradingSignal(
            strategy=signal_data.strategy,
            symbol=signal_data.symbol,
            side=OrderSide(signal_data.side),
            order_type=OrderType(signal_data.type),
            risk=RiskConfig(
                percent=signal_data.risk.percent,
                fixed_amount=signal_data.risk.fixed_amount,
                max_risk_per_trade=signal_data.risk.max_risk_per_trade
            ),
            sl=StopLossConfig(
                pips=signal_data.sl.pips,
                price=signal_data.sl.price,
                atr_multiplier=signal_data.sl.atr_multiplier
            ),
            tp=TakeProfitConfig(
                pips=signal_data.tp.pips,
                price=signal_data.tp.price,
                risk_reward_ratio=signal_data.tp.risk_reward_ratio
            ),
            price=signal_data.price,
            comment=signal_data.comment,
            idempotency_key=signal_data.idempotency_key,
            magic_number=signal_data.magic_number
        )
        
        # Signal ausführen
        result = trading_engine.execute_signal(signal)
        
        # Audit Log
        audit_log("signal_executed", {
            "strategy": signal.strategy,
            "symbol": signal.symbol,
            "side": signal.side.value,
            "success": result.success,
            "order_id": result.order_id
        })
        
        # Response erstellen
        response = TradingSignalResponse(
            ok=result.success,
            order_id=result.order_id,
            position_id=result.position_id,
            executed_price=result.executed_price,
            sl=result.sl_price,
            tp=result.tp_price,
            lot_size=result.lot_size,
            server_time=result.server_time,
            error_message=result.error_message
        )
        
        status_code = 200 if result.success else 422
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        return handle_api_error(e, 400)

@api.route('/order', methods=['POST'])
@require_auth
def post_order():
    """Direkte Order platzieren"""
    try:
        # Request validieren
        order_data = OrderRequest(**request.get_json())
        
        # Lizenz prüfen
        license_manager = get_license_manager()
        if license_manager and not license_manager.is_licensed():
            return jsonify(ErrorResponse(
                error="Lizenz erforderlich",
                code=402
            ).dict()), 402
        
        # Trading Engine abrufen
        trading_engine = get_trading_engine()
        if not trading_engine:
            return jsonify(ErrorResponse(
                error="Trading Engine nicht verfügbar",
                code=503
            ).dict()), 503
        
        # Signal erstellen
        signal = TradingSignal(
            strategy="direct_order",
            symbol=order_data.symbol,
            side=OrderSide(order_data.side),
            order_type=OrderType(order_data.type),
            risk=RiskConfig(percent=0.0),  # Kein Risikomanagement für direkte Orders
            sl=StopLossConfig(price=order_data.sl),
            tp=TakeProfitConfig(price=order_data.tp),
            price=order_data.price,
            comment=order_data.comment,
            idempotency_key="",  # Keine Idempotency für direkte Orders
            magic_number=order_data.magic_number
        )
        
        # Order ausführen
        result = trading_engine.execute_signal(signal)
        
        # Audit Log
        audit_log("order_executed", {
            "symbol": order_data.symbol,
            "side": order_data.side,
            "volume": order_data.volume,
            "success": result.success,
            "order_id": result.order_id
        })
        
        # Response erstellen
        response = TradingSignalResponse(
            ok=result.success,
            order_id=result.order_id,
            position_id=result.position_id,
            executed_price=result.executed_price,
            sl=result.sl_price,
            tp=result.tp_price,
            lot_size=result.lot_size,
            server_time=result.server_time,
            error_message=result.error_message
        )
        
        status_code = 200 if result.success else 422
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        return handle_api_error(e, 400)

@api.route('/positions', methods=['GET'])
@require_auth
def get_positions():
    """Offene Positionen abrufen"""
    try:
        symbol = request.args.get('symbol')
        
        # Trading Engine abrufen
        trading_engine = get_trading_engine()
        if not trading_engine:
            return jsonify(ErrorResponse(
                error="Trading Engine nicht verfügbar",
                code=503
            ).dict()), 503
        
        # Positionen abrufen
        positions = trading_engine.get_positions(symbol)
        
        # Response erstellen
        position_list = []
        for pos in positions:
            position_list.append(PositionInfo(**pos).dict())
        
        return jsonify({
            "success": True,
            "positions": position_list,
            "count": len(position_list)
        }), 200
        
    except Exception as e:
        return handle_api_error(e, 500)

@api.route('/modify', methods=['POST'])
@require_auth
def modify_position():
    """Position modifizieren"""
    try:
        # Request validieren
        modify_data = ModifyRequest(**request.get_json())
        
        # Trading Engine abrufen
        trading_engine = get_trading_engine()
        if not trading_engine:
            return jsonify(ErrorResponse(
                error="Trading Engine nicht verfügbar",
                code=503
            ).dict()), 503
        
        # Position modifizieren
        success = trading_engine.modify_position(
            modify_data.ticket,
            modify_data.sl,
            modify_data.tp
        )
        
        # Audit Log
        audit_log("position_modified", {
            "ticket": modify_data.ticket,
            "sl": modify_data.sl,
            "tp": modify_data.tp,
            "success": success
        })
        
        if success:
            return jsonify(SuccessResponse(
                message="Position erfolgreich modifiziert"
            ).dict()), 200
        else:
            return jsonify(ErrorResponse(
                error="Position konnte nicht modifiziert werden",
                code=422
            ).dict()), 422
        
    except Exception as e:
        return handle_api_error(e, 400)

@api.route('/close', methods=['POST'])
@require_auth
def close_position():
    """Position schließen"""
    try:
        # Request validieren
        close_data = CloseRequest(**request.get_json())
        
        # Trading Engine abrufen
        trading_engine = get_trading_engine()
        if not trading_engine:
            return jsonify(ErrorResponse(
                error="Trading Engine nicht verfügbar",
                code=503
            ).dict()), 503
        
        # Position schließen
        success = trading_engine.close_position(
            close_data.ticket,
            close_data.volume
        )
        
        # Audit Log
        audit_log("position_closed", {
            "ticket": close_data.ticket,
            "volume": close_data.volume,
            "success": success
        })
        
        if success:
            return jsonify(SuccessResponse(
                message="Position erfolgreich geschlossen"
            ).dict()), 200
        else:
            return jsonify(ErrorResponse(
                error="Position konnte nicht geschlossen werden",
                code=422
            ).dict()), 422
        
    except Exception as e:
        return handle_api_error(e, 400)

@api.route('/account', methods=['GET'])
@require_auth
def get_account():
    """Kontoinformationen abrufen"""
    try:
        # Account Manager abrufen
        account_manager = get_account_manager()
        if not account_manager:
            return jsonify(ErrorResponse(
                error="Account Manager nicht verfügbar",
                code=503
            ).dict()), 503
        
        # Konto-Info abrufen
        account_info = account_manager.get_account_summary()
        if not account_info:
            return jsonify(ErrorResponse(
                error="Kontoinformationen nicht verfügbar",
                code=503
            ).dict()), 503
        
        # Response erstellen
        response = AccountInfo(
            login=account_info.login,
            server=account_info.server,
            balance=account_info.balance,
            equity=account_info.equity,
            margin=account_info.margin,
            free_margin=account_info.free_margin,
            margin_level=account_info.margin_level,
            currency=account_info.currency,
            leverage=account_info.leverage,
            profit=account_info.profit,
            company=account_info.company,
            name=account_info.name,
            server_time=account_info.server_time
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        return handle_api_error(e, 500)

@api.route('/symbols', methods=['GET'])
@require_auth
def get_symbols():
    """Verfügbare Symbole abrufen"""
    try:
        symbol = request.args.get('symbol')
        
        # MT5 Client abrufen
        mt5_client = get_mt5_client()
        if not mt5_client:
            return jsonify(ErrorResponse(
                error="MT5 Client nicht verfügbar",
                code=503
            ).dict()), 503
        
        if symbol:
            # Einzelnes Symbol
            symbol_info = mt5_client.get_symbol_info(symbol)
            if not symbol_info:
                return jsonify(ErrorResponse(
                    error=f"Symbol {symbol} nicht gefunden",
                    code=404
                ).dict()), 404
            
            response = SymbolInfo(
                name=symbol_info.name,
                digits=symbol_info.digits,
                point=symbol_info.point,
                tick_value=symbol_info.tick_value,
                contract_size=symbol_info.contract_size,
                margin_required=symbol_info.margin_required,
                spread=symbol_info.spread,
                is_trade_allowed=symbol_info.is_trade_allowed
            )
            
            return jsonify(response.dict()), 200
        else:
            # Alle Symbole (vereinfacht - nur gecachte)
            symbols = []
            for symbol_name, symbol_info in mt5_client.symbols_cache.items():
                symbols.append(SymbolInfo(
                    name=symbol_info.name,
                    digits=symbol_info.digits,
                    point=symbol_info.point,
                    tick_value=symbol_info.tick_value,
                    contract_size=symbol_info.contract_size,
                    margin_required=symbol_info.margin_required,
                    spread=symbol_info.spread,
                    is_trade_allowed=symbol_info.is_trade_allowed
                ).dict())
            
            return jsonify({
                "success": True,
                "symbols": symbols,
                "count": len(symbols)
            }), 200
        
    except Exception as e:
        return handle_api_error(e, 500)

@api.route('/health', methods=['GET'])
@require_auth
def get_health():
    """System Health Check"""
    try:
        # MT5 Client Status
        mt5_client = get_mt5_client()
        mt5_connected = mt5_client.is_connected if mt5_client else False
        
        # Lizenz Status
        license_manager = get_license_manager()
        license_status = "licensed" if license_manager and license_manager.is_licensed() else "unlicensed"
        
        # Response erstellen
        response = HealthResponse(
            status="healthy" if mt5_connected else "degraded",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            database="connected",  # Vereinfacht
            redis="connected" if current_app.config.get('REDIS_URL') else "disconnected",
            mt5_connected=mt5_connected,
            license_status=license_status
        )
        
        status_code = 200 if mt5_connected else 503
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        return handle_api_error(e, 500)

@api.route('/metrics', methods=['GET'])
@require_auth
def get_metrics():
    """System-Metriken abrufen"""
    try:
        # Account Manager abrufen
        account_manager = get_account_manager()
        if not account_manager:
            return jsonify(ErrorResponse(
                error="Account Manager nicht verfügbar",
                code=503
            ).dict()), 503
        
        # Risiko-Metriken abrufen
        risk_metrics = account_manager.get_risk_metrics()
        if not risk_metrics:
            return jsonify(ErrorResponse(
                error="Risiko-Metriken nicht verfügbar",
                code=503
            ).dict()), 503
        
        return jsonify({
            "success": True,
            "metrics": risk_metrics
        }), 200
        
    except Exception as e:
        return handle_api_error(e, 500)
