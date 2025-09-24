@echo off
REM ============================================================================
REM MT5 Flask Gateway - NSIS Installer Builder
REM Windows Batch Script für Installer-Erstellung
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
set "NSIS_SCRIPT=installers\nsis\mt5_flask_gateway.nsi"
set "OUTPUT_NAME=MT5_Flask_Gateway_Setup.exe"

echo %BLUE%============================================================================%RESET%
echo %BLUE%  %APP_NAME% v%APP_VERSION% - NSIS Installer Builder%RESET%
echo %BLUE%============================================================================%RESET%
echo.

REM Log-Datei
set "LOG_FILE=%CD%\logs\installer_build.log"
if not exist "logs" mkdir logs

echo [%date% %time%] Installer-Build gestartet > "%LOG_FILE%"

REM Schritt 1: NSIS-Installation prüfen
echo %BLUE%Schritt 1: Prüfe NSIS-Installation...%RESET%
echo [%date% %time%] Prüfe NSIS-Installation >> "%LOG_FILE%"

REM Suche NSIS in Standard-Pfaden
set "NSIS_FOUND="
set "NSIS_PATH="

REM Standard-Installationspfade prüfen
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set "NSIS_PATH=C:\Program Files (x86)\NSIS\makensis.exe"
    set "NSIS_FOUND=1"
)
if exist "C:\Program Files\NSIS\makensis.exe" (
    set "NSIS_PATH=C:\Program Files\NSIS\makensis.exe"
    set "NSIS_FOUND=1"
)

REM PATH prüfen
if not defined NSIS_FOUND (
    makensis /VERSION >nul 2>&1
    if !errorlevel! equ 0 (
        set "NSIS_PATH=makensis"
        set "NSIS_FOUND=1"
    )
)

if not defined NSIS_FOUND (
    echo %RED%Fehler: NSIS nicht gefunden.%RESET%
    echo.
    echo %YELLOW%NSIS muss installiert werden:%RESET%
    echo   1. Besuchen Sie: https://nsis.sourceforge.io/Download
    echo   2. Laden Sie die neueste Version herunter
    echo   3. Installieren Sie NSIS
    echo   4. Führen Sie dieses Skript erneut aus
    echo.
    echo %BLUE%Automatische Installation versuchen? (erfordert Chocolatey)%RESET%
    set /p "INSTALL_NSIS=NSIS über Chocolatey installieren? (j/N): "
    if /i "!INSTALL_NSIS!"=="j" (
        echo %BLUE%Installiere NSIS über Chocolatey...%RESET%
        choco install nsis -y
        if !errorlevel! equ 0 (
            echo %GREEN%✓%RESET% NSIS erfolgreich installiert
            set "NSIS_PATH=makensis"
            set "NSIS_FOUND=1"
        ) else (
            echo %RED%Chocolatey-Installation fehlgeschlagen.%RESET%
            echo [%date% %time%] NSIS-Installation via Chocolatey fehlgeschlagen >> "%LOG_FILE%"
            pause
            exit /b 1
        )
    ) else (
        echo [%date% %time%] NSIS nicht gefunden und Installation abgelehnt >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

echo %GREEN%✓%RESET% NSIS gefunden: !NSIS_PATH!
echo [%date% %time%] NSIS gefunden: !NSIS_PATH! >> "%LOG_FILE%"

REM Schritt 2: Build-Umgebung prüfen
echo %BLUE%Schritt 2: Prüfe Build-Umgebung...%RESET%
echo [%date% %time%] Prüfe Build-Umgebung >> "%LOG_FILE%"

REM NSIS-Skript prüfen
if not exist "%NSIS_SCRIPT%" (
    echo %RED%Fehler: NSIS-Skript nicht gefunden: %NSIS_SCRIPT%%RESET%
    echo [%date% %time%] NSIS-Skript nicht gefunden: %NSIS_SCRIPT% >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo %GREEN%✓%RESET% NSIS-Skript gefunden: %NSIS_SCRIPT%

REM Prüfe ob EXE vorhanden ist
if not exist "dist\MT5_Flask_Gateway\MT5_Flask_Gateway.exe" (
    echo %YELLOW%Warnung: Kompilierte EXE nicht gefunden.%RESET%
    echo.
    set /p "BUILD_EXE=Soll zuerst die EXE erstellt werden? (j/N): "
    if /i "!BUILD_EXE!"=="j" (
        echo %BLUE%Erstelle EXE mit PyInstaller...%RESET%
        call scripts\build_exe.bat
        if !errorlevel! neq 0 (
            echo %RED%EXE-Build fehlgeschlagen.%RESET%
            echo [%date% %time%] EXE-Build fehlgeschlagen >> "%LOG_FILE%"
            pause
            exit /b 1
        )
    ) else (
        echo %YELLOW%Installer wird ohne EXE erstellt (nur Skripte).%RESET%
    )
)

if exist "dist\MT5_Flask_Gateway\MT5_Flask_Gateway.exe" (
    echo %GREEN%✓%RESET% EXE gefunden: dist\MT5_Flask_Gateway\MT5_Flask_Gateway.exe
) else (
    echo %YELLOW%⚠%RESET% Kein EXE gefunden, verwende Skript-Modus
)

echo [%date% %time%] Build-Umgebung geprüft >> "%LOG_FILE%"

REM Schritt 3: Vorbereitung
echo %BLUE%Schritt 3: Bereite Build vor...%RESET%
echo [%date% %time%] Bereite Build vor >> "%LOG_FILE%"

REM Erstelle temporäres Build-Verzeichnis
set "BUILD_TEMP=%TEMP%\MT5Gateway_Build_%RANDOM%"
if exist "%BUILD_TEMP%" rmdir /s /q "%BUILD_TEMP%"
mkdir "%BUILD_TEMP%"

echo %GREEN%✓%RESET% Temporäres Build-Verzeichnis: %BUILD_TEMP%

REM Kopiere notwendige Dateien
echo %BLUE%Kopiere Build-Dateien...%RESET%

REM Haupt-EXE oder Skripte
if exist "dist\MT5_Flask_Gateway" (
    robocopy "dist\MT5_Flask_Gateway" "%BUILD_TEMP%\dist\MT5_Flask_Gateway" /E /R:3 /W:1 /NFL /NDL /NJH /NJS >nul
    echo %GREEN%✓%RESET% EXE-Dateien kopiert
) else (
    REM Kopiere Python-Skripte für Installer
    mkdir "%BUILD_TEMP%\app_files"
    robocopy "%CD%" "%BUILD_TEMP%\app_files" /E /XD venv __pycache__ .git .github build dist node_modules /XF *.log *.tmp /R:3 /W:1 /NFL /NDL /NJH /NJS >nul
    echo %GREEN%✓%RESET% App-Dateien kopiert
)

REM Kopiere Installer-Skript und Assets
robocopy "installers" "%BUILD_TEMP%\installers" /E /R:3 /W:1 /NFL /NDL /NJH /NJS >nul
if exist "LICENSE" copy "LICENSE" "%BUILD_TEMP%\" >nul
if exist "README.md" copy "README.md" "%BUILD_TEMP%\" >nul

echo %GREEN%✓%RESET% Build-Dateien vorbereitet
echo [%date% %time%] Build-Dateien vorbereitet >> "%LOG_FILE%"

REM Schritt 4: NSIS-Variablen setzen
echo %BLUE%Schritt 4: Konfiguriere NSIS-Build...%RESET%
echo [%date% %time%] Konfiguriere NSIS-Build >> "%LOG_FILE%"

REM Erstelle temporäres NSIS-Skript mit aktuellen Pfaden
set "TEMP_NSIS=%BUILD_TEMP%\build_script.nsi"

REM NSIS-Skript anpassen für aktuelle Pfade
powershell -Command "(Get-Content '%NSIS_SCRIPT%') -replace 'dist\\MT5_Flask_Gateway\\', '%BUILD_TEMP%\dist\MT5_Flask_Gateway\' | Set-Content '%TEMP_NSIS%'"

echo %GREEN%✓%RESET% NSIS-Konfiguration erstellt
echo [%date% %time%] NSIS-Konfiguration erstellt >> "%LOG_FILE%"

REM Schritt 5: Installer erstellen
echo %BLUE%Schritt 5: Erstelle Installer...%RESET%
echo [%date% %time%] Starte NSIS-Kompilierung >> "%LOG_FILE%"

REM Wechsle ins Build-Verzeichnis
pushd "%BUILD_TEMP%"

REM Führe NSIS aus
echo %BLUE%NSIS-Kompilierung läuft...%RESET%
"%NSIS_PATH%" "%TEMP_NSIS%"
set "NSIS_RESULT=%errorlevel%"

popd

if %NSIS_RESULT% neq 0 (
    echo %RED%Fehler bei NSIS-Kompilierung (Exit-Code: %NSIS_RESULT%).%RESET%
    echo [%date% %time%] NSIS-Kompilierung fehlgeschlagen mit Exit-Code %NSIS_RESULT% >> "%LOG_FILE%"
    echo.
    echo %YELLOW%Mögliche Ursachen:%RESET%
    echo   • NSIS-Skript-Fehler
    echo   • Fehlende Dateien
    echo   • Pfad-Probleme
    echo.
    echo %BLUE%Debug-Informationen:%RESET%
    echo   • Build-Verzeichnis: %BUILD_TEMP%
    echo   • NSIS-Skript: %TEMP_NSIS%
    echo   • Log-Datei: %LOG_FILE%
    echo.
    pause
    exit /b 1
)

echo %GREEN%✓%RESET% NSIS-Kompilierung erfolgreich

REM Schritt 6: Installer kopieren und verifizieren
echo %BLUE%Schritt 6: Finalisiere Installer...%RESET%
echo [%date% %time%] Finalisiere Installer >> "%LOG_FILE%"

REM Suche erstellten Installer
set "INSTALLER_SOURCE="
if exist "%BUILD_TEMP%\%OUTPUT_NAME%" (
    set "INSTALLER_SOURCE=%BUILD_TEMP%\%OUTPUT_NAME%"
)
if exist "%BUILD_TEMP%\installers\%OUTPUT_NAME%" (
    set "INSTALLER_SOURCE=%BUILD_TEMP%\installers\%OUTPUT_NAME%"
)

if not defined INSTALLER_SOURCE (
    echo %RED%Fehler: Installer-Datei nicht gefunden.%RESET%
    echo [%date% %time%] Installer-Datei nicht gefunden >> "%LOG_FILE%"
    echo.
    echo %BLUE%Suche in:%RESET%
    dir "%BUILD_TEMP%\*.exe" /s
    pause
    exit /b 1
)

REM Kopiere Installer ins Hauptverzeichnis
copy "!INSTALLER_SOURCE!" "%CD%\%OUTPUT_NAME%" >nul
if %errorlevel% neq 0 (
    echo %RED%Fehler beim Kopieren des Installers.%RESET%
    echo [%date% %time%] Fehler beim Kopieren des Installers >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Verifiziere Installer
if exist "%CD%\%OUTPUT_NAME%" (
    for %%F in ("%CD%\%OUTPUT_NAME%") do set "INSTALLER_SIZE=%%~zF"
    echo %GREEN%✓%RESET% Installer erstellt: %OUTPUT_NAME%
    echo %GREEN%✓%RESET% Größe: !INSTALLER_SIZE! Bytes
    echo [%date% %time%] Installer erfolgreich erstellt: %OUTPUT_NAME% (!INSTALLER_SIZE! Bytes) >> "%LOG_FILE%"
) else (
    echo %RED%Fehler: Installer-Verifikation fehlgeschlagen.%RESET%
    echo [%date% %time%] Installer-Verifikation fehlgeschlagen >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Schritt 7: Cleanup
echo %BLUE%Schritt 7: Bereinige temporäre Dateien...%RESET%
echo [%date% %time%] Bereinige temporäre Dateien >> "%LOG_FILE%"

REM Lösche temporäres Build-Verzeichnis
if exist "%BUILD_TEMP%" (
    rmdir /s /q "%BUILD_TEMP%" >nul 2>&1
    echo %GREEN%✓%RESET% Temporäre Dateien bereinigt
)

echo.
echo %GREEN%============================================================================%RESET%
echo %GREEN%  Installer erfolgreich erstellt!%RESET%
echo %GREEN%============================================================================%RESET%
echo.
echo %BLUE%Installer-Informationen:%RESET%
echo   • Datei: %OUTPUT_NAME%
echo   • Größe: !INSTALLER_SIZE! Bytes
echo   • Pfad: %CD%\%OUTPUT_NAME%
echo.
echo %BLUE%Nächste Schritte:%RESET%
echo   1. Testen Sie den Installer auf einem sauberen System
echo   2. Digitale Signierung (optional)
echo   3. Verteilung an Benutzer
echo.
echo %BLUE%Test-Empfehlung:%RESET%
echo   • Verwenden Sie eine Windows-VM für Tests
echo   • Testen Sie Installation und Deinstallation
echo   • Prüfen Sie alle Verknüpfungen und Features
echo.

echo [%date% %time%] Installer-Build erfolgreich abgeschlossen >> "%LOG_FILE%"

pause
exit /b 0
