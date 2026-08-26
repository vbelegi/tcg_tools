import { FormEvent, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { api } from "../../api/client";

type PlacementRow = {
  placement: number;
  display_name: string;
  email: string;
  phone: string;
  create_account: boolean;
  is_drop: boolean;
};

function emptyRow(placement: number): PlacementRow {
  return {
    placement,
    display_name: "",
    email: "",
    phone: "",
    create_account: false,
    is_drop: false,
  };
}

export function TorneioExternoPage() {
  const navigate = useNavigate();
  const { data: presets } = useQuery({ queryKey: ["presets"], queryFn: api.getPresets });
  const { data: tcgGames } = useQuery({
    queryKey: ["tcg-games"],
    queryFn: () => api.listTcgGames(),
  });
  const [name, setName] = useState("");
  const [eventDate, setEventDate] = useState(new Date().toISOString().slice(0, 10));
  const [entryFee, setEntryFee] = useState("0");
  const [presetId, setPresetId] = useState("standard");
  const [tcgGameId, setTcgGameId] = useState("");
  const [notes, setNotes] = useState("");
  const [rows, setRows] = useState<PlacementRow[]>([emptyRow(1), emptyRow(2), emptyRow(3), emptyRow(4)]);
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: () => {
      if (!tcgGameId) throw new Error("Selecione o TCG do torneio.");
      return api.createExternalTorneio({
        name,
        event_date: eventDate,
        format: "swiss",
        premiacao_preset_id: presetId,
        entry_fee: parseFloat(entryFee) || 0,
        notes: notes || undefined,
        tcg_game_id: Number(tcgGameId),
        placements: rows
          .filter((r) => r.display_name.trim())
          .map((r) => ({
            placement: r.placement,
            display_name: r.display_name.trim(),
            email: r.email.trim() || undefined,
            phone: r.phone.trim() || undefined,
            create_account: r.create_account,
            is_drop: r.is_drop,
          })),
      });
    },
    onSuccess: (t: { id: number }) => navigate(`/torneios/${t.id}`),
    onError: (e) => setError((e as Error).message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  const presetIds = presets ? Object.keys(presets.presets) : ["standard"];

  return (
    <div>
      <h1>Importar torneio externo</h1>
      <p>Resultados mínimos para FP, ranking e perfis (sem rodadas internas).</p>
      {error && <p className="error">{error}</p>}
      <form onSubmit={onSubmit}>
        <div className="form-row">
          <label>Nome</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="form-row">
          <label htmlFor="externo-tcg">TCG</label>
          <select
            id="externo-tcg"
            value={tcgGameId}
            onChange={(e) => setTcgGameId(e.target.value)}
            required
          >
            <option value="">— selecionar —</option>
            {tcgGames?.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label>Data</label>
          <input type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} required />
        </div>
        <div className="form-row">
          <label>Taxa de inscrição (para cálculo FP)</label>
          <input value={entryFee} onChange={(e) => setEntryFee(e.target.value)} />
        </div>
        <div className="form-row">
          <label>Preset de premiação</label>
          <select value={presetId} onChange={(e) => setPresetId(e.target.value)}>
            {presetIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label>Notas</label>
          <input value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>

        <h2>Colocações</h2>
        {rows.map((row, idx) => (
          <div key={idx} className="card" style={{ marginBottom: "0.75rem" }}>
            <div className="form-row">
              <label>Colocação</label>
              <input
                type="number"
                min={1}
                value={row.placement}
                onChange={(e) => {
                  const next = [...rows];
                  next[idx] = { ...row, placement: parseInt(e.target.value, 10) || 1 };
                  setRows(next);
                }}
              />
            </div>
            <div className="form-row">
              <label>Nome de exibição</label>
              <input
                value={row.display_name}
                onChange={(e) => {
                  const next = [...rows];
                  next[idx] = { ...row, display_name: e.target.value };
                  setRows(next);
                }}
              />
            </div>
            <div className="form-row">
              <label>E-mail (opcional, para criar conta)</label>
              <input
                type="email"
                value={row.email}
                onChange={(e) => {
                  const next = [...rows];
                  next[idx] = { ...row, email: e.target.value };
                  setRows(next);
                }}
              />
            </div>
            <div className="form-row">
              <label>Celular (opcional)</label>
              <input
                value={row.phone}
                onChange={(e) => {
                  const next = [...rows];
                  next[idx] = { ...row, phone: e.target.value };
                  setRows(next);
                }}
              />
            </div>
            <label>
              <input
                type="checkbox"
                checked={row.create_account}
                onChange={(e) => {
                  const next = [...rows];
                  next[idx] = { ...row, create_account: e.target.checked };
                  setRows(next);
                }}
              />{" "}
              Criar conta incompleta
            </label>{" "}
            <label>
              <input
                type="checkbox"
                checked={row.is_drop}
                onChange={(e) => {
                  const next = [...rows];
                  next[idx] = { ...row, is_drop: e.target.checked };
                  setRows(next);
                }}
              />{" "}
              Drop/WO (0 FP)
            </label>
          </div>
        ))}
        <button
          type="button"
          className="secondary"
          onClick={() => setRows([...rows, emptyRow(rows.length + 1)])}
        >
          + colocação
        </button>
        <div style={{ marginTop: "1.5rem" }}>
          <button className="primary" type="submit" disabled={mutation.isPending || !name.trim()}>
            Importar e atribuir FP
          </button>
        </div>
      </form>
    </div>
  );
}
