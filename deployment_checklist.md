# AI Swing Trader Cloud Deployment Checklist

## Deployment Architecture

- Scheduler/runtime: GitHub Actions.
- State recovery: Supabase plus cached local state files.
- Dashboard: Netlify React application.
- Trading cycle command: `python -m paper_trading.market_scheduler --once`.
- Data update command: `python -m paper_trading.update_nifty500_data`.

## GitHub Repository Secrets

- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_KEY`: Supabase server-side key for GitHub Actions inserts.
- `ANGEL_CLIENT_CODE`: Angel One client code.
- `ANGEL_API_KEY`: Angel One API key.
- `ANGEL_PASSWORD`: Angel One PIN/password used by SmartAPI.
- `ANGEL_TOTP`: Angel One TOTP secret.

## GitHub Actions

- Workflow: `.github/workflows/trading_cycle.yml`.
- Schedule:
  - `03:45 UTC` = `09:15 IST`.
  - `05:45 UTC` = `11:15 IST`.
  - `07:45 UTC` = `13:15 IST`.
  - `09:45 UTC` = `15:15 IST`.
- Manual trigger: `workflow_dispatch`.
- State cache includes:
  - `current_portfolio.csv`
  - `logs/last_processed_slot.txt`
  - `logs/dashboard_metrics.json`
  - `logs/state_backups`
  - `data/live/2h`
- Artifacts include system logs, update logs, validation reports, metrics, and last processed slot.

## Netlify Setup

- Build command: `npm run build`.
- Publish directory: `dist`.
- Node version: `20`.
- Configuration file: `netlify.toml`.
- Required Netlify environment variables:
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY`

## Supabase Requirements

- REST API enabled.
- GitHub Actions key can insert into:
  - `paper_trades`
  - `portfolio_snapshots`
  - `rotation_log`
- Dashboard anon key can read:
  - `paper_trades`
  - `portfolio_snapshots`
  - `rotation_log`
  - `pqs_rankings` if enabled later.
- Recommended future tables/views:
  - `open_positions`
  - `system_metrics`
  - `scheduler_status`
  - `system_logs`

## Runtime Files

- `configs/nifty500_symbols.txt` must exist.
- `data/live/2h/*.parquet` must contain 2H candles with `datetime`, `open`, `high`, `low`, `close`, and `volume`.
- `models/rl_trade_exit_agent_tqs25.zip` must exist.
- `current_portfolio.csv` is automatically created if missing.
- `logs/last_processed_slot.txt` is updated only after a successful portfolio cycle.
- `logs/system.log` captures scheduler, cycle, portfolio, Supabase, data update, and validation events.
- `logs/dashboard_metrics.json` exposes dashboard-ready counters.

## Validation Commands

- Python compile: `python -m compileall paper_trading`
- Python tests: `python -m pytest test_market_scheduler.py test_state_manager.py test_health_check.py test_data_validator.py -q`
- Health check: `python -m paper_trading.health_check`
- Data validation: `python -m paper_trading.data_validator`
- Frontend build: `npm run build`

## Safety Rules

- Never update `logs/last_processed_slot.txt` before a successful portfolio cycle.
- Never run on incomplete candles.
- Incremental data update must append, deduplicate, validate timestamps, and preserve a rolling window.
- Live trading controls in the Netlify UI remain disabled until authenticated backend control APIs are explicitly built.
