"""Classify SPEI values into drought severity categories."""

import numpy as np
import pandas as pd

# Categories from driest to wettest, with a numeric code (useful for colour ramps).
CODES = {
    "Extreme drought": -3,
    "Severe drought": -2,
    "Moderate drought": -1,
    "Normal": 0,
    "Moderate wet": 1,
    "Severe wet": 2,
    "Extreme wet": 3,
}
NO_DATA = "No data"
SEVERITY_DTYPE = pd.CategoricalDtype([*CODES, NO_DATA])


def classify_spei(spei: pd.Series) -> pd.DataFrame:
    """Return the severity category and code of each SPEI value, keeping the input index.

    A value exactly on a threshold belongs to the more extreme category: -1.00 is
    "Moderate drought" and 1.00 is "Moderate wet". A missing value becomes "No data"
    with a missing code; it is never guessed into a real category.
    """
    # np.select picks the first true condition, so each line only needs its upper bound.
    conditions = [
        spei <= -2.0,  # Extreme drought
        spei <= -1.5,  # Severe drought
        spei <= -1.0,  # Moderate drought
        spei < 1.0,  # Normal
        spei < 1.5,  # Moderate wet
        spei < 2.0,  # Severe wet
        spei >= 2.0,  # Extreme wet
    ]
    labels = pd.Series(np.select(conditions, list(CODES), default=NO_DATA), index=spei.index)
    return pd.DataFrame(
        {
            "severity": labels.astype(SEVERITY_DTYPE),
            "severity_code": labels.map(CODES).astype("Int8"),
        }
    )
