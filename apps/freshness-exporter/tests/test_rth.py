from datetime import UTC, datetime

import pytest

from freshness_exporter.rth import in_rth


@pytest.mark.parametrize(
    ("utc", "expected"),
    [
        (datetime(2026, 11, 9, 14, 29, tzinfo=UTC), False),  # 09:29 ET Monday (EST, UTC-5)
        (datetime(2026, 11, 9, 14, 30, tzinfo=UTC), True),  # 09:30 ET open
        (datetime(2026, 11, 9, 20, 59, tzinfo=UTC), True),  # 15:59 ET
        (datetime(2026, 11, 9, 21, 0, tzinfo=UTC), False),  # 16:00 ET close
        (datetime(2026, 10, 30, 13, 30, tzinfo=UTC), True),  # 09:30 EDT (UTC-4)
        (datetime(2026, 11, 7, 15, 0, tzinfo=UTC), False),  # Saturday
    ],
)
def test_in_rth(utc, expected):
    assert in_rth(utc) is expected


def test_naive_rejected():
    with pytest.raises(ValueError):
        in_rth(datetime(2026, 11, 9, 15, 0))  # noqa: DTZ001
