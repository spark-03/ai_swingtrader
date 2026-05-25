import csv
import os
from datetime import datetime


# ======================================================
# THESIS LIFECYCLE LOGGER
# ======================================================
#
# PURPOSE:
# ----------------------------------
# Record how trades evolve candle-by-candle.
#
# This creates a behavioral dataset for:
#
# - thesis deterioration analysis
# - lifecycle intelligence
# - exit optimization
# - regime-aware exits
# - RL reward shaping
# - adaptive trade management
#
# ======================================================


LOG_PATH = "logs/thesis_lifecycle.csv"


# ======================================================
# SAFE VALUE
# ======================================================

def safe_value(x, default=0):

    try:

        if x is None:

            return default

        return float(x)

    except Exception:

        return default


# ======================================================
# CREATE FILE IF NEEDED
# ======================================================

def ensure_log_file():

    os.makedirs(
        "logs",
        exist_ok=True
    )

    if not os.path.exists(LOG_PATH):

        with open(
            LOG_PATH,
            mode="w",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([

                # CORE INFO
                "timestamp",
                "symbol",
                "side",

                # TRADE LIFECYCLE
                "holding_time",

                # PRICE
                "close",

                # THESIS
                "thesis_score",
                "peak_thesis_score",
                "thesis_decay",

                # TRADE QUALITY
                "unrealized_r",
                "pnl",

                # CONTEXT
                "market_regime",

                # EXIT INFO
                "exit_reason"
            ])


# ======================================================
# MAIN LOGGER
# ======================================================

def log_thesis_lifecycle(

    symbol,
    side,
    holding_time,
    close,

    thesis_score,
    peak_thesis_score,

    unrealized_r,

    market_regime,

    entry_price,

    exit_reason=None
):

    ensure_log_file()

    # ==================================================
    # THESIS DECAY
    # ==================================================

    if peak_thesis_score > 0:

        thesis_decay = (

            thesis_score
            / peak_thesis_score
        )

    else:

        thesis_decay = 0

    # ==================================================
    # PNL
    # ==================================================

    if side == "BUY":

        pnl = close - entry_price

    else:

        pnl = entry_price - close

    # ==================================================
    # WRITE ROW
    # ==================================================

    with open(
        LOG_PATH,
        mode="a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([

            # TIMESTAMP
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            # CORE
            symbol,
            side,

            # LIFECYCLE
            holding_time,

            # PRICE
            round(
                safe_value(close),
                2
            ),

            # THESIS
            safe_value(thesis_score),

            safe_value(
                peak_thesis_score
            ),

            round(
                safe_value(thesis_decay),
                3
            ),

            # TRADE QUALITY
            round(
                safe_value(unrealized_r),
                3
            ),

            round(
                safe_value(pnl),
                2
            ),

            # CONTEXT
            market_regime,

            # EXIT
            exit_reason
        ])


# ======================================================
# OPTIONAL QUICK SUMMARY
# ======================================================

def print_logger_status():

    if os.path.exists(LOG_PATH):

        print(
            f"\nLifecycle logs active:"
            f"\n{LOG_PATH}"
        )

    else:

        print(
            "\nLifecycle logger not initialized."
        )