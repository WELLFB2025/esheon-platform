# Changelog

## 0.1.0 — 2026-10-13 — Paper by default, gated live

- Owner decision: Esheon supports paper and live trading. Paper stays the default.
- `esheon.safety.resolve_trading_mode()`: live only when ESHEON_MODE=live AND ALPACA_PAPER=false AND separate live keys AND bot allow-listed AND limits within hard ceilings AND armed for today's New York date AND kill switch off. Missing or conflicting config refuses.
- `require_paper_mode()` kept for log-only components; it now also refuses when ESHEON_MODE=live.
- `PriceLabel.LIVE_FILL`; fills may be PAPER_FILL or LIVE_FILL.
- CLAUDE.md: rules rewritten for gated live; Claude Code may never arm live, set live mode, add live bots or touch live keys.
- `.claude/settings.json`: deny rules for the arm file, kill file, live mode and live keys; asks before editing safety.py.
- docs/LIVE_TRADING.md (gate, owner commands, promotion criteria); Milestone 2 prompt closes the 0DTE accidental-live path; new Milestone 8 prompt.
- 33 new tests (56 total).

## 0.0.1 — 2026-10-12 — Milestone 0: repo foundation

- CLAUDE.md standing rules and `.claude/settings.json` deny rules for Claude Code.
- `esheon.safety`: `require_paper_mode()` refuses unless `ALPACA_PAPER=true` and the paper endpoint; `redact()` masks secrets, key IDs and account numbers.
- `esheon.models`: broker-neutral orders, fills (PAPER_FILL only), quotes with staleness, positions, account snapshots, risk decisions.
- `esheon.interfaces`: draft Strategy / BotRisk / Broker protocols.
- `esheon.ids`: unique `ESHEON-<BOT>-<UTC>-<nonce>` client order IDs.
- Tests, including a static check that no source contains a live-trading path. CI on push.
- Docs: implementation plan, milestone prompts, reference copies of the master prompt and developer guide.
- No existing bot, account or deployment touched. No strategy code yet.
