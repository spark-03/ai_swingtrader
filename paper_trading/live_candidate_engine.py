from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from paper_trading.common import (
    add_state_features,
    ensure_parent,
)

from paper_trading.universe import (
    load_universe
)


def zscore(series: pd.Series) -> pd.Series:

    std = float(series.std(ddof=0))

    if std == 0 or np.isnan(std):

        return pd.Series(
            np.zeros(len(series)),
            index=series.index
        )

    return (
        series - float(series.mean())
    ) / std


@dataclass
class CandidateEngineConfig:

    hourly_data_dir: Path = Path(
        "data/live/2h"
    )

    output_file: Path = Path(
        "logs/live_candidates.csv"
    )


class LiveCandidateEngine:

    def __init__(
        self,
        config: CandidateEngineConfig | None = None
    ) -> None:

        self.config = (
            config
            or
            CandidateEngineConfig()
        )

    def generate_candidates(self) -> pd.DataFrame:

        universe = load_universe()

        print(
            f"Universe Size: {len(universe)}"
        )

        files = []

        for symbol in universe:

            file_path = (
                self.config.hourly_data_dir
                /
                f"{symbol}.parquet"
            )

            if file_path.exists():

                files.append(
                    file_path
                )

        print(
            f"Files Found: {len(files)}"
        )

        records = []

        print(
            f"Scanning {len(files)} symbols..."
        )

        for file_path in files:

            symbol = file_path.stem

            try:

                df = pd.read_parquet(
                    file_path
                )

                if len(df) < 20:
                    continue

                if "datetime" in df.columns:

                    df["datetime"] = (
                        pd.to_datetime(
                            df["datetime"]
                        )
                    )

                feats = add_state_features(
                    df
                )

            except Exception as e:

                print(
                    f"Skipping {symbol}: {e}"
                )

                continue

            if feats.empty:
                continue

            latest = feats.iloc[-1]

            records.append({

                "timestamp":
                    latest["datetime"],

                "symbol":
                    symbol,

                "ema_spread":
                    float(
                        latest["ema_spread"]
                    ),

                "compression_score":
                    float(
                        latest["compression_score"]
                    ),

                "volatility_score":
                    float(
                        latest["volatility_score"]
                    ),

                "momentum_score":
                    float(
                        latest["momentum_score"]
                    ),

                "trend_strength":
                    float(
                        latest["trend_strength"]
                    ),

                "last_price":
                    float(
                        latest["close"]
                    )

            })

        df = pd.DataFrame(records)

        if df.empty:

            ensure_parent(
                self.config.output_file
            )

            df.to_csv(
                self.config.output_file,
                index=False
            )

            return df

        df["pqs"] = (

            0.40 *
            zscore(df["ema_spread"])

            +

            0.25 *
            zscore(df["trend_strength"])

            +

            0.20 *
            zscore(df["momentum_score"])

            +

            0.10 *
            zscore(
                -df["compression_score"]
            )

            +

            0.05 *
            zscore(
                -df["volatility_score"]
            )

        )

        df = (
            df
            .sort_values(
                "pqs",
                ascending=False
            )
            .reset_index(
                drop=True
            )
        )

        df["rank"] = (
            np.arange(
                len(df)
            ) + 1
        )

        ordered_cols = [

            "timestamp",
            "rank",
            "symbol",
            "pqs",
            "ema_spread",
            "compression_score",
            "volatility_score",
            "momentum_score",
            "trend_strength",
            "last_price"

        ]

        df = df[
            ordered_cols
        ]

        ensure_parent(
            self.config.output_file
        )

        df.to_csv(
            self.config.output_file,
            index=False
        )

        snapshot_dir = Path(
            "logs/pqs_rankings"
        )

        snapshot_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        snapshot_name = (
            pd.Timestamp.now()
            .strftime(
                "%Y_%m_%d_%H_%M"
            )
            + ".csv"
        )

        snapshot_path = (
            snapshot_dir
            /
            snapshot_name
        )

        df.to_csv(
            snapshot_path,
            index=False
        )

        print(
            f"\nGenerated candidates: {len(df)}"
        )

        print(
            f"Snapshot Saved: {snapshot_path}"
        )

        print(
            "\n=== TOP 20 PQS STOCKS ===\n"
        )

        print(

            df[
                [
                    "rank",
                    "symbol",
                    "pqs"
                ]
            ]
            .head(20)
            .to_string(
                index=False
            )

        )

        print(
            f"\nSaved: {self.config.output_file}"
        )

        return df


def main():

    engine = (
        LiveCandidateEngine()
    )

    engine.generate_candidates()


if __name__ == "__main__":
    main()
