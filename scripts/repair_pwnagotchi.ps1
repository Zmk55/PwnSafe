[CmdletBinding()]
param(
    [string]$TargetHost = "10.0.0.2",
    [string]$TargetUser = "pi",
    [string]$KeyPath = "",
    [switch]$NoRestart
)

$ErrorActionPreference = "Stop"
$localScript = Join-Path $PSScriptRoot "repair_pwnagotchi.sh"
$remoteScript = "/tmp/pwnsafe-repair-pwnagotchi.sh"
$target = "${TargetUser}@${TargetHost}"

if (-not (Test-Path -LiteralPath $localScript)) {
    throw "Device repair script not found: $localScript"
}

if (-not $KeyPath) {
    $candidate = Join-Path ([Environment]::GetFolderPath("UserProfile")) ".ssh\pwnsafe_id_rsa"
    if (Test-Path -LiteralPath $candidate) {
        $KeyPath = $candidate
    }
}

$sshOptions = @("-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new")
if ($KeyPath) {
    if (-not (Test-Path -LiteralPath $KeyPath)) {
        throw "SSH key not found: $KeyPath"
    }
    $sshOptions += @("-i", (Resolve-Path -LiteralPath $KeyPath).Path)
}

$ssh = (Get-Command ssh.exe -ErrorAction Stop).Source
$scp = (Get-Command scp.exe -ErrorAction Stop).Source

Write-Host "Copying repair script to $target..."
& $scp @sshOptions $localScript "${target}:$remoteScript"
if ($LASTEXITCODE -ne 0) {
    throw "SCP failed with exit code $LASTEXITCODE."
}

$repairArgument = if ($NoRestart) { " --no-restart" } else { "" }
$remoteCommand = "sed -i 's/\r$//' '$remoteScript'; sudo bash '$remoteScript'$repairArgument; result=`$?; rm -f '$remoteScript'; exit `$result"

Write-Host "Applying repairs on $target..."
& $ssh @sshOptions -tt $target $remoteCommand
if ($LASTEXITCODE -ne 0) {
    throw "Remote repair failed with exit code $LASTEXITCODE."
}

Write-Host "Pwnagotchi repairs completed successfully."
