"""Type registry. Adding a promotional action type means adding it here."""

from __future__ import annotations

from app.core.promo.types.base import PromoTypeHandler
from app.core.promo.types.raffle_purchase_right import RafflePurchaseRightHandler

_HANDLERS: dict[str, PromoTypeHandler] = {
    RafflePurchaseRightHandler.key: RafflePurchaseRightHandler(),
}


def known_types() -> list[PromoTypeHandler]:
    return list(_HANDLERS.values())


def is_known_type(key: str) -> bool:
    return key in _HANDLERS


def get_handler(key: str) -> PromoTypeHandler | None:
    return _HANDLERS.get(key)
