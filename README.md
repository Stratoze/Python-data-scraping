# P1 — Factors Affecting Final Grades

UCI Student Performance (mathematics primary, Portuguese for comparison) + Wikipedia PISA reference.

## Quickstart (project venv — recommended)
```powershell
uv venv .venv
$env:UV_CACHE_DIR="$PWD\.uv-cache"
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\python main.py
```
Fallback without uv: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py` (if `ensurepip` fails on your machine, prefer the `uv` route above).
`main.py` downloads the UCI zip if raw CSVs are missing, then writes `data/processed/cleaned_students.csv` (both subjects), `cleaned_students_mat.csv` and `cleaned_students_por.csv` (one file per subject, no `subject` filter needed), `pisa_clean.csv`, `summary.json` and the charts in `images/`. Close those files in Excel/WPS and any image viewer before running (Windows locks open files).

PISA is **cache-first**: a normal run reads `data/raw/pisa_reference.csv` without touching the network, so results stay reproducible. `python main.py --refresh-pisa` re-scrapes Wikipedia; the new table only replaces the cache if it passes `validate_pisa_raw()` (all 3 subjects in both table families, valid years, ≥30 countries and exactly one OECD average per subject/year, scores in 200–700). Otherwise it warns and keeps the old cache. Provenance (revision id, permalink, scrape time) is stored in `data/raw/pisa_reference.meta.json` and copied to `summary.json → pisa_source`.
Open `analysis.ipynb` for the full EDA notebook. Open `notebook_huong_dan.ipynb` for a step-by-step, heavily commented walkthrough (Vietnamese; run cells top to bottom, no network, writes nothing into the project). `report.md` (English) and `report_vi.md` (Vietnamese) are **hand-written 1–2 page reports**; every number in them comes from `data/processed/summary.json`, so after re-running `main.py` on changed data, update the numbers by hand. `PROJECT_GUIDE.md` is the main overview document (data, cleaning, scraping, charts, code map; Vietnamese), `METHODS.md` explains each statistical method (formula, real code, real results; Vietnamese) and `QA.md` is the oral-defence Q&A.

Requirements: pandas, numpy, matplotlib, scipy, requests, beautifulsoup4, notebook, pytest (`requirements.txt`).

Tests: `.\.venv\Scripts\python -m pytest` (43 unit tests in `tests/test_data_processor.py`, no network needed). Only `main.py` forces the non-interactive `Agg` plotting backend; `data_processor.py` leaves the backend alone, so `plt.show()` works in the notebook.

## Layout
```
AGENTS.md  CLAUDE.md  CONTEXT.md  PROJECT_GUIDE.md  METHODS.md  QA.md
data_processor.py  main.py  requirements.txt  pytest.ini  tests/
analysis.ipynb  report.md  report_vi.md
data/raw/          student-mat.csv, student-por.csv, student.txt, student-merge.R, pisa_reference.csv (PISA scrape, page strings) + pisa_reference.meta.json, oecd_pisa2025_table_I1.csv (+ .meta.json, official OECD table used to cross-check the scrape)
data/processed/    cleaned_students.csv (both subjects + anomaly flags), cleaned_students_mat.csv, cleaned_students_por.csv, pisa_clean.csv, summary.json
images/            01_bar_studytime_internet.png, 02_hist_g3.png, 03_heatmap_corr.png
docs/agents/       issue-tracker.md, domain.md
docs/adr/          0001 flag dropout suspects, 0002 risk group never uses G3
```

## Data sources
- UCI Student Performance: https://archive.ics.uci.edu/dataset/320/student+performance (`fetch_uci_raw()` downloads `https://archive.ics.uci.edu/static/public/320/student+performance.zip` and extracts `student.zip`). Analysis is centred on `mat`; `por` is used as the out-of-sample holdout for the risk rule.
- PISA reference: https://en.wikipedia.org/wiki/Programme_for_International_Student_Assessment (latest ranking summary + "Rankings comparison 2000–2022" tables; CC BY-SA, live scrape + CSV cache)
