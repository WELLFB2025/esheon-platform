# Changelog

## 0.0.1 — 2026-10-12 — Milestone 0: repo foundation

- CLAUDE.md standing rules and `.claude/settings.json` deny rules for Claude Code.
- `esheon.safety`: `require_paper_mode()` refuses unless `ALPACA_PAPER=true` and the paper endpoint; `redact()` masks secrets, key IDs and account numbers.
- `esheon.models`: broker-neutral orders, fills (PAPER_FILL only), quotes with staleness, positions, account snapshots, risk decisions.
- `esheon.interfaces`: draft Strategy / BotRisk / Broker protocols.
- `esheon.ids`: unique `ESHEON-<BOT>-<UTC>-<nonce>` client order IDs.
- Tests, including a static check that no source contains a live-trading path. CI on push.
- Docs: implementation plan, milestone prompts, reference copies of the master prompt and developer guide.
- No existing bot, account or deployment touched. No strategy code yet.
