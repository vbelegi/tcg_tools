# Configuração (`settings.json`)

Arquivo: `config/settings.json`

## Comportamento

| Situação | Ação |
|----------|------|
| Arquivo não existe | Criado a partir dos defaults de `core/config.py` |
| Arquivo inválido ou corrompido | Removido, recriado, mensagem no console |
| Alteração pelo menu | Grava somente se o conteúdo mudou |
| Execução normal | Lê **somente** o arquivo; defaults não são mesclados |

## Campos

### `min_jogadores` (int, ≥ 1)

Quantidade mínima de jogadores aceita nas opções de cálculo e na geração de tabela.

### `min_premiados` (int, ≥ 1)

Mínimo de colocados que recebem prêmio, independentemente de `N`.

### `max_premiados` (int, ≥ min_premiados)

Teto de colocados premiados.

### `crescimento` (int, ≥ 1)

Controla quando aumenta o número de premiados:

```
floor((N + 1) / crescimento)
```

Quanto **menor**, mais cedo novos lugares passam a ser premiados.

### `r` (float, 0 < r < 1)

Razão da curva exponencial de pesos. Valores típicos: 0,70–0,80.

### `casas_decimais` (int, 0–4)

Casas decimais dos prêmios. Com Créditos na Loja, 2 casas (centavos) é o usual.

## Valores padrão (somente para criação do arquivo)

```json
{
  "min_jogadores": 4,
  "min_premiados": 3,
  "max_premiados": 8,
  "crescimento": 4,
  "r": 0.72,
  "casas_decimais": 2
}
```

> O `settings.json` existente no repositório pode divergir (ex.: `crescimento: 3`). Isso é intencional — o arquivo vivo prevalece.

## Guardrails

- Campos desconhecidos ou ausentes invalidam o arquivo.
- `max_premiados` deve ser ≥ `min_premiados`.
- `N` informado deve ser ≥ `min_jogadores` e ≥ `min_premiados`.
- Valor de inscrição, quando informado, deve ser > 0.

## Exports (`exports/`)

| Situação | Comportamento |
|----------|---------------|
| Exportar CSV com nome já existente | Arquivo substituído |
| Salvar alteração de configuração | Pergunta se deseja limpar exports antigos |
| Opção `limpar_exports` no menu | Remove todos os CSVs de `exports/` após confirmação |
