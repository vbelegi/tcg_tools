import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";

export function TorneioNovoPage() {
  const navigate = useNavigate();
  const { data: presets } = useQuery({ queryKey: ["presets"], queryFn: api.getPresets });
  const [name, setName] = useState("");
  const [eventDate, setEventDate] = useState(new Date().toISOString().slice(0, 10));
  const [format, setFormat] = useState<"swiss" | "single_elimination">("swiss");
  const [maxRounds, setMaxRounds] = useState("");
  const [entryFee, setEntryFee] = useState("35");
  const [bestOf, setBestOf] = useState(3);
  const [presetId, setPresetId] = useState("standard");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: () => {
      const rounds = maxRounds ? parseInt(maxRounds, 10) : null;
      if (rounds != null && format === "swiss" && rounds < 2) {
        const ok = window.confirm(
          "Menos de 2 rodadas é incomum mesmo para 4 jogadores. Deseja criar assim mesmo?",
        );
        if (!ok) throw new Error("cancelado");
      }
      return api.createTorneio({
        name,
        event_date: eventDate,
        format,
        max_rounds: rounds,
        entry_fee: parseFloat(entryFee) || 0,
        best_of: bestOf,
        premiacao_preset_id: presetId,
      });
    },
    onSuccess: (t) => navigate(`/torneios/${t.id}`),
    onError: (e) => {
      if ((e as Error).message !== "cancelado") setError((e as Error).message);
    },
  });

  const presetIds = presets ? Object.keys(presets.presets) : ["standard"];

  return (
    <div>
      <h1>Novo torneio</h1>
      <div className="form-row">
        <label>Nome</label>
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div className="form-row">
        <label>Data</label>
        <input type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} />
      </div>
      <div className="form-row">
        <label>Formato</label>
        <select value={format} onChange={(e) => setFormat(e.target.value as typeof format)}>
          <option value="swiss">Suíço</option>
          <option value="single_elimination">Eliminatória simples</option>
        </select>
      </div>
      {format === "swiss" && (
        <div className="form-row">
          <label>Rodadas máximas (vazio = automático ceil(log2(N)))</label>
          <input type="number" min={1} value={maxRounds} onChange={(e) => setMaxRounds(e.target.value)} />
        </div>
      )}
      <div className="form-row">
        <label>Valor inscrição (R$)</label>
        <input type="number" step="0.01" value={entryFee} onChange={(e) => setEntryFee(e.target.value)} />
      </div>
      <div className="form-row">
        <label>Melhor de</label>
        <select value={bestOf} onChange={(e) => setBestOf(+e.target.value)}>
          <option value={1}>1</option>
          <option value={3}>3</option>
          <option value={5}>5</option>
        </select>
      </div>
      <div className="form-row">
        <label>Preset premiação</label>
        <select value={presetId} onChange={(e) => setPresetId(e.target.value)}>
          {presetIds.map((id) => (
            <option key={id} value={id}>{presets?.presets[id]?.label ?? id}</option>
          ))}
        </select>
      </div>
      {error && <p className="error">{error}</p>}
      <button className="primary" onClick={() => mutation.mutate()} disabled={!name || mutation.isPending}>
        Criar
      </button>
    </div>
  );
}
