@echo off
REM MT5 Flask Gateway - Build EXE Script
REM Windows Batch Script für PyInstaller Build

echo ========================================
echo MT5 Flask Gateway - Build EXE
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

REM Installiere PyInstaller falls nicht vorhanden
echo Installiere PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo FEHLER: PyInstaller konnte nicht installiert werden.
    pause
    exit /b 1
)

REM Erstelle Build-Verzeichnis
if not exist "build" mkdir build
if not exist "dist" mkdir dist

REM Erstelle PyInstaller Spec-Datei
echo Erstelle PyInstaller Spec-Datei...
echo # -*- mode: python ; coding: utf-8 -*- > mt5_gateway.spec
echo. >> mt5_gateway.spec
echo block_cipher = None >> mt5_gateway.spec
echo. >> mt5_gateway.spec
echo a = Analysis( >> mt5_gateway.spec
echo     ['app.py'], >> mt5_gateway.spec
echo     pathex=[], >> mt5_gateway.spec
echo     binaries=[], >> mt5_gateway.spec
echo     datas=[ >> mt5_gateway.spec
echo         ('app/ui/templates', 'app/ui/templates'), >> mt5_gateway.spec
echo         ('app/ui/static', 'app/ui/static'), >> mt5_gateway.spec
echo         ('env.example', '.'), >> mt5_gateway.spec
echo     ], >> mt5_gateway.spec
echo     hiddenimports=[ >> mt5_gateway.spec
echo         'MetaTrader5', >> mt5_gateway.spec
echo         'flask', >> mt5_gateway.spec
echo         'sqlalchemy', >> mt5_gateway.spec
echo         'redis', >> mt5_gateway.spec
echo         'stripe', >> mt5_gateway.spec
echo         'pydantic', >> mt5_gateway.spec
echo         'marshmallow', >> mt5_gateway.spec
echo         'cryptography', >> mt5_gateway.spec
echo         'psutil', >> mt5_gateway.spec
echo     ], >> mt5_gateway.spec
echo     hookspath=[], >> mt5_gateway.spec
echo     hooksconfig={}, >> mt5_gateway.spec
echo     runtime_hooks=[], >> mt5_gateway.spec
echo     excludes=[], >> mt5_gateway.spec
echo     win_no_prefer_redirects=False, >> mt5_gateway.spec
echo     win_private_assemblies=False, >> mt5_gateway.spec
echo     cipher=block_cipher, >> mt5_gateway.spec
echo     noarchive=False, >> mt5_gateway.spec
echo ^) >> mt5_gateway.spec
echo. >> mt5_gateway.spec
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher^) >> mt5_gateway.spec
echo. >> mt5_gateway.spec
echo exe = EXE( >> mt5_gateway.spec
echo     pyz, >> mt5_gateway.spec
echo     a.scripts, >> mt5_gateway.spec
echo     [], >> mt5_gateway.spec
echo     exclude_binaries=True, >> mt5_gateway.spec
echo     name='MT5_Flask_Gateway', >> mt5_gateway.spec
echo     debug=False, >> mt5_gateway.spec
echo     bootloader_ignore_signals=False, >> mt5_gateway.spec
echo     strip=False, >> mt5_gateway.spec
echo     upx=True, >> mt5_gateway.spec
echo     console=True, >> mt5_gateway.spec
echo     disable_windowed_traceback=False, >> mt5_gateway.spec
echo     target_arch=None, >> mt5_gateway.spec
echo     codesign_identity=None, >> mt5_gateway.spec
echo     entitlements_file=None, >> mt5_gateway.spec
echo ^) >> mt5_gateway.spec
echo. >> mt5_gateway.spec
echo coll = COLLECT( >> mt5_gateway.spec
echo     exe, >> mt5_gateway.spec
echo     a.binaries, >> mt5_gateway.spec
echo     a.zipfiles, >> mt5_gateway.spec
echo     a.datas, >> mt5_gateway.spec
echo     strip=False, >> mt5_gateway.spec
echo     upx=True, >> mt5_gateway.spec
echo     upx_exclude=[], >> mt5_gateway.spec
echo     name='MT5_Flask_Gateway' >> mt5_gateway.spec
echo ^) >> mt5_gateway.spec

REM Führe PyInstaller aus
echo Führe PyInstaller aus...
echo Dies kann einige Minuten dauern...
pyinstaller mt5_gateway.spec
if %errorlevel% neq 0 (
    echo FEHLER: PyInstaller Build fehlgeschlagen.
    pause
    exit /b 1
)

REM Kopiere zusätzliche Dateien
echo Kopiere zusätzliche Dateien...
if exist "dist\MT5_Flask_Gateway" (
    copy env.example "dist\MT5_Flask_Gateway\"
    if not exist "dist\MT5_Flask_Gateway\logs" mkdir "dist\MT5_Flask_Gateway\logs"
    if not exist "dist\MT5_Flask_Gateway\data" mkdir "dist\MT5_Flask_Gateway\data"
    if not exist "dist\MT5_Flask_Gateway\config" mkdir "dist\MT5_Flask_Gateway\config"
    
    REM Erstelle Start-Skript für EXE
    echo @echo off > "dist\MT5_Flask_Gateway\start_gateway.bat"
    echo echo MT5 Flask Gateway wird gestartet... >> "dist\MT5_Flask_Gateway\start_gateway.bat"
    echo MT5_Flask_Gateway.exe >> "dist\MT5_Flask_Gateway\start_gateway.bat"
    echo pause >> "dist\MT5_Flask_Gateway\start_gateway.bat"
    
    REM Erstelle README für EXE
    echo MT5 Flask Gateway - Standalone Version > "dist\MT5_Flask_Gateway\README.txt"
    echo. >> "dist\MT5_Flask_Gateway\README.txt"
    echo Installation: >> "dist\MT5_Flask_Gateway\README.txt"
    echo 1. Kopieren Sie den gesamten Ordner an den gewünschten Speicherort >> "dist\MT5_Flask_Gateway\README.txt"
    echo 2. Bearbeiten Sie env.example und benennen Sie es in .env um >> "dist\MT5_Flask_Gateway\README.txt"
    echo 3. Starten Sie das Gateway mit start_gateway.bat >> "dist\MT5_Flask_Gateway\README.txt"
    echo 4. Öffnen Sie http://localhost:8080 im Browser >> "dist\MT5_Flask_Gateway\README.txt"
    echo. >> "dist\MT5_Flask_Gateway\README.txt"
    echo Support: support@mt5gateway.com >> "dist\MT5_Flask_Gateway\README.txt"
    
    echo EXE-Build erfolgreich erstellt in dist\MT5_Flask_Gateway\
) else (
    echo FEHLER: Build-Verzeichnis nicht gefunden.
    pause
    exit /b 1
)

REM Bereinige temporäre Dateien
echo Bereinige temporäre Dateien...
if exist "build" rmdir /s /q "build"
if exist "mt5_gateway.spec" del "mt5_gateway.spec"

echo ========================================
echo EXE-Build abgeschlossen!
echo ========================================
echo.
echo Die ausführbare Datei befindet sich in: dist\MT5_Flask_Gateway\
echo.
echo Nächste Schritte:
echo 1. Testen Sie die EXE-Datei
echo 2. Erstellen Sie einen Installer mit make_installer.bat
echo 3. Verteilen Sie die Anwendung
echo.

pause
