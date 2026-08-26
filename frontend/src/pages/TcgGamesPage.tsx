import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { api } from "../api/client";

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
    <div>
      <h1>TCGs</h1>
      <p style={{ opacity: 0.85 }}>Cadastro de jogos para o calendário (cor dos chips).</p>

      <form onSubmit={onSubmit} className="card" style={{ marginTop: "1rem", maxWidth: 420 }}>
        <h2>Novo TCG</h2>
        <div className="form-row">
          <label htmlFor="tcg-name">Nome</label>
          <input id="tcg-name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="form-row">
          <label htmlFor="tcg-color">Cor (hex)</label>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input
              id="tcg-color"
              type="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              style={{ width: 48, height: 36, padding: 0 }}
            />
            <input value={color} onChange={(e) => setColor(e.target.value)} />
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        <button className="primary" type="submit" disabled={create.isPending}>
          Adicionar
        </button>
      </form>

      {isLoading && <p>Carregando…</p>}
      <table style={{ marginTop: "1.5rem" }}>
        <thead>
          <tr>
            <th>Cor</th>
            <th>Nome</th>
            <th>Slug</th>
            <th>Ativo</th>
          </tr>
        </thead>
        <tbody>
          {games.map((g) => (
            <tr key={g.id} style={{ opacity: g.active === false ? 0.5 : 1 }}>
              <td>
                <input
                  type="color"
                  value={g.color_hex}
                  onChange={(e) => updateColor.mutate({ id: g.id, color_hex: e.target.value })}
                  title={g.color_hex}
                  style={{ width: 40, height: 28, padding: 0 }}
                />
              </td>
              <td>{g.name}</td>
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
  );
}
