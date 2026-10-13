"""Trading-mode gate and secret redaction.

Paper is the default. Live trading happens only when EVERY live condition holds;
any missing, conflicting or unreadable input resolves to a refusal, never to live.
Every broker client Esheon builds must get its mode from ``resolve_trading_mode()``.

Claude Code must never create the arm file, set ESHEON_MODE=live, or handle live keys.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from zoneinfo import ZoneInfo

PAPER_ENDPOINT = "https://paper-api.alpaca.markets"
LIVE_ENDPOINT = "https://api.alpaca.markets"
MARKET_TZ = ZoneInfo("America/New_York")

# Hard ceilings for live trading. A live config above these is refused.
# Raising them is a deliberate code change that needs owner review.
HARD_MAX_ORDER_NOTIONAL = Decimal("1000")
HARD_MAX_DAILY_LOSS = Decimal("250")
HARD_MAX_OPEN_POSITIONS = 5

DEFAULT_ARM_FILE = "~/.esheon/live_arm"
DEFAULT_KILL_FILE = "~/.esheon/KILL"


class LiveTradingRefused(RuntimeError):
    """Raised when configuration is unsafe, ambiguous, or not fully armed."""


class TradingMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


@dataclass(frozen=True)
class LiveLimits:
    max_order_notional: Decimal
    max_daily_loss: Decimal
    max_open_positions: int


@dataclass(frozen=True)
class TradingContext:
    mode: TradingMode
    bot_id: str
    endpoint: str
    key_env: str  # NAME of the env var holding the key id, never its value
    secret_env: str
    limits: LiveLimits | None = None  # set only in LIVE


def _flag(env: Mapping[str, str], name: str) -> str:
    return env.get(name, "").strip().lower()


def _check_url(env: Mapping[str, str], expected: str) -> None:
    for name in ("ALPACA_BASE_URL", "APCA_API_BASE_URL"):
        url = env.get(name, "").strip().rstrip("/").lower()
        if url and url != expected:
            raise LiveTradingRefused(f"{name} does not match the {expected} endpoint; refusing.")


def kill_switch_on(env: Mapping[str, str] | None = None) -> bool:
    env = os.environ if env is None else env
    return Path(env.get("ESHEON_KILL_FILE", DEFAULT_KILL_FILE)).expanduser().exists()


def require_paper_mode(env: Mapping[str, str] | None = None) -> None:
    """Strict paper check for components that must never trade live (e.g. the zone logger)."""
    env = os.environ if env is None else env
    if _flag(env, "ALPACA_PAPER") != "true" or _flag(env, "ESHEON_MODE") not in ("", "paper"):
        raise LiveTradingRefused("This component is paper-only: need ALPACA_PAPER=true and no live mode.")
    _check_url(env, PAPER_ENDPOINT)


def _live_limits(env: Mapping[str, str]) -> LiveLimits:
    try:
        notional = Decimal(env["ESHEON_LIVE_MAX_ORDER_NOTIONAL"])
        daily = Decimal(env["ESHEON_LIVE_MAX_DAILY_LOSS"])
        positions = int(env["ESHEON_LIVE_MAX_OPEN_POSITIONS"])
    except (KeyError, InvalidOperation, ValueError):
        raise LiveTradingRefused("Live limits missing or unreadable; refusing.") from None
    if not (0 < notional <= HARD_MAX_ORDER_NOTIONAL):
        raise LiveTradingRefused(f"Live max order notional must be >0 and <= {HARD_MAX_ORDER_NOTIONAL}.")
    if not (0 < daily <= HARD_MAX_DAILY_LOSS):
        raise LiveTradingRefused(f"Live max daily loss must be >0 and <= {HARD_MAX_DAILY_LOSS}.")
    if not (0 < positions <= HARD_MAX_OPEN_POSITIONS):
        raise LiveTradingRefused(f"Live max open positions must be 1..{HARD_MAX_OPEN_POSITIONS}.")
    return LiveLimits(notional, daily, positions)


def _armed_today(env: Mapping[str, str], now: datetime) -> bool:
    """The owner arms live trading for ONE market day by writing 'LIVE YYYY-MM-DD' to the arm file."""
    path = Path(env.get("ESHEON_LIVE_ARM_FILE", DEFAULT_ARM_FILE)).expanduser()
    try:
        content = path.read_text().strip()
    except OSError:
        return False
    today = now.astimezone(MARKET_TZ).date().isoformat()
    return content == f"LIVE {today}"


def resolve_trading_mode(bot_id: str, now: datetime, env: Mapping[str, str] | None = None) -> TradingContext:
    """Decide paper vs live for one bot. Anything short of a complete live setup is paper or a refusal."""
    env = os.environ if env is None else env
    if now.tzinfo is None:
        raise LiveTradingRefused("now must be timezone-aware")
    mode = _flag(env, "ESHEON_MODE") or "paper"
    paper_flag = _flag(env, "ALPACA_PAPER")

    if mode == "paper":
        if paper_flag != "true":
            raise LiveTradingRefused("ESHEON_MODE is paper but ALPACA_PAPER is not 'true'; conflicting config.")
        _check_url(env, PAPER_ENDPOINT)
        return TradingContext(TradingMode.PAPER, bot_id, PAPER_ENDPOINT, "ALPACA_API_KEY", "ALPACA_SECRET_KEY")

    if mode != "live":
        raise LiveTradingRefused(f"Unknown ESHEON_MODE {mode!r}; refusing.")
    if paper_flag != "false":
        raise LiveTradingRefused("ESHEON_MODE is live but ALPACA_PAPER is not 'false'; conflicting config.")
    _check_url(env, LIVE_ENDPOINT)
    allowed = {b.strip() for b in env.get("ESHEON_LIVE_BOTS", "").split(",") if b.strip()}
    if bot_id not in allowed:
        raise LiveTradingRefused(f"Bot {bot_id!r} is not in ESHEON_LIVE_BOTS; refusing live.")
    for name in ("ALPACA_LIVE_API_KEY", "ALPACA_LIVE_SECRET_KEY"):
        if not key_present(name, env):
            raise LiveTradingRefused(f"{name} is not set; live keys must be separate from paper keys.")
    if env.get("ALPACA_LIVE_API_KEY") == env.get("ALPACA_API_KEY"):
        raise LiveTradingRefused("Live and paper API keys are identical; refusing.")
    limits = _live_limits(env)
    if kill_switch_on(env):
        raise LiveTradingRefused("Kill switch is on; no live trading.")
    if not _armed_today(env, now):
        raise LiveTradingRefused("Live trading is not armed for today's market date.")
    return TradingContext(
        TradingMode.LIVE, bot_id, LIVE_ENDPOINT, "ALPACA_LIVE_API_KEY", "ALPACA_LIVE_SECRET_KEY", limits
    )


def key_present(name: str, env: Mapping[str, str] | None = None) -> bool:
    """Report whether a secret is set, without ever returning its value."""
    env = os.environ if env is None else env
    return bool(env.get(name, "").strip())


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*)\s*[=:]\s*(['\"]?)[^\s'\"]+\2"
)
_ALPACA_KEY_ID = re.compile(r"\b[PA]K[A-Z0-9]{14,}\b")
_ACCOUNT_NUMBER = re.compile(r"\bPA[A-Z0-9]{6,}\b")  # paper accounts; live ones are digit runs below
_LONG_DIGITS = re.compile(r"\b\d{8,}\b")


def redact(text: str) -> str:
    """Mask secrets, Alpaca key IDs and account numbers in text bound for logs or reports."""
    text = _SECRET_ASSIGNMENT.sub(lambda m: f"{m.group(1)}=[REDACTED]", text)
    text = _ALPACA_KEY_ID.sub("[REDACTED_KEY]", text)
    text = _ACCOUNT_NUMBER.sub(_mask_account, text)
    text = _LONG_DIGITS.sub(lambda m: "[REDACTED_" + m.group(0)[-4:] + "]", text)
    return text


def _mask_account(m: re.Match) -> str:
    s = m.group(0)
    # Only mask tokens that contain a digit: avoids words like ACCOUNTS or AAPL-like tickers.
    return "[REDACTED_ACCOUNT]" if any(c.isdigit() for c in s) else s
