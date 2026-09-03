import { Link } from "react-router-dom";

export function TermosPage() {
  return (
    <div className="legal-page">
      <article className="legal-article">
        <p className="legal-version">Versão 1.0 · setembro 2026</p>
        <h1>Termos de uso</h1>
        <p>
          Estes Termos regem o uso da plataforma TCG Tools operada pela FOURSE (torneios.fourse.com.br),
          para gestão de torneios de card games, ranking Fourse Points e serviços correlatos.
        </p>
        <h2>1. Conta</h2>
        <p>
          Você é responsável por manter a confidencialidade da senha e pelas atividades realizadas com sua
          conta. Contas incomplete criadas pela loja devem ser finalizadas pelo link de convite.
        </p>
        <h2>2. Torneios e conduta</h2>
        <p>
          A participação em torneios está sujeita às regras do evento, check-in e decisões da equipe da loja.
          Resultados, colocações e decklists informados podem ser exibidos publicamente na plataforma.
        </p>
        <h2>3. Conteúdo e propriedade</h2>
        <p>
          Nomes de jogadores, decklists e dados de torneio podem permanecer visíveis no histórico esportivo.
          Em caso de exclusão de conta, o histórico permanece identificado como &quot;Anônimo&quot;.
        </p>
        <h2>4. Disponibilidade</h2>
        <p>
          A plataforma é oferecida &quot;como está&quot;. Podemos alterar funcionalidades ou interromper o serviço
          com aviso razoável quando possível.
        </p>
        <h2>5. Contato</h2>
        <p>
          Dúvidas:{" "}
          <a href="mailto:contato@fourse.com.br">contato@fourse.com.br</a> ·{" "}
          <a href="https://fourse.com.br" target="_blank" rel="noopener noreferrer">
            fourse.com.br
          </a>
        </p>
        <p>
          <Link to="/privacidade">Ver Política de privacidade</Link>
        </p>
      </article>
    </div>
  );
}
