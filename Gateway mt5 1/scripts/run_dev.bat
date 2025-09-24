@echo off
REM MT5 Flask Gateway - Development Server
REM Windows Batch Script für Entwicklungsumgebung

echo ========================================
echo MT5 Flask Gateway - Development Server
echo ========================================
echo.

REM Prüfe ob virtuelle Umgebung existiert
if not exist "venv" (
    echo FEHLER: Virtuelle Umgebung nicht gefunden.
    echo Führen Sie zuerst install_production.bat aus.
    pause
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo FEHLER: Virtuelle Umgebung konnte nicht aktiviert werden.
    pause
    exit /b 1
)

REM Setze Umgebungsvariablen für Entwicklung
set FLASK_ENV=development
set FLASK_DEBUG=1
set PYTHONPATH=%CD%

REM Starte Entwicklungsserver
echo Starte Entwicklungsserver...
echo.
echo Server läuft auf: http://localhost:8080
echo Drücken Sie Ctrl+C zum Beenden
echo.

python app.py

pause
