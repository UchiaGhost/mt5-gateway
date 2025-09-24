"""
Telemetrie-Service für MT5 Flask Gateway
Opt-in Metriken und DSGVO-konforme Datensammlung
"""

import json
import logging
import platform
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from app.config import Config

@dataclass
class TelemetryEvent:
    """Telemetrie-Event"""
    event_id: str
    event_type: str
    timestamp: datetime
    session_id: str
    user_id: Optional[str]
    data: Dict[str, Any]

@dataclass
class SystemMetrics:
    """System-Metriken"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int

class TelemetryService:
    """Telemetrie-Service"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_enabled = not config.TELEMETRY_OPTOUT
        self.session_id = str(uuid.uuid4())
        self.events: List[TelemetryEvent] = []
        self.metrics: List[SystemMetrics] = []
        self.max_events = 1000
        self.max_metrics = 100
        
        # DSGVO-Hinweise
        self.privacy_notice = {
            "data_collection": "Anonymisierte Nutzungsdaten für Produktverbesserung",
            "data_types": ["API-Calls", "Fehlerkategorien", "System-Metriken", "Performance-Daten"],
            "retention": "30 Tage",
            "purpose": "Produktverbesserung und Fehlerbehebung",
            "legal_basis": "Berechtigtes Interesse (Art. 6 Abs. 1 lit. f DSGVO)"
        }
    
    def is_telemetry_enabled(self) -> bool:
        """Prüft ob Telemetrie aktiviert ist"""
        return self.is_enabled
    
    def enable_telemetry(self) -> None:
        """Aktiviert Telemetrie"""
        self.is_enabled = True
        self.logger.info("Telemetrie aktiviert")
    
    def disable_telemetry(self) -> None:
        """Deaktiviert Telemetrie"""
        self.is_enabled = False
        self.events.clear()
        self.metrics.clear()
        self.logger.info("Telemetrie deaktiviert")
    
    def _create_event(self, event_type: str, data: Dict[str, Any], 
                     user_id: Optional[str] = None) -> TelemetryEvent:
        """Erstellt Telemetrie-Event"""
        return TelemetryEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            session_id=self.session_id,
            user_id=user_id,
            data=data
        )
    
    def track_api_call(self, endpoint: str, method: str, status_code: int, 
                      response_time: float, user_id: Optional[str] = None) -> None:
        """Verfolgt API-Aufrufe"""
        if not self.is_enabled:
            return
        
        try:
            event_data = {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            event = self._create_event("api_call", event_data, user_id)
            self.events.append(event)
            
            # Events begrenzen
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verfolgen von API-Aufruf: {e}")
    
    def track_error(self, error_type: str, error_message: str, 
                   context: Dict[str, Any], user_id: Optional[str] = None) -> None:
        """Verfolgt Fehler"""
        if not self.is_enabled:
            return
        
        try:
            event_data = {
                "error_type": error_type,
                "error_message": error_message[:200],  # Begrenzen
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            event = self._create_event("error", event_data, user_id)
            self.events.append(event)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verfolgen von Fehler: {e}")
    
    def track_trading_signal(self, strategy: str, symbol: str, side: str, 
                           success: bool, user_id: Optional[str] = None) -> None:
        """Verfolgt Trading-Signale"""
        if not self.is_enabled:
            return
        
        try:
            event_data = {
                "strategy": strategy,
                "symbol": symbol,
                "side": side,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            event = self._create_event("trading_signal", event_data, user_id)
            self.events.append(event)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verfolgen von Trading-Signal: {e}")
    
    def track_system_metrics(self) -> None:
        """Sammelt System-Metriken"""
        if not self.is_enabled:
            return
        
        try:
            import psutil
            
            # CPU-Nutzung
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Speicher-Nutzung
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Festplatten-Nutzung
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Netzwerk-IO
            network_io = psutil.net_io_counters()
            network_data = {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            }
            
            # Aktive Verbindungen
            connections = len(psutil.net_connections())
            
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_data,
                active_connections=connections
            )
            
            self.metrics.append(metrics)
            
            # Metriken begrenzen
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
                
        except Exception as e:
            self.logger.error(f"Fehler beim Sammeln von System-Metriken: {e}")
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Gibt Telemetrie-Zusammenfassung zurück"""
        if not self.is_enabled:
            return {"enabled": False}
        
        try:
            # Events nach Typ gruppieren
            event_counts = {}
            for event in self.events:
                event_type = event.event_type
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Letzte Metriken
            latest_metrics = self.metrics[-1] if self.metrics else None
            
            return {
                "enabled": True,
                "session_id": self.session_id,
                "total_events": len(self.events),
                "event_counts": event_counts,
                "latest_metrics": asdict(latest_metrics) if latest_metrics else None,
                "privacy_notice": self.privacy_notice
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Telemetrie-Zusammenfassung: {e}")
            return {"enabled": False, "error": str(e)}
    
    def export_telemetry_data(self) -> Dict[str, Any]:
        """Exportiert Telemetrie-Daten"""
        if not self.is_enabled:
            return {"enabled": False}
        
        try:
            # Events serialisieren
            events_data = []
            for event in self.events:
                event_dict = asdict(event)
                event_dict['timestamp'] = event.timestamp.isoformat()
                events_data.append(event_dict)
            
            # Metriken serialisieren
            metrics_data = []
            for metric in self.metrics:
                metric_dict = asdict(metric)
                metric_dict['timestamp'] = metric.timestamp.isoformat()
                metrics_data.append(metric_dict)
            
            return {
                "enabled": True,
                "session_id": self.session_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "events": events_data,
                "metrics": metrics_data,
                "privacy_notice": self.privacy_notice
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Exportieren der Telemetrie-Daten: {e}")
            return {"enabled": False, "error": str(e)}
    
    def clear_telemetry_data(self) -> None:
        """Löscht Telemetrie-Daten"""
        self.events.clear()
        self.metrics.clear()
        self.logger.info("Telemetrie-Daten gelöscht")
    
    def get_privacy_notice(self) -> Dict[str, Any]:
        """Gibt Datenschutzhinweise zurück"""
        return {
            **self.privacy_notice,
            "opt_out_available": True,
            "data_controller": "MT5 Flask Gateway",
            "contact": "privacy@mt5gateway.com",
            "rights": [
                "Auskunft über verarbeitete Daten",
                "Berichtigung unrichtiger Daten",
                "Löschung der Daten",
                "Einschränkung der Verarbeitung",
                "Widerspruch gegen die Verarbeitung"
            ]
        }

# Globale Telemetrie-Service Instanz
telemetry_service: Optional[TelemetryService] = None

def init_telemetry_service(config: Config) -> None:
    """Initialisiert den Telemetrie-Service"""
    global telemetry_service
    telemetry_service = TelemetryService(config)

def get_telemetry_service() -> Optional[TelemetryService]:
    """Gibt den Telemetrie-Service zurück"""
    return telemetry_service
