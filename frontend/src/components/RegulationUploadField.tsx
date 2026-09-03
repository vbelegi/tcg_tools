import { useState } from "react";

import { api } from "../api/client";
import type { PromoAction, PromoRegulation } from "../api/types";
import { FilePicker } from "./FilePicker";

type Props = {
  actionId: number;
  current: PromoRegulation | null;
  history?: PromoRegulation[];
  onUploaded: (action: PromoAction) => void;
};

export function RegulationUploadField({ actionId, current, history = [], onUploaded }: Props) {
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState("");

  const upload = async (file: File) => {
    setError("");
    setProgress(0);
    try {
      const action = await api.uploadPromoRegulation(actionId, file, setProgress);
      onUploaded(action);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setProgress(null);
    }
  };

  const superseded = history.filter((version) => version.version !== current?.version);

  return (
    <div className="form-row regulation-field">
      <label htmlFor={`regulamento-${actionId}`}>Regulamento (PDF)</label>
      <p className="field-hint">
        Envie o arquivo PDF do regulamento — não é um link. Cada envio cria uma nova versão e
        preserva a anterior.
      </p>
      <div className="regulation-field-actions">
        <FilePicker
          id={`regulamento-${actionId}`}
          accept=".pdf,application/pdf"
          disabled={progress !== null}
          buttonLabel="Escolher PDF"
          onFile={(file) => void upload(file)}
        />
        {current && (
          <a href={current.url} target="_blank" rel="noreferrer">
            Ver regulamento ({current.display_name})
          </a>
        )}
      </div>

      {progress !== null && (
        <progress className="regulation-progress" max={100} value={progress}>
          {progress}%
        </progress>
      )}

      {error && <p className="error">{error}</p>}

      {superseded.length > 0 && (
        <details className="regulation-history">
          <summary>Versões anteriores ({superseded.length})</summary>
          <ul>
            {superseded.map((version) => (
              <li key={version.version}>
                <a href={version.url} target="_blank" rel="noreferrer">
                  {version.display_name}
                </a>
                {version.uploaded_at && (
                  <span className="muted"> · {version.uploaded_at.slice(0, 10)}</span>
                )}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
