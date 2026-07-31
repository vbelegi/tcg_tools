import { Modal } from "./Modal";

type RaffleResultModalProps = {
  open: boolean;
  winners: string[];
  onClose: () => void;
  onRedraw?: () => void;
  redrawPending?: boolean;
};

export function RaffleResultModal({
  open,
  winners,
  onClose,
  onRedraw,
  redrawPending,
}: RaffleResultModalProps) {
  return (
    <Modal
      open={open}
      title="Resultado do sorteio"
      onClose={onClose}
      footer={
        <>
          {onRedraw && (
            <button className="secondary" onClick={onRedraw} disabled={redrawPending}>
              Sortear novamente
            </button>
          )}
          <button className="primary" onClick={onClose}>
            Fechar
          </button>
        </>
      }
    >
      {winners.length === 0 ? (
        <p>Nenhum sorteado.</p>
      ) : (
        <ol className="raffle-winners">
          {winners.map((name, i) => (
            <li key={`${i}-${name}`}>
              <span className="raffle-winners-rank">Sorteado {i + 1}</span>
              <span className="raffle-winners-name">{name}</span>
            </li>
          ))}
        </ol>
      )}
    </Modal>
  );
}
