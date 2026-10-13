# Milestone prompts

Paste one per fresh Claude Code session (run `/clear` between milestones). CLAUDE.md carries the standing rules.
Update the Status line in CLAUDE.md and docs/IMPLEMENTATION_PLAN.md when a milestone closes.

## Milestone 1 — audit and baseline (start in plan mode)

```text
Milestone 1 only: audit and baseline. Do not write feature code.

Repos to inspect (read-only except ~/work/esheon):
- ~/work/zdte-live (branch fixes-345), ~/work/stock-bots, ~/work/zdte-arch
Follow CLAUDE.md. No .env, no ~/alpaca_trading_bots, no launchctl, no deploy scripts.

Do, in order, using rg and targeted reads only:
1. pwd and git status --short --branch in each repo. Record branch, HEAD commit, dirty files.
2. Confirm entry points and risk/order code paths:
   - 0DTE: runtime.py, bot.py header, config.py, RiskEngine.can_open_position, OrderManager
   - stock-bots: run.py, stockbot/runner.py, risk.py, portfolio.py, broker.py, state.py
   - optbot: logger.py, data.ReadOnlyTrading
3. Run both test suites with the command in CLAUDE.md. Report exact pass/fail/skip counts
   (the guide claims 448 and 110; treat as unverified).
4. Check whether optbot/cog.py and optbot/macd_first_engine.py have a pin test (guide says no).
5. Map existing code to the 5 target strategies. Label each: existing / reused / partial /
   shadow-only / not started. Do NOT open ict_liquidity_bot.
6. Document account topology from code and docs only (prefixes, PAPER checks,
   one-account-per-bot rule, deploy-script key checks). Note the PDT impact on a shared account.
7. List persistence used today (CSV/JSON files) vs what Esheon needs (Postgres).
8. Compare src/esheon/models.py and interfaces.py with the real code; list needed changes.

Write in ~/work/esheon/docs:
- ARCHITECTURE_AUDIT.md: verified vs only-described, test results with commands, risks.
- Update IMPLEMENTATION_PLAN.md: re-size milestones 2-7 from what you found.

Then stop. Report in <= 25 lines: verified findings, commands + results, top risks,
owner decisions needed, and the smallest next step. Do not start Milestone 2.
```

## Milestone 2 — stabilize + close the accidental live path

```text
Milestone 2: stabilize existing code. Read docs/IMPLEMENTATION_PLAN.md,
docs/ARCHITECTURE_AUDIT.md and docs/LIVE_TRADING.md first.
1. zdte-live: replace "ALPACA_PAPER=false means live" with the Esheon gate rules:
   paper unless ESHEON_MODE=live AND ALPACA_PAPER=false AND every other gate
   condition holds; conflicting or missing config refuses to start. Leave live OFF.
   Add tests proving ALPACA_PAPER=false alone refuses. Do not change strategy logic.
2. Make the shared daily-loss limit fail CLOSED (block new entries) on errors. Test it.
3. Add the missing pin tests for optbot/cog.py and optbot/macd_first_engine.py
   against ~/work/zdte-live.
4. Mark the network-calling and deployed-layout tests so the dev suites pass offline.
5. Fix only other defects I approved: <list>. Keep golden tests unchanged.
6. Correct CLAUDE.md lines the audit disproved.
Run all suites. Hand me the exact deploy command for zdte-live; do not deploy.
Stop and report: diff --stat, test counts, anything triaged.
```

## Milestone 3 — interfaces, central risk, order manager

```text
Milestone 3, in ~/work/esheon only. Revise src/esheon/interfaces.py from the audit.
Write adapters that WRAP the existing 0DTE RiskEngine and stock-bots
risk.can_enter/portfolio.check without changing them. Build CentralRisk with atomic
reservations (buying power, open risk, cash reserve, PDT budget per account, daily
loss, drawdown) and an OrderManager (client order IDs, persist intent before submit,
query-by-ID on timeout, never retry entries).
Tests: concurrent signals, insufficient buying power, stale account, duplicate order,
submit timeout, central-risk failure, PDT exhausted. Use a fake broker. Stop and report.
```

## Milestone 4 — strategies

```text
Milestone 4. Wrap the MACD-first + EMA engine as Strategy 1 by importing it (never
copy or edit). For Strategy <N> only: write a pre-registered spec in
docs/BOT_SPECIFICATIONS.md (rules, params, periods P1/P3/P2, cost model, pass
criteria) and stop for my approval before coding it. Approved strategies run
shadow-only with deterministic tests on fixture bars. Stop and report.
```

## Milestone 5 — Alpaca paper adapter + database

```text
Milestone 5. Build the Alpaca paper adapter around the existing broker.py logic
(paper=True enforced via esheon.safety, refuse otherwise). Add Postgres tables for
signals, risk decisions, reservations, order intents, orders, fills, allocations,
audit events. Implement restart/reconnect reconciliation. Tests: ambiguous submit makes
no duplicate, restart with open positions, partial fills. Stop and report.
```

## Milestone 6 — portfolio backtest + shared-account test

```text
Milestone 6. Combined backtest of all approved strategies with MODERATE and ADVERSE
costs; report gross and net separately, labelled QUOTE_ACTUAL/BAR_PROXY/PAPER_FILL.
Write docs/MIGRATION_AND_ROLLBACK.md for a shared account. Test same-symbol,
opposite-direction, manual broker positions, PDT exhaustion and restarts against a
DEDICATED test paper account only. Do not change any existing bot's account. Stop and report.
```

## Milestone 7 — hardening

```text
Milestone 7. Add health checks, structured logs, alerts (reuse notify.py), a global
stop-new-entries switch, backups and docs/OPERATIONS.md. Run failure tests: broker
down, DB down, stale data, central-risk down. Produce a readiness report listing what
is verified and every known limitation. No live trading. Stop and report.
```

## Milestone 8 — live trading (only after Milestones 3–7 are done)

```text
Milestone 8. Read docs/LIVE_TRADING.md. Wire the Alpaca adapter to take endpoint and
key NAMES only from esheon.safety.resolve_trading_mode(); never read key values into
logs. Enforce TradingContext.limits in central risk (order notional, daily loss, open
positions) and count PDT day trades per live account. Record live fills as LIVE_FILL
in separate tables/files from paper; reconcile live state on every start.
Tests with a fake broker: every gate condition missing refuses; kill switch blocks new
orders mid-session; arm expiry at midnight ET stops new entries; limits are hard stops.
Do NOT create the arm file, set ESHEON_MODE=live, add bots to ESHEON_LIVE_BOTS or touch
live keys. Write the owner's go-live checklist for ONE bot at minimum size. Stop and report.
```
