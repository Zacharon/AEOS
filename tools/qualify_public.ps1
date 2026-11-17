param([Parameter(Mandatory=$true)][string]$WorkRoot)
$ErrorActionPreference = 'Stop'
$aeosRepo = Split-Path -Parent $PSScriptRoot
$aeosWork = [IO.Path]::GetFullPath($WorkRoot)
if (Test-Path -LiteralPath $aeosWork) { throw 'Qualification requires an absent work directory.' }
New-Item -ItemType Directory -Path $aeosWork | Out-Null
python -B "$PSScriptRoot/build_public.py" | Set-Content -LiteralPath (Join-Path $aeosWork 'build.json')
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
$aeosExtract = Join-Path $aeosWork 'extracted package'
python -B "$PSScriptRoot/qualify_public.py" --extract-public-3 "$aeosExtract"
if ($LASTEXITCODE -ne 0) { throw 'Extraction failed.' }
Push-Location -LiteralPath $aeosExtract
try {
    # Execute exactly the shared command block rendered into current guides.
    & "$PSScriptRoot/first_run_commands.ps1" *> (Join-Path $aeosWork 'startup.log')
} finally { Pop-Location }
$aeosPython = Join-Path $aeosWork 'aeos env/Scripts/python.exe'
& "$aeosPython" -B "$PSScriptRoot/qualify_public.py" --work "$aeosWork"
if ($LASTEXITCODE -ne 0) { throw 'Qualification failed; inspect preserved logs.' }
