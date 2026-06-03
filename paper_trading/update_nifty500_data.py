from __future__ import annotations
from paper_trading.supabase_logger import SupabaseLogger
import concurrent.futures as cf
import os
import time
from datetime import datetime
from math import ceil
from pathlib import Path
from threading import local
from typing import Any

import pandas as pd

from paper_trading.data_utils import (
    IST,
    LIVE_2H_DIR,
    ThreadSafeCounter,
    UpdateResult,
    append_update_log,
    build_2h_bars_from_hourly,
    build_symbol_token_map,
    create_smart_session,
    fetch_recent_hourly_data,
    filter_completed_2h_bars,
    load_credentials_from_env,
    load_instrument_master,
    load_nifty500_universe,
    merge_with_existing_and_trim,
    save_symbol_2h_parquet,
)
from paper_trading.data_validator import validate_parquet_file
from paper_trading.logging_config import get_system_logger


THREAD_CTX = local()
LOGGER = get_system_logger("paper_trading.data_update")
BATCH_SIZE = 10
BATCH_SLEEP_SECONDS = 10
RETRY_BACKOFF_SECONDS = (5, 10, 20)
RETRYABLE_ERROR_MARKERS = (
    "429",
    "rate limit",
    "timeout",
    "timed out",
    "too many requests",
    "temporarily unavailable",
)


def _is_retryable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in RETRYABLE_ERROR_MARKERS)


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _resolve_token(
    symbol: str,
    token_map: dict[str, str],
    smart: Any,
) -> str | None:
    if symbol in token_map:
        return token_map[symbol]

    # Fallback: normalize formats and search API.
    base = symbol.replace("-EQ", "")
    for alt in (base, f"{base}-EQ"):
        if alt in token_map:
            return token_map[alt]

    try:
        res = smart.searchScrip("NSE", base)
        if isinstance(res, dict) and res.get("status") is False:
            message = " ".join(
                str(res.get(k, ""))
                for k in ("message", "error", "errorcode")
                if res.get(k)
            )
            if any(marker in message.lower() for marker in RETRYABLE_ERROR_MARKERS):
                raise RuntimeError(f"Angel API retryable error: {message or res}")
        rows = res.get("data", []) if isinstance(res, dict) else []
        if rows:
            return str(rows[0].get("symboltoken", "")).strip() or None
    except Exception as exc:
        if _is_retryable_error(exc):
            raise
        return None
    return None


def _get_thread_smart(creds) -> Any:
    smart = getattr(THREAD_CTX, "smart", None)
    if smart is None:
        smart = create_smart_session(creds)
        THREAD_CTX.smart = smart
    return smart


def _process_symbol_once(
    symbol: str,
    token_map: dict[str, str],
    creds,
) -> UpdateResult:
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    smart = _get_thread_smart(creds)
    token = _resolve_token(symbol, token_map, smart)
    if not token:
        return UpdateResult(now, symbol, 0, 0.0, "FAILED", "Token not found")

    out_file = LIVE_2H_DIR / f"{symbol}.parquet"
    hourly_df = fetch_recent_hourly_data(
        smart=smart,
        symbol_token=token,
        existing_2h_file=out_file,
        days_bootstrap=45,
        days_incremental=7,
        pause_sec=0.02,
    )
    bars_2h = build_2h_bars_from_hourly(hourly_df)
    bars_2h = filter_completed_2h_bars(bars_2h)
    merged = merge_with_existing_and_trim(out_file, bars_2h, keep_last=60)

    if merged.empty:
        return UpdateResult(now, symbol, 0, 0.0, "FAILED", "No completed 2H bars")

    if merged["datetime"].isna().any():
        return UpdateResult(now, symbol, 0, 0.0, "FAILED", "Null timestamps after merge")
    if merged["datetime"].duplicated().any():
        return UpdateResult(now, symbol, 0, 0.0, "FAILED", "Duplicate timestamps after merge")
    if not merged["datetime"].is_monotonic_increasing:
        return UpdateResult(now, symbol, 0, 0.0, "FAILED", "Timestamps not ascending after merge")
    if len(merged) < 30:
        return UpdateResult(now, symbol, 0, 0.0, "FAILED", "Insufficient rolling 2H window")

    saved_file = save_symbol_2h_parquet(symbol, merged)

    supabase = SupabaseLogger()
    supabase.upsert_market_candles(
    symbol,
    merged,
)

    validation = validate_parquet_file(saved_file)
    if validation.status == "FAIL":
        return UpdateResult(now, symbol, 0, 0.0, "FAILED", validation.error)

    latest_close = float(merged["close"].iloc[-1])
    LOGGER.info("Data update saved symbol=%s bars=%s latest_close=%s", symbol, len(merged), latest_close)
    return UpdateResult(now, symbol, int(len(merged)), latest_close, "SUCCESS", "")


def _process_symbol(
    symbol: str,
    token_map: dict[str, str],
    creds,
) -> UpdateResult:
    last_error = ""
    for attempt in range(len(RETRY_BACKOFF_SECONDS) + 1):
        now = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
        try:
            return _process_symbol_once(symbol, token_map, creds)
        except Exception as exc:
            last_error = str(exc)[:500]
            if not _is_retryable_error(exc) or attempt == len(RETRY_BACKOFF_SECONDS):
                return UpdateResult(now, symbol, 0, 0.0, "FAILED", last_error)

            wait_sec = RETRY_BACKOFF_SECONDS[attempt]
            print(
                f"{symbol}: retry {attempt + 1}/3 after {wait_sec}s ({last_error})",
                flush=True,
            )
            time.sleep(wait_sec)

    return UpdateResult(
        datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        symbol,
        0,
        0.0,
        "FAILED",
        last_error,
    )


def run_update() -> None:

    print("Loading credentials...", flush=True)
    creds = load_credentials_from_env()

    print("Loading universe...", flush=True)
    universe = load_nifty500_universe()

    print(
        f"Symbols to update incrementally: {len(universe)}"
    )

    print("Loading token cache...", flush=True)

    token_cache_file = Path(
        "data/cache/nifty500_tokens.csv"
    )

    if token_cache_file.exists():

        token_df = pd.read_csv(
            token_cache_file
        )

        token_map = dict(
            zip(
                token_df["symbol"],
                token_df["token"]
            )
        )

        print(
            f"Loaded {len(token_map)} cached tokens",
            flush=True
        )

    else:

        print(
            "Token cache not found",
            flush=True
        )

        print(
            "Downloading instrument master once...",
            flush=True
        )

        token_df = pd.read_csv(
          "data/nifty500_tokens.csv"
)

        token_map = dict(
        zip(
        token_df["symbol"],
        token_df["token"]
    )
)
        

        Path(
            "data/cache"
        ).mkdir(
            parents=True,
            exist_ok=True
        )

        pd.DataFrame(
            {
                "symbol": list(token_map.keys()),
                "token": list(token_map.values())
            }
        ).to_csv(
            token_cache_file,
            index=False
        )

        print(
            f"Saved token cache with {len(token_map)} symbols",
            flush=True
        )

    max_workers = int(
        os.getenv(
            "DATA_UPDATE_WORKERS",
            "3"
        )
    )

    max_workers = max(
        2,
        min(
            max_workers,
            BATCH_SIZE
        )
    )

    start_time = time.monotonic()

    print("\nUniverse Loaded")
    print(f"Total Symbols: {len(universe)}")
    print(f"Token Map Size: {len(token_map)}")
    print(f"Workers: {max_workers}")
    print(f"Batch Size: {BATCH_SIZE}")

    results = []

    counter = ThreadSafeCounter()

    batches = _chunks(
        universe,
        BATCH_SIZE
    )

    total_batches = (
        ceil(
            len(universe)
            / BATCH_SIZE
        )
        if universe
        else 0
    )

    with cf.ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        for batch_no, batch in enumerate(
            batches,
            start=1
        ):

            print(
                f"\nStarting Batch {batch_no}/{total_batches}",
                flush=True
            )

            batch_results = []

            fut_map = {

                executor.submit(
                    _process_symbol,
                    sym,
                    token_map,
                    creds
                ): sym

                for sym in batch

            }

            for fut in cf.as_completed(
                fut_map
            ):

                sym = fut_map[fut]

                try:

                    res = fut.result()

                except Exception as exc:

                    res = UpdateResult(
                        timestamp=datetime.now(
                            IST
                        ).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        symbol=sym,
                        bars_saved=0,
                        latest_close=0.0,
                        status="FAILED",
                        error=str(exc)[:500]
                    )

                batch_results.append(
                    res
                )

                results.append(
                    res
                )

                if res.status == "SUCCESS":

                    counter.mark_success()

                else:

                    counter.mark_failed()

            batch_success = sum(

                1

                for r in batch_results

                if r.status == "SUCCESS"

            )

            batch_failed = (
                len(batch_results)
                - batch_success
            )

            print(
                f"Batch {batch_no} Complete"
            )

            print(
                f"Processed: {len(batch_results)}"
            )

            print(
                f"Success: {batch_success}"
            )

            print(
                f"Failed: {batch_failed}"
            )

            if batch_no < total_batches:

                print(
                    f"Sleeping {BATCH_SLEEP_SECONDS}s..."
                )

                time.sleep(
                    BATCH_SLEEP_SECONDS
                )

    append_update_log(
        results
    )

    runtime = (
        time.monotonic()
        - start_time
    )

    print("\n=== FINAL SUMMARY ===")

    print(
        f"Universe Size: {len(universe)}"
    )

    print(
        f"Successful: {counter.success}"
    )

    print(
        f"Failed: {counter.failed}"
    )

    print(
        f"Runtime: {runtime:.2f} seconds"
    )
    LOGGER.info(
        "Data update complete universe=%s successful=%s failed=%s runtime_seconds=%.2f",
        len(universe),
        counter.success,
        counter.failed,
        runtime,
    )

    print(
        "\nSaved:"
    )

    print(
        "data/live/2h"
    )

    print(
        "logs/data_update_log.csv"
    )

def main() -> None:
    run_update()


if __name__ == "__main__":
    main()
