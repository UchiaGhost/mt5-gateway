"""
REST API Schemas für MT5 Flask Gateway
Pydantic-Modelle für Request/Response-Validierung
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class OrderSide(str, Enum):
    """Order-Seiten"""
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    """Order-Typen"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class RiskConfig(BaseModel):
    """Risikokonfiguration"""
    percent: float = Field(..., ge=0.1, le=10.0, description="Risikoprozentsatz")
    fixed_amount: Optional[float] = Field(None, ge=0, description="Fester Risikobetrag")
    max_risk_per_trade: float = Field(2.0, ge=0.1, le=5.0, description="Maximales Risiko pro Trade")

class StopLossConfig(BaseModel):
    """Stop-Loss Konfiguration"""
    pips: Optional[int] = Field(None, ge=1, le=1000, description="Stop-Loss in Pips")
    price: Optional[float] = Field(None, gt=0, description="Stop-Loss Preis")
    atr_multiplier: Optional[float] = Field(None, ge=0.5, le=5.0, description="ATR-Multiplikator")

class TakeProfitConfig(BaseModel):
    """Take-Profit Konfiguration"""
    pips: Optional[int] = Field(None, ge=1, le=1000, description="Take-Profit in Pips")
    price: Optional[float] = Field(None, gt=0, description="Take-Profit Preis")
    risk_reward_ratio: Optional[float] = Field(None, ge=0.5, le=10.0, description="Risk-Reward-Verhältnis")

class TradingSignalRequest(BaseModel):
    """Trading-Signal Request"""
    strategy: str = Field(..., min_length=1, max_length=50, description="Strategie-Name")
    symbol: str = Field(..., min_length=3, max_length=20, description="Symbol")
    side: OrderSide = Field(..., description="Order-Seite")
    type: OrderType = Field(..., description="Order-Typ")
    risk: RiskConfig = Field(..., description="Risikokonfiguration")
    sl: StopLossConfig = Field(..., description="Stop-Loss Konfiguration")
    tp: TakeProfitConfig = Field(..., description="Take-Profit Konfiguration")
    price: Optional[float] = Field(None, gt=0, description="Limit-Preis")
    comment: str = Field("", max_length=100, description="Kommentar")
    idempotency_key: str = Field("", min_length=1, max_length=100, description="Idempotency-Key")
    magic_number: int = Field(0, ge=0, le=999999, description="Magic Number")

    @validator('idempotency_key')
    def validate_idempotency_key(cls, v):
        if not v:
            import uuid
            v = str(uuid.uuid4())
        return v

class OrderRequest(BaseModel):
    """Direkte Order-Request"""
    symbol: str = Field(..., min_length=3, max_length=20, description="Symbol")
    side: OrderSide = Field(..., description="Order-Seite")
    type: OrderType = Field(..., description="Order-Typ")
    volume: float = Field(..., gt=0, le=100, description="Lot-Größe")
    price: Optional[float] = Field(None, gt=0, description="Limit-Preis")
    sl: Optional[float] = Field(None, gt=0, description="Stop-Loss Preis")
    tp: Optional[float] = Field(None, gt=0, description="Take-Profit Preis")
    comment: str = Field("", max_length=100, description="Kommentar")
    magic_number: int = Field(0, ge=0, le=999999, description="Magic Number")

class ModifyRequest(BaseModel):
    """Position-Modifikation Request"""
    ticket: int = Field(..., gt=0, description="Position-Ticket")
    sl: Optional[float] = Field(None, gt=0, description="Neuer Stop-Loss")
    tp: Optional[float] = Field(None, gt=0, description="Neuer Take-Profit")

class CloseRequest(BaseModel):
    """Position-Schließung Request"""
    ticket: int = Field(..., gt=0, description="Position-Ticket")
    volume: Optional[float] = Field(None, gt=0, description="Schließungs-Volumen")

class TradingSignalResponse(BaseModel):
    """Trading-Signal Response"""
    ok: bool = Field(..., description="Erfolg")
    order_id: Optional[int] = Field(None, description="Order-ID")
    position_id: Optional[int] = Field(None, description="Position-ID")
    executed_price: Optional[float] = Field(None, description="Ausführungspreis")
    sl: Optional[float] = Field(None, description="Stop-Loss Preis")
    tp: Optional[float] = Field(None, description="Take-Profit Preis")
    lot_size: Optional[float] = Field(None, description="Lot-Größe")
    server_time: Optional[datetime] = Field(None, description="Server-Zeit")
    error_message: Optional[str] = Field(None, description="Fehlermeldung")

class PositionInfo(BaseModel):
    """Position-Informationen"""
    ticket: int = Field(..., description="Ticket")
    symbol: str = Field(..., description="Symbol")
    type: str = Field(..., description="Typ")
    volume: float = Field(..., description="Volumen")
    price_open: float = Field(..., description="Eröffnungspreis")
    price_current: float = Field(..., description="Aktueller Preis")
    sl: float = Field(..., description="Stop-Loss")
    tp: float = Field(..., description="Take-Profit")
    profit: float = Field(..., description="Gewinn/Verlust")
    swap: float = Field(..., description="Swap")
    comment: str = Field(..., description="Kommentar")
    magic: int = Field(..., description="Magic Number")
    time: datetime = Field(..., description="Zeit")

class AccountInfo(BaseModel):
    """Konto-Informationen"""
    login: int = Field(..., description="Login")
    server: str = Field(..., description="Server")
    balance: float = Field(..., description="Balance")
    equity: float = Field(..., description="Equity")
    margin: float = Field(..., description="Margin")
    free_margin: float = Field(..., description="Freie Margin")
    margin_level: float = Field(..., description="Margin Level")
    currency: str = Field(..., description="Währung")
    leverage: int = Field(..., description="Hebel")
    profit: float = Field(..., description="Gewinn/Verlust")
    company: str = Field(..., description="Broker")
    name: str = Field(..., description="Konto-Name")
    server_time: datetime = Field(..., description="Server-Zeit")

class SymbolInfo(BaseModel):
    """Symbol-Informationen"""
    name: str = Field(..., description="Symbol-Name")
    digits: int = Field(..., description="Nachkommastellen")
    point: float = Field(..., description="Point-Wert")
    tick_value: float = Field(..., description="Tick-Wert")
    contract_size: float = Field(..., description="Kontraktgröße")
    margin_required: float = Field(..., description="Erforderliche Margin")
    spread: int = Field(..., description="Spread")
    is_trade_allowed: bool = Field(..., description="Handel erlaubt")

class HealthResponse(BaseModel):
    """Health Check Response"""
    status: str = Field(..., description="Status")
    timestamp: datetime = Field(..., description="Zeitstempel")
    version: str = Field(..., description="Version")
    database: str = Field(..., description="Datenbank-Status")
    redis: str = Field(..., description="Redis-Status")
    mt5_connected: bool = Field(..., description="MT5 verbunden")
    license_status: str = Field(..., description="Lizenz-Status")

class ErrorResponse(BaseModel):
    """Fehler-Response"""
    error: str = Field(..., description="Fehlermeldung")
    code: Optional[int] = Field(None, description="Fehlercode")
    details: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Details")

class SuccessResponse(BaseModel):
    """Erfolgs-Response"""
    success: bool = Field(True, description="Erfolg")
    message: Optional[str] = Field(None, description="Nachricht")
    data: Optional[Dict[str, Any]] = Field(None, description="Daten")
