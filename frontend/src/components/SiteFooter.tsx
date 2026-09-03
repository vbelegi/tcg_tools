import { Link } from "react-router-dom";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <nav className="site-footer-links" aria-label="Informações legais">
        <Link to="/termos">Termos de uso</Link>
        <span aria-hidden="true">·</span>
        <Link to="/privacidade">Privacidade</Link>
      </nav>
      <a
        className="powered-by"
        href="https://fourse.com.br"
        target="_blank"
        rel="noopener noreferrer"
      >
        <span>Powered by</span>
        <span className="fourse-logo">FOURSE</span>
      </a>
    </footer>
  );
}
