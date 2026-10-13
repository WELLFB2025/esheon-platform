"""Client order IDs: unique, attributable to a bot, and safe to look up after a timeout."""

from __future__ import annotations

import re
import secrets
from datetime import datetime

from .models import _require_utc

_BOT_CODE = re.compile(r"^[A-Z0-9]{2,8}$")
_ID = re.compile(r"^ESHEON-([A-Z0-9]{2,8})-(\d{14})-([0-9a-f]{8})$")
MAX_LEN = 48  # Alpaca allows 128; keep well under


def make_client_order_id(bot_code: str, now: datetime, nonce: str | None = None) -> str:
    """Return e.g. ``ESHEON-SDAY-20261013143000-1a2b3c4d``.

    Distinct prefix from the existing ESHEL-* bots, so orders never collide with theirs.
    """
    if not _BOT_CODE.match(bot_code):
        raise ValueError("bot_code must be 2-8 uppercase letters/digits")
    _require_utc(now, "now")
    nonce = nonce or secrets.token_hex(4)
    if not re.fullmatch(r"[0-9a-f]{8}", nonce):
        raise ValueError("nonce must be 8 lowercase hex chars")
    cid = f"ESHEON-{bot_code}-{now:%Y%m%d%H%M%S}-{nonce}"
    assert len(cid) <= MAX_LEN
    return cid


def bot_code_of(client_order_id: str) -> str | None:
    """Recover the owning bot from an ID, or None if it isn't an Esheon ID."""
    m = _ID.match(client_order_id)
    return m.group(1) if m else None
