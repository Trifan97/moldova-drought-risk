"""Tests for SPEI severity classification."""

import math

import pandas as pd
import pytest

from moldova_drought.classify import classify_spei


@pytest.mark.parametrize(
    ("spei", "expected"),
    [
        (-3.0, "Extremely dry"),
        (-2.0, "Extremely dry"),
        (-1.99, "Very dry"),
        (-1.5, "Very dry"),
        (-1.49, "Moderately dry"),
        (-1.0, "Moderately dry"),
        (-0.995, "Normal"),
        (-0.99, "Normal"),
        (0.0, "Normal"),
        (0.99, "Normal"),
        (0.995, "Normal"),
        (1.0, "Moderately wet"),
        (1.49, "Moderately wet"),
        (1.5, "Very wet"),
        (1.99, "Very wet"),
        (2.0, "Extremely wet"),
        (3.0, "Extremely wet"),
        (-math.inf, "Extremely dry"),
        (math.inf, "Extremely wet"),
        (math.nan, "No data"),
    ],
)
def test_category(spei: float, expected: str) -> None:
    result = classify_spei(pd.Series([spei]))

    assert result["severity"].iloc[0] == expected


def test_codes_run_from_minus_3_to_3_and_no_data_has_none() -> None:
    result = classify_spei(pd.Series([-2.5, 0.0, 2.5, math.nan]))

    expected = pd.Series([-3, 0, 3, pd.NA], dtype="Int8", name="severity_code")
    pd.testing.assert_series_equal(result["severity_code"], expected)


def test_sorting_follows_severity_not_alphabet() -> None:
    result = classify_spei(pd.Series([2.5, math.nan, -2.5, 0.0]))

    ordered = result["severity"].sort_values().tolist()

    assert ordered == ["Extremely dry", "Normal", "Extremely wet", "No data"]


def test_keeps_the_input_index() -> None:
    spei = pd.Series([0.0, -2.5], index=[10, 20])

    assert classify_spei(spei).index.tolist() == [10, 20]
