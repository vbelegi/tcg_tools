import { Link } from "react-router-dom";

const WHATSAPP_E164 = "551631903190";
const WHATSAPP_DISPLAY = "(16) 3190-3190";
const CONTACT_EMAIL = "contato@fourse.com.br";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-start">
        <nav className="site-footer-links" aria-label="Informações legais">
          <Link to="/termos">Termos de uso</Link>
          <span aria-hidden="true">·</span>
          <Link to="/privacidade">Privacidade</Link>
        </nav>
        <p className="site-footer-meta">
          <span>Araraquara (SP)</span>
          <span aria-hidden="true">·</span>
          <a
            href={`https://wa.me/${WHATSAPP_E164}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {WHATSAPP_DISPLAY}
          </a>
          <span aria-hidden="true">·</span>
          <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        </p>
      </div>
      <a
        className="powered-by"
        href="https://fourse.com.br"
        target="_blank"
        rel="noopener noreferrer"
      >
        <span>Powered by</span>
        <img
          className="fourse-logo-img"
          src="/brand/fourse-logo.png"
          alt="FOURSE"
          width={120}
          height={24}
          decoding="async"
        />
      </a>
    </footer>
  );
}
