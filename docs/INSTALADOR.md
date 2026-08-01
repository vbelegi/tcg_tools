# Instalador Windows — TCG Tools

## Para a loja

1. Baixe `TCGTools-{versão}-setup.exe` (GitHub Releases ou pendrive)
2. Execute o instalador (admin necessário — instala em `Program Files`)
3. Aceite SmartScreen se aparecer: **Mais informações → Executar mesmo assim** (instalador não assinado na v1)
4. Configure porta (padrão 8000) e opcionalmente "Iniciar com Windows"
5. Use o atalho **TCG Tools** — abre o navegador em `http://127.0.0.1:{porta}`

**Não é necessário** Python, Node, Git nem scripts PowerShell na loja.

Cada **usuário Windows** na máquina tem dados próprios em `%APPDATA%\TCGTools\` e pode executar sua própria instância (mutex `Local\TCGTools_SingleInstance`, por sessão de usuário).

## Atualizar

Execute o novo `setup.exe` **por cima** da instalação existente. Binários são substituídos; dados em `%APPDATA%\TCGTools\` são preservados (DB, config, exports, logs).

O wizard **atualiza** `launcher_config.json` (porta e autostart) a cada install/upgrade.

Antes de sobrescrever arquivos, o instalador encerra `TCGTools.exe` e processos `python.exe` filhos em `Program Files\TCG Tools\`.

## Desinstalar

Painel de Controle → Desinstalar TCG Tools.

- Arquivos em **Program Files** são sempre removidos.
- Na tela de progresso, **desmarque por padrão** a opção *"Remover dados locais"* se quiser **manter** `tcg_tools.db`, exports, logs e presets em `%APPDATA%\TCGTools\`.
- Marque a opção para apagar todos os dados locais.

Faça backup de `tcg_tools.db` antes de marcar remoção de dados.

## O que o instalador contém

- Python 3.13 embeddable + dependências de produção (pins exatos em `requirements-prod.lock`)
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

Presets de premiação graváveis: `%APPDATA%\TCGTools\premiacao_presets.json`.

## Gerar instalador (desenvolvedor)

Ver [BUILD_RELEASE.md](BUILD_RELEASE.md).

## Dev com clone do repositório

Use `scripts/setup.ps1` e `scripts/Iniciar TCG Tools.bat` (ou `scripts/start-dev.ps1`). Mesmo mutex do launcher — **não** rode `.bat` e `TCGTools.exe` ao mesmo tempo na mesma sessão.
