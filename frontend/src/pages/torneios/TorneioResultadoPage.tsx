import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useEffect, useState } from "react";

import { Link, useParams } from "react-router-dom";

import { RaffleResultModal } from "../../components/RaffleResultModal";
import { api } from "../../api/client";
import { drawWinners } from "../../utils/raffle";



export function TorneioResultadoPage() {

  const { id } = useParams<{ id: string }>();

  const eventId = Number(id);

  const qc = useQueryClient();

  const [decklists, setDecklists] = useState<Record<number, string>>({});
  const [decklistsSaved, setDecklistsSaved] = useState(false);

  const [exportError, setExportError] = useState("");
  const [raffleWinnerCount, setRaffleWinnerCount] = useState("1");
  const [raffleError, setRaffleError] = useState("");
  const [raffleWinners, setRaffleWinners] = useState<string[]>([]);
  const [raffleModalOpen, setRaffleModalOpen] = useState(false);

  useEffect(() => {
    if (!decklistsSaved) return;
    const t = window.setTimeout(() => setDecklistsSaved(false), 2500);
    return () => window.clearTimeout(t);
  }, [decklistsSaved]);



  const { data: torneio } = useQuery({

    queryKey: ["torneio", eventId],

    queryFn: () => api.getTorneio(eventId),

  });



  const { data: classificacao } = useQuery({

    queryKey: ["classificacao", eventId],

    queryFn: () => api.getClassificacao(eventId),

  });



  const { data: premiacao } = useQuery({

    queryKey: ["premiacao-torneio", eventId],

    queryFn: () => api.getPremiacao(eventId),

  });



  const saveDecklists = useMutation({

    mutationFn: () =>

      api.updateDecklists(

        eventId,

        Object.entries(decklists).map(([player_id, decklist]) => ({

          player_id: Number(player_id),

          decklist: decklist || null,

        })),

      ),

    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["classificacao", eventId] });
      setDecklistsSaved(true);
    },

  });



  const handleExport = async () => {

    setExportError("");

    try {

      await api.exportLog(eventId);

    } catch (e) {

      setExportError((e as Error).message);

    }

  };



  const prem = premiacao as { premios: number[]; creditos?: number[] | null; entry_fee?: number } | undefined;

  const showCreditos = prem && (prem.entry_fee ?? 0) > 0 && prem.creditos;

  const eligiblePlayers =
    classificacao?.standings.filter((s) => !s.is_drop).map((s) => s.name) ?? [];

  const runTournamentRaffle = () => {
    setRaffleError("");
    try {
      const count = parseInt(raffleWinnerCount, 10);
      setRaffleWinners(drawWinners(eligiblePlayers, count));
      setRaffleModalOpen(true);
    } catch (e) {
      setRaffleWinners([]);
      setRaffleModalOpen(false);
      setRaffleError((e as Error).message);
    }
  };



  return (

    <div>

      <Link to={`/torneios/${eventId}`}>← Voltar</Link>

      <h1>Resultado final</h1>



      <h2>Classificação</h2>

      {classificacao && (

        <table>

          <thead>

            <tr>

              <th>#</th>

              <th>Jogador</th>

              <th>Pts</th>

              <th>OMW%</th>

              <th>GW%</th>

              <th>Decklist (opcional)</th>

            </tr>

          </thead>

          <tbody>

            {classificacao.standings.map((s) => (

              <tr key={s.player_id}>

                <td>{s.rank_label ?? s.rank}</td>

                <td>{s.name}</td>

                <td>{s.is_drop ? "—" : s.points}</td>

                <td>{s.is_drop ? "—" : `${(s.omw * 100).toFixed(1)}%`}</td>

                <td>{s.is_drop ? "—" : `${(s.gw * 100).toFixed(1)}%`}</td>

                <td>

                  {!s.is_drop && (

                    <input

                      placeholder="Nome ou URL"

                      defaultValue={s.decklist ?? ""}

                      onChange={(e) =>

                        setDecklists({ ...decklists, [s.player_id]: e.target.value })

                      }

                    />

                  )}

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      )}



      <div style={{ marginTop: "1rem" }}>
        <button
          className="secondary"
          onClick={() => saveDecklists.mutate()}
          disabled={saveDecklists.isPending}
        >
          {saveDecklists.isPending ? "Salvando…" : "Salvar decklists"}
        </button>
        {decklistsSaved && (
          <div className="save-feedback success" role="status">
            Salvo com sucesso
          </div>
        )}
      </div>



      <h2 style={{ marginTop: "2rem" }}>Premiação</h2>

      {torneio && torneio.entry_fee === 0 && (

        <p className="warning">

          Inscrição R$ 0 — sem pot a distribuir. Use a aba Premiação para calcular split isolado.

        </p>

      )}

      {prem && (

        <table>

          <thead>

            <tr>

              <th>Colocação</th>

              <th>Inscrições</th>

              {showCreditos && <th>Créditos na Loja</th>}

            </tr>

          </thead>

          <tbody>

            {prem.premios.map((p, i) => (

              <tr key={i}>

                <td>{i + 1}º</td>

                <td>{p}</td>

                {showCreditos && <td>R$ {(prem.creditos![i] ?? 0).toFixed(2)}</td>}

              </tr>

            ))}

          </tbody>

        </table>

      )}



      <h2 style={{ marginTop: "2rem" }}>Sorteio</h2>
      <p style={{ fontSize: "0.9rem", opacity: 0.85 }}>
        Sorteia entre jogadores válidos ({eligiblePlayers.length} — exclui quem deu drop).
      </p>
      {raffleError && <p className="error">{raffleError}</p>}
      <div className="form-row">
        <label htmlFor="raffle-winner-count">Número de sorteados</label>
        <input
          id="raffle-winner-count"
          type="number"
          min={1}
          max={Math.max(1, eligiblePlayers.length)}
          value={raffleWinnerCount}
          onChange={(e) => setRaffleWinnerCount(e.target.value)}
          disabled={eligiblePlayers.length === 0}
        />
      </div>
      <button
        className="secondary"
        type="button"
        style={{ marginTop: "0.75rem" }}
        onClick={runTournamentRaffle}
        disabled={eligiblePlayers.length === 0}
      >
        Sortear entre jogadores do torneio
      </button>

      <RaffleResultModal
        open={raffleModalOpen}
        winners={raffleWinners}
        onClose={() => setRaffleModalOpen(false)}
        onRedraw={runTournamentRaffle}
      />



      {torneio?.status === "finished" && (

        <>

          <button className="primary" style={{ marginTop: "1.5rem" }} onClick={handleExport}>

            Exportar log JSON

          </button>

          {exportError && <p className="error">{exportError}</p>}

        </>

      )}

    </div>

  );

}


