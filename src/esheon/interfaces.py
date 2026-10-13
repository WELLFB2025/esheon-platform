"""Draft protocols for the order path.

Strategy -> BotRisk -> CentralRisk + reservation -> OrderManager -> Broker

Strategies never call a Broker. Revised in Milestone 3 after the audit.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from .models import (
    AccountSnapshot,
    BrokerOrder,
    OrderIntent,
    Position,
    RiskDecision,
    Signal,
    StrategyStatus,
)


@runtime_checkable
class Strategy(Protocol):
    bot_id: str
    version: str
    status: StrategyStatus

    def evaluate(self, bars: Any) -> Sequence[Signal]: ...


@runtime_checkable
class BotRisk(Protocol):
    def check(self, signal: Signal, account: AccountSnapshot) -> RiskDecision: ...


@runtime_checkable
class Broker(Protocol):
    """Paper-only broker adapter. Implementations must call safety.require_paper_mode()."""

    def get_account(self) -> AccountSnapshot: ...

    def get_positions(self) -> Sequence[Position]: ...

    def get_order_by_client_id(self, client_order_id: str) -> BrokerOrder | None: ...

    def submit_order(self, intent: OrderIntent) -> BrokerOrder: ...

    def cancel_order(self, client_order_id: str) -> None: ...
