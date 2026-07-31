import { useState } from "react";

import { RaffleResultModal } from "../../components/RaffleResultModal";
import { drawWinners } from "../../utils/raffle";

type Participant = { id: number; name: string };

let nextId = 1;

export function SorteadorPage() {
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [nameInput, setNameInput] = useState("");
  const [winnerCount, setWinnerCount] = useState("1");
  const [error, setError] = useState("");
  const [winners, setWinners] = useState<string[]>([]);
  const [modalOpen, setModalOpen] = useState(false);

  const addParticipant = () => {
    const name = nameInput.trim();
    if (!name) return;
    setParticipants((prev) => [...prev, { id: nextId++, name }]);
    setNameInput("");
    setError("");
  };

  const removeParticipant = (id: number) => {
    setParticipants((prev) => prev.filter((p) => p.id !== id));
  };

  const runDraw = () => {
    setError("");
    try {
      const count = parseInt(winnerCount, 10);
      const names = participants.map((p) => p.name);
      setWinners(drawWinners(names, count));
      setModalOpen(true);
    } catch (e) {
      setWinners([]);
      setModalOpen(false);
      setError((e as Error).message);
    }
  };

  return (
    <div>
      <h1>Sorteador</h1>
      <p style={{ opacity: 0.85, maxWidth: "40rem" }}>
        Cadastre participantes, defina quantos serão sorteados e o app escolhe os ganhadores de forma
        aleatória (sem repetição na mesma rodada).
      </p>

      {error && <p className="error">{error}</p>}

      <h2>Participantes ({participants.length})</h2>
      {participants.length > 0 && (
        <ul className="participant-list">
          {participants.map((p) => (
            <li key={p.id}>
              {p.name}{" "}
              <button className="secondary" type="button" onClick={() => removeParticipant(p.id)}>
                Remover
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="form-row">
        <label htmlFor="participant-name">Nome</label>
        <input
          id="participant-name"
          value={nameInput}
          onChange={(e) => setNameInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") addParticipant();
          }}
          placeholder="Nome do participante"
        />
      </div>
      <button className="secondary" type="button" onClick={addParticipant} disabled={!nameInput.trim()}>
        Adicionar participante
      </button>

      <div className="form-row" style={{ marginTop: "1.5rem" }}>
        <label htmlFor="winner-count">Número de sorteados</label>
        <input
          id="winner-count"
          type="number"
          min={1}
          max={Math.max(1, participants.length)}
          value={winnerCount}
          onChange={(e) => setWinnerCount(e.target.value)}
        />
      </div>

      <button
        className="primary"
        type="button"
        style={{ marginTop: "1rem" }}
        onClick={runDraw}
        disabled={participants.length === 0}
      >
        Sortear
      </button>

      <RaffleResultModal
        open={modalOpen}
        winners={winners}
        onClose={() => setModalOpen(false)}
        onRedraw={runDraw}
      />
    </div>
  );
}
