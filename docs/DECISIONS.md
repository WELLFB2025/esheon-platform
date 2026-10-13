# Owner decisions

Newest first. Each entry: date · decision · consequences for the build.

## 2026-10-13 · One shared account for all bots

All Esheon bots trade through **one** Alpaca account — one paper account, and later one live account.

What this requires (built in Milestones 3–6, migrated only after Milestone 6 tests pass):

- **Central risk owns the account.** Buying power, open risk, cash reserve and daily loss are account-wide, with per-bot allocations and atomic reservations so simultaneous signals can't overspend.
- **Day-trade budget is shared.** Under $25,000 equity in a margin account, all bots together get 3 day trades per 5 business days. Central risk counts and allocates them. Practical options: fund the account above $25,000, or limit intraday bots.
  - Paper: Alpaca lets you reset a paper account's balance; set it at or above $25,000 if you want the paper test to reflect an unrestricted account.
- **Attribution by order ID.** Every order carries `ESHEON-<BOT>-…`; positions and P&L are attributed per bot even though the broker nets positions by symbol.
- **Same-symbol conflicts.** Two bots in the same symbol share one broker position. Opposite-direction signals on one symbol are blocked unless a tested netting policy exists.
- **Migration is a project, not a config edit.** Today each bot has its own account, keys, prefix and state, and the deploy scripts refuse a shared API key. Milestone 6 tests the shared account on a dedicated paper account, writes `docs/MIGRATION_AND_ROLLBACK.md`, and the owner migrates bots one at a time.
- **Live:** one live account too, behind the gate in `docs/LIVE_TRADING.md`; `ESHEON_LIVE_BOTS` decides which bots may use it.

## 2026-10-13 · Paper by default, gated live

Esheon supports paper and live trading. Paper is the default; live only through `esheon.safety.resolve_trading_mode()`. See `docs/LIVE_TRADING.md`.

## 2026-10-12 · Own repo

Esheon lives in its own repo (`WellFb2025/esheon-platform`), separate from the bot repos.
