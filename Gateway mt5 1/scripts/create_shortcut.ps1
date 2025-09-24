# ============================================================================
# MT5 Flask Gateway - Desktop Shortcut Creation Script
# PowerShell Script für Erstellung/Aktualisierung von Desktop-Verknüpfungen
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Target,
    
    [Parameter(Mandatory=$true)]
    [string]$ShortcutPath,
    
    [Parameter(Mandatory=$false)]
    [string]$WorkingDirectory = "",
    
    [Parameter(Mandatory=$false)]
    [string]$IconPath = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Arguments = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Description = "MT5 Flask Gateway",
    
    [Parameter(Mandatory=$false)]
    [int]$WindowStyle = 1,  # 1 = Normal, 3 = Maximized, 7 = Minimized
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Farben für bessere UX
function Write-Success($Message) { 
    Write-Host "✓ $Message" -ForegroundColor Green 
}

function Write-Warning($Message) { 
    Write-Host "⚠ $Message" -ForegroundColor Yellow 
}

function Write-Error($Message) { 
    Write-Host "✗ $Message" -ForegroundColor Red 
}

function Write-Info($Message) { 
    Write-Host "ℹ $Message" -ForegroundColor Blue 
}

Write-Info "MT5 Flask Gateway - Desktop Shortcut Creation"
Write-Info "============================================="
Write-Output ""

# Log-Datei
$LogFile = "$PWD\logs\shortcut_creation.log"
if (!(Test-Path (Split-Path $LogFile))) {
    New-Item -ItemType Directory -Path (Split-Path $LogFile) -Force | Out-Null
}

"[$(Get-Date)] Shortcut-Erstellung gestartet" | Out-File $LogFile -Append
"[$(Get-Date)] Target: $Target" | Out-File $LogFile -Append
"[$(Get-Date)] ShortcutPath: $ShortcutPath" | Out-File $LogFile -Append

try {
    # Schritt 1: Eingabe-Validierung
    Write-Info "Schritt 1: Validiere Eingabe-Parameter..."
    
    # Prüfe Target-Datei
    if (!(Test-Path $Target)) {
        Write-Error "Target-Datei nicht gefunden: $Target"
        "[$(Get-Date)] Fehler: Target-Datei nicht gefunden: $Target" | Out-File $LogFile -Append
        exit 1
    }
    
    Write-Success "Target-Datei gefunden: $Target"
    
    # Prüfe Shortcut-Verzeichnis
    $ShortcutDir = Split-Path $ShortcutPath -Parent
    if (!(Test-Path $ShortcutDir)) {
        Write-Info "Erstelle Shortcut-Verzeichnis: $ShortcutDir"
        New-Item -ItemType Directory -Path $ShortcutDir -Force | Out-Null
    }
    
    # Prüfe Working Directory
    if ($WorkingDirectory -and !(Test-Path $WorkingDirectory)) {
        Write-Warning "Working Directory nicht gefunden: $WorkingDirectory"
        $WorkingDirectory = Split-Path $Target -Parent
        Write-Info "Verwende Target-Verzeichnis als Working Directory: $WorkingDirectory"
    }
    
    if (!$WorkingDirectory) {
        $WorkingDirectory = Split-Path $Target -Parent
    }
    
    # Prüfe Icon-Datei
    if ($IconPath -and !(Test-Path $IconPath)) {
        Write-Warning "Icon-Datei nicht gefunden: $IconPath"
        $IconPath = ""
    }
    
    Write-Success "Parameter validiert"
    
    # Schritt 2: Prüfe bestehende Verknüpfung
    Write-Info "Schritt 2: Prüfe bestehende Verknüpfung..."
    
    if (Test-Path $ShortcutPath) {
        if ($Force) {
            Write-Info "Überschreibe bestehende Verknüpfung (Force-Modus)"
            Remove-Item $ShortcutPath -Force
            "[$(Get-Date)] Bestehende Verknüpfung überschrieben" | Out-File $LogFile -Append
        } else {
            Write-Warning "Verknüpfung existiert bereits: $ShortcutPath"
            Write-Info "Verwenden Sie -Force zum Überschreiben"
            "[$(Get-Date)] Verknüpfung existiert bereits, nicht überschrieben" | Out-File $LogFile -Append
            exit 0
        }
    }
    
    # Schritt 3: Erstelle Verknüpfung
    Write-Info "Schritt 3: Erstelle Desktop-Verknüpfung..."
    
    # WScript.Shell COM-Objekt erstellen
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    
    # Shortcut-Eigenschaften setzen
    $Shortcut.TargetPath = $Target
    $Shortcut.WorkingDirectory = $WorkingDirectory
    $Shortcut.Description = $Description
    $Shortcut.WindowStyle = $WindowStyle
    
    # Arguments setzen falls vorhanden
    if ($Arguments) {
        $Shortcut.Arguments = $Arguments
        Write-Info "Arguments gesetzt: $Arguments"
    }
    
    # Icon setzen falls vorhanden
    if ($IconPath) {
        $Shortcut.IconLocation = $IconPath
        Write-Info "Icon gesetzt: $IconPath"
    } else {
        # Verwende Target als Icon-Quelle
        $Shortcut.IconLocation = "$Target,0"
        Write-Info "Standard-Icon verwendet: $Target"
    }
    
    # Shortcut speichern
    $Shortcut.Save()
    
    # COM-Objekt freigeben
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($WshShell) | Out-Null
    
    Write-Success "Desktop-Verknüpfung erfolgreich erstellt"
    "[$(Get-Date)] Desktop-Verknüpfung erfolgreich erstellt" | Out-File $LogFile -Append
    
    # Schritt 4: Verknüpfung verifizieren
    Write-Info "Schritt 4: Verifiziere Verknüpfung..."
    
    if (Test-Path $ShortcutPath) {
        $ShortcutInfo = Get-Item $ShortcutPath
        Write-Success "Verknüpfung verifiziert: $($ShortcutInfo.Name)"
        Write-Info "Größe: $($ShortcutInfo.Length) Bytes"
        Write-Info "Erstellt: $($ShortcutInfo.CreationTime)"
        
        "[$(Get-Date)] Verknüpfung verifiziert: $($ShortcutInfo.FullName)" | Out-File $LogFile -Append
    } else {
        Write-Error "Verknüpfung konnte nicht verifiziert werden"
        "[$(Get-Date)] Fehler: Verknüpfung konnte nicht verifiziert werden" | Out-File $LogFile -Append
        exit 1
    }
    
    # Schritt 5: Zusätzliche Desktop-Integration
    Write-Info "Schritt 5: Desktop-Integration..."
    
    try {
        # Erstelle auch Startmenü-Verknüpfung
        $StartMenuPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\MT5 Flask Gateway.lnk"
        $StartMenuDir = Split-Path $StartMenuPath -Parent
        
        if (!(Test-Path $StartMenuDir)) {
            New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
        }
        
        $StartMenuShortcut = $WshShell.CreateShortcut($StartMenuPath)
        $StartMenuShortcut.TargetPath = $Target
        $StartMenuShortcut.WorkingDirectory = $WorkingDirectory
        $StartMenuShortcut.Description = $Description
        $StartMenuShortcut.WindowStyle = $WindowStyle
        
        if ($Arguments) { $StartMenuShortcut.Arguments = $Arguments }
        if ($IconPath) { $StartMenuShortcut.IconLocation = $IconPath } else { $StartMenuShortcut.IconLocation = "$Target,0" }
        
        $StartMenuShortcut.Save()
        
        Write-Success "Startmenü-Verknüpfung erstellt: $StartMenuPath"
        "[$(Get-Date)] Startmenü-Verknüpfung erstellt: $StartMenuPath" | Out-File $LogFile -Append
        
    } catch {
        Write-Warning "Startmenü-Verknüpfung konnte nicht erstellt werden: $($_.Exception.Message)"
        "[$(Get-Date)] Warnung: Startmenü-Verknüpfung fehlgeschlagen: $($_.Exception.Message)" | Out-File $LogFile -Append
    }
    
    Write-Output ""
    Write-Success "Desktop-Verknüpfung erfolgreich erstellt!"
    Write-Info "Verknüpfung: $ShortcutPath"
    Write-Info "Target: $Target"
    Write-Info "Working Directory: $WorkingDirectory"
    Write-Output ""
    
    "[$(Get-Date)] Shortcut-Erstellung erfolgreich abgeschlossen" | Out-File $LogFile -Append
    exit 0
    
} catch {
    Write-Error "Unerwarteter Fehler bei Shortcut-Erstellung: $($_.Exception.Message)"
    Write-Error "Details: $($_.Exception.StackTrace)"
    "[$(Get-Date)] Unerwarteter Fehler: $($_.Exception.Message)" | Out-File $LogFile -Append
    exit 1
}

# Zusätzliche Hilfsfunktionen

function Create-StartMenuFolder {
    param(
        [string]$AppName,
        [string]$TargetPath,
        [string]$WorkingDirectory,
        [string]$IconPath = ""
    )
    
    try {
        # Erstelle Startmenü-Ordner
        $StartMenuFolder = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\$AppName"
        if (!(Test-Path $StartMenuFolder)) {
            New-Item -ItemType Directory -Path $StartMenuFolder -Force | Out-Null
        }
        
        # Erstelle Haupt-Verknüpfung
        $MainShortcut = "$StartMenuFolder\$AppName.lnk"
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($MainShortcut)
        $Shortcut.TargetPath = $TargetPath
        $Shortcut.WorkingDirectory = $WorkingDirectory
        $Shortcut.Description = $AppName
        if ($IconPath) { $Shortcut.IconLocation = $IconPath }
        $Shortcut.Save()
        
        # Erstelle Konfigurations-Verknüpfung
        $ConfigShortcut = "$StartMenuFolder\Konfiguration.lnk"
        $ConfigLink = $WshShell.CreateShortcut($ConfigShortcut)
        $ConfigLink.TargetPath = "notepad.exe"
        $ConfigLink.Arguments = "$WorkingDirectory\config\.env"
        $ConfigLink.Description = "$AppName Konfiguration"
        $ConfigLink.Save()
        
        # Erstelle Logs-Verknüpfung
        $LogsShortcut = "$StartMenuFolder\Logs.lnk"
        $LogsLink = $WshShell.CreateShortcut($LogsShortcut)
        $LogsLink.TargetPath = "explorer.exe"
        $LogsLink.Arguments = "$WorkingDirectory\logs"
        $LogsLink.Description = "$AppName Logs"
        $LogsLink.Save()
        
        Write-Success "Startmenü-Ordner erstellt: $StartMenuFolder"
        return $true
        
    } catch {
        Write-Warning "Startmenü-Integration fehlgeschlagen: $($_.Exception.Message)"
        return $false
    }
}
