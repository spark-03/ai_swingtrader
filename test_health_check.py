from __future__ import annotations

from paper_trading.health_check import CheckResult, format_report


def test_health_report_pass_fail_format():
    report = format_report(
        [
            CheckResult("A", True, "ok"),
            CheckResult("B", False, "bad"),
        ]
    )

    assert "PASS: A - ok" in report
    assert "FAIL: B - bad" in report
    assert "OVERALL: FAIL" in report
