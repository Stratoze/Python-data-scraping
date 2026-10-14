# P1 — Kế hoạch cắt gọn source code

Trạng thái: **DONE trên branch `slim-down`** (2026-10-14, chưa merge vào `main`). Phần dưới mục "Kết quả cuối cùng" là đề xuất ban đầu, giữ lại để tham khảo; chỗ nào khác đề xuất thì theo "Kết quả cuối cùng".

## Kết quả cuối cùng (quyết định đã chốt)

**Giữ lại (khác đề xuất ban đầu ở mục 4):**
- Kiểm định: `ALPHA`/`_p`, Welch t-test + 95% CI chênh lệch, ANOVA một chiều + $\eta^2$, Holm (`_holm`), kiểm định tương quan Pearson r + p + 95% CI (`_corr_tests`). `scipy` vẫn trong `requirements.txt`.
- Rule rủi ro: `_risk_eval` (precision/recall, tỉ lệ trượt từng nhóm) + holdout trên `por` (`_risk_holdout`, holdout chặt qua `MERGE_KEYS`).
- Đối chiếu OECD (`cross_check_pisa`, `data/raw/oecd_pisa2025_table_I1.csv`), `_pisa_context`.
- CSV riêng từng môn `cleaned_students_mat.csv` / `_por.csv`.
- `clean_data()` 6 bước giữ nguyên; `cleaned_students.csv` giống hệt byte với trước khi cắt.

**Đã bỏ:** OLS + HC3 (`_ols`, `_regression`, `REG_FACTORS`), Kruskal-Wallis, Cohen's d, Wilson CI (`_wilson`), Fisher + `_tier_eval`, phân tích độ nhạy (`_sensitivity`), paired t-test + Wilcoxon 2 môn (`_paired_subjects`), `_subject_comparison`, biểu đồ 4 (`_plot_pisa`, `images/04_pisa_portugal_oecd.png`); file `report_builder.py`, `export_pdf.py`, `tests/test_report_builder.py`, `report_summary*.md`, mọi `report*.pdf`, `STATISTICAL_METHODS.md`, `PROJECT_OVERVIEW.md`, `docs/adr/0003-por-for-comparison-and-holdout-only.md`; `markdown-it-py`, `pygments` khỏi `requirements.txt`.

**Report:** `report.md` (EN) + `report_vi.md` (VI), cả hai viết tay 1–2 trang, số lấy từ `summary.json`.

**Docs:** `PROJECT_GUIDE.md` (tổng quan) + `METHODS.md` (các phương pháp thống kê) thay cho `PROJECT_OVERVIEW.md` + `STATISTICAL_METHODS.md`; `QA.md`, `README.md`, `CONTEXT.md`, ADR 0001/0002 đã cập nhật theo bản cắt gọn.

**Kích thước thực tế:** `data_processor.py` 832 dòng (trước 1043), `main.py` 72, tổng code không tính test 904 dòng (trước ~2817); 43 test (`tests/test_data_processor.py`), pass hết.

**Còn lại cho team:** slide `presentation/talk.pptx` phải sửa tay. Số holdout (recall 91.4%, precision 66.0%) và số rule trên `mat` vẫn đúng; cần rà các slide có R² hồi quy, Fisher/Wilson CI, so sánh ghép cặp 2 môn (−1.26 điểm), biểu đồ 4 PISA, tỉ lệ trượt nhóm medium/low cũ (22.5% / 4.0% → nay 7.8% / 1.2%), số test 48 → 43.

---

## 1. Mục tiêu

Chỉ giữ những gì đề P1 yêu cầu (ảnh trong `requirement/`), tập trung làm rõ **thu thập → làm sạch → chuẩn hoá dữ liệu**. Bỏ các phần thống kê nâng cao mà đề không đòi.

Đề yêu cầu:
- Thu thập UCI + scrape bảng PISA tham khảo; lưu raw CSV.
- Làm sạch kiểu dữ liệu; encode yes/no; EDA bằng `groupby` mean/std.
- Vẽ bar, histogram, heatmap; viết insight + giới hạn dữ liệu.
- 4 hàm cơ bản; list of dicts; dict mapping; set unique schools/jobs; tuple ngưỡng.
- `StudentDataProcessor.load_data() / clean_data() / analyze() / export_results()`; `main.py` xuất `cleaned_students.csv` + `summary.json`.
- Câu hỏi phụ: so sánh điểm theo studytime/absences/failures/internet; pass/fail; phân nhóm rủi ro; tương quan G1, G2, G3.
- Deliverables: notebook, `data_processor.py`, `main.py`, raw/cleaned data, 3 biểu đồ, report 1–2 trang.

## 2. Cách làm an toàn

1. Tạo nhánh mới `slim-down` từ `main` (commit `2a5f495`). **Không làm trực tiếp trên `main`.**
2. Cắt + chạy lại + test trên nhánh đó.
3. M xem kết quả, ưng thì merge vào `main`; không ưng thì xoá nhánh, `main` y nguyên.

## 3. GIỮ LẠI (không đổi logic)

| Phần | Vị trí hiện tại | Ghi chú |
|---|---|---|
| Tuple ngưỡng `THRESHOLDS`, `ANOMALY_THRESHOLDS`, `PISA_CHECKS` | `data_processor.py` 27–40 | |
| `VAR_DESCRIPTIONS`, `VALID_RANGES`, `REQUIRED_COLS`, `YES_NO_COLS`, `FLAG_COLS`, `SAMPLE_STUDENTS` | 68–108 | dict mapping, list of dicts |
| 4 hàm cơ bản + `classify_risk` | 114–162 | |
| `fetch_uci_raw` (tải UCI) | 179–192 | |
| Scrape PISA: `_parse_pisa_html`, `validate_pisa_raw`, cache-first `scrape_pisa_table`, `clean_pisa` | 195–372 | scraping là yêu cầu bắt buộc |
| `load_data()` | | bỏ phần đọc file OECD |
| **`clean_data()` 6 bước** (strip, ép kiểu + miền giá trị, encode yes/no, bỏ trùng/thiếu, cột dẫn xuất, 6 cờ bất thường) + `cleaning_log` | 681–744 | **trọng tâm, giữ nguyên 100%** |
| `analyze()`: set unique, groupby mean/std/n, tương quan G1/G2/G3 + ma trận, tỉ lệ đỗ (all vs exclude_dropout), hồ sơ 38 em G3 = 0, đánh giá rule rủi ro (tỉ lệ trượt theo nhóm, precision/recall đơn giản) | | |
| 3 biểu đồ bắt buộc: bar, histogram, heatmap | 912–989 | |
| `export_results()`: `cleaned_students.csv`, `_mat.csv`, `_por.csv`, `pisa_clean.csv`, `summary.json` | 1022–1043 | |
| `main.py` (`--refresh-pisa`, chạy pipeline, in log) | | bỏ phần in kết quả thống kê nâng cao + gọi report_builder |
| Test: 4 hàm, rule rủi ro không dùng G3, parse/validate/clean PISA, cache-first, `clean_data` với 6 dòng cấy lỗi, xuất CSV theo môn | `tests/` | |
| ADR 0001 (gắn cờ G3 = 0), ADR 0002 (rule rủi ro không dùng G3) | `docs/adr/` | sửa nhẹ chỗ nhắc holdout |

## 4. BỎ ĐI

### 4.1 Trong `data_processor.py`
| Bỏ | Dòng | Lý do |
|---|---|---|
| `ALPHA`, `BINARY_TEST_COLS`, `MULTI_TEST_COLS`, `TEST_LEVEL_CAP`, `CORR_TEST_COLS` | 42–50 | chỉ phục vụ kiểm định |
| `MERGE_KEYS`, `REG_FACTORS`, `REG_GRADES`, `OECD_PISA_YEAR`, `OECD_NAME_ALIASES` | 52–66 | ghép cặp / hồi quy / OECD |
| `cross_check_pisa` (đối chiếu OECD) | 375–416 | |
| `_p`, `_holm`, `_group_tests` (Welch t-test, ANOVA, Kruskal), `_corr_tests` | 433–502 | |
| `_ols` (hồi quy OLS + HC3) | 505–533 | |
| `_paired_subjects` (paired t-test, Wilcoxon) | 537–566 | |
| `_wilson`, `_tier_eval` (Fisher) | 597–602, 627–643 | `_risk_eval` giữ bản đơn giản: tp/fp/fn, precision, recall, tỉ lệ trượt từng nhóm |
| `_regression`, `_sensitivity`, `_risk_holdout`, `_subject_comparison` | 791–873 | |
| Biểu đồ 4 `_plot_pisa` | 991–1019 | đề chỉ cần 3 biểu đồ |
| `import scipy` | 25 | không còn dùng |

**Không chắc, m quyết:** `_pisa_context` (875–890, 16 dòng): trích điểm Bồ Đào Nha vs OECD theo năm vào `summary.json`. Giữ thì report có 1 câu bối cảnh PISA (dữ liệu scrape được *dùng* vào đâu đó); bỏ thì PISA chỉ được scrape + làm sạch + lưu CSV. **T đề xuất giữ.**

### 4.2 Bỏ nguyên file
| File | Lý do |
|---|---|
| `report_builder.py` (1591 dòng) | thay bằng `report.md` viết tay 1–2 trang |
| `export_pdf.py` | không cần PDF sinh tự động |
| `report_vi.md`, `report_summary.md`, `report_summary_vi.md`, `report*.pdf` (4 file) | |
| `tests/test_report_builder.py` | test file đã bỏ |
| `data/raw/oecd_pisa2025_table_I1.csv` + `.meta.json` | chỉ dùng cho đối chiếu OECD |
| `images/04_pisa_portugal_oecd.png` | |
| `STATISTICAL_METHODS.md` | toàn bộ nói về phần bị bỏ |
| `docs/adr/0003-por-for-comparison-and-holdout-only.md` | holdout/paired bị bỏ |

### 4.3 `requirements.txt`
Bỏ `scipy`, `markdown-it-py`, `pygments`.

### 4.4 Test bị xoá (vì code tương ứng bị bỏ)
`test_holm_*`, `test_wilson_*`, `test_ols_*`, `test_tier_eval_*`, `test_cross_check_pisa_*`, `test_holdout_*`, `test_paired_subjects_*`, `test_group_tests_*`, `test_report_builder.py`. Ước lượng còn khoảng 35 test (đếm lại sau khi cắt).

## 5. Sửa lại

| File | Sửa gì |
|---|---|
| `analysis.ipynb` | Bỏ cell 14–19 (kiểm định, OLS, sensitivity), cell 22–23 (so sánh môn), phần OECD ở cell 25, cell 27–28 (report_builder). Cell 20–21 rule rủi ro chỉ còn in-sample. Thêm 1 cell markdown insight + giới hạn viết tay. Chạy lại toàn bộ. |
| `report.md` | Viết tay 1–2 trang: câu hỏi, dữ liệu + làm sạch (số từ `cleaning_log`), phát hiện G3 = 0, EDA groupby, tương quan, rule rủi ro, PISA bối cảnh, giới hạn. Số lấy từ `summary.json` sau khi chạy. |
| `README.md`, `PROJECT_OVERVIEW.md`, `QA.md`, `CONTEXT.md` | Xoá các mục về phần đã bỏ; cập nhật số dòng, số test, danh sách file. |
| `.scratch/p1-known-issues/spec.md` | Ghi chú các mục đã bị bỏ theo quyết định cắt gọn. |

## 6. Hệ quả m cần biết trước

1. **Mất các kết luận có kiểm định**, report chỉ còn nói ở mức mô tả:
   - "Internet không có ý nghĩa sau hiệu chỉnh Holm (p = 0.080)" → chỉ còn "nhóm có internet cao hơn ~1 điểm, error bar chồng nhau, mẫu không có internet nhỏ".
   - Hồi quy R² 0.234 / 0.937 → chỉ còn tương quan r(G2, G3) = 0.966.
   - Holdout `por` recall 91.4% → chỉ còn số trên `mat` (recall 93.8%, precision 81.9%), và phải ghi rõ là **đánh giá trên chính dữ liệu dùng để đặt ngưỡng** (lạc quan hơn thực tế).
   - "Toán thấp hơn Bồ Đào Nha 1.26 điểm (ghép cặp)" → bỏ.
   - "PISA 274/274 khớp OECD" → bỏ.
2. **Slide `presentation/talk.pptx` (Stratoze vừa sửa slide 6–7) đang dùng số holdout và rule** → phải sửa slide cho khớp. T không sửa được file pptx cho đẹp; Stratoze/m tự sửa.
3. Báo cáo không còn tự sinh: sửa code mà số đổi thì phải tự sửa `report.md` (đây là lỗi A2 cũ quay lại, chấp nhận vì report chỉ 1–2 trang).
4. Ước lượng `data_processor.py` từ 1043 còn khoảng 650–700 dòng; tổng code (không tính test) từ ~2817 còn khoảng 750 dòng. **Số ước lượng, đếm lại sau khi cắt.**

## 7. Kiểm tra sau khi cắt

- `pytest` pass toàn bộ.
- `python main.py` chạy được, ra đủ 3 ảnh + 5 file trong `data/processed/`.
- Notebook chạy lại từ đầu không lỗi.
- Grep không còn tên hàm/hằng đã bỏ (`_holm`, `_ols`, `cross_check_pisa`, `report_builder`, `scipy`…) trong code và docs.
- So số cốt lõi trước/sau (tỉ lệ đỗ 67.1% / 74.2%, 38 em G3 = 0, r(G2, G3) = 0.966, recall/precision rule) phải **giống hệt**, vì phần làm sạch không đổi.

## 8. M cần trả lời

1. Duyệt toàn bộ, hay gạch mục nào ra khỏi danh sách "BỎ ĐI"?
2. `_pisa_context` + 1 câu bối cảnh PISA trong report: giữ (đề xuất) hay bỏ?
3. Report viết tay bằng tiếng Anh, tiếng Việt, hay cả hai?
4. Có giữ `cleaned_students_mat.csv` / `_por.csv` không (đề chỉ yêu cầu `cleaned_students.csv`)? T đề xuất giữ, chỉ 3 dòng code.
