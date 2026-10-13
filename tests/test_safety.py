import pytest

from esheon.safety import LiveTradingRefused, key_present, redact, require_paper_mode


@pytest.mark.parametrize("env", [{}, {"ALPACA_PAPER": "false"}, {"ALPACA_PAPER": "1"}, {"ALPACA_PAPER": ""}])
def test_refuses_without_explicit_paper_flag(env):
    with pytest.raises(LiveTradingRefused):
        require_paper_mode(env)


@pytest.mark.parametrize("var", ["ALPACA_BASE_URL", "APCA_API_BASE_URL"])
def test_refuses_live_endpoint_even_with_paper_flag(var):
    with pytest.raises(LiveTradingRefused):
        require_paper_mode({"ALPACA_PAPER": "true", var: "https://api.alpaca.markets"})


def test_accepts_paper():
    require_paper_mode({"ALPACA_PAPER": "TRUE"})
    require_paper_mode({"ALPACA_PAPER": "true", "ALPACA_BASE_URL": "https://paper-api.alpaca.markets/"})


def test_key_present_never_returns_value():
    env = {"ALPACA_SECRET_KEY": "s3cret"}
    assert key_present("ALPACA_SECRET_KEY", env) is True
    assert key_present("MISSING", env) is False


def test_redact_masks_secrets_keys_and_accounts():
    text = (
        "ALPACA_SECRET_KEY=abc123xyz token: 'tok_999' key id PKABCDEFGHIJKLMNOP12 "
        "FEE activity for account PA3ABCDEF12 ref 123456789012"
    )
    out = redact(text)
    for leaked in ("abc123xyz", "tok_999", "PKABCDEFGHIJKLMNOP12", "PA3ABCDEF12", "123456789012"):
        assert leaked not in out
    assert "[REDACTED_9012]" in out  # last four kept for reconciliation


def test_redact_leaves_ordinary_text():
    s = "PAPER_FILL at 12.50 for SPY on 2026-10-12"
    assert redact(s) == s
