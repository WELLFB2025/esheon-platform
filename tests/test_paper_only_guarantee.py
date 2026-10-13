"""Static guard: no source file may contain a live-trading path."""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"

FORBIDDEN = [
    re.compile(r"paper\s*=\s*False"),
    re.compile(r"ALPACA_PAPER\s*=\s*['\"]?false", re.I),
    re.compile(r"https?://api\.alpaca\.markets"),
]


def test_no_live_trading_code_in_src():
    offenders = []
    for path in SRC.rglob("*.py"):
        text = path.read_text()
        for pat in FORBIDDEN:
            if pat.search(text):
                offenders.append(f"{path.relative_to(SRC)}: {pat.pattern}")
    assert not offenders, offenders
