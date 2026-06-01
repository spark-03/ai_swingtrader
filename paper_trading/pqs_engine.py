import pandas as pd
import numpy as np


def zscore(series):
    std = float(series.std(ddof=0))

    if std == 0 or np.isnan(std):
        return pd.Series(
            np.zeros(len(series)),
            index=series.index
        )

    return (
        series - series.mean()
    ) / std


def calculate_pqs(df):

    work = df.copy()

    work["pqs"] = (

        0.40 *
        zscore(work["ema_spread"])

        +

        0.25 *
        zscore(work["trend_strength"])

        +

        0.20 *
        zscore(work["momentum_score"])

        +

        0.10 *
        zscore(
            -work["compression_score"]
        )

        +

        0.05 *
        zscore(
            -work["volatility_score"]
        )

    )

    return work
