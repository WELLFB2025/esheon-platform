# EshelBot Trading Bots — Developer Guide

Oct 11, 2026 · @WELLS

Four bots trade or watch the market on Alpaca **paper** accounts: the live 0DTE options bot, plus three bots in ~/work/stock-bots (daily stocks, 2-minute stock scalps, and a log-only zone signal logger). Code is built and tested in the work repos and copied into ~/alpaca_trading_bots/\<bot\> by a deploy script that the owner runs.

## The bots

Only the 0DTE options bot is confirmed live. The three stock-repo bots are built and tested, and their deploy commands were handed over on 2026-10-11.

| Bot                         | What it does                                                                                   | Source (build + test here)         | Live folder (~/alpaca_trading_bots/) | launchd label           | Order prefix | Status                                                        |
|-----------------------------|------------------------------------------------------------------------------------------------|------------------------------------|--------------------------------------|-------------------------|--------------|---------------------------------------------------------------|
| EshelBot 0DTE               | Buys same-day SPY/TSLA calls or puts on a MACD-first + EMA 9/21 signal (2-min)                 | ~/work/zdte-live, branch fixes-345 | zero_dte_bot                         | com.wells.zerodtebot    | ESHEL-ZDTE-  | Live (f567fa8b); variant-D shadow 7784ed3e waiting for deploy |
| Bot 1 stock_daily_bot       | Same signal on **daily** candles, long-only fractional stocks, holds overnight                 | ~/work/stock-bots                  | stock_daily_bot                      | com.wells.stockdailybot | ESHEL-SDAY-  | Built a4352f2; not confirmed deployed                         |
| Bot 2 stock_scalp_bot       | Same signal on **2-min** candles, long-only fractional scalps                                  | ~/work/stock-bots                  | stock_scalp_bot                      | com.wells.stockscalpbot | ESHEL-SSCP-  | Built a4352f2; not confirmed deployed                         |
| Bot 3 sd_zone_signal_logger | Logs demand/supply-zone signals (v1/v2/v3) on SPY/TSLA with real 0DTE quotes. **Never trades** | ~/work/stock-bots (optbot/)        | sd_zone_signal_logger                | com.wells.sdzonelogger  | none         | Built a4352f2; not confirmed deployed                         |

Research and backtests live separately in ~/work/zdte-arch (branch main, research/), with their own .venv. That venv is also the one that runs the stock-bots tests. A sibling ict_liquidity_bot folder also exists. It is out of scope here; the deploy scripts only check that its API key is not reused.

## How the code moves

_Diagram (not included): code path · 3 repos → owner's deploy → 4 bots → Alpaca._

code path · 3 repos → owner's deploy → 4 bots → Alpaca

Developers build and test in the work repos. Only a deploy script the owner runs copies code into ~/alpaca_trading_bots/, and each trading bot talks to its own paper account.

## EshelBot 0DTE options bot

The bot holds at most one 1-contract SPY or TSLA 0DTE option, entered on a MACD-first signal and exited by a staged premium stop. Its own README.md is out of date: it still describes ±\$30 exits. Trust bot.py's header docstring and config.py.

**Runtime** (runtime.py, see docs/ARCHITECTURE.md). A supervisor starts two threads that share one Portfolio:

- **Trade manager**, every 5 s (20 s when the market is closed). It syncs every position with the broker, which is the source of truth, then runs each position's stop, lock, trail and 15:45 flatten.

- **Opportunity scanner**, every 60 s. It runs every symbol through the MACD-first signal, RiskEngine.can_open_position(), contract choice, OrderManager, and then signals.csv.

**Signal** (macd_first_engine.py + macd_first_signal_adapter.py, 2-min IEX bars):

- The MACD (12,26,9) cross comes first. An EMA 9/21 cross in the same direction must confirm it 1–10 candles later.

- Until 10:15 ET a MACD cross with the EMAs already aligned also counts (trend_open_entry.py). The same applies to a pre-market cross still in force at 09:30 (the carry entry).

- Candidates go earliest signal candle first, then by MACD-histogram strength. The SPY-first priority timer was removed on 2026-10-06.

**Contract and size:**

- Today's expiry, strike nearest the underlying.

- Ask between \$0.50 (MIN_OPTION_PREMIUM) and \$2.00 (\$200 per contract).

- 1 contract. Limits in config.py: 1 position, 1 contract, \$200 risk.

- TSLA has 0DTE options only on Mon/Wed/Fri. zero_dte_universe.py skips symbols with no same-day contract.

**Exits** (per contract, bot.py):

| Stage   | Trigger             | Stop                                                                                            |
|---------|---------------------|-------------------------------------------------------------------------------------------------|
| Initial | at entry            | broker-side hard stop \$15 below entry                                                          |
| Protect | premium P&L ≥ +\$30 | moves up to lock +\$15                                                                          |
| Trend   | P&L ≥ +\$60         | trails \$10 below the option's best bid; the resting stop is re-placed when the trail rises \$5 |
| Flatten | 15:45 ET            | sell everything; no new entries                                                                 |

**Guardrails:**

- \$100 minimum cash after entry.

- Daily max loss of \$200 per contract, then halted for the day.

- A 3-scan cooldown after every close.

- No averaging down.

- Each signal bar is acted on once.

- The consecutive-loss halt is off (losses are still counted).

- The self-learner (learner.py) can veto a (direction, UTC hour) bucket with ≥ 8 trades and \< 35% wins. An audit found defects in it, recorded in research/self_learner_audit.

**Shadows (log only, never trade):**

| Shadow                                                                   | Where                                        | Writes                               |
|--------------------------------------------------------------------------|----------------------------------------------|--------------------------------------|
| Rules R2 (skip 10–11 ET), T20, R1, COG filter, strategy C (VWAP+COG), W2 | config.SHADOW_RULES, checked live per signal | shadow\_\*.csv, signals.csv          |
| \$20 stop                                                                | shadow_stops.py, after 16:20 ET              | shadow_stops.csv                     |
| 8-min entry delay                                                        | shadow_delay.py                              | shadow_delay8.csv                    |
| EMA21 trend-line exit                                                    | shadow_trendline.py                          | shadow_trendline.csv                 |
| Range trails R30_8, R50_5                                                | shadow_rangetrail.py                         | shadow_rangetrail.csv                |
| Pre-market continuation                                                  | shadow_premarket.py, after 16:10 ET          | shadow_premarket.csv                 |
| Variant D (no +\$30 lock)                                                | shadow_nolock.py                             | shadow_nolock.csv (not yet deployed) |

The after-close shadows run after 16:20 because Alpaca serves option bars only once they are 15+ minutes old. Each one replays trades with stop_replay.simulate_exit_v on 1-minute option bars. Each shadow has an off switch in config.py.

**Records:**

- trade_ledger.csv holds closed trades with **gross** P&L. Alpaca posts fees separately as FEE activities, about \$0.10–0.12 per round trip.

- signals.csv, quote_log/ (real bid/ask, JSONL per day), portfolio_state.json, bot.log.

## Stock bots: the shared engine

Bots 1 and 2 run the same stockbot/ package. The only difference is the settings.py copied in at deploy (bots/daily/ or bots/scalp/). run.py loads .env, validates the settings and refuses to start unless ALPACA_PAPER=true. It then holds an fcntl lock and calls Bot.step in a loop.

**One Bot.step cycle** (stockbot/runner.py):

1.  Load bot_state.json. Read the clock and the account; if the account read fails, no entries this cycle.

2.  On the first open cycle of a session, roll the locks (locks.new_session). Then update them against equity, and cancel open entry orders if a lock fires.

3.  Reconcile every tracked position with the broker. A broker-side stop fill is booked as a close.

4.  Manage each position with exits.decide: stop, profit lock, trail, time stop, flatten. Exits always run, even when locked.

5.  If the scan is due and inside the entry window, run the scan:

    1.  Load the universe and fetch bars.

    2.  Run signals.evaluate, then sort the signals by EMA-cross time.

    3.  Check risk.can_enter, then \_size_and_gate, then portfolio.check.

    4.  Enter.

6.  Write risk_status.json and save the state.

**Entry gates, in order:**

- risk.can_enter: long only, entry window, position limit, already held, account blocked, locks, daily loss, consecutive-loss halt, cooldown, duplicate signal, PDT, cash reserve.

- Sizing: a fresh quote, the ATR, a valid stop, then risk-based size.

- portfolio.check: exposure, open risk, sector, and correlation with held names.

Every decision lands in signals.csv with its code.

**Entry** (\_enter): the signal key is saved as acted *before* the order, so it is never sent twice. The order is a market buy with a client order id. If the submit throws, the broker is asked for that id before giving up, and entries are never retried. Any unfilled remainder is cancelled, the stop is computed from the actual fill, and a resting DAY stop order is placed.

| Module                                             | Role                                                            |
|----------------------------------------------------|-----------------------------------------------------------------|
| botsettings.py                                     | frozen Settings dataclass + validate()                          |
| broker.py                                          | AlpacaBroker (paper only); bars, quotes, orders, stops; DRY_RUN |
| signals.py                                         | exact EMA-cross pre-filter, then the MACD-first engine          |
| macd_first_engine.py, macd_first_signal_adapter.py | byte-identical copies of the 0DTE bot's engine                  |
| sizing.py                                          | size(), stop_price() (pct / ATR / dollars), fractional step     |
| exits.py                                           | decide(), initial_stop(), R-unit thresholds()                   |
| locks.py                                           | daily-loss, consecutive-loss, drawdown locks; manual_reset      |
| portfolio.py                                       | exposure, open-risk, sector, correlation, PDT room              |
| risk.py                                            | can_enter                                                       |
| state.py                                           | bot_state.json: positions, pending, acted signals, locks        |
| universe.py + universe_snapshot.json               | S&P 500 + 15 ETFs (518 symbols) with sectors                    |
| ledger.py, notify.py                               | trade_ledger.csv; ALERT log lines + optional Telegram           |

## Bot 1 and Bot 2: settings

Both bots trade the same MACD-first + EMA 9/21 signal, long only, across S&P 500 + 15 ETFs, with up to 3 positions. Bot 1 swings on daily candles with risk-based sizing; Bot 2 scalps 2-min candles at a fixed \$200. Each bots/\<x\>/settings.py is the single source of truth, and its docstring records the user decisions behind it.

| Setting           | Bot 1 stock_daily_bot                                                                              | Bot 2 stock_scalp_bot                                      |
|-------------------|----------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| Candles           | daily (signal on the last completed session)                                                       | 2-minute                                                   |
| Entry window (ET) | 09:31–10:00                                                                                        | 09:30–15:25                                                |
| Sizing            | risk-based fractional: 0.5% of equity (1% ceiling), capped at \$200                                | \$200 notional, fractional                                 |
| Initial stop      | 1.5 × ATR14 of completed daily bars (stop_mode="atr"); 5% fallback for adopted positions           | −\$1.00                                                    |
| Profit exits      | in R: +3R locks +1.5R; +6R starts a 1R trail (0.5R ratchet)                                        | +\$1.50 target; breakeven at +\$1.00; 20-min time stop     |
| End of day        | holds overnight (no flatten)                                                                       | flatten 15:45                                              |
| Loss controls     | daily loss 1.5% of equity; 3 losses in a row (both reset next session); 8% drawdown (manual reset) | \$200 daily loss; stop for the day after 3 losses in a row |
| Portfolio gate    | exposure ≤ 60%, open risk ≤ 1.5%, sector block, correlation ≤ 0.80 (60 days)                       | exposure ≤ 80%, sector block, correlation ≤ 0.80           |
| Always            | \$100 cash reserve, 3-candle cooldown, PDT guard (no entry once Alpaca's day-trade count is 3)     | same                                                       |
| Poll / scan       | 15 s / 60 s                                                                                        | 5 s / 60 s                                                 |

**Known limits:**

- Alpaca fractional orders are DAY-only. Bot 1's protective stop is re-placed every morning, so **positions are unprotected overnight** (gap risk).

- A \$500 account has 3 day trades per 5 business days. That caps Bot 2 at about 3 scalps a week, and the PDT guard enforces it.

- Manual lock reset: python run.py --reset-lock NAME --reason "...". It is audited in the log; see docs/BOT1_RISK_SPEC.md.

## Bot 3: sd_zone_signal_logger

Bot 3 records, live and side by side, what three demand/supply-zone entry rules would have done on SPY and TSLA 0DTE options. All three failed their pre-registered backtests, so it **never trades**; it builds out-of-sample evidence.

**Zones** (optbot/zones.py):

- Zones are built on 15-min candles assembled from 2-min bars (to_15min).

- A zone is "base before impulse": 1–3 base candles with bodies ≤ 0.5 ATR14 (Wilder), then a 1–3-candle impulse of ≥ 1.5 ATR that breaks the last swing (swing_n=3).

- Demand zones give CALLs; supply zones give PUTs.

- A zone expires after 3 sessions, or when a close goes through it.

**Entry rules** (optbot/strategy.evaluate, one signal per zone per version):

| Version | Params       | Trigger                                                                                                                   | Spec                        |
|---------|--------------|---------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| v1      | ZoneParams() | a Change of Guard (cog.py, verbatim live copy) **confirms** on the last 2-min candle, within 15 bars of the first retest  | backtest/sdcog_spec.json    |
| v2      | zones.V2     | a COG is **active** in the zone's direction during any retest within 30 bars (60 min)                                     | backtest/sdcog_v2_spec.json |
| v3      | zones.V3     | no COG: a rejection candle (into the zone, closes back out in the favourable half) on ≥ 1.5× the 20-candle average volume | backtest/sdvol_v3_spec.json |

**Each 60-s scan** (optbot/logger.SignalLogger.step), 09:32–16:00 ET while the market is open:

1.  Fetch 7 days of 2-min IEX bars once a day, again after any gap over 10 minutes, then a 12-minute top-up each scan.

2.  Evaluate v1, v2 and v3 for each symbol. An error in one version does not stop the others.

3.  Append each new (version, zone) to signals_log.csv with:

    - the zone and trigger detail;

    - the nearest-strike 0DTE contract and its real bid/ask (QUOTE_ACTUAL);

    - eligible, or the reason it isn't: premium outside \$0.50–\$2.00, entry at or after 15:28 SPY / 15:13 TSLA, no chain, no quote.

4.  Dedupe keys persist in logger_state.json, so a restart never logs a signal twice.

**After 16:30 ET**, once per day, each eligible signal is replayed:

- The replay uses the production exits, through optbot/stop_replay.py (a byte-identical copy of the live module) with a ProductionRules object.

- It runs on the day's 1-minute option trade bars, entering at the logged ask.

- Results go to outcomes.csv.

- They are hypothetical, before costs: subtract about \$2–4 per trade.

**No-order guarantee** (both enforced by tests/test_sdlogger.py):

- The source contains no order code. The test parses the AST of logger.py, data.py, strategy.py, zones.py and run_sdlog.py.

- optbot/data.ReadOnlyTrading wraps the trading client so only get_clock and get_calendar are reachable. Anything else raises PermissionError.

**Promotion rule:** a version may become a trading bot only if its live-logged outcomes are positive after MODERATE costs over ≥ 30 eligible signals.

## Testing

Every change must pass its repo's full suite before commit, and every deploy script runs the suite again in the installed layout. If the tests fail, the bot is not restarted (or the change is rolled back).

| Suite                                | Tests | Command (from the repo root)                                                                                  |
|--------------------------------------|-------|---------------------------------------------------------------------------------------------------------------|
| 0DTE (~/work/zdte-live/tests)        | 448   | ALPACA_API_KEY=T ALPACA_SECRET_KEY=T ~/work/zdte-arch/.venv/bin/python -m pytest -q -p no:cacheprovider tests |
| stock-bots (~/work/stock-bots/tests) | 110   | same command                                                                                                  |

The dummy T keys only satisfy imports. No test calls Alpaca, and none needs a .env.

**stock-bots suites:**

| File                 | Tests | Covers                                                                                                                                                           |
|----------------------|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| test_risk.py         | 54    | sizing, ATR, locks, portfolio/correlation gate, broker failures (timeouts, partial fills, rejections), restarts, settings validation                             |
| test_sdlogger.py     | 23    | Bot 3: no-order AST check, read-only client, dedupe across restarts, eligibility, gap refetch, production-exit replay, fixture-day parity with strategy.evaluate |
| test_optbot_zones.py | 13    | zone detection, retests, v2/v3 params against the spec files                                                                                                     |
| test_stockbots.py    | 13    | Bot 1/2 end-to-end steps on tests/fakes.FakeBroker                                                                                                               |
| test_regression.py   | 7     | golden decisions on real SPY/TSLA bars                                                                                                                           |

**Fixtures:** tests/fixtures/ holds SPY/TSLA daily and 2-min CSVs plus golden.json. The golden file was recorded from the pre-upgrade code by tests/make_golden.py. Regenerate it only for an intended behaviour change, and say so in the commit.

**Verbatim copies stay verbatim.** Several modules are byte-identical copies of the live 0DTE bot:

- stockbot/macd_first_engine.py and stockbot/macd_first_signal_adapter.py are checked against ~/work/zdte-live (test_risk.py) and against pinned hashes (test_stockbots.py).

- optbot/stop_replay.py is checked against ~/work/zdte-live (test_sdlogger.py).

- optbot/cog.py and optbot/macd_first_engine.py match live as of 2026-10-11, but **no test guards them yet**. Adding one is an open item.

- The live-folder checks skip when ~/work/zdte-live is absent. Never edit a copy: change the live module first, then re-copy.

**Live-code fingerprint:** ~/work/zdte-arch/research/shadow_audit/prod_fingerprint.py OUT.json \[COMPARE.json\] hashes the live 0DTE folder's code files without opening .env. Use it to prove research left production untouched.

## Deploy and operate

The owner runs every deploy, from a terminal or as ! \<command\> in Claude Code. Developers build, test and commit, then hand over the exact command. Each deploy script refuses to run when the source repo has uncommitted changes.

| Bot           | Deploy command                                                   | What the script does                                                                                                                                                                                                                                                                                                                         |
|---------------|------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0DTE          | sh ~/work/zdte-live/deploy/deploy\_\<change\>.sh                 | refuses during market hours (09:25–16:05 ET Mon–Fri) unless --during-market-hours; refuses if any live file differs from its BASE commit; backs up to deploy_backups/\<ts\>\_\<change\>; copies only the listed files; runs the 448 tests in the live layout; restarts; checks the startup line; **rolls back automatically** on any failure |
| Bot 1 / Bot 2 | sh ~/work/stock-bots/deploy/deploy_stock_bot.sh daily (or scalp) | first run creates .env from env.example and stops; refuses template keys and any API key shared with another bot; backs up; copies stockbot/, bots/, tests/, run.py, the bot's settings.py; own venv; runs tests; installs the launchd plist; checks the startup line                                                                        |
| Bot 3         | sh ~/work/stock-bots/deploy/deploy_sd_logger.sh                  | same pattern; copies optbot/, its tests and fixtures, and the three spec files; run_sdlog.py becomes run.py; a shared key only prints a rate-limit note (it never trades)                                                                                                                                                                    |

**The BASE rule (0DTE):** each 0DTE deploy script names the live commit it was built on. After a successful deploy, the deployed commit becomes the next script's BASE. Live is f567fa8b today, or 7784ed3e once the variant-D shadow is deployed.

**Running services** (launchd, KeepAlive; the stock-repo bots also throttle restarts to 30 s):

| Task                 | Command                                                                          |
|----------------------|----------------------------------------------------------------------------------|
| Stop a bot           | launchctl bootout gui/\$(id -u)/\<label\>                                        |
| Restart              | launchctl kickstart -k gui/\$(id -u)/\<label\>                                   |
| Watch the log        | tail -f ~/alpaca_trading_bots/\<folder\>/bot.log                                 |
| Crash output         | launchd_stderr.log in the bot folder                                             |
| Reset a Bot 1/2 lock | venv/bin/python run.py --reset-lock NAME --reason "..." in the bot folder        |
| Dry run (Bot 1/2)    | DRY_RUN=true in the bot's .env: signals and decisions are logged, no orders sent |

**Files each bot writes** (never copied over by a deploy):

- 0DTE: trade_ledger.csv, signals.csv, shadow\_\*.csv, quote_log/, portfolio_state.json.

- Bots 1/2: trade_ledger.csv, signals.csv, bot_state.json, risk_status.json.

- Bot 3: signals_log.csv, outcomes.csv, logger_state.json.

- Every bot: bot.log.

## Rules every change follows

These bots trade on paper only, and no change reaches a live folder without the owner running it.

1.  **Paper only.** Every broker client is built with paper=True. The stock bots refuse to start unless ALPACA_PAPER=true. Never add a live-trading path.

2.  **Secrets.** Never print, log, commit or paste key values. Never open a bot's .env from tooling; deploy scripts compare keys without printing them. Alpaca FEE activity descriptions contain the account number, so redact it in anything you publish.

3.  **Who deploys.** Developer tooling (including Claude Code) cannot edit ~/alpaca_trading_bots/\*\*, cannot run shell commands that touch it, and cannot run launchctl. This is deliberate. Build in the work repos, commit, and hand over the deploy command.

4.  **One account per bot.** Each trading bot has its own Alpaca paper account, order-ID prefix, folder, venv, state and launchd label. They share no files at runtime.

5.  **Strategy changes need explicit approval.** A new rule ships as a **shadow** first: logged next to what the bot actually did, with an off switch in config. It goes live only on the owner's say-so.

6.  **Pre-register research.** Commit the spec (rule, parameters, periods, pass criteria) before the first run, and report the decision it produces. The periods are:

    - P1 development: 2024-09-16..2025-09-15

    - P0 held-out: 2024-02-05..09-13, now used once

    - P3: 2025-09-15..2026-03-31

    - P2: 2026-04-01..09-30

7.  **Honest labels.** Simulated or replayed prices are never called fills. Tag every price QUOTE_ACTUAL, BAR_PROXY or paper fill. Bot P&L is gross; fees are separate. Judge results after the MODERATE and ADVERSE costs from research/execution_cost_study.

8.  **Verbatim copies stay verbatim.** Shared engine files are copied byte-for-byte from the live 0DTE bot (see Testing).

## Research so far and open items

No strategy tested so far shows an edge after realistic costs. Risk controls cut drawdowns but do not create profit, which is why everything stays on paper and new ideas ship as shadows. Studies live in ~/work/zdte-arch/research/\<study\>/ or ~/work/stock-bots/backtest/.

| Date       | Study                                         | Result                                                                                                                              |
|------------|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| 2026-10-11 | Bot 3 zones v3: volume rejection, no COG      | FAIL: P1 −\$226, P3+P2 −\$210 after MODERATE costs                                                                                  |
| 2026-10-11 | Bot 3 zones v1 / v2: COG confirm / COG active | FAIL: v1 only 11 trades in 2.5 years; v2 P1 −\$45, P3+P2 −\$50                                                                      |
| 2026-10-11 | Bot 1 next-session lock reset                 | OOS +8.7% at base costs, −4.8% at conservative costs                                                                                |
| 2026-10-10 | Bot 1 ATR stop                                | positive in development and OOS, but the profit came from the top 3 trades                                                          |
| 2026-10-10 | 0DTE risk variants at \$500/\$200             | only variant D (no +\$30 lock) beat production on development and held-out data; still negative after costs, so it runs as a shadow |
| 2026-10-09 | Self-learner audit                            | a fixed rule, not ML; no predictive value; defects found (feedback lock, 35% floor, UTC buckets)                                    |
| 2026-10-09 | Execution costs                               | observed half-spreads \$0.005–0.025/share; no executable edge                                                                       |
| 2026-10-09 | Entry-vol filter v1                           | null on held-out P0                                                                                                                 |
| 2026-10-04 | 0DTE rule R2 (skip 10–11 ET)                  | passed all 3 periods; in shadow since 2026-10-04                                                                                    |

**Open items:**

- [ ] Owner deploys: Bot 1, Bot 2, Bot 3, and the 0DTE variant-D shadow (commands in Deploy and operate).

- [ ] Add a test that pins optbot/cog.py and optbot/macd_first_engine.py to the live copies.

- [ ] Update the 0DTE README.md; it still describes ±\$30 exits.

- [ ] Evaluate the shadows after 2–4 weeks with shadow_report.py \<rule\> and research/shadow_audit/evaluate_shadow.py. The protocol needs ≥ 20 sessions and ≥ 100 MACD-first signals.

- [ ] Schedule research/shadow_audit/shadow_collect.py to run after 16:30 ET; it is not scheduled yet.

- [ ] Fix the self-learner defects, or switch it off. It is waiting on an owner decision.

- [ ] Confirm whether ict_liquidity_bot is still running and who owns it.
