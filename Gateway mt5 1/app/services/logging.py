"""
Logging-Service für MT5 Flask Gateway
Strukturierte Logs, Rotation und Archivierung
"""

import json
import logging
import os
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from app.config import Config

@dataclass
class LogEntry:
    """Log-Eintrag"""
    timestamp: datetime
    level: str
    logger: str
    message: str
    module: str
    function: str
    line: int
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class StructuredFormatter(logging.Formatter):
    """Strukturierter Log-Formatter"""
    
    def format(self, record):
        """Formatiert Log-Record"""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            trace_id=getattr(record, 'trace_id', None),
            user_id=getattr(record, 'user_id', None),
            extra_data=getattr(record, 'extra_data', None)
        )
        
        return json.dumps(asdict(log_entry), default=str, ensure_ascii=False)

class LoggingService:
    """Logging-Service"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.log_dir = "logs"
        self.log_file = os.path.join(self.log_dir, "mt5_gateway.log")
        self.audit_log_file = os.path.join(self.log_dir, "audit.log")
        self.error_log_file = os.path.join(self.log_dir, "error.log")
        
        # Log-Verzeichnis erstellen
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Logging konfigurieren
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Konfiguriert Logging"""
        try:
            # Root Logger konfigurieren
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, self.config.LOG_LEVEL.upper()))
            
            # Bestehende Handler entfernen
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Haupt-Log-Handler
            main_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.config.MAX_LOG_SIZE,
                backupCount=self.config.BACKUP_COUNT,
                encoding='utf-8'
            )
            main_handler.setFormatter(StructuredFormatter())
            main_handler.setLevel(logging.INFO)
            root_logger.addHandler(main_handler)
            
            # Error-Log-Handler
            error_handler = RotatingFileHandler(
                self.error_log_file,
                maxBytes=self.config.MAX_LOG_SIZE,
                backupCount=self.config.BACKUP_COUNT,
                encoding='utf-8'
            )
            error_handler.setFormatter(StructuredFormatter())
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)
            
            # Audit-Log-Handler
            audit_handler = TimedRotatingFileHandler(
                self.audit_log_file,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
            audit_handler.setFormatter(StructuredFormatter())
            audit_handler.setLevel(logging.INFO)
            root_logger.addHandler(audit_handler)
            
            # Console-Handler für Development
            if self.config.LOG_LEVEL.upper() == 'DEBUG':
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
                console_handler.setLevel(logging.DEBUG)
                root_logger.addHandler(console_handler)
            
            self.logger.info("Logging konfiguriert")
            
        except Exception as e:
            print(f"Fehler bei Logging-Konfiguration: {e}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Gibt Logger zurück"""
        return logging.getLogger(name)
    
    def log_audit(self, action: str, details: Dict[str, Any], 
                  trace_id: Optional[str] = None, user_id: Optional[str] = None) -> None:
        """Audit-Log"""
        audit_logger = logging.getLogger('audit')
        
        # Extra-Daten hinzufügen
        extra_data = {
            'action': action,
            'details': details,
            'trace_id': trace_id,
            'user_id': user_id
        }
        
        audit_logger.info(f"AUDIT: {action}", extra={'extra_data': extra_data})
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                  trace_id: Optional[str] = None, user_id: Optional[str] = None) -> None:
        """Error-Log"""
        error_logger = logging.getLogger('error')
        
        extra_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'trace_id': trace_id,
            'user_id': user_id
        }
        
        error_logger.error(f"ERROR: {error}", extra={'extra_data': extra_data})
    
    def log_trading_event(self, event_type: str, symbol: str, 
                         details: Dict[str, Any], trace_id: Optional[str] = None) -> None:
        """Trading-Event-Log"""
        trading_logger = logging.getLogger('trading')
        
        extra_data = {
            'event_type': event_type,
            'symbol': symbol,
            'details': details,
            'trace_id': trace_id
        }
        
        trading_logger.info(f"TRADING: {event_type} - {symbol}", extra={'extra_data': extra_data})
    
    def log_api_request(self, method: str, endpoint: str, status_code: int,
                       response_time: float, trace_id: Optional[str] = None) -> None:
        """API-Request-Log"""
        api_logger = logging.getLogger('api')
        
        extra_data = {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time': response_time,
            'trace_id': trace_id
        }
        
        api_logger.info(f"API: {method} {endpoint} - {status_code}", extra={'extra_data': extra_data})
    
    def get_log_files(self) -> List[Dict[str, Any]]:
        """Gibt verfügbare Log-Dateien zurück"""
        log_files = []
        
        try:
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(self.log_dir, filename)
                    stat = os.stat(filepath)
                    
                    log_files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
            
            # Nach Änderungsdatum sortieren
            log_files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Log-Dateien: {e}")
        
        return log_files
    
    def read_log_file(self, filename: str, lines: int = 100) -> List[str]:
        """Liest Log-Datei"""
        try:
            filepath = os.path.join(self.log_dir, filename)
            
            if not os.path.exists(filepath):
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
            # Letzte N Zeilen
            return all_lines[-lines:] if lines > 0 else all_lines
            
        except Exception as e:
            self.logger.error(f"Fehler beim Lesen der Log-Datei {filename}: {e}")
            return []
    
    def search_logs(self, query: str, log_type: str = "all", 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Durchsucht Logs"""
        results = []
        
        try:
            log_files = self.get_log_files()
            
            for log_file in log_files:
                if log_type != "all" and log_type not in log_file['filename']:
                    continue
                
                lines = self.read_log_file(log_file['filename'], 0)
                
                for line in lines:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Datum-Filter
                        if start_date or end_date:
                            log_time = datetime.fromisoformat(log_entry['timestamp'])
                            if start_date and log_time < start_date:
                                continue
                            if end_date and log_time > end_date:
                                continue
                        
                        # Query-Filter
                        if query.lower() in line.lower():
                            results.append({
                                'log_file': log_file['filename'],
                                'log_entry': log_entry
                            })
                            
                    except json.JSONDecodeError:
                        # Nicht-JSON Zeilen ignorieren
                        continue
            
            # Nach Zeitstempel sortieren
            results.sort(key=lambda x: x['log_entry']['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Log-Suche: {e}")
        
        return results
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Bereinigt alte Log-Dateien"""
        cleaned_count = 0
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            log_files = self.get_log_files()
            
            for log_file in log_files:
                file_date = datetime.fromisoformat(log_file['modified'])
                
                if file_date < cutoff_date:
                    try:
                        os.remove(log_file['filepath'])
                        cleaned_count += 1
                        self.logger.info(f"Alte Log-Datei gelöscht: {log_file['filename']}")
                    except Exception as e:
                        self.logger.error(f"Fehler beim Löschen der Log-Datei {log_file['filename']}: {e}")
            
        except Exception as e:
            self.logger.error(f"Fehler bei Log-Bereinigung: {e}")
        
        return cleaned_count
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Gibt Log-Statistiken zurück"""
        try:
            log_files = self.get_log_files()
            total_size = sum(log_file['size'] for log_file in log_files)
            
            return {
                'total_files': len(log_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'log_files': log_files,
                'log_directory': self.log_dir
            }
            
        except Exception as e:
            self.logger.error(f"Fehler bei Log-Statistiken: {e}")
            return {}

# Globale Logging-Service Instanz
logging_service: Optional[LoggingService] = None

def init_logging_service(config: Config) -> None:
    """Initialisiert den Logging-Service"""
    global logging_service
    logging_service = LoggingService(config)

def get_logging_service() -> Optional[LoggingService]:
    """Gibt den Logging-Service zurück"""
    return logging_service
