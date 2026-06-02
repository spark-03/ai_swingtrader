import type { DashboardData } from "../types/trading";

export const mockDashboardData: DashboardData = {
  snapshot: {
    timestamp: new Date().toISOString(),
    cash: 384000,
    equity: 1048600,
    positions: 3,
    daily_pnl: 8600
  },
  positions: [
    {
      symbol: "RELIANCE-EQ",
      entry_timestamp: "2026-06-01T09:15:00Z",
      entry_price: 1420,
      quantity: 180,
      slot_capital: 255600,
      current_price: 1458,
      pqs: 2.41,
      status: "OPEN"
    },
    {
      symbol: "TCS-EQ",
      entry_timestamp: "2026-05-31T11:15:00Z",
      entry_price: 3860,
      quantity: 62,
      slot_capital: 239320,
      current_price: 3828,
      pqs: 1.87,
      status: "OPEN"
    }
  ],
  trades: [
    {
      timestamp: "2026-06-01T09:16:00Z",
      symbol: "RELIANCE-EQ",
      action: "BUY",
      price: 1420,
      quantity: 180,
      reason: "top_pqs_candidate",
      rl_decision: "HOLD"
    },
    {
      timestamp: "2026-06-01T11:17:00Z",
      symbol: "INFY-EQ",
      action: "SELL",
      price: 1510,
      quantity: 120,
      reason: "rl_exit",
      rl_decision: "SELL"
    }
  ],
  rotations: [
    {
      timestamp: "2026-06-01T13:18:00Z",
      old_symbol: "INFY-EQ",
      new_symbol: "TCS-EQ",
      old_tqs: 1.12,
      new_tqs: 1.87
    }
  ],
  rankings: [
    { timestamp: "2026-06-01T13:15:00Z", rank: 1, symbol: "RELIANCE-EQ", pqs: 2.41, last_price: 1458 },
    { timestamp: "2026-06-01T13:15:00Z", rank: 2, symbol: "TCS-EQ", pqs: 1.87, last_price: 3828 },
    { timestamp: "2026-06-01T13:15:00Z", rank: 3, symbol: "HDFCBANK-EQ", pqs: 1.72, last_price: 1684 }
  ],
  metrics: {
    cycle_count: 42,
    trades_executed: 19,
    exits_triggered: 6,
    rotations_triggered: 4,
    active_positions: 3,
    portfolio_value: 1048600,
    last_processed_slot: "2026-06-01 13",
    last_cycle_completed_at: "2026-06-01T07:48:11Z",
    last_error: null
  },
  logs: [
    "2026-06-01T13:15:00+0530 INFO Scheduler started",
    "2026-06-01T13:15:05+0530 INFO Cycle start candle_slot=2026-06-01 13",
    "2026-06-01T13:17:11+0530 INFO Cycle completion duration_seconds=126.4"
  ]
};
