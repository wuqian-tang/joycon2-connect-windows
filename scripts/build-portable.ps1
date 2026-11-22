param([string]$Python = '', [switch]$SkipInstall, [switch]$SkipBluetoothScan)
$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
Push-Location $appRoot
try {
    if (-not $Python) {
        $candidates = @((Join-Path $appRoot '.venv\Scripts\python.exe'),
                        (Join-Path (Split-Path -Parent $appRoot) '.venv\Scripts\python.exe'))
        $Python = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
        if (-not $Python) {
            & python -m venv .venv
            if ($LASTEXITCODE -ne 0) { throw 'Python 3.10 x64 or newer is required to build.' }
            $Python = Join-Path $appRoot '.venv\Scripts\python.exe'
        }
    }
    & $Python -c "import struct,sys; assert sys.platform=='win32' and struct.calcsize('P')==8, 'Build requires Windows x64 Python'"
    if ($LASTEXITCODE -ne 0) { throw 'Build requires Windows x64 Python.' }
    if (-not $SkipInstall) {
        & $Python -m pip install --index-url https://pypi.org/simple -r requirements-build.txt
        if ($LASTEXITCODE -ne 0) { throw 'Build dependencies could not be installed.' }
    }
    & $Python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    if (-not (Test-Path -LiteralPath 'assets\app.ico')) {
        & $Python scripts\make_icon.py
        if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }
    }
    & $Python -m PyInstaller --noconfirm --clean JoyCon2Assistant.spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
    $bundle = Join-Path $appRoot 'dist\JoyCon2Assistant'
    Copy-Item -LiteralPath LICENSE,NOTICE.md,PORTABLE-README.txt -Destination $bundle
    if (Test-Path -LiteralPath README.md) { Copy-Item -LiteralPath README.md -Destination $bundle }
    New-Item -ItemType Directory -Force -Path (Join-Path $bundle 'assets') | Out-Null
    Copy-Item -LiteralPath assets\app.png -Destination (Join-Path $bundle 'assets')
    if (Test-Path -LiteralPath docs\screenshots) {
        New-Item -ItemType Directory -Force -Path (Join-Path $bundle 'docs') | Out-Null
        Copy-Item -LiteralPath docs\screenshots -Destination (Join-Path $bundle 'docs') -Recurse
    }
    if (Test-Path -LiteralPath docs\ARCHITECTURE.md) {
        New-Item -ItemType Directory -Force -Path (Join-Path $bundle 'docs') | Out-Null
        Copy-Item -LiteralPath docs\ARCHITECTURE.md -Destination (Join-Path $bundle 'docs')
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $bundle 'scripts') | Out-Null
    Copy-Item -LiteralPath scripts\create-shortcut.ps1 -Destination (Join-Path $bundle 'scripts')
    # Validate without adding runtime files to the distributable folder.
    $verifyArguments = @('scripts\verify-portable.py', $bundle)
    if ($SkipBluetoothScan) { $verifyArguments += '--skip-bluetooth' }
    & $Python @verifyArguments
    if ($LASTEXITCODE -ne 0) { throw 'Portable smoke verification failed.' }
    New-Item -ItemType Directory -Force -Path releases | Out-Null
    $version = & $Python -c "from joycon2_assistant.paths import VERSION; print(VERSION)"
    $archive = Join-Path $appRoot "releases\JoyCon2Assistant-$version-windows-x64.zip"
    Compress-Archive -LiteralPath $bundle -DestinationPath $archive -Force
    $hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $([IO.Path]::GetFileName($archive))" | Set-Content -LiteralPath "$archive.sha256" -Encoding ascii
    Write-Host "Portable ZIP: $archive"
    Write-Host "SHA256: $hash"
} finally {
    Pop-Location
}
