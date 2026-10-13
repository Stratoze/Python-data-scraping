"""P1 entry point: collect raw data, then run the full StudentDataProcessor pipeline."""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # script run: write PNG files only, never open plot windows

from data_processor import StudentDataProcessor, fetch_uci_raw, read_pisa_meta, scrape_pisa_table  # noqa: E402
from report_builder import build_reports  # noqa: E402

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
RAW_PATHS = {"mat": RAW / "student-mat.csv", "por": RAW / "student-por.csv"}
PISA_RAW = RAW / "pisa_reference.csv"
OECD_RAW = RAW / "oecd_pisa2025_table_I1.csv"
PROCESSED = ROOT / "data" / "processed"
IMAGES = ROOT / "images"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-pisa", action="store_true",
                        help="re-scrape Wikipedia PISA instead of using the cached raw CSV")
    args = parser.parse_args()

    fetch_uci_raw(RAW)

    # Reference scrape: cache-first, live only when missing or --refresh-pisa
    try:
        pisa = scrape_pisa_table(out_csv=PISA_RAW, refresh=args.refresh_pisa)
        meta = read_pisa_meta(PISA_RAW) or {}
        print(f"PISA raw: {len(pisa)} rows <- {PISA_RAW.name} "
              f"(revision {meta.get('revision_id')}, scraped {meta.get('scraped_at')})")
    except Exception as exc:  # noqa: BLE001 - reference data is optional
        print(f"PISA scrape skipped ({type(exc).__name__}: {exc})")

    proc = StudentDataProcessor(RAW_PATHS, PISA_RAW, PROCESSED, IMAGES, primary_subject="mat",
                                oecd_raw=OECD_RAW)
    df = proc.load_data()
    print(f"Loaded raw: {len(df)} rows ({df['subject'].value_counts().to_dict()})")
    clean = proc.clean_data()
    print(f"Cleaned: {len(clean)} rows, log={ {k: v for k, v in proc.cleaning_log.items() if isinstance(v, int)} }")

    res = proc.analyze()
    for scope, s in res["scopes"].items():
        corr = s["corr_full"]
        print(f"[mat/{scope}] n={s['n']} pass_rate={s['pass_rate']} "
              f"G2-G3={s['corr_G1_G2_G3']['G2_G3']} absences-G3={corr['G3']['absences']}")
    high = res["risk_eval"]["all"]["high"]
    print(f"Risk rule (high vs fail): precision={high['precision']} recall={high['recall']}")
    for key in [k for k in res["risk_eval"] if k.startswith("holdout_")]:
        h = res["risk_eval"][key]["high"]
        print(f"  {key}: n={res['risk_eval'][key]['n']} precision={h['precision']} recall={h['recall']}")
    tests = res["scopes"]["exclude_dropout"]["group_tests"]
    print("Significant after Holm: " + ", ".join(f"{k} (p_holm={v['p_holm']})"
                                                for k, v in tests.items() if v["significant"]))
    print("Not significant: " + ", ".join(f"{k} (p_holm={v['p_holm']})"
                                         for k, v in tests.items() if not v["significant"]))
    print(f"Anomaly counts: {res['anomaly_counts']}")
    check = res.get("pisa_oecd_check", {})
    for year, c in ((k, v) for k, v in check.items() if k.isdigit()):
        print(f"PISA vs OECD {year}: {c['n_within_tolerance']}/{c['n_compared']} within ±{c['tolerance']}, "
              f"exact {c['n_exact']}, mismatches {c['mismatches']}")

    cleaned_csv, summary_json = proc.export_results()
    print(f"Wrote {cleaned_csv}")
    print(f"Wrote {summary_json}")
    print("Charts: 01_bar_studytime_internet.png, 02_hist_g3.png, 03_heatmap_corr.png")
    for path in build_reports(proc, ROOT):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
