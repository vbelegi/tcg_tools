# Instalador Windows — TCG Tools

## Para a loja

1. Baixe `TCGTools-{versão}-setup.exe` (GitHub Releases ou pendrive)
2. Execute o instalador (admin necessário — instala em `Program Files`)
3. Aceite SmartScreen se aparecer: **Mais informações → Executar mesmo assim** (instalador não assinado na v1)
4. Configure porta (padrão 8000) e opcionalmente "Iniciar com Windows"
5. Use o atalho **TCG Tools** — abre o navegador em `http://127.0.0.1:{porta}`

**Não é necessário** Python, Node, Git nem scripts PowerShell na loja.

## Atualizar

Execute o novo `setup.exe` **por cima** da instalação existente. Binários são substituídos; dados em `%APPDATA%\TCGTools\` são preservados (DB, config, exports, logs).

## Desinstalar

Painel de Controle → Desinstalar TCG Tools. **Todos os dados** em `%APPDATA%\TCGTools\` são removidos após confirmação. Faça backup de `tcg_tools.db` antes.

## O que o instalador contém

- Python 3.13 embeddable + dependências de produção
- Backend FastAPI + migrações Alembic
- Frontend React buildado (`frontend/dist/`)
- Launcher `TCGTools.exe` (bandeja do sistema)

## Configuração pós-instalação

Arquivo `%APPDATA%\TCGTools\launcher_config.json`:

```json
{
  "port": 8000,
  "start_with_windows": false
}
```

Edite a porta e reinicie o app pelo tray (Encerrar → atalho).

## Gerar instalador (desenvolvedor)

Ver [BUILD_RELEASE.md](BUILD_RELEASE.md).

## Dev com clone do repositório

Use `scripts/setup.ps1` — fluxo separado, não usar na loja.
