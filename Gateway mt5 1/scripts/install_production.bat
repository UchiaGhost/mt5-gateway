@echo off
REM ============================================================================
REM MT5 Flask Gateway - Production Installation Script
REM Erweiterte Version mit Python-Management und robuster Konfiguration
REM ============================================================================

setlocal enableextensions enabledelayedexpansion

REM Farben für bessere UX
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

REM App-Konfiguration
set "APP_NAME=MT5 Flask Gateway"
set "APP_VERSION=1.0.0"
set "REQUIRED_PYTHON_VERSION=3.11"
set "DEFAULT_PORT=8080"

echo %BLUE%============================================================================%RESET%
echo %BLUE%  %APP_NAME% v%APP_VERSION% - Produktions-Installation%RESET%
echo %BLUE%============================================================================%RESET%
echo.

REM Aktuelles Verzeichnis sollte %PROGRAMDATA%\MT5FlaskGateway sein
if not exist "requirements.txt" (
    echo %RED%Fehler: requirements.txt nicht gefunden.%RESET%
    echo Bitte stellen Sie sicher, dass das Skript aus dem App-Verzeichnis ausgeführt wird.
    exit /b 1
)

REM Log-Datei
set "LOG_FILE=%CD%\logs\install.log"
echo [%date% %time%] Installation gestartet > "%LOG_FILE%"

echo %BLUE%Schritt 1: Python-Installation sicherstellen...%RESET%
echo [%date% %time%] Prüfe Python-Installation >> "%LOG_FILE%"

REM Führe Python-Prüfung/Installation aus
powershell -ExecutionPolicy Bypass -File "scripts\ensure_python.ps1" -Version %REQUIRED_PYTHON_VERSION%
set "PYTHON_RESULT=%errorlevel%"

if %PYTHON_RESULT% neq 0 (
    echo %RED%Fehler: Python %REQUIRED_PYTHON_VERSION% konnte nicht bereitgestellt werden.%RESET%
    echo [%date% %time%] Python-Installation fehlgeschlagen >> "%LOG_FILE%"
    exit /b 1
)

echo %GREEN%✓%RESET% Python %REQUIRED_PYTHON_VERSION% verfügbar
echo.

REM Ermittle Python-Kommando
set "PYTHON_CMD=python"
py -%REQUIRED_PYTHON_VERSION% --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -%REQUIRED_PYTHON_VERSION%"
)

echo %BLUE%Schritt 2: Virtuelle Umgebung erstellen...%RESET%
echo [%date% %time%] Erstelle virtuelle Umgebung >> "%LOG_FILE%"

REM Entferne alte venv falls vorhanden
if exist "venv" (
    echo %YELLOW%Entferne alte virtuelle Umgebung...%RESET%
    rmdir /s /q "venv" >nul 2>&1
)

REM Erstelle neue venv
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo %RED%Fehler: Virtuelle Umgebung konnte nicht erstellt werden.%RESET%
    echo [%date% %time%] venv-Erstellung fehlgeschlagen >> "%LOG_FILE%"
    exit /b 1
)

echo %GREEN%✓%RESET% Virtuelle Umgebung erstellt
echo.

echo %BLUE%Schritt 3: Aktiviere venv und installiere Abhängigkeiten...%RESET%
echo [%date% %time%] Aktiviere venv und installiere Abhängigkeiten >> "%LOG_FILE%"

REM Aktiviere venv
call "venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo %RED%Fehler: Virtuelle Umgebung konnte nicht aktiviert werden.%RESET%
    echo [%date% %time%] venv-Aktivierung fehlgeschlagen >> "%LOG_FILE%"
    exit /b 1
)

REM Upgrade pip, setuptools, wheel
echo %BLUE%Upgrade pip, setuptools, wheel...%RESET%
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo %YELLOW%Warnung: pip upgrade fehlgeschlagen. Fahre fort...%RESET%
    echo [%date% %time%] pip upgrade fehlgeschlagen >> "%LOG_FILE%"
)

REM Installiere Requirements
echo %BLUE%Installiere Python-Abhängigkeiten...%RESET%
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo %RED%Fehler: Abhängigkeiten konnten nicht installiert werden.%RESET%
    echo [%date% %time%] pip install requirements.txt fehlgeschlagen >> "%LOG_FILE%"
    exit /b 1
)

echo %GREEN%✓%RESET% Abhängigkeiten installiert
echo.

echo %BLUE%Schritt 4: Konfiguration vorbereiten...%RESET%
echo [%date% %time%] Konfiguration vorbereiten >> "%LOG_FILE%"

REM Erstelle config-Verzeichnis
if not exist "config" mkdir config

REM .env-Datei erstellen/aktualisieren
if not exist "config\.env" (
    if exist "env.example" (
        echo %BLUE%Erstelle .env aus env.example...%RESET%
        copy "env.example" "config\.env" >nul
        echo [%date% %time%] .env aus env.example erstellt >> "%LOG_FILE%"
    ) else (
        echo %BLUE%Erstelle Standard-.env-Datei...%RESET%
        call :create_default_env
        echo [%date% %time%] Standard-.env erstellt >> "%LOG_FILE%"
    )
) else (
    echo %GREEN%✓%RESET% .env-Datei existiert bereits
)

REM Generiere sichere Schlüssel
echo %BLUE%Generiere sichere API-Schlüssel...%RESET%
call :generate_secure_keys

REM Suche MT5-Installation
echo %BLUE%Suche MetaTrader 5 Installation...%RESET%
call :find_mt5_installation

echo %GREEN%✓%RESET% Konfiguration vorbereitet
echo.

echo %BLUE%Schritt 5: Datenbank initialisieren...%RESET%
echo [%date% %time%] Datenbank initialisieren >> "%LOG_FILE%"

REM SQLite-Datenbank erstellen
python -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all(); print('✓ Datenbank initialisiert')"
if %errorlevel% neq 0 (
    echo %YELLOW%Warnung: Datenbank-Initialisierung fehlgeschlagen. Das ist normal beim ersten Start.%RESET%
    echo [%date% %time%] Datenbank-Initialisierung fehlgeschlagen >> "%LOG_FILE%"
) else (
    echo %GREEN%✓%RESET% Datenbank initialisiert
)

REM Admin-Benutzer erstellen
echo %BLUE%Erstelle Admin-Benutzer...%RESET%
python -c "from app import create_app; from app.models import User, db; app = create_app(); app.app_context().push(); admin = User.query.filter_by(username='admin').first(); (admin and print('✓ Admin-Benutzer existiert bereits')) or (User(username='admin', email='admin@mt5gateway.com').set_password('admin123'), db.session.add(User.query.filter_by(username='admin').first()), db.session.commit(), print('✓ Admin-Benutzer erstellt: admin / admin123'))"
if %errorlevel% neq 0 (
    echo %YELLOW%Warnung: Admin-Benutzer konnte nicht erstellt werden.%RESET%
    echo [%date% %time%] Admin-Benutzer-Erstellung fehlgeschlagen >> "%LOG_FILE%"
) else (
    echo %GREEN%✓%RESET% Admin-Benutzer bereit
)

echo.

echo %BLUE%Schritt 6: Firewall-Regel konfigurieren...%RESET%
echo [%date% %time%] Firewall-Regel konfigurieren >> "%LOG_FILE%"

REM Prüfe bestehende Regel
netsh advfirewall firewall show rule name="%APP_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo %BLUE%Erstelle Firewall-Regel für Port %DEFAULT_PORT%...%RESET%
    netsh advfirewall firewall add rule name="%APP_NAME%" dir=in action=allow protocol=TCP localport=%DEFAULT_PORT%
    if %errorlevel% equ 0 (
        echo %GREEN%✓%RESET% Firewall-Regel erstellt
        echo [%date% %time%] Firewall-Regel erstellt >> "%LOG_FILE%"
    ) else (
        echo %YELLOW%Warnung: Firewall-Regel konnte nicht erstellt werden.%RESET%
        echo [%date% %time%] Firewall-Regel fehlgeschlagen >> "%LOG_FILE%"
    )
) else (
    echo %GREEN%✓%RESET% Firewall-Regel existiert bereits
)

echo.

echo %BLUE%Schritt 7: Windows-Service (optional)...%RESET%
echo [%date% %time%] Windows-Service prüfen >> "%LOG_FILE%"

REM Prüfe SERVICE_MODE in .env
findstr "SERVICE_MODE=true" "config\.env" >nul 2>&1
if %errorlevel% equ 0 (
    echo %BLUE%Service-Modus aktiviert. Installiere Windows-Service...%RESET%
    call :install_windows_service
) else (
    echo %GREEN%✓%RESET% Standard-Modus (kein Service)
)

echo.

echo %BLUE%Schritt 8: Erstelle Start-Skripte...%RESET%
echo [%date% %time%] Erstelle Start-Skripte >> "%LOG_FILE%"

REM Erstelle run_app.bat
call :create_run_script

REM Erstelle stop_app.bat
call :create_stop_script

echo %GREEN%✓%RESET% Start-Skripte erstellt
echo.

echo %GREEN%============================================================================%RESET%
echo %GREEN%  Installation erfolgreich abgeschlossen!%RESET%
echo %GREEN%============================================================================%RESET%
echo.
echo %BLUE%Nächste Schritte:%RESET%
echo   1. Bearbeiten Sie config\.env mit Ihren MT5-Zugangsdaten
echo   2. Starten Sie das Gateway mit scripts\run_app.bat
echo   3. Öffnen Sie http://localhost:%DEFAULT_PORT% im Browser
echo   4. Melden Sie sich mit admin / admin123 an
echo.
echo %BLUE%Wichtige Dateien:%RESET%
echo   • Konfiguration: config\.env
echo   • Logs: logs\
echo   • Datenbank: data\
echo   • Start: scripts\run_app.bat
echo   • Stop: scripts\stop_app.bat
echo.

echo [%date% %time%] Installation erfolgreich abgeschlossen >> "%LOG_FILE%"
exit /b 0

REM ============================================================================
REM Hilfsfunktionen
REM ============================================================================

:create_default_env
echo FLASK_ENV=production > "config\.env"
echo SECRET_KEY=change_me_to_secure_random_string_32_chars_min >> "config\.env"
echo API_PUBLIC_KEY=pub_xxxxx >> "config\.env"
echo API_SECRET_KEY=sec_xxxxx >> "config\.env"
echo ALLOWED_IPS=127.0.0.1,::1 >> "config\.env"
echo RATE_LIMIT_PER_MIN=60 >> "config\.env"
echo MT5_SERVER=YourBroker-Server >> "config\.env"
echo MT5_LOGIN=1234567 >> "config\.env"
echo MT5_PASSWORD=changeme >> "config\.env"
echo MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe >> "config\.env"
echo LICENSE_SERVER_URL=https://license.example.com >> "config\.env"
echo LICENSE_KEY= >> "config\.env"
echo TELEMETRY_OPTOUT=false >> "config\.env"
echo UI_ADMIN_PASSWORD=admin123 >> "config\.env"
echo PORT=%DEFAULT_PORT% >> "config\.env"
echo BIND=0.0.0.0 >> "config\.env"
echo DATABASE_URL=sqlite:///data/mt5_gateway.db >> "config\.env"
echo REDIS_URL=redis://localhost:6379/0 >> "config\.env"
echo LOG_LEVEL=INFO >> "config\.env"
echo LOG_FILE=logs/mt5_gateway.log >> "config\.env"
echo MAX_LOG_SIZE=10485760 >> "config\.env"
echo BACKUP_COUNT=5 >> "config\.env"
echo SERVICE_MODE=false >> "config\.env"
goto :eof

:generate_secure_keys
REM Generiere sichere Schlüssel mit PowerShell
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(32, 8)"') do set "SECRET_KEY=%%i"
for /f %%i in ('powershell -Command "'pub_' + [guid]::NewGuid().ToString('N').Substring(0, 16)"') do set "API_PUBLIC_KEY=%%i"
for /f %%i in ('powershell -Command "'sec_' + [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N').Substring(0, 16)"') do set "API_SECRET_KEY=%%i"
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(16, 4)"') do set "ADMIN_PASSWORD=%%i"

REM Aktualisiere .env mit sicheren Schlüsseln
powershell -Command "(Get-Content 'config\.env') -replace 'SECRET_KEY=change_me_to_secure_random_string_32_chars_min', 'SECRET_KEY=%SECRET_KEY%' | Set-Content 'config\.env'"
powershell -Command "(Get-Content 'config\.env') -replace 'API_PUBLIC_KEY=pub_xxxxx', 'API_PUBLIC_KEY=%API_PUBLIC_KEY%' | Set-Content 'config\.env'"
powershell -Command "(Get-Content 'config\.env') -replace 'API_SECRET_KEY=sec_xxxxx', 'API_SECRET_KEY=%API_SECRET_KEY%' | Set-Content 'config\.env'"
powershell -Command "(Get-Content 'config\.env') -replace 'UI_ADMIN_PASSWORD=admin123', 'UI_ADMIN_PASSWORD=%ADMIN_PASSWORD%' | Set-Content 'config\.env'"

echo %GREEN%✓%RESET% Sichere Schlüssel generiert
goto :eof

:find_mt5_installation
REM Suche MT5 in Standard-Verzeichnissen
set "MT5_FOUND="
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    set "MT5_FOUND=C:\Program Files\MetaTrader 5\terminal64.exe"
)
if exist "C:\Program Files (x86)\MetaTrader 5\terminal64.exe" (
    set "MT5_FOUND=C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
)

if defined MT5_FOUND (
    echo %GREEN%✓%RESET% MetaTrader 5 gefunden: !MT5_FOUND!
    powershell -Command "(Get-Content 'config\.env') -replace 'MT5_PATH=C:\\\\Program Files\\\\MetaTrader 5\\\\terminal64.exe', 'MT5_PATH=!MT5_FOUND:\=\\!' | Set-Content 'config\.env'"
) else (
    echo %YELLOW%Warnung: MetaTrader 5 nicht gefunden. Bitte MT5_PATH in config\.env manuell setzen.%RESET%
)
goto :eof

:install_windows_service
REM Windows-Service Installation (vereinfacht)
echo %BLUE%Installiere Windows-Service...%RESET%
REM Hier könnte NSSM oder sc.exe verwendet werden
echo %YELLOW%Service-Installation noch nicht implementiert.%RESET%
echo Verwenden Sie vorerst scripts\run_app.bat für den manuellen Start.
goto :eof

:create_run_script
echo @echo off > "scripts\run_app.bat"
echo REM MT5 Flask Gateway - Start Script >> "scripts\run_app.bat"
echo. >> "scripts\run_app.bat"
echo cd /d "%%~dp0\.." >> "scripts\run_app.bat"
echo. >> "scripts\run_app.bat"
echo REM Aktiviere venv >> "scripts\run_app.bat"
echo call "venv\Scripts\activate.bat" >> "scripts\run_app.bat"
echo if %%errorlevel%% neq 0 ( >> "scripts\run_app.bat"
echo     echo Fehler: Virtuelle Umgebung konnte nicht aktiviert werden. >> "scripts\run_app.bat"
echo     pause >> "scripts\run_app.bat"
echo     exit /b 1 >> "scripts\run_app.bat"
echo ^) >> "scripts\run_app.bat"
echo. >> "scripts\run_app.bat"
echo REM Prüfe .env >> "scripts\run_app.bat"
echo if not exist "config\.env" ( >> "scripts\run_app.bat"
echo     echo Fehler: Konfigurationsdatei config\.env nicht gefunden. >> "scripts\run_app.bat"
echo     pause >> "scripts\run_app.bat"
echo     exit /b 1 >> "scripts\run_app.bat"
echo ^) >> "scripts\run_app.bat"
echo. >> "scripts\run_app.bat"
echo echo MT5 Flask Gateway wird gestartet... >> "scripts\run_app.bat"
echo echo. >> "scripts\run_app.bat"
echo echo Server läuft auf: http://localhost:8080 >> "scripts\run_app.bat"
echo echo Drücken Sie Ctrl+C zum Beenden >> "scripts\run_app.bat"
echo echo. >> "scripts\run_app.bat"
echo. >> "scripts\run_app.bat"
echo REM Starte App >> "scripts\run_app.bat"
echo python app.py >> "scripts\run_app.bat"
echo. >> "scripts\run_app.bat"
echo pause >> "scripts\run_app.bat"
goto :eof

:create_stop_script
echo @echo off > "scripts\stop_app.bat"
echo REM MT5 Flask Gateway - Stop Script >> "scripts\stop_app.bat"
echo. >> "scripts\stop_app.bat"
echo echo MT5 Flask Gateway wird gestoppt... >> "scripts\stop_app.bat"
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq MT5*" 2^>nul >> "scripts\stop_app.bat"
echo taskkill /f /im MT5_Flask_Gateway.exe 2^>nul >> "scripts\stop_app.bat"
echo echo Gateway gestoppt. >> "scripts\stop_app.bat"
echo timeout /t 3 /nobreak ^>nul >> "scripts\stop_app.bat"
goto :eof