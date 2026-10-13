"""Paper-only enforcement and secret redaction.

Every broker client Esheon builds must call ``require_paper_mode()`` first.
There is deliberately no switch that allows live trading.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping

PAPER_ENDPOINT = "https://paper-api.alpaca.markets"


class LiveTradingRefused(RuntimeError):
    """Raised whenever configuration could lead to a non-paper broker connection."""


def require_paper_mode(env: Mapping[str, str] | None = None) -> None:
    """Refuse to continue unless the environment is unambiguously paper-only.

    Rules:
    - ``ALPACA_PAPER`` must be exactly ``true`` (case-insensitive).
    - If ``ALPACA_BASE_URL`` / ``APCA_API_BASE_URL`` is set, it must be the paper endpoint.
    """
    env = os.environ if env is None else env
    if env.get("ALPACA_PAPER", "").strip().lower() != "true":
        raise LiveTradingRefused("ALPACA_PAPER must be 'true'; Esheon is paper-only.")
    for name in ("ALPACA_BASE_URL", "APCA_API_BASE_URL"):
        url = env.get(name, "").strip().rstrip("/").lower()
        if url and url != PAPER_ENDPOINT:
            raise LiveTradingRefused(f"{name} must be the paper endpoint; refusing.")


def key_present(name: str, env: Mapping[str, str] | None = None) -> bool:
    """Report whether a secret is set, without ever returning its value."""
    env = os.environ if env is None else env
    return bool(env.get(name, "").strip())


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*)\s*[=:]\s*(['\"]?)[^\s'\"]+\2"
)
_ALPACA_KEY_ID = re.compile(r"\b[PA]K[A-Z0-9]{14,}\b")
_ACCOUNT_NUMBER = re.compile(r"\bPA[A-Z0-9]{6,}\b")
_LONG_DIGITS = re.compile(r"\b\d{8,}\b")


def redact(text: str) -> str:
    """Mask secrets, Alpaca key IDs and account numbers in text bound for logs or reports."""
    text = _SECRET_ASSIGNMENT.sub(lambda m: f"{m.group(1)}=[REDACTED]", text)
    text = _ALPACA_KEY_ID.sub("[REDACTED_KEY]", text)
    text = _ACCOUNT_NUMBER.sub("[REDACTED_ACCOUNT]", text)
    text = _LONG_DIGITS.sub(lambda m: "[REDACTED_" + m.group(0)[-4:] + "]", text)
    return text
