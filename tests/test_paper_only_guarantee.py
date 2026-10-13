"""Static guard: only esheon/safety.py may know the live endpoint or construct a non-paper client.

Every broker client must take its endpoint and keys from safety.resolve_trading_mode().
"""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
GATE = SRC / "esheon" / "safety.py"

FORBIDDEN = [
    re.compile(r"paper\s*=\s*False"),
    re.compile(r"ALPACA_PAPER\s*=\s*['\"]?false", re.I),
    re.compile(r"https?://api\.alpaca\.markets"),
    re.compile(r"ESHEON_MODE\s*=\s*['\"]?live", re.I),
]


def test_live_paths_only_in_the_gate():
    offenders = []
    for path in SRC.rglob("*.py"):
        if path == GATE:
            continue
        text = path.read_text()
        for pat in FORBIDDEN:
            if pat.search(text):
                offenders.append(f"{path.relative_to(SRC)}: {pat.pattern}")
    assert not offenders, offenders


def test_gate_exists_and_defaults_to_paper():
    text = GATE.read_text()
    assert 'or "paper"' in text  # missing ESHEON_MODE means paper
