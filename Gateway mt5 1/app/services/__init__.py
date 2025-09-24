"""
Lizenzierungs-Service für MT5 Flask Gateway
Online/Offline Lizenzprüfung, Feature-Gates und Monetarisierung
"""

import hashlib
import json
import logging
import platform
import psutil
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from app.config import Config

@dataclass
class LicenseInfo:
    """Lizenz-Informationen"""
    license_key: str
    license_type: str  # trial, basic, pro, enterprise
    expires_at: datetime
    max_activations: int
    current_activations: int
    features: List[str]
    hardware_fingerprint: str
    is_valid: bool

@dataclass
class FeatureGate:
    """Feature-Gate"""
    name: str
    enabled: bool
    limit: Optional[int] = None
    description: Optional[str] = None

class LicenseManager:
    """Lizenz-Manager"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.license_info: Optional[LicenseInfo] = None
        self.offline_cache: Optional[Dict[str, Any]] = None
        self.cache_file = "license_cache.json"
        self.hardware_fingerprint = self._generate_hardware_fingerprint()
        
        # Feature-Gates definieren
        self.feature_gates = {
            "max_concurrent_orders": FeatureGate(
                name="max_concurrent_orders",
                enabled=True,
                limit=10,
                description="Maximale parallele Orders"
            ),
            "advanced_strategies": FeatureGate(
                name="advanced_strategies",
                enabled=False,
                description="Erweiterte Trading-Strategien"
            ),
            "custom_indicators": FeatureGate(
                name="custom_indicators",
                enabled=False,
                description="Benutzerdefinierte Indikatoren"
            ),
            "api_rate_limit": FeatureGate(
                name="api_rate_limit",
                enabled=True,
                limit=60,
                description="API Rate Limit pro Minute"
            ),
            "telemetry": FeatureGate(
                name="telemetry",
                enabled=True,
                description="Telemetrie-Daten"
            )
        }
        
        # Offline-Cache laden
        self._load_offline_cache()
    
    def _generate_hardware_fingerprint(self) -> str:
        """Generiert Hardware-Fingerprint"""
        try:
            # System-Informationen sammeln
            system_info = {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "machine": platform.machine(),
                "node": platform.node(),
                "cpu_count": psutil.cpu_count(),
                "memory": psutil.virtual_memory().total,
                "disk": psutil.disk_usage('/').total if hasattr(psutil, 'disk_usage') else 0
            }
            
            # Fingerprint generieren
            fingerprint_data = json.dumps(system_info, sort_keys=True)
            fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
            
            return fingerprint
            
        except Exception as e:
            self.logger.error(f"Fehler bei Hardware-Fingerprint: {e}")
            return "unknown"
    
    def _load_offline_cache(self) -> None:
        """Lädt Offline-Cache"""
        try:
            import os
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.offline_cache = json.load(f)
                    
                # Cache-Gültigkeit prüfen
                if self.offline_cache:
                    cache_time = datetime.fromisoformat(self.offline_cache.get('timestamp', '1970-01-01'))
                    if datetime.utcnow() - cache_time > timedelta(hours=24):
                        self.offline_cache = None
                        
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des Offline-Cache: {e}")
            self.offline_cache = None
    
    def _save_offline_cache(self, license_data: Dict[str, Any]) -> None:
        """Speichert Offline-Cache"""
        try:
            cache_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "license_data": license_data,
                "hardware_fingerprint": self.hardware_fingerprint
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern des Offline-Cache: {e}")
    
    def _verify_offline_license(self) -> bool:
        """Verifiziert Offline-Lizenz"""
        if not self.offline_cache:
            return False
        
        try:
            license_data = self.offline_cache.get('license_data', {})
            hardware_fp = self.offline_cache.get('hardware_fingerprint')
            
            # Hardware-Fingerprint prüfen
            if hardware_fp != self.hardware_fingerprint:
                self.logger.warning("Hardware-Fingerprint stimmt nicht überein")
                return False
            
            # Lizenz-Gültigkeit prüfen
            expires_at = datetime.fromisoformat(license_data.get('expires_at', '1970-01-01'))
            if datetime.utcnow() > expires_at:
                self.logger.warning("Offline-Lizenz abgelaufen")
                return False
            
            # Lizenz-Info erstellen
            self.license_info = LicenseInfo(
                license_key=license_data.get('license_key', ''),
                license_type=license_data.get('license_type', 'trial'),
                expires_at=expires_at,
                max_activations=license_data.get('max_activations', 1),
                current_activations=license_data.get('current_activations', 1),
                features=license_data.get('features', []),
                hardware_fingerprint=self.hardware_fingerprint,
                is_valid=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Offline-Lizenz-Verifikation: {e}")
            return False
    
    def _verify_online_license(self) -> bool:
        """Verifiziert Online-Lizenz"""
        if not self.config.LICENSE_SERVER_URL or not self.config.LICENSE_KEY:
            return False
        
        try:
            # Lizenz-Server anfragen
            url = f"{self.config.LICENSE_SERVER_URL}/license/verify"
            payload = {
                "license_key": self.config.LICENSE_KEY,
                "hardware_fingerprint": self.hardware_fingerprint,
                "version": "1.0.0"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                license_data = response.json()
                
                # Lizenz-Info erstellen
                self.license_info = LicenseInfo(
                    license_key=license_data.get('license_key', ''),
                    license_type=license_data.get('license_type', 'trial'),
                    expires_at=datetime.fromisoformat(license_data.get('expires_at', '1970-01-01')),
                    max_activations=license_data.get('max_activations', 1),
                    current_activations=license_data.get('current_activations', 1),
                    features=license_data.get('features', []),
                    hardware_fingerprint=self.hardware_fingerprint,
                    is_valid=True
                )
                
                # Offline-Cache aktualisieren
                self._save_offline_cache(license_data)
                
                return True
            else:
                self.logger.warning(f"Lizenz-Server antwortete mit Status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler bei Online-Lizenz-Verifikation: {e}")
            return False
    
    def verify_license(self) -> bool:
        """Verifiziert Lizenz (Online mit Offline-Fallback)"""
        # Zuerst Online-Verifikation versuchen
        if self._verify_online_license():
            return True
        
        # Falls Online-Verifikation fehlschlägt, Offline-Cache prüfen
        if self._verify_offline_license():
            return True
        
        # Fallback: Trial-Lizenz
        self.license_info = LicenseInfo(
            license_key="trial",
            license_type="trial",
            expires_at=datetime.utcnow() + timedelta(days=14),
            max_activations=1,
            current_activations=1,
            features=["basic_trading"],
            hardware_fingerprint=self.hardware_fingerprint,
            is_valid=True
        )
        
        self.logger.info("Trial-Lizenz aktiviert")
        return True
    
    def is_licensed(self) -> bool:
        """Prüft ob Lizenz gültig ist"""
        if not self.license_info:
            return self.verify_license()
        
        return self.license_info.is_valid and datetime.utcnow() < self.license_info.expires_at
    
    def get_license_info(self) -> Optional[LicenseInfo]:
        """Gibt Lizenz-Informationen zurück"""
        if not self.license_info:
            self.verify_license()
        
        return self.license_info
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Prüft ob Feature aktiviert ist"""
        if not self.is_licensed():
            return False
        
        # Feature-Gate prüfen
        feature_gate = self.feature_gates.get(feature_name)
        if not feature_gate:
            return False
        
        # Lizenz-Features prüfen
        if self.license_info and feature_name in self.license_info.features:
            return True
        
        # Standard-Features für Trial/Basic
        if self.license_info and self.license_info.license_type in ['trial', 'basic']:
            return feature_gate.enabled
        
        return False
    
    def get_feature_limit(self, feature_name: str) -> Optional[int]:
        """Gibt Feature-Limit zurück"""
        if not self.is_feature_enabled(feature_name):
            return None
        
        feature_gate = self.feature_gates.get(feature_name)
        if not feature_gate:
            return None
        
        # Lizenz-basierte Limits
        if self.license_info:
            if self.license_info.license_type == 'enterprise':
                return None  # Kein Limit
            elif self.license_info.license_type == 'pro':
                return feature_gate.limit * 2 if feature_gate.limit else None
            elif self.license_info.license_type == 'basic':
                return feature_gate.limit
            else:  # trial
                return max(1, feature_gate.limit // 2) if feature_gate.limit else 1
        
        return feature_gate.limit
    
    def get_license_status(self) -> Dict[str, Any]:
        """Gibt Lizenz-Status zurück"""
        if not self.license_info:
            self.verify_license()
        
        if not self.license_info:
            return {
                "status": "unlicensed",
                "message": "Keine Lizenz verfügbar"
            }
        
        days_remaining = (self.license_info.expires_at - datetime.utcnow()).days
        
        return {
            "status": "licensed" if self.is_licensed() else "expired",
            "license_type": self.license_info.license_type,
            "expires_at": self.license_info.expires_at.isoformat(),
            "days_remaining": days_remaining,
            "features": self.license_info.features,
            "hardware_fingerprint": self.hardware_fingerprint,
            "max_activations": self.license_info.max_activations,
            "current_activations": self.license_info.current_activations
        }

# Globale Lizenz-Manager Instanz
license_manager: Optional[LicenseManager] = None

def init_license_manager(config: Config) -> None:
    """Initialisiert den Lizenz-Manager"""
    global license_manager
    license_manager = LicenseManager(config)

def get_license_manager() -> Optional[LicenseManager]:
    """Gibt den Lizenz-Manager zurück"""
    return license_manager
