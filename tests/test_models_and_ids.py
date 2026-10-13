from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from esheon.ids import bot_code_of, make_client_order_id
from esheon.models import (
    Fill,
    OrderIntent,
    OrderType,
    PriceLabel,
    Quote,
    Side,
    TimeInForce,
)

UTC = timezone.utc
T0 = datetime(2026, 10, 13, 14, 30, tzinfo=UTC)


def intent(**kw):
    base = dict(
        client_order_id="ESHEON-SDAY-20261013143000-1a2b3c4d",
        bot_id="stock_daily",
        strategy_version="macd_ema@1",
        symbol="SPY",
        side=Side.BUY,
        qty=Decimal("0.5"),
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        created_at=T0,
    )
    base.update(kw)
    return OrderIntent(**base)


def test_intent_valid():
    assert intent().qty == Decimal("0.5")


@pytest.mark.parametrize(
    "kw",
    [
        {"qty": Decimal("0")},
        {"created_at": datetime(2026, 10, 13, 14, 30)},  # naive
        {"order_type": OrderType.LIMIT},  # no limit price
        {"order_type": OrderType.STOP},  # no stop price
    ],
)
def test_intent_rejects_bad_input(kw):
    with pytest.raises(ValueError):
        intent(**kw)


def test_fill_must_be_a_real_fill():
    kw = dict(client_order_id="x", symbol="SPY", side=Side.BUY, qty=Decimal(1), price=Decimal("500"), ts=T0)
    assert Fill(**kw).label is PriceLabel.PAPER_FILL  # default
    assert Fill(**kw, label=PriceLabel.LIVE_FILL).label is PriceLabel.LIVE_FILL
    for label in (PriceLabel.QUOTE_ACTUAL, PriceLabel.BAR_PROXY):
        with pytest.raises(ValueError):
            Fill(**kw, label=label)


def test_quote_staleness_and_validation():
    q = Quote("SPY", Decimal("500.00"), Decimal("500.02"), T0, provider="iex")
    assert not q.is_stale(T0 + timedelta(seconds=5), timedelta(seconds=10))
    assert q.is_stale(T0 + timedelta(seconds=11), timedelta(seconds=10))
    with pytest.raises(ValueError):
        Quote("SPY", Decimal("501"), Decimal("500"), T0, provider="iex")


def test_client_order_ids_unique_and_attributable():
    ids = {make_client_order_id("SDAY", T0) for _ in range(500)}
    assert len(ids) == 500
    assert all(bot_code_of(i) == "SDAY" for i in ids)
    assert bot_code_of("ESHEL-ZDTE-123") is None  # legacy bots' IDs are not Esheon's


@pytest.mark.parametrize("code", ["s", "sday", "TOOLONGCODE", "SD-Y"])
def test_bad_bot_codes(code):
    with pytest.raises(ValueError):
        make_client_order_id(code, T0)
