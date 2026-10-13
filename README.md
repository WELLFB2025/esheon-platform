# Esheon

Multi-strategy trading backend, built in gated milestones from the existing EshelBot bots. Paper by default; live only through one gate.

> **Paper by default.** Live trading needs every condition in [docs/LIVE_TRADING.md](docs/LIVE_TRADING.md): explicit live mode, separate live keys, an allow-listed bot, hard limits, a daily owner arm, and no kill switch. Anything less refuses.

## Status

Milestones 0 (foundation) and 1 (audit) are done. Milestone 2 (stabilize, close 0DTE's accidental live path) is next.
See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Target architecture

```
Strategy -> Bot Risk -> Central Risk + atomic reservation -> Order Manager -> Broker Adapter (Alpaca paper)
```

Five strategy bots, each with its own risk config; one central account risk manager; one order manager;
one broker-neutral interface; durable PostgreSQL records; later, an API and a mobile app.

## What's here now

| Path | Contents |
|---|---|
| `CLAUDE.md` | Standing rules Claude Code loads every session |
| `.claude/settings.json` | Permission deny rules (no `.env`, no live bot folders, no arming live, no `launchctl`, no deploy scripts) |
| `src/esheon/safety.py` | Trading-mode gate (paper default, gated live), kill switch, secret redaction |
| `src/esheon/models.py` | Broker-neutral orders, fills, positions, price labels |
| `src/esheon/interfaces.py` | Draft Strategy / BotRisk / Broker protocols (revised after the audit) |
| `src/esheon/ids.py` | Unique, attributable client order IDs |
| `docs/MILESTONE_PROMPTS.md` | One paste-ready Claude Code prompt per milestone |
| `docs/reference/` | The master prompt and the EshelBot developer guide |

## Setup

```bash
git clone https://github.com/WellFb2025/esheon-platform.git ~/work/esheon
cd ~/work/esheon
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
```

Then start Claude Code in `~/work/esheon`, switch to auto mode, and paste the next milestone's prompt from `docs/MILESTONE_PROMPTS.md`.

Also copy the deny rules from `.claude/settings.json` into `~/.claude/settings.json`, so they apply
when Claude Code works in `zdte-live`, `stock-bots` and `zdte-arch` too.
