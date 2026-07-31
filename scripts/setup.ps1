# TCG Tools — setup inicial (Windows)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

$Backend = Join-Path $Root "backend"

$Frontend = Join-Path $Root "frontend"

$Runtime = Join-Path $Root "runtime"



Write-Host "TCG Tools — Setup" -ForegroundColor Cyan



function Get-EmbeddablePython {

    param([string]$RuntimeDir)

    $EmbDir = Join-Path $RuntimeDir "python"

    $PyExe = Join-Path $EmbDir "python.exe"

    if (Test-Path $PyExe) { return $PyExe }



    Write-Host "Baixando Python 3.13 embeddable..." -ForegroundColor Yellow

    New-Item -ItemType Directory -Force -Path $EmbDir | Out-Null

    $ZipUrl = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip"

    $ZipPath = Join-Path $RuntimeDir "python-embed.zip"

    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing

    Expand-Archive -Path $ZipPath -DestinationPath $EmbDir -Force

    Remove-Item $ZipPath -Force



    $PthFile = Get-ChildItem -Path $EmbDir -Filter "python*._pth" | Select-Object -First 1

    if ($PthFile) {

        $content = Get-Content $PthFile.FullName

        $content = $content -replace "#import site", "import site"

        if ($content -notcontains "Lib\site-packages") {

            $content += "Lib\site-packages"

        }

        Set-Content -Path $PthFile.FullName -Value $content

    }



    $GetPip = Join-Path $RuntimeDir "get-pip.py"

    if (-not (Test-Path $GetPip)) {

        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip -UseBasicParsing

    }

    & $PyExe $GetPip --no-warn-script-location

    return $PyExe

}



function Install-BackendDeps {

    param([string]$PythonExe)

    Set-Location $Backend

    if ($PythonExe -match " ") {

        & py -3.13 -m pip install -e ".[dev]"

    } else {

        & $PythonExe -m pip install -e ".[dev]"

    }

    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias Python." }

}



$PythonExe = $null

$uv = Get-Command uv -ErrorAction SilentlyContinue

if ($uv) {

    Write-Host "Usando uv para ambiente Python 3.13..."

    New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

    Set-Location $Backend

    uv venv (Join-Path $Runtime "venv") --python 3.13

    $PythonExe = Join-Path $Runtime "venv\Scripts\python.exe"

    uv pip install -e ".[dev]" --python $PythonExe

} else {

    $py313 = $null

    try {

        $null = & py -3.13 -c "import sys" 2>$null

        if ($LASTEXITCODE -eq 0) { $py313 = "py -3.13" }

    } catch { }



    if ($py313) {

        Write-Host "Usando Python 3.13 (py -3.13)..."

        Install-BackendDeps -PythonExe $py313

    } else {

        Write-Host "py -3.13 nao encontrado; tentando Python embeddable..." -ForegroundColor Yellow

        New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

        $PythonExe = Get-EmbeddablePython -RuntimeDir $Runtime

        Install-BackendDeps -PythonExe $PythonExe

    }

}



Write-Host "Build frontend..."

Set-Location $Frontend

if (Get-Command npm -ErrorAction SilentlyContinue) {

    npm ci 2>$null; if ($LASTEXITCODE -ne 0) { npm install }

    npm run build

} else {

    Write-Host "AVISO: npm nao encontrado. Instale Node.js e execute 'npm run build' em frontend/" -ForegroundColor Yellow

}



$DataDir = if ($env:TCGTOOLS_DATA_DIR) { $env:TCGTOOLS_DATA_DIR } else { Join-Path $Root "data" }

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

New-Item -ItemType Directory -Force -Path (Join-Path $Root "logs") | Out-Null

New-Item -ItemType Directory -Force -Path (Join-Path $Root "exports") | Out-Null



Write-Host "Setup concluido. Use 'scripts\Iniciar TCG Tools.bat' para iniciar." -ForegroundColor Green

