# Architecture audit (Milestone 1)

Date: 2026-10-13. Read-only audit of the dev repos. No `.env`, no deployed folder, no launchctl, no deploy scripts run.
`ict_liquidity_bot` was not opened; facts about it below come only from 0DTE code comments and tests.

**Verified** = seen in code or produced by a command in this session. **Described** = stated in docs or comments, not executed.

## 1. Repo state

| Repo | Branch | HEAD | Dirty |
|---|---|---|---|
| esheon | main (= origin/main) | `ec00544` 2026-10-13 | clean |
| zdte-live | fixes-345 | `f5ef4b22` 2026-10-12 shadow $10 stop | clean |
| stock-bots | main | `44ead66` 2026-10-11 Bot 3 trading (`sd_cog_options_bot`) | clean |
| zdte-arch | main | `108092ae` 2026-10-12 pullback-entry research | untracked only: `research/cache/`, `research/out/*`, two research `out/cache` dirs |

Note: `zdte-live/deploy/deploy_fixes_345.sh` tells the owner to put **zdte-arch** on `fixes-345`; zdte-arch is on `main`. Which repo the deploy really reads from needs owner confirmation.

## 2. Tests (verified)

| Suite | Command (from repo root) | Result |
|---|---|---|
| 0DTE (zdte-live) | `ALPACA_API_KEY=T ALPACA_SECRET_KEY=T PYTHONDONTWRITEBYTECODE=1 ~/work/zdte-arch/.venv/bin/python -m pytest -q -p no:cacheprovider tests` | **9 failed, 442 passed**, 11 subtests passed, 8.9 s |
| stock-bots | same command | **139 passed**, 0 failed, 0 skipped, 75.9 s |
| esheon | `.venv/bin/pytest -q -p no:cacheprovider` | **23 passed** |

The guide's "448 and 110" are wrong for today's HEADs (451 and 139).

0DTE failures, by cause:
- **Deployed-layout tests (6)** — `test_module_parity` x5 and `test_account_risk::SharedLocation`: they expect the deployed folder layout (`<parent>/zero_dte_bot`, `<parent>/ict_liquidity_bot`, parent dir named for the deployed folder). In the dev repo the parent is `~/work`. They only pass where deployed. Not a code defect; they cannot run in dev.
- **Network tests (2)** — `test_audit_log::test_msft_sep16_audit_matches_spec_example`, `test_signal_engine::TestRealDataIntegration`: call `data.alpaca.markets` and get 401 with dummy keys. **CLAUDE.md's "no test calls Alpaca" is false for these two.**
- **Stale assertion (1)** — `test_entry_and_stop_ownership::test_protect_lock_floor_is_entry_plus_15_dollars`: expects 1.315 for entry 1.24 x2, code returns 1.39. `protect_floor_price` is unchanged since the 2026-09-30 baseline and its docstring says per-contract "whatever the position size", so the test, not the code, is out of date. Needs owner confirmation before touching either.

## 3. Entry points and order paths (verified)

**0DTE (`zdte-live`)** — `runtime.run()` supervisor + `TradeManager` (5 s: broker sync, stops/lock/trail, 15:45 flatten, heartbeat) + `OpportunityScanner` (~60 s). Path: signal → `RiskEngine.can_open_position` (health/broker-sync staleness, account block, market open, EOD, daily loss, consecutive losses, cooldown, duplicate signal, position/symbol/strategy/contract/premium caps) → `size_entry` → `portfolio.reserve_entry(client_order_id)` → `OrderManager.submit_order` (per-thread client, never resubmits a client_order_id, failed submit = UNKNOWN) → Alpaca. Order IDs `ESHEL-ZDTE-<32 hex>`.
- `bot.py:137` `PAPER = ALPACA_PAPER env, default true`. **Setting `ALPACA_PAPER=false` selects the live endpoint; no refusal.** (Stock bots and Bot 3 refuse.)
- **No PDT logic anywhere in 0DTE** (`rg daytrade|pdt` → nothing outside tests).
- `account_risk.py`: shared daily-loss governor for zero_dte_bot + ict_liquidity_bot, which (per its docstring and `broker_reconciliation.py`) **trade the same Alpaca account** with namespaces `ESHEL-ZDTE-` / `ESHEL-ICT-`. It **fails open** to each bot's own -$200 limit.

**Stock bots (`stock-bots`)** — `run.py` (refuses if `ALPACA_PAPER != true`, single-instance lock) → `stockbot/runner.Bot.step` → `_reconcile` / `_manage` / `_scan_and_enter` → `risk.can_enter` (window, positions, held/pending, account block, locks, daily loss, consecutive, cooldown, duplicate signal, **`portfolio.pdt_room`**, cash reserve) → `_size_and_gate` → `portfolio.check` (exposure, open risk, sector, correlation; unknown correlation blocks) → `AlpacaBroker` (`paper=True` hard-coded). Prefixes `ESHEL-SDAY-` (Bot 1 daily), `ESHEL-SSCP-` (Bot 2 scalp). State `bot_state.json`.

**Bot 3 — two programs now, not one.**
- `run_sdlog.py` + `optbot/logger.py`: zone signal logger. `optbot/data.ReadOnlyTrading` allows only `get_clock`/`get_calendar`; AST no-order test in `tests/test_sdlogger.py`. Verified, intact.
- **New since the guide:** `run_sdtrade.py` + `sdbot/trader.py` + `sdbot/broker.py` = `sd_cog_options_bot`, a **paper trader** of zone rule v2 on 0DTE SPY/TSLA options, prefix `ESHEL-SDCO-`, own account required by `deploy_sd_trader.sh`. Its docstring says the rule's backtest **failed** and it trades at the owner's request. **No PDT check** in `sdbot/`. CLAUDE.md rule 10 covers the logger only; it must be clarified.

## 4. Verbatim copies and pin tests (verified)

All five copies are byte-identical to `zdte-live` today (`cmp`).

| Copy | Pin test |
|---|---|
| `stockbot/macd_first_engine.py`, `stockbot/macd_first_signal_adapter.py` | yes: fixed hash (`test_stockbots.py`) + live compare (`test_risk.py`) |
| `optbot/stop_replay.py` | yes: live compare (`test_sdlogger.py`) |
| `optbot/cog.py` | **none** (guide correct) |
| `optbot/macd_first_engine.py` | **none** (guide correct) |

## 5. Strategy map

| Target | Code | Status |
|---|---|---|
| 1. MACD + EMA 9/21 | 0DTE `MACD_FIRST_0DTE`; Bot 1 daily, Bot 2 scalp via verbatim engine | **existing** (0DTE); **reused** (Bots 1/2) |
| 2. ICT / Price Action | `ict_liquidity_bot` (not opened) | not started (in Esheon) |
| 3. Trend / VWAP | 0DTE shadow rule `C_vwap_cog` (`config.SHADOW_RULES`) | **shadow-only** |
| 4. Momentum / Breakout | none found | not started |
| 5. Mean Reversion | none found | not started |
| Zone rule v2 (COG + supply/demand) | `sdbot` trader + `optbot` logger | **partial** (paper-traded, failed backtest; not one of the five) |

0DTE also carries shadow exits (stops 20/10, delay 8, EMA21 trendline, range trails, no-lock variant D) — log-only.

## 6. Account topology (from code/docs only)

| Bot | Prefix | Paper check | Account |
|---|---|---|---|
| zero_dte_bot | `ESHEL-ZDTE-` | env, default true, **not enforced** | **shared with ict_liquidity_bot** |
| ict_liquidity_bot | `ESHEL-ICT-` | unknown (not opened) | shared with 0DTE |
| Bot 1 stock_daily_bot | `ESHEL-SDAY-` | `run.py` refuses + `paper=True` | own; `deploy_stock_bot.sh` refuses a key shared with any other bot |
| Bot 2 stock_scalp_bot | `ESHEL-SSCP-` | same | own |
| Bot 3 trader sd_cog_options_bot | `ESHEL-SDCO-` | `run_sdtrade.py` refuses + `paper=True` | own; deploy refuses shared key |
| Bot 3 logger | none (no orders) | ReadOnlyTrading | may share a key (deploy prints a note) |

CLAUDE.md "each trading bot has its own account" is **false for 0DTE + ICT**. PDT on a shared <$25k account: every same-day round trip by any bot spends the account's 3 per 5 days; 0DTE options are always day trades unless they expire, so 0DTE alone can exhaust the budget and Bots 1/2's `pdt_guard` would then block entries — or, on 0DTE/Bot 3 (no guard), the broker rejects or flags. Central risk must own the per-account PDT budget.

## 7. Persistence

Today (verified by grep): JSON state (`portfolio_state.json`, `bot_state.json`, `sd_state.json`, `logger_state.json`, `account_risk.json` with flock, `risk_status.json`, `universe.json`), CSV ledgers (`trade_ledger.csv`, `signals.csv`, `signals_log.csv`, `outcomes.csv`, `cog_events.csv`, many `shadow_*.csv`), and SQLite in 0DTE research helpers (`signal_history.py`, `trade_history.py`). No Postgres anywhere.
Esheon needs (Postgres): order intents before submit, broker orders/fills keyed by client_order_id, positions with bot attribution, risk decisions with inputs, reservations, PDT ledger per account, signals incl. shadow, reconciliation runs, price labels.

## 8. Esheon models vs real code — needed changes

- Money: bots use `float`; adapters must convert to `Decimal` at the boundary.
- `Signal`: real signals carry `key` (dedupe across restarts), direction (`bullish/bearish` or `LONG`), lead/age metadata. Add `key`, `direction`, `metadata`.
- Options: add an instrument model (underlying, OCC symbol, expiry, strike, right); qty in contracts; `OrderIntent` needs asset class and **notional** (Bot 1 fractional buys).
- `AccountSnapshot`: add `trading_blocked`, `account_blocked`, `pattern_day_trader`, `account_id` (redacted).
- `Position`: add `entry_time`, `stop_order_id`, `risk_dollars` (worst-case incl. overnight gap), `strategy`, `sector`.
- `RiskDecision`: map 0DTE `Decision` codes and stock `(ok, code)` strings to a shared reason-code enum; keep legacy code in `inputs`.
- `Broker` protocol: add `replace_order` (stop ratchet), `get_clock`/`get_calendar`, open orders by prefix; split market data into a `DataProvider` protocol.
- Missing protocols: `CentralRisk` with atomic `reserve`/`release`/`expire` (0DTE already has `reserve_entry`/`expire_stale_reservations`), `OrderManager`, `PdtBudget`.
- IDs: keep `ESHEON-` distinct; reconciliation must also recognise `ESHEL-ZDTE/ICT/SDAY/SSCP/SDCO-`.

## 9. Top risks

1. 0DTE has a live-endpoint path (`ALPACA_PAPER=false`) and is not covered by `require_paper_mode()`.
2. 0DTE + ICT share one account; shared loss governor fails open (conflicts with CLAUDE.md rule 8).
3. No PDT budget in 0DTE or Bot 3 trader.
4. Two 0DTE tests hit the network; 6 tests only pass in the deployed layout, so dev "green" is not reachable as-is.
5. `optbot/cog.py` and `optbot/macd_first_engine.py` have no pin test.
6. Bot 3 now trades a rule that failed its backtest; docs (CLAUDE.md, plan) still call Bot 3 log-only.
7. Deploy-branch ambiguity (zdte-arch vs zdte-live `fixes-345`).
