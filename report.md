# P1 Report — Factors Affecting Final Grades (UCI Student Performance)

**Main question:** How do study time, absences, family support and intermediate grades (G1, G2) relate to the final grade (G3)?

**Data:** UCI Student Performance, 2 Portuguese secondary schools (GP, MS), 2005–06. `student-mat.csv` (395 students, mathematics) is analysed; `student-por.csv` (649 students) is used to test the risk rule on new students. Context: PISA scores scraped from Wikipedia (2342 raw rows → 1662 clean rows), cross-checked with the official OECD PISA 2025 Table I.1 (2025: 274/274 scores identical; 2022: 208/211 within ±1).

## 1. Data collection and cleaning

- **Collection:** `fetch_uci_raw` downloads `student.zip` from UCI if the raw files are missing. `scrape_pisa_table` reads the PISA tables with `requests` + BeautifulSoup, validates them (3 subjects, years ≥ 2000, scores 200–700, ≥ 30 countries, exactly 1 OECD average row) and caches them in `data/raw/pisa_reference.csv` (Wikipedia revision 1378067005).
- **Cleaning (`clean_data`, 6 steps):** trim whitespace → cast numbers and check the valid range of each column (from `student.txt`) → encode yes/no as 1/0 → drop duplicates and rows missing required values → add derived columns (`pass_fail`, `absence_level`, `avg_grade`, `avg_g1g2`, `risk_group`) → add 6 anomaly flags (rows kept, never deleted).
- **Result:** the raw UCI data is technically clean: 0 out-of-range values, 0 invalid yes/no, 0 duplicates, 0 rows missing a required value; all 1044 rows kept. `avg_grade` contains G3, so it is descriptive only and never used to predict G3.
- **Key data-quality finding:** 38 mathematics students have **G3 = 0**, and **all 38 have 0 recorded absences** (only 21.6% of the other students do), with a mean G1 of 7.5. They most likely did not sit the final exam, so they are flagged as `dropout_suspect`. Keeping them unflagged changes r(absences, G3) from **−0.213** to **+0.034** and hides the real effect. Conclusions below use the 357 students with G3 > 0.

## 2. Findings (mathematics, 357 students)

| Factor | Mean G3 by group | Test (Holm-corrected, α = 0.05) |
|---|---|---|
| Intermediate grades | — | r(G2, G3) = **0.966**, r(G1, G3) = 0.892 |
| Past failures (0 / 1 / 2 / 3) | 11.94 / 10.15 / 8.83 / 8.27 | ANOVA p_holm < 0.001, η² = 0.089; r = −0.294 |
| Absences (low / medium / high) | 12.26 / 11.38 / 10.37 | ANOVA p_holm < 0.001, η² = 0.053; r = −0.213 |
| Study time (<2h / 2–5h / 5–10h / >10h) | 11.47 / 11.07 / 12.56 / 12.67 | ANOVA p_holm = 0.019, but η² = 0.036 (small) |
| Internet at home (yes / no) | 11.68 / 10.71 | Welch t-test p = 0.027 → p_holm = **0.080, not significant** |
| Family support (yes / no) | 11.35 / 11.80 | p_holm = 0.404, no difference |
| School support (yes / no) | 9.62 / 11.83 | p_holm < 0.001; weaker students receive support (reverse direction) |

- **Pass rate:** 67.1% of all 395 students; 74.2% after removing the 38 dropout suspects.
- **Early-warning rule** (`risk_group`, uses only G1, G2, failures, absences, never G3): `high` = G2 < 10 or ≥ 2 failures. On mathematics it catches 93.8% of failing students (precision 81.9%). On 275 Portuguese students who do not appear in the mathematics file it still catches **91.4%** (precision 66.0%). Fail rate by tier (mathematics): low 1.2%, medium 7.8%, high 81.9%.
- **PISA context:** in 2006 Portugal scored below the OECD average in mathematics (466 vs 494); it caught up in 2015 (492 vs 490) and was level in 2025 (460 vs 463).

**Charts:** `images/01_bar_studytime_internet.png` (mean G3 by study time × internet, 95% CI), `02_hist_g3.png` (G3 distribution, the G3 = 0 group in red), `03_heatmap_corr.png` (Pearson correlations).

## 3. Limitations

- 2 schools, one school year, cross-sectional data: all findings are associations, not causes.
- Study time and absences are reported buckets/counts; unmeasured factors (motivation, teachers, income) are not in the data.
- "Dropout suspect" is inferred from the data, not confirmed by the schools.
- Small groups give unreliable means (e.g. study time > 10h without internet: n = 3).
- The risk-rule thresholds were chosen on mathematics; the holdout shares the same schools and year.
- PISA is country-level context only and is not linked to individual students; 2000–2018 values come from Wikipedia only.

*Reproduce: `pip install -r requirements.txt`, then `python main.py` (add `--refresh-pisa` to re-scrape Wikipedia). Step-by-step analysis: `analysis.ipynb`.*
