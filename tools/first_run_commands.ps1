$ErrorActionPreference = 'Stop'
$aeosParent = Split-Path -Parent $PWD.Path
$aeosEnvironment = [IO.Path]::GetFullPath((Join-Path $aeosParent 'aeos env'))
$aeosOutput = [IO.Path]::GetFullPath((Join-Path $aeosParent 'aeos first run'))
if ((Test-Path -LiteralPath $aeosEnvironment) -or (Test-Path -LiteralPath $aeosOutput)) {
    throw 'Choose new sibling environment/output names; existing evidence is preserved.'
}
python -c "import platform,sys; sys.exit(0 if platform.python_implementation() == 'CPython' and sys.version_info[:3] == (3,14,5) else 'Use CPython 3.14.5')"
if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
python -m venv "$aeosEnvironment"
if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed.' }
$aeosPython = Join-Path $aeosEnvironment 'Scripts/python.exe'
& "$aeosPython" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Prerequisite installation failed.' }
& "$aeosPython" -B scripts/check_package.py .
if ($LASTEXITCODE -ne 0) { throw 'Package integrity check failed.' }
& "$aeosPython" -B scripts/demo.py --output "$aeosOutput"
if ($LASTEXITCODE -ne 0) { throw 'Demo failed.' }
