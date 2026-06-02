from __future__ import annotations

import pandas as pd

from paper_trading.data_validator import validate_data_dir, validate_parquet_file


def test_data_validator_detects_duplicate_candles(tmp_path):
    path = tmp_path / "AAA.parquet"
    df = pd.DataFrame(
        {
            "datetime": pd.to_datetime(["2026-06-01 09:15", "2026-06-01 09:15"]),
            "open": [1, 1],
            "high": [1, 1],
            "low": [1, 1],
            "close": [1, 1],
            "volume": [1, 1],
        }
    )
    df.to_parquet(path, index=False)

    result = validate_parquet_file(path)

    assert result.status == "WARNING"
    assert result.duplicate_candles == 1


def test_data_validator_detects_empty_directory(tmp_path):
    results = validate_data_dir(tmp_path)

    assert results[0].status == "FAIL"
    assert "no parquet files" in results[0].error
