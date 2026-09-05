import { useState } from "react";

import { api } from "../api/client";

export type DecklistImportMeta = {
  source: string;
  source_id: string;
  source_url: string;
  name: string | null;
  format: string | null;
  price_low_brl: number | null;
};

type Props = {
  decklist: string;
  onDecklistChange: (text: string) => void;
  meta: DecklistImportMeta | null;
  onMetaChange: (meta: DecklistImportMeta | null) => void;
  textareaRows?: number;
  className?: string;
};

export function LigaMagicDeckImportFields({
  decklist,
  onDecklistChange,
  meta,
  onMetaChange,
  textareaRows = 3,
  className,
}: Props) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const importDeck = async () => {
    const trimmed = url.trim();
    if (!trimmed) {
      setError("Cole a URL do deck na LigaMagic.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const preview = await api.previewDeckImport(trimmed);
      onDecklistChange(preview.plain_text);
      onMetaChange({
        source: preview.source,
        source_id: preview.source_id,
        source_url: preview.source_url,
        name: preview.name,
        format: preview.format,
        price_low_brl:
          preview.price_low_brl == null ? null : Number(preview.price_low_brl),
      });
    } catch (e) {
      setError((e as Error).message || "Falha ao importar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={className ?? "resultado-deck-edit"}>
      <textarea
        className="resultado-deck-input"
        rows={textareaRows}
        placeholder="Lista em texto ou importe da LigaMagic"
        value={decklist}
        onChange={(e) => {
          onDecklistChange(e.target.value);
          if (meta) onMetaChange(null);
        }}
      />
      <div className="resultado-deck-import">
        <input
          type="url"
          className="resultado-deck-input"
          placeholder="URL LigaMagic"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button type="button" className="secondary" disabled={busy} onClick={() => void importDeck()}>
          {busy ? "Importando…" : "Importar"}
        </button>
      </div>
      {error ? (
        <p className="error" style={{ margin: "0.25rem 0 0" }}>
          {error}
        </p>
      ) : null}
      {meta ? (
        <p className="field-hint" style={{ margin: "0.25rem 0 0" }}>
          {meta.name || "Importado"}
          {meta.format ? ` · ${meta.format}` : ""}
          {meta.price_low_brl != null
            ? ` · R$ ${Number(meta.price_low_brl).toFixed(2)} (menor)`
            : ""}
        </p>
      ) : null}
    </div>
  );
}
