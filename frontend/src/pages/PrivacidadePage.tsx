import { Link } from "react-router-dom";

export function PrivacidadePage() {
  return (
    <div className="legal-page">
      <article className="legal-article">
        <p className="legal-version">Versão 1.0 · setembro 2026</p>
        <h1>Política de privacidade</h1>
        <p>
          Esta política descreve como a FOURSE trata dados pessoais na plataforma TCG Tools
          (torneios.fourse.com.br), em conformidade com a LGPD (Lei nº 13.709/2018).
        </p>

        <h2>1. Controlador</h2>
        <p>
          FOURSE — contato:{" "}
          <a href="mailto:contato@fourse.com.br">contato@fourse.com.br</a>
        </p>

        <h2>2. Dados que coletamos</h2>
        <ul>
          <li>Identificação: nome de exibição, e-mail, celular, data de nascimento</li>
          <li>Menores de 18 anos: nome e celular do responsável</li>
          <li>Conta: senha (armazenada com hash), avatar opcional</li>
          <li>Torneios: inscrições, presença, decklists, resultados, Fourse Points</li>
          <li>Técnicos: cookie de sessão essencial</li>
        </ul>

        <h2>3. Finalidades e bases</h2>
        <ul>
          <li>Operar conta, torneios e ranking (execução de serviços / interesse legítimo)</li>
          <li>
            Comunicações comerciais da loja (WhatsApp e/ou e-mail), salvo oposição do titular —
            interesse legítimo no relacionamento com a comunidade; você pode desativar em Meu Perfil
          </li>
          <li>Segurança, prevenção a abuso e cumprimento legal</li>
        </ul>

        <h2>4. Perfil e dados públicos</h2>
        <p>
          Nome de exibição, avatar, histórico de torneios, decklists e ranking podem ser públicos.
          E-mail, celular, nascimento e dados do responsável <strong>não</strong> são expostos em
          perfis públicos.
        </p>

        <h2>5. Cookies</h2>
        <p>
          Usamos o cookie essencial <code>tcgtools_session</code> (HttpOnly) apenas para autenticação.
          Não utilizamos cookies de publicidade de terceiros nesta aplicação.
        </p>

        <h2>6. Compartilhamento</h2>
        <p>
          Dados podem ser acessados por administradores e staff da loja para operar eventos. Provedores
          de hospedagem/e-mail processam dados sob instrução. Não vendemos dados pessoais.
        </p>

        <h2>7. Retenção</h2>
        <ul>
          <li>Contas incomplete sem ativação: anonimização após 180 dias</li>
          <li>
            Exclusão de conta: dados de identificação removidos; histórico de torneio permanece como
            &quot;Anônimo&quot;
          </li>
          <li>Backups operacionais seguem política de retenção da infraestrutura</li>
        </ul>

        <h2>8. Seus direitos</h2>
        <p>
          Acesso e correção (perfil), portabilidade (exportação dos seus dados), oposição a marketing
          (preferências no perfil), exclusão de conta e demais direitos da LGPD. Solicitações:{" "}
          <a href="mailto:contato@fourse.com.br">contato@fourse.com.br</a>
        </p>

        <h2>9. Menores</h2>
        <p>
          Cadastro de menores exige dados do responsável. Comunicações comerciais não são direcionadas
          a menores de 18 anos pela plataforma.
        </p>

        <p>
          <Link to="/termos">Ver Termos de uso</Link>
        </p>
      </article>
    </div>
  );
}
