import matplotlib

matplotlib.use("Agg")

from pathlib import Path  # noqa: E402

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

import data_processor as dp  # noqa: E402

RAW_MAT = Path(__file__).resolve().parents[1] / "data" / "raw" / "student-mat.csv"


@pytest.fixture
def student_rows() -> pd.DataFrame:
    """First 6 real student-mat rows as page strings (a realistic template to mutate)."""
    return pd.read_csv(RAW_MAT, sep=";", dtype=str, keep_default_na=False).head(6).copy()


def valid_pisa_raw(n_countries: int = dp.PISA_MIN_COUNTRIES) -> pd.DataFrame:
    """Smallest raw PISA table that passes validate_pisa_raw()."""
    rows = []
    for source, year in (("summary", "2025"), ("comparison", "2022")):
        for subject in dp.PISA_SUBJECTS.values():
            rows.append({"source": source, "year": year, "subject": subject, "rank": "",
                         "country": "International Average (OECD)", "score": "480"})
            for i in range(n_countries):
                rows.append({"source": source, "year": year, "subject": subject, "rank": str(i + 1),
                             "country": f"Country {i}", "score": str(550 - i)})
    return pd.DataFrame(rows)
