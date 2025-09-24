# ============================================================================
# MT5 Flask Gateway - Python Installation & Verification Script
# PowerShell Script für automatische Python-Bereitstellung
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$Version = "3.11",
    
    [Parameter(Mandatory=$false)]
    [string]$Architecture = "amd64",
    
    [Parameter(Mandatory=$false)]
    [string]$DownloadPath = "$env:TEMP\python-installer.exe",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Farben für bessere UX
$Host.UI.RawUI.ForegroundColor = "White"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($Message) { Write-ColorOutput Green "✓ $Message" }
function Write-Warning($Message) { Write-ColorOutput Yellow "⚠ $Message" }
function Write-Error($Message) { Write-ColorOutput Red "✗ $Message" }
function Write-Info($Message) { Write-ColorOutput Blue "ℹ $Message" }

Write-Info "MT5 Flask Gateway - Python $Version Installation"
Write-Info "=============================================="
Write-Output ""

# Log-Datei
$LogFile = "$PWD\logs\python_install.log"
if (!(Test-Path (Split-Path $LogFile))) {
    New-Item -ItemType Directory -Path (Split-Path $LogFile) -Force | Out-Null
}

"[$(Get-Date)] Python-Installation gestartet - Version $Version" | Out-File $LogFile -Append

try {
    # Schritt 1: Prüfe vorhandene Python-Installation
    Write-Info "Schritt 1: Prüfe vorhandene Python-Installation..."
    
    $PythonFound = $false
    $PythonPath = ""
    $PythonCommand = ""
    
    # Prüfe py launcher
    try {
        $PyVersion = & py -$Version --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python $Version über py launcher gefunden: $PyVersion"
            $PythonFound = $true
            $PythonCommand = "py -$Version"
            "[$(Get-Date)] Python über py launcher gefunden: $PyVersion" | Out-File $LogFile -Append
        }
    }
    catch {
        Write-Info "py launcher nicht verfügbar oder Version $Version nicht gefunden"
    }
    
    # Prüfe direkten python Befehl
    if (-not $PythonFound) {
        try {
            $DirectVersion = & python --version 2>$null
            if ($LASTEXITCODE -eq 0 -and $DirectVersion -match $Version) {
                Write-Success "Python $Version direkt gefunden: $DirectVersion"
                $PythonFound = $true
                $PythonCommand = "python"
                "[$(Get-Date)] Python direkt gefunden: $DirectVersion" | Out-File $LogFile -Append
            }
        }
        catch {
            Write-Info "Direkter python Befehl nicht verfügbar"
        }
    }
    
    # Prüfe Registry
    if (-not $PythonFound) {
        Write-Info "Prüfe Registry für Python-Installationen..."
        
        $RegistryPaths = @(
            "HKLM:\SOFTWARE\Python\PythonCore\",
            "HKCU:\SOFTWARE\Python\PythonCore\",
            "HKLM:\SOFTWARE\WOW6432Node\Python\PythonCore\"
        )
        
        foreach ($RegPath in $RegistryPaths) {
            if (Test-Path $RegPath) {
                $PythonVersions = Get-ChildItem $RegPath -ErrorAction SilentlyContinue
                foreach ($PythonVer in $PythonVersions) {
                    if ($PythonVer.PSChildName -match $Version) {
                        $InstallPath = Get-ItemProperty "$($PythonVer.PSPath)\InstallPath" -Name "(default)" -ErrorAction SilentlyContinue
                        if ($InstallPath -and (Test-Path "$($InstallPath.'(default)')python.exe")) {
                            Write-Success "Python $Version in Registry gefunden: $($InstallPath.'(default)')"
                            $PythonFound = $true
                            $PythonPath = $InstallPath.'(default)'
                            break
                        }
                    }
                }
                if ($PythonFound) { break }
            }
        }
    }
    
    # Wenn gefunden und nicht Force, dann fertig
    if ($PythonFound -and -not $Force) {
        Write-Success "Python $Version ist bereits verfügbar!"
        Write-Output ""
        exit 0
    }
    
    # Schritt 2: Python herunterladen
    Write-Info "Schritt 2: Python $Version wird heruntergeladen..."
    
    # Bestimme Download-URL
    $MajorMinor = $Version
    $PatchVersion = "11"  # Latest patch version für 3.11
    if ($Version -eq "3.12") { $PatchVersion = "7" }
    
    $FullVersion = "$MajorMinor.$PatchVersion"
    $DownloadUrl = "https://www.python.org/ftp/python/$FullVersion/python-$FullVersion-$Architecture.exe"
    
    Write-Info "Download-URL: $DownloadUrl"
    "[$(Get-Date)] Download-URL: $DownloadUrl" | Out-File $LogFile -Append
    
    # Download mit Retry-Logik
    $MaxRetries = 3
    $RetryCount = 0
    $DownloadSuccess = $false
    
    while ($RetryCount -lt $MaxRetries -and -not $DownloadSuccess) {
        try {
            $RetryCount++
            Write-Info "Download-Versuch $RetryCount von $MaxRetries..."
            
            # Lösche alte Datei falls vorhanden
            if (Test-Path $DownloadPath) {
                Remove-Item $DownloadPath -Force
            }
            
            # Download mit Progress
            $WebClient = New-Object System.Net.WebClient
            
            # Progress-Handler
            $WebClient.add_DownloadProgressChanged({
                param($sender, $e)
                $percent = $e.ProgressPercentage
                if ($percent % 10 -eq 0) {  # Nur jeder 10. Prozent
                    Write-Progress -Activity "Python herunterladen" -Status "$percent% abgeschlossen" -PercentComplete $percent
                }
            })
            
            $WebClient.DownloadFile($DownloadUrl, $DownloadPath)
            $WebClient.Dispose()
            
            Write-Progress -Activity "Python herunterladen" -Completed
            
            if (Test-Path $DownloadPath) {
                $FileSize = (Get-Item $DownloadPath).Length
                if ($FileSize -gt 1MB) {
                    Write-Success "Python-Installer heruntergeladen ($([math]::Round($FileSize/1MB, 2)) MB)"
                    $DownloadSuccess = $true
                    "[$(Get-Date)] Download erfolgreich: $FileSize Bytes" | Out-File $LogFile -Append
                } else {
                    throw "Download-Datei zu klein: $FileSize Bytes"
                }
            } else {
                throw "Download-Datei nicht erstellt"
            }
        }
        catch {
            Write-Warning "Download-Versuch $RetryCount fehlgeschlagen: $($_.Exception.Message)"
            "[$(Get-Date)] Download-Versuch $RetryCount fehlgeschlagen: $($_.Exception.Message)" | Out-File $LogFile -Append
            
            if ($RetryCount -lt $MaxRetries) {
                Write-Info "Warte 5 Sekunden vor erneutem Versuch..."
                Start-Sleep -Seconds 5
            }
        }
    }
    
    if (-not $DownloadSuccess) {
        Write-Error "Python-Download nach $MaxRetries Versuchen fehlgeschlagen"
        "[$(Get-Date)] Python-Download endgültig fehlgeschlagen" | Out-File $LogFile -Append
        exit 1
    }
    
    # Schritt 3: Python installieren
    Write-Info "Schritt 3: Installiere Python $Version..."
    
    # Installation mit silent flags
    $InstallArgs = @(
        "/quiet",
        "InstallAllUsers=1",
        "PrependPath=1",
        "Include_launcher=1",
        "Include_pip=1",
        "Include_test=0",
        "Include_doc=0",
        "Include_dev=0",
        "Include_debug=0",
        "Include_tcltk=1",
        "TargetDir=C:\Python$($Version.Replace('.', ''))",
        "AssociateFiles=0"
    )
    
    Write-Info "Starte Installation (silent)..."
    "[$(Get-Date)] Starte Python-Installation mit Argumenten: $($InstallArgs -join ' ')" | Out-File $LogFile -Append
    
    $Process = Start-Process -FilePath $DownloadPath -ArgumentList $InstallArgs -Wait -PassThru -NoNewWindow
    
    if ($Process.ExitCode -eq 0) {
        Write-Success "Python $Version erfolgreich installiert"
        "[$(Get-Date)] Python-Installation erfolgreich abgeschlossen" | Out-File $LogFile -Append
    } else {
        Write-Error "Python-Installation fehlgeschlagen (Exit-Code: $($Process.ExitCode))"
        "[$(Get-Date)] Python-Installation fehlgeschlagen mit Exit-Code: $($Process.ExitCode)" | Out-File $LogFile -Append
        exit 1
    }
    
    # Schritt 4: Installation verifizieren
    Write-Info "Schritt 4: Verifiziere Installation..."
    
    # Warte kurz für Registry-Updates
    Start-Sleep -Seconds 3
    
    # Aktualisiere PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    
    # Teste Python
    $VerificationSuccess = $false
    try {
        $InstalledVersion = & py -$Version --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python erfolgreich verifiziert: $InstalledVersion"
            $VerificationSuccess = $true
        }
    }
    catch {
        Write-Warning "py launcher Verifikation fehlgeschlagen"
    }
    
    if (-not $VerificationSuccess) {
        try {
            $InstalledVersion = & python --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Python erfolgreich verifiziert: $InstalledVersion"
                $VerificationSuccess = $true
            }
        }
        catch {
            Write-Warning "Direkte python Verifikation fehlgeschlagen"
        }
    }
    
    if (-not $VerificationSuccess) {
        Write-Error "Python-Installation konnte nicht verifiziert werden"
        "[$(Get-Date)] Python-Verifikation fehlgeschlagen" | Out-File $LogFile -Append
        exit 1
    }
    
    # Schritt 5: pip aktualisieren
    Write-Info "Schritt 5: Aktualisiere pip..."
    
    try {
        & py -$Version -m pip install --upgrade pip setuptools wheel
        if ($LASTEXITCODE -eq 0) {
            Write-Success "pip erfolgreich aktualisiert"
        } else {
            Write-Warning "pip-Update fehlgeschlagen (nicht kritisch)"
        }
    }
    catch {
        Write-Warning "pip-Update fehlgeschlagen: $($_.Exception.Message)"
    }
    
    # Cleanup
    Write-Info "Bereinige temporäre Dateien..."
    try {
        if (Test-Path $DownloadPath) {
            Remove-Item $DownloadPath -Force
            Write-Success "Installer-Datei gelöscht"
        }
    }
    catch {
        Write-Warning "Cleanup fehlgeschlagen: $($_.Exception.Message)"
    }
    
    Write-Output ""
    Write-Success "Python $Version Installation erfolgreich abgeschlossen!"
    Write-Info "Python ist jetzt über 'py -$Version' oder 'python' verfügbar."
    Write-Output ""
    
    "[$(Get-Date)] Python-Installation erfolgreich abgeschlossen" | Out-File $LogFile -Append
    exit 0
    
} catch {
    Write-Error "Unerwarteter Fehler: $($_.Exception.Message)"
    Write-Error "Details: $($_.Exception.StackTrace)"
    "[$(Get-Date)] Unerwarteter Fehler: $($_.Exception.Message)" | Out-File $LogFile -Append
    exit 1
}
