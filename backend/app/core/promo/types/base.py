"""Contract every promotional action type must fulfil.

Generic concerns (CRUD, publishing, regulation, notification, search, calendar,
audit) never look at the type. Only enrolment, the management panel and the
end-of-period behaviour dispatch through a handler.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PromoTypeHandler(Protocol):
    #: Stored in promo_actions.type
    key: str
    #: Shown in the type dropdown
    label: str
    #: Frontend picks the management panel component by this key
    management_panel_key: str

    def how_to_participate_text(self) -> str:
        """Player-facing explanation of how to join this kind of action."""
        ...
