"""
Unit Tests für MT5 Flask Gateway
Tests für Sicherheit, Trading Engine und API-Endpunkte
"""

import pytest
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app import create_app
from app.config import TestingConfig
from app.security import SecurityManager, generate_test_signature, create_test_headers
from app.mt5.trading import TradingEngine, TradingSignal, OrderSide, OrderType, RiskConfig, StopLossConfig, TakeProfitConfig
from app.mt5.mock import MockMT5Client, MockTradingEngine
from app.api.schemas import TradingSignalRequest, OrderRequest

@pytest.fixture
def app():
    """Erstellt Test-App"""
    app = create_app(TestingConfig())
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Erstellt Test-Client"""
    return app.test_client()

@pytest.fixture
def mock_mt5_client():
    """Mock MT5 Client"""
    return MockMT5Client()

@pytest.fixture
def mock_trading_engine(mock_mt5_client):
    """Mock Trading Engine"""
    return MockTradingEngine(mock_mt5_client)

@pytest.fixture
def security_manager():
    """Security Manager für Tests"""
    config = TestingConfig()
    return SecurityManager(config, None)

class TestSecurityManager:
    """Tests für Security Manager"""
    
    def test_generate_signature(self, security_manager):
        """Test Signatur-Generierung"""
        secret = "test_secret"
        method = "POST"
        path = "/api/v1/signal"
        body = '{"test": "data"}'
        timestamp = str(int(time.time()))
        nonce = "test_nonce_123"
        
        signature = security_manager.generate_signature(
            secret, method, path, body, timestamp, nonce
        )
        
        assert isinstance(signature, str)
        assert len(signature) > 0
    
    def test_verify_signature(self, security_manager):
        """Test Signatur-Verifikation"""
        secret = "test_secret"
        method = "POST"
        path = "/api/v1/signal"
        body = '{"test": "data"}'
        timestamp = str(int(time.time()))
        nonce = "test_nonce_123"
        
        signature = security_manager.generate_signature(
            secret, method, path, body, timestamp, nonce
        )
        
        # Gültige Signatur
        assert security_manager.verify_signature(
            signature, secret, method, path, body, timestamp, nonce
        )
        
        # Ungültige Signatur
        assert not security_manager.verify_signature(
            "invalid_signature", secret, method, path, body, timestamp, nonce
        )
    
    def test_validate_timestamp(self, security_manager):
        """Test Zeitstempel-Validierung"""
        current_time = int(time.time())
        
        # Gültiger Zeitstempel
        assert security_manager.validate_timestamp(str(current_time))
        
        # Zu alter Zeitstempel
        old_time = current_time - 400  # 400 Sekunden alt
        assert not security_manager.validate_timestamp(str(old_time))
        
        # Zu neuer Zeitstempel
        future_time = current_time + 400  # 400 Sekunden in der Zukunft
        assert not security_manager.validate_timestamp(str(future_time))
    
    def test_validate_nonce(self, security_manager):
        """Test Nonce-Validierung"""
        nonce1 = "test_nonce_123456789"
        nonce2 = "test_nonce_987654321"
        
        # Erste Verwendung
        assert security_manager.validate_nonce(nonce1)
        
        # Zweite Verwendung (sollte fehlschlagen)
        assert not security_manager.validate_nonce(nonce1)
        
        # Andere Nonce (sollte funktionieren)
        assert security_manager.validate_nonce(nonce2)
    
    def test_validate_ip(self, security_manager):
        """Test IP-Validierung"""
        # Lokale IPs sind erlaubt
        assert security_manager.validate_ip("127.0.0.1")
        assert security_manager.validate_ip("::1")
        
        # Andere IPs sind nicht erlaubt
        assert not security_manager.validate_ip("192.168.1.1")
        assert not security_manager.validate_ip("8.8.8.8")

class TestTradingEngine:
    """Tests für Trading Engine"""
    
    def test_calculate_lot_size(self, mock_trading_engine):
        """Test Lot-Größen-Berechnung"""
        symbol = "EURUSD"
        risk_config = RiskConfig(percent=1.0)
        sl_points = 20
        
        lot_size = mock_trading_engine.calculate_lot_size(symbol, risk_config, sl_points)
        
        assert lot_size is not None
        assert lot_size > 0
        assert lot_size >= 0.01  # Min Lot
        assert lot_size <= 100.0  # Max Lot
    
    def test_calculate_sl_tp_prices(self, mock_trading_engine):
        """Test SL/TP-Preis-Berechnung"""
        symbol = "EURUSD"
        side = OrderSide.BUY
        entry_price = 1.1000
        sl_config = StopLossConfig(pips=20)
        tp_config = TakeProfitConfig(pips=40)
        
        sl_price, tp_price = mock_trading_engine.calculate_sl_tp_prices(
            symbol, side, entry_price, sl_config, tp_config
        )
        
        assert sl_price is not None
        assert tp_price is not None
        assert sl_price < entry_price  # SL unter Entry für Buy
        assert tp_price > entry_price  # TP über Entry für Buy
    
    def test_validate_idempotency(self, mock_trading_engine):
        """Test Idempotency-Validierung"""
        key1 = "test_key_123"
        key2 = "test_key_456"
        
        # Erste Verwendung
        assert mock_trading_engine.validate_idempotency(key1)
        
        # Zweite Verwendung (sollte fehlschlagen)
        assert not mock_trading_engine.validate_idempotency(key1)
        
        # Andere Key (sollte funktionieren)
        assert mock_trading_engine.validate_idempotency(key2)
    
    def test_execute_signal(self, mock_trading_engine):
        """Test Signal-Ausführung"""
        signal = TradingSignal(
            strategy="test_strategy",
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            risk=RiskConfig(percent=1.0),
            sl=StopLossConfig(pips=20),
            tp=TakeProfitConfig(pips=40),
            comment="test_signal",
            idempotency_key="test_idempotency_123"
        )
        
        result = mock_trading_engine.execute_signal(signal)
        
        assert result.success
        assert result.order_id is not None
        assert result.position_id is not None
        assert result.executed_price is not None
        assert result.lot_size is not None
    
    def test_execute_signal_duplicate(self, mock_trading_engine):
        """Test doppelte Signal-Ausführung"""
        signal = TradingSignal(
            strategy="test_strategy",
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            risk=RiskConfig(percent=1.0),
            sl=StopLossConfig(pips=20),
            tp=TakeProfitConfig(pips=40),
            comment="test_signal",
            idempotency_key="duplicate_test_key"
        )
        
        # Erste Ausführung
        result1 = mock_trading_engine.execute_signal(signal)
        assert result1.success
        
        # Zweite Ausführung (sollte fehlschlagen)
        result2 = mock_trading_engine.execute_signal(signal)
        assert not result2.success
        assert "bereits verwendet" in result2.error_message

class TestAPIEndpoints:
    """Tests für API-Endpunkte"""
    
    def test_health_endpoint(self, client):
        """Test Health Check Endpoint"""
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
    
    def test_signal_endpoint_unauthorized(self, client):
        """Test Signal Endpoint ohne Authentifizierung"""
        response = client.post('/api/v1/signal', json={
            "strategy": "test",
            "symbol": "EURUSD",
            "side": "buy",
            "type": "market",
            "risk": {"percent": 1.0},
            "sl": {"pips": 20},
            "tp": {"pips": 40}
        })
        
        assert response.status_code == 401
    
    def test_signal_endpoint_authorized(self, client):
        """Test Signal Endpoint mit Authentifizierung"""
        # Test-Header erstellen
        headers = create_test_headers(
            api_key="test_pub_key",
            secret="test_sec_key",
            method="POST",
            path="/api/v1/signal",
            body='{"strategy":"test","symbol":"EURUSD","side":"buy","type":"market","risk":{"percent":1.0},"sl":{"pips":20},"tp":{"pips":40}}'
        )
        
        response = client.post('/api/v1/signal', 
                             json={
                                 "strategy": "test",
                                 "symbol": "EURUSD",
                                 "side": "buy",
                                 "type": "market",
                                 "risk": {"percent": 1.0},
                                 "sl": {"pips": 20},
                                 "tp": {"pips": 40}
                             },
                             headers=headers)
        
        # Mock-Modus sollte funktionieren
        assert response.status_code in [200, 503]  # 503 wenn MT5 nicht verfügbar
    
    def test_positions_endpoint(self, client):
        """Test Positions Endpoint"""
        headers = create_test_headers(
            api_key="test_pub_key",
            secret="test_sec_key",
            method="GET",
            path="/api/v1/positions",
            body=""
        )
        
        response = client.get('/api/v1/positions', headers=headers)
        assert response.status_code in [200, 503]
    
    def test_account_endpoint(self, client):
        """Test Account Endpoint"""
        headers = create_test_headers(
            api_key="test_pub_key",
            secret="test_sec_key",
            method="GET",
            path="/api/v1/account",
            body=""
        )
        
        response = client.get('/api/v1/account', headers=headers)
        assert response.status_code in [200, 503]

class TestSchemas:
    """Tests für Pydantic-Schemas"""
    
    def test_trading_signal_request_valid(self):
        """Test gültiges Trading-Signal-Request"""
        data = {
            "strategy": "test_strategy",
            "symbol": "EURUSD",
            "side": "buy",
            "type": "market",
            "risk": {"percent": 1.0},
            "sl": {"pips": 20},
            "tp": {"pips": 40},
            "comment": "test_comment",
            "idempotency_key": "test_key_123"
        }
        
        request = TradingSignalRequest(**data)
        
        assert request.strategy == "test_strategy"
        assert request.symbol == "EURUSD"
        assert request.side == "buy"
        assert request.type == "market"
        assert request.risk.percent == 1.0
        assert request.sl.pips == 20
        assert request.tp.pips == 40
    
    def test_trading_signal_request_invalid(self):
        """Test ungültiges Trading-Signal-Request"""
        data = {
            "strategy": "",  # Leerer String
            "symbol": "EURUSD",
            "side": "invalid_side",  # Ungültige Seite
            "type": "market",
            "risk": {"percent": 15.0},  # Zu hohes Risiko
            "sl": {"pips": 20},
            "tp": {"pips": 40}
        }
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            TradingSignalRequest(**data)
    
    def test_order_request_valid(self):
        """Test gültiges Order-Request"""
        data = {
            "symbol": "EURUSD",
            "side": "buy",
            "type": "market",
            "volume": 0.1,
            "sl": 1.0950,
            "tp": 1.1050,
            "comment": "test_order"
        }
        
        request = OrderRequest(**data)
        
        assert request.symbol == "EURUSD"
        assert request.side == "buy"
        assert request.type == "market"
        assert request.volume == 0.1
        assert request.sl == 1.0950
        assert request.tp == 1.1050

class TestMockMT5:
    """Tests für Mock MT5 Client"""
    
    def test_mock_mt5_initialization(self, mock_mt5_client):
        """Test Mock MT5 Initialisierung"""
        assert mock_mt5_client.is_connected
        assert mock_mt5_client.account_info is not None
        assert len(mock_mt5_client.symbols_cache) > 0
    
    def test_mock_mt5_symbol_info(self, mock_mt5_client):
        """Test Mock Symbol-Info"""
        symbol_info = mock_mt5_client.get_symbol_info("EURUSD")
        
        assert symbol_info is not None
        assert symbol_info.name == "EURUSD"
        assert symbol_info.digits == 5
        assert symbol_info.point == 0.00001
        assert symbol_info.is_trade_allowed
    
    def test_mock_mt5_account_info(self, mock_mt5_client):
        """Test Mock Account-Info"""
        account_info = mock_mt5_client.get_account_info()
        
        assert account_info is not None
        assert account_info['login'] == 1234567
        assert account_info['balance'] == 10000.0
        assert account_info['currency'] == "USD"
    
    def test_mock_mt5_positions(self, mock_trading_engine):
        """Test Mock Positionen"""
        # Position hinzufügen
        signal = TradingSignal(
            strategy="test",
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            risk=RiskConfig(percent=1.0),
            sl=StopLossConfig(pips=20),
            tp=TakeProfitConfig(pips=40),
            comment="test_position"
        )
        
        result = mock_trading_engine.execute_signal(signal)
        assert result.success
        
        # Positionen abrufen
        positions = mock_trading_engine.get_positions()
        assert len(positions) == 1
        assert positions[0]['symbol'] == "EURUSD"
        assert positions[0]['type'] == "buy"

# Integration Tests
class TestIntegration:
    """Integration Tests"""
    
    def test_full_trading_flow(self, mock_trading_engine):
        """Test vollständiger Trading-Flow"""
        # Signal erstellen
        signal = TradingSignal(
            strategy="integration_test",
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            risk=RiskConfig(percent=1.0),
            sl=StopLossConfig(pips=20),
            tp=TakeProfitConfig(pips=40),
            comment="integration_test_signal",
            idempotency_key="integration_test_key"
        )
        
        # Signal ausführen
        result = mock_trading_engine.execute_signal(signal)
        assert result.success
        
        # Positionen prüfen
        positions = mock_trading_engine.get_positions()
        assert len(positions) == 1
        
        position = positions[0]
        assert position['symbol'] == "EURUSD"
        assert position['type'] == "buy"
        
        # Position modifizieren
        success = mock_trading_engine.modify_position(
            position['ticket'], 
            sl=1.0950, 
            tp=1.1050
        )
        assert success
        
        # Position schließen
        success = mock_trading_engine.close_position(position['ticket'])
        assert success
        
        # Positionen prüfen (sollte leer sein)
        positions = mock_trading_engine.get_positions()
        assert len(positions) == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
