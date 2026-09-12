$ErrorActionPreference = "Stop"

$BaseUrl = "http://127.0.0.1:8000"
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\PrivacyGuard"
$InstalledExe = Join-Path $InstallDir "PrivacyGuard.exe"
$DbPath = Join-Path $env:LOCALAPPDATA "PrivacyGuard\privacyguard.db"

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Wait-PrivacyGuard {
    param(
        [int]$Attempts = 20
    )

    for ($i = 0; $i -lt $Attempts; $i++) {
        Start-Sleep -Seconds 1
        try {
            $health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 2
            if ($health.status -eq "online") {
                return $health
            }
        }
        catch {
        }
    }

    throw "PrivacyGuard did not become healthy on port 8000."
}

function Start-PrivacyGuard {
    Assert-True (Test-Path $InstalledExe) "Installed PrivacyGuard.exe was not found at $InstalledExe"

    $process = Start-Process -FilePath $InstalledExe -PassThru
    $null = Wait-PrivacyGuard
    return $process
}

function Stop-PrivacyGuard {
    param($Process)

    if ($null -ne $Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force
        $Process.WaitForExit()
    }

    Start-Sleep -Seconds 1
}

Write-Host "=== PrivacyGuard Windows acceptance test ==="

$process = $null

try {
    # -----------------------------------------------------
    # First launch: engine, frontend routes, APIs
    # -----------------------------------------------------
    $process = Start-PrivacyGuard

    $health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 5
    Assert-True ($health.status -eq "online") "Health endpoint is not online."
    Assert-True ($health.version -eq "2.1.0") "Unexpected PrivacyGuard version: $($health.version)"

    $networkInfo = Invoke-RestMethod -Uri "$BaseUrl/api/network/info" -TimeoutSec 5
    Assert-True (-not [string]::IsNullOrWhiteSpace($networkInfo.hostname)) "Network info did not return a hostname."
    Assert-True (-not [string]::IsNullOrWhiteSpace($networkInfo.operating_system)) "Network info did not return an operating system."

    foreach ($route in @("/", "/network", "/identity", "/history", "/settings")) {
        $page = Invoke-WebRequest -Uri "$BaseUrl$route" -TimeoutSec 5
        Assert-True ($page.StatusCode -eq 200) "Frontend route $route did not return HTTP 200."
        Assert-True ($page.Content -match 'id="root"') "Frontend route $route did not return the React application shell."
    }

    $history = Invoke-RestMethod -Uri "$BaseUrl/api/history" -TimeoutSec 5
    Assert-True ($history.status -eq "success") "History endpoint failed."

    $trustStatus = Invoke-RestMethod -Uri "$BaseUrl/api/network/trust-status" -TimeoutSec 5
    Assert-True ($trustStatus.status -eq "success") "Trust-status endpoint failed."

    $invalidIdentity = Invoke-RestMethod `
        -Uri "$BaseUrl/api/identity/check" `
        -Method Post `
        -ContentType "application/json" `
        -Body '{"email":"not-an-email"}' `
        -TimeoutSec 5

    Assert-True ($invalidIdentity.status -eq "error") "Identity validation did not reject an invalid email address."

    $scan = Invoke-RestMethod -Uri "$BaseUrl/api/network/scan" -TimeoutSec 45
    Assert-True (($scan.status -eq "success") -or ($scan.status -eq "error")) "Network scan endpoint returned an unexpected status."

    if ($scan.status -eq "error") {
        $expectedSafetyMessages = @(
            "PrivacyGuard could not determine the local network range.",
            "Invalid local network range.",
            "PrivacyGuard only scans private local networks.",
            "PrivacyGuard limits scans to a maximum of 256 local addresses."
        )
        Assert-True ($expectedSafetyMessages -contains $scan.message) "Network scan failed for an unexpected reason: $($scan.message)"
        Write-Host "Network scan safety guard returned: $($scan.message)"
    }
    else {
        Assert-True ($null -ne $scan.devices_found) "Successful network scan did not return devices_found."
        Write-Host "Network scan executed successfully with $($scan.devices_found) device(s)."
    }

    $pdfPath = Join-Path $env:RUNNER_TEMP "PrivacyGuard-Acceptance-Report.pdf"
    $headersPath = Join-Path $env:RUNNER_TEMP "PrivacyGuard-Acceptance-Report.headers"
    & curl.exe -sS -D $headersPath -o $pdfPath "$BaseUrl/api/report/security"
    if ($LASTEXITCODE -ne 0) {
        throw "Security report download failed with curl exit code $LASTEXITCODE."
    }

    Assert-True (Test-Path $pdfPath) "Security report PDF was not created."
    Assert-True ((Get-Item $pdfPath).Length -gt 1000) "Security report PDF is unexpectedly small."
    $headersText = Get-Content $headersPath -Raw
    Assert-True ($headersText -match "application/pdf") "Security report did not return application/pdf."

    Assert-True (Test-Path $DbPath) "PrivacyGuard local SQLite database was not created at $DbPath"

    Stop-PrivacyGuard $process
    $process = $null

    # -----------------------------------------------------
    # Seed one local test device to exercise trust controls.
    # This only touches the ephemeral CI runner database.
    # -----------------------------------------------------
    $pythonScript = @'
import sqlite3
import sys
from datetime import datetime

path = sys.argv[1]
now = datetime.now().isoformat()
connection = sqlite3.connect(path)
connection.execute(
    """
    INSERT OR IGNORE INTO known_devices (
        device_key, mac_address, ip_address, device_name,
        device_type, first_seen, last_seen, times_seen
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        "IP:127.0.0.254",
        None,
        "127.0.0.254",
        "CI Acceptance Device",
        "Test Device",
        now,
        now,
        1,
    ),
)
connection.commit()
connection.close()
'@

    $pythonScript | python - $DbPath
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to seed the acceptance-test device into SQLite."
    }

    # -----------------------------------------------------
    # Second launch: trusted-device mutation
    # -----------------------------------------------------
    $process = Start-PrivacyGuard

    $knownDevices = Invoke-RestMethod -Uri "$BaseUrl/api/network/devices" -TimeoutSec 5
    Assert-True ($knownDevices.status -eq "success") "Known-device endpoint failed."

    $testDevice = $knownDevices.devices | Where-Object { $_.name -eq "CI Acceptance Device" } | Select-Object -First 1
    Assert-True ($null -ne $testDevice) "Acceptance-test device was not returned by the API."

    $trustUpdate = Invoke-RestMethod `
        -Uri "$BaseUrl/api/network/devices/$($testDevice.id)/trust" `
        -Method Patch `
        -ContentType "application/json" `
        -Body '{"trusted":true}' `
        -TimeoutSec 5

    Assert-True ($trustUpdate.status -eq "success") "Trust-device update failed."
    Assert-True ($trustUpdate.trusted -eq $true) "Trust-device update did not set trusted=true."

    $trustStatus = Invoke-RestMethod -Uri "$BaseUrl/api/network/trust-status" -TimeoutSec 5
    Assert-True ($trustStatus.trusted_ids -contains $testDevice.id) "Trusted device was not returned by trust-status."

    Stop-PrivacyGuard $process
    $process = $null

    # -----------------------------------------------------
    # Third launch: persistence across restart
    # -----------------------------------------------------
    $process = Start-PrivacyGuard

    $trustStatusAfterRestart = Invoke-RestMethod -Uri "$BaseUrl/api/network/trust-status" -TimeoutSec 5
    Assert-True ($trustStatusAfterRestart.trusted_ids -contains $testDevice.id) "Trusted-device state did not persist after restart."

    $historyAfterRestart = Invoke-RestMethod -Uri "$BaseUrl/api/history" -TimeoutSec 5
    Assert-True ($historyAfterRestart.status -eq "success") "History endpoint failed after restart."

    Write-Host "All Windows acceptance checks passed."
}
finally {
    if ($null -ne $process) {
        Stop-PrivacyGuard $process
    }
}
