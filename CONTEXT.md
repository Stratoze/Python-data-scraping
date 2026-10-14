# Student Performance

Analysis of factors influencing final grades in secondary education mathematics (primary subject `mat`), with Portuguese (`por`) as a secondary comparison cohort.

## Language

**Final Grade (G3)**:
Year-end grade on a 0-20 scale; the prediction target.
_Avoid_: final score, result

**Pass**:
G3 >= 10. Binary outcome derived from Final Grade.
_Avoid_: succeed, cleared

**Intermediate Grades (G1, G2)**:
First- and second-period grades on a 0-20 scale.
_Avoid_: midterm, mid score

**Studytime**:
Weekly study time bucket 1-4 (<2h, 2-5h, 5-10h, >10h).
_Avoid_: study hours, learning time

**Absences**:
Count of school absences. Bucketed low 0-3 / medium 4-9 / high >=10.
_Avoid_: truancy, missing days

**Failures**:
Count of past class failures (0-3). Distinct from Absences.
_Avoid_: repeats, fails

**Risk Group**:
Early-warning segment: low / medium / high, derived only from information available before the final exam (Intermediate Grades, Failures, Absences — never G3). high: G2 < 10 or Failures >= 2; medium: G1 < 10 or Failures >= 1 or Absences high. Tiers map to actions: high = intervene, medium = monitor, low = no action. Observed fail rates on `mat`: high 81.9%, medium 7.8%, low 1.2%; on the strict Holdout: 66.0%, 9.8%, 0.8%.
_Avoid_: risk level, danger group

**Holdout**:
Out-of-sample check of the frozen Risk Group rule on the non-primary Subject (`por`). "Strict holdout" keeps only `por` students whose 13 merge keys (as in `student-merge.R`) do not appear in `mat`.
_Avoid_: test set, validation data

**Dropout Suspect**:
Student with G3 = 0. In `mat` all 38 such students also have 0 recorded Absences, so the zero reflects not sitting the final exam / leaving school rather than a real grade. Flagged, never deleted; headline statistics are reported both with and without them.
_Avoid_: zero scorer, outlier student

**Anomaly Flag**:
Boolean column marking a suspicious row without removing it: `dropout_suspect`, `g2_zero`, `grade_drop` (G1−G3 >= 8 or G2−G3 >= 6, excluding Dropout Suspects), `absence_outlier` (> Q3 + 1.5·IQR within subject), `age_outlier` (age >= 20), `inconsistent_grade` (G3 > 0 but G2 = 0).
_Avoid_: error row, bad data

**Subject**:
Course cohort of a row: `mat` (mathematics, 395 rows) or `por` (Portuguese, 649 rows). Some students appear in both.

**PISA Reference**:
Country-level PISA mean scores scraped from Wikipedia (latest ranking summary + 2000–2022 comparison tables). Context only; never joined to student rows.
The latest cycle (2025) and the derived 2022 values are cross-checked against OECD Table I.1 (`data/raw/oecd_pisa2025_table_I1.csv`); earlier cycles are Wikipedia-only.
