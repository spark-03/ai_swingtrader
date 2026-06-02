from __future__ import annotations

import argparse
import subprocess
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, time as datetime_time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from paper_trading.logging_config import get_system_logger
from paper_trading.metrics import load_metrics, save_metrics
from paper_trading.state_manager import StateManager


IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = datetime_time(9, 15)
MARKET_CLOSE = datetime_time(15, 30)
RUN_TIMES = {"09:15", "11:15", "13:15", "15:15"}
POLL_INTERVAL_SECONDS = 30
LIVE_2H_DIR = Path("data/live/2h")
PORTFOLIO_COMMAND = ["python", "-m", "paper_trading.run_live_portfolio"]


@dataclass(frozen=True)
class CandleAvailability:
    latest_timestamp: pd.Timestamp | None
    scanned_files: int
    readable_files: int

    @property
    def slot_key(self) -> str | None:
        if self.latest_timestamp is None:
            return None
        return self.latest_timestamp.strftime("%Y-%m-%d %H")


def get_current_time() -> datetime:
    return datetime.now(IST)


def format_slot(current_time: datetime) -> str:
    return current_time.strftime("%Y-%m-%d %H:%M")


def is_market_day(current_time: datetime) -> bool:
    return current_time.weekday() < 5


def is_market_hours(current_time: datetime) -> bool:
    return MARKET_OPEN <= current_time.time() <= MARKET_CLOSE


def is_processing_slot(current_time: datetime, allow_late_minutes: int = 0) -> bool:
    if current_time.strftime("%H:%M") in RUN_TIMES:
        return True

    if allow_late_minutes <= 0:
        return False

    for run_time in RUN_TIMES:
        hour, minute = [int(part) for part in run_time.split(":")]
        boundary = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if boundary <= current_time <= boundary + timedelta(minutes=allow_late_minutes):
            return True
    return False


def normalize_candle_timestamp(value: object) -> pd.Timestamp | None:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return None

    timestamp = pd.Timestamp(timestamp)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(IST)
    else:
        timestamp = timestamp.tz_convert(IST)
    return timestamp


def get_latest_available_candle_timestamp(data_dir: Path = LIVE_2H_DIR) -> CandleAvailability:
    latest: pd.Timestamp | None = None
    scanned_files = 0
    readable_files = 0

    if not data_dir.exists():
        return CandleAvailability(None, scanned_files, readable_files)

    for parquet_file in data_dir.glob("*.parquet"):
        scanned_files += 1
        try:
            df = pd.read_parquet(parquet_file, columns=["datetime"])
        except Exception:
            continue

        if df.empty or "datetime" not in df.columns:
            continue

        timestamps = pd.to_datetime(df["datetime"], errors="coerce").dropna()
        if timestamps.empty:
            continue

        candidate = normalize_candle_timestamp(timestamps.max())
        if candidate is None:
            continue

        readable_files += 1
        if latest is None or candidate > latest:
            latest = candidate

    return CandleAvailability(latest, scanned_files, readable_files)


def has_new_candle(state_manager: StateManager, availability: CandleAvailability) -> bool:
    current_candle_slot = availability.slot_key
    if current_candle_slot is None:
        return False

    last_processed_slot = state_manager.load_last_processed_slot()
    return current_candle_slot != last_processed_slot


def run_cycle(slot: str | None = None) -> None:
    command = [*PORTFOLIO_COMMAND]
    if slot:
        command.extend(["--slot", slot])
    subprocess.run(command, check=True)


def process_scheduler_tick(
    *,
    state_manager: StateManager | None = None,
    data_dir: Path = LIVE_2H_DIR,
    allow_late_minutes: int = 0,
) -> None:
    logger = get_system_logger("paper_trading.scheduler")
    state_manager = state_manager or StateManager()
    current_time = get_current_time()
    current_slot = format_slot(current_time)

    print(f"Current time: {current_time.isoformat(timespec='seconds')}", flush=True)
    logger.info("Current time: %s", current_time.isoformat(timespec="seconds"))

    if not is_market_day(current_time):
        print(f"Current slot: {current_slot}", flush=True)
        print("Weekend detected", flush=True)
        logger.info("Weekend detected slot=%s", current_slot)
        return

    if not is_market_hours(current_time):
        print(f"Current slot: {current_slot}", flush=True)
        print("Outside market hours", flush=True)
        logger.info("Outside market hours slot=%s", current_slot)
        return

    if not is_processing_slot(current_time, allow_late_minutes=allow_late_minutes):
        print("Current slot: None", flush=True)
        logger.info("No completed 2H boundary at slot=%s", current_slot)
        return

    print(f"Current slot: {current_slot}", flush=True)
    logger.info("Checking candle availability slot=%s", current_slot)

    availability = get_latest_available_candle_timestamp(data_dir)
    logger.info(
        "Latest available 2H candle=%s scanned_files=%s readable_files=%s",
        availability.latest_timestamp,
        availability.scanned_files,
        availability.readable_files,
    )

    current_candle_slot = availability.slot_key
    if current_candle_slot is None:
        print("No new candle exists", flush=True)
        logger.warning("No readable 2H candle data found")
        return

    last_processed_slot = state_manager.load_last_processed_slot()
    if current_candle_slot == last_processed_slot:
        print("Skipping duplicate slot", flush=True)
        logger.info("Skipping duplicate slot candle_slot=%s", current_candle_slot)
        return

    print("Running cycle", flush=True)
    logger.info(
        "Cycle start current_slot=%s candle_slot=%s last_processed_slot=%s",
        current_slot,
        current_candle_slot,
        last_processed_slot,
    )

    started_at = time.monotonic()
    try:
        run_cycle(current_candle_slot)
        duration = time.monotonic() - started_at
        state_manager.save_last_processed_slot(current_candle_slot)
        metrics = load_metrics()
        metrics["last_processed_slot"] = current_candle_slot
        save_metrics(metrics)
        logger.info("Cycle completion candle_slot=%s duration_seconds=%.3f", current_candle_slot, duration)
    except Exception:
        logger.exception("Trading cycle failed; last_processed_slot was not updated")
        traceback.print_exc()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 2H market scheduler.")
    parser.add_argument("--once", action="store_true", help="Run one scheduler tick and exit.")
    parser.add_argument(
        "--allow-late-minutes",
        type=int,
        default=0,
        help="Grace window for delayed cloud schedulers. Default is strict slot matching.",
    )
    args = parser.parse_args()

    logger = get_system_logger("paper_trading.scheduler")
    print("Scheduler started", flush=True)
    logger.info("Scheduler started")

    if args.once:
        try:
            process_scheduler_tick(allow_late_minutes=args.allow_late_minutes)
        except Exception:
            logger.exception("Scheduler tick failed")
            traceback.print_exc()
        return

    while True:
        try:
            process_scheduler_tick()
        except Exception:
            logger.exception("Scheduler tick failed")
            traceback.print_exc()

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
