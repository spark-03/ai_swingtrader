from __future__ import annotations

import argparse
import importlib.metadata
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd
import requests

from paper_trading.live_candidate_engine import CandidateEngineConfig
from paper_trading.logging_config import get_system_logger
from paper_trading.pqs_engine import calculate_pqs
from paper_trading.rl_exit_engine import RLExitConfig
from paper_trading.supabase_logger import SupabaseConfig


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


def check_supabase_connectivity() -> CheckResult:
    try:
        config = SupabaseConfig.from_env()
        endpoint = f"{config.url}/rest/v1/"
        response = requests.get(
            endpoint,
            headers={
                "apikey": config.key,
                "Authorization": f"Bearer {config.key}",
            },
            timeout=15,
        )
        if response.status_code < 500:
            return CheckResult("Supabase connectivity", True, f"HTTP {response.status_code}")
        return CheckResult("Supabase connectivity", False, f"HTTP {response.status_code}")
    except Exception as exc:
        return CheckResult("Supabase connectivity", False, str(exc))


def check_file_exists(name: str, path: Path) -> CheckResult:
    if path.exists() and path.stat().st_size >= 0:
        return CheckResult(name, True, str(path))
    return CheckResult(name, False, f"Missing: {path}")


def check_2h_data_exists(path: Path) -> CheckResult:
    files = list(path.glob("*.parquet")) if path.exists() else []
    readable = 0
    for file_path in files[:10]:
        try:
            df = pd.read_parquet(file_path, columns=["datetime"])
            if not df.empty:
                readable += 1
        except Exception:
            continue

    if files and readable > 0:
        return CheckResult("2H data exists", True, f"{len(files)} parquet files, sample_readable={readable}")
    return CheckResult("2H data exists", False, f"No readable parquet files in {path}")


def check_pqs_engine_loads() -> CheckResult:
    try:
        sample = pd.DataFrame(
            {
                "ema_spread": [0.1, 0.2, 0.3],
                "trend_strength": [0.1, 0.2, 0.3],
                "momentum_score": [0.3, 0.2, 0.1],
                "compression_score": [0.2, 0.2, 0.2],
                "volatility_score": [0.1, 0.2, 0.3],
            }
        )
        out = calculate_pqs(sample)
        if "pqs" in out.columns:
            return CheckResult("PQS engine loads", True, "PQS calculation succeeded")
        return CheckResult("PQS engine loads", False, "PQS column missing")
    except Exception as exc:
        return CheckResult("PQS engine loads", False, str(exc))


def check_requirements_file(path: Path = Path("requirements.txt")) -> CheckResult:
    if not path.exists():
        return CheckResult("requirements.txt verification", False, "requirements.txt missing")

    missing: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        package = line.split("==", 1)[0].split(">=", 1)[0].split("<=", 1)[0].strip()
        try:
            importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            missing.append(package)

    if missing:
        return CheckResult("requirements.txt verification", False, "Missing packages: " + ", ".join(missing))
    return CheckResult("requirements.txt verification", True, "All listed packages are installed")


def run_checks() -> list[CheckResult]:
    checks: list[Callable[[], CheckResult]] = [
        check_supabase_connectivity,
        lambda: check_file_exists("Portfolio file exists", Path("current_portfolio.csv")),
        lambda: check_file_exists("Universe file exists", Path("configs/nifty500_symbols.txt")),
        lambda: check_2h_data_exists(CandidateEngineConfig().hourly_data_dir),
        lambda: check_file_exists("RL model exists", RLExitConfig().model_path),
        check_pqs_engine_loads,
        check_requirements_file,
    ]
    return [check() for check in checks]


def format_report(results: list[CheckResult]) -> str:
    lines = ["Production Health Check"]
    for result in results:
        lines.append(f"{result.status}: {result.name} - {result.detail}")
    overall = "PASS" if all(result.passed for result in results) else "FAIL"
    lines.append(f"OVERALL: {overall}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run production health checks.")
    parser.add_argument("--allow-missing-supabase", action="store_true", help="Do not fail when Supabase env is absent.")
    args = parser.parse_args()

    logger = get_system_logger("paper_trading.health_check")
    results = run_checks()

    if args.allow_missing_supabase and not os.getenv("SUPABASE_URL"):
        results = [
            CheckResult(r.name, True, "Skipped by --allow-missing-supabase") if r.name == "Supabase connectivity" else r
            for r in results
        ]

    report = format_report(results)
    print(report)
    logger.info(report.replace("\n", " | "))
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
