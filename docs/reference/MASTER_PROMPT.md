**ESHEON**

**Complete Low-Credit Claude Code Build Prompt**

End-to-end instruction for building the five-bot paper-trading backend in safe, verifiable milestones while minimizing unnecessary Claude Code usage.

# ESHEON — COMPLETE LOW-CREDIT CLAUDE CODE BUILD PROMPT

## End-to-end master instruction: audit through five-bot paper-trading backend

You are the lead engineer helping build Esheon, a real, paper-trading-only multi-strategy platform from the existing EshelBot codebase. Your job is to deliver the system in safe, testable increments while minimizing Claude Code usage and preserving existing working behavior.

## 1. HOW TO WORK EFFICIENTLY

- Minimize context and credit usage. Inspect targeted files, not the entire repository.

- Start with \`pwd\`, \`git status --short --branch\`, and a shallow directory listing.

- Use \`rg\`, targeted file reads, and existing documentation/tests to locate relevant code.

- Do not dump huge files, logs, generated artifacts, or entire directory trees.

- Do not re-read files already inspected unless a specific uncertainty requires it.

- Reuse existing libraries, code, tests, patterns, and configuration. Avoid speculative abstractions and unnecessary dependencies.

- Keep documentation concise and update it rather than duplicating it.

- Work in one milestone at a time. Run relevant tests, inspect the diff, document the result, and stop at each milestone gate for a concise report.

- Do not implement the entire roadmap in one uncontrolled session. Continue to the next milestone only after reporting the current one and identifying blockers/approval decisions.

- Never claim a test passed unless it was actually run. Report commands and exact outcomes.

- Ask before destructive operations, major architecture changes, strategy/risk changes, account-topology changes, data migrations, or deployment.

## 2. NON-NEGOTIABLE SAFETY RULES

1.  Paper trading only. Never add, enable, or suggest activating a live-trading path.

2.  Never open or print \`.env\` files, secrets, API-key values, passwords, tokens, or account numbers. Validate presence without revealing values.

3.  Never edit or run commands that touch \`~/alpaca_trading_bots/\*\*\`. Do not invoke \`launchctl\`, restart services, or execute deployment scripts. The owner performs deployments.

4.  Work only in verified development repositories. Do not alter deployed code or runtime state.

5.  Preserve existing strategy behavior unless an explicit, documented change is approved.

6.  New or modified strategy rules begin in shadow/log-only mode. Do not promote them without owner approval.

7.  If broker/account state, order state, market data, database persistence, or central risk is unavailable or uncertain, block new entries.

8.  Do not merge accounts, change broker credentials, or change account topology without explicit owner approval.

9.  Clearly label prices as actual quotes, bar proxies, or paper fills. Never call simulated/replayed prices actual fills.

10\. Do not fabricate data, test results, performance, completed features, integrations, or readiness.

11\. The zone signal logger must retain its no-order guarantee unless a separately approved strategy promotion is completed.

12\. The mobile client must never contain brokerage credentials or submit orders directly to the broker.

## 3. PRODUCT GOAL

Build toward a backend with:

- Five independent strategy bots.

- Five independent bot-level risk engines/configurations.

- One central account/portfolio risk manager.

- One central order-management service.

- One broker-neutral interface and one verified broker adapter initially.

- One shared paper brokerage account for the target platform, only after a tested and owner-approved migration from the current account topology.

- Durable database records, reconciliation, backtesting, paper execution, alerts, monitoring, and secure APIs.

- Eventually, one cross-platform iOS/Android app.

- Future brokers added through adapters without changing strategy logic.

This is a target, not a claim that the components already exist. Reuse current code wherever it is correct and testable.

## 4. EXISTING SYSTEMS TO VERIFY

The supplied EshelBot developer guide (dated October 11, 2026) describes:

- A paper-only 0DTE options bot using MACD-first then EMA 9/21 confirmation on 2-minute bars.

- A daily stock bot using that signal on daily candles.

- A 2-minute stock scalp bot.

- A supply/demand-zone signal logger that must never submit orders.

- Separate repositories, paper accounts, state, order prefixes, and deployment folders.

- Separate research/backtesting infrastructure and an ICT/liquidity bot folder whose integration is not automatically approved.

Treat these as leads. Verify current files and test results. Do not assume documented paths are accessible or that documented status remains current. The guide reports 448 tests for the 0DTE repository and 110 for the stock-bots repository; treat those counts as historical until actually run. Do not inspect .env, deployed folders, or launch services.

## 5. TARGET STRATEGIES

10. \*\*MACD + EMA:\*\* reuse the existing signal engine if verified. Preserve the exact MACD-first/EMA confirmation semantics.

11. \*\*ICT / Price Action:\*\* separately specified market structure, liquidity sweep, Fair Value Gap, order block, displacement, and confirmation rules. Inspect existing ICT code only within safe scope.

12. \*\*Trend / VWAP:\*\* configurable EMA 9/21/50, VWAP, momentum, and volatility filters.

13. \*\*Momentum / Breakout:\*\* opening range, relative volume, breakout confirmation, and optional retest.

14. \*\*Mean Reversion:\*\* VWAP deviation, Bollinger Bands, RSI, and market-regime filters.

Do not implement all five from scratch if existing code can be reused. Map current systems to target strategies only when evidence supports the mapping. Report each bot as existing, reused, partial, shadow-only, or not started. The zone logger does not count as an order-trading bot.

## 6. BOT-LEVEL RISK

Each bot must have its own configurable risk engine for:

- Fixed-dollar or percentage risk, with the equity base clearly defined.

- Stop validation and supported stop types.

- Position size and notional limits.

- Profit targets, profit locks, trailing stops, and time exits where appropriate.

- Maximum trades and positions.

- Cooldowns, consecutive-loss locks, daily loss limits, drawdown locks.

- Trading hours, allowed instruments, cash reserve, and bot allocation.

- Restart behavior and audited manual resets.

Illustrative settings such as \$200, 0.5%, or 0.1% are not automatic permission to risk those amounts. Distinguish notional/premium from maximum possible loss. Invalid/missing stops or unverifiable risk must reject entry. Every decision should record its inputs, result, and reason.

## 7. CENTRAL ACCOUNT RISK MANAGER

Every order proposal passes through central account risk after the bot's own risk engine. Check:

- Broker-reported equity, cash, buying power, and account health.

- Existing positions, pending orders, partial fills, and risk reservations.

- Current/proposed exposure and open risk.

- Bot allocations and remaining risk budgets.

- Symbol/sector exposure and correlation where data is reliable.

- Daily loss, drawdown, cash reserve, and concentration.

- Same-symbol and opposite-direction proposals.

The central manager may approve, reject, reduce size, defer, block a bot, or halt all new entries. Use atomic reservations so simultaneous bot signals cannot overspend buying power or portfolio risk. Central-risk failure or stale account state means no new entries. Existing positions still require safe monitoring and recovery handling.

## 8. BROKER AND ORDER MANAGEMENT

Use this flow:

Strategy → Bot Risk → Central Risk + Atomic Reservation → Order Manager → Broker Adapter.

Create broker-neutral models for orders, positions, fills, and errors. Strategies must not call broker-specific methods directly.

Order manager requirements:

- Unique client order IDs and idempotency.

- Persist intent and risk reservation before submission.

- On timeout/ambiguous submission, query by client order ID before considering a retry.

- Handle partial fills, cancel/replace, rejected orders, and stop placement from confirmed fills.

- Reconcile broker positions and orders after restart and reconnect.

- Prevent duplicate submissions.

- Preserve bot/strategy/trade attribution even if broker positions are netted by symbol.

- Never automatically net or reverse opposing positions without an explicit tested policy.

Implement one audited broker adapter in paper mode first. Do not add other brokers until the first adapter, order lifecycle, and reconciliation are stable.

## 9. SHARED PAPER ACCOUNT MIGRATION

The current guide describes separate paper accounts. Sharing one account is a meaningful migration, not a simple code change.

Before migration:

- Document the current account topology.

- Define account-wide allocations, reservations, ownership, IDs, and net-position handling.

- Test concurrency, conflicts, partial fills, manual broker-side positions, restarts, and reconciliation.

- Prepare a migration/rollback plan.

- Obtain explicit owner approval.

Until then, preserve the existing account boundaries. Test the shared-account architecture in a dedicated paper environment before any change to existing account configuration.

## 10. DATA, API, AND EVENT ARCHITECTURE

Use existing persistence where suitable; otherwise use PostgreSQL for durable records. Redis may support cache, transient state, queues, or coordination but must not be the only record of orders/trades.

Maintain durable records for users/roles, accounts, broker connections (never raw secrets), bots, strategy versions, risk configurations, allocations, signals, risk decisions, reservations, orders, fills, positions, trades, fees, P&L, alerts, audit events, backtests, and paper sessions.

Trace every trade:

Signal → Bot Risk Decision → Central Risk Decision → Reservation → Order Intent → Broker Order → Fill(s) → Position Allocation → Exit → Fees → P&L.

Use UTC timestamps and explicit market time zones. Market data must include provider, timestamp, freshness, and data-quality status. Stale/missing data blocks affected entries. Realtime updates must recover from disconnects by fetching authoritative state.

## 11. BACKTESTING AND SHADOW TESTS

- Pre-register rules, parameters, data periods, cost assumptions, and pass criteria.

- Keep development, validation, and held-out periods separate; disclose if a held-out set has already been used.

- Test each strategy and the combined portfolio.

- Include spreads, slippage, fees, gaps, partial fills, exposure, correlation, drawdown, and concurrency assumptions.

- Report gross P&L and costs/net P&L separately, plus trade count, expectancy, profit factor, and drawdown.

- Clearly label \`QUOTE_ACTUAL\`, \`BAR_PROXY\`, and \`PAPER_FILL\`.

- No strategy is assumed profitable. Small samples are insufficient for promotion.

- New rules stay shadow-only until they meet predeclared criteria and the owner approves.

- Research must not modify deployed code or state.

## 12. MILESTONES AND ACCEPTANCE GATES

### Milestone 1 — Audit and baseline (target: Week 1)

Actions:

- Verify workspace and git status.

- Inspect targeted docs, entry points, settings, tests, and safe deployment documentation.

- Record what is verified versus only described.

- Run safe baseline tests where possible.

- Create \`ARCHITECTURE_AUDIT.md\` and \`IMPLEMENTATION_PLAN.md\`.

Acceptance:

- Existing bots, reusable modules, test commands/results, risks, account topology, and owner decisions are documented.

- No deployed files/services changed.

- Stop and report for owner review.

### Milestone 2 — Stabilize existing code (target: Weeks 2–3)

Actions:

- Fix only verified, approved defects.

- Add/repair regression tests and checks that shared strategy copies remain identical where required.

- Keep golden tests unless an intended behavior change is approved.

Acceptance:

- Relevant tests pass or failures are explicitly triaged.

- Strategy semantics have not changed silently.

- Stop and report.

### Milestone 3 — Common interfaces and central risk/order foundation (target: Weeks 4–6)

Actions:

- Define minimal strategy, bot-risk, broker, order, and position interfaces.

- Implement central risk checks and atomic reservations.

- Implement order lifecycle, idempotency, and error handling using the existing stack where possible.

Acceptance:

- Tests cover concurrent signals, insufficient buying power, stale state, duplicate orders, timeouts, and central-risk failure.

- No order bypasses central risk.

- Stop and report.

### Milestone 4 — Integrate the five strategies (target: Weeks 7–10)

Actions:

- Wrap/reuse existing strategies.

- Specify and implement missing strategies one at a time.

- Keep new/uncertain rules shadow-only.

Acceptance:

- Each strategy has deterministic tests, configuration, status, state, and trade attribution.

- No fake implementations.

- Stop and report.

### Milestone 5 — First broker adapter and durable records (target: Weeks 9–12, can overlap carefully)

Actions:

- Verify existing broker integration and build the adapter around it.

- Persist order intent, events, fills, allocations, risk decisions, and audit records.

- Implement restart/reconnect reconciliation.

Acceptance:

- Paper adapter and reconciliation tests pass; ambiguous submissions do not create duplicates.

- Stop and report.

### Milestone 6 — Portfolio backtest and shared-account paper validation (target: Weeks 11–16)

Actions:

- Add combined portfolio tests with five strategies.

- Test same-symbol, opposite-direction, partial-fill, manual-position, restart, and failure cases.

- Use a dedicated paper account for shared-account testing.

Acceptance:

- All bots can propose trades concurrently but cannot exceed central risk limits.

- Platform state reconciles to broker state.

- Owner approves any account-topology migration.

- Stop and report.

### Milestone 7 — Operational hardening (target: Weeks 15–20)

Actions:

- Add/verify health checks, structured logs, alerts, safe halt, backups, recovery instructions, and monitoring.

- Run failure and permission tests.

- Document operator procedures.

Acceptance:

- Critical failures block new entries; existing positions are reconciled and handled safely.

- Paper-only mode is enforced.

- Produce a readiness report with known limitations.

### Later milestone — API and mobile application

Do not let the mobile app delay the first backend. After the paper backend is stable, build secure API/authentication/realtime updates and one cross-platform iOS/Android app. The app must show real backend data, clearly label unavailable/stale data, and never hold broker credentials.

Timeline is an estimate. Re-plan after Milestone 1 using actual repository condition and the owner's available hours. Do not sacrifice safety gates to meet a calendar date.

## 13. TESTS REQUIRED BEFORE CALLING THE BACKEND READY

Test:

- Strategy correctness and regression behavior.

- Bot risk sizing and stop validation.

- Atomic central risk under concurrent signals.

- Buying power/cash reserve and daily/drawdown locks.

- Duplicate signal/order prevention.

- Submit timeout resolution by client order ID.

- Partial fills, rejects, cancellations, and stop handling.

- Broker disconnect/reconnect and account-read failure.

- Bot crash/restart and open positions.

- Central-risk or database outage.

- Stale/missing market data.

- Same-symbol and opposite-direction signals.

- Manual broker positions and allocation reconciliation.

- Global stop-new-trades.

- Zone logger no-order guarantee.

- Backtest reproducibility and cost labelling.

- Paper-only configuration and secret redaction.

Do not report skipped or mocked tests as fully passed. State what each test double does and does not verify.

## 14. DOCUMENTATION

Maintain only necessary, concise documents:

- \`ARCHITECTURE_AUDIT.md\`

- \`IMPLEMENTATION_PLAN.md\`

- \`ARCHITECTURE.md\`

- \`BOT_SPECIFICATIONS.md\`

- \`RISK_MANAGEMENT.md\`

- \`BROKER_ARCHITECTURE.md\`

- \`ORDER_LIFECYCLE.md\`

- \`DATABASE_SCHEMA.md\`

- \`BACKTESTING.md\`

- \`PAPER_TRADING.md\`

- \`SECURITY.md\`

- \`TESTING.md\`

- \`OPERATIONS.md\`

- \`MIGRATION_AND_ROLLBACK.md\`

- \`CHANGELOG.md\`

Do not create every document immediately. Add or update documents when the relevant milestone requires them.

## 15. DEFINITION OF DONE FOR THE FIVE-BOT PAPER BACKEND

The backend is ready only when:

- Five strategy modules are genuinely implemented or explicitly status-labelled.

- Each has independent risk configuration.

- All orders pass through central risk and the central order manager.

- The first broker adapter works in paper mode.

- Shared-account behavior is tested in a dedicated paper environment and approved.

- Orders are idempotent and broker state reconciles after restarts.

- Bot-level position attribution and P&L are traceable.

- Portfolio backtests include realistic cost assumptions.

- Critical failure cases are tested and fail safely.

- Logs, alerts, security boundaries, and operating procedures exist.

- Test evidence and remaining limitations are documented.

This does not prove profitability and does not authorize live trading.

## 16. FIRST ACTION

Start with Milestone 1 only. Do not code the full system now.

- Inspect the minimum necessary files.

- Do not open \`.env\`, touch \`~/alpaca_trading_bots/\*\*\`, run deploy scripts, or invoke \`launchctl\`.

- Create/update \`ARCHITECTURE_AUDIT.md\` and \`IMPLEMENTATION_PLAN.md\`.

- Run safe baseline tests if possible.

- Report verified findings, commands/results, risks, owner decisions, and the smallest recommended next milestone.

- Stop for review.

Final principle: Be economical with context and credits, reuse working code, preserve paper-only safeguards, verify before claiming, and build Esheon in small, testable increments.
