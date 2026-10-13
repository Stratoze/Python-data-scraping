from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import requests

import data_processor as dp
from conftest import valid_pisa_raw


# ---------------------------------------------------------------------------
# 4 basic functions: boundaries that decide pass/fail and absence buckets
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("g3, expected", [(9, "fail"), (9.99, "fail"), (10, "pass"), (20, "pass")])
def test_pass_mark_boundary(g3, expected):
    assert dp.calc_pass_fail(g3) == expected


@pytest.mark.parametrize("n, expected", [(0, "low"), (3, "low"), (4, "medium"), (9, "medium"),
                                         (10, "high"), (75, "high")])
def test_absence_bucket_boundaries(n, expected):
    assert dp.classify_absences(n) == expected


@pytest.mark.parametrize("value, expected", [("yes", 1), (" YES ", 1), ("no", 0), ("No", 0),
                                             ("maybe", None), ("", None), (None, None)])
def test_yes_no_rejects_unknown_values(value, expected):
    assert dp.convert_yes_no(value) == expected


# ---------------------------------------------------------------------------
# Risk rule: no leakage from G3, threshold precedence
# ---------------------------------------------------------------------------
def _risk(**kw):
    row = {"G1": 14, "G2": 14, "G3": 14, "failures": 0, "absences": 0} | kw
    return dp.classify_risk(pd.Series(row))


def test_risk_rule_ignores_final_grade():
    for g3 in (0, 9, 10, 20):
        assert _risk(G3=g3) == "low"
        assert _risk(G2=9, G3=g3) == "high"


@pytest.mark.parametrize("kw, expected", [
    ({"G2": 9}, "high"), ({"failures": 2}, "high"), ({"G1": 9, "G2": 9}, "high"),
    ({"G1": 9}, "medium"), ({"failures": 1}, "medium"), ({"absences": 10}, "medium"),
    ({"absences": 9}, "low"), ({"G1": 10, "G2": 10}, "low"),
])
def test_risk_rule_thresholds(kw, expected):
    assert _risk(**kw) == expected


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------
def test_holm_adjustment_is_monotone_and_capped():
    adj = dp._holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.9})
    # sorted: a .01*4=.04, c .03*3=.09, b .04*2=.08 -> raised to .09, d .9*1 -> .9
    assert adj == pytest.approx({"a": 0.04, "c": 0.09, "b": 0.09, "d": 0.9})
    assert dp._holm({"x": 0.6, "y": 0.7}) == {"x": 1.0, "y": 1.0}  # capped at 1


def test_wilson_interval_bounds():
    low, high = dp._wilson(64, 70)
    assert 0 < low < 64 / 70 < high < 1
    assert dp._wilson(0, 0) == [0.0, 0.0]
    assert dp._wilson(10, 10)[1] == pytest.approx(1.0)


def test_ols_recovers_known_effects_with_others_held_fixed():
    rng = np.random.default_rng(0)
    n = 400
    studytime = rng.integers(1, 5, n)
    absences = rng.integers(0, 30, n)
    sex = rng.choice(["F", "M"], n)
    # absences correlated with studytime, so a single-variable slope would be biased
    absences = absences + 3 * studytime
    g3 = 8 + 1.5 * studytime - 0.2 * absences + 0.7 * (sex == "M") + rng.normal(0, 1, n)
    df = pd.DataFrame({"studytime": studytime, "absences": absences, "sex": sex,
                       "address": "U", "G3": g3})
    res = dp._ols(df, ["studytime", "absences", "male"])
    for name, true in {"studytime": 1.5, "absences": -0.2, "male": 0.7}.items():
        c = res["coef"][name]
        assert c["ci95"][0] < true < c["ci95"][1]
        assert c["significant"]
    assert 0.5 < res["r2"] <= 1 and res["n"] == n and res["n_predictors"] == 3


def test_tier_eval_detects_medium_riskier_than_low():
    groups = ["low"] * 200 + ["medium"] * 100 + ["high"] * 100
    fails = [False] * 199 + [True] + [False] * 85 + [True] * 15 + [True] * 70 + [False] * 30
    df = pd.DataFrame({"risk_group": groups})
    t = dp._tier_eval(df, pd.Series(fails))
    assert (t["low"]["n_fail"], t["medium"]["n_fail"], t["high"]["n_fail"]) == (1, 15, 70)
    assert t["medium_vs_low"]["relative_risk"] == 30.0
    assert t["medium_vs_low"]["significant"]
    same = dp._tier_eval(df, pd.Series([g == "high" or i % 50 == 0 for i, g in enumerate(groups)]))
    assert not same["medium_vs_low"]["significant"]


# ---------------------------------------------------------------------------
# PISA scraping: parse, validate, clean, cross-check, cache-first
# ---------------------------------------------------------------------------
PISA_HTML = """
<h2>PISA 2025 ranking summary</h2>
<table class="wikitable"><tbody>
 <tr><th>Science [29]</th><th>Mathematics [29]</th></tr>
 <tr><td>
  <table class="wikitable"><tbody>
   <tr><th>Rank</th><th>Country/economy</th><th>Score</th></tr>
   <tr><td>1</td><td>Alpha *</td><td>560</td></tr>
   <tr><td>International Average (OECD)</td><td>482</td></tr>
  </tbody></table></td>
  <td>
  <table class="wikitable"><tbody>
   <tr><th>Rank</th><th>Country/economy</th><th>Score</th></tr>
   <tr><td>1</td><td>Beta</td><td>600</td></tr>
  </tbody></table></td></tr>
</tbody></table>
<h3>Rankings comparison 2000–2022</h3>
<table class="wikitable"><tbody>
 <tr><th colspan="5">Mathematics</th></tr>
 <tr><th>Country</th><th>2022 [41]</th><th>2018</th></tr>
 <tr><th>Score</th><th>Rank</th><th>Score</th><th>Rank</th></tr>
 <tr><td>Portugal</td><td>472</td><td>29</td><td>492</td><td>28</td></tr>
 <tr><td>Gamma</td><td>401</td><td>60</td><td>—</td><td>—</td></tr>
</tbody></table>
"""


def test_parse_pisa_html_maps_subjects_years_and_oecd_row():
    rows = set(dp._parse_pisa_html(PISA_HTML).itertuples(index=False, name=None))
    assert rows == {
        # (source, year, subject, rank, country, score) — page strings kept as-is
        ("summary", "2025", "science", "1", "Alpha *", "560"),
        ("summary", "2025", "science", "", "International Average (OECD)", "482"),
        ("summary", "2025", "mathematics", "1", "Beta", "600"),
        ("comparison", "2022", "mathematics", "29", "Portugal", "472"),
        ("comparison", "2018", "mathematics", "28", "Portugal", "492"),
        ("comparison", "2022", "mathematics", "60", "Gamma", "401"),
        ("comparison", "2018", "mathematics", "—", "Gamma", "—"),
    }


def test_validate_pisa_accepts_complete_table():
    dp.validate_pisa_raw(valid_pisa_raw())


@pytest.mark.parametrize("break_it, message", [
    (lambda d: d[~((d.source == "summary") & (d.subject == "reading"))], "subjects"),
    (lambda d: d.assign(year=d.year.where(d.source != "summary", "")), "invalid year"),
    (lambda d: d.assign(score=d.score.where(d.country != "Country 0", "950")), "outside"),
    (lambda d: d[~d.country.str.contains("International Average")], "OECD average"),
    (lambda d: d[~d.country.isin([f"Country {i}" for i in range(5)])], "only"),
    (lambda d: d.assign(rank=d["rank"].where(d.country != "Country 3", "—")), "without numeric rank"),
])
def test_validate_pisa_rejects_broken_tables(break_it, message):
    with pytest.raises(ValueError, match=message):
        dp.validate_pisa_raw(break_it(valid_pisa_raw()))


def test_clean_pisa_normalises_names_and_drops_non_participants():
    raw = pd.DataFrame([
        {"source": "comparison", "year": "2022", "subject": "mathematics", "rank": "9", "country": "Canada *", "score": "497"},
        {"source": "comparison", "year": "2022", "subject": "mathematics", "rank": "—", "country": "Gamma [a]", "score": "—"},
        {"source": "summary", "year": "2025", "subject": "mathematics", "rank": "", "country": "International Average (OECD)", "score": "463"},
    ])
    out = dp.clean_pisa(raw)
    assert set(out["country"]) == {"Canada", "OECD average"}
    assert out.loc[out.country == "Canada", "score"].item() == 497
    assert pd.isna(out.loc[out.country == "OECD average", "rank"].item())


def test_cross_check_pisa_flags_only_real_mismatches():
    oecd = pd.DataFrame([{"country": "Korea", "science": "526", "reading": "501", "mathematics": "522",
                          "science_change": "-2", "reading_change": "-15", "mathematics_change": "m"}])
    pisa = pd.DataFrame([
        {"country": "South Korea", "subject": "science", "year": 2025, "score": 526},
        {"country": "South Korea", "subject": "reading", "year": 2025, "score": 501},
        {"country": "South Korea", "subject": "mathematics", "year": 2025, "score": 523},
        {"country": "South Korea", "subject": "science", "year": 2022, "score": 529},  # 528 ±1 -> ok
        {"country": "South Korea", "subject": "reading", "year": 2022, "score": 519},  # 516 -> mismatch
    ])
    res = dp.cross_check_pisa(pisa, oecd)
    assert res["2025"]["n_compared"] == 3 and res["2025"]["n_within_tolerance"] == 2
    assert res["2025"]["mismatches"] == [{"country": "South Korea", "subject": "mathematics",
                                          "score": 523, "oecd": 522}]
    assert res["2022"]["n_compared"] == 2  # mathematics change is "m" -> not comparable
    assert [m["subject"] for m in res["2022"]["mismatches"]] == ["reading"]


def test_scrape_reads_cache_without_network(tmp_path, monkeypatch):
    cache = tmp_path / "pisa.csv"
    valid_pisa_raw().to_csv(cache, index=False)
    monkeypatch.setattr(requests, "get", lambda *a, **k: pytest.fail("network used"))
    assert len(dp.scrape_pisa_table(out_csv=cache)) == len(valid_pisa_raw())


def test_refresh_with_broken_page_keeps_cache(tmp_path, monkeypatch):
    cache = tmp_path / "pisa.csv"
    valid_pisa_raw().to_csv(cache, index=False)
    before = cache.read_bytes()

    class Broken:
        text, encoding = "<html><table class='wikitable'><tr><th>Rank</th></tr></table></html>", None

        def raise_for_status(self):
            pass

    monkeypatch.setattr(requests, "get", lambda *a, **k: Broken())
    with pytest.warns(UserWarning, match="keeping cached"):
        dp.scrape_pisa_table(out_csv=cache, refresh=True)
    assert cache.read_bytes() == before
    with pytest.raises(RuntimeError):
        dp.scrape_pisa_table(out_csv=tmp_path / "missing.csv", refresh=True)


# ---------------------------------------------------------------------------
# Student cleaning + holdout
# ---------------------------------------------------------------------------
def _processor(tmp_path, mat: pd.DataFrame, por: pd.DataFrame | None = None):
    paths = {"mat": tmp_path / "mat.csv"}
    mat.to_csv(paths["mat"], sep=";", index=False)
    if por is not None:
        paths["por"] = tmp_path / "por.csv"
        por.to_csv(paths["por"], sep=";", index=False)
    proc = dp.StudentDataProcessor(paths, None, tmp_path / "out", tmp_path / "img")
    proc.load_data()
    return proc


def test_clean_data_counts_problems_and_flags_dropouts(tmp_path, student_rows):
    rows = student_rows.copy()
    rows.loc[0, "age"] = "30"              # outside 15-22 -> NaN -> required column -> dropped
    rows.loc[1, "famsup"] = " maybe "      # not yes/no -> counted, encoded as missing
    rows.loc[2, "G3"] = "0"                # dropout suspect (flag, keep row)
    rows.loc[3, "school"] = " GP "         # whitespace
    rows = pd.concat([rows, rows.iloc[[4]]], ignore_index=True)  # exact duplicate
    proc = _processor(tmp_path, rows)
    clean = proc.clean_data()
    log = proc.cleaning_log

    assert log["n_out_of_range"]["age"] == 1
    assert log["n_missing_required_dropped"] == 1
    assert log["n_invalid_yes_no"]["famsup"] == 1
    assert log["n_duplicates_dropped"] == 1
    assert log["n_cells_stripped"] >= 2
    assert log["rows_in"] == 7 and log["rows_out"] == len(clean) == 5
    assert clean["famsup_bin"].isna().sum() == 1
    assert clean["dropout_suspect"].sum() == 1
    assert not clean["grade_drop"][clean["dropout_suspect"]].any()
    assert set(clean["school"]) == {"GP"}


def test_holdout_excludes_students_shared_with_primary_subject(tmp_path, student_rows):
    mat = student_rows.iloc[:3]
    por = student_rows.iloc[2:6].copy()      # row 2 is the same pupil as in mat
    por.loc[por.index[1:], "school"] = "MS"  # make the other por rows distinct pupils
    proc = _processor(tmp_path, mat, por)
    proc.clean_data()
    out = proc._risk_holdout()
    assert out["holdout_por"]["n"] == 4
    assert out["holdout_por_only"]["n"] == 3


def test_paired_subjects_matches_same_pupils_and_skips_ambiguous_keys(tmp_path, student_rows):
    mat = student_rows.copy()
    mat["G3"] = ["10", "11", "12", "13", "0", "15"]   # row 4: dropout suspect in mat -> pair not compared
    por = student_rows.copy()
    por["G3"] = ["12", "12", "15", "14", "10", "16"]
    twin = por.iloc[[5]].assign(G1="3")                # same key as row 5 inside por -> cannot be matched
    proc = _processor(tmp_path, mat, pd.concat([por, twin], ignore_index=True))
    res = dp._paired_subjects(proc.clean_data(), "mat", "por")
    assert res["n_duplicate_keys_b"] == 2
    assert res["n_matched"] == 5 and res["n_pairs"] == 4
    assert res["diff"] == pytest.approx(-1.75)        # (10-12 + 11-12 + 12-15 + 13-14) / 4


def test_group_tests_merge_sparse_failure_levels():
    rng = np.random.default_rng(1)
    n = 80
    df = pd.DataFrame({
        "G3": rng.integers(5, 20, n), "failures": [0] * 50 + [1] * 20 + [2] * 6 + [3] * 4,
        "studytime": rng.integers(1, 5, n), "absence_level": rng.choice(["low", "medium", "high"], n),
        **{c: rng.choice(["yes", "no"], n) for c in dp.BINARY_TEST_COLS}})
    res = dp._group_tests(df)["failures"]
    assert res["levels"] == ["0", "1", "2+"] and res["k_groups"] == 3


def test_user_agent_conforms_to_wikimedia_policy():
    ua = dp.HTTP_HEADERS.get("User-Agent", "")
    assert "P1-edu-project" in ua
    assert "mailto:" in ua or "@" in ua
    assert "github.com" in ua or "http" in ua


def test_devtools_manual_check_csv_exists_and_matches_schema():
    path = Path(__file__).resolve().parents[1] / "data" / "raw" / "pisa_manual_check.csv"
    assert path.exists(), "pisa_manual_check.csv missing"
    df = pd.read_csv(path)
    assert list(df.columns) == ["Rank", "Country/economy", "Score"]
    assert len(df) >= 80
    assert "Portugal" in df["Country/economy"].to_numpy()


def test_export_results_writes_combined_and_separate_subject_csvs(tmp_path, student_rows):
    mat = student_rows.iloc[:4].copy()
    por = student_rows.iloc[2:6].copy()
    proc = _processor(tmp_path, mat, por)
    proc.clean_data()
    proc.results = {"test": 123}
    proc.export_results()
    out_dir = tmp_path / "out"
    combined = pd.read_csv(out_dir / "cleaned_students.csv")
    mat_csv = pd.read_csv(out_dir / "cleaned_students_mat.csv")
    por_csv = pd.read_csv(out_dir / "cleaned_students_por.csv")

    assert len(combined) == len(mat_csv) + len(por_csv)
    assert set(mat_csv["subject"]) == {"mat"}
    assert set(por_csv["subject"]) == {"por"}
    assert (out_dir / "summary.json").exists()


def test_calc_average_grade_warns_against_prediction_leakage():
    val = dp.calc_average_grade(10, 12, 14)
    assert val == pytest.approx(12.0)
    doc = dp.calc_average_grade.__doc__ or ""
    assert "leakage" in doc.lower()
    assert "avg_grade" in dp.VAR_DESCRIPTIONS
    assert "leakage" in dp.VAR_DESCRIPTIONS["avg_grade"].lower() or "do not use" in dp.VAR_DESCRIPTIONS["avg_grade"].lower()
