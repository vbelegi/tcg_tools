# Pester tests for Embed-Python.ps1

BeforeAll {
    $ModuleRoot = Split-Path -Parent $PSScriptRoot
    . (Join-Path $ModuleRoot "lib\Embed-Python.ps1")
}

Describe "Initialize-EmbedPythonPathFile" {
    It "enables site-packages in _pth file" {
        $tmp = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_.FullName }
        $emb = Join-Path $tmp.FullName "python"
        New-Item -ItemType Directory -Path $emb | Out-Null
        @(
            "python313.zip",
            "#import site"
        ) | Set-Content (Join-Path $emb "python313._pth")

        Initialize-EmbedPythonPathFile -EmbDir $emb | Out-Null
        $content = Get-Content (Join-Path $emb "python313._pth")
        $content | Should -Contain "import site"
        $content | Should -Contain "Lib\site-packages"

        Remove-Item $tmp.FullName -Recurse -Force
    }
}

Describe "Get-EmbedPythonZipUrl" {
    It "builds expected URL for 3.13.0" {
        Get-EmbedPythonZipUrl -Version "3.13.0" | Should -Be "https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip"
    }
}
