from datetime import datetime, timezone
from decimal import Decimal

import pytest

from esheon.safety import (
    LIVE_ENDPOINT,
    PAPER_ENDPOINT,
    LiveTradingRefused,
    TradingMode,
    require_paper_mode,
    resolve_trading_mode,
)

# 2026-10-13 14:30 UTC = 10:30 ET
NOW = datetime(2026, 10, 13, 14, 30, tzinfo=timezone.utc)


@pytest.fixture
def live_env(tmp_path):
    arm = tmp_path / "live_arm"
    arm.write_text("LIVE 2026-10-13\n")
    return {
        "ESHEON_MODE": "live",
        "ALPACA_PAPER": "false",
        "ESHEON_LIVE_BOTS": "stock_daily, zdte",
        "ALPACA_API_KEY": "paperkey",
        "ALPACA_LIVE_API_KEY": "livekey",
        "ALPACA_LIVE_SECRET_KEY": "livesecret",
        "ESHEON_LIVE_MAX_ORDER_NOTIONAL": "200",
        "ESHEON_LIVE_MAX_DAILY_LOSS": "100",
        "ESHEON_LIVE_MAX_OPEN_POSITIONS": "1",
        "ESHEON_LIVE_ARM_FILE": str(arm),
        "ESHEON_KILL_FILE": str(tmp_path / "KILL"),
    }


# ---------- paper (default) ----------

def test_default_is_paper():
    ctx = resolve_trading_mode("zdte", NOW, {"ALPACA_PAPER": "true"})
    assert ctx.mode is TradingMode.PAPER
    assert ctx.endpoint == PAPER_ENDPOINT
    assert ctx.key_env == "ALPACA_API_KEY"
    assert ctx.limits is None


@pytest.mark.parametrize("env", [{}, {"ALPACA_PAPER": "false"}, {"ESHEON_MODE": "paper"}])
def test_paper_mode_needs_paper_flag(env):
    """The old 0DTE flaw: ALPACA_PAPER=false alone must never mean live."""
    with pytest.raises(LiveTradingRefused):
        resolve_trading_mode("zdte", NOW, env)


def test_paper_refuses_live_url():
    with pytest.raises(LiveTradingRefused):
        resolve_trading_mode("zdte", NOW, {"ALPACA_PAPER": "true", "ALPACA_BASE_URL": LIVE_ENDPOINT})


def test_unknown_mode_refused():
    with pytest.raises(LiveTradingRefused):
        resolve_trading_mode("zdte", NOW, {"ESHEON_MODE": "Live!", "ALPACA_PAPER": "false"})


# ---------- live (fully armed) ----------

def test_fully_armed_live(live_env):
    ctx = resolve_trading_mode("stock_daily", NOW, live_env)
    assert ctx.mode is TradingMode.LIVE
    assert ctx.endpoint == LIVE_ENDPOINT
    assert ctx.key_env == "ALPACA_LIVE_API_KEY"
    assert ctx.limits.max_order_notional == Decimal("200")


@pytest.mark.parametrize(
    "change",
    [
        {"ALPACA_PAPER": "true"},  # conflicting flags
        {"ALPACA_PAPER": ""},
        {"ESHEON_LIVE_BOTS": "zdte"},  # bot not allowed
        {"ESHEON_LIVE_BOTS": ""},
        {"ALPACA_LIVE_API_KEY": ""},  # live keys missing
        {"ALPACA_LIVE_SECRET_KEY": ""},
        {"ALPACA_LIVE_API_KEY": "paperkey"},  # same as paper key
        {"ALPACA_BASE_URL": PAPER_ENDPOINT},  # wrong endpoint
        {"ESHEON_LIVE_MAX_ORDER_NOTIONAL": "5000"},  # above hard ceiling
        {"ESHEON_LIVE_MAX_DAILY_LOSS": "0"},
        {"ESHEON_LIVE_MAX_OPEN_POSITIONS": "50"},
        {"ESHEON_LIVE_MAX_DAILY_LOSS": "lots"},
    ],
)
def test_any_missing_live_condition_refuses(live_env, change):
    live_env.update(change)
    with pytest.raises(LiveTradingRefused):
        resolve_trading_mode("stock_daily", NOW, live_env)


def test_missing_limit_refuses(live_env):
    del live_env["ESHEON_LIVE_MAX_OPEN_POSITIONS"]
    with pytest.raises(LiveTradingRefused):
        resolve_trading_mode("stock_daily", NOW, live_env)


def test_arm_expires_next_day(live_env):
    tomorrow = datetime(2026, 10, 14, 14, 30, tzinfo=timezone.utc)
    with pytest.raises(LiveTradingRefused, match="not armed"):
        resolve_trading_mode("stock_daily", tomorrow, live_env)


def test_arm_uses_market_date_not_utc(live_env):
    # 2026-10-14 01:00 UTC is still 2026-10-13 21:00 in New York -> still armed
    late = datetime(2026, 10, 14, 1, 0, tzinfo=timezone.utc)
    assert resolve_trading_mode("stock_daily", late, live_env).mode is TradingMode.LIVE


@pytest.mark.parametrize("content", ["", "LIVE", "live 2026-10-13", "LIVE 2026-10-12", "yes"])
def test_bad_arm_file_refuses(live_env, content, tmp_path):
    with open(live_env["ESHEON_LIVE_ARM_FILE"], "w") as f:
        f.write(content)
    with pytest.raises(LiveTradingRefused):
        resolve_trading_mode("stock_daily", NOW, live_env)


def test_missing_arm_file_refuses(live_env, tmp_path):
    live_env["ESHEON_LIVE_ARM_FILE"] = str(tmp_path / "nope")
    with pytest.raises(LiveTradingRefused):
        resolve_trading_mode("stock_daily", NOW, live_env)


def test_kill_switch_blocks_live(live_env):
    open(live_env["ESHEON_KILL_FILE"], "w").close()
    with pytest.raises(LiveTradingRefused, match="Kill switch"):
        resolve_trading_mode("stock_daily", NOW, live_env)


def test_naive_time_refused(live_env):
    with pytest.raises(LiveTradingRefused):
        resolve_trading_mode("stock_daily", datetime(2026, 10, 13, 10, 30), live_env)


def test_refusal_never_leaks_key_values(live_env):
    live_env["ALPACA_LIVE_API_KEY"] = "paperkey"
    with pytest.raises(LiveTradingRefused) as e:
        resolve_trading_mode("stock_daily", NOW, live_env)
    assert "paperkey" not in str(e.value)


# ---------- paper-only components ----------

def test_paper_only_component_refuses_live_mode(live_env):
    with pytest.raises(LiveTradingRefused):
        require_paper_mode(live_env)
    with pytest.raises(LiveTradingRefused):
        require_paper_mode({"ALPACA_PAPER": "true", "ESHEON_MODE": "live"})
    require_paper_mode({"ALPACA_PAPER": "true"})
