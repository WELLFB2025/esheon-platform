# Esheon — project rules for Claude Code

Esheon is a multi-strategy trading backend built from the EshelBot bots. **Paper by default; live only through the gate.**
Full roadmap: docs/IMPLEMENTATION_PLAN.md. Live design: docs/LIVE_TRADING.md. Current milestone: see "Status" at the bottom.

## Hard safety rules (never break these)
1. Paper is the default. Every broker client gets its mode, endpoint and key names from `esheon.safety.resolve_trading_mode()` and nowhere else. Never add another path to live (no `paper=False`, no hard-coded live URL, no "ALPACA_PAPER=false means live"). Missing or conflicting config must refuse, never fall through to live.
1a. Claude Code never turns live on: never create or edit the arm file (`~/.esheon/live_arm`), never set `ESHEON_MODE=live`, never add a bot to `ESHEON_LIVE_BOTS`, never raise the hard ceilings in `safety.py` or remove the kill switch without explicit owner approval in the session. The owner arms live trading by hand.
2. Never open, print, log or commit `.env` files, API keys (paper or live), secrets or account numbers. Check that a key is present without showing its value. Alpaca FEE descriptions contain the account number: redact it.
3. Never read, edit or run commands that touch `~/alpaca_trading_bots/**`. Never run `launchctl` or any `deploy/*.sh` script. The owner deploys; hand over the exact command instead.
4. Work only in the dev repos: `~/work/esheon`, `~/work/zdte-live`, `~/work/stock-bots`, `~/work/zdte-arch`.
5. Never edit a verbatim copy (`stockbot/macd_first_engine.py`, `stockbot/macd_first_signal_adapter.py`, `optbot/stop_replay.py`, `optbot/cog.py`, `optbot/macd_first_engine.py`). Change the live module in zdte-live first, then re-copy. Esheon imports these; it never forks them.
6. Preserve existing strategy behavior. Golden tests (`tests/fixtures/golden.json`) are regenerated only for an approved, intended change, and the commit says so.
7. New or changed strategy rules ship as shadow/log-only with an off switch. Promotion to paper trading needs owner approval; promotion to live needs the criteria in docs/LIVE_TRADING.md plus written owner sign-off.
8. If account state, order state, market data, the database or central risk is unavailable or stale: block new entries. Existing positions are still monitored.
9. Every order goes Strategy -> Bot Risk -> Central Risk + atomic reservation -> Order Manager -> Broker Adapter. Nothing bypasses central risk.
10. The zone signal logger (Bot 3, `optbot/`) never places orders. (The separate `sdbot/` paper trader is a different program; it is not covered by this guarantee.) Its AST no-order test and ReadOnlyTrading wrapper must stay.
11. Label every price `QUOTE_ACTUAL`, `BAR_PROXY`, `PAPER_FILL` or `LIVE_FILL`. Never call replayed prices fills, and never mix paper and live P&L. P&L is gross; report fees separately.
12. Never fabricate data, test results, performance or readiness. Never say a test passed unless you ran it; report the command and exact result.
13. Ask first before: destructive operations, architecture changes, strategy or risk changes, account-topology changes, data migrations, new dependencies.

## Known facts to respect (verify before relying on them)
- TARGET (owner decision, docs/DECISIONS.md): all bots share ONE account. TODAY: bots still have separate accounts (audit found 0DTE and ICT may already share one). Don't change any bot's account or keys until the Milestone 6 migration plan is approved; the owner migrates.
- Under $25,000 equity, the whole shared account gets 3 day trades per 5 business days (PDT). Central risk counts and allocates them across bots.
- Fractional stock orders are DAY-only, so Bot 1 positions are unprotected overnight.
- Bars are 2-min IEX; Alpaca option bars are only served once 15+ minutes old.
- Research periods: P1 dev 2024-09-16..2025-09-15, P0 held-out 2024-02-05..09-13 (already used once), P3 2025-09-15..2026-03-31, P2 2026-04-01..09-30.

## Commands
- Tests (0DTE or stock-bots, from repo root):
  `ALPACA_API_KEY=T ALPACA_SECRET_KEY=T ~/work/zdte-arch/.venv/bin/python -m pytest -q -p no:cacheprovider tests`
  Dummy keys only satisfy imports. Audit: 2 zdte-live tests DO call Alpaca's data API (401 with dummy keys) and 6 expect the deployed layout; Milestone 2 marks them so the dev suite runs offline.
- Live-code fingerprint (proves production untouched):
  `~/work/zdte-arch/research/shadow_audit/prod_fingerprint.py OUT.json [COMPARE.json]`

## How to work (low credit)
- Start with `pwd`, `git status --short --branch`, a shallow listing. Use `rg` and targeted reads; never dump large files, logs or trees.
- Don't re-read files you already read this session.
- One milestone per session. At the end: run relevant tests, show `git diff --stat`, update docs, commit, push, write a short report, stop.
- Pre-approved (no prompt): Esheon and bot-repo test commands, `rg`, `git add/commit/fetch`, `git push origin <branch>`. Run git from inside the repo (`cd ~/work/<repo> && git …`), not `git -C`, so the rules match. Never force-push.
- Report each bot/strategy as: existing, reused, partial, shadow-only, or not started.
- Keep docs short; update instead of duplicating. Create a doc only when its milestone needs it.

## Repo layout
- `src/esheon/safety.py` — trading-mode gate (`resolve_trading_mode`), paper-only check for log-only components (`require_paper_mode`), kill switch, redaction.
- `src/esheon/models.py`, `interfaces.py`, `ids.py` — broker-neutral core (draft until the audit confirms it).
- `docs/MILESTONE_PROMPTS.md` — the prompt for each milestone. `docs/reference/` — source docs, read only the section you need.
- Esheon tests: `.venv/bin/pytest -q` (no network, no keys).

## Status
- Milestone 0 (repo foundation): done
- Milestone 1 (audit): done — docs/ARCHITECTURE_AUDIT.md
- Current milestone: 2 (stabilize + close 0DTE's accidental live path) — prompt in docs/MILESTONE_PROMPTS.md
- Decisions made: docs/DECISIONS.md. Open owner decisions: docs/IMPLEMENTATION_PLAN.md
