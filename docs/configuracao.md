# Configuração de premiação (presets)

A premiação usa **presets** armazenados em `%APPDATA%\TCGTools\premiacao_presets.json` (instalação Windows) ou `./data/premiacao_presets.json` (desenvolvimento). Na primeira execução, o arquivo é criado a partir dos defaults em `backend/config/premiacao_presets.json`. A UI em **Premiação → Presets** edita esse arquivo via API.

## Formato do arquivo

```json
{
  "version": 1,
  "default_preset": "standard",
  "presets": {
    "standard": {
      "label": "Standard semanal",
      "min_jogadores": 4,
      "min_premiados": 3,
      "max_premiados": 8,
      "crescimento": 4,
      "r": 0.72,
      "casas_decimais": 2
    }
  }
}
```

| Campo | Descrição |
|-------|-----------|
| `default_preset` | ID usado quando nenhum preset é informado na API ou na UI |
| `label` | Nome exibido na interface |
| `min_jogadores` | Mínimo de jogadores aceito no cálculo e na tabela |
| `min_premiados` | Mínimo de colocados premiados |
| `max_premiados` | Teto de colocados premiados |
| `crescimento` | Escala `floor((N + 1) / crescimento)` — ver [modelo_premiacao.md](modelo_premiacao.md) |
| `r` | Razão da curva exponencial (0 < r < 1) |
| `casas_decimais` | Precisão dos prêmios (0–4); com Créditos na Loja, 2 casas |

## Comportamento

| Situação | Ação |
|----------|------|
| Arquivo ausente | Criado com preset `standard` padrão |
| Preset inválido | API retorna HTTP 422 com mensagem em português |
| Alteração via UI ou `PUT /api/v1/premiacao/presets/{id}` | Grava o JSON completo no disco |

## Migração legada

Na primeira carga, se existir `config/settings.json` (formato flat da CLI antiga) e ainda não houver presets, o sistema importa esses valores para o preset `default`. Esse arquivo **não** é a fonte da verdade após a migração — apenas facilita a transição.

## Exports (`exports/`)

CSV gerados pelo botão **Exportar CSV** (aba Tabela ou via `POST /api/v1/premiacao/export`):

- Encoding UTF-8 com BOM (`utf-8-sig`) para Excel
- Separador `;`
- Nome: `premiacao_{min_jogadores}_a_{limite}.csv`
- Arquivo existente com o mesmo nome é **substituído**
- A pasta `exports/` também recebe cópia opcional no servidor (gitignored)

## Torneios

Ao criar um evento, o preset escolhido é copiado para `events.premiacao_preset` (snapshot). Alterações posteriores nos presets globais **não** afetam torneios já criados. O resultado final fica em `events.premiacao_resultado` após finalizar.

## Variáveis de ambiente

| Variável | Efeito |
|----------|--------|
| `TCGTOOLS_PRESETS_FILE` | Caminho alternativo ao JSON de presets |
| `TCGTOOLS_EXPORTS_DIR` | Pasta de CSV exportados (default: `{data_dir}/exports`) |
| `TCGTOOLS_DATA_DIR` | Pasta de dados (SQLite, exports, logs) |
| `TCGTOOLS_PUBLIC_BASE_URL` | URL pública (convites, verificação de e-mail, cookies Secure em HTTPS) |
| `TCGTOOLS_EMAIL_ENABLED` | `true` em produção para enviar e-mails |
| `TCGTOOLS_EMAIL_FROM` | Remetente (ex.: `Fourse <noreply@fourse.com.br>`) |
| `TCGTOOLS_EMAIL_REPLY_TO` | Reply-To (ex.: `contato@fourse.com.br`) |
| `TCGTOOLS_SMTP_HOST` | SMTP (Hostinger: `smtp.hostinger.com`) |
| `TCGTOOLS_SMTP_PORT` | Porta (465 SSL) |
| `TCGTOOLS_SMTP_USER` / `TCGTOOLS_SMTP_PASSWORD` | Credenciais da caixa de envio |

Em **development**, e-mails são apenas **logados no console** (sem SMTP).

Consulte também [INSTALACAO.md](INSTALACAO.md), [V2_WEB.md](V2_WEB.md) e o [README](../README.md).
