import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "../../api/client";
import { PremiacaoBandsTable } from "../../components/PremiacaoBandsTable";
import { SeFormatOptions, type SeBoConfig } from "../../components/SeFormatOptions";
import type { Preset } from "../../api/types";

type Tab = "calcular" | "tabela" | "presets";

export function PremiacaoPage() {
  const [tab, setTab] = useState<Tab>("calcular");

  return (
    <div>
      <h1>Premiação</h1>
      <div className="tabs">
        {(["calcular", "tabela", "presets"] as Tab[]).map((t) => (
          <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
            {t === "calcular" ? "Calcular" : t === "tabela" ? "Tabela" : "Presets"}
          </button>
        ))}
      </div>
      {tab === "calcular" && <CalcularTab />}
      {tab === "tabela" && <TabelaTab />}
      {tab === "presets" && <PresetsTab />}
    </div>
  );
}

function CalcularTab() {
  const { data: presetsData } = useQuery({ queryKey: ["presets"], queryFn: api.getPresets });
  const [jogadores, setJogadores] = useState(16);
  const [valor, setValor] = useState("");
  const [presetId, setPresetId] = useState("standard");
  const [formato, setFormato] = useState<"swiss" | "single_elimination">("swiss");
  const [thirdPlaceMatch, setThirdPlaceMatch] = useState(false);
  const [bestOf, setBestOf] = useState(3);
  const [seBoConfig, setSeBoConfig] = useState<SeBoConfig>({});

  const sePhaseRounds = useMemo(
    () => Math.ceil(Math.log2(Math.max(jogadores, 2))),
    [jogadores],
  );

  const mutation = useMutation({
    mutationFn: () =>
      api.calcular(
        jogadores,
        presetId,
        valor ? parseFloat(valor) : undefined,
        formato,
        thirdPlaceMatch,
      ),
  });

  const presetIds = presetsData ? Object.keys(presetsData.presets) : ["standard"];

  return (
    <div>
      <div className="form-row">
        <label>Preset</label>
        <select value={presetId} onChange={(e) => setPresetId(e.target.value)}>
          {presetIds.map((id) => (
            <option key={id} value={id}>
              {presetsData?.presets[id]?.label ?? id}
            </option>
          ))}
        </select>
      </div>
      <div className="form-row">
        <label>Formato</label>
        <select value={formato} onChange={(e) => setFormato(e.target.value as typeof formato)}>
          <option value="swiss">Suíço</option>
          <option value="single_elimination">Eliminatória</option>
        </select>
      </div>
      {formato === "single_elimination" && (
        <>
          <div className="form-row">
            <label>Melhor de (referência para torneios)</label>
            <select value={bestOf} onChange={(e) => setBestOf(+e.target.value)}>
              <option value={1}>1</option>
              <option value={3}>3</option>
              <option value={5}>5</option>
            </select>
          </div>
          <SeFormatOptions
            thirdPlaceMatch={thirdPlaceMatch}
            onThirdPlaceMatchChange={setThirdPlaceMatch}
            seBoConfig={seBoConfig}
            onSeBoConfigChange={setSeBoConfig}
            defaultBestOf={bestOf}
            maxRounds={sePhaseRounds}
          />
          <p style={{ fontSize: "0.9rem", opacity: 0.85 }}>
            O cálculo abaixo mostra pools por faixa; Bo por fase vale ao criar um torneio eliminatória.
          </p>
        </>
      )}
      <div className="form-row">
        <label>Jogadores</label>
        <input type="number" min={4} value={jogadores} onChange={(e) => setJogadores(+e.target.value)} />
      </div>
      <div className="form-row">
        <label>Valor inscrição (R$) — opcional</label>
        <input type="number" step="0.01" value={valor} onChange={(e) => setValor(e.target.value)} />
      </div>
      <button className="primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
        Calcular
      </button>
      {mutation.error && <p className="error">{(mutation.error as Error).message}</p>}
      {mutation.data && (
        <div style={{ marginTop: "1.5rem" }}>
          <p>
            <strong>Top {mutation.data.premiados}</strong> — Total: {mutation.data.total_inscricoes}{" "}
            inscrições
          </p>
          {mutation.data.total_creditos != null && (
            <p>
              Total em créditos na loja: <strong>R$ {mutation.data.total_creditos.toFixed(2)}</strong>
              {valor && (
                <span style={{ opacity: 0.85 }}>
                  {" "}
                  (= {jogadores} × R$ {parseFloat(valor).toFixed(2)})
                </span>
              )}
            </p>
          )}
          {mutation.data.bands && mutation.data.bands.length > 0 ? (
            <PremiacaoBandsTable
              bands={mutation.data.bands}
              bandCreditos={mutation.data.band_creditos ?? undefined}
              entryFee={valor ? parseFloat(valor) : undefined}
            />
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Colocação</th>
                  <th>Inscrições</th>
                  {mutation.data.creditos && <th>Créditos na Loja</th>}
                </tr>
              </thead>
              <tbody>
                {mutation.data.premios.map((p, i) => (
                  <tr key={i}>
                    <td>{i + 1}º</td>
                    <td>{p.toFixed(2)}</td>
                    {mutation.data!.creditos && <td>R$ {mutation.data!.creditos![i].toFixed(2)}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

function TabelaTab() {
  const { data: presetsData } = useQuery({ queryKey: ["presets"], queryFn: api.getPresets });
  const [ate, setAte] = useState(32);
  const [presetId, setPresetId] = useState("standard");

  const { data, refetch, isFetching } = useQuery({
    queryKey: ["tabela", ate, presetId],
    queryFn: () => api.tabela(ate, presetId),
    enabled: false,
  });

  const presetIds = presetsData ? Object.keys(presetsData.presets) : ["standard"];

  return (
    <div>
      <div className="form-row">
        <label>Preset</label>
        <select value={presetId} onChange={(e) => setPresetId(e.target.value)}>
          {presetIds.map((id) => (
            <option key={id} value={id}>{presetsData?.presets[id]?.label ?? id}</option>
          ))}
        </select>
      </div>
      <div className="form-row">
        <label>Até N jogadores</label>
        <input type="number" min={4} value={ate} onChange={(e) => setAte(+e.target.value)} />
      </div>
      <button className="primary" onClick={() => refetch()} disabled={isFetching}>Gerar tabela</button>
      {data && data.linhas.length > 0 && (
        <>
          <div style={{ overflowX: "auto", marginTop: "1rem" }}>
            <table>
              <thead>
                <tr>
                  <th>Jogadores</th>
                  <th>Premiados</th>
                  {data.linhas[0].premios.map((_, i) => (
                    <th key={i}>{i + 1}º</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.linhas.map((l) => (
                  <tr key={l.jogadores}>
                    <td>{l.jogadores}</td>
                    <td>{l.premiados}</td>
                    {l.premios.map((p, i) => (
                      <td key={i}>{p.toFixed(2)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="secondary" style={{ marginTop: "1rem" }} onClick={() => api.exportCsv(ate, presetId)}>
            Exportar CSV
          </button>
        </>
      )}
    </div>
  );
}

function PresetsTab() {
  const { data, refetch } = useQuery({ queryKey: ["presets"], queryFn: api.getPresets });
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<Preset | null>(null);
  const [loadedMtime, setLoadedMtime] = useState<number | null>(null);
  const [msg, setMsg] = useState("");

  if (!data) return <p>Carregando...</p>;

  const startEdit = (id: string) => {
    setEditId(id);
    setForm({ ...data.presets[id] });
    setLoadedMtime(data.presets_updated_at ?? null);
    setMsg("");
  };

  const save = async () => {
    if (!editId || !form) return;
    try {
      await api.updatePreset(editId, form, loadedMtime ?? undefined);
      setMsg("Preset salvo. Exports anteriores podem estar desatualizados.");
      const refreshed = await refetch();
      setLoadedMtime(refreshed.data?.presets_updated_at ?? null);
    } catch (e) {
      setMsg((e as Error).message);
    }
  };

  return (
    <div>
      {data.exports_desatualizados && (
        <p className="warning" role="alert">
          Exports CSV podem estar desatualizados — os presets foram alterados após a última exportação.
          Gere novamente na aba Tabela.
        </p>
      )}
      <ul>
        {Object.entries(data.presets).map(([id, p]) => (
          <li key={id} style={{ marginBottom: "0.5rem" }}>
            <strong>{p.label}</strong> ({id}){" "}
            <button className="secondary" onClick={() => startEdit(id)}>Editar</button>
          </li>
        ))}
      </ul>
      {editId && form && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h3>Editar: {editId}</h3>
          {(["label", "min_jogadores", "min_premiados", "max_premiados", "crescimento", "r", "casas_decimais"] as const).map(
            (key) => (
              <div className="form-row" key={key}>
                <label>{key}</label>
                <input
                  value={String(form[key] ?? "")}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      [key]: key === "label" || key === "r" ? e.target.value : +e.target.value,
                    } as Preset)
                  }
                />
              </div>
            ),
          )}
          <div className="form-row">
            <label>fp_k (Fourse Points; vazio = 10)</label>
            <input
              type="number"
              min={1}
              value={form.fp_k ?? ""}
              onChange={(e) => {
                const v = e.target.value;
                setForm({
                  ...form,
                  fp_k: v === "" ? undefined : Number(v),
                } as Preset);
              }}
            />
          </div>
          <button className="primary" onClick={save}>Salvar</button>
        </div>
      )}
      {msg && <p className={msg.includes("salvo") ? "success" : "error"}>{msg}</p>}
    </div>
  );
}
