#Requires -Version 5
#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PrivateAdapter,
    [string]$PublicAdapter = "",
    [ipaddress]$ScopeAddress = "10.0.0.1"
)

$ErrorActionPreference = "Stop"

if (-not (Get-NetAdapter -Name $PrivateAdapter -ErrorAction SilentlyContinue)) {
    throw "Private adapter '$PrivateAdapter' was not found."
}

if ([string]::IsNullOrWhiteSpace($PublicAdapter)) {
    $route = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" |
        Where-Object {
            $_.NextHop -ne "0.0.0.0" -and
            $_.InterfaceAlias -ne $PrivateAdapter -and
            (Get-NetAdapter -InterfaceIndex $_.InterfaceIndex).Status -eq "Up"
        } |
        Sort-Object RouteMetric |
        Select-Object -First 1
    if (-not $route) {
        throw "No active default-route adapter was found."
    }
    $PublicAdapter = $route.InterfaceAlias
}

if ($PublicAdapter -eq $PrivateAdapter) {
    throw "Public and private adapters must be different."
}
if (-not (Get-NetAdapter -Name $PublicAdapter -ErrorAction SilentlyContinue)) {
    throw "Public adapter '$PublicAdapter' was not found."
}

$sharedAccessPath = "HKLM:\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters"
New-ItemProperty -Path $sharedAccessPath -Name ScopeAddress -Value $ScopeAddress.IPAddressToString -PropertyType String -Force | Out-Null
New-ItemProperty -Path $sharedAccessPath -Name ScopeAddressBackup -Value $ScopeAddress.IPAddressToString -PropertyType String -Force | Out-Null
Set-Service -Name SharedAccess -StartupType Manual
Start-Service -Name SharedAccess

$sharing = New-Object -ComObject HNetCfg.HNetShare
$connections = @($sharing.EnumEveryConnection)

function Get-SharingConnection([string]$Name) {
    foreach ($connection in $connections) {
        if ($sharing.NetConnectionProps.Invoke($connection).Name -eq $Name) {
            return $connection
        }
    }
    throw "ICS could not resolve adapter '$Name'."
}

foreach ($connection in $connections) {
    $configuration = $sharing.INetSharingConfigurationForINetConnection.Invoke($connection)
    if ($configuration.SharingEnabled) {
        $configuration.DisableSharing()
    }
}

$publicConnection = Get-SharingConnection $PublicAdapter
$privateConnection = Get-SharingConnection $PrivateAdapter
$publicConfiguration = $sharing.INetSharingConfigurationForINetConnection.Invoke($publicConnection)
$privateConfiguration = $sharing.INetSharingConfigurationForINetConnection.Invoke($privateConnection)

$publicConfiguration.EnableSharing(0)
$privateConfiguration.EnableSharing(1)
Start-Sleep -Seconds 2

if (-not $publicConfiguration.SharingEnabled -or $publicConfiguration.SharingConnectionType -ne 0) {
    throw "The public adapter did not enter public sharing mode."
}
if (-not $privateConfiguration.SharingEnabled -or $privateConfiguration.SharingConnectionType -ne 1) {
    throw "The RNDIS adapter did not enter private sharing mode."
}

$addressReady = $false
for ($attempt = 0; $attempt -lt 10; $attempt++) {
    $addressReady = [bool](Get-NetIPAddress -InterfaceAlias $PrivateAdapter -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -eq $ScopeAddress.IPAddressToString })
    if ($addressReady) { break }
    Start-Sleep -Seconds 1
}
if (-not $addressReady) {
    throw "ICS was enabled, but '$PrivateAdapter' does not have $($ScopeAddress.IPAddressToString)."
}

Write-Output "PUBLIC_ADAPTER=$PublicAdapter"
Write-Output "PRIVATE_ADAPTER=$PrivateAdapter"
Write-Output "ICS_ENABLED=1"
