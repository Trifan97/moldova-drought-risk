"""Drought-risk summary per district: how drought frequency changed between two normals."""

import pandas as pd

from moldova_drought.classify import CODES


def drought_summary(table: pd.DataFrame) -> pd.DataFrame:
    """One row per district: % of months in drought per WMO normal, the change, the driest month.

    "In drought" means Moderate drought or worse (SPEI-3 <= -1.0). Percentages count only
    months with data: "No data" months are left out.
    """
    valid = table.dropna(subset=["spei_3"]).assign(
        drought=lambda t: t["severity_code"] <= CODES["Moderate drought"]
    )
    year = valid["date"].dt.year
    baseline = valid[year.between(1961, 1990)].groupby("district_id")["drought"].mean()
    recent = valid[year.between(1991, 2020)].groupby("district_id")["drought"].mean()

    summary = pd.DataFrame(
        {
            "drought_pct_1961_1990": (baseline * 100).round(1),
            "drought_pct_1991_2020": (recent * 100).round(1),
        }
    )
    # From the rounded shares, so the three columns agree when read side by side.
    summary["drought_change_pp"] = (
        summary["drought_pct_1991_2020"] - summary["drought_pct_1961_1990"]
    ).round(1)

    # Sort by SPEI and keep each district's first row: its driest month.
    driest = (
        valid.sort_values("spei_3", kind="stable")
        .drop_duplicates("district_id")
        .set_index("district_id")[["spei_3", "date"]]
        .rename(columns={"spei_3": "driest_spei_3", "date": "driest_month"})
    )
    return summary.join(driest).reset_index()
