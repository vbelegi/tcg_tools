# Pester tests for Docker / VPS packaging (Phase 1)

BeforeAll {
    $RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    if (-not (Test-Path (Join-Path $RepoRoot "Dockerfile"))) {
        $RepoRoot = Split-Path -Parent $PSScriptRoot
    }
    $script:RepoRoot = $RepoRoot
}

Describe "Docker packaging files" {
    It "has Dockerfile at repo root" {
        Test-Path (Join-Path $script:RepoRoot "Dockerfile") | Should -Be $true
    }

    It "has docker-compose.yml with app, db, caddy" {
        $compose = Get-Content (Join-Path $script:RepoRoot "docker-compose.yml") -Raw
        $compose | Should -Match '(?m)^\s*app:\s*$'
        $compose | Should -Match '(?m)^\s*db:\s*$'
        $compose | Should -Match '(?m)^\s*caddy:\s*$'
    }

    It "has deploy entrypoint, backup, offsite, vps-deploy and Caddyfile" {
        Test-Path (Join-Path $script:RepoRoot "deploy\docker-entrypoint.sh") | Should -Be $true
        Test-Path (Join-Path $script:RepoRoot "deploy\backup-db.sh") | Should -Be $true
        Test-Path (Join-Path $script:RepoRoot "deploy\backup-offsite.sh") | Should -Be $true
        Test-Path (Join-Path $script:RepoRoot "deploy\vps-deploy.sh") | Should -Be $true
        Test-Path (Join-Path $script:RepoRoot "deploy\Caddyfile") | Should -Be $true
    }

    It "has .env.example with MySQL and bootstrap keys" {
        $envExample = Get-Content (Join-Path $script:RepoRoot ".env.example") -Raw
        $envExample | Should -Match 'MYSQL_PASSWORD='
        $envExample | Should -Match 'MYSQL_ROOT_PASSWORD='
        $envExample | Should -Match 'TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD='
        $envExample | Should -Match 'SITE_ADDRESS='
        $envExample | Should -Match 'BACKUP_RCLONE_REMOTE'
    }

    It "documents V2 web deploy" {
        Test-Path (Join-Path $script:RepoRoot "docs\V2_WEB.md") | Should -Be $true
    }

    It "has VPS runbook" {
        Test-Path (Join-Path $script:RepoRoot "docs\RUNBOOK_VPS.md") | Should -Be $true
    }

    It "has VPS deploy workflow" {
        Test-Path (Join-Path $script:RepoRoot ".github\workflows\deploy-vps.yml") | Should -Be $true
    }

    It "prod lock includes pymysql" {
        $lock = Get-Content (Join-Path $script:RepoRoot "backend\requirements-prod.lock") -Raw
        $lock | Should -Match '(?i)pymysql=='
    }

    It "gitignore keeps .env out of git but allows .env.example" {
        $gi = Get-Content (Join-Path $script:RepoRoot ".gitignore") -Raw
        $gi | Should -Match '(?m)^\.env\s*$'
        $gi | Should -Match '\.env\.\*'
        $gi | Should -Match '!\.env\.example'
    }
}

Describe "docker compose config" {
    It "renders compose when Docker is available" -Skip:(-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Push-Location $script:RepoRoot
        try {
            $env:MYSQL_PASSWORD = "test-pass"
            $env:MYSQL_ROOT_PASSWORD = "test-root"
            $env:SITE_ADDRESS = ":80"
            docker compose config 2>&1 | Out-Null
            $LASTEXITCODE | Should -Be 0
        }
        finally {
            Pop-Location
            Remove-Item Env:MYSQL_PASSWORD -ErrorAction SilentlyContinue
            Remove-Item Env:MYSQL_ROOT_PASSWORD -ErrorAction SilentlyContinue
            Remove-Item Env:SITE_ADDRESS -ErrorAction SilentlyContinue
        }
    }
}
