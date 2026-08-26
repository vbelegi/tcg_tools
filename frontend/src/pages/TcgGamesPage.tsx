import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { api } from "../api/client";
import { tcgIconUrl } from "../utils/tcgIcons";

export function TcgGamesPage() {
  const qc = useQueryClient();
  const { data: games = [], isLoading } = useQuery({
    queryKey: ["tcg-games-admin"],
    queryFn: () => api.listTcgGames(true),
  });
  const [name, setName] = useState("");
  const [color, setColor] = useState("#888888");
  const [error, setError] = useState("");

  const create = useMutation({
    mutationFn: () => api.createTcgGame({ name, color_hex: color }),
    onSuccess: () => {
      setName("");
      setError("");
      qc.invalidateQueries({ queryKey: ["tcg-games-admin"] });
      qc.invalidateQueries({ queryKey: ["tcg-games"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      api.updateTcgGame(id, { active }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tcg-games-admin"] });
      qc.invalidateQueries({ queryKey: ["tcg-games"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const updateColor = useMutation({
    mutationFn: ({ id, color_hex }: { id: number; color_hex: string }) =>
      api.updateTcgGame(id, { color_hex }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tcg-games-admin"] });
      qc.invalidateQueries({ queryKey: ["tcg-games"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    create.mutate();
  };

  return (
    <div className="admin-page">
      <header className="torneio-manage-header">
        <div>
          <h1>TCGs</h1>
          <p className="torneio-manage-meta">
            Jogos do calendário e chips · {games.length} cadastrado(s)
          </p>
        </div>
      </header>

      <details className="torneio-advanced admin-create-panel">
        <summary>Novo TCG</summary>
        <form onSubmit={onSubmit} className="admin-form-dense">
          <div className="admin-form-grid">
            <div className="form-row">
              <label htmlFor="tcg-name">Nome</label>
              <input id="tcg-name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="form-row">
              <label htmlFor="tcg-color">Cor</label>
              <div className="admin-color-row">
                <input
                  id="tcg-color"
                  type="color"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                />
                <input value={color} onChange={(e) => setColor(e.target.value)} />
              </div>
            </div>
          </div>
          {error && <p className="error">{error}</p>}
          <button className="primary" type="submit" disabled={create.isPending}>
            {create.isPending ? "Adicionando…" : "Adicionar"}
          </button>
        </form>
      </details>

      {isLoading && <p>Carregando…</p>}

      <div className="resultado-table-wrap">
        <table className="resultado-table">
          <thead>
            <tr>
              <th>Jogo</th>
              <th>Cor</th>
              <th>Slug</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {games.map((g) => (
              <tr key={g.id} className={g.active === false ? "admin-row-inactive" : undefined}>
                <td>
                  <span className="tcg-row-label">
                    <img src={tcgIconUrl(g.name)} alt="" width={22} height={22} className="tcg-row-icon" />
                    <strong>{g.name}</strong>
                  </span>
                </td>
                <td>
                  <input
                    type="color"
                    value={g.color_hex}
                    onChange={(e) => updateColor.mutate({ id: g.id, color_hex: e.target.value })}
                    title={g.color_hex}
                    className="admin-color-swatch"
                  />
                </td>
                <td>
                  <code>{g.slug}</code>
                </td>
                <td>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => toggle.mutate({ id: g.id, active: g.active === false })}
                  >
                    {g.active === false ? "Reativar" : "Desativar"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
