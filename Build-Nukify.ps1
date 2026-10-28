param(
    [Parameter(Mandatory=$true)][string]$BlenderDirectory,
    [string]$InnoCompiler = "$PSScriptRoot/.tools/inno/ISCC.exe"
)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $version = (Get-Content packaging/release.json -Raw | ConvertFrom-Json).version
    & .\.buildenv\Scripts\python.exe scripts/fetch_sources.py
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la preparacion de fuentes externas.' }
    # PyInstaller writes normal INFO output to stderr in Windows PowerShell 5.
    $ErrorActionPreference = 'Continue'
    & .\.buildenv\Scripts\python.exe -m PyInstaller --clean --noconfirm --windowed --onedir --name Nukify --distpath "releases/$version" --icon assets/nukify-logo.png --paths desktop --add-data 'desktop;desktop' --collect-all PyOpenColorIO --add-data 'assets;assets' desktop/app.py
    $buildExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($buildExit -ne 0) { throw 'Fallo el build de Nukify.' }
    & .\.buildenv\Scripts\python.exe scripts/package_standalone.py --blender-dir $BlenderDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Fallo el empaquetado del motor.' }
    & $InnoCompiler "/DAppVersion=$version" packaging/Nukify.iss
    if ($LASTEXITCODE -ne 0) { throw 'Fallo el instalador.' }
} finally { Pop-Location }
