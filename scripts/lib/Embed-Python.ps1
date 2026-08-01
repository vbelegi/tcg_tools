# Shared embeddable Python setup for TCG Tools (dev setup + release build).

$Script:DefaultPythonVersion = "3.13.0"
$Script:DefaultEmbedZipUrl = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip"

function Get-EmbedPythonZipUrl {
    param([string]$Version = $Script:DefaultPythonVersion)
    $parts = $Version.Split(".")
    if ($parts.Length -lt 2) { throw "Invalid Python version: $Version" }
    $majorMinor = "$($parts[0]).$($parts[1]).$($parts[2])"
    return "https://www.python.org/ftp/python/$majorMinor/python-$majorMinor-embed-amd64.zip"
}

function Initialize-EmbedPythonPathFile {
    param([string]$EmbDir)

    $PthFile = Get-ChildItem -Path $EmbDir -Filter "python*._pth" | Select-Object -First 1
    if (-not $PthFile) {
        throw "python*._pth not found in $EmbDir"
    }

    $content = Get-Content $PthFile.FullName
    $content = $content -replace "#import site", "import site"
    if ($content -notcontains "Lib\site-packages") {
        $content += "Lib\site-packages"
    }
    Set-Content -Path $PthFile.FullName -Value $content
    return $PthFile.FullName
}

function Install-EmbedPython {
    param(
        [string]$RuntimeDir,
        [string]$ZipUrl = $Script:DefaultEmbedZipUrl,
        [switch]$SkipDownload,
        [string]$ZipPathOverride
    )

    $EmbDir = Join-Path $RuntimeDir "python"
    $PyExe = Join-Path $EmbDir "python.exe"
    if (Test-Path $PyExe) {
        return $PyExe
    }

    New-Item -ItemType Directory -Force -Path $EmbDir | Out-Null

    $ZipPath = if ($ZipPathOverride) { $ZipPathOverride } else { Join-Path $RuntimeDir "python-embed.zip" }

    if (-not $SkipDownload) {
        if (-not (Test-Path $ZipPath)) {
            Write-Host "Baixando Python embeddable..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
        }
        Expand-Archive -Path $ZipPath -DestinationPath $EmbDir -Force
        if ($ZipPath -eq (Join-Path $RuntimeDir "python-embed.zip")) {
            Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
        }
    } elseif (-not (Test-Path $ZipPath)) {
        throw "SkipDownload exige ZipPathOverride existente: $ZipPath"
    } else {
        Expand-Archive -Path $ZipPath -DestinationPath $EmbDir -Force
    }

    Initialize-EmbedPythonPathFile -EmbDir $EmbDir | Out-Null

    $GetPip = Join-Path $RuntimeDir "get-pip.py"
    if (-not (Test-Path $GetPip)) {
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip -UseBasicParsing
    }
    & $PyExe $GetPip --no-warn-script-location
    if ($LASTEXITCODE -ne 0) { throw "get-pip failed." }

    return $PyExe
}

