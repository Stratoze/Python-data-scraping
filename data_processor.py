"""P1 - Student Performance data processor.

Covers the full P1 rubric:
- 4 basic functions (yes/no encode, pass/fail, absence buckets, average grade)
- list[dict] sample students, dict mappings, set() uniques, tuple threshold config
- OOP pipeline: StudentDataProcessor.load_data / clean_data / analyze / export_results
- UCI raw collection (student.zip) + Wikipedia PISA scrape (requests + BeautifulSoup, cached)
"""
from __future__ import annotations

import io
import json
import re
import warnings
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from scipy import stats

# ---------------------------------------------------------------------------
# Threshold config as tuples (immutable, per rubric)
# ---------------------------------------------------------------------------
# (PASS_MARK, G_WARN, ABS_MED, ABS_HIGH, FAIL_HIGH)
THRESHOLDS = (10, 10, 4, 10, 2)
PASS_MARK, G_WARN, ABS_MED, ABS_HIGH, FAIL_HIGH = THRESHOLDS

# Anomaly flags: (IQR_K, G1_DROP, G2_DROP, AGE_OUTLIER)
ANOMALY_THRESHOLDS = (1.5, 8, 6, 20)
IQR_K, G1_DROP, G2_DROP, AGE_OUTLIER = ANOMALY_THRESHOLDS

# PISA scrape sanity checks: (MIN_COUNTRIES per subject/year, SCORE_MIN, SCORE_MAX)
PISA_CHECKS = (30, 200, 700)
PISA_MIN_COUNTRIES, PISA_SCORE_MIN, PISA_SCORE_MAX = PISA_CHECKS

# Statistical tests: significance level and the variables whose G3 groups are compared
ALPHA = 0.05
BINARY_TEST_COLS = ["internet", "famsup", "schoolsup", "paid"]
MULTI_TEST_COLS = ["studytime", "absence_level", "failures"]
# Sparse levels merged before ANOVA/Kruskal: failures 2 and 3 have ~12 students each -> one "2+" group
TEST_LEVEL_CAP = {"failures": 2}
# Chart 1 bars with fewer students are drawn hatched: their mean is not reliable
MIN_RELIABLE_N = 10
CORR_TEST_COLS = ["G1", "G2", "studytime", "failures", "absences", "famsup_bin"]

# Columns identifying the same student in student-mat and student-por (student-merge.R)
MERGE_KEYS = ["school", "sex", "age", "address", "famsize", "Pstatus", "Medu", "Fedu",
              "Mjob", "Fjob", "reason", "nursery", "internet"]

# Multivariable regression of G3 (each coefficient = effect with all other columns held fixed).
# Background factors: the main-question variables plus socio-economic / demographic controls.
REG_FACTORS = ["studytime", "failures", "absences", "famsup_bin", "schoolsup_bin", "paid_bin",
               "internet_bin", "higher_bin", "Medu", "Fedu", "male", "age", "urban"]
REG_GRADES = ["G1", "G2"]

# OECD PISA 2025 Table I.1 (official source used to cross-check the Wikipedia scrape).
# Country names that differ between the OECD report and Wikipedia:
OECD_PISA_YEAR = 2025
OECD_NAME_ALIASES = {"Chinese Taipei": "Taiwan", "Czechia": "Czech Republic", "Korea": "South Korea",
                     "Slovak Republic": "Slovakia", "Viet Nam": "Vietnam"}

# Variable description mapping (dict mapping, per rubric)
VAR_DESCRIPTIONS = {
    "studytime": "Weekly study time bucket 1-4 (<2h, 2-5h, 5-10h, >10h)",
    "absences": "Number of school absences",
    "failures": "Number of past class failures",
    "internet": "Internet access at home (yes/no)",
    "G1": "First period grade (0-20)",
    "G2": "Second period grade (0-20)",
    "G3": "Final grade (0-20)",
    "schoolsup": "Extra educational support from school (yes/no)",
    "famsup": "Family educational support (yes/no)",
    "paid": "Extra paid classes within the course subject (yes/no)",
    "avg_grade": "Mean of G1, G2, G3 (descriptive only: contains target G3, DO NOT use as predictor)",
    "avg_g1g2": "Mean of G1 and G2 (mid-year performance; safe for early prediction)",
}

# Valid value domain per numeric column (from data/raw/student.txt)
VALID_RANGES = {
    "age": (15, 22), "Medu": (0, 4), "Fedu": (0, 4),
    "traveltime": (1, 4), "studytime": (1, 4), "failures": (0, 3),
    "famrel": (1, 5), "freetime": (1, 5), "goout": (1, 5),
    "Dalc": (1, 5), "Walc": (1, 5), "health": (1, 5),
    "absences": (0, 93), "G1": (0, 20), "G2": (0, 20), "G3": (0, 20),
}
REQUIRED_COLS = ["G1", "G2", "G3", "absences", "failures", "studytime", "age"]

YES_NO_COLS = ["schoolsup", "famsup", "paid", "activities", "nursery",
               "higher", "internet", "romantic"]

FLAG_COLS = ["dropout_suspect", "g2_zero", "grade_drop",
             "absence_outlier", "age_outlier", "inconsistent_grade"]

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
def convert_yes_no(value) -> int | None:
    """Encode 'yes'/'no' (case-insensitive, stripped) to 1/0; anything else -> None."""
    text = str(value).strip().lower()
    if text == "yes":
        return 1
    if text == "no":
        return 0
    return None


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
    """Mean of the three grade periods: (G1 + G2 + G3) / 3.

    WARNING: Contains the target G3. Descriptive only; NEVER use as a predictor
    for G3 to prevent target leakage. For early prediction, use avg_g1g2 instead.
    """
    return (float(g1) + float(g2) + float(g3)) / 3.0


def classify_risk(row: pd.Series) -> str:
    """Early-warning segment from information available before the final exam.

    Uses only G1, G2, failures, absences (never G3, so it can be evaluated
    against pass/fail without leakage).
    high   : G2 < G_WARN or failures >= FAIL_HIGH
    medium : G1 < G_WARN or failures > 0 or absences high (>= ABS_HIGH)
    low    : otherwise
    """
    if row["G2"] < G_WARN or row["failures"] >= FAIL_HIGH:
        return "high"
    if (row["G1"] < G_WARN or row["failures"] > 0
            or classify_absences(row["absences"]) == "high"):
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Data collection: UCI zip + Wikipedia PISA
# ---------------------------------------------------------------------------
UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/320/student+performance.zip"
UCI_FILES = ("student-mat.csv", "student-por.csv", "student-merge.R", "student.txt")
PISA_URL = ("https://en.wikipedia.org/wiki/"
            "Programme_for_International_Student_Assessment")
HTTP_HEADERS = {
    "User-Agent": "P1-edu-project/1.0 (https://github.com/Stratoze/Python-data-scraping; "
                  "mailto:vohoangquocminh2k5@gmail.com) student coursework"
}
PISA_SUBJECTS = {"mathematics": "mathematics", "science": "science", "reading": "reading"}


def fetch_uci_raw(raw_dir: Path, url: str = UCI_ZIP_URL) -> list[Path]:
    """Download UCI student.zip and extract raw files if any are missing."""
    raw_dir = Path(raw_dir)
    targets = [raw_dir / name for name in UCI_FILES]
    if all(p.exists() for p in targets):
        return targets
    raw_dir.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=60, headers=HTTP_HEADERS)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as outer:
        with zipfile.ZipFile(io.BytesIO(outer.read("student.zip"))) as inner:
            for name in UCI_FILES:
                (raw_dir / name).write_bytes(inner.read(name))
    return targets


def _cell_texts(tr) -> list[str]:
    return [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"], recursive=False)]


def _strip_footnote(text: str) -> str:
    return re.sub(r"\s*\[\s*[^\]]*\]", "", text).strip()


def _parse_pisa_html(html: str) -> pd.DataFrame:
    """Extract PISA ranking tables into a raw long table (all values as page strings).

    - summary  : latest 'ranking summary' tables (Rank | Country/economy | Score),
                 subject order taken from the container table header.
    - comparison: 'Rankings comparison' tables (Country | year score/rank pairs).
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []
    for table in soup.find_all("table", class_="wikitable"):
        trs = table.find_all("tr", recursive=False) or table.select(":scope > tbody > tr")
        if not trs:
            continue
        head = _cell_texts(trs[0])
        heading = table.find_previous(["h2", "h3"])
        heading_text = heading.get_text(" ", strip=True) if heading else ""

        # Container of the latest ranking summary: header lists the subjects,
        # nested tables hold Rank | Country/economy | Score in the same order.
        subjects = [_strip_footnote(h).lower() for h in head]
        nested = table.find_all("table", class_="wikitable")
        if nested and all(s in PISA_SUBJECTS for s in subjects) and len(nested) == len(subjects):
            year_match = re.search(r"(\d{4})", heading_text)
            year = year_match.group(1) if year_match else ""
            for subject, sub in zip(subjects, nested):
                for tr in sub.find_all("tr")[1:]:
                    cells = _cell_texts(tr)
                    if len(cells) == 3:
                        rank, country, score = cells
                    elif len(cells) == 2:  # e.g. "International Average (OECD)" has no rank
                        rank, (country, score) = "", cells
                    else:
                        continue
                    rows.append({"source": "summary", "year": year,
                                 "subject": PISA_SUBJECTS[subject],
                                 "rank": rank, "country": country, "score": score})
            continue

        # Historical comparison: single-cell subject title, then Country | years, then Score/Rank.
        if (len(head) == 1 and _strip_footnote(head[0]).lower() in PISA_SUBJECTS
                and len(trs) > 3 and _cell_texts(trs[1])[:1] == ["Country"]):
            subject = PISA_SUBJECTS[_strip_footnote(head[0]).lower()]
            years = [_strip_footnote(y) for y in _cell_texts(trs[1])[1:]]
            for tr in trs[3:]:
                cells = _cell_texts(tr)
                if len(cells) != 1 + 2 * len(years):
                    continue
                country = cells[0]
                for k, year in enumerate(years):
                    rows.append({"source": "comparison", "year": year, "subject": subject,
                                 "rank": cells[2 + 2 * k], "country": country,
                                 "score": cells[1 + 2 * k]})
    if not rows:
        raise ValueError("No PISA ranking table found")
    return pd.DataFrame(rows, columns=["source", "year", "subject", "rank", "country", "score"])


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace("—", "", regex=False), errors="coerce")


def validate_pisa_raw(df: pd.DataFrame) -> None:
    """Sanity-check a raw PISA table; raise ValueError listing every problem.

    Catches silent mis-parses after a Wikipedia layout change: missing table
    families, wrong subject/year labels, empty or implausible score columns.
    """
    problems: list[str] = []
    for src in ("summary", "comparison"):
        got = set(df.loc[df["source"] == src, "subject"])
        if got != set(PISA_SUBJECTS.values()):
            problems.append(f"{src}: subjects {sorted(got)} != {sorted(PISA_SUBJECTS.values())}")
    years = _to_num(df["year"])
    bad_year = years.isna() | ~years.between(2000, datetime.now().year)
    if bad_year.any():
        problems.append(f"invalid year values: {sorted(set(df.loc[bad_year, 'year']))}")
    score = _to_num(df["score"])
    out_of_range = score.notna() & ~score.between(PISA_SCORE_MIN, PISA_SCORE_MAX)
    if out_of_range.any():
        problems.append(f"{int(out_of_range.sum())} scores outside "
                        f"[{PISA_SCORE_MIN}, {PISA_SCORE_MAX}]")
    is_avg = df["country"].str.contains("International Average", case=False)
    for (src, subj, year), g in df.groupby(["source", "subject", "year"]):
        countries = g[~is_avg.loc[g.index] & score.loc[g.index].notna()]
        if len(countries) < PISA_MIN_COUNTRIES:
            problems.append(f"{src}/{subj}/{year}: only {len(countries)} countries with a score")
        if _to_num(countries["rank"]).isna().any():
            problems.append(f"{src}/{subj}/{year}: country rows without numeric rank")
        if countries["country"].duplicated().any():
            problems.append(f"{src}/{subj}/{year}: duplicated countries")
        if int(is_avg.loc[g.index].sum()) != 1:
            problems.append(f"{src}/{subj}/{year}: expected exactly 1 OECD average row")
    if problems:
        raise ValueError("PISA validation failed: " + "; ".join(problems))


def _meta_path(out_csv: Path) -> Path:
    return Path(out_csv).with_suffix(".meta.json")


def read_pisa_meta(out_csv: Path) -> dict | None:
    """Provenance of the cached raw PISA CSV (url, revision, scraped_at), if recorded."""
    path = _meta_path(out_csv)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _read_pisa_cache(out_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(out_csv, dtype=str, keep_default_na=False)
    validate_pisa_raw(df)
    return df


def scrape_pisa_table(url: str = PISA_URL, out_csv: Path | None = None,
                      refresh: bool = False) -> pd.DataFrame:
    """Cache-first PISA scrape from Wikipedia into a raw long CSV.

    - Cache exists and refresh=False: read and validate the cache, no network.
    - Otherwise fetch live, parse, validate; only a valid result overwrites the
      cache, together with <out_csv>.meta.json (url, revision id, permalink, time).
    - Live fetch/parse/validation fails: warn and fall back to a valid cache,
      else raise RuntimeError.
    """
    cache = Path(out_csv) if out_csv is not None else None
    if cache is not None and cache.exists() and not refresh:
        return _read_pisa_cache(cache)
    try:
        resp = requests.get(url, timeout=25, headers=HTTP_HEADERS)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        df = _parse_pisa_html(resp.text)
        validate_pisa_raw(df)
    except Exception as exc:
        if cache is not None and cache.exists():
            warnings.warn(f"Live PISA scrape failed ({type(exc).__name__}: {exc}); "
                          f"keeping cached {cache.name}", stacklevel=2)
            return _read_pisa_cache(cache)
        raise RuntimeError(f"PISA scrape failed: {type(exc).__name__}: {exc}") from exc
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache, index=False, encoding="utf-8")
        rev = re.search(r'"wgRevisionId":(\d+)', resp.text)
        meta = {
            "url": url,
            "revision_id": int(rev.group(1)) if rev else None,
            "permalink": (f"https://en.wikipedia.org/w/index.php?oldid={rev.group(1)}"
                          if rev else None),
            "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "n_rows": int(len(df)),
        }
        _meta_path(cache).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return df


def clean_pisa(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise the raw PISA long table: numeric rank/score/year, clean country names."""
    df = raw.copy()
    df["country"] = (df["country"].astype(str)
                     .map(_strip_footnote)
                     .str.replace(r"\s*\*+$", "", regex=True)
                     .str.strip())
    df.loc[df["country"].str.contains("International Average", case=False), "country"] = "OECD average"
    for col in ["year", "rank", "score"]:
        df[col] = _to_num(df[col])
    df = df.dropna(subset=["year", "score"])  # country did not take part that year
    df["year"] = df["year"].astype(int)
    df["score"] = df["score"].astype(int)
    df["rank"] = df["rank"].astype("Int64")
    return (df.drop_duplicates(subset=["year", "subject", "country"])
              .sort_values(["subject", "year", "rank"])
              .reset_index(drop=True))


def cross_check_pisa(pisa: pd.DataFrame, oecd: pd.DataFrame) -> dict:
    """Compare scraped Wikipedia PISA scores with the official OECD Table I.1.

    - OECD_PISA_YEAR scores must match exactly (both are rounded means).
    - The previous cycle (2022) is derived as score - change; because OECD
      computes the change from unrounded means, a difference of 1 is allowed.
    """
    o = oecd.copy()
    o["country"] = o["country"].str.replace(r"\s*\*+$", "", regex=True).str.strip().replace(OECD_NAME_ALIASES)
    rows = []
    for subject in PISA_SUBJECTS.values():
        score, change = _to_num(o[subject]), _to_num(o[f"{subject}_change"])
        rows.append(pd.DataFrame({"country": o["country"], "subject": subject,
                                  "year": OECD_PISA_YEAR, "oecd": score}))
        rows.append(pd.DataFrame({"country": o["country"], "subject": subject,
                                  "year": OECD_PISA_YEAR - 3, "oecd": score - change}))
    ref = pd.concat(rows).dropna(subset=["oecd"])
    merged = ref.merge(pisa[["country", "subject", "year", "score"]],
                       on=["country", "subject", "year"], how="inner")
    merged["diff"] = merged["score"] - merged["oecd"]
    out: dict = {}
    for year, tol in ((OECD_PISA_YEAR, 0), (OECD_PISA_YEAR - 3, 1)):
        g = merged[merged["year"] == year]
        bad = g[g["diff"].abs() > tol]
        out[str(year)] = {
            "tolerance": tol,
            "n_compared": int(len(g)),
            "n_within_tolerance": int(len(g) - len(bad)),
            "n_exact": int((g["diff"] == 0).sum()),
            "max_abs_diff": int(g["diff"].abs().max()) if len(g) else None,
            "mismatches": bad[["country", "subject", "score", "oecd"]].astype(
                {"score": int, "oecd": int}).to_dict("records"),
        }
    latest = pisa[pisa["year"] == OECD_PISA_YEAR]
    official = set(o["country"])
    out["missing_in_wikipedia"] = {
        s: sorted(official - set(latest.loc[latest["subject"] == s, "country"]))
        for s in PISA_SUBJECTS.values()}
    out["missing_in_oecd"] = {
        s: sorted(set(latest.loc[latest["subject"] == s, "country"]) - official)
        for s in PISA_SUBJECTS.values()}
    return out


# ---------------------------------------------------------------------------
# OOP pipeline
# ---------------------------------------------------------------------------
def _grp(df: pd.DataFrame, col: str) -> dict:
    g = df.groupby(col)["G3"].agg(["mean", "std", "count"])
    return {str(k): {"mean": round(float(v["mean"]), 2),
                     "std": round(float(v["std"]), 2) if pd.notna(v["std"]) else 0.0,
                     "n": int(v["count"])}
            for k, v in g.iterrows()}


CORR_COLS = ["G1", "G2", "G3", "studytime", "failures", "absences", "famsup_bin"]


def _p(x: float) -> float:
    """Round a p-value to 3 significant digits (keeps tiny values readable)."""
    return float(f"{x:.3g}")


def _holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values (controls the family-wise error rate)."""
    out, running, m = {}, 0.0, len(pvals)
    for i, (k, p) in enumerate(sorted(pvals.items(), key=lambda kv: kv[1])):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def _group_tests(df: pd.DataFrame) -> dict:
    """Is the G3 difference between groups larger than chance?

    - yes/no columns: Welch t-test (unequal variances), 95% CI of the mean
      difference, Cohen's d effect size.
    - multi-level columns: one-way ANOVA with eta-squared effect size, plus
      Kruskal-Wallis as a check that does not assume normal data.
    All p-values of the family are Holm-adjusted before comparing to ALPHA.
    """
    tests: dict = {}
    for col in BINARY_TEST_COLS:
        yes = df.loc[df[col] == "yes", "G3"].astype(float)
        no = df.loc[df[col] == "no", "G3"].astype(float)
        res = stats.ttest_ind(yes, no, equal_var=False)
        ci = res.confidence_interval(1 - ALPHA)
        pooled_sd = np.sqrt(((len(yes) - 1) * yes.var() + (len(no) - 1) * no.var())
                            / (len(yes) + len(no) - 2))
        diff = yes.mean() - no.mean()
        tests[col] = {"test": "Welch t-test", "n_yes": int(len(yes)), "n_no": int(len(no)),
                      "mean_yes": round(float(yes.mean()), 2), "mean_no": round(float(no.mean()), 2),
                      "diff": round(float(diff), 2),
                      "ci95": [round(float(ci.low), 2), round(float(ci.high), 2)],
                      "stat": round(float(res.statistic), 2), "df": round(float(res.df), 1),
                      "p": _p(res.pvalue), "effect": round(float(diff / pooled_sd), 2),
                      "effect_name": "Cohen's d"}
    for col in MULTI_TEST_COLS:
        cap = TEST_LEVEL_CAP.get(col)
        levels = df[col].clip(upper=cap) if cap is not None else df[col]
        by = df.groupby(levels)
        groups = [g["G3"].astype(float).to_numpy() for _, g in by]
        anova = stats.f_oneway(*groups)
        kw = stats.kruskal(*groups)
        grand = df["G3"].mean()
        ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
        ss_total = float(((df["G3"] - grand) ** 2).sum())
        tests[col] = {"test": "one-way ANOVA", "k_groups": len(groups),
                      "levels": [f"{k}+" if cap is not None and k == cap else str(k) for k in by.groups],
                      "stat": round(float(anova.statistic), 2), "p": _p(anova.pvalue),
                      "effect": round(float(ss_between / ss_total), 3), "effect_name": "eta²",
                      "kruskal_H": round(float(kw.statistic), 2), "p_kruskal": _p(kw.pvalue)}
    adjusted = _holm({k: v["p"] for k, v in tests.items()})
    for k, v in tests.items():
        v["p_holm"] = _p(adjusted[k])
        v["significant"] = bool(adjusted[k] < ALPHA)
    return tests


def _corr_tests(df: pd.DataFrame) -> dict:
    """Pearson r with G3: p-value and 95% CI for each variable."""
    out = {}
    for col in CORR_TEST_COLS:
        res = stats.pearsonr(df[col].astype(float), df["G3"].astype(float))
        ci = res.confidence_interval(1 - ALPHA)
        out[col] = {"r": round(float(res.statistic), 3), "p": _p(res.pvalue),
                    "ci95": [round(float(ci.low), 3), round(float(ci.high), 3)]}
    return out


def _ols(df: pd.DataFrame, cols: list[str]) -> dict:
    """Linear regression of G3 on `cols` with HC3 heteroskedasticity-robust standard errors.

    Each coefficient b = expected change in G3 (points) for +1 unit of that column while
    every other column stays fixed. `male` and `urban` are 0/1 versions of sex / address.
    """
    X = df.assign(male=(df["sex"] == "M").astype(int),
                  urban=(df["address"] == "U").astype(int))[cols].astype(float).to_numpy()
    y = df["G3"].astype(float).to_numpy()
    A = np.column_stack([np.ones(len(y)), X])
    n, k = A.shape
    xtx_inv = np.linalg.inv(A.T @ A)
    beta = xtx_inv @ A.T @ y
    resid = y - A @ beta
    leverage = np.einsum("ij,jk,ik->i", A, xtx_inv, A)
    meat = A.T @ (A * (resid ** 2 / (1 - leverage) ** 2)[:, None])
    se = np.sqrt(np.diag(xtx_inv @ meat @ xtx_inv))
    dof = n - k
    p = 2 * stats.t.sf(np.abs(beta / se), dof)
    q = stats.t.ppf(1 - ALPHA / 2, dof)
    r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    return {
        "n": int(n), "n_predictors": int(k - 1),
        "r2": round(float(r2), 3), "adj_r2": round(float(1 - (1 - r2) * (n - 1) / dof), 3),
        "coef": {name: {"b": round(float(b), 3), "se": round(float(s), 3),
                        "ci95": [round(float(b - q * s), 3), round(float(b + q * s), 3)],
                        "p": _p(pv), "significant": bool(pv < ALPHA)}
                 for name, b, s, pv in zip(["intercept"] + cols, beta, se, p)},
    }



def _paired_subjects(clean: pd.DataFrame, a: str, b: str) -> dict:
    """Same pupils in courses a and b: compare their G3 pairwise instead of as two independent groups.

    Pupils are matched on MERGE_KEYS (as in student-merge.R). Keys that repeat inside one
    course cannot be matched safely, so those rows are left out. Pairs where either
    course is a dropout suspect (G3 = 0) are excluded from the grade comparison.
    """
    def unique_rows(subj: str) -> tuple[pd.DataFrame, int]:
        g = clean[clean["subject"] == subj]
        dup = g.duplicated(MERGE_KEYS, keep=False)
        return g[~dup], int(dup.sum())

    ga, dup_a = unique_rows(a)
    gb, dup_b = unique_rows(b)
    pairs = ga.merge(gb, on=MERGE_KEYS, suffixes=(f"_{a}", f"_{b}"))
    ok = pairs[~pairs[f"dropout_suspect_{a}"] & ~pairs[f"dropout_suspect_{b}"]]
    x, y = ok[f"G3_{a}"].astype(float), ok[f"G3_{b}"].astype(float)
    t = stats.ttest_rel(x, y)
    ci = t.confidence_interval(1 - ALPHA)
    return {
        "n_a": int((clean["subject"] == a).sum()), "n_b": int((clean["subject"] == b).sum()),
        "n_duplicate_keys_a": dup_a, "n_duplicate_keys_b": dup_b,
        "n_matched": int(len(pairs)), "n_pairs": int(len(ok)),
        "mean_G3_a": round(float(x.mean()), 2), "mean_G3_b": round(float(y.mean()), 2),
        "diff": round(float((x - y).mean()), 2),
        "ci95": [round(float(ci.low), 2), round(float(ci.high), 2)],
        "p_ttest": _p(t.pvalue), "p_wilcoxon": _p(stats.wilcoxon(x, y).pvalue),
        "significant": bool(t.pvalue < ALPHA),
        "corr_G3": round(float(x.corr(y)), 3),
    }


def _scope_stats(df: pd.DataFrame) -> dict:
    corr = df[CORR_COLS].astype(float).corr().round(3)
    return {
        "n": int(len(df)),
        "pass_rate": round(float((df["pass_fail"] == "pass").mean()), 4),
        "n_pass": int((df["pass_fail"] == "pass").sum()),
        "n_fail": int((df["pass_fail"] == "fail").sum()),
        "by_studytime": _grp(df, "studytime"),
        "by_absence_level": _grp(df, "absence_level"),
        "by_failures": _grp(df, "failures"),
        "by_internet": _grp(df, "internet"),
        "by_studytime_internet": _grp(df.assign(st_net=df["studytime"].astype(str) + "|" + df["internet"]),
                                      "st_net"),
        "by_famsup": _grp(df, "famsup"),
        "by_schoolsup": _grp(df, "schoolsup"),
        "by_paid": _grp(df, "paid"),
        "by_risk_group": _grp(df, "risk_group"),
        "corr_G1_G2_G3": {
            "G1_G2": float(corr.loc["G1", "G2"]),
            "G1_G3": float(corr.loc["G1", "G3"]),
            "G2_G3": float(corr.loc["G2", "G3"]),
        },
        "corr_full": corr.to_dict(),
        "group_tests": _group_tests(df),
        "corr_tests": _corr_tests(df),
    }


def _wilson(k: int, n: int) -> list[float]:
    """95% Wilson confidence interval of a proportion k/n."""
    if n == 0:
        return [0.0, 0.0]
    ci = stats.binomtest(k, n).proportion_ci(1 - ALPHA, method="wilson")
    return [round(float(ci.low), 4), round(float(ci.high), 4)]


def _risk_eval(df: pd.DataFrame) -> dict:
    """Confusion counts of risk flags vs. actual fail (G3 < PASS_MARK), with 95% Wilson CIs."""
    actual = df["pass_fail"] == "fail"
    out = {"n": int(len(df)), "fail_rate": round(float(actual.mean()), 4),
           "fail_rate_by_group": {
               g: round(float(actual[df["risk_group"] == g].mean()), 4)
               for g in ["low", "medium", "high"] if (df["risk_group"] == g).any()},
           "tiers": _tier_eval(df, actual)}
    for name, flagged in {"high": df["risk_group"] == "high",
                          "high_or_medium": df["risk_group"] != "low"}.items():
        tp = int((flagged & actual).sum())
        fp = int((flagged & ~actual).sum())
        fn = int((~flagged & actual).sum())
        tn = int((~flagged & ~actual).sum())
        out[name] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                     "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
                     "precision_ci95": _wilson(tp, tp + fp),
                     "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
                     "recall_ci95": _wilson(tp, tp + fn)}
    return out


def _tier_eval(df: pd.DataFrame, actual: pd.Series) -> dict:
    """Does each risk tier carry information? Fail rate (Wilson CI) per tier, and
    Fisher's exact test of medium vs low (is 'medium' really riskier than 'low'?)."""
    out: dict = {}
    for g in ["low", "medium", "high"]:
        m = df["risk_group"] == g
        k, n = int((actual & m).sum()), int(m.sum())
        out[g] = {"n": n, "n_fail": k, "fail_rate": round(k / n, 4) if n else 0.0,
                  "fail_rate_ci95": _wilson(k, n)}
    lo, me = out["low"], out["medium"]
    table = [[me["n_fail"], me["n"] - me["n_fail"]], [lo["n_fail"], lo["n"] - lo["n_fail"]]]
    fisher = stats.fisher_exact(table)
    out["medium_vs_low"] = {
        "odds_ratio": round(float(fisher.statistic), 2) if np.isfinite(fisher.statistic) else None,
        "relative_risk": round(me["fail_rate"] / lo["fail_rate"], 1) if lo["fail_rate"] else None,
        "p": _p(fisher.pvalue), "significant": bool(fisher.pvalue < ALPHA)}
    return out


class StudentDataProcessor:
    """Load -> clean -> analyze -> export for UCI student data + PISA reference."""

    def __init__(self, raw_paths: dict[str, Path], pisa_raw: Path | None,
                 processed_dir: Path, images_dir: Path, primary_subject: str = "mat",
                 oecd_raw: Path | None = None):
        self.raw_paths = {k: Path(v) for k, v in raw_paths.items()}
        self.pisa_raw = Path(pisa_raw) if pisa_raw is not None else None
        self.oecd_raw = Path(oecd_raw) if oecd_raw is not None else None
        self.processed_dir = Path(processed_dir)
        self.images_dir = Path(images_dir)
        self.primary_subject = primary_subject
        self.df: pd.DataFrame | None = None
        self.pisa_df: pd.DataFrame | None = None
        self.oecd_df: pd.DataFrame | None = None
        self.clean: pd.DataFrame | None = None
        self.pisa_clean: pd.DataFrame | None = None
        self.cleaning_log: dict = {}
        self.results: dict = {}

    # -- step 1: load ----------------------------------------------------
    def load_data(self) -> pd.DataFrame:
        frames = []
        for subject, path in self.raw_paths.items():
            part = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)
            part.insert(0, "subject", subject)
            frames.append(part)
        self.df = pd.concat(frames, ignore_index=True)
        if self.pisa_raw is not None and self.pisa_raw.exists():
            self.pisa_df = pd.read_csv(self.pisa_raw, dtype=str, keep_default_na=False)
        if self.oecd_raw is not None and self.oecd_raw.exists():
            self.oecd_df = pd.read_csv(self.oecd_raw, dtype=str, keep_default_na=False)
        return self.df

    # -- step 2: clean ---------------------------------------------------
    def clean_data(self) -> pd.DataFrame:
        assert self.df is not None, "call load_data() first"
        df = self.df.copy()
        log: dict = {"rows_in": int(len(df))}

        # 1) whitespace
        str_cols = [c for c in df.columns if c not in VALID_RANGES]
        stripped = df[str_cols].apply(lambda s: s.str.strip())
        log["n_cells_stripped"] = int((stripped != df[str_cols]).sum().sum())
        df[str_cols] = stripped

        # 2) numeric casts + domain checks (bad values -> NaN)
        log["n_non_numeric"], log["n_out_of_range"] = {}, {}
        for col, (lo, hi) in VALID_RANGES.items():
            num = pd.to_numeric(df[col], errors="coerce")
            log["n_non_numeric"][col] = int((num.isna() & (df[col] != "")).sum())
            bad = num.notna() & ~num.between(lo, hi)
            log["n_out_of_range"][col] = int(bad.sum())
            df[col] = num.mask(bad)

        # 3) yes/no encoding with validation
        log["n_invalid_yes_no"] = {}
        for col in YES_NO_COLS:
            enc = df[col].map(convert_yes_no)
            log["n_invalid_yes_no"][col] = int(enc.isna().sum())
            df[col + "_bin"] = enc.astype("Int64")

        # 4) duplicates (within subject) + missing required values
        before = len(df)
        df = df.drop_duplicates()
        log["n_duplicates_dropped"] = int(before - len(df))
        before = len(df)
        df = df.dropna(subset=REQUIRED_COLS).reset_index(drop=True)
        log["n_missing_required_dropped"] = int(before - len(df))
        for col in VALID_RANGES:
            if df[col].notna().all():
                df[col] = df[col].astype(int)

        # 5) derived columns
        df["pass_fail"] = df["G3"].apply(calc_pass_fail)
        df["absence_level"] = df["absences"].apply(classify_absences)
        df["avg_grade"] = df.apply(
            lambda r: calc_average_grade(r["G1"], r["G2"], r["G3"]), axis=1).round(2)
        df["avg_g1g2"] = ((df["G1"] + df["G2"]) / 2).round(2)
        df["risk_group"] = df.apply(classify_risk, axis=1)

        # 6) anomaly flags (flag, never delete); absence fence per subject
        q = df.groupby("subject")["absences"].quantile([0.25, 0.75]).unstack()
        fences = (q[0.75] + IQR_K * (q[0.75] - q[0.25])).to_dict()
        df["dropout_suspect"] = df["G3"] == 0
        df["g2_zero"] = df["G2"] == 0
        df["grade_drop"] = (((df["G1"] - df["G3"]) >= G1_DROP) | ((df["G2"] - df["G3"]) >= G2_DROP)) \
            & ~df["dropout_suspect"]
        df["absence_outlier"] = df["absences"] > df["subject"].map(fences)
        df["age_outlier"] = df["age"] >= AGE_OUTLIER
        df["inconsistent_grade"] = (df["G3"] > 0) & (df["G2"] == 0)
        log["absence_outlier_fence"] = {k: float(v) for k, v in fences.items()}
        log["rows_out"] = int(len(df))

        self.clean = df
        self.cleaning_log = log
        if self.pisa_df is not None:
            self.pisa_clean = clean_pisa(self.pisa_df)
        return df

    # -- step 3: analyze -------------------------------------------------
    def analyze(self) -> dict:
        assert self.clean is not None, "call clean_data() first"
        df = self.clean[self.clean["subject"] == self.primary_subject]
        core = df[~df["dropout_suspect"]]

        self.results = {
            "primary_subject": self.primary_subject,
            # set() uniques (rubric)
            "unique_schools": sorted(set(df["school"])),
            "unique_mjobs": sorted(set(df["Mjob"])),
            "unique_fjobs": sorted(set(df["Fjob"])),
            "thresholds": list(THRESHOLDS),
            "anomaly_thresholds": list(ANOMALY_THRESHOLDS),
            "cleaning_log": self.cleaning_log,
            "anomaly_counts": {
                subj: {f: int(g[f].sum()) for f in FLAG_COLS}
                for subj, g in self.clean.groupby("subject")},
            "scopes": {"all": _scope_stats(df), "exclude_dropout": _scope_stats(core)},
            "risk_eval": {"all": _risk_eval(df), "exclude_dropout": _risk_eval(core),
                          **self._risk_holdout()},
            "subject_comparison": self._subject_comparison(),
            "subject_paired": {subj: _paired_subjects(self.clean, self.primary_subject, subj)
                               for subj in sorted(set(self.clean["subject"]) - {self.primary_subject})},
            "regression": self._regression(),
            "sensitivity": self._sensitivity(),
            "dropout_profile": {
                "n": int(df["dropout_suspect"].sum()),
                "n_absences_zero": int((df.loc[df["dropout_suspect"], "absences"] == 0).sum()),
                "n_g2_zero": int((df.loc[df["dropout_suspect"], "G2"] == 0).sum()),
                "mean_G1": round(float(df.loc[df["dropout_suspect"], "G1"].mean()), 2),
                "mean_G2": round(float(df.loc[df["dropout_suspect"], "G2"].mean()), 2),
                "share_absences_zero_others": round(float(
                    (df.loc[~df["dropout_suspect"], "absences"] == 0).mean()), 4),
            },
        }
        if self.pisa_clean is not None:
            self.results["pisa_context"] = self._pisa_context()
            self.results["pisa_source"] = read_pisa_meta(self.pisa_raw)
            if self.oecd_df is not None:
                self.results["pisa_oecd_check"] = cross_check_pisa(self.pisa_clean, self.oecd_df)
                self.results["pisa_oecd_source"] = read_pisa_meta(self.oecd_raw)
        self._plot_charts(df, core)
        return self.results

    def _regression(self) -> dict:
        """Multivariable OLS per subject (dropout suspects excluded).

        factors: background variables only (what predicts G3 before any grade is known);
        factors_plus_grades: the same plus G1, G2 (what still matters once grades are known).
        """
        out: dict = {}
        for subj, g in self.clean.groupby("subject"):
            core = g[~g["dropout_suspect"]]
            out[subj] = {"factors": _ols(core, REG_FACTORS),
                         "factors_plus_grades": _ols(core, REG_FACTORS + REG_GRADES)}
        return out

    def _sensitivity(self) -> dict:
        """Does the absences finding survive different assumptions about the zeros?

        - all: keep every student;
        - exclude_dropout: drop G3 = 0 (dropout suspects);
        - exclude_dropout_and_zero_absences: also drop absences = 0, in case 0 means
          'not recorded' rather than 'never absent'.
        """
        out: dict = {}
        for subj, g in self.clean.groupby("subject"):
            scenarios = {
                "all": g,
                "exclude_dropout": g[~g["dropout_suspect"]],
                "exclude_dropout_and_zero_absences": g[~g["dropout_suspect"] & (g["absences"] > 0)],
            }
            res = {}
            for name, d in scenarios.items():
                r = stats.pearsonr(d["absences"].astype(float), d["G3"].astype(float))
                ci = r.confidence_interval(1 - ALPHA)
                levels = [x["G3"].astype(float).to_numpy() for _, x in d.groupby("absence_level")]
                res[name] = {
                    "n": int(len(d)),
                    "r_absences_G3": round(float(r.statistic), 3), "p": _p(r.pvalue),
                    "ci95": [round(float(ci.low), 3), round(float(ci.high), 3)],
                    "mean_G3_by_absence_level": {
                        k: round(float(x["G3"].mean()), 2) for k, x in d.groupby("absence_level")},
                    "anova_p": _p(stats.f_oneway(*levels).pvalue),
                    "pass_rate": round(float((d["pass_fail"] == "pass").mean()), 4),
                }
            drop = g[g["dropout_suspect"]]
            res["dropout_pattern"] = {"n_dropout": int(len(drop)),
                                      "n_dropout_absences_zero": int((drop["absences"] == 0).sum()),
                                      "share_absences_zero_others": round(float(
                                          (g.loc[~g["dropout_suspect"], "absences"] == 0).mean()), 4)}
            out[subj] = res
        return out

    def _risk_holdout(self) -> dict:
        """Evaluate the frozen risk rule on the other subject(s) (out-of-sample).

        The rule thresholds were chosen on the primary subject, so other
        subjects act as holdout data. `holdout_<s>_only` keeps only students
        whose MERGE_KEYS do not appear in the primary subject (no shared pupils).
        """
        primary = self.clean[self.clean["subject"] == self.primary_subject]
        seen = set(map(tuple, primary[MERGE_KEYS].astype(str).to_numpy()))
        out: dict = {}
        for subj, g in self.clean.groupby("subject"):
            if subj == self.primary_subject:
                continue
            shared = g[MERGE_KEYS].astype(str).apply(tuple, axis=1).isin(seen)
            out[f"holdout_{subj}"] = _risk_eval(g)
            out[f"holdout_{subj}_only"] = _risk_eval(g[~shared])
        return out

    def _subject_comparison(self) -> dict:
        out = {}
        for subj, g in self.clean.groupby("subject"):
            core = g[~g["dropout_suspect"]]
            out[subj] = {
                "n": int(len(g)),
                "n_dropout_suspect": int(g["dropout_suspect"].sum()),
                "pass_rate": round(float((g["pass_fail"] == "pass").mean()), 4),
                "mean_G3": round(float(g["G3"].mean()), 2),
                "mean_G3_exclude_dropout": round(float(core["G3"].mean()), 2),
                "corr_G2_G3_exclude_dropout": round(float(core["G2"].corr(core["G3"])), 3),
                "corr_absences_G3_exclude_dropout": round(float(core["absences"].corr(core["G3"])), 3),
                "corr_failures_G3_exclude_dropout": round(float(core["failures"].corr(core["G3"])), 3),
            }
        return out

    def _pisa_context(self) -> dict:
        """Portugal vs OECD average per subject/year (country-level context only)."""
        p = self.pisa_clean
        sel = p[p["country"].isin(["Portugal", "OECD average"])]
        out: dict = {}
        for (subject, year), g in sel.groupby(["subject", "year"]):
            by = g.set_index("country")
            if "Portugal" not in by.index:
                continue
            row = {"portugal": int(by.loc["Portugal", "score"]),
                   "portugal_rank": (int(by.loc["Portugal", "rank"])
                                     if pd.notna(by.loc["Portugal", "rank"]) else None)}
            if "OECD average" in by.index:
                row["oecd_average"] = int(by.loc["OECD average", "score"])
            out.setdefault(subject, {})[str(year)] = row
        return out

    def _plot_charts(self, df: pd.DataFrame, core: pd.DataFrame) -> None:
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self._plot_bar(df, core)
        self._plot_hist(df, core)
        self._plot_heatmap(df, core)
        if self.pisa_clean is not None:
            self._plot_pisa()
    def _save_fig(self, fig, filename: str) -> None:
        target = self.images_dir / filename
        try:
            fig.savefig(target, dpi=150)
        except PermissionError as exc:
            raise PermissionError(
                f"Cannot save chart '{filename}': file is locked by an image viewer. "
                f"Please close the viewer and retry (Đóng file ảnh đang mở rồi chạy lại)."
            ) from exc
        finally:
            plt.close(fig)


    def _plot_bar(self, df: pd.DataFrame, core: pd.DataFrame) -> None:
        """Chart 1: grouped bar - mean G3 by studytime x internet, 95% CI + n."""
        n_drop = int(df["dropout_suspect"].sum())
        stats = core.groupby(["studytime", "internet"])["G3"].agg(["mean", "std", "count"])
        stats["ci"] = 1.96 * stats["std"].fillna(0) / np.sqrt(stats["count"])
        levels = sorted(core["studytime"].unique())
        fig, ax = plt.subplots(figsize=(8, 5))
        width = 0.38
        for k, net in enumerate(["no", "yes"]):
            xs, means, cis, ns = [], [], [], []
            for i, lvl in enumerate(levels):
                if (lvl, net) in stats.index:
                    s = stats.loc[(lvl, net)]
                    xs.append(i + (k - 0.5) * width)
                    means.append(s["mean"]); cis.append(s["ci"]); ns.append(int(s["count"]))
            bars = ax.bar(xs, means, width, yerr=cis, capsize=4, label=net,
                          color=f"C{k}", edgecolor="black", linewidth=0.5)
            for b, n, ci in zip(bars, ns, cis):
                if n < MIN_RELIABLE_N:
                    b.set_alpha(0.4)
                    b.set_hatch("//")
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + ci + 0.2,
                        f"n={n}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(range(len(levels)), ["<2h", "2-5h", "5-10h", ">10h"], rotation=0)
        ax.set_title(f"Mean final grade (G3) by weekly studytime and internet access\n"
                     f"(excluding {n_drop} dropout suspects with G3 = 0; bars = 95% CI; hatched = n < {MIN_RELIABLE_N})")
        ax.set_xlabel("Weekly studytime")
        ax.set_ylabel("Mean G3 (0-20)")
        ax.set_ylim(0, 20)
        handles, _ = ax.get_legend_handles_labels()
        handles.append(Patch(facecolor="white", edgecolor="black", hatch="//",
                             label=f"n < {MIN_RELIABLE_N}: unreliable"))
        ax.legend(handles=handles, title="Internet at home", loc="upper left")
        fig.tight_layout()
        self._save_fig(fig, "01_bar_studytime_internet.png")

    def _plot_hist(self, df: pd.DataFrame, core: pd.DataFrame) -> None:
        """Chart 2: histogram - G3 distribution, one bin per integer grade."""
        n_drop = int(df["dropout_suspect"].sum())
        fig, ax = plt.subplots(figsize=(8, 5))
        bins = np.arange(-0.5, 21.5, 1)
        ax.hist(core["G3"], bins=bins, edgecolor="black", color="C0", label="G3 > 0")
        ax.hist(df.loc[df["dropout_suspect"], "G3"], bins=bins, edgecolor="black",
                color="C3", label=f"Dropout suspect, G3 = 0 (n={n_drop})")
        ax.axvline(PASS_MARK - 0.5, color="black", linestyle="--",
                   label=f"Pass mark = {PASS_MARK}")
        pass_all = (df["pass_fail"] == "pass").mean()
        pass_core = (core["pass_fail"] == "pass").mean()
        ax.text(0.98, 0.70, f"Pass rate: {pass_all:.1%} (all)\n"
                            f"{pass_core:.1%} (excl. dropout)",
                transform=ax.transAxes, ha="right", va="top", fontsize=9)
        ax.set_xticks(range(0, 21, 2))
        ax.set_title(f"Distribution of final grades (G3), n={len(df)}")
        ax.set_xlabel("G3 (0-20)")
        ax.set_ylabel("Students")
        ax.legend()
        fig.tight_layout()
        self._save_fig(fig, "02_hist_g3.png")

    def _plot_heatmap(self, df: pd.DataFrame, core: pd.DataFrame) -> None:
        """Chart 3: heatmap - Pearson correlation (excluding dropout), diverging colormap."""
        n_drop = int(df["dropout_suspect"].sum())
        corr = core[CORR_COLS].astype(float).corr()
        labels = [c.replace("_bin", "") for c in CORR_COLS]
        fig, ax = plt.subplots(figsize=(7.5, 6.5))
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        im = ax.imshow(np.ma.array(corr.values, mask=mask), cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
        ax.set_yticks(range(len(labels)), labels)
        for i in range(len(labels)):
            for j in range(i + 1):
                v = corr.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if abs(v) > 0.6 else "black")
        ax.set_title(f"Pearson correlation (excluding {n_drop} dropout suspects, n={len(core)})")
        fig.colorbar(im, ax=ax, shrink=0.8)
        fig.tight_layout()
        self._save_fig(fig, "03_heatmap_corr.png")

    def _plot_pisa(self) -> None:
        """Chart 4 (context): Portugal vs OECD average PISA score per subject over time."""
        p = self.pisa_clean
        fig, axes = plt.subplots(1, 3, figsize=(12, 4.6), sharey=True)
        styles = {"Portugal": dict(color="C0", marker="o", lw=2),
                  "OECD average": dict(color="gray", marker="s", ls="--", lw=1.5)}
        for ax, subject in zip(axes, ["mathematics", "reading", "science"]):
            series = {c: p[(p["subject"] == subject) & (p["country"] == c)].sort_values("year")
                      for c in styles}
            last = {c: s.iloc[-1] for c, s in series.items()}
            higher = max(last, key=lambda c: last[c]["score"])
            for country, s in series.items():
                ax.plot(s["year"], s["score"], label=country, **styles[country])
                ax.annotate(f"{last[country]['score']}", (last[country]["year"], last[country]["score"]),
                            textcoords="offset points", xytext=(6, 5 if country == higher else -11),
                            fontsize=8, color=styles[country]["color"])
            ax.axvspan(2005, 2006, color="C1", alpha=0.25,
                       label="UCI cohort (2005–06)" if subject == "mathematics" else None)
            ax.set_title(subject.capitalize())
            ax.set_xlabel("PISA cycle (year)")
            ax.set_xticks(sorted(p.loc[p["subject"] == subject, "year"].unique()))
            ax.tick_params(axis="x", rotation=45)
            ax.set_xlim(right=ax.get_xlim()[1] + 2)
            ax.grid(alpha=0.3)
        axes[0].set_ylabel("Mean PISA score")
        fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=9)
        fig.suptitle("PISA mean score: Portugal vs OECD average (source: Wikipedia, cross-checked with OECD)")
        fig.tight_layout(rect=(0, 0.07, 1, 1))
        self._save_fig(fig, "04_pisa_portugal_oecd.png")

    # -- step 4: export --------------------------------------------------
    def export_results(self) -> tuple[Path, Path]:
        assert self.clean is not None and self.results, "run clean+analyze first"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        cleaned_csv = self.processed_dir / "cleaned_students.csv"
        cleaned_mat_csv = self.processed_dir / "cleaned_students_mat.csv"
        cleaned_por_csv = self.processed_dir / "cleaned_students_por.csv"
        summary_json = self.processed_dir / "summary.json"
        pisa_csv = self.processed_dir / "pisa_clean.csv"
        try:
            self.clean.to_csv(cleaned_csv, index=False)
            self.clean[self.clean["subject"] == "mat"].to_csv(cleaned_mat_csv, index=False)
            self.clean[self.clean["subject"] == "por"].to_csv(cleaned_por_csv, index=False)
            if self.pisa_clean is not None:
                self.pisa_clean.to_csv(pisa_csv, index=False)
            with open(summary_json, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
        except PermissionError as exc:
            raise PermissionError(
                f"Cannot write output files in '{self.processed_dir}': file is locked by another program (Excel/WPS). "
                f"Please close the file and retry (Đóng file trong Excel/WPS rồi chạy lại)."
            ) from exc
        return cleaned_csv, summary_json
