from pathlib import Path


UNIVERSE_FILE = Path(
    "configs/nifty500_symbols.txt"
)


def load_universe():

    if not UNIVERSE_FILE.exists():

        raise FileNotFoundError(
            f"Universe file not found: {UNIVERSE_FILE}"
        )

    with open(
        UNIVERSE_FILE,
        "r",
        encoding="utf-8-sig"
    ) as f:

        symbols = [

            line.strip()

            for line in f

            if line.strip()

        ]

    return sorted(
        list(
            set(symbols)
        )
    )
