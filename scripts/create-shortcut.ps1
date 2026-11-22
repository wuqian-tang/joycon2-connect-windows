param([string]$Destination = [Environment]::GetFolderPath('Desktop'))
$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $appRoot 'JoyCon2Assistant.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw 'Extract the entire portable ZIP, then run this script inside its scripts folder.'
}
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $Destination 'Joy-Con 2 Assistant.lnk'))
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = $appRoot
$shortcut.IconLocation = "$exe,0"
$shortcut.Description = 'Joy-Con 2 local connection assistant'
$shortcut.Save()
Write-Host 'Created desktop shortcut.'
