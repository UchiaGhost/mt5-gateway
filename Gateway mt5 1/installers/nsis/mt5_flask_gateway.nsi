; MT5 Flask Gateway - NSIS Installer Script
; Erstellt einen Windows-Installer für das MT5 Flask Gateway

!define APP_NAME "MT5 Flask Gateway"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "MT5 Gateway Team"
!define APP_URL "https://mt5gateway.com"
!define APP_EXE "MT5_Flask_Gateway.exe"
!define APP_ICON "app\ui\static\img\icon.ico"

; Modern UI
!include "MUI2.nsh"

; Allgemeine Einstellungen
Name "${APP_NAME}"
OutFile "MT5_Flask_Gateway_Setup.exe"
InstallDir "$PROGRAMFILES\MT5 Flask Gateway"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

; Interface Einstellungen
!define MUI_ABORTWARNING
!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"

; Seiten
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Sprachen
!insertmacro MUI_LANGUAGE "German"

; Installer Sektionen
Section "Hauptprogramm" SecMain
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; Hauptdateien
    File "dist\MT5_Flask_Gateway\${APP_EXE}"
    File "dist\MT5_Flask_Gateway\env.example"
    File "dist\MT5_Flask_Gateway\README.txt"
    
    ; Verzeichnisse erstellen
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\config"
    
    ; Registry-Einträge
    WriteRegStr HKLM "Software\${APP_NAME}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" '"$INSTDIR\${APP_EXE}"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
    
    ; Uninstaller erstellen
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Desktop-Verknüpfung" SecDesktop
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
SectionEnd

Section "Startmenü-Verknüpfung" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Gateway starten.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Gateway stoppen.lnk" "$INSTDIR\stop_gateway.bat" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Konfiguration.lnk" "$INSTDIR\config" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Logs.lnk" "$INSTDIR\logs" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Deinstallieren.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd

Section "Firewall-Regel" SecFirewall
    ; Firewall-Regel für Port 8080 hinzufügen
    ExecWait 'netsh advfirewall firewall add rule name="${APP_NAME}" dir=in action=allow protocol=TCP localport=8080'
SectionEnd

Section "Windows-Service" SecService
    ; Optional: Als Windows-Service installieren
    ; Hier könnte NSSM oder ähnliches verwendet werden
    MessageBox MB_YESNO "Möchten Sie das MT5 Gateway als Windows-Service installieren?" IDNO skip_service
    
    ; Service-Installation (vereinfacht)
    File "scripts\install_service.bat"
    ExecWait '"$INSTDIR\install_service.bat"'
    
    skip_service:
SectionEnd

; Sektions-Beschreibungen
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "Hauptprogramm und erforderliche Dateien"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Desktop-Verknüpfung erstellen"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Startmenü-Verknüpfungen erstellen"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecFirewall} "Firewall-Regel für Port 8080 hinzufügen"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecService} "Als Windows-Service installieren (optional)"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Sektion
Section "Uninstall"
    ; Dateien entfernen
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\env.example"
    Delete "$INSTDIR\README.txt"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$INSTDIR\install_service.bat"
    
    ; Verzeichnisse entfernen (nur wenn leer)
    RMDir "$INSTDIR\logs"
    RMDir "$INSTDIR\data"
    RMDir "$INSTDIR\config"
    RMDir "$INSTDIR"
    
    ; Verknüpfungen entfernen
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\*.*"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    ; Registry-Einträge entfernen
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"
    
    ; Firewall-Regel entfernen
    ExecWait 'netsh advfirewall firewall delete rule name="${APP_NAME}"'
    
    ; Service entfernen (falls installiert)
    ExecWait 'sc stop "MT5FlaskGateway"' 2
    ExecWait 'sc delete "MT5FlaskGateway"' 2
SectionEnd

; Funktionen
Function .onInit
    ; Prüfe ob bereits installiert
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString"
    StrCmp $R0 "" done
    
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} ist bereits installiert. $\n$\nKlicken Sie auf 'OK', um die vorherige Version zu deinstallieren, oder 'Abbrechen', um die Installation zu beenden." \
        IDOK uninst
    Abort
    
    uninst:
        ClearErrors
        ExecWait '$R0 _?=$INSTDIR'
        
        IfErrors no_remove_uninstaller done
        no_remove_uninstaller:
    
    done:
FunctionEnd

Function .onInstSuccess
    ; Nach erfolgreicher Installation
    MessageBox MB_YESNO "Installation erfolgreich!$\n$\nMöchten Sie das MT5 Gateway jetzt starten?" IDYES start_app
    Return
    
    start_app:
        Exec '"$INSTDIR\${APP_EXE}"'
FunctionEnd

; Post-Installation Skripte
Section -Post
    ; Start-Skript erstellen
    FileOpen $0 "$INSTDIR\start_gateway.bat" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 "echo MT5 Flask Gateway wird gestartet...$\r$\n"
    FileWrite $0 "cd /d $\"$INSTDIR$\"$\r$\n"
    FileWrite $0 "$\"$INSTDIR\${APP_EXE}$\"$\r$\n"
    FileWrite $0 "pause$\r$\n"
    FileClose $0
    
    ; Stop-Skript erstellen
    FileOpen $0 "$INSTDIR\stop_gateway.bat" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 "echo MT5 Flask Gateway wird gestoppt...$\r$\n"
    FileWrite $0 "taskkill /f /im ${APP_EXE} 2>nul$\r$\n"
    FileWrite $0 "echo Gateway gestoppt.$\r$\n"
    FileWrite $0 "pause$\r$\n"
    FileClose $0
    
    ; Konfigurationsdatei erstellen
    IfFileExists "$INSTDIR\config\.env" config_exists create_config
    create_config:
        CopyFiles "$INSTDIR\env.example" "$INSTDIR\config\.env"
    config_exists:
SectionEnd
