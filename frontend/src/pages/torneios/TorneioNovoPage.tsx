import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { SeFormatOptions, type SeBoConfig } from "../../components/SeFormatOptions";
import { Switch } from "../../components/Switch";

export function TorneioNovoPage() {
  const navigate = useNavigate();
  const { data: presets } = useQuery({ queryKey: ["presets"], queryFn: api.getPresets });
  const { data: tcgGames } = useQuery({
    queryKey: ["tcg-games"],
    queryFn: () => api.listTcgGames(),
  });
  const [name, setName] = useState("");
  const [eventDate, setEventDate] = useState(new Date().toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState("19:00");
  const [description, setDescription] = useState("");
  const [tcgGameId, setTcgGameId] = useState("");
  const [format, setFormat] = useState<"swiss" | "single_elimination">("swiss");
  const [maxRounds, setMaxRounds] = useState("");
  const [entryFee, setEntryFee] = useState("35");
  const [bestOf, setBestOf] = useState(3);
  const [presetId, setPresetId] = useState("standard");
  const [thirdPlaceMatch, setThirdPlaceMatch] = useState(false);
  const [seBoConfig, setSeBoConfig] = useState<SeBoConfig>({});
  const [expectedPlayers, setExpectedPlayers] = useState("8");
  const [registrationOpen, setRegistrationOpen] = useState(true);
  const [pairingMode, setPairingMode] = useState<"platform" | "manual">("platform");
  const [error, setError] = useState("");

  const sePhaseRounds = useMemo(() => {
    const n = parseInt(expectedPlayers, 10);
    if (!Number.isFinite(n) || n < 2) return Math.ceil(Math.log2(8));
    return Math.ceil(Math.log2(n));
  }, [expectedPlayers]);

  const mutation = useMutation({
    mutationFn: () => {
      const rounds = maxRounds ? parseInt(maxRounds, 10) : null;
      if (rounds != null && format === "swiss" && rounds < 2) {
        const ok = window.confirm(
          "Menos de 2 rodadas é incomum mesmo para 4 jogadores. Deseja criar assim mesmo?",
        );
        if (!ok) throw new Error("cancelado");
      }
      if (!tcgGameId) {
        throw new Error("Selecione o TCG do torneio.");
      }
      return api.createTorneio({
        name,
        event_date: eventDate,
        format,
        max_rounds: rounds,
        entry_fee: parseFloat(entryFee) || 0,
        best_of: bestOf,
        premiacao_preset_id: presetId,
        third_place_match: format === "single_elimination" ? thirdPlaceMatch : false,
        se_bo_config:
          format === "single_elimination" && Object.keys(seBoConfig).length > 0
            ? seBoConfig
            : undefined,
        registration_open: registrationOpen,
        description: description.trim() || null,
        start_time: startTime || null,
        tcg_game_id: Number(tcgGameId),
        pairing_mode: pairingMode,
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
      <Link to="/torneios" className="torneio-back">
        ← Torneios
      </Link>
      <h1>Novo torneio</h1>
      <div className="form-row">
        <label htmlFor="torneio-name">Nome</label>
        <input id="torneio-name" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div className="form-row">
        <label htmlFor="torneio-tcg">TCG</label>
        <select
          id="torneio-tcg"
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
        <label htmlFor="torneio-date">Data</label>
        <input
          id="torneio-date"
          type="date"
          value={eventDate}
          onChange={(e) => setEventDate(e.target.value)}
        />
      </div>
      <div className="form-row">
        <label htmlFor="torneio-time">Horário (opcional)</label>
        <input
          id="torneio-time"
          type="time"
          value={startTime}
          onChange={(e) => setStartTime(e.target.value)}
        />
      </div>
      <div className="form-row">
        <label htmlFor="torneio-desc">Descrição (calendário)</label>
        <textarea
          id="torneio-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="Breve texto para o calendário público"
        />
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
          <input
            type="number"
            min={1}
            value={maxRounds}
            onChange={(e) => setMaxRounds(e.target.value)}
          />
        </div>
      )}
      <div className="form-row">
        <label>Valor inscrição (R$)</label>
        <input
          type="number"
          step="0.01"
          value={entryFee}
          onChange={(e) => setEntryFee(e.target.value)}
        />
      </div>
      <div className="form-row">
        <label>Melhor de (padrão global)</label>
        <select value={bestOf} onChange={(e) => setBestOf(+e.target.value)}>
          <option value={1}>1</option>
          <option value={3}>3</option>
          <option value={5}>5</option>
        </select>
      </div>
      {format === "single_elimination" && (
        <div className="form-row">
          <label>Jogadores esperados (para opções Bo por fase)</label>
          <input
            type="number"
            min={2}
            value={expectedPlayers}
            onChange={(e) => setExpectedPlayers(e.target.value)}
          />
        </div>
      )}
      {format === "single_elimination" && (
        <SeFormatOptions
          thirdPlaceMatch={thirdPlaceMatch}
          onThirdPlaceMatchChange={setThirdPlaceMatch}
          seBoConfig={seBoConfig}
          onSeBoConfigChange={setSeBoConfig}
          defaultBestOf={bestOf}
          maxRounds={sePhaseRounds}
        />
      )}
      <div className="form-row">
        <label>Preset premiação</label>
        <select value={presetId} onChange={(e) => setPresetId(e.target.value)}>
          {presetIds.map((id) => (
            <option key={id} value={id}>
              {presets?.presets[id]?.label ?? id}
            </option>
          ))}
        </select>
      </div>
      <div className="form-row">
        <Switch
          checked={pairingMode === "manual"}
          onChange={(checked) => setPairingMode(checked ? "manual" : "platform")}
        >
          Sem rodadas na plataforma (operação externa — colocações manuais)
        </Switch>
      </div>
      <div className="form-row">
        <Switch checked={registrationOpen} onChange={setRegistrationOpen}>
          Inscrições abertas (self-inscrição)
        </Switch>
      </div>
      {error && <p className="error">{error}</p>}
      <button
        className="primary"
        onClick={() => mutation.mutate()}
        disabled={!name || mutation.isPending}
      >
        Criar
      </button>
    </div>
  );
}
