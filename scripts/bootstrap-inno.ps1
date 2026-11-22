param([string]$ToolRoot = '')
$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
if (-not $ToolRoot) { $ToolRoot = Join-Path (Split-Path -Parent $appRoot) 'build-tools' }
$ToolRoot = [IO.Path]::GetFullPath($ToolRoot)
$downloadDir = Join-Path $ToolRoot 'downloads'
$compilerDir = Join-Path $ToolRoot 'InnoSetup7'
New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
$download = Join-Path $downloadDir 'innosetup-7.1.1-x64.exe'
Invoke-WebRequest -Uri 'https://github.com/jrsoftware/issrc/releases/download/is-7_1_1/innosetup-7.1.1-x64.exe' -OutFile $download
$expected = '8a5a6711c3766a6e5fb74f280ba0e3551e719ce94538d901fdbd1f8f9920b3f0'
if ((Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Official Inno Setup download hash did not match.'
}
$signature = Get-AuthenticodeSignature -LiteralPath $download
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Pyrsys B.V.') {
    throw 'Official Inno Setup signature was not valid.'
}
# Official portable mode creates neither an uninstaller nor an Add/Remove entry.
# Use the selected compiler folder and suppress shortcut creation.
$process = Start-Process -FilePath $download -ArgumentList @('/PORTABLE=1','/VERYSILENT',
    '/CURRENTUSER','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS',('/DIR="' + $compilerDir + '"')) `
    -PassThru -Wait -WindowStyle Hidden
if ($process.ExitCode -ne 0) { throw 'Inno Setup portable installation failed.' }
Write-Host (Join-Path $compilerDir 'ISCC.exe')
