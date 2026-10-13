# P1 Report — Factors Affecting Final Grades (UCI Student Performance, `mat`)

*Summary version. Full report (data, code, charts, tests): `report.pdf`.*

**Main question:** How do study time, absences, family support and intermediate grades (G1, G2)
relate to the final grade (G3)?

## 1. Executive summary

| Question | Answer (mathematics, 357 students with G3 > 0 unless stated) |
|---|---|
| Intermediate grades → G3 | Strongest link: r(G2, G3) = **0.966**, r(G1, G3) = 0.892 |
| Past failures → G3 | 0 failures: **11.94**, 1: 10.15, 2: 8.83, 3: 8.27 (r = -0.294) |
| Absences → G3 | low 12.26 / medium 11.38 / high 10.37 (r = **-0.213**, ANOVA Holm p < 0.001) |
| Study time → G3 | weak positive, r = 0.127 (ANOVA Holm p 0.019, eta² = 0.036: small) |
| Internet at home → G3 | yes 11.68 vs no 10.71; raw p 0.027, Holm p 0.080 → **not significant after correction** |
| All factors together (regression) | background factors explain R² = 0.234; significant in both courses with the others held fixed: **studytime (+1 bucket), failures (+1 past failure), absences (+1 absence), schoolsup (yes vs no)**; internet adjusted b = +0.53 (p 0.247) |
| Family support (`famsup`) → G3 | yes 11.35 vs no 11.8 (Holm p 0.404): **no significant difference** |
| Pass rate | 67.1% of all 395 students; 74.2% after removing 38 dropout suspects |
| Early-warning rule (no G3) | designed on mat: recall 93.8%, precision 81.9%; **tested on unseen Portuguese-only students: recall 91.4%, precision 66.0%** |

**Key data-quality finding:** 38 students have G3 = 0 and **38 of them have 0 recorded
absences**. They are treated as *dropout suspects* (flagged, not deleted). Including them flips the absences
correlation to r = 0.034 and hides the real negative effect.

## 2. Limitations and next steps

- One subject/year as primary cohort; small groups (see Chart 1 `n=` labels) give wide confidence intervals.
- Regression adjusts only for variables in the data; unmeasured factors (motivation, teachers, income) can still confound, so effects are associations, not causes.
- "Dropout suspect" is inferred from the data, not confirmed by the schools; the sensitivity analysis (6.1) shows the absences conclusion does not depend on it.
- The holdout set shares the schools and the school year with the training data, and the strict holdout is small (n = 275); precision on new schools could differ.
- PISA 2025 and 2022 values are verified against the OECD report; earlier cycles (2000–2018) come from Wikipedia only.
- All findings are correlational, not causal.

*Reproduce: `pip install -r requirements.txt` then `python main.py` (add `--refresh-pisa` to re-scrape Wikipedia).*
