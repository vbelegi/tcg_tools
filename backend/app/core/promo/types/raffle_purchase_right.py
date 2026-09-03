"""Sorteio de Direito de Compra Físico.

Enrolment is deliberately in-store only: staff generates a single-use QR code
that dies on first access, so the link cannot be forwarded to anyone outside.
"""

from __future__ import annotations

from app.models import PromoActionType


class RafflePurchaseRightHandler:
    key = PromoActionType.raffle_purchase_right.value
    label = "Sorteio de Direito de Compra Físico"
    management_panel_key = "raffle_purchase_right"

    def how_to_participate_text(self) -> str:
        return (
            "A inscrição é presencial. Vá até a loja durante o período da ação e peça "
            "ao atendente o QR code de inscrição. O link do QR vale por 10 minutos e "
            "só pode ser usado uma vez, então a leitura precisa ser feita na hora. "
            "É necessário ter conta na plataforma com e-mail verificado. "
            "Após a data de término, os contemplados são definidos por sorteio."
        )
