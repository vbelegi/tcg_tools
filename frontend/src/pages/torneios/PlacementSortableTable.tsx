import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { PlacementRow } from "./colocacaoOrder";
import { Switch } from "../../components/Switch";

type SortableRowProps = {
  row: PlacementRow;
  onPlacementChange: (playerId: number, placement: string) => void;
  onDropToggle: (playerId: number, isDrop: boolean) => void;
  onDecklistChange: (playerId: number, decklist: string) => void;
};

function SortablePlacementRow({
  row,
  onPlacementChange,
  onDropToggle,
  onDecklistChange,
}: SortableRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: row.player_id,
    disabled: row.is_drop,
  });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <tr
      ref={setNodeRef}
      style={style}
      className={row.is_drop ? "admin-row-inactive" : isDragging ? "colocacao-row-dragging" : undefined}
    >
      <td className="externo-col-place">
        <div className="colocacao-place-cell">
          {!row.is_drop && (
            <button
              type="button"
              className="colocacao-drag-handle"
              aria-label={`Arrastar ${row.name}`}
              {...attributes}
              {...listeners}
            >
              ⋮⋮
            </button>
          )}
          <input
            type="number"
            min={1}
            value={row.is_drop ? "" : row.placement}
            disabled={row.is_drop}
            onChange={(e) => onPlacementChange(row.player_id, e.target.value)}
            aria-label={`Colocação de ${row.name}`}
          />
        </div>
      </td>
      <td>
        <strong>{row.name}</strong>
      </td>
      <td className="externo-col-flags">
        <Switch
          checked={row.is_drop}
          onChange={(checked) => onDropToggle(row.player_id, checked)}
        >
          Drop/WO
        </Switch>
      </td>
      <td>
        <input
          value={row.decklist}
          placeholder="Nome ou URL"
          onChange={(e) => onDecklistChange(row.player_id, e.target.value)}
        />
      </td>
    </tr>
  );
}

type PlacementTableBodyProps = {
  rows: PlacementRow[];
  setRows: React.Dispatch<React.SetStateAction<PlacementRow[]>>;
};

export function PlacementSortableTableBody({ rows, setRows }: PlacementTableBodyProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const rankedIds = rows.filter((r) => !r.is_drop).map((r) => r.player_id);

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setRows((prev) => {
      const ranked = prev.filter((r) => !r.is_drop);
      const drops = prev.filter((r) => r.is_drop);
      const oldIndex = ranked.findIndex((r) => r.player_id === active.id);
      const newIndex = ranked.findIndex((r) => r.player_id === over.id);
      if (oldIndex < 0 || newIndex < 0) return prev;
      const moved = arrayMove(ranked, oldIndex, newIndex).map((r, idx) => ({
        ...r,
        placement: String(idx + 1),
      }));
      return [...moved, ...drops];
    });
  };

  const updateRow = (playerId: number, patch: Partial<PlacementRow>) => {
    setRows((prev) => prev.map((r) => (r.player_id === playerId ? { ...r, ...patch } : r)));
  };

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
      <SortableContext items={rankedIds} strategy={verticalListSortingStrategy}>
        <tbody>
          {rows.map((row) => (
            <SortablePlacementRow
              key={row.player_id}
              row={row}
              onPlacementChange={(id, placement) => updateRow(id, { placement })}
              onDropToggle={(id, is_drop) =>
                setRows((prev) => {
                  const next = prev.map((r) =>
                    r.player_id === id ? { ...r, is_drop, placement: is_drop ? "" : r.placement } : r,
                  );
                  const ranked = next.filter((r) => !r.is_drop);
                  const drops = next.filter((r) => r.is_drop);
                  const renumbered = ranked.map((r, idx) => ({ ...r, placement: String(idx + 1) }));
                  return [...renumbered, ...drops];
                })
              }
              onDecklistChange={(id, decklist) => updateRow(id, { decklist })}
            />
          ))}
        </tbody>
      </SortableContext>
    </DndContext>
  );
}
