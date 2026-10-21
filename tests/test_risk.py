"""Tests for the drought-risk summary."""

import math

import pandas as pd

from moldova_drought.classify import classify_spei
from moldova_drought.risk import drought_summary


def make_table(
    baseline: list[float], recent: list[float], district_id: str = "MD-A"
) -> pd.DataFrame:
    """One district's monthly rows: `baseline` values from Jan 1970, `recent` from Jan 2000."""
    dates = [
        *pd.date_range("1970-01-01", periods=len(baseline), freq="MS"),
        *pd.date_range("2000-01-01", periods=len(recent), freq="MS"),
    ]
    spei = pd.Series([*baseline, *recent])
    months = pd.DataFrame({"district_id": district_id, "date": dates, "spei_3": spei})
    return months.join(classify_spei(spei))


def test_shares_per_normal_leave_out_missing_months() -> None:
    table = make_table(baseline=[math.nan, -1.2, 0.0, 0.0, 0.0], recent=[-1.2, -1.6, 0.0, 0.0])

    summary = drought_summary(table).iloc[0]

    assert summary["drought_pct_1961_1990"] == 25.0  # 1 of 4 months with data
    assert summary["drought_pct_1991_2020"] == 50.0  # 2 of 4 months
    assert summary["drought_change_pp"] == 25.0


def test_change_agrees_with_the_rounded_shares() -> None:
    table = make_table(baseline=[-1.2, 0.0, 0.0], recent=[-1.2, -1.2, 0.0])

    summary = drought_summary(table).iloc[0]

    # Shown as 33.3% and 66.7%, so the change shown must be 33.4, not 33.3.
    assert summary["drought_change_pp"] == 33.4


def test_driest_month() -> None:
    summary = drought_summary(make_table(baseline=[0.0], recent=[-1.6, -1.2])).iloc[0]

    assert summary["driest_spei_3"] == -1.6
    assert summary["driest_month"] == pd.Timestamp("2000-01-01")


def test_one_row_per_district_even_with_repeated_index() -> None:
    # concat keeps both tables' index labels (0, 1 twice): the summary must not care.
    table = pd.concat([make_table([0.0], [-1.2], "MD-A"), make_table([0.0], [-1.2], "MD-B")])

    summary = drought_summary(table)

    assert summary["district_id"].tolist() == ["MD-A", "MD-B"]
