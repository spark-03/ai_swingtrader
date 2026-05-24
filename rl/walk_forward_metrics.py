import pandas as pd
import os

RESULTS_CSV = os.path.join('rl', 'walk_forward_results.csv')
OUTPUT_TXT = os.path.join('rl', 'walk_forward_summary.txt')

if not os.path.exists(RESULTS_CSV):
    raise FileNotFoundError(f"Results file not found: {RESULTS_CSV}")

results = pd.read_csv(RESULTS_CSV)

total_symbols = results['symbol'].nunique()

top20 = results.nlargest(20, 'total_pnl')[['symbol', 'total_pnl']]

overall_pnl = results['total_pnl'].sum()
overall_trades = results['trade_count'].sum()
expectancy = overall_pnl / overall_trades if overall_trades != 0 else 0.0

overall_wins = results['wins'].sum()
overall_win_rate = (overall_wins / overall_trades) * 100 if overall_trades != 0 else 0.0

positive_pnl = results[results['total_pnl'] > 0]['total_pnl'].sum()
negative_pnl = -results[results['total_pnl'] < 0]['total_pnl'].sum()
profit_factor = positive_pnl / negative_pnl if negative_pnl != 0 else float('inf')

# Approximate max drawdown using cumulative PnL sorted descending
sorted_pnl = results.sort_values('total_pnl', ascending=False)['total_pnl'].cumsum()
roll_max = sorted_pnl.cummax()
max_drawdown = (roll_max - sorted_pnl).max()

avg_trade_duration = results['avg_hold_candles'].mean() if 'avg_hold_candles' in results.columns else None

total_skipped = results['skipped_signals'].sum() if 'skipped_signals' in results.columns else 0

best_symbol = results.loc[results['total_pnl'].idxmax()]
worst_symbol = results.loc[results['total_pnl'].idxmin()]

with open(OUTPUT_TXT, 'w') as f:
    f.write('=== Walk‑Forward Summary ===\n')
    f.write(f'Total symbols tested: {total_symbols}\n')
    f.write('\nTop 20 symbols by PnL:\n')
    f.write(top20.to_string(index=False))
    f.write('\n\n')
    f.write(f'Overall expectancy (PnL per trade): {expectancy:.4f}\n')
    f.write(f'Overall win rate: {overall_win_rate:.2f}%\n')
    f.write(f'Profit factor: {profit_factor:.4f}\n')
    f.write(f'Max drawdown (approx): {max_drawdown:.2f}\n')
    f.write(f'Average trade duration (candles): {avg_trade_duration if avg_trade_duration is not None else "N/A"}\n')
    f.write(f'Total skipped signals: {total_skipped}\n')
    f.write(f'Best symbol: {best_symbol["symbol"]} (PnL={best_symbol["total_pnl"]})\n')
    f.write(f'Worst symbol: {worst_symbol["symbol"]} (PnL={worst_symbol["total_pnl"]})\n')

print('Metrics written to', OUTPUT_TXT)
