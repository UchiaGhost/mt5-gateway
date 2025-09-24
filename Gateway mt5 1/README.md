# MT5 Flask Gateway

> **Produktionstaugliches MetaTrader 5 Gateway für n8n Integration**

[![CI/CD Pipeline](https://github.com/mt5gateway/mt5-flask-gateway/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/mt5gateway/mt5-flask-gateway/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](CHANGELOG.md)

## 🚀 Übersicht

Das **MT5 Flask Gateway** ist eine vollständige, monetarisierbare Lösung, die eine sichere HTTP/REST-Schnittstelle für **n8n** (Request Node/Webhook) bereitstellt, um Trading-Signale an **MetaTrader 5** zu senden. Die Anwendung bietet eine moderne Web-UI für Konfiguration, Monitoring und Lizenzierung.

### ✨ Hauptfunktionen

- **🔐 Sichere API**: HMAC-Signaturen, Rate Limiting, IP-Allowlist
- **📊 MT5 Integration**: Vollständige MetaTrader 5 Anbindung
- **🎯 n8n Ready**: Optimiert für n8n Request Nodes
- **💻 Web-UI**: Modernes Dashboard mit TailwindCSS
- **💰 Monetarisierung**: Lizenzierung, Stripe-Integration, Feature-Gates
- **📈 Monitoring**: Echtzeit-Logs, Metriken, Health Checks
- **🔧 Einfache Installation**: Windows-Installer, Batch-Skripte
- **🧪 Tests**: Umfassende Test-Suite mit Mock-Backend

## 🏗️ Architektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      n8n        │───▶│  Flask Gateway  │───▶│   MetaTrader 5  │
│  (Request Node) │    │   (REST API)    │    │   (Trading)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Web-UI        │
                       │  (Dashboard)    │
                       └─────────────────┘
```

### Tech-Stack

- **Backend**: Python 3.11+, Flask, SQLAlchemy
- **Trading**: MetaTrader5 Python SDK
- **Frontend**: HTML5, TailwindCSS, Alpine.js
- **Sicherheit**: HMAC-SHA256, Rate Limiting, CORS
- **Datenbank**: SQLite (produktionsreif)
- **Cache**: Redis (optional)
- **Zahlungen**: Stripe
- **Build**: PyInstaller, NSIS

## 🚀 Schnellstart

### 1. One-Click Installation (Windows)

#### ⚡ Einfachste Methode - Doppelklick-Start
```bash
# 1. Repository herunterladen/entpacken
# 2. Doppelklick auf: Start-MT5-Flask-Gateway.cmd
# 3. Fertig! 🎉
```

Das **One-Click Bootstrap-Skript** führt automatisch aus:
- ✅ Admin-Rechte-Prüfung (UAC-Elevation)
- ✅ Python 3.11+ Installation (falls nötig)
- ✅ Projekt-Setup in `%PROGRAMDATA%\MT5FlaskGateway`
- ✅ Virtuelle Umgebung + Dependencies
- ✅ Sichere `.env`-Generierung
- ✅ Firewall-Regel für Port 8080
- ✅ Desktop-Verknüpfung erstellen
- ✅ Browser öffnen + Web-UI starten

#### 🔧 Alternative Installationsmethoden

**Windows-Installer:**
```bash
# Kompilierten Installer herunterladen und ausführen
MT5_Flask_Gateway_Setup.exe
```

**Manuelle Installation:**
```bash
# Nur für Entwickler/erweiterte Nutzer
scripts\install_production.bat
```

**Manuell (Entwicklung):**
```bash
# Repository klonen
git clone https://github.com/mt5gateway/mt5-flask-gateway.git
cd mt5-flask-gateway

# Virtuelle Umgebung erstellen
python -m venv venv
venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration
copy env.example .env
# .env bearbeiten mit Ihren MT5-Zugangsdaten

# Starten
python app.py
```

### 2. Konfiguration

1. **MT5-Verbindung einrichten**:
   - Server, Login, Passwort in `.env` konfigurieren
   - MT5-Pfad angeben

2. **API-Keys generieren**:
   - Web-UI öffnen: http://localhost:8080
   - Mit `admin` / `admin123` anmelden
   - Neue API-Keys in der Konfiguration generieren

3. **n8n konfigurieren**:
   - HTTP Request Node hinzufügen
   - URL: `http://localhost:8080/api/v1/signal`
   - Headers und Body nach Dokumentation konfigurieren

### 3. Erste Schritte

```bash
# Gateway starten
start_mt5_gateway.bat

# Web-UI öffnen
http://localhost:8080

# API testen
curl -X POST "http://localhost:8080/api/v1/signal" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: pub_xxxxx" \
  -H "X-TS: 1695555555" \
  -H "X-NONCE: 9f2a1c0c7b1e4d8e" \
  -H "X-SIGNATURE: <calculated_hmac>" \
  -d '{
    "strategy":"breakout-v1",
    "symbol":"EURUSD",
    "side":"buy",
    "type":"market",
    "risk":{"percent":1.0},
    "sl":{"pips":20},
    "tp":{"pips":40},
    "idempotency_key":"test-123"
  }'
```

## 📚 API-Dokumentation

### Authentifizierung

Alle API-Endpunkte erfordern HMAC-SHA256-Authentifizierung:

```http
X-API-KEY: pub_xxxxx
X-TS: 1695555555
X-NONCE: 9f2a1c0c7b1e4d8e
X-SIGNATURE: <hmac_sha256_signature>
```

### Endpunkte

#### `POST /api/v1/signal`
Trading-Signal verarbeiten

**Request:**
```json
{
  "strategy": "breakout-v1",
  "symbol": "EURUSD",
  "side": "buy",
  "type": "market",
  "risk": {"percent": 1.0},
  "sl": {"pips": 20},
  "tp": {"pips": 40},
  "comment": "n8n-signal-123",
  "idempotency_key": "b0f7b..."
}
```

**Response:**
```json
{
  "ok": true,
  "order_id": 12345678,
  "position_id": 987654,
  "executed_price": 1.07321,
  "sl": 1.07121,
  "tp": 1.07721,
  "server_time": "2025-09-24T10:15:00Z"
}
```

#### `GET /api/v1/positions`
Offene Positionen abrufen

#### `GET /api/v1/account`
Kontoinformationen abrufen

#### `GET /api/v1/health`
System Health Check

### Vollständige API-Dokumentation

Siehe [API-Dokumentation](docs/api.md) für alle verfügbaren Endpunkte.

## 🎨 Web-UI

Die Web-UI bietet:

- **📊 Dashboard**: MT5-Status, offene Positionen, letzte Signale
- **⚙️ Konfiguration**: MT5-Zugang, Trading-Einstellungen, API-Keys
- **🔗 n8n Integration**: Beispiel-Requests, cURL-Befehle, Troubleshooting
- **📋 Logs**: Filterbare Logs, Download, Suche
- **🔑 Lizenzierung**: Lizenz-Status, Feature-Gates, Kauf-Optionen

**Zugang**: http://localhost:8080
**Standard-Login**: `admin` / `admin123`

## 💰 Lizenzierung & Monetarisierung

### Lizenz-Modelle

- **🆓 Trial**: 14 Tage kostenlos
- **💼 Basic**: €99/Monat - Standard-Features
- **⭐ Pro**: €199/Monat - Erweiterte Features
- **🏢 Enterprise**: €499/Monat - Unbegrenzte Features

### Features nach Lizenz

| Feature | Trial | Basic | Pro | Enterprise |
|---------|-------|-------|-----|------------|
| API-Zugang | ✅ | ✅ | ✅ | ✅ |
| Standard-Strategien | ✅ | ✅ | ✅ | ✅ |
| Erweiterte Strategien | ❌ | ❌ | ✅ | ✅ |
| Custom Indikatoren | ❌ | ❌ | ✅ | ✅ |
| Parallele Orders | 2 | 10 | 50 | Unbegrenzt |
| Support | ❌ | E-Mail | Priorität | 24/7 |

### Zahlungsabwicklung

- **Stripe-Integration** für sichere Zahlungen
- **Automatische Lizenz-Aktivierung**
- **Webhook-basierte Updates**
- **Offline-Lizenz-Cache**

## 🔧 Entwicklung

### Setup

```bash
# Repository klonen
git clone https://github.com/mt5gateway/mt5-flask-gateway.git
cd mt5-flask-gateway

# Entwicklungsumgebung
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Tests ausführen
pytest tests/

# Entwicklungsserver
scripts\run_dev.bat
```

### Projektstruktur

```
mt5-flask-gateway/
├── app/                    # Hauptanwendung
│   ├── api/               # REST API
│   ├── mt5/               # MT5 Integration
│   ├── security/          # Sicherheitsmodule
│   ├── services/          # Services (Lizenz, Logging, etc.)
│   └── ui/                # Web-UI
├── tests/                 # Tests
├── scripts/               # Build-Skripte
├── installers/            # Installer-Konfiguration
└── docs/                  # Dokumentation
```

### Tests

```bash
# Unit Tests
pytest tests/unit/

# Integration Tests
pytest tests/integration/

# E2E Tests
pytest tests/e2e/

# Performance Tests
locust -f tests/performance/locustfile.py
```

## 📦 Build & Deployment

### EXE erstellen

```bash
scripts\build_exe.bat
```

### Installer erstellen

```bash
scripts\make_installer.bat
```

### Docker (Optional)

```bash
docker build -t mt5-gateway .
docker run -p 8080:8080 mt5-gateway
```

## 🔒 Sicherheit

- **HMAC-SHA256** für alle API-Requests
- **Rate Limiting** pro IP und API-Key
- **IP-Allowlist** konfigurierbar
- **Replay-Schutz** mit Nonce und Zeitstempel
- **Audit-Logging** aller Aktionen
- **HTTPS-Ready** (Reverse Proxy empfohlen)

## 📊 Monitoring & Logs

- **Strukturierte JSON-Logs**
- **Log-Rotation** und Archivierung
- **Echtzeit-Metriken**
- **Health Checks**
- **Performance-Monitoring**

## 🆘 Support

- **📧 E-Mail**: support@mt5gateway.com
- **📖 Dokumentation**: https://docs.mt5gateway.com
- **🐛 Issues**: GitHub Issues
- **💬 Community**: Discord Server

## 🎯 One-Click Start (Windows)

### Schritt-für-Schritt Anleitung

#### 1. Download & Vorbereitung
```
📁 MT5-Flask-Gateway.zip herunterladen
📂 Entpacken auf Desktop oder gewünschten Ordner
```

#### 2. One-Click Start
```
🖱️ Doppelklick auf: Start-MT5-Flask-Gateway.cmd
⚡ Das System macht den Rest automatisch!
```

#### 3. Was passiert automatisch?
```
🔐 UAC-Berechtigung anfordern (Admin-Rechte)
🐍 Python 3.11+ prüfen/installieren
📁 App nach %PROGRAMDATA%\MT5FlaskGateway installieren
🔧 Virtuelle Umgebung + Dependencies
🔑 Sichere Schlüssel generieren (.env)
🔥 Firewall-Regel für Port 8080 erstellen
🖥️ Desktop-Verknüpfung "MT5 Flask Gateway.lnk"
🌐 Browser öffnen → http://localhost:8080
```

#### 4. Erste Anmeldung
```
👤 Benutzername: admin
🔒 Passwort: admin123
🏠 URL: http://localhost:8080
```

#### 5. MT5 konfigurieren
```
⚙️ Konfiguration → MT5-Verbindung
🏦 Server: Ihr Broker-Server
👤 Login: Ihre MT5-Login-ID
🔑 Passwort: Ihr MT5-Passwort
📍 Pfad: C:\Program Files\MetaTrader 5\terminal64.exe
```

#### 6. n8n verbinden
```
🔗 n8n Integration → Beispiele kopieren
📋 HTTP Request Node konfigurieren
🔑 API-Keys aus Konfiguration verwenden
```

### Troubleshooting

| Problem | Lösung |
|---------|--------|
| 🚫 "Zugriff verweigert" | Als Administrator ausführen |
| 🐍 Python-Download-Fehler | Internetverbindung prüfen |
| 🔥 Firewall-Warnung | Port 8080 freigeben |
| 🏦 MT5-Verbindung fehlschlägt | MT5-Zugangsdaten prüfen |
| 🌐 Browser öffnet nicht | Manuell: http://localhost:8080 |

### Support-Bundle erstellen
```
❌ Bei Problemen: Support-Bundle wird automatisch erstellt
📧 Senden an: support@mt5gateway.com
📁 Pfad: %PROGRAMDATA%\MT5FlaskGateway\logs\support-bundle-*.zip
```

## 📄 Lizenz

Dieses Projekt ist proprietär lizenziert. Siehe [LICENSE](LICENSE) für Details.

## 🤝 Beitragen

Wir freuen uns über Beiträge! Bitte lesen Sie unsere [Contributing Guidelines](CONTRIBUTING.md).

## 📈 Roadmap

- [ ] WebSocket-Unterstützung für Echtzeit-Updates
- [ ] Docker-Container für einfache Deployment
- [ ] Mehrsprachigkeit (EN/DE)
- [ ] Mobile App
- [ ] Cloud-Hosting-Optionen

## 🙏 Danksagungen

- MetaTrader 5 Team für das Python SDK
- Flask Community für das großartige Framework
- n8n Team für die inspirierende Workflow-Plattform

---

**MT5 Flask Gateway** - Verbinden Sie Ihre Trading-Strategien mit MetaTrader 5 über n8n! 🚀
