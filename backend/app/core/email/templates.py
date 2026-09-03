"""Plain-text and HTML email bodies."""

from __future__ import annotations


def _html_wrapper(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; color: #1a1a1a; line-height: 1.5;">
{body}
<p style="color: #666; font-size: 12px;">Fourse — torneios de TCG</p>
</body>
</html>"""


def verification_email(*, verify_url: str, hours: int) -> tuple[str, str, str]:
    subject = "Confirme seu e-mail — Fourse"
    text = (
        "Olá,\n\n"
        "Confirme seu endereço de e-mail clicando no link abaixo:\n\n"
        f"{verify_url}\n\n"
        f"O link é válido por {hours} horas.\n\n"
        "Se você não criou uma conta, ignore este e-mail.\n"
    )
    html = _html_wrapper(
        f"<p>Olá,</p>"
        f"<p>Confirme seu endereço de e-mail:</p>"
        f'<p><a href="{verify_url}">{verify_url}</a></p>'
        f"<p>O link é válido por <strong>{hours} horas</strong>.</p>"
        "<p>Se você não criou uma conta, ignore este e-mail.</p>"
    )
    return subject, text, html


def invite_email(*, claim_url: str, display_name: str, days: int) -> tuple[str, str, str]:
    subject = "Finalize seu cadastro — Fourse"
    text = (
        f"Olá, {display_name},\n\n"
        "Você foi convidado(a) a criar sua conta na plataforma Fourse.\n\n"
        f"Acesse o link para definir sua senha e concluir o cadastro:\n\n"
        f"{claim_url}\n\n"
        f"O link é válido por {days} dias.\n"
    )
    html = _html_wrapper(
        f"<p>Olá, <strong>{display_name}</strong>,</p>"
        "<p>Você foi convidado(a) a criar sua conta na plataforma Fourse.</p>"
        f'<p><a href="{claim_url}">Concluir cadastro</a></p>'
        f"<p>O link é válido por <strong>{days} dias</strong>.</p>"
    )
    return subject, text, html


def password_reset_email(*, reset_url: str, days: int) -> tuple[str, str, str]:
    subject = "Redefinir senha — Fourse"
    text = (
        "Recebemos um pedido para redefinir sua senha.\n\n"
        f"Acesse o link abaixo:\n\n"
        f"{reset_url}\n\n"
        f"O link é válido por {days} dias.\n\n"
        "Se você não solicitou isso, ignore este e-mail.\n"
    )
    html = _html_wrapper(
        "<p>Recebemos um pedido para redefinir sua senha.</p>"
        f'<p><a href="{reset_url}">Redefinir senha</a></p>'
        f"<p>O link é válido por <strong>{days} dias</strong>.</p>"
        "<p>Se você não solicitou isso, ignore este e-mail.</p>"
    )
    return subject, text, html


def promo_update_email(
    *,
    display_name: str,
    action_name: str,
    action_url: str,
    change_lines: list[str],
) -> tuple[str, str, str]:
    subject = f"Atualização: {action_name}"
    bullets_text = "\n".join(f"- {line}" for line in change_lines)
    text = (
        f"Olá, {display_name},\n\n"
        f"A ação promocional “{action_name}” foi atualizada:\n\n"
        f"{bullets_text}\n\n"
        f"Veja os detalhes: {action_url}\n"
    )
    items = "".join(f"<li>{_escape(line)}</li>" for line in change_lines)
    html = _html_wrapper(
        f"<p>Olá, <strong>{_escape(display_name)}</strong>,</p>"
        f"<p>A ação promocional <strong>{_escape(action_name)}</strong> foi atualizada:</p>"
        f"<ul>{items}</ul>"
        f'<p><a href="{_escape(action_url)}">Ver ação promocional</a></p>'
    )
    return subject, text, html


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
