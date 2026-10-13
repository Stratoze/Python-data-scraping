"""Generate report.md (English) and report_vi.md (Vietnamese) from pipeline results.

Every number comes from StudentDataProcessor.results (the same dict written to
summary.json) and every code block is read from the live source with `inspect`,
so the reports cannot drift from the code or the data.
"""
from __future__ import annotations

import inspect
import re
import textwrap
from datetime import date
from pathlib import Path

import data_processor as dp

ROOT = Path(__file__).resolve().parent
IMG = {"bar": "images/01_bar_studytime_internet.png",
       "hist": "images/02_hist_g3.png",
       "heat": "images/03_heatmap_corr.png",
       "pisa": "images/04_pisa_portugal_oecd.png"}
STUDY_LABEL = {"1": "<2h", "2": "2-5h", "3": "5-10h", "4": ">10h"}
SUBJECT_ORDER = ["mathematics", "reading", "science"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def code(obj) -> str:
    """Fenced source of a function/method with file + line range."""
    lines, start = inspect.getsourcelines(obj)
    path = Path(inspect.getsourcefile(obj)).name
    body = textwrap.dedent("".join(lines)).rstrip()
    return (f"`{path}` — `{obj.__qualname__}` (lines {start}–{start + len(lines) - 1})\n\n"
            f"```python\n{body}\n```")


def code_region(path: Path, start_marker: str, end_marker: str) -> str:
    """Fenced source between two marker lines of a file (start inclusive, end exclusive)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    i = next(k for k, ln in enumerate(lines) if start_marker in ln)
    j = next(k for k, ln in enumerate(lines) if k > i and end_marker in ln)
    while j > i and (not lines[j - 1].strip() or lines[j - 1].startswith("# ----")):
        j -= 1
    body = "\n".join(lines[i:j]).rstrip()
    return f"`{path.name}` (lines {i + 1}–{j})\n\n```python\n{body}\n```"


def table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def grp_rows(all_: dict, core: dict, order: list[str] | None = None,
             label=lambda k: k) -> list[list]:
    keys = order or sorted(core, key=lambda k: (len(k), k))
    rows = []
    for k in keys:
        a, c = all_.get(k), core.get(k)
        rows.append([label(k),
                     f"{a['mean']} ± {a['std']} (n={a['n']})" if a else "—",
                     f"**{c['mean']}** ± {c['std']} (n={c['n']})" if c else "—"])
    return rows


def _facts(proc: dp.StudentDataProcessor) -> dict:
    r = proc.results
    A, E = r["scopes"]["all"], r["scopes"]["exclude_dropout"]
    subj = r["primary_subject"]
    mat = proc.clean[proc.clean["subject"] == subj]
    core = mat[~mat["dropout_suspect"]]
    raw_counts = proc.df["subject"].value_counts().to_dict()
    ab = E["by_absence_level"]
    corr_g3 = {k: v for k, v in E["corr_full"]["G3"].items() if k != "G3"}
    sc = r["subject_comparison"]
    corr_keys = ["corr_G2_G3_exclude_dropout", "corr_absences_G3_exclude_dropout",
                 "corr_failures_G3_exclude_dropout"]
    pisa = r.get("pisa_context", {})
    latest = {s: max(pisa[s], key=int) for s in pisa}
    return {
        "r": r, "A": A, "E": E, "subj": subj,
        "n_raw": raw_counts, "n_cols": proc.df.shape[1] - 1,
        "log": r["cleaning_log"], "flags": r["anomaly_counts"][subj],
        "flags_all": r["anomaly_counts"], "dp": r["dropout_profile"],
        "risk": r["risk_eval"]["all"], "risk_core": r["risk_eval"]["exclude_dropout"],
        "sc": sc, "pisa": pisa, "pisa_latest": latest, "pisa_src": r.get("pisa_source") or {},
        "n_pisa_raw": len(proc.pisa_df) if proc.pisa_df is not None else 0,
        "n_pisa_clean": len(proc.pisa_clean) if proc.pisa_clean is not None else 0,
        "abs_monotonic": ab["low"]["mean"] > ab["medium"]["mean"] > ab["high"]["mean"],
        "small_groups": sorted(((k, v["n"]) for k, v in E["by_studytime_internet"].items()
                                if v["n"] < dp.MIN_RELIABLE_N), key=lambda kv: kv[1]),
        "gap_1_3": int(mat["G3"].between(1, 3).sum()),
        "mode_g3": int(core["G3"].mode().iloc[0]),
        "corr_g3_sorted": sorted(corr_g3.items(), key=lambda kv: -abs(kv[1])),
        "same_sign": all((sc["mat"][k] > 0) == (sc["por"][k] > 0) for k in corr_keys),
        "invalid_total": (sum(r["cleaning_log"]["n_non_numeric"].values())
                          + sum(r["cleaning_log"]["n_out_of_range"].values())
                          + sum(r["cleaning_log"]["n_invalid_yes_no"].values())
                          + r["cleaning_log"]["n_duplicates_dropped"]
                          + r["cleaning_log"]["n_missing_required_dropped"]
                          + r["cleaning_log"]["n_cells_stripped"]),
        "today": date.today().isoformat(),
        "gt": E["group_tests"], "ct": E["corr_tests"],
        "sig": [k for k, v in E["group_tests"].items() if v["significant"]],
        "nonsig": [k for k, v in E["group_tests"].items() if not v["significant"]],
        "ho": r["risk_eval"].get("holdout_por_only", {}).get("high"),
        "ho_ev": r["risk_eval"].get("holdout_por_only"),
        "kw_agree": all((v["p_kruskal"] < dp.ALPHA) == (v["p"] < dp.ALPHA)
                        for v in E["group_tests"].values() if "p_kruskal" in v),
        "oc": r.get("pisa_oecd_check"), "osrc": r.get("pisa_oecd_source") or {},
        "pt_check": _portugal_check(proc),
        "catch_up": next((int(y) for y, v in sorted(pisa.get("mathematics", {}).items(), key=lambda kv: int(kv[0]))
                          if v.get("oecd_average") is not None and v["portugal"] >= v["oecd_average"]), None),
        "below_2006": all(v["portugal"] < v["oecd_average"] for v in
                          (pisa.get(s, {}).get("2006", {}) for s in SUBJECT_ORDER) if "oecd_average" in v),
        "reg": r["regression"], "sens": r["sensitivity"],
        "abs_robust": all(r["sensitivity"][s][sc]["r_absences_G3"] < 0 and r["sensitivity"][s][sc]["p"] < dp.ALPHA
                          for s in r["sensitivity"]
                          for sc in ("exclude_dropout", "exclude_dropout_and_zero_absences")),
        "reg_sig_both": [c for c in dp.REG_FACTORS
                         if all(r["regression"][s]["factors"]["coef"][c]["significant"] for s in r["regression"])],
        "reg_grades_sig": [c for c in dp.REG_FACTORS
                           if r["regression"][subj]["factors_plus_grades"]["coef"][c]["significant"]],
        "tier_ok": all(r["risk_eval"][k]["tiers"]["medium_vs_low"]["significant"]
                       for k in ("all", "holdout_por_only") if k in r["risk_eval"]),
        "fail_steps": _fail_steps(E["by_failures"]),
        "pair": r["subject_paired"].get("por"),
        "ho_n": r["risk_eval"].get("holdout_por_only", {}).get("n"),
    }


def _fail_steps(by_failures: dict) -> list[tuple[str, str, float, int]]:
    """Change in mean G3 between consecutive failure counts: (from, to, diff, n of 'to' group)."""
    keys = sorted(by_failures, key=int)
    return [(a, b, round(by_failures[b]["mean"] - by_failures[a]["mean"], 2), by_failures[b]["n"])
            for a, b in zip(keys, keys[1:])]


def _fail_steps_text(steps: list, vi: bool) -> str:
    parts = ", ".join(f"{a}→{b}: {d:+.2f}" for a, b, d, _ in steps)
    first_biggest = bool(steps) and all(abs(steps[0][2]) > abs(d) for _, _, d, _ in steps[1:])
    small = ", ".join(f"{b} (n = {n})" for _, b, _, n in steps if n < 20)
    if vi:
        head = f"Mức thay đổi G3 trung bình giữa 2 mức liền nhau (exclude_dropout): {parts}."
        tail = (" **Lần trượt đầu tiên** đi kèm mức tụt điểm lớn nhất; các lần sau vẫn tụt nhưng ít hơn."
                if first_biggest else " Mức tụt không lớn nhất ở lần trượt đầu tiên.")
        note = f" Lưu ý nhóm ít học sinh: {small}." if small else ""
    else:
        head = f"Change in mean G3 between consecutive levels (exclude_dropout): {parts}."
        tail = (" The **first failure** comes with the biggest drop; later failures still lower G3 but by less."
                if first_biggest else " The biggest drop is not at the first failure.")
        note = f" Small groups: {small}." if small else ""
    return head + tail + note


def _paired_text(f: dict, vi: bool) -> str:
    """Section 10.1: why mat/por are not independent + paired G3 comparison of the same pupils."""
    p = f["pair"]
    sig = p["significant"]
    if vi:
        rows = [["Cặp học sinh khớp được", p["n_matched"]],
                ["Cặp dùng để so (G3 > 0 ở cả 2 môn)", p["n_pairs"]],
                ["G3 trung bình mat / por", f"{p['mean_G3_a']} / {p['mean_G3_b']}"],
                ["Chênh lệch mat − por [CI 95%]", f"{p['diff']:+.2f} [{p['ci95'][0]}, {p['ci95'][1]}]"],
                ["p (t-test ghép cặp) / p (Wilcoxon)", f"{_fmt_p(p['p_ttest'])} / {_fmt_p(p['p_wilcoxon'])}"],
                ["r(G3 mat, G3 por) của cùng học sinh", p["corr_G3"]]]
        verdict = (f"Cùng một học sinh, điểm môn Toán {'thấp' if p['diff'] < 0 else 'cao'} hơn môn Bồ Đào Nha "
                   f"trung bình {abs(p['diff']):.2f} điểm, chênh lệch **có ý nghĩa thống kê**."
                   if sig else "Cùng một học sinh, điểm 2 môn **không khác nhau có ý nghĩa thống kê**.")
        return f"""**2 file không phải 2 mẫu độc lập.** Ghép học sinh theo 13 cột nhận dạng (`MERGE_KEYS`, giống
`student-merge.R`) tìm được **{p['n_matched']}** em có mặt ở cả 2 môn ({p['n_duplicate_keys_a']} dòng mat và {p['n_duplicate_keys_b']} dòng por
có key bị lặp trong cùng file nên không ghép chắc chắn được và bị bỏ ra). Vì vậy bảng trên so 2 nhóm chồng lấn nhau:
việc 2 môn cho kết quả giống nhau một phần là do cùng học sinh được đo 2 lần, **chưa phải** kiểm chứng độc lập.
Kiểm chứng độc lập thật sự là bản holdout chặt ở mục 9 (chỉ học sinh por không có trong mat, n = {f['ho_n']}).

**So sánh ghép cặp (cùng học sinh, 2 môn):** t-test ghép cặp (`scipy.stats.ttest_rel`) và Wilcoxon (không cần
giả định phân phối chuẩn), bỏ các cặp có G3 = 0 ở ít nhất một môn.

{table(['Chỉ số', 'Giá trị'], rows)}

{verdict}"""
    rows = [["Pupils matched", p["n_matched"]],
            ["Pairs compared (G3 > 0 in both courses)", p["n_pairs"]],
            ["Mean G3 mat / por", f"{p['mean_G3_a']} / {p['mean_G3_b']}"],
            ["Difference mat − por [95% CI]", f"{p['diff']:+.2f} [{p['ci95'][0]}, {p['ci95'][1]}]"],
            ["p (paired t-test) / p (Wilcoxon)", f"{_fmt_p(p['p_ttest'])} / {_fmt_p(p['p_wilcoxon'])}"],
            ["r(G3 mat, G3 por) of the same pupil", p["corr_G3"]]]
    verdict = (f"The same pupil scores on average {abs(p['diff']):.2f} points {'lower' if p['diff'] < 0 else 'higher'} "
               f"in mathematics than in Portuguese, and the difference is **significant**."
               if sig else "The same pupil's grades in the two courses are **not significantly different**.")
    return f"""**The two files are not independent samples.** Matching pupils on the 13 identifying columns
(`MERGE_KEYS`, as in `student-merge.R`) finds **{p['n_matched']}** pupils who take both courses ({p['n_duplicate_keys_a']} mat and
{p['n_duplicate_keys_b']} por rows have a key that repeats inside the same file, so they cannot be matched safely and are left out).
The table above therefore compares two overlapping groups: part of the agreement between the courses is the same
pupils measured twice, so it is **not** an independent replication. The truly independent check is the strict
holdout in section 9 (only por pupils who are not in mat, n = {f['ho_n']}).

**Paired comparison (same pupil, two courses):** paired t-test (`scipy.stats.ttest_rel`) and Wilcoxon signed-rank
(no normality assumption); pairs with G3 = 0 in either course are left out.

{table(['Metric', 'Value'], rows)}

{verdict}"""



def _portugal_check(proc: dp.StudentDataProcessor) -> list[list]:
    """Portugal + OECD average, latest cycle: Wikipedia value vs official OECD value."""
    if proc.oecd_df is None or proc.pisa_clean is None:
        return []
    o = proc.oecd_df.set_index(proc.oecd_df["country"].str.replace(r"\s*\*+$", "", regex=True))
    p = proc.pisa_clean[proc.pisa_clean["year"] == dp.OECD_PISA_YEAR].set_index(["country", "subject"])
    rows = []
    for country in ["Portugal", "OECD average"]:
        for s in SUBJECT_ORDER:
            wiki, off = int(p.loc[(country, s), "score"]), int(o.loc[country, s])
            rows.append([country, s, wiki, off, "✅" if wiki == off else "❌"])
    return rows


REG_LABEL = {
    "studytime": ("studytime (+1 bucket)", "studytime (+1 mức)"),
    "failures": ("failures (+1 past failure)", "failures (+1 lần trượt)"),
    "absences": ("absences (+1 absence)", "absences (+1 buổi vắng)"),
    "famsup_bin": ("famsup (yes vs no)", "famsup (có vs không)"),
    "schoolsup_bin": ("schoolsup (yes vs no)", "schoolsup (có vs không)"),
    "paid_bin": ("paid classes (yes vs no)", "học thêm trả phí (có vs không)"),
    "internet_bin": ("internet (yes vs no)", "internet (có vs không)"),
    "higher_bin": ("wants higher education (yes vs no)", "muốn học đại học (có vs không)"),
    "Medu": ("mother's education (+1 level)", "học vấn mẹ (+1 bậc)"),
    "Fedu": ("father's education (+1 level)", "học vấn bố (+1 bậc)"),
    "male": ("sex (male vs female)", "giới tính (nam vs nữ)"),
    "age": ("age (+1 year)", "tuổi (+1 năm)"),
    "urban": ("address (urban vs rural)", "nơi ở (thành thị vs nông thôn)"),
    "G1": ("G1 (+1 point)", "G1 (+1 điểm)"),
    "G2": ("G2 (+1 point)", "G2 (+1 điểm)"),
}


def _lbl(col: str, vi: bool) -> str:
    return REG_LABEL[col][1 if vi else 0]


def _reg_rows(f: dict, model: str, cols: list[str], vi: bool) -> list[list]:
    yes = "✅"
    rows = []
    for c in cols:
        m = f["reg"]["mat"][model]["coef"][c]
        p = f["reg"].get("por", {}).get(model, {}).get("coef", {}).get(c)
        rows.append([_lbl(c, vi), f"{m['b']:+.3f}", f"[{m['ci95'][0]}, {m['ci95'][1]}]", _fmt_p(m["p"]),
                     yes if m["significant"] else "—",
                     (f"{p['b']:+.3f} {'✅' if p['significant'] else '—'}" if p else "—")])
    return rows


SENS_LABEL = {
    "all": ("all students", "toàn bộ học sinh"),
    "exclude_dropout": ("exclude dropout suspects (G3 = 0)", "bỏ nhóm nghi bỏ thi (G3 = 0)"),
    "exclude_dropout_and_zero_absences": ("also exclude absences = 0 (maybe 'not recorded')",
                                          "bỏ thêm absences = 0 (có thể là 'không được ghi')"),
}


def _sens_rows(f: dict, vi: bool) -> list[list]:
    rows = []
    for subj, scen in f["sens"].items():
        for key, labels in SENS_LABEL.items():
            s = scen[key]
            lv = s["mean_G3_by_absence_level"]
            rows.append([subj, labels[1 if vi else 0], s["n"],
                         f"**{s['r_absences_G3']:+.3f}** [{s['ci95'][0]}, {s['ci95'][1]}]", _fmt_p(s["p"]),
                         f"{lv.get('low', '—')} / {lv.get('medium', '—')} / {lv.get('high', '—')}",
                         _fmt_p(s["anova_p"]), pct(s["pass_rate"])])
    return rows


TIER_SCOPES = {"all": ("mat (rule designed here)", "mat (dữ liệu đặt rule)"),
               "holdout_por_only": ("por strict holdout (unseen)", "por holdout chặt (chưa thấy)")}


def _tier_rows(r: dict, vi: bool) -> list[list]:
    rows = []
    for key, labels in TIER_SCOPES.items():
        t = r["risk_eval"].get(key, {}).get("tiers")
        if not t:
            continue
        cells = [f"{t[g]['n_fail']}/{t[g]['n']} = **{pct(t[g]['fail_rate'])}** "
                 f"[{pct(t[g]['fail_rate_ci95'][0])}, {pct(t[g]['fail_rate_ci95'][1])}]"
                 for g in ("low", "medium", "high")]
        mv = t["medium_vs_low"]
        rows.append([labels[1 if vi else 0], *cells,
                     f"×{mv['relative_risk']} (p {_fmt_p(mv['p'])}) {'✅' if mv['significant'] else '❌'}"])
    return rows


def _oecd_rows(f: dict, vi: bool) -> list[list]:
    oc = f["oc"]
    rows = []
    for year in sorted((k for k in oc if k.isdigit()), reverse=True):
        c = oc[year]
        if vi:
            how = "so trực tiếp, phải khớp tuyệt đối" if c["tolerance"] == 0 else f"suy ra = điểm 2025 − mức thay đổi, cho lệch ±{c['tolerance']} do làm tròn"
        else:
            how = "direct, must match exactly" if c["tolerance"] == 0 else f"derived = 2025 score − change, ±{c['tolerance']} allowed for rounding"
        bad = "; ".join(f"{m['country']} {m['subject']} {m['score']} vs {m['oecd']}" for m in c["mismatches"]) or "—"
        rows.append([year, how, c["n_compared"], c["n_within_tolerance"], c["n_exact"], c["max_abs_diff"], bad])
    return rows


def _pisa_rows(f: dict) -> list[list]:
    rows = []
    for s in SUBJECT_ORDER:
        for y, v in sorted(f["pisa"].get(s, {}).items(), key=lambda kv: int(kv[0])):
            oecd = v.get("oecd_average")
            rows.append([s, y, v["portugal"], oecd if oecd is not None else "—",
                         f"{v['portugal'] - oecd:+d}" if oecd is not None else "—",
                         v["portugal_rank"] if v["portugal_rank"] is not None else "—"])
    return rows


def _confusion(risk: dict) -> list[list]:
    h = risk["high"]
    return [["flagged high", h["tp"], h["fp"]], ["not flagged", h["fn"], h["tn"]]]


def _fmt_p(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def _test_rows(E: dict, vi: bool) -> list[list]:
    yes, no = ("có", "không") if vi else ("yes", "no")
    groups = "nhóm" if vi else "groups"
    sig = ("✅ có", "❌ không") if vi else ("✅ yes", "❌ no")
    rows = []
    for col, v in E["group_tests"].items():
        if v["test"] == "Welch t-test":
            compare = f"{yes} {v['mean_yes']} (n={v['n_yes']}) vs {no} {v['mean_no']} (n={v['n_no']})"
            stat = f"t = {v['stat']} (df {v['df']})"
            extra = f"{v['diff']:+.2f} [{v['ci95'][0]}, {v['ci95'][1]}]"
        else:
            compare = f"{v['k_groups']} {groups} ({', '.join(v['levels'])})"
            stat = f"F = {v['stat']}"
            extra = f"Kruskal–Wallis H = {v['kruskal_H']}, p {_fmt_p(v['p_kruskal'])}"
        rows.append([f"`{col}`", v["test"], compare, stat, extra, _fmt_p(v["p"]),
                     _fmt_p(v["p_holm"]), f"{v['effect_name']} = {v['effect']}",
                     sig[0] if v["significant"] else sig[1]])
    return rows


def _corr_rows(E: dict) -> list[list]:
    return [[f"`{k.replace('_bin', '')}`", f"{v['r']:+.3f}", f"[{v['ci95'][0]}, {v['ci95'][1]}]",
             _fmt_p(v["p"])] for k, v in E["corr_tests"].items()]


HOLDOUT_LABELS = {
    "all": ("mat — in-sample (rule designed here)", "mat — in-sample (rule được đặt trên dữ liệu này)"),
    "holdout_por": ("por — all students (holdout)", "por — toàn bộ học sinh (holdout)"),
    "holdout_por_only": ("por — only students not in mat (strict holdout)",
                         "por — chỉ học sinh không có trong mat (holdout chặt)"),
}


def _holdout_rows(r: dict, vi: bool) -> list[list]:
    rows = []
    for key, labels in HOLDOUT_LABELS.items():
        ev = r["risk_eval"].get(key)
        if ev is None:
            continue
        h = ev["high"]
        rows.append([labels[1] if vi else labels[0], ev["n"], pct(ev["fail_rate"]),
                     f"{h['tp']} / {h['fp']} / {h['fn']}",
                     f"**{pct(h['recall'])}** [{pct(h['recall_ci95'][0])}, {pct(h['recall_ci95'][1])}]",
                     f"**{pct(h['precision'])}** [{pct(h['precision_ci95'][0])}, {pct(h['precision_ci95'][1])}]"])
    return rows


def _clean_rows(log: dict, vi: bool) -> list[list]:
    nn, oor, yn = (sum(log[k].values()) for k in ("n_non_numeric", "n_out_of_range", "n_invalid_yes_no"))
    if vi:
        return [
            ["1. Cắt khoảng trắng ở các cột chữ", "`str.strip()`", log["n_cells_stripped"]],
            ["2a. Ép kiểu số 16 cột số", "`pd.to_numeric(errors='coerce')`", nn],
            ["2b. Kiểm tra miền giá trị theo `student.txt`", "`VALID_RANGES` → ngoài miền thành NaN", oor],
            ["3. Mã hoá yes/no → 1/0, giá trị lạ → NaN", "`convert_yes_no`", yn],
            ["4a. Xoá dòng trùng", "`drop_duplicates()`", log["n_duplicates_dropped"]],
            ["4b. Xoá dòng thiếu cột bắt buộc", "`dropna(subset=REQUIRED_COLS)`", log["n_missing_required_dropped"]],
        ]
    return [
        ["1. Strip whitespace in text columns", "`str.strip()`", log["n_cells_stripped"]],
        ["2a. Cast 16 numeric columns", "`pd.to_numeric(errors='coerce')`", nn],
        ["2b. Domain check against `student.txt`", "`VALID_RANGES` → out-of-range becomes NaN", oor],
        ["3. Encode yes/no → 1/0, anything else → NaN", "`convert_yes_no`", yn],
        ["4a. Drop duplicate rows", "`drop_duplicates()`", log["n_duplicates_dropped"]],
        ["4b. Drop rows missing a required column", "`dropna(subset=REQUIRED_COLS)`", log["n_missing_required_dropped"]],
    ]


def _flag_rows(f: dict, vi: bool) -> list[list]:
    fence = f["log"]["absence_outlier_fence"][f["subj"]]
    k, g1d, g2d, age = dp.ANOMALY_THRESHOLDS
    fl = f["flags"]
    if vi:
        defs = [
            ("dropout_suspect", "`G3 == 0`", "Nghi bỏ thi / bỏ học"),
            ("g2_zero", "`G2 == 0`", "Nghi vắng kỳ 2"),
            ("grade_drop", f"`G1−G3 ≥ {g1d}` hoặc `G2−G3 ≥ {g2d}`, loại trừ dropout", "Tụt điểm đột ngột"),
            ("absence_outlier", f"`absences > Q3 + {k}·IQR` (= {fence:g} ở {f['subj']})", "Vắng nhiều bất thường"),
            ("age_outlier", f"`age ≥ {age}`", "Học muộn / lưu ban"),
            ("inconsistent_grade", "`G3 > 0` nhưng `G2 == 0`", "Điểm mâu thuẫn"),
        ]
    else:
        defs = [
            ("dropout_suspect", "`G3 == 0`", "Likely did not sit the final exam / left school"),
            ("g2_zero", "`G2 == 0`", "Likely absent for period 2"),
            ("grade_drop", f"`G1−G3 ≥ {g1d}` or `G2−G3 ≥ {g2d}`, dropouts excluded", "Sudden grade drop"),
            ("absence_outlier", f"`absences > Q3 + {k}·IQR` (= {fence:g} in {f['subj']})", "Unusually many absences"),
            ("age_outlier", f"`age ≥ {age}`", "Late start / repeated years"),
            ("inconsistent_grade", "`G3 > 0` but `G2 == 0`", "Contradictory grades"),
        ]
    return [[f"`{n}`", rule, fl[n], f["flags_all"].get("por", {}).get(n, "—"), why] for n, rule, why in defs]


# ---------------------------------------------------------------------------
# English
# ---------------------------------------------------------------------------
def render_en(f: dict, codes: dict) -> str:
    r, A, E, dpf, risk = f["r"], f["A"], f["E"], f["dp"], f["risk"]
    h = risk["high"]
    ps = f["pisa_src"]
    top = f["corr_g3_sorted"]
    pl = f["pisa_latest"]
    pm = f["pisa"].get("mathematics", {})
    s = []
    s.append(f"""# P1 Report — Factors Affecting Final Grades (UCI Student Performance, `{f['subj']}`)

> Generated automatically by `report_builder.py` on {f['today']} from the same results written to
> `data/processed/summary.json`. Every number below is computed by the pipeline and every code block
> is read from the current source file, so the report cannot drift from the code or the data.
> Re-generate with `python main.py`.

**Main question:** How do study time, absences, family support and intermediate grades (G1, G2)
relate to the final grade (G3)?

## 1. Executive summary

| Question | Answer (mathematics, {E['n']} students with G3 > 0 unless stated) |
|---|---|
| Intermediate grades → G3 | Strongest link: r(G2, G3) = **{E['corr_G1_G2_G3']['G2_G3']}**, r(G1, G3) = {E['corr_G1_G2_G3']['G1_G3']} |
| Past failures → G3 | 0 failures: **{E['by_failures']['0']['mean']}**, 1: {E['by_failures']['1']['mean']}, 2: {E['by_failures']['2']['mean']}, 3: {E['by_failures']['3']['mean']} (r = {E['corr_full']['G3']['failures']}) |
| Absences → G3 | low {E['by_absence_level']['low']['mean']} / medium {E['by_absence_level']['medium']['mean']} / high {E['by_absence_level']['high']['mean']} (r = **{E['corr_full']['G3']['absences']}**, ANOVA Holm p {_fmt_p(f['gt']['absence_level']['p_holm'])}) |
| Study time → G3 | weak positive, r = {E['corr_full']['G3']['studytime']} (ANOVA Holm p {_fmt_p(f['gt']['studytime']['p_holm'])}, eta² = {f['gt']['studytime']['effect']}: small) |
| Internet at home → G3 | yes {f['gt']['internet']['mean_yes']} vs no {f['gt']['internet']['mean_no']}; raw p {_fmt_p(f['gt']['internet']['p'])}, Holm p {_fmt_p(f['gt']['internet']['p_holm'])} → **{'significant' if f['gt']['internet']['significant'] else 'not significant after correction'}** |
| All factors together (regression) | background factors explain R² = {f['reg']['mat']['factors']['r2']}; significant in both courses with the others held fixed: **{', '.join(_lbl(c, False) for c in f['reg_sig_both'])}**; internet adjusted b = {f['reg']['mat']['factors']['coef']['internet_bin']['b']:+.2f} (p {_fmt_p(f['reg']['mat']['factors']['coef']['internet_bin']['p'])}) |
| Family support (`famsup`) → G3 | yes {E['by_famsup']['yes']['mean']} vs no {E['by_famsup']['no']['mean']} (Holm p {_fmt_p(f['gt']['famsup']['p_holm'])}): **{'significant' if f['gt']['famsup']['significant'] else 'no significant difference'}** |
| Pass rate | {pct(A['pass_rate'])} of all {A['n']} students; {pct(E['pass_rate'])} after removing {dpf['n']} dropout suspects |
| Early-warning rule (no G3) | designed on mat: recall {pct(h['recall'])}, precision {pct(h['precision'])}; **tested on unseen Portuguese-only students: recall {pct(f['ho']['recall'])}, precision {pct(f['ho']['precision'])}** |

**Key data-quality finding:** {dpf['n']} students have G3 = 0 and **{dpf['n_absences_zero']} of them have 0 recorded
absences**. They are treated as *dropout suspects* (flagged, not deleted). Including them flips the absences
correlation to r = {A['corr_full']['G3']['absences']} and hides the real negative effect.

## 2. Requirement checklist

| Requirement (assignment sheet) | Where it is done | Section |
|---|---|---|
| UCI Student Performance dataset (`student.zip`) | `fetch_uci_raw()` | 3.1 |
| Web scraping: Wikipedia PISA | `scrape_pisa_table()`, `_parse_pisa_html()`, `validate_pisa_raw()` | 3.2 |
| Save raw CSV | `data/raw/student-*.csv`, `data/raw/pisa_reference.csv` | 3 |
| Clean data types, encode yes/no | `clean_data()` | 5 |
| 4 basic functions (yes/no, pass/fail, absence level, average grade) | `convert_yes_no`, `calc_pass_fail`, `classify_absences`, `calc_average_grade` | 4 |
| list of dicts, dict mapping, set of unique schools/jobs, tuple thresholds | `SAMPLE_STUDENTS`, `VAR_DESCRIPTIONS`, `set()` in `analyze()`, `THRESHOLDS` | 4 |
| EDA with groupby, mean, std | `_grp()`, `_scope_stats()` | 7 |
| Compare G3 by studytime, absences, failures, internet | `by_*` tables | 7 |
| Pass/fail; learning-risk groups | `pass_fail`, `classify_risk()`, `_risk_eval()` | 7, 9 |
| Correlation G1, G2, G3 | `corr_G1_G2_G3`, heatmap | 7, 8.3 |
| Bar chart, histogram, heatmap | `_plot_bar`, `_plot_hist`, `_plot_heatmap` | 8 |
| OOP: `load_data()`, `clean_data()`, `analyze()`, `export_results()`; `main.py` exports `cleaned_students.csv` + `summary.json` | `StudentDataProcessor`, `main.py` | 11 |
| Insights and limitations | — | 12, 13 |

## 3. Data collection

### 3.1 UCI Student Performance

**What was done:** the official UCI zip is downloaded only if the raw CSVs are missing, then the inner
`student.zip` is extracted into `data/raw/`. Raw files are never edited afterwards.

| File | Rows | Columns | Role |
|---|---|---|---|
| `student-mat.csv` | {f['n_raw'].get('mat')} | {f['n_cols']} | Primary analysis (mathematics) |
| `student-por.csv` | {f['n_raw'].get('por')} | {f['n_cols']} | Replication / comparison (Portuguese) |

{codes['fetch_uci_raw']}

**Why it can be trusted:** the URL is the official UCI download; files are byte-for-byte what UCI ships;
row/column counts match the UCI description (395 / 649 students, 33 attributes).

### 3.2 Wikipedia PISA (web scraping)

**What was done:**
1. `requests.get` downloads the HTML of the [PISA article]({ps.get('url', dp.PISA_URL)}) (no browser needed: the tables are plain HTML).
2. `BeautifulSoup` finds every `table.wikitable` and keeps two families:
   - **summary**: latest ranking (`Rank | Country/economy | Score`), one nested table per subject;
   - **comparison**: "Rankings comparison 2000–2022", one row per country with `score, rank` pairs per year (converted from wide to long).
3. The result ({f['n_pisa_raw']} rows, page strings untouched) is saved to `data/raw/pisa_reference.csv`.
4. Collection is **cache-first**: normal runs read the saved CSV; `python main.py --refresh-pisa` re-scrapes.

| Provenance | Value |
|---|---|
| Wikipedia revision | [{ps.get('revision_id')}]({ps.get('permalink')}) |
| Scraped at (UTC) | {ps.get('scraped_at')} |
| Raw rows | {ps.get('n_rows')} |
| Licence | CC BY-SA 4.0 (Wikipedia) |
| User-Agent | `{dp.HTTP_HEADERS['User-Agent']}` |

{codes['scrape_pisa_table']}

{codes['_parse_pisa_html']}

**Why it can be trusted — structural validation.** Every scraped table (and every cache read) must pass
`validate_pisa_raw()`; otherwise it is rejected and the previous cache is kept:

- both table families contain all 3 subjects;
- every year is a number between 2000 and the current year;
- every score lies in [{dp.PISA_SCORE_MIN}, {dp.PISA_SCORE_MAX}];
- every (source, subject, year) has ≥ {dp.PISA_MIN_COUNTRIES} countries with a score, numeric ranks, no duplicate country and exactly one OECD-average row.

{codes['validate_pisa_raw']}

### 3.3 PISA cleaning

Footnotes (`[41]`) and trailing `*` are removed from country names, `—` (did not participate) becomes
missing, rank/score/year become numbers, "International Average (OECD)" is renamed `OECD average`.
Result: {f['n_pisa_clean']} rows in `data/processed/pisa_clean.csv`.

{codes['clean_pisa']}

### 3.4 Cross-check against the official OECD report

**What was done.** Wikipedia is a secondary source, so the scraped numbers are compared with the **official OECD
publication**: {f['osrc'].get('source', '—')}, {f['osrc'].get('table', '—')} ([DOI]({f['osrc'].get('doi', '#')}), licence {f['osrc'].get('licence', '—')}).
The table was extracted once from the OECD PDF into `data/raw/oecd_pisa2025_table_I1.csv` ({f['osrc'].get('n_rows', '—')} rows:
OECD average + every participating country). Five country names differ between the two sources and are mapped
(`OECD_NAME_ALIASES`, e.g. "Chinese Taipei" → "Taiwan").

{table(['Cycle', 'How compared', 'Pairs compared', 'Within tolerance', 'Exact', 'Max |diff|', 'Mismatches (Wikipedia vs OECD)'], _oecd_rows(f, vi=False))}

Countries in the OECD table but missing from a Wikipedia table: {'; '.join(f"{s}: {', '.join(v)}" for s, v in f['oc']['missing_in_wikipedia'].items() if v) or 'none'}.

**Portugal and OECD average (the rows this report actually uses):**

{table(['Country', 'Subject', 'Wikipedia', 'OECD official', 'Match'], f['pt_check'])}

**Why it can be trusted:** every {dp.OECD_PISA_YEAR} score scraped from Wikipedia equals the official OECD value, and
the 2022 values (derived from the OECD change column) agree within rounding except for the rows listed as
mismatches above, which do not affect Portugal. Earlier cycles (2000–2018) are not covered by this OECD table and
remain Wikipedia-only.

{codes['cross_check_pisa']}

## 4. Python basics required by the assignment

Configuration (tuples, dict mappings, list of dicts) — real source:

{codes['config']}

The four basic functions:

{codes['convert_yes_no']}

{codes['calc_pass_fail']}

{codes['classify_absences']}

{codes['calc_average_grade']}

`set()` of unique values (computed in `analyze()`): schools = `{r['unique_schools']}`, mother's jobs = `{r['unique_mjobs']}`, father's jobs = `{r['unique_fjobs']}`.

## 5. Data cleaning

**What was done** (`StudentDataProcessor.clean_data()`, order matters: cast → validate → drop → derive → flag).
Rows in: {f['log']['rows_in']} (both subjects) → rows out: {f['log']['rows_out']}.

{table(['Step', 'How', 'Rows/cells affected'], _clean_rows(f['log'], vi=False))}

Derived columns: `pass_fail` (G3 ≥ {dp.PASS_MARK}), `absence_level` (low 0–{dp.ABS_MED - 1} / medium {dp.ABS_MED}–{dp.ABS_HIGH - 1} / high ≥ {dp.ABS_HIGH}),
`avg_grade` (G1+G2+G3)/3 (descriptive only: contains target G3 so DO NOT use as predictor to prevent data leakage; use `avg_g1g2` for early prediction), `avg_g1g2`, `risk_group`, and 6 anomaly flags.

{codes['load_data']}

{codes['clean_data']}

**Why it can be trusted:** each check *counts* what it changed and the counts are stored in
`summary.json → cleaning_log`. All {f['invalid_total']} — i.e. the raw UCI data is structurally clean; the only real
problem is semantic (G3 = 0, section 6). Nothing is silently coerced: an unexpected value would become NaN
and show up in these counts.

### 5.1 Anomaly flags (flag, never delete)

{table(['Flag', 'Rule', f"Count ({f['subj']})", 'Count (por)', 'Meaning'], _flag_rows(f, vi=False))}

Thresholds come from the tuple `ANOMALY_THRESHOLDS = {dp.ANOMALY_THRESHOLDS}` (IQR factor, G1 drop, G2 drop, age).
The IQR fence is computed per subject because the two courses have different absence distributions.

## 6. Dropout suspects (G3 = 0)

| Evidence | Value |
|---|---|
| Students with G3 = 0 | {dpf['n']} |
| … of which absences = 0 | **{dpf['n_absences_zero']} / {dpf['n']}** |
| … of which G2 = 0 | {dpf['n_g2_zero']} |
| Their mean G1 / G2 | {dpf['mean_G1']} / {dpf['mean_G2']} |
| Share of absences = 0 among other students | {pct(dpf['share_absences_zero_others'])} |
| Students with G3 between 1 and 3 | {f['gap_1_3']} (empty gap before the zeros) |

**Interpretation:** these students had real G1 grades, then a zero final grade with zero recorded absences.
A genuine grade of 0/20 after G1 ≈ {dpf['mean_G1']} is implausible; "did not sit the exam / left school, absences
not recorded" is the consistent explanation. They are kept in `cleaned_students.csv` with `dropout_suspect = True`
and every statistic is reported twice: **all** (n = {A['n']}) and **exclude_dropout** (n = {E['n']}).

| Statistic | all (n={A['n']}) | exclude_dropout (n={E['n']}) |
|---|---|---|
| Pass rate | {pct(A['pass_rate'])} | **{pct(E['pass_rate'])}** |
| r(G2, G3) | {A['corr_G1_G2_G3']['G2_G3']} | **{E['corr_G1_G2_G3']['G2_G3']}** |
| r(G1, G3) | {A['corr_G1_G2_G3']['G1_G3']} | **{E['corr_G1_G2_G3']['G1_G3']}** |
| r(absences, G3) | {A['corr_full']['G3']['absences']} | **{E['corr_full']['G3']['absences']}** |
| r(failures, G3) | {A['corr_full']['G3']['failures']} | **{E['corr_full']['G3']['failures']}** |

### 6.1 Sensitivity analysis: does the conclusion depend on how the zeros are treated?

**What was done.** Two assumptions could be wrong: (1) G3 = 0 means "dropped out", and (2) absences = 0 means "never
absent" — it might instead mean "not recorded". The absences analysis is therefore repeated under three scenarios, in
both courses, and the result is compared.

{table(['Course', 'Scenario', 'n', 'r(absences, G3) [95% CI]', 'p', 'Mean G3 low / medium / high', 'ANOVA p', 'Pass rate'], _sens_rows(f, vi=False))}

Dropout pattern in both courses: {', '.join(f"{s}: {v['dropout_pattern']['n_dropout_absences_zero']}/{v['dropout_pattern']['n_dropout']} dropout suspects have absences = 0 (vs {pct(v['dropout_pattern']['share_absences_zero_others'])} of other students)" for s, v in f['sens'].items())}.

**Interpretation:**
- {'In every scenario that removes the zeros, absences have a **significant negative** relationship with G3 in both courses. The conclusion holds whether or not the dropout assumption is right and whether or not absences = 0 is real.' if f['abs_robust'] else 'At least one scenario without the zeros does not show a significant negative relationship; the absences conclusion depends on how the zeros are treated.'}
- Only the "all students" scenario hides or weakens the effect — exactly the distortion caused by the G3 = 0 rows.
- The dropout pattern (G3 = 0 always together with absences = 0) appears in both courses, which supports reading it as "not assessed / left school" rather than a real grade.

{codes['_sensitivity']}

## 7. Exploratory analysis (groupby → mean ± std, n)

Cells show *mean G3 ± standard deviation (n students)*. Bold = headline scope.

**By weekly study time**

{table(['Studytime', 'all', 'exclude_dropout'], grp_rows(A['by_studytime'], E['by_studytime'], label=lambda k: f"{k} ({STUDY_LABEL[k]})"))}

**By absence level** — {'mean G3 decreases steadily from low to high absences' if f['abs_monotonic'] else 'not monotonic'} once dropout suspects are removed.

{table(['Absence level', 'all', 'exclude_dropout'], grp_rows(A['by_absence_level'], E['by_absence_level'], order=['low', 'medium', 'high']))}

**By past failures**

{table(['Failures', 'all', 'exclude_dropout'], grp_rows(A['by_failures'], E['by_failures']))}

{_fail_steps_text(f['fail_steps'], vi=False)}

**By internet at home / family support / school support / paid classes**

{table(['Group', 'all', 'exclude_dropout'], [['internet = ' + k, *grp_rows(A['by_internet'], E['by_internet'], order=[k])[0][1:]] for k in ['no', 'yes']] + [['famsup = ' + k, *grp_rows(A['by_famsup'], E['by_famsup'], order=[k])[0][1:]] for k in ['no', 'yes']] + [['schoolsup = ' + k, *grp_rows(A['by_schoolsup'], E['by_schoolsup'], order=[k])[0][1:]] for k in ['no', 'yes']] + [['paid = ' + k, *grp_rows(A['by_paid'], E['by_paid'], order=[k])[0][1:]] for k in ['no', 'yes']])}

Note: `schoolsup = yes` students score lower because extra school support is *given to* weaker students
(reverse causality) — this is not evidence that support lowers grades.

{codes['_grp']}

{codes['_scope_stats']}

### 7.1 Significance tests: is each difference real or just chance?

**What was done.** For every comparison above, a statistical test asks: *if the groups really had the same mean G3,
how likely is a difference this large just by chance?* That probability is the **p-value**; a difference is called
significant when p < α = {dp.ALPHA}.

| Method | Used for | Why this one |
|---|---|---|
| Welch t-test | yes/no variables (internet, famsup, schoolsup, paid) | Compares 2 means without assuming equal variances (group sizes are very unequal, e.g. 58 vs 299) |
| One-way ANOVA (F) | studytime (4 levels), absence level (3), failures ({len(f['gt']['failures']['levels'])}: {', '.join(f['gt']['failures']['levels'])}) | Compares ≥ 3 means in one test. Failures 2 and 3 have only about a dozen students each, so they are merged into one "2+" group for the tests (the descriptive tables in section 7 keep all 4 levels) |
| Kruskal–Wallis (H) | same as ANOVA | Rank-based check that does not assume normally distributed grades |
| Holm–Bonferroni correction | all {len(f['gt'])} tests together | Running many tests raises the chance of a false "significant"; Holm adjusts the p-values so the whole family keeps a 5% error rate |
| Effect size: Cohen's d / eta² | every test | p only says "real or not"; effect size says "how big". d: 0.2 small, 0.5 medium, 0.8 large. eta² = share of G3 variance explained: 0.01 small, 0.06 medium, 0.14 large |
| 95% CI of the difference | t-tests | Range of plausible true differences; if it contains 0 the difference is not significant |

**Results (exclude_dropout, n = {E['n']}):**

{table(['Variable', 'Test', 'Groups (mean G3)', 'Statistic', 'Diff [95% CI] / robustness check', 'p', 'p (Holm)', 'Effect size', 'Significant?'], _test_rows(E, vi=False))}

**Pearson correlation with G3 (p-value and 95% CI of r):**

{table(['Variable', 'r', '95% CI', 'p'], _corr_rows(E))}

**Interpretation:**
- Significant after Holm correction: {', '.join(f'`{c}`' for c in f['sig']) or 'none'}. Not significant: {', '.join(f'`{c}`' for c in f['nonsig']) or 'none'}.
- Internet: the +{f['gt']['internet']['diff']} point gap has raw p = {_fmt_p(f['gt']['internet']['p'])} but Holm p = {_fmt_p(f['gt']['internet']['p_holm'])}, so it {'survives' if f['gt']['internet']['significant'] else '**does not survive**'} the multiple-testing correction. It should be presented as a weak, uncertain difference.
- Family support: CI [{f['gt']['famsup']['ci95'][0]}, {f['gt']['famsup']['ci95'][1]}] contains 0 → no evidence that `famsup` changes G3.
- Study time is significant but tiny (eta² = {f['gt']['studytime']['effect']}: it explains about {f['gt']['studytime']['effect'] * 100:.1f}% of G3 variance). Failures (eta² = {f['gt']['failures']['effect']}) and absences (eta² = {f['gt']['absence_level']['effect']}) matter more.
- {'ANOVA and Kruskal–Wallis agree in every case, so the conclusions do not depend on assuming normal grades.' if f['kw_agree'] else 'ANOVA and Kruskal–Wallis disagree for at least one variable; treat that result with caution.'}

**Why it can be trusted:** tests come from `scipy.stats` (standard implementations), use unequal-variance and
non-parametric variants where assumptions are doubtful, and are corrected for multiple testing.

{codes['_group_tests']}

{codes['_holm']}

{codes['_corr_tests']}

### 7.2 Multivariable regression: which factors still matter when the others are held fixed?

**What was done.** Single-variable comparisons (7.1) cannot tell whether a factor matters by itself or only travels
together with another one (e.g. internet ↔ better-educated parents). An **ordinary least-squares (OLS) regression**
estimates all factors at the same time: each coefficient **b** is the expected change in G3 (points) for +1 unit of that
variable **with every other variable held fixed**. Standard errors are HC3 (robust to unequal variances). Students with
G3 > 0 only. Two models:

- **Model A — background factors** ({len(dp.REG_FACTORS)} predictors: the main-question variables plus mother's/father's education, sex, age, address).
- **Model B — Model A + G1, G2**: what still matters once the intermediate grades are known.

{table(['Model', 'mat: n / R² / adj. R²', 'por: n / R² / adj. R²'], [[name, *[f"{f['reg'][s][key]['n']} / {f['reg'][s][key]['r2']} / {f['reg'][s][key]['adj_r2']}" for s in ('mat', 'por')]] for key, name in (('factors', 'A: background factors'), ('factors_plus_grades', 'B: A + G1, G2'))])}

R² = share of the variation in G3 explained by the model (0 = nothing, 1 = everything).

**Model A coefficients** (mat; last column repeats the same model on por as a replication):

{table(['Variable', 'b (G3 points)', '95% CI', 'p', 'Significant (mat)', 'por: b, significant'], _reg_rows(f, 'factors', dp.REG_FACTORS, vi=False))}

**Model B, grades only** (all background coefficients are in `summary.json → regression`):

{table(['Variable', 'b (G3 points)', '95% CI', 'p', 'Significant (mat)', 'por: b, significant'], _reg_rows(f, 'factors_plus_grades', dp.REG_GRADES, vi=False))}

**Interpretation:**
- Significant in **both** courses with everything else held fixed: {', '.join(_lbl(c, False) for c in f['reg_sig_both'])}.
- Internet: the raw gap was {f['gt']['internet']['diff']:+.2f}; with the other factors held fixed b = {f['reg']['mat']['factors']['coef']['internet_bin']['b']:+.2f} (p {_fmt_p(f['reg']['mat']['factors']['coef']['internet_bin']['p'])}) → {'still significant' if f['reg']['mat']['factors']['coef']['internet_bin']['significant'] else '**no independent effect**'}.
- Family support (`famsup`): b = {f['reg']['mat']['factors']['coef']['famsup_bin']['b']:+.2f} (p {_fmt_p(f['reg']['mat']['factors']['coef']['famsup_bin']['p'])}) → {'significant' if f['reg']['mat']['factors']['coef']['famsup_bin']['significant'] else 'no measurable effect'}.
- Background factors explain only R² = {f['reg']['mat']['factors']['r2']} (mat): most of the differences between students are *not* explained by these variables.
- Once G1 and G2 are known (Model B, R² = {f['reg']['mat']['factors_plus_grades']['r2']}), only {', '.join(_lbl(c, False) for c in f['reg_grades_sig']) or 'no background variable'} keep(s) a significant extra effect in mat: the intermediate grades already contain almost all the information.
- G1 and G2 are strongly correlated with each other (r = {E['corr_G1_G2_G3']['G1_G2']}), so Model B cannot reliably split their effect: read only R² and the combined effect of the two grades, and do not compare b(G1) with b(G2).
- Regression adjusts only for variables that are in the data; it shows associations, not causes.

{codes['_ols']}

{codes['_regression']}

## 8. Charts

The first three images are written by the pipeline (`analyze()` → `_plot_charts()`), never drawn by hand.
Deleting `images/` and running `python main.py` recreates them. A fourth, context chart for PISA is in section 10.2.

### 8.1 Chart 1 — Grouped bar chart: mean G3 by study time and internet access

![Chart 1]({IMG['bar']})

**Definition.** A grouped bar chart compares the *mean* of one numeric variable (G3) across combinations of two
categorical variables (study-time bucket × internet at home). Data: {E['n']} students (dropout suspects excluded).

| Element | What it shows |
|---|---|
| X axis | Weekly study-time bucket: 1 = <2h, 2 = 2–5h, 3 = 5–10h, 4 = >10h |
| Y axis | Mean final grade G3 on the 0–20 scale (axis fixed to 0–20 so bar heights are comparable) |
| Blue bar | Students **without** internet at home |
| Orange bar | Students **with** internet at home |
| Black whisker (error bar) | 95% confidence interval of the mean: mean ± 1.96·std/√n. Wide whisker = uncertain mean |
| `n=` label | Number of students in that bar |
| Hatched, faded bar | Fewer than {dp.MIN_RELIABLE_N} students: the mean is not reliable, do not draw conclusions from it |
| Legend | Colour → internet group |

**How to read it:** compare bar heights *together with* their whiskers; if two whiskers overlap a lot, the
difference is not reliable. Hatched bars (n < {dp.MIN_RELIABLE_N}): {', '.join(f"studytime {k.split('|')[0]} & internet={k.split('|')[1]} (n={n})" for k, n in f['small_groups']) or 'none'}.

**Takeaway:** with internet {E['by_internet']['yes']['mean']} vs without {E['by_internet']['no']['mean']} overall, but this gap is
{'significant' if f['gt']['internet']['significant'] else '**not significant** after Holm correction (section 7.1)'}; overlapping whiskers in the chart show the same thing.
Study time shows only a weak upward trend (r = {E['corr_full']['G3']['studytime']}).

{codes['_plot_bar']}

### 8.2 Chart 2 — Histogram of final grades (G3)

![Chart 2]({IMG['hist']})

**Definition.** A histogram splits a numeric variable into bins and shows how many observations fall in each bin.
Here each bin is exactly one grade point (bins centred on 0, 1, …, 20). Data: all {A['n']} students.

| Element | What it shows |
|---|---|
| X axis | Final grade G3 (0–20) |
| Y axis | Number of students with that grade |
| Blue bars | Students with G3 > 0 |
| Red bar at 0 | Dropout suspects (G3 = 0, n = {dpf['n']}) |
| Dashed vertical line | Pass mark: left of the line = fail (G3 < {dp.PASS_MARK}), right = pass (G3 ≥ {dp.PASS_MARK}) |
| Text box | Pass rate for all students and after excluding dropout suspects |
| Legend | Colour / line meaning |

**Takeaway:** the distribution of real grades is roughly bell-shaped around {f['mode_g3']} (most frequent grade), with a
separate spike at 0 and an empty gap at 1–3 ({f['gap_1_3']} students) — visual evidence that the zeros are a different
phenomenon, not the low tail of the grade distribution.

{codes['_plot_hist']}

### 8.3 Chart 3 — Correlation heatmap

![Chart 3]({IMG['heat']})

**Definition.** A heatmap shows a matrix of numbers as colours. Each cell is the **Pearson correlation
coefficient** r between two variables: r = cov(X, Y) / (σX·σY), ranging from −1 (perfect negative linear
relationship) through 0 (no linear relationship) to +1 (perfect positive). Data: {E['n']} students (dropout suspects excluded).

| Element | What it shows |
|---|---|
| Rows / columns | Variables: G1, G2, G3 (grades), studytime (1–4), failures (0–3), absences (count), famsup (1 = yes, 0 = no) |
| Cell colour | Red = positive r, blue = negative r, white ≈ 0; darker = stronger |
| Number in cell | Value of r (2 decimals) |
| Diagonal (1.00) | Each variable with itself — always 1 |
| Blank upper triangle | Hidden because the matrix is symmetric (r(X,Y) = r(Y,X)) |
| Colour bar | Maps colour to r from −1 to +1 |

Note: `famsup` is 0/1, so its r is the point-biserial correlation (same formula).

**Takeaway — correlations with G3, strongest first:** {', '.join(f"{k.replace('_bin', '')} {v:+.3f}" for k, v in top)}.

{codes['_plot_heatmap']}

## 9. Early-warning risk rule

**What was done:** `classify_risk()` uses **only information available before the final exam** (G1, G2,
failures, absences — never G3), so it can be honestly evaluated against the real pass/fail outcome.

- high: G2 < {dp.G_WARN} or failures ≥ {dp.FAIL_HIGH}
- medium: G1 < {dp.G_WARN} or failures ≥ 1 or absences ≥ {dp.ABS_HIGH}
- low: otherwise

{codes['classify_risk']}

**Evaluation on all {A['n']} students** (flag = risk group "high", truth = G3 < {dp.PASS_MARK}):

{table(['', 'actually fail', 'actually pass'], _confusion(risk))}

- **Recall** = TP / (TP + FN) = {h['tp']} / {h['tp'] + h['fn']} = **{pct(h['recall'])}** of real fails are flagged early (95% CI {pct(h['recall_ci95'][0])}–{pct(h['recall_ci95'][1])}).
- **Precision** = TP / (TP + FP) = {h['tp']} / {h['tp'] + h['fp']} = **{pct(h['precision'])}** of flagged students really fail (95% CI {pct(h['precision_ci95'][0])}–{pct(h['precision_ci95'][1])}).
- Fail rate per group: {', '.join(f"{k} {pct(v)}" for k, v in risk['fail_rate_by_group'].items())}.

{codes['_risk_eval']}

**Out-of-sample test (holdout).** The thresholds above were chosen while looking at the mathematics data, so the
numbers above are *in-sample* and may be optimistic. To check, the **same frozen rule** (no threshold changed) is
applied to the Portuguese course, which the rule never saw. Because many pupils take both courses, a strict holdout
keeps only Portuguese students whose 13 identifying columns (`MERGE_KEYS`, as in `student-merge.R`) do not appear in
the mathematics file. Confidence intervals are 95% Wilson intervals.

{table(['Dataset', 'n', 'Fail rate', 'TP / FP / FN', 'Recall [95% CI]', 'Precision [95% CI]'], _holdout_rows(r, vi=False))}

**Interpretation:**
- **Recall** on unseen students: {pct(f['ho']['recall'])} vs {pct(h['recall'])} in-sample — the rule still catches {f['ho']['tp']} of {f['ho']['tp'] + f['ho']['fn']} future fails.
- **Precision drops** ({pct(f['ho']['precision'])} vs {pct(h['precision'])}): more false alarms. Part of this is because fewer students fail in Portuguese (fail rate {pct(f['ho_ev']['fail_rate'])} vs {pct(risk['fail_rate'])}); precision always falls when the outcome is rarer.
- Conclusion: the rule is a good *screening* tool (few missed fails), not a precise prediction; the honest numbers to quote are the holdout ones.

{codes['_wilson']}

{codes['_risk_holdout']}

**Are three tiers justified (low / medium / high)?** The table shows how many students in each tier actually fail
(Wilson 95% CI), and whether "medium" is really riskier than "low" (relative risk, Fisher's exact test — suitable for
small counts).

{table(['Dataset', 'low: fails / n', 'medium: fails / n', 'high: fails / n', 'medium vs low'], _tier_rows(f['r'], vi=False))}

{"Medium students fail several times more often than low students both on the data the rule was built on and on unseen students (Fisher's exact test significant in both), while still far below high. The three tiers therefore carry information and map to three actions: **high → intervene now**, **medium → monitor**, **low → no action**. Headline precision/recall use the high tier as the alert." if f['tier_ok'] else "Medium is not reliably riskier than low on unseen students, so the rule should be used as two tiers (high vs not high)."}

{codes['_tier_eval']}

**Why it can be trusted:** no leakage (G3 is not an input — visible in `classify_risk()`), uncertainty is shown as
confidence intervals, and performance is verified on students the rule was never tuned on.

## 10. Context

### 10.1 Mathematics vs Portuguese (replication)

{table(['Metric', 'mat', 'por'], [[k, f["sc"]['mat'][k], f["sc"]['por'][k]] for k in f["sc"]['mat']])}

The direction of every key correlation (G2, absences, failures vs G3) is {'**the same**' if f['same_sign'] else '**not** the same'} in both courses.

{_paired_text(f, vi=False)}

{codes['_subject_comparison']}

{codes['_paired_subjects']}

### 10.2 PISA: Portugal vs OECD average

The UCI students come from two Portuguese schools (2005–2006 school year, Cortez & Silva 2008). PISA gives
**country-level** context only; it is never joined to student rows.

{table(['Subject', 'Year', 'Portugal', 'OECD average', 'Difference', 'Portugal rank'], _pisa_rows(f))}

Mathematics: Portugal {pm[min(pm, key=int)]['portugal'] if pm else '—'} in {min(pm, key=int) if pm else '—'} → {pm[pl['mathematics']]['portugal'] if pm else '—'} in {pl.get('mathematics', '—')} (OECD {pm[pl['mathematics']].get('oecd_average', '—') if pm else '—'}).

{codes['_pisa_context']}

#### Chart 4 — PISA trend: Portugal vs OECD average

![Chart 4]({IMG['pisa']})

**Definition.** A line chart shows how a value changes over time. Each panel is one PISA subject; each point is the
national mean PISA score in one test cycle (PISA scores are scaled so the OECD mean was about 500 when each subject was
first the main domain). Data: `pisa_clean.csv` ({f['n_pisa_clean']} rows), cross-checked with OECD in section 3.4.

| Element | What it shows |
|---|---|
| Panels | Mathematics, Reading, Science (science starts in 2006 in the comparison table) |
| X axis | PISA cycle year (2000, 2003, …, 2022, {dp.OECD_PISA_YEAR}) |
| Y axis | Mean PISA score (shared across panels so levels are comparable) |
| Blue solid line, circles | Portugal |
| Grey dashed line, squares | OECD average |
| Number at the end of each line | Latest ({dp.OECD_PISA_YEAR}) score |
| Orange band | 2005–06, the school year in which the UCI students were surveyed |

**How to read it:** the vertical gap between the two lines is Portugal's distance from the OECD average in that year.

**Takeaway:** in mathematics Portugal went from {pm[min(pm, key=int)]['portugal'] if pm else '—'} ({min(pm, key=int) if pm else '—'}, OECD {pm[min(pm, key=int)].get('oecd_average', '—') if pm else '—'}) to
{pm[pl['mathematics']]['portugal'] if pm else '—'} ({pl.get('mathematics', '—')}, OECD {pm[pl['mathematics']].get('oecd_average', '—') if pm else '—'}). {f"It first reached the OECD average in {f['catch_up']} and has since moved together with it." if f['catch_up'] else 'It has not reached the OECD average in any cycle.'}
{'At the time of the UCI data (orange band, closest cycle 2006) Portugal was below the OECD average in every subject.' if f['below_2006'] else 'In 2006 (closest cycle to the UCI data) Portugal was not below the OECD average in every subject.'}

{codes['_plot_pisa']}

## 11. Pipeline (OOP) and outputs

`main.py` runs: `fetch_uci_raw` → `scrape_pisa_table` (cache-first) → `load_data` → `clean_data` → `analyze`
(+ charts) → `export_results` → this report.

{codes['main']}

{codes['analyze']}

{codes['export_results']}

| Output | Content |
|---|---|
| `data/processed/cleaned_students.csv` | {f['log']['rows_out']} rows (both subjects, column `subject`), encoded columns, derived columns, 6 anomaly flags |
| `data/processed/cleaned_students_mat.csv`, `cleaned_students_por.csv` | same columns, one file per subject ({f['n_raw'].get('mat')} / {f['n_raw'].get('por')} rows), no `subject` filter needed |
| `data/processed/pisa_clean.csv` | {f['n_pisa_clean']} clean PISA rows |
| `data/processed/summary.json` | all statistics in this report |
| `images/*.png` | 3 required charts + 1 PISA context chart |
| `report.md`, `report_vi.md` | this report (EN / VI) |

## 12. Why the results can be trusted (verification summary)

| Check | Result |
|---|---|
| Raw data identical to UCI download | Downloaded from the official URL; {f['n_raw'].get('mat')} / {f['n_raw'].get('por')} rows, {f['n_cols']} columns as documented |
| Cleaning checks (types, ranges, yes/no, duplicates, missing) | All counted in `cleaning_log`; total issues found = {f['invalid_total']} |
| G3 = 0 handled explicitly | Flagged; {dpf['n_absences_zero']}/{dpf['n']} have 0 absences; results shown with and without them |
| Sensitivity | Headline conclusions compared across `all` vs `exclude_dropout` (section 6) |
| Replication | Same correlation directions in the Portuguese course: {'yes' if f['same_sign'] else 'no'} |
| No leakage in risk rule | G3 is not an input of `classify_risk()` |
| Significance tests | Welch t / ANOVA + Kruskal–Wallis, Holm-corrected; significant: {', '.join(f['sig'])}; not significant: {', '.join(f['nonsig'])} |
| Multivariable regression | OLS with HC3 errors; Model A R² = {f['reg']['mat']['factors']['r2']}; significant in both courses: {', '.join(f['reg_sig_both'])} |
| Sensitivity to the zeros | Absences effect negative and significant in every scenario without zeros, both courses: {'yes' if f['abs_robust'] else 'no'} |
| Risk tiers | Medium vs low fail risk ×{f['r']['risk_eval']['all']['tiers']['medium_vs_low']['relative_risk']} (mat), ×{f['r']['risk_eval']['holdout_por_only']['tiers']['medium_vs_low']['relative_risk']} (unseen por); significant in both: {'yes' if f['tier_ok'] else 'no'} |
| Risk rule out-of-sample | Frozen rule on unseen Portuguese-only students: recall {pct(f['ho']['recall'])}, precision {pct(f['ho']['precision'])} |
| PISA scrape | Structural validation + pinned Wikipedia revision {ps.get('revision_id')} |
| PISA vs official OECD | {dp.OECD_PISA_YEAR}: {f['oc'][str(dp.OECD_PISA_YEAR)]['n_within_tolerance']}/{f['oc'][str(dp.OECD_PISA_YEAR)]['n_compared']} scores identical; 2022 (derived): {f['oc'][str(dp.OECD_PISA_YEAR - 3)]['n_within_tolerance']}/{f['oc'][str(dp.OECD_PISA_YEAR - 3)]['n_compared']} within ±1 |
| Charts | Generated by code shown in section 8; reproducible with `python main.py` |
| Report numbers | Generated from the pipeline results by `report_builder.py`; cannot go stale |

## 13. Limitations and next steps

- One subject/year as primary cohort; small groups (see Chart 1 `n=` labels) give wide confidence intervals.
- Regression adjusts only for variables in the data; unmeasured factors (motivation, teachers, income) can still confound, so effects are associations, not causes.
- "Dropout suspect" is inferred from the data, not confirmed by the schools; the sensitivity analysis (6.1) shows the absences conclusion does not depend on it.
- The holdout set shares the schools and the school year with the training data, and the strict holdout is small (n = {f['ho_ev']['n']}); precision on new schools could differ.
- PISA {dp.OECD_PISA_YEAR} and 2022 values are verified against the OECD report; earlier cycles (2000–2018) come from Wikipedia only.
- All findings are correlational, not causal.

*Reproduce: `pip install -r requirements.txt` then `python main.py` (add `--refresh-pisa` to re-scrape Wikipedia).*
""")
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Vietnamese
# ---------------------------------------------------------------------------
def render_vi(f: dict, codes: dict) -> str:
    r, A, E, dpf, risk = f["r"], f["A"], f["E"], f["dp"], f["risk"]
    h = risk["high"]
    ps = f["pisa_src"]
    top = f["corr_g3_sorted"]
    pl = f["pisa_latest"]
    pm = f["pisa"].get("mathematics", {})
    yn = {"yes": "có", "no": "không"}
    return f"""# Báo cáo P1 — Các yếu tố ảnh hưởng đến điểm cuối kỳ (UCI Student Performance, `{f['subj']}`)

> Báo cáo được sinh tự động bởi `report_builder.py` ngày {f['today']}, từ cùng kết quả được ghi vào
> `data/processed/summary.json`. Mọi con số do pipeline tính ra, mọi đoạn code được đọc trực tiếp từ file
> nguồn hiện tại, nên báo cáo không thể lệch với code hay dữ liệu. Tạo lại bằng `python main.py`.

**Câu hỏi chính:** Thời gian tự học, số buổi vắng, hỗ trợ từ gia đình và điểm giữa kỳ (G1, G2) liên quan
thế nào đến điểm cuối kỳ (G3)?

## 1. Tóm tắt

| Câu hỏi | Trả lời (môn Toán, {E['n']} học sinh có G3 > 0, trừ khi ghi khác) |
|---|---|
| Điểm giữa kỳ → G3 | Liên hệ mạnh nhất: r(G2, G3) = **{E['corr_G1_G2_G3']['G2_G3']}**, r(G1, G3) = {E['corr_G1_G2_G3']['G1_G3']} |
| Số lần trượt trước → G3 | 0 lần: **{E['by_failures']['0']['mean']}**, 1: {E['by_failures']['1']['mean']}, 2: {E['by_failures']['2']['mean']}, 3: {E['by_failures']['3']['mean']} (r = {E['corr_full']['G3']['failures']}) |
| Vắng học → G3 | thấp {E['by_absence_level']['low']['mean']} / trung bình {E['by_absence_level']['medium']['mean']} / cao {E['by_absence_level']['high']['mean']} (r = **{E['corr_full']['G3']['absences']}**, ANOVA p Holm {_fmt_p(f['gt']['absence_level']['p_holm'])}) |
| Thời gian tự học → G3 | dương nhưng yếu, r = {E['corr_full']['G3']['studytime']} (ANOVA p Holm {_fmt_p(f['gt']['studytime']['p_holm'])}, eta² = {f['gt']['studytime']['effect']}: rất nhỏ) |
| Internet ở nhà → G3 | có {f['gt']['internet']['mean_yes']} vs không {f['gt']['internet']['mean_no']}; p gốc {_fmt_p(f['gt']['internet']['p'])}, p Holm {_fmt_p(f['gt']['internet']['p_holm'])} → **{'có ý nghĩa thống kê' if f['gt']['internet']['significant'] else 'không còn ý nghĩa sau hiệu chỉnh'}** |
| Xét tất cả yếu tố cùng lúc (hồi quy) | các yếu tố nền giải thích R² = {f['reg']['mat']['factors']['r2']}; có ý nghĩa ở cả 2 môn khi giữ các yếu tố khác cố định: **{', '.join(_lbl(c, True) for c in f['reg_sig_both'])}**; internet sau điều chỉnh b = {f['reg']['mat']['factors']['coef']['internet_bin']['b']:+.2f} (p {_fmt_p(f['reg']['mat']['factors']['coef']['internet_bin']['p'])}) |
| Hỗ trợ gia đình (`famsup`) → G3 | có {E['by_famsup']['yes']['mean']} vs không {E['by_famsup']['no']['mean']} (p Holm {_fmt_p(f['gt']['famsup']['p_holm'])}): **{'có khác biệt' if f['gt']['famsup']['significant'] else 'không có khác biệt có ý nghĩa'}** |
| Tỉ lệ đỗ | {pct(A['pass_rate'])} trên toàn bộ {A['n']} học sinh; {pct(E['pass_rate'])} sau khi bỏ {dpf['n']} em nghi bỏ thi |
| Rule cảnh báo sớm (không dùng G3) | đặt trên mat: recall {pct(h['recall'])}, precision {pct(h['precision'])}; **kiểm tra trên học sinh môn Bồ Đào Nha chưa từng thấy: recall {pct(f['ho']['recall'])}, precision {pct(f['ho']['precision'])}** |

**Phát hiện quan trọng về chất lượng dữ liệu:** {dpf['n']} học sinh có G3 = 0 và **{dpf['n_absences_zero']} em trong số đó có
0 buổi vắng được ghi nhận**. Nhóm này được gắn cờ *dropout suspect* (nghi bỏ thi), không xoá. Nếu để lẫn vào, tương quan
vắng học–G3 thành r = {A['corr_full']['G3']['absences']} và che mất ảnh hưởng tiêu cực thật sự của vắng học.

## 2. Đối chiếu yêu cầu đề bài

| Yêu cầu (bảng đề) | Thực hiện ở đâu | Mục |
|---|---|---|
| Dataset UCI Student Performance (`student.zip`) | `fetch_uci_raw()` | 3.1 |
| Web scraping Wikipedia PISA | `scrape_pisa_table()`, `_parse_pisa_html()`, `validate_pisa_raw()` | 3.2 |
| Lưu raw CSV | `data/raw/student-*.csv`, `data/raw/pisa_reference.csv` | 3 |
| Làm sạch kiểu dữ liệu, encode yes/no | `clean_data()` | 5 |
| 4 hàm cơ bản (yes/no, pass/fail, phân loại vắng, điểm trung bình) | `convert_yes_no`, `calc_pass_fail`, `classify_absences`, `calc_average_grade` | 4 |
| list of dicts, dict mapping, set trường/nghề, tuple ngưỡng | `SAMPLE_STUDENTS`, `VAR_DESCRIPTIONS`, `set()` trong `analyze()`, `THRESHOLDS` | 4 |
| EDA bằng groupby, mean, std | `_grp()`, `_scope_stats()` | 7 |
| So sánh G3 theo studytime, absences, failures, internet | các bảng `by_*` | 7 |
| Tính pass/fail; phân nhóm rủi ro học tập | `pass_fail`, `classify_risk()`, `_risk_eval()` | 7, 9 |
| Tương quan G1, G2, G3 | `corr_G1_G2_G3`, heatmap | 7, 8.3 |
| Vẽ bar, histogram, heatmap | `_plot_bar`, `_plot_hist`, `_plot_heatmap` | 8 |
| OOP: `load_data()`, `clean_data()`, `analyze()`, `export_results()`; `main.py` xuất `cleaned_students.csv` + `summary.json` | `StudentDataProcessor`, `main.py` | 11 |
| Insight và giới hạn dữ liệu | — | 12, 13 |

## 3. Thu thập dữ liệu

### 3.1 UCI Student Performance

**Đã làm gì:** chỉ khi chưa có file raw thì mới tải file zip chính thức của UCI, rồi giải nén `student.zip`
bên trong vào `data/raw/`. File raw không bao giờ bị sửa sau đó.

| File | Số dòng | Số cột | Vai trò |
|---|---|---|---|
| `student-mat.csv` | {f['n_raw'].get('mat')} | {f['n_cols']} | Phân tích chính (môn Toán) |
| `student-por.csv` | {f['n_raw'].get('por')} | {f['n_cols']} | Đối chứng / so sánh (môn Bồ Đào Nha) |

{codes['fetch_uci_raw']}

**Vì sao tin được:** URL là link tải chính thức của UCI; file giữ nguyên như UCI phát hành; số dòng/cột khớp
mô tả của UCI (395 / 649 học sinh, 33 thuộc tính).

### 3.2 Cào dữ liệu PISA từ Wikipedia

**Đã làm gì:**
1. `requests.get` tải HTML của [bài viết PISA]({ps.get('url', dp.PISA_URL)}) (không cần trình duyệt vì bảng nằm sẵn trong HTML).
2. `BeautifulSoup` tìm mọi `table.wikitable` và giữ 2 loại bảng:
   - **summary**: bảng xếp hạng mới nhất (`Rank | Country/economy | Score`), mỗi môn 1 bảng con;
   - **comparison**: "Rankings comparison 2000–2022", mỗi nước 1 dòng với cặp `score, rank` theo từng năm (chuyển từ dạng rộng sang dạng dài).
3. Kết quả ({f['n_pisa_raw']} dòng, giữ nguyên chuỗi gốc của trang) lưu vào `data/raw/pisa_reference.csv`.
4. Cơ chế **cache-first**: chạy bình thường thì đọc file đã lưu; muốn cào lại thì chạy `python main.py --refresh-pisa`.

| Nguồn gốc | Giá trị |
|---|---|
| Phiên bản (revision) Wikipedia | [{ps.get('revision_id')}]({ps.get('permalink')}) |
| Thời điểm cào (UTC) | {ps.get('scraped_at')} |
| Số dòng thô | {ps.get('n_rows')} |
| Giấy phép | CC BY-SA 4.0 (Wikipedia) |
| User-Agent | `{dp.HTTP_HEADERS['User-Agent']}` |

{codes['scrape_pisa_table']}

{codes['_parse_pisa_html']}

**Vì sao tin được — kiểm tra cấu trúc.** Mọi bảng cào về (và mọi lần đọc cache) phải qua `validate_pisa_raw()`;
không đạt thì bị loại và giữ nguyên cache cũ:

- cả 2 loại bảng đều có đủ 3 môn;
- năm là số trong khoảng 2000 đến năm hiện tại;
- mọi điểm nằm trong [{dp.PISA_SCORE_MIN}, {dp.PISA_SCORE_MAX}];
- mỗi (nguồn, môn, năm) có ≥ {dp.PISA_MIN_COUNTRIES} nước có điểm, hạng là số, không trùng nước và có đúng 1 dòng trung bình OECD.

{codes['validate_pisa_raw']}

### 3.3 Làm sạch PISA

Bỏ chú thích (`[41]`) và dấu `*` cuối tên nước, `—` (không tham gia) thành giá trị thiếu, rank/score/year đổi
sang số, "International Average (OECD)" đổi tên thành `OECD average`. Kết quả: {f['n_pisa_clean']} dòng trong
`data/processed/pisa_clean.csv`.

{codes['clean_pisa']}

### 3.4 Đối chiếu với báo cáo chính thức của OECD

**Đã làm gì.** Wikipedia là nguồn thứ cấp, nên số liệu cào về được so với **ấn phẩm chính thức của OECD**:
{f['osrc'].get('source', '—')}, {f['osrc'].get('table', '—')} ([DOI]({f['osrc'].get('doi', '#')}), giấy phép {f['osrc'].get('licence', '—')}).
Bảng này được trích một lần từ file PDF của OECD vào `data/raw/oecd_pisa2025_table_I1.csv` ({f['osrc'].get('n_rows', '—')} dòng:
trung bình OECD + mọi quốc gia tham gia). Có 5 tên nước khác nhau giữa 2 nguồn và đã được ánh xạ
(`OECD_NAME_ALIASES`, vd "Chinese Taipei" → "Taiwan").

{table(['Kỳ thi', 'Cách so', 'Số cặp so', 'Trong ngưỡng', 'Khớp tuyệt đối', 'Lệch lớn nhất', 'Không khớp (Wikipedia vs OECD)'], _oecd_rows(f, vi=True))}

Nước có trong bảng OECD nhưng thiếu trong bảng Wikipedia: {'; '.join(f"{s}: {', '.join(v)}" for s, v in f['oc']['missing_in_wikipedia'].items() if v) or 'không có'}.

**Bồ Đào Nha và trung bình OECD (các dòng báo cáo này thực sự dùng):**

{table(['Quốc gia', 'Môn', 'Wikipedia', 'OECD chính thức', 'Khớp'], f['pt_check'])}

**Vì sao tin được:** mọi điểm {dp.OECD_PISA_YEAR} cào từ Wikipedia đều trùng với giá trị chính thức của OECD; điểm 2022
(suy ra từ cột mức thay đổi của OECD) khớp trong phạm vi làm tròn, trừ các dòng ghi ở cột không khớp, và các dòng đó không
ảnh hưởng đến Bồ Đào Nha. Các kỳ cũ hơn (2000–2018) không có trong bảng OECD này nên vẫn chỉ dựa vào Wikipedia.

{codes['cross_check_pisa']}

## 4. Python cơ bản theo yêu cầu đề

Cấu hình (tuple, dict mapping, list of dicts) — code thật:

{codes['config']}

Bốn hàm cơ bản:

{codes['convert_yes_no']}

{codes['calc_pass_fail']}

{codes['classify_absences']}

{codes['calc_average_grade']}

`set()` các giá trị duy nhất (tính trong `analyze()`): trường = `{r['unique_schools']}`, nghề của mẹ = `{r['unique_mjobs']}`, nghề của bố = `{r['unique_fjobs']}`.

## 5. Làm sạch dữ liệu

**Đã làm gì** (`StudentDataProcessor.clean_data()`, theo thứ tự: ép kiểu → kiểm tra → loại bỏ → tạo cột → gắn cờ).
Số dòng vào: {f['log']['rows_in']} (cả 2 môn) → số dòng ra: {f['log']['rows_out']}.

{table(['Bước', 'Cách làm', 'Số dòng/ô bị ảnh hưởng'], _clean_rows(f['log'], vi=True))}

Cột tạo thêm: `pass_fail` (G3 ≥ {dp.PASS_MARK}), `absence_level` (thấp 0–{dp.ABS_MED - 1} / trung bình {dp.ABS_MED}–{dp.ABS_HIGH - 1} / cao ≥ {dp.ABS_HIGH}),
`avg_grade` (G1+G2+G3)/3 (chỉ để mô tả: chứa biến mục tiêu G3 nên KHÔNG dùng làm biến dự báo để tránh rò rỉ dữ liệu / target leakage; dùng `avg_g1g2` khi dự báo sớm), `avg_g1g2`, `risk_group`, và 6 cột cờ bất thường.
{codes['load_data']}

{codes['clean_data']}

**Vì sao tin được:** mỗi bước kiểm tra đều *đếm* số giá trị nó thay đổi và lưu vào `summary.json → cleaning_log`.
Tổng cộng {f['invalid_total']} lỗi — tức dữ liệu UCI gốc sạch về cấu trúc; vấn đề thật duy nhất là về ý nghĩa (G3 = 0, mục 6).
Không có gì bị ép ngầm: giá trị lạ sẽ thành NaN và hiện ra trong các con số đếm này.

### 5.1 Cờ bất thường (gắn cờ, không xoá)

{table(['Cờ', 'Điều kiện', f"Số dòng ({f['subj']})", 'Số dòng (por)', 'Ý nghĩa'], _flag_rows(f, vi=True))}

Ngưỡng lấy từ tuple `ANOMALY_THRESHOLDS = {dp.ANOMALY_THRESHOLDS}` (hệ số IQR, mức tụt G1, mức tụt G2, tuổi).
Ngưỡng IQR tính riêng cho từng môn vì phân phối số buổi vắng của 2 môn khác nhau.

## 6. Nhóm nghi bỏ thi (G3 = 0)

| Bằng chứng | Giá trị |
|---|---|
| Số học sinh có G3 = 0 | {dpf['n']} |
| … trong đó số buổi vắng = 0 | **{dpf['n_absences_zero']} / {dpf['n']}** |
| … trong đó G2 = 0 | {dpf['n_g2_zero']} |
| G1 / G2 trung bình của nhóm | {dpf['mean_G1']} / {dpf['mean_G2']} |
| Tỉ lệ vắng = 0 ở các học sinh còn lại | {pct(dpf['share_absences_zero_others'])} |
| Số học sinh có G3 từ 1 đến 3 | {f['gap_1_3']} (khoảng trống ngay trước cột 0) |

**Diễn giải:** các em này vẫn có điểm G1 thật, rồi điểm cuối kỳ bằng 0 và 0 buổi vắng được ghi nhận. Điểm 0/20
thật sau khi G1 ≈ {dpf['mean_G1']} là khó tin; giải thích hợp lý là "không dự thi / nghỉ học, số buổi vắng không được ghi".
Các em vẫn nằm trong `cleaned_students.csv` với `dropout_suspect = True`, và mọi thống kê được báo cáo 2 lần:
**all** (n = {A['n']}) và **exclude_dropout** (n = {E['n']}).

| Chỉ số | all (n={A['n']}) | exclude_dropout (n={E['n']}) |
|---|---|---|
| Tỉ lệ đỗ | {pct(A['pass_rate'])} | **{pct(E['pass_rate'])}** |
| r(G2, G3) | {A['corr_G1_G2_G3']['G2_G3']} | **{E['corr_G1_G2_G3']['G2_G3']}** |
| r(G1, G3) | {A['corr_G1_G2_G3']['G1_G3']} | **{E['corr_G1_G2_G3']['G1_G3']}** |
| r(vắng học, G3) | {A['corr_full']['G3']['absences']} | **{E['corr_full']['G3']['absences']}** |
| r(số lần trượt, G3) | {A['corr_full']['G3']['failures']} | **{E['corr_full']['G3']['failures']}** |

### 6.1 Phân tích độ nhạy: kết luận có phụ thuộc vào cách xử lý các số 0 không?

**Đã làm gì.** Có 2 giả định có thể sai: (1) G3 = 0 nghĩa là "bỏ thi", và (2) absences = 0 nghĩa là "không vắng buổi nào" —
cũng có thể là "không được ghi nhận". Vì vậy phân tích vắng học được lặp lại theo 3 kịch bản, ở cả 2 môn, rồi so sánh kết quả.

{table(['Môn', 'Kịch bản', 'n', 'r(vắng, G3) [CI 95%]', 'p', 'G3 trung bình: vắng thấp / vừa / cao', 'ANOVA p', 'Tỉ lệ đỗ'], _sens_rows(f, vi=True))}

Mẫu hình bỏ thi ở cả 2 môn: {', '.join(f"{s}: {v['dropout_pattern']['n_dropout_absences_zero']}/{v['dropout_pattern']['n_dropout']} em nghi bỏ thi có absences = 0 (so với {pct(v['dropout_pattern']['share_absences_zero_others'])} ở các em còn lại)" for s, v in f['sens'].items())}.

**Diễn giải:**
- {'Ở mọi kịch bản đã bỏ các số 0, vắng học đều có quan hệ **âm và có ý nghĩa** với G3 ở cả 2 môn. Kết luận vẫn đúng dù giả định bỏ thi đúng hay sai, và dù absences = 0 là thật hay do không ghi nhận.' if f['abs_robust'] else 'Có ít nhất một kịch bản đã bỏ số 0 mà quan hệ âm không có ý nghĩa; kết luận về vắng học phụ thuộc vào cách xử lý số 0.'}
- Chỉ kịch bản "toàn bộ học sinh" làm mờ hoặc che mất ảnh hưởng — đúng là sự méo mó do các dòng G3 = 0 gây ra.
- Mẫu hình bỏ thi (G3 = 0 luôn đi kèm absences = 0) xuất hiện ở cả 2 môn, củng cố cách hiểu "không dự thi / nghỉ học" thay vì điểm thật.

{codes['_sensitivity']}

## 7. Phân tích khám phá (groupby → mean ± std, n)

Mỗi ô là *G3 trung bình ± độ lệch chuẩn (n học sinh)*. In đậm = phạm vi dùng cho kết luận chính.

**Theo thời gian tự học mỗi tuần**

{table(['Studytime', 'all', 'exclude_dropout'], grp_rows(A['by_studytime'], E['by_studytime'], label=lambda k: f"{k} ({STUDY_LABEL[k]})"))}

**Theo mức độ vắng** — {'G3 trung bình giảm dần từ vắng thấp đến vắng cao' if f['abs_monotonic'] else 'không giảm đều'} khi đã bỏ nhóm nghi bỏ thi.

{table(['Mức vắng', 'all', 'exclude_dropout'], grp_rows(A['by_absence_level'], E['by_absence_level'], order=['low', 'medium', 'high'], label=lambda k: {'low': 'thấp (low)', 'medium': 'trung bình (medium)', 'high': 'cao (high)'}[k]))}

**Theo số lần trượt trước đây**

{table(['Số lần trượt', 'all', 'exclude_dropout'], grp_rows(A['by_failures'], E['by_failures']))}

{_fail_steps_text(f['fail_steps'], vi=True)}

**Theo internet ở nhà / hỗ trợ gia đình / hỗ trợ của trường / học thêm có trả phí**

{table(['Nhóm', 'all', 'exclude_dropout'], [['internet = ' + yn[k], *grp_rows(A['by_internet'], E['by_internet'], order=[k])[0][1:]] for k in ['no', 'yes']] + [['famsup = ' + yn[k], *grp_rows(A['by_famsup'], E['by_famsup'], order=[k])[0][1:]] for k in ['no', 'yes']] + [['schoolsup = ' + yn[k], *grp_rows(A['by_schoolsup'], E['by_schoolsup'], order=[k])[0][1:]] for k in ['no', 'yes']] + [['paid = ' + yn[k], *grp_rows(A['by_paid'], E['by_paid'], order=[k])[0][1:]] for k in ['no', 'yes']])}

Lưu ý: học sinh `schoolsup = có` điểm thấp hơn vì trường *dành* hỗ trợ cho em học yếu (quan hệ nhân quả ngược) —
đây không phải bằng chứng hỗ trợ làm giảm điểm.

{codes['_grp']}

{codes['_scope_stats']}

### 7.1 Kiểm định thống kê: chênh lệch là thật hay do ngẫu nhiên?

**Đã làm gì.** Với mỗi so sánh ở trên, kiểm định thống kê trả lời: *nếu các nhóm thực sự có cùng G3 trung bình, thì
khả năng thấy chênh lệch lớn cỡ này chỉ do ngẫu nhiên là bao nhiêu?* Xác suất đó là **p-value**; chênh lệch được gọi là
có ý nghĩa thống kê khi p < α = {dp.ALPHA}.

| Phương pháp | Dùng cho | Vì sao chọn |
|---|---|---|
| Welch t-test | biến có/không (internet, famsup, schoolsup, paid) | So 2 trung bình mà không giả định phương sai bằng nhau (cỡ nhóm chênh nhiều, vd 58 vs 299) |
| ANOVA một chiều (F) | studytime (4 mức), mức vắng (3), số lần trượt ({len(f['gt']['failures']['levels'])}: {', '.join(f['gt']['failures']['levels'])}) | So ≥ 3 trung bình trong một kiểm định. Mức trượt 2 và 3 mỗi mức chỉ khoảng chục học sinh nên được gộp thành một nhóm "2+" khi kiểm định (bảng mô tả ở mục 7 vẫn giữ đủ 4 mức) |
| Kruskal–Wallis (H) | giống ANOVA | Kiểm tra lại dựa trên thứ hạng, không cần giả định điểm phân phối chuẩn |
| Hiệu chỉnh Holm–Bonferroni | cả {len(f['gt'])} kiểm định cùng lúc | Làm nhiều kiểm định thì dễ ra "có ý nghĩa" giả; Holm điều chỉnh p để cả nhóm kiểm định giữ sai số 5% |
| Độ lớn hiệu ứng: Cohen's d / eta² | mọi kiểm định | p chỉ cho biết "thật hay không"; effect size cho biết "lớn cỡ nào". d: 0.2 nhỏ, 0.5 vừa, 0.8 lớn. eta² = tỉ lệ phương sai G3 được giải thích: 0.01 nhỏ, 0.06 vừa, 0.14 lớn |
| Khoảng tin cậy 95% của chênh lệch | t-test | Khoảng giá trị hợp lý của chênh lệch thật; nếu chứa 0 thì chênh lệch không có ý nghĩa |

**Kết quả (exclude_dropout, n = {E['n']}):**

{table(['Biến', 'Kiểm định', 'Nhóm (G3 trung bình)', 'Thống kê', 'Chênh lệch [CI 95%] / kiểm tra lại', 'p', 'p (Holm)', 'Effect size', 'Có ý nghĩa?'], _test_rows(E, vi=True))}

**Tương quan Pearson với G3 (p-value và CI 95% của r):**

{table(['Biến', 'r', 'CI 95%', 'p'], _corr_rows(E))}

**Diễn giải:**
- Có ý nghĩa sau hiệu chỉnh Holm: {', '.join(f'`{c}`' for c in f['sig']) or 'không có'}. Không có ý nghĩa: {', '.join(f'`{c}`' for c in f['nonsig']) or 'không có'}.
- Internet: chênh +{f['gt']['internet']['diff']} điểm có p gốc = {_fmt_p(f['gt']['internet']['p'])} nhưng p Holm = {_fmt_p(f['gt']['internet']['p_holm'])}, nên {'vẫn giữ được' if f['gt']['internet']['significant'] else '**không còn ý nghĩa**'} sau hiệu chỉnh nhiều kiểm định. Chỉ nên trình bày như một chênh lệch yếu, chưa chắc chắn.
- Hỗ trợ gia đình: CI [{f['gt']['famsup']['ci95'][0]}, {f['gt']['famsup']['ci95'][1]}] chứa 0 → không có bằng chứng `famsup` làm thay đổi G3.
- Thời gian tự học có ý nghĩa nhưng rất nhỏ (eta² = {f['gt']['studytime']['effect']}: chỉ giải thích khoảng {f['gt']['studytime']['effect'] * 100:.1f}% phương sai của G3). Số lần trượt (eta² = {f['gt']['failures']['effect']}) và vắng học (eta² = {f['gt']['absence_level']['effect']}) quan trọng hơn.
- {'ANOVA và Kruskal–Wallis cho cùng kết luận ở mọi biến, nên kết luận không phụ thuộc giả định điểm phân phối chuẩn.' if f['kw_agree'] else 'ANOVA và Kruskal–Wallis không thống nhất ở ít nhất một biến; cần thận trọng với kết quả đó.'}

**Vì sao tin được:** kiểm định dùng `scipy.stats` (cài đặt chuẩn), dùng biến thể không cần phương sai bằng nhau và
phi tham số ở chỗ giả định đáng ngờ, và đã hiệu chỉnh cho nhiều kiểm định.

{codes['_group_tests']}

{codes['_holm']}

{codes['_corr_tests']}

### 7.2 Hồi quy đa biến: yếu tố nào vẫn quan trọng khi giữ các yếu tố khác cố định?

**Đã làm gì.** So sánh từng biến riêng lẻ (7.1) không phân biệt được một yếu tố tự nó có tác dụng hay chỉ đi kèm yếu tố
khác (vd internet ↔ bố mẹ học vấn cao). **Hồi quy tuyến tính OLS** ước lượng tất cả yếu tố cùng lúc: mỗi hệ số **b** là mức
thay đổi kỳ vọng của G3 (điểm) khi biến đó tăng 1 đơn vị **trong khi mọi biến khác giữ nguyên**. Sai số chuẩn dùng HC3 (không
cần giả định phương sai bằng nhau). Chỉ dùng học sinh có G3 > 0. Hai mô hình:

- **Mô hình A — yếu tố nền** ({len(dp.REG_FACTORS)} biến: các biến của câu hỏi chính + học vấn bố/mẹ, giới tính, tuổi, nơi ở).
- **Mô hình B — A + G1, G2**: còn yếu tố nào quan trọng khi đã biết điểm giữa kỳ.

{table(['Mô hình', 'mat: n / R² / R² hiệu chỉnh', 'por: n / R² / R² hiệu chỉnh'], [[name, *[f"{f['reg'][s][key]['n']} / {f['reg'][s][key]['r2']} / {f['reg'][s][key]['adj_r2']}" for s in ('mat', 'por')]] for key, name in (('factors', 'A: yếu tố nền'), ('factors_plus_grades', 'B: A + G1, G2'))])}

R² = tỉ lệ biến động của G3 mà mô hình giải thích được (0 = không gì, 1 = toàn bộ).

**Hệ số mô hình A** (mat; cột cuối chạy lại cùng mô hình trên por để kiểm tra lặp lại):

{table(['Biến', 'b (điểm G3)', 'CI 95%', 'p', 'Có ý nghĩa (mat)', 'por: b, có ý nghĩa'], _reg_rows(f, 'factors', dp.REG_FACTORS, vi=True))}

**Mô hình B, chỉ phần điểm** (toàn bộ hệ số có trong `summary.json → regression`):

{table(['Biến', 'b (điểm G3)', 'CI 95%', 'p', 'Có ý nghĩa (mat)', 'por: b, có ý nghĩa'], _reg_rows(f, 'factors_plus_grades', dp.REG_GRADES, vi=True))}

**Diễn giải:**
- Có ý nghĩa ở **cả 2 môn** khi giữ mọi yếu tố khác cố định: {', '.join(_lbl(c, True) for c in f['reg_sig_both'])}.
- Internet: chênh lệch thô là {f['gt']['internet']['diff']:+.2f}; khi giữ các yếu tố khác cố định b = {f['reg']['mat']['factors']['coef']['internet_bin']['b']:+.2f} (p {_fmt_p(f['reg']['mat']['factors']['coef']['internet_bin']['p'])}) → {'vẫn có ý nghĩa' if f['reg']['mat']['factors']['coef']['internet_bin']['significant'] else '**không có tác động riêng**'}.
- Hỗ trợ gia đình (`famsup`): b = {f['reg']['mat']['factors']['coef']['famsup_bin']['b']:+.2f} (p {_fmt_p(f['reg']['mat']['factors']['coef']['famsup_bin']['p'])}) → {'có ý nghĩa' if f['reg']['mat']['factors']['coef']['famsup_bin']['significant'] else 'không đo được tác động'}.
- Các yếu tố nền chỉ giải thích R² = {f['reg']['mat']['factors']['r2']} (mat): phần lớn khác biệt giữa học sinh *không* được giải thích bởi các biến này.
- Khi đã biết G1, G2 (mô hình B, R² = {f['reg']['mat']['factors_plus_grades']['r2']}), chỉ còn {', '.join(_lbl(c, True) for c in f['reg_grades_sig']) or 'không biến nền nào'} giữ tác động riêng có ý nghĩa ở mat: điểm giữa kỳ đã chứa gần như toàn bộ thông tin.
- G1 và G2 tương quan rất mạnh với nhau (r = {E['corr_G1_G2_G3']['G1_G2']}), nên mô hình B không tách được tác động riêng của từng điểm: chỉ đọc R² và tác động chung của 2 điểm giữa kỳ, không so sánh b(G1) với b(G2).
- Hồi quy chỉ điều chỉnh cho các biến có trong dữ liệu; kết quả là quan hệ tương quan, không phải nhân quả.

{codes['_ols']}

{codes['_regression']}

## 8. Biểu đồ

Ba ảnh đầu do pipeline sinh ra (`analyze()` → `_plot_charts()`), không vẽ tay. Xoá thư mục `images/` rồi chạy
`python main.py` là ảnh được tạo lại. Ảnh thứ tư (bối cảnh PISA) nằm ở mục 10.2.

### 8.1 Biểu đồ 1 — Biểu đồ cột nhóm: G3 trung bình theo thời gian tự học và internet

![Biểu đồ 1]({IMG['bar']})

**Định nghĩa.** Biểu đồ cột nhóm (grouped bar chart) so sánh *giá trị trung bình* của một biến số (G3) giữa các tổ
hợp của hai biến phân loại (mức thời gian tự học × có internet ở nhà hay không). Dữ liệu: {E['n']} học sinh (đã bỏ nhóm nghi bỏ thi).

| Thành phần | Ý nghĩa |
|---|---|
| Trục X | Mức thời gian tự học mỗi tuần: 1 = <2h, 2 = 2–5h, 3 = 5–10h, 4 = >10h |
| Trục Y | Điểm cuối kỳ G3 trung bình, thang 0–20 (cố định 0–20 để so chiều cao cột cho công bằng) |
| Cột xanh dương | Học sinh **không có** internet ở nhà |
| Cột cam | Học sinh **có** internet ở nhà |
| Thanh đen (error bar) | Khoảng tin cậy 95% của trung bình: mean ± 1.96·std/√n. Thanh càng dài thì trung bình càng kém chắc chắn |
| Nhãn `n=` | Số học sinh trong cột đó |
| Cột gạch chéo, nhạt màu | Dưới {dp.MIN_RELIABLE_N} học sinh: trung bình không đáng tin, không rút kết luận từ cột này |
| Chú giải (legend) | Màu → nhóm internet |

**Cách đọc:** so chiều cao cột *cùng với* thanh sai số; nếu 2 thanh chồng lên nhau nhiều thì chênh lệch không đáng tin.
Các cột gạch chéo (n < {dp.MIN_RELIABLE_N}): {', '.join(f"studytime {k.split('|')[0]} & internet={yn[k.split('|')[1]]} (n={n})" for k, n in f['small_groups']) or 'không có'}.

**Kết luận:** có internet {E['by_internet']['yes']['mean']} vs không có {E['by_internet']['no']['mean']}, nhưng chênh lệch này
{'có ý nghĩa thống kê' if f['gt']['internet']['significant'] else '**không có ý nghĩa** sau hiệu chỉnh Holm (mục 7.1)'}; các thanh sai số chồng lên nhau trên biểu đồ cũng cho thấy điều đó.
Thời gian tự học chỉ có xu hướng tăng nhẹ (r = {E['corr_full']['G3']['studytime']}).

{codes['_plot_bar']}

### 8.2 Biểu đồ 2 — Histogram điểm cuối kỳ (G3)

![Biểu đồ 2]({IMG['hist']})

**Định nghĩa.** Histogram chia một biến số thành các khoảng (bin) và cho biết có bao nhiêu quan sát rơi vào mỗi khoảng.
Ở đây mỗi bin đúng bằng 1 điểm (tâm bin tại 0, 1, …, 20). Dữ liệu: toàn bộ {A['n']} học sinh.

| Thành phần | Ý nghĩa |
|---|---|
| Trục X | Điểm cuối kỳ G3 (0–20) |
| Trục Y | Số học sinh đạt điểm đó |
| Cột xanh dương | Học sinh có G3 > 0 |
| Cột đỏ tại 0 | Nhóm nghi bỏ thi (G3 = 0, n = {dpf['n']}) |
| Đường đứt nét dọc | Mốc đỗ: bên trái = trượt (G3 < {dp.PASS_MARK}), bên phải = đỗ (G3 ≥ {dp.PASS_MARK}) |
| Ô chữ | Tỉ lệ đỗ trên toàn bộ học sinh và sau khi bỏ nhóm nghi bỏ thi |
| Chú giải (legend) | Ý nghĩa màu / đường |

**Kết luận:** điểm thật phân bố gần hình chuông quanh {f['mode_g3']} (điểm xuất hiện nhiều nhất), còn cột 0 tách hẳn ra với
khoảng trống ở 1–3 điểm ({f['gap_1_3']} học sinh) — bằng chứng trực quan rằng điểm 0 là hiện tượng khác, không phải đuôi thấp
của phân phối điểm.

{codes['_plot_hist']}

### 8.3 Biểu đồ 3 — Heatmap tương quan

![Biểu đồ 3]({IMG['heat']})

**Định nghĩa.** Heatmap biểu diễn một ma trận số bằng màu sắc. Mỗi ô là **hệ số tương quan Pearson** r giữa hai biến:
r = cov(X, Y) / (σX·σY), nằm trong khoảng −1 (tương quan tuyến tính âm hoàn toàn), 0 (không có quan hệ tuyến tính)
đến +1 (dương hoàn toàn). Dữ liệu: {E['n']} học sinh (đã bỏ nhóm nghi bỏ thi).

| Thành phần | Ý nghĩa |
|---|---|
| Hàng / cột | Các biến: G1, G2, G3 (điểm), studytime (1–4), failures (0–3), absences (số buổi vắng), famsup (1 = có, 0 = không) |
| Màu ô | Đỏ = r dương, xanh = r âm, trắng ≈ 0; màu càng đậm thì quan hệ càng mạnh |
| Số trong ô | Giá trị r (2 chữ số thập phân) |
| Đường chéo (1.00) | Mỗi biến với chính nó — luôn bằng 1 |
| Nửa trên để trống | Ẩn đi vì ma trận đối xứng (r(X,Y) = r(Y,X)) |
| Thanh màu | Quy đổi màu sang giá trị r từ −1 đến +1 |

Ghi chú: `famsup` là biến 0/1 nên r của nó là tương quan point-biserial (cùng công thức).

**Kết luận — tương quan với G3, từ mạnh đến yếu:** {', '.join(f"{k.replace('_bin', '')} {v:+.3f}" for k, v in top)}.

{codes['_plot_heatmap']}

## 9. Rule cảnh báo sớm nguy cơ trượt

**Đã làm gì:** `classify_risk()` **chỉ dùng thông tin có trước kỳ thi cuối** (G1, G2, số lần trượt, số buổi vắng —
không bao giờ dùng G3), nên có thể đánh giá trung thực với kết quả đỗ/trượt thật.

- high (cao): G2 < {dp.G_WARN} hoặc số lần trượt ≥ {dp.FAIL_HIGH}
- medium (trung bình): G1 < {dp.G_WARN} hoặc số lần trượt ≥ 1 hoặc vắng ≥ {dp.ABS_HIGH}
- low (thấp): còn lại

{codes['classify_risk']}

**Đánh giá trên toàn bộ {A['n']} học sinh** (cảnh báo = nhóm "high", thực tế = G3 < {dp.PASS_MARK}):

{table(['', 'trượt thật', 'đỗ thật'], [['bị cảnh báo high', h['tp'], h['fp']], ['không bị cảnh báo', h['fn'], h['tn']]])}

- **Recall** = TP / (TP + FN) = {h['tp']} / {h['tp'] + h['fn']} = **{pct(h['recall'])}** số em trượt thật được cảnh báo sớm (CI 95% {pct(h['recall_ci95'][0])}–{pct(h['recall_ci95'][1])}).
- **Precision** = TP / (TP + FP) = {h['tp']} / {h['tp'] + h['fp']} = **{pct(h['precision'])}** số em bị cảnh báo thực sự trượt (CI 95% {pct(h['precision_ci95'][0])}–{pct(h['precision_ci95'][1])}).
- Tỉ lệ trượt theo nhóm: {', '.join(f"{k} {pct(v)}" for k, v in risk['fail_rate_by_group'].items())}.

{codes['_risk_eval']}

**Kiểm tra ngoài mẫu (holdout).** Các ngưỡng ở trên được chọn khi đã nhìn dữ liệu môn Toán, nên các con số trên là
*in-sample* và có thể lạc quan. Để kiểm tra, **giữ nguyên rule** (không đổi ngưỡng nào) rồi áp lên môn Bồ Đào Nha, dữ liệu
mà rule chưa từng thấy. Vì nhiều học sinh học cả 2 môn, bản holdout chặt chỉ giữ những học sinh môn Bồ Đào Nha có 13 cột
nhận dạng (`MERGE_KEYS`, giống `student-merge.R`) không xuất hiện trong file môn Toán. Khoảng tin cậy là khoảng Wilson 95%.

{table(['Tập dữ liệu', 'n', 'Tỉ lệ trượt', 'TP / FP / FN', 'Recall [CI 95%]', 'Precision [CI 95%]'], _holdout_rows(r, vi=True))}

**Diễn giải:**
- **Recall** trên học sinh chưa thấy: {pct(f['ho']['recall'])} so với {pct(h['recall'])} in-sample — rule vẫn bắt được {f['ho']['tp']}/{f['ho']['tp'] + f['ho']['fn']} em sẽ trượt.
- **Precision giảm** ({pct(f['ho']['precision'])} so với {pct(h['precision'])}): báo động nhầm nhiều hơn. Một phần vì môn Bồ Đào Nha ít em trượt hơn (tỉ lệ trượt {pct(f['ho_ev']['fail_rate'])} so với {pct(risk['fail_rate'])}); precision luôn giảm khi kết quả cần bắt hiếm hơn.
- Kết luận: rule là công cụ *sàng lọc* tốt (ít bỏ sót em trượt), không phải dự đoán chính xác; con số trung thực nên trích dẫn là con số holdout.

{codes['_wilson']}

{codes['_risk_holdout']}

**Chia 3 nhóm (low / medium / high) có hợp lý không?** Bảng cho biết bao nhiêu em trong mỗi nhóm thực sự trượt (CI Wilson 95%),
và nhóm "medium" có thực sự rủi ro hơn "low" không (nguy cơ tương đối, kiểm định chính xác Fisher — phù hợp khi số đếm nhỏ).

{table(['Tập dữ liệu', 'low: trượt / n', 'medium: trượt / n', 'high: trượt / n', 'medium so với low'], _tier_rows(f['r'], vi=True))}

{"Nhóm medium trượt nhiều gấp nhiều lần nhóm low, cả trên dữ liệu dùng để đặt rule lẫn trên học sinh chưa từng thấy (kiểm định Fisher có ý nghĩa ở cả 2), trong khi vẫn thấp xa nhóm high. Vì vậy 3 nhóm đều mang thông tin và ứng với 3 hành động: **high → can thiệp ngay**, **medium → theo dõi**, **low → không cần can thiệp**. Precision/recall chính dùng nhóm high làm cảnh báo." if f['tier_ok'] else "Nhóm medium không chắc chắn rủi ro hơn low trên học sinh chưa thấy, nên chỉ nên dùng rule 2 nhóm (high / không high)."}

{codes['_tier_eval']}

**Vì sao tin được:** không rò rỉ dữ liệu (G3 không phải đầu vào — thấy rõ trong `classify_risk()`), độ bất định được thể
hiện bằng khoảng tin cậy, và hiệu năng được kiểm chứng trên học sinh mà rule chưa từng được chỉnh theo.

## 10. Bối cảnh

### 10.1 Môn Toán vs môn Bồ Đào Nha (kiểm tra lặp lại)

{table(['Chỉ số', 'mat', 'por'], [[k, f["sc"]['mat'][k], f["sc"]['por'][k]] for k in f["sc"]['mat']])}

Chiều của các tương quan chính (G2, vắng học, số lần trượt với G3) {'**giống nhau**' if f['same_sign'] else '**không** giống nhau'} ở cả 2 môn.

{_paired_text(f, vi=True)}

{codes['_subject_comparison']}

{codes['_paired_subjects']}

### 10.2 PISA: Bồ Đào Nha so với trung bình OECD

Học sinh trong dữ liệu UCI đến từ 2 trường ở Bồ Đào Nha (năm học 2005–2006, Cortez & Silva 2008). PISA chỉ cung cấp
bối cảnh **cấp quốc gia**; không bao giờ ghép với từng dòng học sinh.

{table(['Môn', 'Năm', 'Bồ Đào Nha', 'TB OECD', 'Chênh lệch', 'Hạng Bồ Đào Nha'], _pisa_rows(f))}

Môn Toán: Bồ Đào Nha {pm[min(pm, key=int)]['portugal'] if pm else '—'} điểm năm {min(pm, key=int) if pm else '—'} → {pm[pl['mathematics']]['portugal'] if pm else '—'} điểm năm {pl.get('mathematics', '—')} (OECD {pm[pl['mathematics']].get('oecd_average', '—') if pm else '—'}).

{codes['_pisa_context']}

#### Biểu đồ 4 — Xu hướng PISA: Bồ Đào Nha so với trung bình OECD

![Biểu đồ 4]({IMG['pisa']})

**Định nghĩa.** Biểu đồ đường (line chart) cho thấy một giá trị thay đổi theo thời gian. Mỗi ô là một môn PISA; mỗi điểm là
điểm PISA trung bình của cả nước trong một kỳ thi (thang PISA được chuẩn hoá sao cho trung bình OECD khoảng 500 ở lần đầu môn đó
là môn chính). Dữ liệu: `pisa_clean.csv` ({f['n_pisa_clean']} dòng), đã đối chiếu với OECD ở mục 3.4.

| Thành phần | Ý nghĩa |
|---|---|
| Các ô | Toán, Đọc hiểu, Khoa học (bảng so sánh có Khoa học từ 2006) |
| Trục X | Năm của kỳ thi PISA (2000, 2003, …, 2022, {dp.OECD_PISA_YEAR}) |
| Trục Y | Điểm PISA trung bình (dùng chung cho 3 ô để so mức điểm) |
| Đường xanh liền, chấm tròn | Bồ Đào Nha |
| Đường xám đứt nét, ô vuông | Trung bình OECD |
| Số ở cuối mỗi đường | Điểm mới nhất ({dp.OECD_PISA_YEAR}) |
| Dải màu cam | Năm học 2005–06, lúc khảo sát học sinh trong dữ liệu UCI |

**Cách đọc:** khoảng cách dọc giữa 2 đường là mức chênh của Bồ Đào Nha so với trung bình OECD trong năm đó.

**Kết luận:** môn Toán, Bồ Đào Nha đi từ {pm[min(pm, key=int)]['portugal'] if pm else '—'} điểm ({min(pm, key=int) if pm else '—'}, OECD {pm[min(pm, key=int)].get('oecd_average', '—') if pm else '—'}) đến
{pm[pl['mathematics']]['portugal'] if pm else '—'} điểm ({pl.get('mathematics', '—')}, OECD {pm[pl['mathematics']].get('oecd_average', '—') if pm else '—'}). {f"Lần đầu bắt kịp trung bình OECD vào năm {f['catch_up']} và từ đó đi cùng nhịp với OECD." if f['catch_up'] else 'Chưa kỳ nào bắt kịp trung bình OECD.'}
{'Vào thời điểm dữ liệu UCI (dải cam, kỳ gần nhất là 2006), Bồ Đào Nha thấp hơn trung bình OECD ở cả 3 môn.' if f['below_2006'] else 'Năm 2006 (kỳ gần dữ liệu UCI nhất) Bồ Đào Nha không thấp hơn OECD ở mọi môn.'}

{codes['_plot_pisa']}

## 11. Pipeline (OOP) và đầu ra

`main.py` chạy: `fetch_uci_raw` → `scrape_pisa_table` (cache-first) → `load_data` → `clean_data` → `analyze`
(+ vẽ biểu đồ) → `export_results` → sinh báo cáo này.

{codes['main']}

{codes['analyze']}

{codes['export_results']}

| Đầu ra | Nội dung |
|---|---|
| `data/processed/cleaned_students.csv` | {f['log']['rows_out']} dòng (cả 2 môn, cột `subject`), cột đã encode, cột tạo thêm, 6 cờ bất thường |
| `data/processed/cleaned_students_mat.csv`, `cleaned_students_por.csv` | cùng các cột, mỗi môn 1 file ({f['n_raw'].get('mat')} / {f['n_raw'].get('por')} dòng), không cần lọc `subject` |
| `data/processed/pisa_clean.csv` | {f['n_pisa_clean']} dòng PISA đã làm sạch |
| `data/processed/summary.json` | toàn bộ thống kê trong báo cáo này |
| `images/*.png` | 3 biểu đồ theo đề + 1 biểu đồ bối cảnh PISA |
| `report.md`, `report_vi.md` | báo cáo này (tiếng Anh / tiếng Việt) |

## 12. Vì sao kết quả đáng tin (tổng hợp kiểm chứng)

| Kiểm tra | Kết quả |
|---|---|
| Dữ liệu thô giống bản tải từ UCI | Tải từ URL chính thức; {f['n_raw'].get('mat')} / {f['n_raw'].get('por')} dòng, {f['n_cols']} cột đúng như tài liệu |
| Các bước làm sạch (kiểu, miền giá trị, yes/no, trùng, thiếu) | Đều được đếm trong `cleaning_log`; tổng số lỗi = {f['invalid_total']} |
| Xử lý rõ ràng G3 = 0 | Gắn cờ; {dpf['n_absences_zero']}/{dpf['n']} em có 0 buổi vắng; kết quả trình bày cả có và không có nhóm này |
| Độ nhạy | So sánh kết luận chính giữa `all` và `exclude_dropout` (mục 6) |
| Lặp lại trên dữ liệu khác | Cùng chiều tương quan ở môn Bồ Đào Nha: {'có' if f['same_sign'] else 'không'} |
| Rule rủi ro không rò rỉ | G3 không phải đầu vào của `classify_risk()` |
| Kiểm định thống kê | Welch t / ANOVA + Kruskal–Wallis, hiệu chỉnh Holm; có ý nghĩa: {', '.join(f['sig'])}; không có ý nghĩa: {', '.join(f['nonsig'])} |
| Hồi quy đa biến | OLS với sai số HC3; mô hình A R² = {f['reg']['mat']['factors']['r2']}; có ý nghĩa ở cả 2 môn: {', '.join(f['reg_sig_both'])} |
| Độ nhạy với các số 0 | Ảnh hưởng của vắng học âm và có ý nghĩa ở mọi kịch bản đã bỏ số 0, cả 2 môn: {'có' if f['abs_robust'] else 'không'} |
| Các nhóm rủi ro | Nguy cơ trượt medium so với low ×{f['r']['risk_eval']['all']['tiers']['medium_vs_low']['relative_risk']} (mat), ×{f['r']['risk_eval']['holdout_por_only']['tiers']['medium_vs_low']['relative_risk']} (por chưa thấy); có ý nghĩa ở cả 2: {'có' if f['tier_ok'] else 'không'} |
| Rule rủi ro ngoài mẫu | Rule cố định trên học sinh chỉ học môn Bồ Đào Nha: recall {pct(f['ho']['recall'])}, precision {pct(f['ho']['precision'])} |
| Cào PISA | Kiểm tra cấu trúc + cố định revision Wikipedia {ps.get('revision_id')} |
| PISA so với OECD chính thức | {dp.OECD_PISA_YEAR}: {f['oc'][str(dp.OECD_PISA_YEAR)]['n_within_tolerance']}/{f['oc'][str(dp.OECD_PISA_YEAR)]['n_compared']} điểm trùng khớp; 2022 (suy ra): {f['oc'][str(dp.OECD_PISA_YEAR - 3)]['n_within_tolerance']}/{f['oc'][str(dp.OECD_PISA_YEAR - 3)]['n_compared']} lệch không quá ±1 |
| Biểu đồ | Sinh bởi code ở mục 8; tái tạo bằng `python main.py` |
| Số liệu trong báo cáo | Sinh từ kết quả pipeline bởi `report_builder.py`; không thể bị cũ |

## 13. Giới hạn và hướng tiếp theo

- Chỉ 1 môn / 1 năm học làm nhóm chính; các nhóm nhỏ (xem nhãn `n=` ở Biểu đồ 1) có khoảng tin cậy rộng.
- Hồi quy chỉ điều chỉnh cho các biến có trong dữ liệu; các yếu tố không đo được (động lực, giáo viên, thu nhập) vẫn có thể gây nhiễu, nên đây là quan hệ tương quan, không phải nhân quả.
- "Nghi bỏ thi" là suy luận từ dữ liệu, chưa được trường xác nhận; phân tích độ nhạy (6.1) cho thấy kết luận về vắng học không phụ thuộc vào giả định này.
- Tập holdout cùng trường, cùng năm học với dữ liệu gốc, và holdout chặt khá nhỏ (n = {f['ho_ev']['n']}); precision ở trường khác có thể khác.
- Điểm PISA {dp.OECD_PISA_YEAR} và 2022 đã đối chiếu với báo cáo OECD; các kỳ cũ hơn (2000–2018) chỉ dựa vào Wikipedia.
- Mọi kết luận là tương quan, không phải nhân quả.

*Tái tạo: `pip install -r requirements.txt` rồi `python main.py` (thêm `--refresh-pisa` để cào lại Wikipedia).*
"""


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------
def _codes() -> dict:
    P = dp.StudentDataProcessor
    funcs = [dp.fetch_uci_raw, dp.scrape_pisa_table, dp._parse_pisa_html, dp.validate_pisa_raw,
             dp.clean_pisa, dp.convert_yes_no, dp.calc_pass_fail, dp.classify_absences,
             dp.calc_average_grade, dp.classify_risk, dp._risk_eval, dp._grp, dp._scope_stats,
             P.load_data, P.clean_data, P.analyze, P.export_results, P._subject_comparison,
             P._pisa_context, P._plot_bar, P._plot_hist, P._plot_heatmap,
             dp._group_tests, dp._holm, dp._corr_tests, dp._wilson, P._risk_holdout,
             dp.cross_check_pisa, P._plot_pisa, dp._ols, P._regression, P._sensitivity, dp._tier_eval,
             dp._paired_subjects]
    codes = {fn.__name__: code(fn) for fn in funcs}
    dp_path = Path(dp.__file__)
    codes["config"] = code_region(dp_path, "# Threshold config", "# 4 basic functions")
    main_path = ROOT / "main.py"
    body = main_path.read_text(encoding="utf-8").rstrip()
    codes["main"] = f"`main.py` (whole file)\n\n```python\n{body}\n```"
    return codes


def _summary(text: str, full_pdf: str, vi: bool) -> str:
    """Short version for a 1–2 page hand-in: title, main question, section 1 and the limitations,
    cut from the full generated report so the numbers are identical."""
    head = text.split("\n## 2.", 1)[0]
    limits = text.split("\n## 13.", 1)[1]
    title, rest = head.split("\n", 1)
    rest = re.sub(r"\n>.*(?:\n>.*)*", "", rest, count=1)  # generation note of the full report
    note = (f"*Bản tóm tắt. Báo cáo đầy đủ (dữ liệu, code, biểu đồ, kiểm định): `{full_pdf}`.*" if vi
            else f"*Summary version. Full report (data, code, charts, tests): `{full_pdf}`.*")
    return f"{title}\n\n{note}\n\n{rest.strip()}\n\n## 2.{limits}"


def build_reports(proc: dp.StudentDataProcessor, out_dir: Path = ROOT) -> list[Path]:
    """Write report.md / report_vi.md (full) and report_summary.md / report_summary_vi.md (1–2 pages)."""
    assert proc.results, "run analyze() first"
    missing = [what for what, key in (("PISA reference data (data/raw/pisa_reference.csv)", "pisa_context"),
                                      ("OECD cross-check (data/raw/oecd_pisa2025_table_I1.csv)", "pisa_oecd_check"))
               if not proc.results.get(key)]
    if missing:
        raise ValueError("cannot build reports, missing: " + "; ".join(missing))
    facts, codes = _facts(proc), _codes()
    out = []
    for name, summary_name, full_pdf, render, vi in (
            ("report.md", "report_summary.md", "report.pdf", render_en, False),
            ("report_vi.md", "report_summary_vi.md", "report_vi.pdf", render_vi, True)):
        text = re.sub(r"\n{3,}", "\n\n", render(facts, codes))
        for file_name, content in ((name, text), (summary_name, _summary(text, full_pdf, vi))):
            path = Path(out_dir) / file_name
            path.write_text(content, encoding="utf-8")
            out.append(path)
    return out
