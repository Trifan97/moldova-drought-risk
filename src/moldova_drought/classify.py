"""Classify SPEI values into drought severity categories."""

import numpy as np
import pandas as pd

# Categories from driest to wettest, with a numeric code (useful for colour ramps).
CODES = {
    "Extremely dry": -3,
    "Very dry": -2,
    "Moderately dry": -1,
    "Normal": 0,
    "Moderately wet": 1,
    "Very wet": 2,
    "Extremely wet": 3,
}
NO_DATA = "No data"
SEVERITY_DTYPE = pd.CategoricalDtype([*CODES, NO_DATA])


def classify_spei(spei: pd.Series) -> pd.DataFrame:
    """Return the severity category and code of each SPEI value, keeping the input index.

    A value exactly on a threshold belongs to the more extreme category: -1.00 is
    "Moderately dry" and 1.00 is "Moderately wet". A missing value becomes "No data"
    with a missing code; it is never guessed into a real category.
    """
    # np.select picks the first true condition, so each line only needs its upper bound.
    conditions = [
        spei <= -2.0,  # Extremely dry
        spei <= -1.5,  # Very dry
        spei <= -1.0,  # Moderately dry
        spei < 1.0,  # Normal
        spei < 1.5,  # Moderately wet
        spei < 2.0,  # Very wet
        spei >= 2.0,  # Extremely wet
    ]
    labels = pd.Series(np.select(conditions, list(CODES), default=NO_DATA), index=spei.index)
    return pd.DataFrame(
        {
            "severity": labels.astype(SEVERITY_DTYPE),
            "severity_code": labels.map(CODES).astype("Int8"),
        }
    )
