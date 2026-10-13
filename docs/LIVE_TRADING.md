# Live trading

Esheon trades **paper by default**. Live trading is possible only through one gate,
`esheon.safety.resolve_trading_mode()`, and only when every condition below holds.
Anything missing, conflicting or unreadable is a refusal — it never falls through to live.

> Research to date shows no strategy with an edge after realistic costs. Live trading
> risks real money. Nothing in this repo is financial advice.

## The gate (all required, checked every time a bot starts or reconnects)

| # | Condition | Set by |
|---|---|---|
| 1 | `ESHEON_MODE=live` **and** `ALPACA_PAPER=false` (either alone refuses) | Owner, in the bot's `.env` |
| 2 | Separate live keys `ALPACA_LIVE_API_KEY` / `ALPACA_LIVE_SECRET_KEY`, different from the paper keys | Owner |
| 3 | Bot listed in `ESHEON_LIVE_BOTS` (comma-separated bot IDs) | Owner |
| 4 | Limits set and within hard ceilings: `ESHEON_LIVE_MAX_ORDER_NOTIONAL` (≤ $1,000), `ESHEON_LIVE_MAX_DAILY_LOSS` (≤ $250), `ESHEON_LIVE_MAX_OPEN_POSITIONS` (≤ 5) | Owner |
| 5 | Armed for **today's** market date: `~/.esheon/live_arm` contains exactly `LIVE YYYY-MM-DD` (New York date). Expires at midnight ET. | Owner, by hand, each trading day |
| 6 | Kill switch off: `~/.esheon/KILL` does not exist | Owner |
| 7 | If a base URL is set, it is the live endpoint | Owner |

Hard ceilings live in `safety.py`. Raising them is a reviewed code change, not a config change.

### Owner commands (run by you, never by Claude Code)

```bash
# Arm live trading for today only
mkdir -p ~/.esheon && echo "LIVE $(TZ=America/New_York date +%F)" > ~/.esheon/live_arm

# Kill switch: block all new live orders immediately
touch ~/.esheon/KILL

# Release kill switch / disarm
rm ~/.esheon/KILL
rm ~/.esheon/live_arm
```

## Promotion: when a strategy may go live

A bot is added to `ESHEON_LIVE_BOTS` only when all of these are written down in
`docs/BOT_SPECIFICATIONS.md` for that bot and signed off by the owner:

1. Pre-registered spec, backtest passed on development and held-out periods after MODERATE **and** ADVERSE costs.
2. Paper-traded through Esheon's full order path for **≥ 20 sessions and ≥ 30 trades**, net positive after fees.
3. Paper records reconcile with the broker with zero unexplained differences.
4. Milestones 3–7 complete (central risk, order manager, reconciliation, kill switch, alerts).
5. Starting live limits chosen and recorded (start at the smallest useful size).

Demotion is automatic in spirit: if live results breach the daily loss limit 3 times in
20 sessions, or drift far from paper results, remove the bot from `ESHEON_LIVE_BOTS` and review.

## Real-account rules the gate does not enforce for you

- **Pattern day trader rule:** margin accounts under $25,000 get 3 day trades per 5 business days. Central risk must count them per live account.
- **Options approval:** 0DTE options need the right options level on the live account.
- **Cash accounts** avoid the PDT rule but must wait for settlement before reusing cash.
- Keep paper and live accounts, keys, state files and P&L completely separate.

## Plan

- **Milestone 2:** replace the 0DTE bot's "ALPACA_PAPER=false means live" path with this gate (left off).
- **Milestones 3–7:** central risk, order manager, reconciliation, alerts, kill switch — prerequisites for live.
- **Milestone 8:** live adapter wiring, LIVE_FILL records, live reconciliation, staged rollout of one bot at minimum size.
