# P1 Report — Factors Affecting Final Grades (student-mat, n=395)

**Main question:** How do studytime, absences and midterm grades (G1/G2) relate to final grade (G3)? Family support is in the data, but this report has no result for it.

## 1. Data & method
- **Primary:** UCI Student Performance, `student-mat.csv` (395 rows × 33 cols, `;`-separated, two schools GP/MS). Saved raw, never edited in place.
- **Reference:** Wikipedia PISA ranking scraped live via `requests + BeautifulSoup` (`scrape_pisa_table()`), cached to `data/raw/pisa_reference.csv` (92 rows × 3 cols: Rank, Country/economy, Score). External context only — different population/year, not joined to student rows.
- **Pipeline:** `StudentDataProcessor.load_data() → clean_data() → analyze() → export_results()`, run by `main.py`. Cleaning: numeric casts (G1/G2/G3, absences, failures, studytime, age), `yes/no → 1/0` (`convert_yes_no`), derived `pass_fail` (G3 ≥ 10), `absence_level` (low 0–3 / medium 4–9 / high ≥10), `avg_grade`, `risk_group` (low/medium/high). EDA: `groupby` + `mean/std` only; charts: bar, histogram, heatmap (matplotlib, no sklearn — descriptive scope).

## 2. Results
- **Base rate:** 265 pass / 130 fail → pass rate **0.671**.
- **Midterms dominate:** corr G2–G3 **0.905**, G1–G3 **0.801**, G1–G2 0.852. Knowing G2 nearly determines G3.
- **Past failures hurt most:** failures=0 mean **11.25** (n=312) vs 1 → 8.12, 2 → 6.24, 3 → 5.69 (r ≈ −0.36). The drop is largest for the first failure (≈ −3.1 points); the next drops are smaller (−1.9, then −0.6).
- **Study time, modest:** bucket 1 (<2h) 10.05 → bucket 3 (5–10h) **11.40** (+1.35); bucket 4 (>10h) 11.26 stalls (n=27, std 5.28 — small-n noise). Correlation studytime–G3 ≈ +0.10.
- **Internet gap:** yes **10.62** (n=329) vs no 9.41 (n=66), +1.2 points — confounded with socioeconomic status, not causal proof.
- **Absences paradox:** medium (4–9) **11.38** > high (≥10) 10.37 > low (0–3) 9.82; corr absences–G3 ≈ **+0.03** ≈ zero. Absence count alone explains nothing here; low-absence variance is high (std 5.61), suggesting interaction with ability/reason for absence.
- **Risk groups (true by construction, not a prediction):** low 13.63 (n=167) / medium 11.65 (n=91) / high 5.68 (n=137). The high group is defined partly by G3 < 10, and 130 of its 137 students have G3 < 10, so the spread follows from the definition. Rule: high = G3 < 10 or failures ≥ 2; medium = G1 or G2 < 10, or failures ≥ 1, or absences ≥ 10; otherwise low. The cut-offs are chosen, not fitted.

## 3. Insights, limits, next steps
G2 + failure history are the actionable levers; studytime/internet are secondary correlates; raw absence counts should not trigger interventions alone. **Limits:** single subject/year (Portuguese math cohort), n=395 (bucket 4 fragile), PISA not comparable at row level, no causal identification, no holdout model. 38 students have G3 = 0 (no value is 1); the data does not say why, so check that before reading anything into them. The risk groups are not an independent test (see Results). **Next:** add `student-por.csv` with a `subject` column, test G1→G2 trajectories, and validate the risk rule out-of-sample before school use.

*Reproduce: `pip install -r requirements.txt && python main.py` → `data/processed/cleaned_students.csv + summary.json`, charts in `images/`; open `analysis.ipynb` for full EDA.*
