@echo off
REM ============================================================================
REM MT5 Flask Gateway - One-Click Bootstrap Installer
REM Windows 10/11 x64 - Produktionsreifes Setup
REM ============================================================================

setlocal enabledelayedexpansion

REM App-Konfiguration
set "APP_NAME=MT5 Flask Gateway"
set "APP_VERSION=1.0.0"
set "APP_DIR=%PROGRAMDATA%\MT5FlaskGateway"
set "PORT=8080"
set "LOG_FILE=%APP_DIR%\logs\bootstrap.log"

REM Farben für bessere UX
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

echo %BLUE%============================================================================%RESET%
echo %BLUE%  %APP_NAME% v%APP_VERSION% - One-Click Bootstrap Installer%RESET%
echo %BLUE%============================================================================%RESET%
echo.

REM Prüfe Admin-Rechte
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%Admin-Rechte erforderlich. Starte mit erhöhten Rechten...%RESET%
    echo.
    
    REM Self-elevate via PowerShell
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs -ArgumentList 'elevated'"
    if %errorlevel% neq 0 (
        echo %RED%Fehler: Konnte nicht mit Admin-Rechten starten.%RESET%
        echo Bitte Rechtsklick auf diese Datei und "Als Administrator ausführen" wählen.
        pause
        exit /b 1
    )
    exit /b 0
)

REM Erstelle App-Verzeichnis und Logs
if not exist "%APP_DIR%" mkdir "%APP_DIR%"
if not exist "%APP_DIR%\logs" mkdir "%APP_DIR%\logs"
if not exist "%APP_DIR%\data" mkdir "%APP_DIR%\data"
if not exist "%APP_DIR%\artifacts" mkdir "%APP_DIR%\artifacts"

REM Logging starten
echo [%date% %time%] Bootstrap gestartet - %APP_NAME% v%APP_VERSION% > "%LOG_FILE%"
echo [%date% %time%] App-Verzeichnis: %APP_DIR% >> "%LOG_FILE%"

echo %GREEN%✓%RESET% Admin-Rechte bestätigt
echo %GREEN%✓%RESET% App-Verzeichnis erstellt: %APP_DIR%
echo.

REM Prüfe ob bereits installiert
if exist "%APP_DIR%\venv\Scripts\activate.bat" (
    echo %YELLOW%Warnung: %APP_NAME% scheint bereits installiert zu sein.%RESET%
    echo.
    set /p "REINSTALL=Möchten Sie eine Neuinstallation durchführen? (j/N): "
    if /i not "!REINSTALL!"=="j" (
        echo %BLUE%Starte vorhandene Installation...%RESET%
        goto :start_existing
    )
    echo %YELLOW%Führe Neuinstallation durch...%RESET%
    echo.
)

REM Kopiere Projekt-Dateien nach %PROGRAMDATA%
echo %BLUE%Kopiere Projekt-Dateien...%RESET%
echo [%date% %time%] Kopiere Projekt-Dateien nach %APP_DIR% >> "%LOG_FILE%"

REM Ermittle aktuelles Verzeichnis (Repo-Root)
set "REPO_DIR=%~dp0"
if "%REPO_DIR:~-1%"=="\" set "REPO_DIR=%REPO_DIR:~0,-1%"

REM Kopiere alle notwendigen Dateien
robocopy "%REPO_DIR%" "%APP_DIR%" /E /XD venv __pycache__ .git .github build dist /XF *.log *.tmp /R:3 /W:1 /NFL /NDL /NJH /NJS >nul 2>&1

if %errorlevel% gtr 3 (
    echo %RED%Fehler beim Kopieren der Dateien.%RESET%
    echo [%date% %time%] Fehler beim Kopieren der Dateien >> "%LOG_FILE%"
    goto :error_exit
)

echo %GREEN%✓%RESET% Projekt-Dateien kopiert
echo.

REM Führe Installation aus
echo %BLUE%Starte Installation...%RESET%
echo [%date% %time%] Starte install_production.bat >> "%LOG_FILE%"

cd /d "%APP_DIR%"
call "scripts\install_production.bat"
set "INSTALL_RESULT=%errorlevel%"

if %INSTALL_RESULT% neq 0 (
    echo %RED%Fehler bei der Installation! (Exit-Code: %INSTALL_RESULT%)%RESET%
    echo [%date% %time%] Installation fehlgeschlagen mit Exit-Code %INSTALL_RESULT% >> "%LOG_FILE%"
    goto :error_exit
)

echo %GREEN%✓%RESET% Installation erfolgreich abgeschlossen
echo.

REM Erstelle Desktop-Verknüpfung
echo %BLUE%Erstelle Desktop-Verknüpfung...%RESET%
echo [%date% %time%] Erstelle Desktop-Verknüpfung >> "%LOG_FILE%"

powershell -ExecutionPolicy Bypass -File "scripts\create_shortcut.ps1" -Target "%APP_DIR%\scripts\run_app.bat" -ShortcutPath "%USERPROFILE%\Desktop\MT5 Flask Gateway.lnk" -WorkingDirectory "%APP_DIR%" -IconPath "%APP_DIR%\app\ui\static\img\icon.ico"

if %errorlevel% neq 0 (
    echo %YELLOW%Warnung: Desktop-Verknüpfung konnte nicht erstellt werden.%RESET%
    echo [%date% %time%] Warnung: Desktop-Verknüpfung konnte nicht erstellt werden >> "%LOG_FILE%"
) else (
    echo %GREEN%✓%RESET% Desktop-Verknüpfung erstellt
)

echo.

REM Starte Anwendung
echo %BLUE%Starte %APP_NAME%...%RESET%
echo [%date% %time%] Starte Anwendung >> "%LOG_FILE%"

REM Prüfe ob EXE vorhanden ist
if exist "%APP_DIR%\artifacts\MT5_Flask_Gateway.exe" (
    echo %GREEN%✓%RESET% Verwende kompilierte EXE-Version
    start "" "%APP_DIR%\artifacts\MT5_Flask_Gateway.exe"
) else (
    echo %GREEN%✓%RESET% Verwende Python-Version
    start "" "scripts\run_app.bat"
)

REM Warte kurz, dann öffne Browser
echo %BLUE%Öffne Web-UI...%RESET%
timeout /t 3 /nobreak >nul

REM Prüfe ob Port verfügbar ist
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:%PORT%/health' -TimeoutSec 5; if ($response.StatusCode -eq 200) { exit 0 } } catch { exit 1 }" >nul 2>&1

if %errorlevel% equ 0 (
    echo %GREEN%✓%RESET% Server läuft - öffne Browser
    start "" "http://localhost:%PORT%"
) else (
    echo %YELLOW%Warnung: Server antwortet noch nicht. Öffne Browser manuell...%RESET%
    start "" "http://localhost:%PORT%"
)

echo.
echo %GREEN%============================================================================%RESET%
echo %GREEN%  %APP_NAME% erfolgreich installiert und gestartet!%RESET%
echo %GREEN%============================================================================%RESET%
echo.
echo %BLUE%Zugriff:%RESET%
echo   • Web-UI: http://localhost:%PORT%
echo   • Standard-Login: admin / admin123
echo   • Desktop-Verknüpfung: MT5 Flask Gateway.lnk
echo.
echo %BLUE%Verzeichnisse:%RESET%
echo   • App-Verzeichnis: %APP_DIR%
echo   • Logs: %APP_DIR%\logs
echo   • Konfiguration: %APP_DIR%\config\.env
echo.
echo %BLUE%Support:%RESET%
echo   • E-Mail: support@mt5gateway.com
echo   • Dokumentation: https://docs.mt5gateway.com
echo.

echo [%date% %time%] Bootstrap erfolgreich abgeschlossen >> "%LOG_FILE%"

REM Verstecke Konsolen-Fenster nach 10 Sekunden
timeout /t 10 /nobreak >nul
exit /b 0

:start_existing
echo %BLUE%Starte vorhandene Installation...%RESET%
cd /d "%APP_DIR%"

if exist "artifacts\MT5_Flask_Gateway.exe" (
    start "" "artifacts\MT5_Flask_Gateway.exe"
) else (
    start "" "scripts\run_app.bat"
)

timeout /t 3 /nobreak >nul
start "" "http://localhost:%PORT%"
echo %GREEN%✓%RESET% %APP_NAME% gestartet
timeout /t 5 /nobreak >nul
exit /b 0

:error_exit
echo.
echo %RED%============================================================================%RESET%
echo %RED%  Installation fehlgeschlagen!%RESET%
echo %RED%============================================================================%RESET%
echo.
echo %YELLOW%Fehlerbehebung:%RESET%
echo   1. Prüfen Sie die Log-Datei: %LOG_FILE%
echo   2. Stellen Sie sicher, dass Sie Admin-Rechte haben
echo   3. Prüfen Sie Ihre Internetverbindung (für Python-Download)
echo   4. Kontaktieren Sie den Support: support@mt5gateway.com
echo.

REM Erstelle Support-Bundle
echo %BLUE%Erstelle Support-Bundle...%RESET%
set "SUPPORT_BUNDLE=%APP_DIR%\logs\support-bundle-%date:~-4,4%%date:~-10,2%%date:~-7,2%-%time:~0,2%%time:~3,2%%time:~6,2%.zip"
set "SUPPORT_BUNDLE=%SUPPORT_BUNDLE: =0%"

powershell -Command "Compress-Archive -Path '%APP_DIR%\logs\*' -DestinationPath '%SUPPORT_BUNDLE%' -Force" >nul 2>&1

if exist "%SUPPORT_BUNDLE%" (
    echo %GREEN%✓%RESET% Support-Bundle erstellt: %SUPPORT_BUNDLE%
    echo   Senden Sie diese Datei an den Support für weitere Hilfe.
) else (
    echo %YELLOW%Warnung: Support-Bundle konnte nicht erstellt werden.%RESET%
)

echo.
echo [%date% %time%] Bootstrap fehlgeschlagen >> "%LOG_FILE%"
pause
exit /b 1
