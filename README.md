# P1 — Factors Affecting Final Grades

UCI Student Performance (mathematics) + Wikipedia PISA reference.

## Quickstart (project venv — recommended)
```powershell
uv venv .venv
$env:UV_CACHE_DIR="$PWD\.uv-cache"
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\python main.py
```
Fallback without uv: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py` (if `ensurepip` fails on your machine, prefer the `uv` route above).
Outputs: `data/processed/cleaned_students.csv`, `data/processed/summary.json`, charts in `images/`.
Open `analysis.ipynb` for the full EDA notebook; see `report.md` for the 1–2 page write-up.

## Layout
```
AGENTS.md  CLAUDE.md  CONTEXT.md
data_processor.py  main.py  requirements.txt
analysis.ipynb  report.md
data/raw/          student-mat.csv, student-por.csv, student.txt, pisa_reference.csv
data/processed/    cleaned_students.csv, summary.json
images/            01_bar_studytime_internet.png, 02_hist_g3.png, 03_heatmap_corr.png
docs/agents/       issue-tracker.md, domain.md
```

## Data sources
- UCI Student Performance: https://archive.ics.uci.edu/dataset/320/student+performance (downloaded `student+performance.zip` via `https://archive.ics.uci.edu/static/public/320/student+performance.zip`, extracted `student-mat.csv`; scope locked to mat per grill decision)
- PISA reference: https://en.wikipedia.org/wiki/Programme_for_International_Student_Assessment (live scrape + CSV cache)
