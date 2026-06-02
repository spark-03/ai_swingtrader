from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import time
from pathlib import Path

import pandas as pd

from paper_trading.logging_config import get_system_logger


EXPECTED_TIMES = (time(9, 15), time(11, 15), time(13, 15))


@dataclass
class FileValidationResult:
    file: str
    status: str
    rows: int
    duplicate_candles: int
    missing_timestamps: int
    error: str


def _expected_timestamps(start: pd.Timestamp, end: pd.Timestamp) -> set[pd.Timestamp]:
    expected: set[pd.Timestamp] = set()
    start_day = start.normalize()
    end_day = end.normalize()

    for day in pd.date_range(start_day, end_day, freq="D"):
        if day.weekday() >= 5:
            continue
        for slot_time in EXPECTED_TIMES:
            expected.add(day + pd.Timedelta(hours=slot_time.hour, minutes=slot_time.minute))
    return expected


def validate_parquet_file(path: Path) -> FileValidationResult:
    if not path.exists() or path.stat().st_size == 0:
        return FileValidationResult(str(path), "FAIL", 0, 0, 0, "empty file")

    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        return FileValidationResult(str(path), "FAIL", 0, 0, 0, f"corrupted parquet: {exc}")

    if df.empty:
        return FileValidationResult(str(path), "FAIL", 0, 0, 0, "empty dataframe")

    if "datetime" not in df.columns:
        return FileValidationResult(str(path), "FAIL", len(df), 0, 0, "missing datetime column")

    timestamps = pd.to_datetime(df["datetime"], errors="coerce")
    invalid_timestamps = int(timestamps.isna().sum())
    clean_timestamps = timestamps.dropna()

    duplicate_candles = int(clean_timestamps.duplicated().sum())
    missing_timestamps = 0
    if not clean_timestamps.empty:
        normalized = set(pd.Timestamp(ts).tz_localize(None) for ts in clean_timestamps)
        expected = _expected_timestamps(clean_timestamps.min(), clean_timestamps.max())
        missing_timestamps = len(expected - normalized)

    errors = []
    if invalid_timestamps:
        errors.append(f"invalid datetime values={invalid_timestamps}")
    if duplicate_candles:
        errors.append(f"duplicate candles={duplicate_candles}")

    status = "PASS" if not errors else "WARNING"
    return FileValidationResult(
        str(path),
        status,
        len(df),
        duplicate_candles,
        missing_timestamps,
        "; ".join(errors),
    )


def validate_data_dir(data_dir: Path) -> list[FileValidationResult]:
    if not data_dir.exists():
        return [FileValidationResult(str(data_dir), "FAIL", 0, 0, 0, "directory missing")]

    files = sorted(data_dir.glob("*.parquet"))
    if not files:
        return [FileValidationResult(str(data_dir), "FAIL", 0, 0, 0, "no parquet files found")]

    return [validate_parquet_file(path) for path in files]


def write_report(results: list[FileValidationResult], output_csv: Path, output_json: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(result) for result in results]
    pd.DataFrame(rows).to_csv(output_csv, index=False)
    output_json.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate live 2H parquet data.")
    parser.add_argument("--data-dir", default="data/live/2h")
    parser.add_argument("--output-csv", default="logs/data_validation_report.csv")
    parser.add_argument("--output-json", default="logs/data_validation_report.json")
    args = parser.parse_args()

    logger = get_system_logger("paper_trading.data_validator")
    results = validate_data_dir(Path(args.data_dir))
    write_report(results, Path(args.output_csv), Path(args.output_json))

    failed = [result for result in results if result.status == "FAIL"]
    warnings = [result for result in results if result.status == "WARNING"]
    print(f"Validated files: {len(results)}")
    print(f"FAIL: {len(failed)}")
    print(f"WARNING: {len(warnings)}")
    print(f"Report: {args.output_csv}")
    logger.info("Data validation complete files=%s failed=%s warnings=%s", len(results), len(failed), len(warnings))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
