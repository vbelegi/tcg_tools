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
    <div>
      <h1>Sorteador</h1>
      <p style={{ opacity: 0.85, maxWidth: "40rem" }}>
        Cadastre participantes e sorteie todos de uma vez ou em modo encadeado (1 a 1, sem repetir).
        Enter adiciona · Esc limpa · cole vários nomes de uma vez.
      </p>

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
          ref={nameRef}
          value={nameInput}
          onChange={(e) => setNameInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder="Nome · Enter adiciona · cole lista"
        />
      </div>
      <button className="secondary" type="button" onClick={addParticipant} disabled={!nameInput.trim()}>
        Adicionar participante
      </button>

      <h2 style={{ marginTop: "2rem" }}>Sorteio</h2>
      <RaffleControls
        participants={names}
        description={`Pool atual: ${names.length} participante(s).`}
        primaryButtonLabel="Sortear"
      />
    </div>
  );
}
