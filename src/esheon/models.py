"""Broker-neutral domain models.

Draft: Milestone 1 compares these against the existing bots and revises them.
All timestamps are timezone-aware UTC. Money and quantities are Decimal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"


class OrderStatus(str, Enum):
    INTENDED = "intended"  # persisted, not yet sent
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    UNKNOWN = "unknown"  # ambiguous submit: resolve by client order ID, never blind-retry


class PriceLabel(str, Enum):
    """Where a price came from. Replayed or simulated prices are never fills."""

    QUOTE_ACTUAL = "QUOTE_ACTUAL"
    BAR_PROXY = "BAR_PROXY"
    PAPER_FILL = "PAPER_FILL"


class StrategyStatus(str, Enum):
    EXISTING = "existing"
    REUSED = "reused"
    PARTIAL = "partial"
    SHADOW_ONLY = "shadow-only"
    NOT_STARTED = "not started"


class RiskVerdict(str, Enum):
    APPROVE = "approve"
    REDUCE = "reduce"
    DEFER = "defer"
    REJECT = "reject"
    HALT = "halt"


def _require_utc(ts: datetime, name: str) -> None:
    if ts.tzinfo is None or ts.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be timezone-aware UTC")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: Decimal
    ask: Decimal
    ts: datetime
    provider: str
    label: PriceLabel = PriceLabel.QUOTE_ACTUAL

    def __post_init__(self) -> None:
        _require_utc(self.ts, "Quote.ts")
        if self.bid < 0 or self.ask < 0 or (self.bid and self.ask and self.bid > self.ask):
            raise ValueError("invalid bid/ask")

    def is_stale(self, now: datetime, max_age: timedelta) -> bool:
        return now - self.ts > max_age


@dataclass(frozen=True)
class Signal:
    bot_id: str
    strategy_version: str
    symbol: str
    side: Side
    ts: datetime
    reason: str
    shadow: bool = True  # new rules are shadow-only until the owner promotes them

    def __post_init__(self) -> None:
        _require_utc(self.ts, "Signal.ts")


@dataclass(frozen=True)
class RiskDecision:
    verdict: RiskVerdict
    reason: str
    qty: Decimal = Decimal("0")
    max_loss: Decimal = Decimal("0")  # worst-case loss, not notional
    inputs: dict = field(default_factory=dict)


@dataclass(frozen=True)
class OrderIntent:
    client_order_id: str
    bot_id: str
    strategy_version: str
    symbol: str
    side: Side
    qty: Decimal
    order_type: OrderType
    time_in_force: TimeInForce
    created_at: datetime
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None

    def __post_init__(self) -> None:
        _require_utc(self.created_at, "OrderIntent.created_at")
        if self.qty <= 0:
            raise ValueError("qty must be positive")
        if self.order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT) and self.limit_price is None:
            raise ValueError("limit orders need limit_price")
        if self.order_type in (OrderType.STOP, OrderType.STOP_LIMIT) and self.stop_price is None:
            raise ValueError("stop orders need stop_price")


@dataclass(frozen=True)
class BrokerOrder:
    client_order_id: str
    broker_order_id: str
    status: OrderStatus
    filled_qty: Decimal = Decimal("0")


@dataclass(frozen=True)
class Fill:
    client_order_id: str
    symbol: str
    side: Side
    qty: Decimal
    price: Decimal
    ts: datetime
    label: PriceLabel = PriceLabel.PAPER_FILL

    def __post_init__(self) -> None:
        _require_utc(self.ts, "Fill.ts")
        if self.label is not PriceLabel.PAPER_FILL:
            raise ValueError("a Fill must be a PAPER_FILL; quotes and bar proxies are not fills")


@dataclass(frozen=True)
class Position:
    symbol: str
    qty: Decimal
    avg_price: Decimal
    bot_id: str | None = None  # None = not attributed (e.g. manual broker-side position)


@dataclass(frozen=True)
class AccountSnapshot:
    equity: Decimal
    cash: Decimal
    buying_power: Decimal
    daytrade_count: int
    ts: datetime
    healthy: bool = True

    def __post_init__(self) -> None:
        _require_utc(self.ts, "AccountSnapshot.ts")
