param([Parameter(Mandatory=$true)][string]$BlenderPath)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $BlenderPath)) {
    throw 'Indicá Blender 4.5 LTS con -BlenderPath.'
}
$launchScript = Join-Path $PSScriptRoot 'scripts\launch.py'
# A separate session with factory preferences. Does not save user preferences.
& $BlenderPath --factory-startup --python $launchScript
