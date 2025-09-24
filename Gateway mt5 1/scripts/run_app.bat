@echo off
REM ============================================================================
REM MT5 Flask Gateway - Application Runner
REM Windows Batch Script für Anwendungsstart mit Fehlerbehandlung
REM ============================================================================

setlocal enabledelayedexpansion

REM Farben für bessere UX
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

REM App-Konfiguration
set "APP_NAME=MT5 Flask Gateway"
set "APP_VERSION=1.0.0"
set "DEFAULT_PORT=8080"

REM Titel setzen
title %APP_NAME% v%APP_VERSION%

echo %BLUE%============================================================================%RESET%
echo %BLUE%  %APP_NAME% v%APP_VERSION% - Application Runner%RESET%
echo %BLUE%============================================================================%RESET%
echo.

REM Wechsle ins App-Verzeichnis (Parent von scripts)
cd /d "%~dp0\.."

REM Log-Datei
set "LOG_FILE=%CD%\logs\run.log"
if not exist "logs" mkdir logs

echo [%date% %time%] App-Start initiiert > "%LOG_FILE%"
echo [%date% %time%] Arbeitsverzeichnis: %CD% >> "%LOG_FILE%"

REM Schritt 1: Umgebung prüfen
echo %BLUE%Schritt 1: Prüfe Umgebung...%RESET%

REM Prüfe virtuelle Umgebung
if not exist "venv\Scripts\activate.bat" (
    echo %RED%Fehler: Virtuelle Umgebung nicht gefunden.%RESET%
    echo Führen Sie zuerst die Installation aus:
    echo   • Start-MT5-Flask-Gateway.cmd (für Neuinstallation)
    echo   • scripts\install_production.bat (für manuelle Installation)
    echo.
    echo [%date% %time%] Fehler: venv nicht gefunden >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo %GREEN%✓%RESET% Virtuelle Umgebung gefunden
echo [%date% %time%] venv gefunden >> "%LOG_FILE%"

REM Aktiviere virtuelle Umgebung
echo %BLUE%Aktiviere virtuelle Umgebung...%RESET%
call "venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo %RED%Fehler: Virtuelle Umgebung konnte nicht aktiviert werden.%RESET%
    echo [%date% %time%] venv-Aktivierung fehlgeschlagen >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo %GREEN%✓%RESET% Virtuelle Umgebung aktiviert
echo [%date% %time%] venv aktiviert >> "%LOG_FILE%"

REM Schritt 2: Konfiguration prüfen
echo %BLUE%Schritt 2: Prüfe Konfiguration...%RESET%

REM Prüfe .env-Datei
if not exist "config\.env" (
    echo %YELLOW%Warnung: Konfigurationsdatei config\.env nicht gefunden.%RESET%
    echo.
    if exist "env.example" (
        echo Erstelle Standard-Konfiguration aus env.example...
        if not exist "config" mkdir config
        copy "env.example" "config\.env" >nul
        echo %GREEN%✓%RESET% Standard-Konfiguration erstellt
        echo.
        echo %YELLOW%WICHTIG: Bitte bearbeiten Sie config\.env mit Ihren MT5-Zugangsdaten!%RESET%
        echo.
        set /p "EDIT_CONFIG=Möchten Sie die Konfiguration jetzt bearbeiten? (j/N): "
        if /i "!EDIT_CONFIG!"=="j" (
            start notepad "config\.env"
            echo %BLUE%Warten auf Konfiguration...%RESET%
            pause
        )
    ) else (
        echo %RED%Fehler: Weder config\.env noch env.example gefunden.%RESET%
        echo [%date% %time%] Keine Konfigurationsdateien gefunden >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

echo %GREEN%✓%RESET% Konfigurationsdatei vorhanden
echo [%date% %time%] Konfiguration gefunden >> "%LOG_FILE%"

REM Lade Port aus .env
for /f "tokens=2 delims==" %%i in ('findstr "^PORT=" "config\.env" 2^>nul') do set "PORT=%%i"
if "!PORT!"=="" set "PORT=%DEFAULT_PORT%"

echo %GREEN%✓%RESET% Port konfiguriert: !PORT!

REM Schritt 3: Abhängigkeiten prüfen
echo %BLUE%Schritt 3: Prüfe Python-Abhängigkeiten...%RESET%

REM Teste kritische Module
python -c "import flask, MetaTrader5, pydantic" >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%Warnung: Einige Abhängigkeiten fehlen. Installiere...%RESET%
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo %RED%Fehler: Abhängigkeiten konnten nicht installiert werden.%RESET%
        echo [%date% %time%] pip install fehlgeschlagen >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

echo %GREEN%✓%RESET% Python-Abhängigkeiten verfügbar
echo [%date% %time%] Abhängigkeiten geprüft >> "%LOG_FILE%"

REM Schritt 4: Port-Verfügbarkeit prüfen
echo %BLUE%Schritt 4: Prüfe Port-Verfügbarkeit...%RESET%

REM Prüfe ob Port belegt ist
netstat -an | findstr ":!PORT!" >nul 2>&1
if %errorlevel% equ 0 (
    echo %YELLOW%Warnung: Port !PORT! ist bereits belegt.%RESET%
    echo.
    echo Aktive Verbindungen auf Port !PORT!:
    netstat -an | findstr ":!PORT!"
    echo.
    set /p "CONTINUE=Trotzdem fortfahren? (j/N): "
    if /i not "!CONTINUE!"=="j" (
        echo %BLUE%Start abgebrochen.%RESET%
        echo [%date% %time%] Start wegen Port-Konflikt abgebrochen >> "%LOG_FILE%"
        pause
        exit /b 0
    )
)

echo %GREEN%✓%RESET% Port !PORT! verfügbar
echo [%date% %time%] Port !PORT! verfügbar >> "%LOG_FILE%"

REM Schritt 5: Lizenz prüfen (optional)
echo %BLUE%Schritt 5: Prüfe Lizenz-Status...%RESET%

python -c "from app.services.licensing import get_license_manager; lm = get_license_manager(); print('✓ Lizenz gültig' if lm and lm.is_licensed() else '⚠ Trial-Modus')" 2>nul
if %errorlevel% neq 0 (
    echo %YELLOW%⚠ Lizenz-Prüfung nicht verfügbar (normal bei erstem Start)%RESET%
) else (
    echo %GREEN%✓%RESET% Lizenz-Status geprüft
)

echo [%date% %time%] Lizenz-Status geprüft >> "%LOG_FILE%"

REM Schritt 6: Anwendung starten
echo.
echo %GREEN%============================================================================%RESET%
echo %GREEN%  Starte %APP_NAME%...%RESET%
echo %GREEN%============================================================================%RESET%
echo.

echo %BLUE%Server-Informationen:%RESET%
echo   • URL: http://localhost:!PORT!
echo   • Port: !PORT!
echo   • Umgebung: Produktion
echo   • Log-Datei: %LOG_FILE%
echo.

echo %BLUE%Standard-Login:%RESET%
echo   • Benutzername: admin
echo   • Passwort: admin123
echo   • (Passwort in config\.env konfigurierbar)
echo.

echo %BLUE%Kontrolle:%RESET%
echo   • Strg+C: Server beenden
echo   • scripts\stop_app.bat: Externes Beenden
echo.

echo %YELLOW%Starte Server...%RESET%
echo [%date% %time%] Server-Start initiiert >> "%LOG_FILE%"

REM Browser nach kurzer Verzögerung öffnen (Hintergrund)
start /b powershell -WindowStyle Hidden -Command "Start-Sleep 5; Start-Process 'http://localhost:!PORT!'" >nul 2>&1

REM Starte Flask-App
python app.py --host 0.0.0.0 --port !PORT!
set "EXIT_CODE=%errorlevel%"

echo.
echo [%date% %time%] Server beendet mit Exit-Code %EXIT_CODE% >> "%LOG_FILE%"

if %EXIT_CODE% neq 0 (
    echo %RED%============================================================================%RESET%
    echo %RED%  Server unerwartet beendet (Exit-Code: %EXIT_CODE%)%RESET%
    echo %RED%============================================================================%RESET%
    echo.
    echo %YELLOW%Mögliche Ursachen:%RESET%
    echo   • Port-Konflikt
    echo   • Konfigurationsfehler in config\.env
    echo   • Fehlende MT5-Installation
    echo   • Python-Fehler
    echo.
    echo %BLUE%Fehlerbehebung:%RESET%
    echo   • Prüfen Sie die Log-Datei: %LOG_FILE%
    echo   • Überprüfen Sie config\.env
    echo   • Kontaktieren Sie den Support: support@mt5gateway.com
    echo.
) else (
    echo %GREEN%============================================================================%RESET%
    echo %GREEN%  Server ordnungsgemäß beendet%RESET%
    echo %GREEN%============================================================================%RESET%
    echo.
    echo %BLUE%Vielen Dank für die Nutzung von %APP_NAME%!%RESET%
    echo.
)

echo Fenster schließt sich in 10 Sekunden...
timeout /t 10 /nobreak >nul
exit /b %EXIT_CODE%
