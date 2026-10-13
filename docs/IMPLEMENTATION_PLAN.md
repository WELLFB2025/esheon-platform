# Implementation plan

Status: **Milestone 1 (audit) done, awaiting owner review** — see [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md).
Milestones 2–7 re-sized from the audit (2026-10-13). Weeks assume the same pace as before; adjust once owner hours are known.

Source documents: [reference/MASTER_PROMPT.md](reference/MASTER_PROMPT.md) (target),
[reference/ESHELBOT_DEVELOPER_GUIDE.md](reference/ESHELBOT_DEVELOPER_GUIDE.md) (current system, Oct 11, 2026 — leads to verify, not facts).

## Milestones

| # | Milestone | Target | Gate |
|---|-----------|--------|------|
| 0 | Repo foundation: CLAUDE.md, safety settings, paper-mode guard, broker-neutral models, CI | Done | Tests pass in CI |
| 1 | Audit and baseline of zdte-live, stock-bots, zdte-arch | Done (2026-10-13) | ARCHITECTURE_AUDIT.md + owner review |
| 2 | Stabilize: pin tests for `optbot/cog.py` + `optbot/macd_first_engine.py`; mark 2 network tests and 6 deployed-layout tests so the dev suite is green offline; resolve the stale lock-floor test with the owner; record baseline fingerprint | Weeks 2–3 (smaller) | 0DTE + stock-bots green offline; no strategy change |
| 3 | Interfaces (revise models per audit §8) + central risk with atomic reservations, **per-account PDT budget**, fail-closed; order manager; Esheon broker wrapper that refuses non-paper for 0DTE too | Weeks 4–7 (larger) | No order bypasses central risk; shared-account PDT test |
| 4 | Strategies: wrap MACD+EMA (0DTE + Bots 1/2 adapters); promote nothing; spec Trend/VWAP from shadow `C_vwap_cog`; then spec the others one at a time | Weeks 8–11 | Each spec pre-registered and approved |
| 5 | Alpaca paper adapter + PostgreSQL records + reconciliation recognising all `ESHEL-*` and `ESHEON-` prefixes | Weeks 11–14 | No duplicate on ambiguous submit |
| 6 | Portfolio backtest + shared-account test on a dedicated paper account (0DTE+ICT already share one — model it first) | Weeks 14–18 | Owner approves any topology change |
| 7 | Operational hardening (fail-closed governor, staleness blocks) + readiness report | Weeks 18–21 | Critical failures block entries |
| — | API and mobile app | After 7 | Separate planning session |

Timeline is an estimate. Safety gates are never skipped to meet a date.

## Known gaps between target and current system

1. **PDT limit.** $500 paper accounts get 3 day trades per 5 business days. Only stock Bots 1/2 check it (`pdt_guard`); 0DTE and the Bot 3 trader do not. Central risk must budget PDT per account.
2. **Account topology.** Stock Bots 1/2 and the Bot 3 trader each have their own account (deploy scripts refuse a shared key). **zero_dte_bot and ict_liquidity_bot already share one account** (code comments), with a fail-open shared loss governor.
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
| 1. MACD + EMA | 0DTE bot, Bot 1 daily, Bot 2 scalp | existing (0DTE), reused (Bots 1/2) — verified |
| 2. ICT / Price Action | `ict_liquidity_bot` (out of scope, owner unknown) | not started |
| 3. Trend / VWAP | 0DTE "strategy C (VWAP+COG)" shadow | shadow-only fragment |
| 4. Momentum / Breakout | none | not started |
| 5. Mean Reversion | none | not started |
| Zone logger (Bot 3) | `optbot/` | log-only; never a trader (verified) |
| Zone rule v2 trader (Bot 3) | `sdbot/` `sd_cog_options_bot`, `ESHEL-SDCO-` | partial: paper-traded, backtest failed; not one of the five |

## Owner decisions

- [x] Repo: Esheon is its own repo (this one).
- [ ] Do the three MACD+EMA bots count as one strategy or three of the five?
- [ ] Accounts/PDT: keep separate accounts, or fund one shared paper account above the PDT threshold?
- [ ] Is `ict_liquidity_bot` still running, who owns it, may Claude Code read it?
- [ ] Self-learner: fix its defects or switch it off?
- [ ] Run the pending Bot 1/2/3 and variant-D deploys before the audit?
- [ ] Database: local PostgreSQL, Docker, or hosted?
- [ ] Hours per week available.
- [ ] 0DTE allows `ALPACA_PAPER=false` (live endpoint). Approve making it refuse, like the stock bots? (change in zdte-live, needs deploy)
- [ ] Bot 3 trader `sd_cog_options_bot`: keep paper-trading a failed rule? CLAUDE.md rule 10 should name logger vs trader.
- [ ] Lock-floor test expects per-position $15 (1.315), code gives per-contract (1.39). Which is intended?
- [ ] Which repo does `deploy_fixes_345.sh` deploy from: zdte-live or zdte-arch?
