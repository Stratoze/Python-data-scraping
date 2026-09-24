"""P1 - Student Performance data processor.

Covers the full P1 rubric:
- 4 basic functions (yes/no encode, pass/fail, absence buckets, average grade)
- list[dict] sample students, dict mappings, set() uniques, tuple threshold config
- OOP pipeline: StudentDataProcessor.load_data / clean_data / analyze / export_results
- UCI raw collection + Wikipedia PISA reference scrape (requests + BeautifulSoup, cached)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Threshold config as tuple (immutable, per rubric)
# (PASS_MARK, RISK_G1G2_WARN, ABS_MED, ABS_HIGH, FAIL_HIGH)
# ---------------------------------------------------------------------------
THRESHOLDS = (10, 10, 4, 10, 2)
PASS_MARK, G_WARN, ABS_MED, ABS_HIGH, FAIL_HIGH = THRESHOLDS

# Variable description mapping (dict mapping, per rubric)
VAR_DESCRIPTIONS = {
    "studytime": "Weekly study time bucket 1-4 (<2h, 2-5h, 5-10h, >10h)",
    "absences": "Number of school absences",
    "failures": "Number of past class failures",
    "internet": "Internet access at home (yes/no)",
    "G1": "First period grade (0-20)",
    "G2": "Second period grade (0-20)",
    "G3": "Final grade (0-20)",
    "schoolsup": "Extra educational support (yes/no)",
    "famsup": "Family educational support (yes/no)",
}

YES_NO_COLS = ["schoolsup", "famsup", "paid", "activities", "nursery",
               "higher", "internet", "romantic"]

# Sample students as list of dicts (per rubric)
SAMPLE_STUDENTS = [
    {"id": 1, "studytime": 2, "absences": 6, "failures": 0,
     "internet": "yes", "G1": 5, "G2": 6, "G3": 6},
    {"id": 2, "studytime": 2, "absences": 4, "failures": 0,
     "internet": "no", "G1": 5, "G2": 5, "G3": 6},
    {"id": 3, "studytime": 3, "absences": 10, "failures": 3,
     "internet": "yes", "G1": 7, "G2": 8, "G3": 10},
]


# ---------------------------------------------------------------------------
# 4 basic functions (Python basics rubric)
# ---------------------------------------------------------------------------
def convert_yes_no(value: str) -> int:
    """Encode 'yes'/'no' (case-insensitive, stripped) to 1/0."""
    return 1 if str(value).strip().lower() == "yes" else 0


def calc_pass_fail(g3: float, pass_mark: int = PASS_MARK) -> str:
    """Return 'pass' if G3 >= pass_mark else 'fail'."""
    return "pass" if float(g3) >= pass_mark else "fail"


def classify_absences(n: int) -> str:
    """Bucket absences: low (0-3) / medium (4-9) / high (>=10)."""
    n = int(n)
    if n < ABS_MED:
        return "low"
    if n < ABS_HIGH:
        return "medium"
    return "high"


def calc_average_grade(g1: float, g2: float, g3: float) -> float:
    """Mean of the three grade periods."""
    return (float(g1) + float(g2) + float(g3)) / 3.0


def classify_risk(row: pd.Series) -> str:
    """Learning-risk segment used across EDA and exports.

    high   : G3 < PASS_MARK or failures >= FAIL_HIGH
    medium : G1 < G_WARN or G2 < G_WARN or failures > 0 or absences high
    low    : otherwise
    """
    if row["G3"] < PASS_MARK or row["failures"] >= FAIL_HIGH:
        return "high"
    if (row["G1"] < G_WARN or row["G2"] < G_WARN
            or row["failures"] > 0
            or classify_absences(row["absences"]) == "high"):
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# PISA reference scrape (Wikipedia, cached)
# ---------------------------------------------------------------------------
PISA_URL = ("https://en.wikipedia.org/wiki/"
            "Programme_for_International_Student_Assessment")


def scrape_pisa_table(url: str = PISA_URL, out_csv: Path | None = None) -> pd.DataFrame:
    """Scrape a wikitable on the PISA page, cache to CSV.

    Manual BeautifulSoup parsing (no pd.read_html) to stay light.
    Returns the DataFrame. On network failure, loads the cached CSV
    if it exists, otherwise re-raises a short error.
    """
    try:
        resp = requests.get(url, timeout=25,
                            headers={"User-Agent": "Mozilla/5.0 P1-edu-project"})
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        tables = soup.find_all("table", {"class": "wikitable"})
        if not tables:
            raise ValueError("No wikitable found on PISA page")
        # Pick the first *sane* ranking table: 2-8 cols, header has Rank/Score.
        # Table 0 on the PISA page is a 3-in-1 container (=> 800+ cols), skip it.
        target = None
        for t in tables:
            rows_tmp = []
            for tr in t.find_all("tr")[:6]:
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if cells:
                    rows_tmp.append(cells)
            if not rows_tmp:
                continue
            width = max(len(r) for r in rows_tmp)
            head = " ".join(rows_tmp[0]).lower()
            if 2 <= width <= 8 and ("rank" in head or "score" in head or "country" in head):
                target = t
                break
        target = target or tables[1] if len(tables) > 1 else tables[0]
        rows = []
        for tr in target.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        df = pd.DataFrame(rows[1:], columns=[f"col_{i}" for i in range(width)]
                          if not rows[0] else rows[0])
        df.columns = [str(c).strip()[:60] for c in df.columns]
        if out_csv is not None:
            out_csv.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(out_csv, index=False, encoding="utf-8")
        return df
    except Exception as exc:
        if out_csv is not None and Path(out_csv).exists():
            return pd.read_csv(out_csv)
        raise RuntimeError(f"PISA scrape failed: {type(exc).__name__}") from exc


# ---------------------------------------------------------------------------
# OOP pipeline
# ---------------------------------------------------------------------------
class StudentDataProcessor:
    """Load -> clean -> analyze -> export for UCI student-mat."""

    def __init__(self, raw_path: Path, pisa_raw: Path,
                 processed_dir: Path, images_dir: Path):
        self.raw_path = Path(raw_path)
        self.pisa_raw = Path(pisa_raw)
        self.processed_dir = Path(processed_dir)
        self.images_dir = Path(images_dir)
        self.df: pd.DataFrame | None = None
        self.clean: pd.DataFrame | None = None
        self.results: dict = {}

    # -- step 1: load ----------------------------------------------------
    def load_data(self) -> pd.DataFrame:
        self.df = pd.read_csv(self.raw_path, sep=";")
        return self.df

    # -- step 2: clean ---------------------------------------------------
    def clean_data(self) -> pd.DataFrame:
        assert self.df is not None, "call load_data() first"
        df = self.df.copy()
        for col in ["G1", "G2", "G3", "absences", "failures", "studytime", "age"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        for col in YES_NO_COLS:
            if col in df.columns:
                df[col + "_bin"] = df[col].apply(convert_yes_no)
        df["pass_fail"] = df["G3"].apply(calc_pass_fail)
        df["absence_level"] = df["absences"].apply(classify_absences)
        df["avg_grade"] = df.apply(
            lambda r: calc_average_grade(r["G1"], r["G2"], r["G3"]), axis=1)
        df["risk_group"] = df.apply(classify_risk, axis=1)
        df = df.dropna(subset=["G1", "G2", "G3"]).reset_index(drop=True)
        self.clean = df
        return df

    # -- step 3: analyze -------------------------------------------------
    def analyze(self) -> dict:
        assert self.clean is not None, "call clean_data() first"
        df = self.clean

        # set() uniques + dict mapping usage (rubric)
        unique_schools = set(df["school"].unique())
        unique_mjobs = set(df["Mjob"].unique())
        unique_fjobs = set(df["Fjob"].unique())

        def grp(col: str) -> dict:
            g = df.groupby(col)["G3"].agg(["mean", "std", "count"])
            return {str(k): {"mean": round(float(v["mean"]), 2),
                             "std": round(float(v["std"]), 2) if pd.notna(v["std"]) else 0.0,
                             "n": int(v["count"])}
                    for k, v in g.iterrows()}

        by_studytime = grp("studytime")
        by_absence = grp("absence_level")
        by_failures = grp("failures")
        by_internet = grp("internet")
        by_risk = grp("risk_group")
        pass_rate = round(float((df["pass_fail"] == "pass").mean()), 4)
        corr = df[["G1", "G2", "G3", "absences", "failures", "studytime"]].corr(
            numeric_only=True).round(3)

        self.results = {
            "n": int(len(df)),
            "pass_rate": pass_rate,
            "n_pass": int((df["pass_fail"] == "pass").sum()),
            "n_fail": int((df["pass_fail"] == "fail").sum()),
            "unique_schools": sorted(unique_schools),
            "unique_mjobs": sorted(unique_mjobs),
            "unique_fjobs": sorted(unique_fjobs),
            "by_studytime": by_studytime,
            "by_absence_level": by_absence,
            "by_failures": by_failures,
            "by_internet": by_internet,
            "by_risk_group": by_risk,
            "corr_G1_G2_G3": {
                "G1_G2": float(corr.loc["G1", "G2"]),
                "G1_G3": float(corr.loc["G1", "G3"]),
                "G2_G3": float(corr.loc["G2", "G3"]),
            },
            "corr_full": corr.to_dict(),
            "thresholds": list(THRESHOLDS),
        }
        self._plot_charts(df, corr)
        return self.results

    def _plot_charts(self, df: pd.DataFrame, corr: pd.DataFrame) -> None:
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Chart 1: bar - mean G3 by studytime (split by internet)
        fig, ax = plt.subplots(figsize=(8, 5))
        piv = df.groupby(["studytime", "internet"])["G3"].mean().unstack()
        piv.plot(kind="bar", ax=ax)
        ax.set_title("Mean final grade (G3) by studytime and internet access")
        ax.set_xlabel("Studytime bucket (1=<2h, 2=2-5h, 3=5-10h, 4=>10h)")
        ax.set_ylabel("Mean G3")
        ax.legend(title="Internet")
        fig.tight_layout()
        fig.savefig(self.images_dir / "01_bar_studytime_internet.png", dpi=150)
        plt.close(fig)

        # Chart 2: histogram - G3 distribution with pass line
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(df["G3"], bins=20, edgecolor="black")
        ax.axvline(PASS_MARK, linestyle="--", label=f"Pass mark = {PASS_MARK}")
        ax.set_title("Distribution of final grades (G3)")
        ax.set_xlabel("G3 (0-20)")
        ax.set_ylabel("Students")
        ax.legend()
        fig.tight_layout()
        fig.savefig(self.images_dir / "02_hist_g3.png", dpi=150)
        plt.close(fig)

        # Chart 3: heatmap - correlation matrix (matplotlib only)
        fig, ax = plt.subplots(figsize=(7, 6))
        cols = list(corr.columns)
        im = ax.imshow(corr.values, vmin=-1, vmax=1)
        ax.set_xticks(range(len(cols)), cols, rotation=45, ha="right")
        ax.set_yticks(range(len(cols)), cols)
        for i in range(len(cols)):
            for j in range(len(cols)):
                ax.text(j, i, f"{corr.values[i, j]:.2f}",
                        ha="center", va="center", fontsize=8)
        ax.set_title("Correlation heatmap (grades + absences/failures/studytime)")
        fig.colorbar(im, ax=ax, shrink=0.8)
        fig.tight_layout()
        fig.savefig(self.images_dir / "03_heatmap_corr.png", dpi=150)
        plt.close(fig)

    # -- step 4: export --------------------------------------------------
    def export_results(self) -> tuple[Path, Path]:
        assert self.clean is not None and self.results, "run clean+analyze first"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        cleaned_csv = self.processed_dir / "cleaned_students.csv"
        summary_json = self.processed_dir / "summary.json"
        self.clean.to_csv(cleaned_csv, index=False)
        with open(summary_json, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        return cleaned_csv, summary_json
