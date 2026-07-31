# Instalador único — estratégia e atualizações

## Objetivo

Um instalador Windows que a loja executa **uma vez** (ou para atualizar) sem clonar repositório, instalar Node ou rodar scripts manualmente.

## Recomendação: build versionada (não Git em runtime)

| Abordagem | Prós | Contras |
|-----------|------|---------|
| **Instalador apontando para Git** | Sempre “último commit” | Requer Git + rede na loja; builds não reproduzíveis; quebra se repo for privado |
| **Instalador a partir de build (recomendado)** | Versão fixa, testada, offline | Requer pipeline de release |

**Use build versionada:** cada release gera um pacote `TCGTools-1.x.x-setup.exe` com backend, frontend buildado, Python embeddable e scripts.

## O que compõe o instalador

1. **Python 3.13 embeddable** em `runtime/python/` (já suportado por `setup.ps1`)
2. **Backend** instalado via `pip install` no embeddable
3. **Frontend** — `frontend/dist/` (sem Node na máquina alvo)
4. **Atalho / `.bat`** — equivalente a `Iniciar TCG Tools.bat`
5. **Dados** — `%APPDATA%\TCGTools\` (SQLite, presets migrados)

### Ferramentas possíveis

- **[Inno Setup](https://jrsoftware.org/isinfo.php)** (gratuito) — script `.iss` copia arquivos, cria atalho, registra desinstalador
- **WiX / MSI** — mais corporativo, maior curva de aprendizado

## Pipeline de release (sugestão)

```text
tag v1.1.0
  → CI: pytest + coverage + npm test + npm build
  → Empacotar artefato (zip ou Inno Setup)
  → Anexar ao GitHub Release
```

Script local de empacotamento (futuro): `scripts/build-release.ps1`

## Atualizações

### Modelo recomendado: reinstalar por cima

1. Usuário baixa `TCGTools-1.2.0-setup.exe` do Release.
2. Executa o instalador **sobre** a instalação existente.
3. O instalador:
   - **Substitui** binários (`runtime/`, `backend/app`, `frontend/dist`, scripts)
   - **Preserva** `%APPDATA%\TCGTools\` (banco e dados do usuário)
   - Roda migrações Alembic no **primeiro start** (já implementado no lifespan)

### O que NÃO sobrescrever

- `%APPDATA%\TCGTools\tcg_tools.db`
- Presets customizados se armazenados em data dir (futuro)
- `exports/` e `logs/` do usuário

### Downgrade

Não suportado oficialmente. Faça backup do `.db` antes de instalar versão anterior.

## Auto-update (futuro, opcional)

- App consulta `releases/latest` (GitHub API) na inicialização
- Notifica “Nova versão 1.2.0 disponível” com link para download
- **Não** auto-baixar Git; baixar apenas o instalador assinado do Release

## Checklist para implementar o instalador

- [ ] `scripts/build-release.ps1` — setup + build frontend + copiar para staging
- [ ] `scripts/installer.iss` (Inno Setup)
- [ ] GitHub Action `release.yml` em tag
- [ ] Documentar caminho de instalação padrão (`C:\Program Files\TCG Tools\`)
- [ ] Teste em VM Windows limpa (sem Python/Node pré-instalados)

## Perguntas frequentes

**Instalar do Git na loja?**  
Possível via `git pull` + `setup.ps1`, mas exige Git, Node (build) e conhecimento técnico. Não recomendado para operação diária.

**Re-executar instalador faz overwrite completo?**  
Sim, dos **arquivos do programa**. Dados em `%APPDATA%\TCGTools\` devem ser preservados pelo script do instalador.

**Precisa desinstalar antes de atualizar?**  
Não, se o instalador usar modo upgrade (Inno Setup `UsePreviousAppDir=yes`).
