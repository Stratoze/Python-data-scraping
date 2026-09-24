"""P1 entry point: run the full StudentDataProcessor pipeline."""
from pathlib import Path

from data_processor import StudentDataProcessor, scrape_pisa_table

ROOT = Path(__file__).resolve().parent
RAW_MAT = ROOT / "data" / "raw" / "student-mat.csv"
PISA_RAW = ROOT / "data" / "raw" / "pisa_reference.csv"
PROCESSED = ROOT / "data" / "processed"
IMAGES = ROOT / "images"


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)

    # Reference scrape (live with cache fallback)
    try:
        pisa = scrape_pisa_table(out_csv=PISA_RAW)
        print(f"PISA reference: {pisa.shape[0]} rows x {pisa.shape[1]} cols -> {PISA_RAW.name}")
    except Exception as exc:  # noqa: BLE001 - reference data is optional
        print(f"PISA scrape skipped ({type(exc).__name__})")

    proc = StudentDataProcessor(RAW_MAT, PISA_RAW, PROCESSED, IMAGES)
    df = proc.load_data()
    print(f"Loaded raw: {len(df)} rows")
    clean = proc.clean_data()
    print(f"Cleaned: {len(clean)} rows, pass_rate={(clean['pass_fail'] == 'pass').mean():.3f}")
    results = proc.analyze()
    print(f"G1-G3 corr={results['corr_G1_G2_G3']['G1_G3']}, "
          f"G2-G3 corr={results['corr_G1_G2_G3']['G2_G3']}")
    cleaned_csv, summary_json = proc.export_results()
    print(f"Wrote {cleaned_csv}")
    print(f"Wrote {summary_json}")
    print("Charts: 01_bar_studytime_internet.png, 02_hist_g3.png, 03_heatmap_corr.png")


if __name__ == "__main__":
    main()
