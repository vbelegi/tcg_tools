import { FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { api } from "../api/client";
import type { PromoAction } from "../api/types";
import { Modal } from "./Modal";

type Props = {
  open: boolean;
  action: PromoAction;
  onClose: () => void;
  onSaved: (action: PromoAction) => void;
};

export function AcaoEditModal({ open, action, onClose, onSaved }: Props) {
  const [name, setName] = useState(action.name);
  const [startDate, setStartDate] = useState(action.start_date);
  const [endDate, setEndDate] = useState(action.end_date);
  const [description, setDescription] = useState(action.description ?? "");
  const [showInCalendar, setShowInCalendar] = useState(action.show_in_calendar);
  const [maxParticipants, setMaxParticipants] = useState(
    action.max_participants != null ? String(action.max_participants) : "",
  );
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setName(action.name);
    setStartDate(action.start_date);
    setEndDate(action.end_date);
    setDescription(action.description ?? "");
    setShowInCalendar(action.show_in_calendar);
    setMaxParticipants(action.max_participants != null ? String(action.max_participants) : "");
    setError("");
  }, [open, action]);

  const save = useMutation({
    mutationFn: () =>
      api.updatePromoAction(action.id, {
        name: name.trim(),
        start_date: startDate,
        end_date: endDate,
        description: description.trim() || null,
        show_in_calendar: showInCalendar,
        max_participants: maxParticipants ? Number(maxParticipants) : null,
      }),
    onSuccess: (updated) => {
      onSaved(updated);
      onClose();
    },
    onError: (e) => setError((e as Error).message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    if (endDate < startDate) {
      setError("A data de término não pode ser anterior à data de início.");
      return;
    }
    save.mutate();
  };

  return (
    <Modal
      open={open}
      title="Editar ação"
      onClose={onClose}
      footer={
        <>
          <button className="secondary" type="button" onClick={onClose}>
            Cancelar
          </button>
          <button className="primary" type="submit" form="acao-edit-form" disabled={save.isPending}>
            {save.isPending ? "Salvando…" : "Salvar"}
          </button>
        </>
      }
    >
      <form id="acao-edit-form" onSubmit={onSubmit}>
        <div className="form-row">
          <label htmlFor="edit-acao-nome">Nome</label>
          <input
            id="edit-acao-nome"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="edit-acao-tipo">Tipo</label>
          <input id="edit-acao-tipo" value={action.type_label} disabled />
          <p className="field-hint">O tipo não pode ser alterado depois que a ação for criada.</p>
        </div>
        <div className="form-row">
          <label htmlFor="edit-acao-inicio">Data de início</label>
          <input
            id="edit-acao-inicio"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="edit-acao-fim">Data de término</label>
          <input
            id="edit-acao-fim"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="edit-acao-desc">Descrição</label>
          <textarea
            id="edit-acao-desc"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div className="form-row">
          <label htmlFor="edit-acao-limite">Limite de participantes</label>
          <input
            id="edit-acao-limite"
            type="number"
            min={1}
            value={maxParticipants}
            placeholder="sem limite"
            onChange={(e) => setMaxParticipants(e.target.value)}
          />
        </div>
        <div className="form-row">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showInCalendar}
              onChange={(e) => setShowInCalendar(e.target.checked)}
            />
            Exibir no calendário
          </label>
        </div>
        <div className="form-row">
          <label className="checkbox-label">
            <input type="checkbox" checked={action.published} disabled />
            Pública
          </label>
          <p className="field-hint">A publicação é feita pelo botão Publicar no topo da página.</p>
        </div>
        {error && <p className="error">{error}</p>}
      </form>
    </Modal>
  );
}
