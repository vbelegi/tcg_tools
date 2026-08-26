import { useEffect, useRef, useState, type ClipboardEvent, type KeyboardEvent } from "react";

import { RaffleControls } from "../../components/RaffleControls";
import { parsePastedNames } from "../../utils/pasteNames";

type Participant = { id: number; name: string };

let nextId = 1;

export function SorteadorPage() {
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [nameInput, setNameInput] = useState("");
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  const addNames = (names: string[]) => {
    if (names.length === 0) return;
    setParticipants((prev) => [
      ...prev,
      ...names.map((name) => ({ id: nextId++, name })),
    ]);
    setNameInput("");
    requestAnimationFrame(() => nameRef.current?.focus());
  };

  const addParticipant = () => {
    const name = nameInput.trim();
    if (!name) return;
    addNames([name]);
  };

  const removeParticipant = (id: number) => {
    setParticipants((prev) => prev.filter((p) => p.id !== id));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      setNameInput("");
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      addParticipant();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    const names = parsePastedNames(e.clipboardData.getData("text"));
    if (names.length <= 1) return;
    e.preventDefault();
    addNames(names);
  };

  const names = participants.map((p) => p.name);

  return (
    <div className="admin-page">
      <header className="torneio-manage-header">
        <div>
          <h1>Sorteador</h1>
          <p className="torneio-manage-meta">
            Enter adiciona · Esc limpa · cole vários nomes · batch ou encadeado
          </p>
        </div>
      </header>

      <section className="resultado-section">
        <div className="resultado-section-head">
          <h2>
            Participantes <span className="torneio-count">{participants.length}</span>
          </h2>
        </div>

        {participants.length > 0 && (
          <ul className="entre-rodadas-chips">
            {participants.map((p) => (
              <li key={p.id}>
                <span className="entre-rodadas-chip chip-with-remove">
                  {p.name}
                  <button
                    type="button"
                    className="chip-remove"
                    aria-label={`Remover ${p.name}`}
                    onClick={() => removeParticipant(p.id)}
                  >
                    ×
                  </button>
                </span>
              </li>
            ))}
          </ul>
        )}

        <div className="admin-inline-add">
          <div className="form-row admin-inline-add-field">
            <label htmlFor="participant-name">Nome</label>
            <input
              id="participant-name"
              ref={nameRef}
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              placeholder="Nome · Enter ou cole lista"
            />
          </div>
          <button
            className="secondary"
            type="button"
            onClick={addParticipant}
            disabled={!nameInput.trim()}
          >
            Adicionar
          </button>
        </div>
      </section>

      <section className="resultado-section">
        <h2>Sorteio</h2>
        <RaffleControls
          participants={names}
          description={`Pool: ${names.length} participante(s)`}
          primaryButtonLabel="Sortear"
          compact
        />
      </section>
    </div>
  );
}
