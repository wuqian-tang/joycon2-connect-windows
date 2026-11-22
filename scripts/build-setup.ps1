param([string]$Compiler = '', [string]$Python = '', [switch]$SkipPortableBuild, [switch]$SkipBluetoothScan)
$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
Push-Location $appRoot
try {
    if (-not $SkipPortableBuild) {
        & "$PSScriptRoot\build-portable.ps1" -SkipBluetoothScan:$SkipBluetoothScan
    }
    if (-not $Python) {
        $pythonCandidates = @((Join-Path $appRoot '.venv\Scripts\python.exe'),
                              (Join-Path (Split-Path -Parent $appRoot) '.venv\Scripts\python.exe'))
        $Python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
        if (-not $Python) { $Python = (Get-Command python -ErrorAction Stop).Source }
    }
    $version = & $Python -c "from joycon2_assistant.paths import VERSION; print(VERSION)"
    if ($LASTEXITCODE -ne 0 -or -not $version) { throw 'Could not read the application version.' }
    if (-not $Compiler) { $Compiler = $env:JOYCON2_ISCC }
    if (-not $Compiler) {
        $candidates = @(
            (Join-Path (Split-Path -Parent $appRoot) 'build-tools\InnoSetup7\ISCC.exe'),
            (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
            (Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe'),
            (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'))
        $available = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($available) { $candidates = @($available.Source) + $candidates }
        $Compiler = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    }
    if (-not $Compiler) {
        throw 'Official Inno Setup compiler is required. Install it portably with scripts/bootstrap-inno.ps1, or pass -Compiler <ISCC.exe>.'
    }
    & $Compiler "/DSourceRoot=$appRoot" "/DAppVersion=$version" 'installer\JoyCon2Connect.iss'
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup compilation failed.' }
    $installer = Join-Path $appRoot "releases\JoyCon2Connect-$version-Setup.exe"
    $hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $([IO.Path]::GetFileName($installer))" | Set-Content -LiteralPath "$installer.sha256" -Encoding ascii
    Write-Host "Setup: $installer"
    Write-Host "SHA256: $hash"
} finally {
    Pop-Location
}
