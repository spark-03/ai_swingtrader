from pathlib import Path

import pandas as pd


# ======================================================
# CONFIG
# ======================================================

INPUT_FILE = Path(
    "data/features/5min/RELIANCE-EQ.parquet"
)

OUTPUT_FILE = Path(
    "logs/RELIANCE_1YEAR_INDICATORS.xlsx"
)


# ======================================================
# LOAD DATA
# ======================================================

df = pd.read_parquet(INPUT_FILE)

print("\nLoaded rows:", len(df))

# ======================================================
# SORT BY TIME
# ======================================================

if "datetime" in df.columns:

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        errors="coerce"
    )

    df = df.sort_values("datetime")

# ======================================================
# KEEP LAST 1 YEAR
# ======================================================

if "datetime" in df.columns:

    latest_date = df["datetime"].max()

    one_year_ago = (
        latest_date
        - pd.Timedelta(days=365)
    )

    df = df[
        df["datetime"] >= one_year_ago
    ]

# ======================================================
# REMOVE TIMEZONES
# ======================================================

for col in df.columns:

    if pd.api.types.is_datetime64_any_dtype(df[col]):

        try:

            df[col] = (
                df[col]
                .dt.tz_localize(None)
            )

        except Exception:

            pass

# ======================================================
# EMPTY CHECK
# ======================================================

if df.empty:

    print("\nERROR: dataframe is empty.")

else:

    # ==================================================
    # CREATE OUTPUT FOLDER
    # ==================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ==================================================
    # EXPORT TO EXCEL
    # ==================================================

    df.to_excel(

        OUTPUT_FILE,

        index=False,

        sheet_name="Indicators",

        engine="openpyxl"
    )

    # ==================================================
    # SUCCESS MESSAGE
    # ==================================================

    print("\nExcel exported successfully:")

    print(OUTPUT_FILE)

    print("\nColumns exported:\n")

    for col in df.columns:

        print("-", col)