import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api/client";
import { todayIso } from "./promoFormat";

export function AcaoNovaPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: types } = useQuery({
    queryKey: ["acoes-tipos"],
    queryFn: () => api.listPromoActionTypes(),
  });

  const [name, setName] = useState("");
  const [type, setType] = useState("");
  const [startDate, setStartDate] = useState(todayIso());
  const [endDate, setEndDate] = useState(todayIso());
  const [description, setDescription] = useState("");
  const [published, setPublished] = useState(false);
  const [showInCalendar, setShowInCalendar] = useState(true);
  const [maxParticipants, setMaxParticipants] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!type && types?.length === 1) setType(types[0].key);
  }, [types, type]);

  const create = useMutation({
    mutationFn: () =>
      api.createPromoAction({
        name: name.trim(),
        type,
        start_date: startDate,
        end_date: endDate,
        description: description.trim() || null,
        published,
        show_in_calendar: showInCalendar,
        max_participants: maxParticipants ? Number(maxParticipants) : null,
      }),
    onSuccess: async (action) => {
      await qc.invalidateQueries({ queryKey: ["acoes"] });
      navigate(`/acoes/${action.id}`);
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
    if (!type) {
      setError("Selecione o tipo da ação.");
      return;
    }
    if (endDate < startDate) {
      setError("A data de término não pode ser anterior à data de início.");
      return;
    }
    create.mutate();
  };

  return (
    <div>
      <h1>Nova Ação Promocional</h1>

      <form onSubmit={onSubmit}>
        <div className="form-row">
          <label htmlFor="acao-nome">Nome</label>
          <input id="acao-nome" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>

        <div className="form-row">
          <label htmlFor="acao-tipo">Tipo</label>
          <select id="acao-tipo" value={type} onChange={(e) => setType(e.target.value)} required>
            <option value="">— selecionar —</option>
            {types?.map((t) => (
              <option key={t.key} value={t.key}>
                {t.label}
              </option>
            ))}
          </select>
          <p className="field-hint">O tipo não pode ser alterado depois que a ação for criada.</p>
        </div>

        <div className="form-row">
          <label htmlFor="acao-inicio">Data de início</label>
          <input
            id="acao-inicio"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
          />
        </div>

        <div className="form-row">
          <label htmlFor="acao-fim">Data de término</label>
          <input
            id="acao-fim"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            required
          />
        </div>

        <div className="form-row">
          <label htmlFor="acao-desc">Descrição</label>
          <textarea
            id="acao-desc"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <div className="form-row">
          <label htmlFor="acao-limite">Limite de participantes</label>
          <input
            id="acao-limite"
            type="number"
            min={1}
            value={maxParticipants}
            placeholder="sem limite"
            onChange={(e) => setMaxParticipants(e.target.value)}
          />
          <p className="field-hint">Deixe vazio para não limitar o número de participantes.</p>
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
            <input
              type="checkbox"
              checked={published}
              onChange={(e) => setPublished(e.target.checked)}
            />
            Pública
          </label>
          <p className="field-hint">
            Ações não publicadas ficam visíveis apenas para staff e admin.
          </p>
        </div>

        <p className="field-hint">
          O regulamento em PDF é enviado na página da ação, logo após a criação.
        </p>

        {error && <p className="error">{error}</p>}

        <button className="primary" type="submit" disabled={create.isPending}>
          {create.isPending ? "Criando…" : "Criar"}
        </button>
      </form>
    </div>
  );
}
