# TCG Tools Launcher

Launcher Windows (`TCGTools.exe`) com bandeja do sistema: inicia uvicorn, abre o navegador e gerencia ciclo de vida do servidor local.

## Pré-requisitos

- Go **1.22+**
- Windows (build alvo)

## Estrutura

```text
launcher/
├── main.go                 # wiring (~30 linhas)
└── internal/
    ├── app/                # orquestrador
    ├── config/             # launcher_config.json em %APPDATA%\TCGTools
    ├── instance/           # mutex single-instance
    ├── process/            # spawn uvicorn + health check
    ├── tray/               # wrapper energye/systray (único import da lib)
    ├── registry/           # autostart HKCU Run
    └── browser/            # abrir URL no navegador padrão
```

## Comandos

```powershell
cd launcher
go mod tidy
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out
go build -ldflags "-H windowsgui -s -w" -o TCGTools.exe .
```

## Cobertura

Meta **≥80%** (gate no CI). Pacotes com lógica testável: `config`, `process`, `registry`, `instance`.

Exclusões documentadas do threshold manual: `main.go`, `internal/tray` (UI nativa), stubs Windows-only.

## Configuração

Arquivo `%APPDATA%\TCGTools\launcher_config.json`:

```json
{
  "port": 8000,
  "start_with_windows": false
}
```

Log de debug: `%APPDATA%\TCGTools\launcher.log`

## Dev local (sem instalador)

1. Build frontend e backend conforme README raiz
2. Coloque Python embeddable em `runtime/python/` ou use `py -3.13`
3. Execute `go run .` a partir de `launcher/` com `TCGTOOLS_DATA_DIR` apontando para `./data`

Em produção instalada, o executável fica na raiz de `C:\Program Files\TCG Tools\` ao lado de `backend/`, `frontend/dist/` e `runtime/python/`.

## Systray

Usa [`github.com/energye/systray/v2`](https://github.com/energye/systray) (pure Go, sem CGO).
