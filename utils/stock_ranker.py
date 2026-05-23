import os

import pandas as pd
import numpy as np


# ====================================
# STOCK RANKER
# ====================================

class StockRanker:

    def __init__(self, data_folder):

        self.data_folder = data_folder

    # ====================================
    # SCORE SINGLE STOCK
    # ====================================

    def score_stock(self, file_path):

        try:

            df = pd.read_parquet(file_path)

            latest = df.iloc[-1]

            close = latest["close"]

            # ====================================
            # EMA TREND
            # ====================================

            ema_20 = latest["EMA_20"]

            ema_50 = latest["EMA_50"]

            ema_trend = (

                ema_20 - ema_50

            ) / ema_50

            # ====================================
            # SHORT MOMENTUM
            # ====================================

            momentum_10 = (

                close -

                df["close"].iloc[-10]

            ) / df["close"].iloc[-10]

            # ====================================
            # MEDIUM MOMENTUM
            # ====================================

            momentum_30 = (

                close -

                df["close"].iloc[-30]

            ) / df["close"].iloc[-30]

            # ====================================
            # LONG MOMENTUM
            # ====================================

            momentum_50 = (

                close -

                df["close"].iloc[-50]

            ) / df["close"].iloc[-50]

            # ====================================
            # ADX TREND STRENGTH
            # ====================================

            adx = latest["ADX"] / 100

            # ====================================
            # VOLATILITY
            # ====================================

            atr = latest["ATR"]

            volatility = atr / close

            # ====================================
            # RELATIVE VOLUME
            # ====================================

            recent_volume_avg = (

                df["volume"]

                .tail(20)

                .mean()
            )

            relative_volume = (

                latest["volume"] /

                recent_volume_avg
            )

            # ====================================
            # VWAP DISTANCE
            # ====================================

            vwap = latest["VWAP"]

            vwap_distance = (

                close -

                vwap

            ) / vwap

            # ====================================
            # VOLATILITY REGIME
            # ====================================

            recent_atr = (

                df["ATR"]

                .tail(20)

                .mean()
            )

            long_atr = (

                df["ATR"]

                .tail(100)

                .mean()
            )

            volatility_regime = (

                recent_atr /

                long_atr
            )

            # ====================================
            # RANGE EXPANSION
            # ====================================

            rolling_high = (

                df["high"]

                .tail(20)

                .max()
            )

            rolling_low = (

                df["low"]

                .tail(20)

                .min()
            )

            range_strength = (

                rolling_high -

                rolling_low

            ) / close

            # ====================================
            # FINAL SCORE
            # ====================================

            score = (

                ema_trend * 25 +

                momentum_10 * 15 +

                momentum_30 * 20 +

                momentum_50 * 20 +

                adx * 10 +

                volatility * 5 +

                relative_volume * 2 +

                vwap_distance * 2 +

                volatility_regime * 1 +

                range_strength * 5
            )

            return {

                "symbol": os.path.basename(file_path).replace("-EQ_5m.parquet", ""),

                "score": float(score),

                "ema_trend": float(ema_trend),

                "momentum_10": float(momentum_10),

                "momentum_30": float(momentum_30),

                "momentum_50": float(momentum_50),

                "adx": float(adx),

                "volatility": float(volatility),

                "relative_volume": float(relative_volume),

                "vwap_distance": float(vwap_distance),

                "volatility_regime": float(volatility_regime),

                "range_strength": float(range_strength)
            }

        except Exception as e:

            print(f"\nFAILED: {file_path}")

            print(e)

            return None

    # ====================================
    # RANK ALL STOCKS
    # ====================================

    def rank_stocks(self):

        files = [

            os.path.join(

                self.data_folder,

                f
            )

            for f in os.listdir(self.data_folder)

            if f.endswith(".parquet")
        ]

        results = []

        for file_path in files:

            result = self.score_stock(

                file_path
            )

            if result is not None:

                results.append(result)

        ranked_df = pd.DataFrame(results)

        ranked_df = ranked_df.sort_values(

            by="score",

            ascending=False
        )

        ranked_df.reset_index(

            drop=True,

            inplace=True
        )

        return ranked_df