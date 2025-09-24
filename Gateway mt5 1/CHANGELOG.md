# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### Hinzugefügt
- **Erstveröffentlichung** des MT5 Flask Gateway
- **Vollständige MT5-Integration** mit Python SDK
- **Sichere REST-API** mit HMAC-SHA256-Authentifizierung
- **Moderne Web-UI** mit TailwindCSS und Alpine.js
- **n8n-Integration** mit Beispielen und Dokumentation
- **Lizenzierungssystem** mit Stripe-Integration
- **Feature-Gates** für verschiedene Lizenz-Modelle
- **Umfassende Sicherheit**:
  - Rate Limiting
  - IP-Allowlist
  - Replay-Schutz
  - Audit-Logging
- **Trading-Funktionen**:
  - Signal-Verarbeitung
  - Risikomanagement
  - Lot-Größen-Berechnung
  - SL/TP-Management
  - Position-Management
- **Monitoring & Logs**:
  - Strukturierte JSON-Logs
  - Log-Rotation
  - Echtzeit-Metriken
  - Health Checks
- **Installation & Deployment**:
  - Windows-Installer (NSIS)
  - Batch-Skripte
  - PyInstaller EXE-Build
  - Desktop-Verknüpfungen
- **Tests & Qualität**:
  - Unit-Tests mit pytest
  - Integration-Tests
  - Mock-Backend für Tests
  - CI/CD-Pipeline mit GitHub Actions
- **Dokumentation**:
  - Vollständige API-Dokumentation
  - n8n-Integration-Guide
  - Troubleshooting-Guide
  - Installations-Anleitung

### Technische Details
- **Python 3.11+** Unterstützung
- **Flask** als Web-Framework
- **SQLAlchemy** für Datenbank-Operationen
- **SQLite** als Standard-Datenbank
- **Redis** für Caching (optional)
- **MetaTrader5** Python SDK
- **Stripe** für Zahlungsabwicklung
- **Pydantic** für Datenvalidierung
- **TailwindCSS** für UI-Styling
- **Alpine.js** für Frontend-Logik

### API-Endpunkte
- `POST /api/v1/signal` - Trading-Signal verarbeiten
- `POST /api/v1/order` - Direkte Order platzieren
- `GET /api/v1/positions` - Offene Positionen abrufen
- `POST /api/v1/modify` - Position modifizieren
- `POST /api/v1/close` - Position schließen
- `GET /api/v1/account` - Kontoinformationen abrufen
- `GET /api/v1/symbols` - Verfügbare Symbole abrufen
- `GET /api/v1/health` - System Health Check
- `GET /api/v1/metrics` - System-Metriken abrufen

### Web-UI-Seiten
- **Dashboard** - Übersicht und Status
- **Konfiguration** - MT5, Trading, API-Einstellungen
- **n8n-Integration** - Beispiele und Anleitung
- **Logs** - Log-Viewer und Suche
- **Lizenzierung** - Lizenz-Status und Kauf

### Lizenz-Modelle
- **Trial** - 14 Tage kostenlos
- **Basic** - €99/Monat
- **Pro** - €199/Monat
- **Enterprise** - €499/Monat

### Sicherheitsfeatures
- HMAC-SHA256-Signaturen für alle API-Requests
- Zeitstempel-Validierung (±300s Toleranz)
- Nonce-basierter Replay-Schutz
- Rate Limiting (konfigurierbar)
- IP-Allowlist-Unterstützung
- Umfassendes Audit-Logging
- CSRF-Schutz für Web-UI

### Build & Deployment
- **Windows-Installer** mit NSIS
- **PyInstaller** für Standalone-EXE
- **Batch-Skripte** für Installation und Verwaltung
- **GitHub Actions** CI/CD-Pipeline
- **Docker-Unterstützung** (experimentell)

### Tests
- **Unit-Tests** für alle Kernmodule
- **Integration-Tests** für API-Endpunkte
- **Mock-Backend** für MT5-Simulation
- **Performance-Tests** mit Locust
- **Security-Tests** mit Trivy

---

## Geplante Features (Roadmap)

### Version 1.1.0
- [ ] WebSocket-Unterstützung für Echtzeit-Updates
- [ ] Erweiterte Trading-Strategien
- [ ] Custom-Indikatoren-Support
- [ ] Mobile-responsive UI-Verbesserungen

### Version 1.2.0
- [ ] Mehrsprachigkeit (EN/DE)
- [ ] Docker-Container-Optimierung
- [ ] Cloud-Hosting-Integration
- [ ] Erweiterte Metriken und Analytics

### Version 2.0.0
- [ ] Mobile App (React Native)
- [ ] Multi-Broker-Unterstützung
- [ ] Advanced Risk Management
- [ ] Machine Learning Integration

---

## Breaking Changes

Keine Breaking Changes in Version 1.0.0 (Erstveröffentlichung).

---

## Bekannte Probleme

- **MT5-Verbindung**: Erfordert lokale MT5-Installation
- **Windows-spezifisch**: Optimiert für Windows 10/11
- **Firewall**: Port 8080 muss freigegeben werden
- **Antivirus**: Möglicherweise False-Positive bei EXE-Build

---

## Migration Guide

N/A für Version 1.0.0 (Erstveröffentlichung).

---

## Contributors

- **MT5 Gateway Team** - Hauptentwicklung
- **Community Contributors** - Feedback und Testing

---

## Support

- **E-Mail**: support@mt5gateway.com
- **Dokumentation**: https://docs.mt5gateway.com
- **GitHub Issues**: https://github.com/mt5gateway/mt5-flask-gateway/issues
- **Discord**: https://discord.gg/mt5gateway
