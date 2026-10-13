# Esheon

Paper-trading-only, multi-strategy trading backend, built in gated milestones from the existing EshelBot bots.

> **Paper only.** Esheon refuses to run unless `ALPACA_PAPER=true`. There is no live-trading path, and none may be added.

## Status

Milestone 0 (repo foundation) is done. Milestone 1 (audit of the existing EshelBot repos) is next.
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
| `.claude/settings.json` | Permission deny rules (no `.env`, no live bot folders, no `launchctl`, no deploy scripts) |
| `src/esheon/safety.py` | Paper-mode guard and secret redaction |
| `src/esheon/models.py` | Broker-neutral orders, fills, positions, price labels |
| `src/esheon/interfaces.py` | Draft Strategy / BotRisk / Broker protocols (revised after the audit) |
| `src/esheon/ids.py` | Unique, attributable client order IDs |
| `docs/MILESTONE_PROMPTS.md` | One paste-ready Claude Code prompt per milestone |
| `docs/reference/` | The master prompt and the EshelBot developer guide |

## Setup

```bash
git clone https://github.com/drick2025/esheon.git ~/work/esheon
cd ~/work/esheon
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
```

Then start Claude Code in `~/work/esheon` and paste the Milestone 1 prompt from `docs/MILESTONE_PROMPTS.md`.

Also copy the deny rules from `.claude/settings.json` into `~/.claude/settings.json`, so they apply
when Claude Code works in `zdte-live`, `stock-bots` and `zdte-arch` too.
