# Implementation plan

Status: **Milestone 0 done (repo foundation). Milestone 1 (audit) not started.**
Re-plan Milestones 2–7 after the Milestone 1 audit, using real repo condition and the owner's hours.

Source documents: [reference/MASTER_PROMPT.md](reference/MASTER_PROMPT.md) (target),
[reference/ESHELBOT_DEVELOPER_GUIDE.md](reference/ESHELBOT_DEVELOPER_GUIDE.md) (current system, Oct 11, 2026 — leads to verify, not facts).

## Milestones

| # | Milestone | Target | Gate |
|---|-----------|--------|------|
| 0 | Repo foundation: CLAUDE.md, safety settings, paper-mode guard, broker-neutral models, CI | Done | Tests pass in CI |
| 1 | Audit and baseline of zdte-live, stock-bots, zdte-arch | Week 1 | ARCHITECTURE_AUDIT.md + owner review |
| 2 | Stabilize existing code; add missing pin test for `optbot/cog.py`, `optbot/macd_first_engine.py` | Weeks 2–3 | Suites pass; no silent strategy change |
| 3 | Interfaces, central risk with atomic reservations (incl. PDT budget), order manager | Weeks 4–6 | No order bypasses central risk |
| 4 | Strategies: wrap MACD+EMA; spec then shadow-build the others one at a time | Weeks 7–10 | Each spec pre-registered and approved |
| 5 | Alpaca paper adapter + PostgreSQL records + reconciliation | Weeks 10–13 | No duplicate on ambiguous submit |
| 6 | Portfolio backtest + shared-account test on a dedicated paper account | Weeks 13–17 | Owner approves any topology change |
| 7 | Operational hardening + readiness report | Weeks 17–20 | Critical failures block entries |
| — | API and mobile app | After 7 | Separate planning session |

Timeline is an estimate. Safety gates are never skipped to meet a date.

## Known gaps between target and current system

1. **PDT limit.** $500 paper accounts get 3 day trades per 5 business days. Five intraday bots on one small account would starve each other. Central risk must budget PDT per account.
2. **Account topology.** Today: one account, order prefix, folder, venv, state per bot; deploy scripts refuse a shared API key. A shared account is a migration project.
3. **Five strategies vs one.** Only MACD-first + EMA 9/21 exists (in three bots). Trend/VWAP has a shadow fragment; the rest are not started.
4. **Two risk stacks.** 0DTE `RiskEngine` + `OrderManager` vs stock-bots `risk.can_enter` → `_size_and_gate` → `portfolio.check`. Wrap both; don't rewrite.
5. **Persistence.** CSV ledgers + JSON state today; Postgres is new and lives here first.
6. **Verbatim copies** must be imported, never forked or edited.
7. **Overnight gap risk** (fractional DAY-only stops) must count in open risk.
8. **Data quality.** IEX bars; option bars served 15+ minutes late.

Research to date shows no strategy with an edge after realistic costs. Esheon is infrastructure, not a profit claim.

## Strategy status

| Target strategy | Existing code | Status |
|---|---|---|
| 1. MACD + EMA | 0DTE bot, Bot 1 daily, Bot 2 scalp | existing (to verify) |
| 2. ICT / Price Action | `ict_liquidity_bot` (out of scope, owner unknown) | not started |
| 3. Trend / VWAP | 0DTE "strategy C (VWAP+COG)" shadow | shadow-only fragment |
| 4. Momentum / Breakout | none | not started |
| 5. Mean Reversion | none | not started |
| Zone logger (Bot 3) | `optbot/` | log-only; never a trader |

## Owner decisions

- [x] Repo: Esheon is its own repo (this one).
- [ ] Do the three MACD+EMA bots count as one strategy or three of the five?
- [ ] Accounts/PDT: keep separate accounts, or fund one shared paper account above the PDT threshold?
- [ ] Is `ict_liquidity_bot` still running, who owns it, may Claude Code read it?
- [ ] Self-learner: fix its defects or switch it off?
- [ ] Run the pending Bot 1/2/3 and variant-D deploys before the audit?
- [ ] Database: local PostgreSQL, Docker, or hosted?
- [ ] Hours per week available.
