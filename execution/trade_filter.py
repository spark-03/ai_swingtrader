import pandas as pd


# ====================================
# TRADE FILTER
# ====================================

class TradeFilter:

    def __init__(

        self,

        min_confidence=0.15,

        min_market_score=5,

        min_q_gap=0.03
    ):

        self.min_confidence = min_confidence

        self.min_market_score = min_market_score

        self.min_q_gap = min_q_gap

    # ====================================
    # FILTER TRADES
    # ====================================

    def filter_trades(self, df):

        filtered = []

        for _, row in df.iterrows():

            signal = row["signal"]

            confidence = row["confidence"]

            market_score = row["market_score"]

            hold_q = row["hold_q"]

            buy_q = row["buy_q"]

            sell_q = row["sell_q"]

            # ====================================
            # Q-VALUE SEPARATION
            # ====================================

            sorted_q = sorted(

                [

                    hold_q,

                    buy_q,

                    sell_q
                ],

                reverse=True
            )

            q_gap = (

                sorted_q[0] -

                sorted_q[1]
            )

            # ====================================
            # SKIP HOLD SIGNALS
            # ====================================

            if signal == "HOLD":

                continue

            # ====================================
            # CONFIDENCE FILTER
            # ====================================

            if confidence < self.min_confidence:

                continue

            # ====================================
            # MARKET QUALITY FILTER
            # ====================================

            if market_score < self.min_market_score:

                continue

            # ====================================
            # DECISIVENESS FILTER
            # ====================================

            if q_gap < self.min_q_gap:

                continue

            row["q_gap"] = q_gap

            filtered.append(row)

        # ====================================
        # FINAL DF
        # ====================================

        filtered_df = pd.DataFrame(filtered)

        if len(filtered_df) == 0:

            return filtered_df

        filtered_df = filtered_df.sort_values(

            by=[

                "confidence",

                "market_score",

                "q_gap"
            ],

            ascending=False
        )

        return filtered_df