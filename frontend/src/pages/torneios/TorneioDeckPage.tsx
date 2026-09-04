import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../../api/client";
import type { PlayerDeckCard } from "../../api/types";

const SECTION_LABELS: Record<string, string> = {
  commander: "Commander",
  main: "Deck",
  sideboard: "Sideboard",
};

function canHover(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(hover: hover)").matches;
}

function cardHasBack(card: PlayerDeckCard): boolean {
  return Boolean(card.has_back_face || card.image_normal_back || card.image_large_back);
}

function cardFaceLabel(card: PlayerDeckCard, flipped: boolean): string {
  if (flipped && card.printed_name_back) return card.printed_name_back;
  return card.printed_name || card.name;
}

function cardThumbSrc(card: PlayerDeckCard, flipped: boolean): string | null {
  if (flipped) {
    return card.image_normal_back || card.image_small_back || null;
  }
  return card.image_normal || card.image_small || null;
}

function cardZoomSrc(card: PlayerDeckCard, flipped: boolean): string | null {
  if (flipped) {
    return card.image_large_back || card.image_normal_back || card.image_small_back || null;
  }
  return card.image_large || card.image_normal || card.image_small || null;
}

function formatSnapshotDate(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function FlipIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden>
      <path
        fill="currentColor"
        d="M12 6V3L8 7l4 4V8c2.76 0 5 2.24 5 5a5 5 0 0 1-1.46 3.54l1.42 1.42A7 7 0 0 0 19 13c0-3.87-3.13-7-7-7zm-5.54.46L5.04 5.04A7 7 0 0 0 5 13c0 3.87 3.13 7 7 7v3l4-4-4-4v3a5 5 0 0 1-5-5c0-1.48.65-2.81 1.46-3.54z"
      />
    </svg>
  );
}

function FlipButton({ flipped, onToggle }: { flipped: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      className={`deck-card-flip${flipped ? " is-flipped" : ""}`}
      title="Virar carta"
      aria-label={flipped ? "Mostrar frente da carta" : "Mostrar verso da carta"}
      aria-pressed={flipped}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onToggle();
      }}
    >
      <FlipIcon />
    </button>
  );
}

function CardZoomModal({
  card,
  initialFlipped,
  onClose,
}: {
  card: PlayerDeckCard;
  initialFlipped: boolean;
  onClose: () => void;
}) {
  const [flipped, setFlipped] = useState(initialFlipped);
  const hasBack = cardHasBack(card);
  const src = cardZoomSrc(card, flipped);
  const label = cardFaceLabel(card, flipped);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  return (
    <div className="deck-zoom-modal" role="dialog" aria-modal="true" aria-label={label}>
      <button type="button" className="deck-zoom-close" onClick={onClose} aria-label="Fechar">
        ×
      </button>
      <button type="button" className="deck-zoom-backdrop" onClick={onClose} aria-label="Fechar" />
      <div className="deck-zoom-panel">
        {src ? <img src={src} alt={label} /> : null}
        <p className="deck-zoom-caption">
          <span>
            {card.qty}× {label}
          </span>
          {hasBack ? <FlipButton flipped={flipped} onToggle={() => setFlipped((v) => !v)} /> : null}
        </p>
      </div>
    </div>
  );
}

function CardTile({
  card,
  onOpenModal,
}: {
  card: PlayerDeckCard;
  onOpenModal: (c: PlayerDeckCard, flipped: boolean) => void;
}) {
  const [hoverZoom, setHoverZoom] = useState(false);
  const [flipped, setFlipped] = useState(false);
  const hasBack = cardHasBack(card);
  const thumb = cardThumbSrc(card, flipped);
  const zoomSrc = cardZoomSrc(card, flipped);
  const label = cardFaceLabel(card, flipped);

  const onArtEnter = () => {
    if (canHover()) setHoverZoom(true);
  };
  const onArtLeave = () => {
    if (canHover()) setHoverZoom(false);
  };
  const onArtClick = () => {
    if (!canHover()) onOpenModal(card, flipped);
  };

  return (
    <li className="deck-card-tile" title={card.name}>
      {thumb ? (
        <img
          className="deck-card-art"
          src={thumb}
          alt={label}
          loading="lazy"
          width={146}
          height={204}
          onMouseEnter={onArtEnter}
          onMouseLeave={onArtLeave}
          onClick={onArtClick}
        />
      ) : (
        <div
          className="deck-card-placeholder"
          role="button"
          tabIndex={0}
          aria-label={`Ampliar ${label}`}
          onMouseEnter={onArtEnter}
          onMouseLeave={onArtLeave}
          onClick={onArtClick}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onArtClick();
            }
          }}
        >
          ?
        </div>
      )}
      <span className="deck-card-qty">{card.qty}×</span>
      <span className="deck-card-name-row">
        <span className="deck-card-name">{label}</span>
        {hasBack ? <FlipButton flipped={flipped} onToggle={() => setFlipped((v) => !v)} /> : null}
      </span>
      {!card.found ? <span className="deck-card-missing">sem imagem</span> : null}
      {hoverZoom && zoomSrc ? (
        <div className="deck-card-zoom" role="presentation">
          <img src={zoomSrc} alt="" />
        </div>
      ) : null}
    </li>
  );
}

function CardGrid({
  cards,
  onOpenModal,
}: {
  cards: PlayerDeckCard[];
  onOpenModal: (c: PlayerDeckCard, flipped: boolean) => void;
}) {
  return (
    <ul className="deck-card-grid">
      {cards.map((c) => (
        <CardTile key={c.name} card={c} onOpenModal={onOpenModal} />
      ))}
    </ul>
  );
}

export function TorneioDeckPage() {
  const { id, playerId } = useParams<{ id: string; playerId: string }>();
  const eventId = Number(id);
  const pid = Number(playerId);
  const [modal, setModal] = useState<{ card: PlayerDeckCard; flipped: boolean } | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["player-deck", eventId, pid],
    queryFn: () => api.getPlayerDeck(eventId, pid),
    enabled: Number.isFinite(eventId) && Number.isFinite(pid),
  });

  if (isLoading) return <p>Carregando deck…</p>;
  if (isError || !data) {
    return (
      <div className="deck-page">
        <Link to={`/torneios/${eventId}/resultado`} className="torneio-back">
          ← Resultado
        </Link>
        <p className="error">{(error as Error)?.message || "Deck não encontrado."}</p>
      </div>
    );
  }

  const snapshotAt = formatSnapshotDate(data.decklist_imported_at);
  const metaParts = [
    data.decklist_name,
    data.decklist_format,
    data.decklist_price_low_brl != null
      ? `R$ ${Number(data.decklist_price_low_brl).toFixed(2)}`
      : null,
    snapshotAt ? `snapshot ${snapshotAt}` : null,
  ].filter(Boolean);

  const sectionOrder = ["commander", "main", "sideboard"] as const;

  return (
    <div className="deck-page">
      <header className="deck-page-header">
        <div className="deck-page-nav">
          <Link to={`/torneios/${eventId}/resultado`} className="torneio-back">
            ← {data.event_name} · Resultado
          </Link>
          {data.decklist_source_url ? (
            <a
              className="secondary deck-liga-btn"
              href={data.decklist_source_url}
              target="_blank"
              rel="noreferrer"
            >
              Ver na LigaMagic
            </a>
          ) : null}
        </div>
        <h1>{data.player_name}</h1>
        {metaParts.length > 0 ? <p className="deck-page-meta">{metaParts.join(" · ")}</p> : null}
        <p className="field-hint">{data.card_count} cartas · imagens via Scryfall</p>
      </header>

      {sectionOrder.map((sectionKey) => {
        const cards = data.sections[sectionKey] || [];
        if (!cards.length) return null;
        const total = cards.reduce((n, c) => n + c.qty, 0);
        return (
          <section key={sectionKey} className="deck-section">
            <h2>
              {SECTION_LABELS[sectionKey] || sectionKey}{" "}
              <span className="field-hint">({total})</span>
            </h2>
            <CardGrid
              cards={cards}
              onOpenModal={(c, flipped) => setModal({ card: c, flipped })}
            />
          </section>
        );
      })}

      {modal ? (
        <CardZoomModal
          card={modal.card}
          initialFlipped={modal.flipped}
          onClose={() => setModal(null)}
        />
      ) : null}
    </div>
  );
}
