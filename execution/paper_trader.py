import pandas as pd


# ====================================
# PAPER TRADER
# ====================================

class PaperTrader:

    def __init__(

        self,

        initial_balance=100000,

        risk_per_trade=0.1
    ):

        self.initial_balance = initial_balance

        self.balance = initial_balance

        self.risk_per_trade = risk_per_trade

        self.positions = {}

        self.trade_history = []

    # ====================================
    # OPEN POSITION
    # ====================================

    def open_position(

        self,

        symbol,

        signal,

        price,

        confidence
    ):

        if symbol in self.positions:

            return

        capital = (

            self.balance *

            self.risk_per_trade
        )

        quantity = capital / price

        self.positions[symbol] = {

            "signal": signal,

            "entry_price": price,

            "quantity": quantity,

            "confidence": confidence
        }

        print(

            f"\nOPENED {signal} | "

            f"{symbol} | "

            f"Price: {price:.2f}"
        )

    # ====================================
    # CLOSE POSITION
    # ====================================

    def close_position(

        self,

        symbol,

        exit_price
    ):

        if symbol not in self.positions:

            return

        position = self.positions[symbol]

        entry_price = position["entry_price"]

        quantity = position["quantity"]

        signal = position["signal"]

        # ====================================
        # LONG PNL
        # ====================================

        if signal == "BUY":

            pnl = (

                exit_price -

                entry_price

            ) * quantity

        # ====================================
        # SHORT PNL
        # ====================================

        else:

            pnl = (

                entry_price -

                exit_price

            ) * quantity

        self.balance += pnl

        # ====================================
        # SAVE HISTORY
        # ====================================

        self.trade_history.append({

            "symbol": symbol,

            "signal": signal,

            "entry_price": entry_price,

            "exit_price": exit_price,

            "quantity": quantity,

            "pnl": pnl,

            "balance": self.balance
        })

        print(

            f"\nCLOSED {symbol} | "

            f"PnL: {pnl:.2f}"
        )

        del self.positions[symbol]

    # ====================================
    # GET METRICS
    # ====================================

    def get_metrics(self):

        total_pnl = (

            self.balance -

            self.initial_balance
        )

        win_trades = len([

            t for t in self.trade_history

            if t["pnl"] > 0
        ])

        total_trades = len(

            self.trade_history
        )

        win_rate = 0

        if total_trades > 0:

            win_rate = (

                win_trades /

                total_trades
            ) * 100

        return {

            "balance": self.balance,

            "total_pnl": total_pnl,

            "total_trades": total_trades,

            "win_rate": win_rate
        }

    # ====================================
    # SAVE HISTORY
    # ====================================

    def save_history(

        self,

        file_name="paper_trades.csv"
    ):

        df = pd.DataFrame(

            self.trade_history
        )

        df.to_csv(

            file_name,

            index=False
        )

        print(

            f"\nSaved: {file_name}"
        )