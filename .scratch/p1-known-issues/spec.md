# P1 — Các vấn đề còn tồn đọng

Status: in-progress

Audit ngày 2026-10-13, sau khi đã làm xong `.scratch/p1-review-fixes/spec.md`. Mỗi mục có: **bằng chứng** (đã kiểm chứng hay suy luận), **rủi ro**, **cách xử lý gợi ý**.

**Tiến độ (cập nhật 2026-10-13):**

| Trạng thái | Mục |
|---|---|
| ✅ Đã xử lý | A1, A2, A3, B1, B2, B3, B4, B5, B6, B7, C1, C2, C3, C5, C6, D1, D2, D5, D6, D7, D8, E1, E2, F2, F3, F4 |
| 🟡 Một phần | D3 (chỉ ghi chú, notebook vẫn ghi file), D4 (chưa pin version) |
| ⏭️ Không làm (user quyết định) | C4 (bỏ phần DevTools), D3/D4 phần còn lại, F1 (user tự làm lại slide), F5 (chạy `export_pdf.py` sau `main.py` là đủ) |
| ⬜ Còn mở | — |

*A3 (2026-10-13): code đã commit + push lên `origin/main` (`e32eeb2`), `.idea/` và `.pytest_cache/` đã vào `.gitignore`.*

Mức độ:
- 🔴 **Cao**: có thể bị trừ điểm hoặc làm sai kết luận.
- 🟠 **Trung bình**: kết luận yếu hoặc dễ bị hỏi vặn.
- 🟡 **Thấp**: kỹ thuật, độ bền, vệ sinh code.

---

## A. Nộp bài / định dạng

### A1 🔴 Report là `report.md` tiếng Anh, chưa có PDF/Word
- **Bằng chứng:** đề ghi "report 1-2 trang" nhưng không nói định dạng. `report.md` dài khoảng 6 KB, tức ~1.5 trang A4.
- **Rủi ro:** lớp có thể yêu cầu PDF/DOCX hoặc viết tiếng Việt.
- **Xử lý:** hỏi giảng viên. Nếu cần thì export bằng `pandoc report.md -o report.pdf` (hoặc docx), hoặc dịch sang tiếng Việt.
- 🟡 **Một phần (2026-10-13):**
  - Đã có bản tiếng Việt `report_vi.md` song song với `report.md`.
  - Theo yêu cầu "report để chiếu", cả 2 file giờ rất chi tiết (~1080 dòng, có code + ảnh + chú thích). Mục **1. Tóm tắt** đứng riêng, dùng làm bản "1–2 trang" nếu cần.
  - ✅ Đã xuất PDF: `export_pdf.py` tạo `report.pdf` và `report_vi.pdf` (mỗi file 32 trang A4, có ảnh, bảng, code tô màu, tiếng Việt hiển thị đúng). Còn vướng độ dài so với yêu cầu 1–2 trang.
  - ✅ **(2026-10-13)** Thêm bản tóm tắt: `report_builder._summary()` cắt từ báo cáo đầy đủ ra `report_summary.md` / `report_summary_vi.md` (tiêu đề, câu hỏi chính, mục 1 Tóm tắt, mục Giới hạn); `export_pdf.py` xuất `report_summary.pdf` / `report_summary_vi.pdf`, **mỗi file 2 trang A4**, số liệu giống hệt bản đầy đủ. Vẫn nên hỏi giảng viên muốn nộp bản nào.

### A2 🟠 Nhận định trong report và notebook bị hardcode số liệu
- **Bằng chứng:** các con số như 0.742, −0.21, 0.966 được gõ tay trong `report.md` và cell markdown cuối của `analysis.ipynb`.
- **Rủi ro:** `main.py` cào PISA live mỗi lần chạy (xem C1). Nếu dữ liệu đổi, chart và `summary.json` đổi theo nhưng chữ trong report thì không, dẫn tới report lệch số.
- **Xử lý:** trước khi nộp, đối chiếu lại report với `summary.json`. Hoặc sinh đoạn insight trong notebook bằng f-string đọc trực tiếp từ `res`.
- ✅ **Đã xử lý (2026-10-13):**
  - `report_builder.py` sinh `report.md` + `report_vi.md` ở cuối mỗi lần `main.py` chạy. Mọi số liệu lấy từ `proc.results` (chính là nội dung `summary.json`). Mọi block code lấy bằng `inspect.getsource`, kèm số dòng.
  - Cell insight cuối notebook giờ gọi `build_reports(proc)` rồi hiển thị mục 1 + 13 của report, không còn số gõ tay.

### A3 🟡 Chưa commit git; có file rác chưa xử lý — ⏭️ bỏ qua theo quyết định của user (2026-10-13)
- **Bằng chứng:** `git status` cho thấy 12 file modified, cùng các mục untracked: `.idea/`, `.scratch/`, `requirement/`, `data/processed/pisa_clean.csv`.
- **Xử lý:**
  - Thêm `.idea/` vào `.gitignore`.
  - Quyết định có commit `requirement/` (ảnh đề) và `.scratch/` hay không.
  - Commit file `pisa_clean.csv`.

---

## B. Phân tích / thống kê

### B1 🟠 Không có kiểm định thống kê, chỉ so mean
- **Bằng chứng:** chênh lệch giữa các nhóm chỉ là mean ± std; không có t-test hay ANOVA. T tự tính Welch t (xấp xỉ chuẩn) trên mat bỏ dropout:

  | So sánh | t | p xấp xỉ | Kết luận |
  |---|---|---|---|
  | internet yes vs no | 2.25 | ≈ 0.03 | có ý nghĩa, nhưng sát ngưỡng |
  | famsup yes vs no | −1.28 | ≈ 0.20 | **không có ý nghĩa** |
  | schoolsup yes vs no | −5.46 | < 0.001 | có ý nghĩa |

- **Rủi ro:** report nói "internet +1 điểm" mà không có độ tin cậy. Riêng famsup cần ghi rõ là không khác biệt.
- **Xử lý:**
  - Thêm Welch t-test / one-way ANOVA. Cần thêm `scipy`, venv hiện **chưa có**.
  - Hoặc báo cáo khoảng tin cậy 95% cho chênh lệch mean.
- ✅ **Đã xử lý (2026-10-13):**
  - Thêm `scipy` vào venv và `requirements.txt`.
  - `_group_tests()` chạy Welch t-test (kèm CI 95% của chênh lệch và Cohen's d) cho internet/famsup/schoolsup/paid; chạy one-way ANOVA (kèm eta²) + Kruskal–Wallis cho studytime/absence_level/failures. Cả 7 kiểm định hiệu chỉnh **Holm** với α = 0.05.
  - `_corr_tests()` tính p-value và CI 95% cho r với G3.
  - Kết quả lưu ở `summary.json → scopes.*.group_tests / corr_tests`; report có mục 7.1 (EN/VI) và notebook có cell 6b.
  - **Kết luận đổi so với trước:** internet có p gốc 0.027 nhưng p Holm = **0.080**, tức **không còn ý nghĩa**. Có ý nghĩa: schoolsup, studytime (eta² chỉ 0.036), absence_level, failures. famsup và paid không có ý nghĩa. ANOVA và Kruskal–Wallis cho cùng kết luận ở mọi biến.

### B2 🟠 Không kiểm soát biến gây nhiễu (confounding)
- **Bằng chứng:** mọi phân tích đều là 1 biến so với G3. Internet, famsup, schoolsup đều có thể đi kèm hoàn cảnh gia đình (Medu/Fedu) hoặc năng lực sẵn có (G1, failures).
- **Rủi ro:** người đọc dễ hiểu các kết luận theo nghĩa nhân quả.
- **Xử lý:** thêm 1 hồi quy tuyến tính đa biến (statsmodels hoặc numpy lstsq), ví dụ `G3 ~ studytime + absences + failures + famsup + internet + Medu`, hoặc ít nhất là phân tầng theo `failures` hay `Medu`. Đề không bắt buộc, nhưng làm thì phần giới hạn mạnh hơn.
- ✅ **Đã xử lý (2026-10-13):**
  - `_ols()` là hồi quy OLS tự viết bằng numpy, sai số chuẩn HC3, p và CI lấy từ phân phối t. Có test kiểm tra hàm ước lượng lại đúng các hệ số đã biết trên dữ liệu giả lập có biến tương quan.
  - `_regression()` chạy 2 mô hình, cho cả mat và por, chỉ trên học sinh có G3 > 0:
    - **Mô hình A:** 13 yếu tố nền (các biến của câu hỏi chính + Medu, Fedu, giới tính, tuổi, nơi ở).
    - **Mô hình B:** A + G1, G2.
  - **Kết quả mô hình A:** R² mat 0.234, por 0.321.
    - Có ý nghĩa ở **cả 2 môn** khi giữ các yếu tố khác cố định: studytime, failures, absences, schoolsup.
    - **Internet sau điều chỉnh b = +0.53, p = 0.25**, tức không có tác động riêng. famsup cũng không có ý nghĩa.
  - **Kết quả mô hình B:** R² 0.937 (mat). Ngoài G1, G2, chỉ còn absences giữ ý nghĩa ở mat (b = −0.013).
  - Kết quả lưu ở `summary.json → regression`, report mục 7.2 (EN/VI) và notebook mục 6c.

### B3 🟠 "Dropout suspect" chỉ là suy luận, và kéo theo nghi vấn về cột absences
- **Bằng chứng:** cả 38/38 em G3 = 0 đều có absences = 0. Có 13 em G2 = 0. G1 trung bình của nhóm này là 7.5.
- **Rủi ro:**
  - Không có xác nhận từ nguồn (UCI không giải thích ý nghĩa điểm 0).
  - Absences = 0 nhiều khả năng là **không được ghi nhận** chứ không phải đi học đủ. Tức cột absences có thể bị thiếu một cách có hệ thống (MNAR), ảnh hưởng mọi phân tích về vắng học, kể cả ở nhóm còn lại.
- **Xử lý:** report đã ghi "inferred" ở phần giới hạn; nên nói thêm ý MNAR. Có thể chạy độ nhạy: loại thêm những em absences = 0 và G2 thấp.
- ✅ **Đã xử lý (2026-10-13):** `_sensitivity()` chạy lại phân tích vắng học theo 3 kịch bản (toàn bộ / bỏ dropout / bỏ dropout + bỏ absences = 0) cho cả 2 môn.
  - Bỏ thêm absences = 0 thì r vẫn **âm và có ý nghĩa**: mat −0.176 (p 0.003), por −0.142 (p 0.004).
  - Mẫu hình "G3 = 0 luôn kèm absences = 0" lặp lại độc lập ở por (15/15).
  - Kết luận: kết luận về vắng học không phụ thuộc vào giả định bỏ thi, cũng không phụ thuộc vào việc absences = 0 là thật hay do không ghi nhận.
  - Kết quả ở report mục 6.1 và notebook mục 6d. Phần giới hạn của report đã đổi câu tương ứng.

### B4 🟠 Rule cảnh báo rủi ro chỉ đánh giá in-sample
- **Bằng chứng:** ngưỡng `G2 < 10 or failures >= 2` được chọn sau khi đã nhìn chính dữ liệu `mat`, rồi precision 0.819 / recall 0.939 cũng đo trên đúng dữ liệu đó.
- **Rủi ro:** con số lạc quan hơn thực tế.
- **Xử lý:** kiểm tra out-of-sample trên `por`. Code chỉ cần gọi `_risk_eval` cho `subject == "por"`, rồi ghi số đó vào report.
- ✅ **Đã xử lý (2026-10-13):**
  - `_risk_holdout()` giữ nguyên rule (không đổi ngưỡng) rồi đánh giá trên `por` theo 2 cách: toàn bộ (n = 649) và **holdout chặt**, tức chỉ học sinh có 13 cột `MERGE_KEYS` không xuất hiện trong `mat` (n = 275).
  - Precision và recall có thêm khoảng tin cậy Wilson 95% (`_wilson`).

  | Tập | Recall [CI 95%] | Precision [CI 95%] |
  |---|---|---|
  | mat in-sample | 93.8% [88.3, 96.9] | 81.9% [74.9, 87.2] |
  | por toàn bộ | 90.0% [82.6, 94.5] | 59.2% [51.3, 66.7] |
  | por holdout chặt | 91.4% [82.5, 96.0] | 66.0% [56.1, 74.6] |

  - **Kết luận:** recall giữ vững, precision giảm (một phần vì tỉ lệ trượt ở por thấp hơn). Report giờ trích con số holdout làm con số chính.
  - **Còn lại:** holdout vẫn cùng trường, cùng năm học (đã ghi ở phần giới hạn).

### B5 🟠 Nhóm "medium" của rule rủi ro gần như vô dụng
- **Bằng chứng:** tỉ lệ fail theo nhóm là low 1.2%, **medium 7.8%**, high 81.9%. Nếu flag cả high lẫn medium thì precision tụt còn 0.566.
- **Rủi ro:** phân 3 nhóm không mang thêm thông tin so với 2 nhóm.
- **Xử lý:** gộp thành 2 nhóm (high / not high) hoặc chỉnh lại tiêu chí của medium. Ghi nhận xét này vào report.
- ✅ **Đã xử lý (2026-10-13), nhưng theo hướng giữ 3 nhóm vì dữ liệu cho thấy medium có ích:**
  - `_tier_eval()` tính tỉ lệ trượt theo nhóm (kèm CI Wilson) và kiểm định Fisher giữa medium và low.
  - **mat:** medium trượt gấp ×6.6 so với low (p 0.013).
  - **por holdout chặt (dữ liệu rule chưa thấy):** ×12.4 (p 0.008).
  - Nhận định cũ "medium gần như vô dụng" là sai: tỉ lệ 7.8% thấp so với high, nhưng cao hơn low nhiều lần.
  - Report giờ gán mỗi nhóm một hành động: **high → can thiệp**, **medium → theo dõi**, **low → không cần can thiệp**. Precision/recall chính vẫn dùng nhóm high.
  - Thử 3 tiêu chí medium khác (dựa trên G2 < 12…) đều cho tỉ lệ trượt 5–10%, nên giữ tiêu chí cũ để tránh overfit.
  - Định nghĩa trong `CONTEXT.md` đã cập nhật.

### B6 🟡 Nhóm cỡ mẫu nhỏ
- **Bằng chứng:** chart 1 có nhóm studytime >10h & no internet chỉ n = 3; studytime 5–10h & no internet n = 5. Failures = 2 hoặc 3 chỉ có n = 12 và 11.
- **Rủi ro:** mean của các nhóm này không đáng tin. Chart đã có CI nhưng người đọc vẫn có thể đọc nhầm.
- **Xử lý:** gộp studytime 3+4, failures ≥ 2. Hoặc giữ nguyên nhưng nhắc rõ trong report (hiện đã nhắc).
- ✅ **Đã xử lý (2026-10-13):**
  - Kiểm định ANOVA/Kruskal gộp số lần trượt 2 và 3 thành nhóm "2+" (`TEST_LEVEL_CAP`). Kết quả vẫn có ý nghĩa (p Holm < 0.001, eta² 0.089). Bảng mô tả ở mục 7 vẫn giữ đủ 4 mức, và có câu nhắc nhóm 2, 3 chỉ có n = 12 và 11.
  - Chart 1: các cột có dưới `MIN_RELIABLE_N = 10` học sinh được vẽ gạch chéo, làm mờ, có chú giải "n < 10: unreliable". Report nêu rõ tên các cột này.
  - Không gộp studytime 3+4 trên chart: nhóm không internet gộp lại cũng chỉ có n = 8, nên vẫn không đáng tin; giữ 4 mức theo đề.

### B7 🟡 So sánh `mat` và `por` không độc lập
- **Bằng chứng:** merge theo 13 cột giống `student-merge.R` ra **382** cặp. Có 4 bản ghi trùng key trong mat và 12 trong por, nên key không duy nhất tuyệt đối.
- **Rủi ro:** `subject_comparison` đang coi 2 nhóm là độc lập, trong khi phần lớn học sinh xuất hiện ở cả hai.
- **Xử lý:** ghi rõ trong report. Nếu muốn so sánh cùng một học sinh, dùng bảng merge và làm paired comparison.
- ✅ **Đã xử lý (2026-10-13):**
  - Thêm `_paired_subjects()`: ghép học sinh theo `MERGE_KEYS`, bỏ các key bị lặp trong cùng file (8 dòng mat, 23 dòng por). Ghép được **358** học sinh, trong đó 324 cặp có G3 > 0 ở cả 2 môn.
  - Kết quả so sánh ghép cặp: điểm Toán thấp hơn điểm Bồ Đào Nha trung bình 1.26 điểm [−1.56, −0.96], p < 0.001 (cả t-test ghép cặp lẫn Wilcoxon). r(G3 mat, G3 por) = 0.589.
  - Mục 10.1 trong report bỏ câu "replicate on an independent file", thay bằng giải thích vì sao 2 file không độc lập, kèm bảng so sánh ghép cặp. Kiểm chứng độc lập thật sự là holdout chặt (n = 275).
  - Số khớp được (358) khác con số 382 ghi ở trên vì giờ bỏ hẳn các key bị lặp thay vì ghép tất cả.

---

## C. Dữ liệu cào (PISA)

### C1 🔴 Raw PISA bị ghi đè mỗi lần chạy, kết quả không tái lập được
- **Bằng chứng:** `main.py` gọi `scrape_pisa_table(out_csv=PISA_RAW)` mỗi lần chạy. Cache chỉ được dùng **khi mạng lỗi**. Spec cũ yêu cầu "chạy lại thì đọc từ cache".
- **Rủi ro:**
  - Wikipedia sửa bảng là `pisa_reference.csv`, `pisa_clean.csv`, `pisa_context` đổi theo, lệch với report.
  - Nguyên tắc "raw không sửa" bị vi phạm với dữ liệu PISA.
- **Xử lý:** đổi sang cache-first, chỉ cào lại khi có cờ `--refresh-pisa` hoặc khi file chưa tồn tại. Ghi thêm ngày cào vào `summary.json`.
- ✅ **Đã xử lý (2026-10-13):**
  - `scrape_pisa_table(..., refresh=False)` chuyển sang cache-first: chạy bình thường thì không gọi mạng.
  - Chỉ cào lại khi chạy `python main.py --refresh-pisa` hoặc khi chưa có cache.
  - Mỗi lần cào lại, provenance (revision id `1378067005`, permalink, `scraped_at`) được ghi vào `data/raw/pisa_reference.meta.json` và `summary.json → pisa_source`. Report cũng trích permalink revision này.

### C2 🟠 Số liệu PISA 2025 lấy từ Wikipedia chưa đối chiếu với OECD
- **Bằng chứng:** OECD đã công bố PISA 2025 ngày 8/9/2026 ([OECD press release](https://www.oecd.org/en/about/news/press-releases/2026/09/pisa-2025-students-reading-and-mathematics-performance-declined-sharply-across-the-oecd.html)), nên việc có bảng 2025 là hợp lý. *(Lần trước t nghi bảng bị gắn nhãn sai, nghi đó sai. Năm 2025 là thật.)* Tuy nhiên các con số cụ thể, ví dụ Portugal math 460 hay OECD 463, **chưa đối chiếu** với bảng gốc của OECD. Riêng việc B-S-J-Z (China) xuất hiện trong bảng 2025 là [INFERENCE] đáng kiểm tra.
- **Rủi ro:** Wikipedia có thể sai hoặc bị sửa.
- **Xử lý:** so Portugal và OECD average 2025 với [PISA 2025 Results, Volume I](https://www.oecd.org/en/publications/2026/09/pisa-2025-results-volume-i_5265bfb1.html), rồi trích nguồn OECD trong report.
- ✅ **Đã xử lý (2026-10-13):**
  - **Nguồn đối chiếu:** trích Table I.1 (trang 30) từ PDF chính thức của OECD ([DOI 10.1787/73451bc5-en](https://doi.org/10.1787/73451bc5-en), CC BY 4.0) vào `data/raw/oecd_pisa2025_table_I1.csv` (92 dòng = OECD average + 91 nước), kèm file `.meta.json` ghi nguồn.
  - **Code:** `cross_check_pisa()` so từng (nước, môn, năm). Có 5 tên nước khác nhau giữa 2 nguồn, ánh xạ bằng `OECD_NAME_ALIASES`. Kết quả nằm ở `summary.json → pisa_oecd_check`, report mục 3.4 và mục 12.
  - **2025:** **274/274 điểm khớp tuyệt đối**, gồm cả Portugal 460/462/482 và OECD 463/461/482.
  - **2022 (suy ra = điểm 2025 − mức thay đổi, cho lệch ±1 do làm tròn):** 208/211 khớp. 3 dòng lệch 6–7 điểm đều là Palestinian Authority, không ảnh hưởng Portugal.
  - Bảng Wikipedia môn Toán và Đọc hiểu thiếu Uzbekistan.
  - **Đính chính:** B-S-J-Z (China) có mặt trong bảng OECD 2025, nên nghi vấn [INFERENCE] trước đó là sai.
  - **Còn lại:** các kỳ 2000–2018 vẫn chỉ dựa vào Wikipedia.

### C3 🟡 Parser PISA phụ thuộc cấu trúc trang
- **Bằng chứng:** năm của bảng summary lấy từ regex trên heading ("PISA 2025 ranking summary"). Môn học lấy theo thứ tự header của bảng chứa. Bảng comparison được nhận diện nhờ hàng 2 bắt đầu bằng `Country`.
- **Rủi ro:** Wikipedia đổi layout là parser ra 0 dòng (`ValueError`), hoặc gán sai môn/năm mà không báo lỗi.
- **Xử lý:** thêm sanity check, ví dụ mỗi (subject, year) phải có ≥ 30 nước và có dòng `OECD average`; sai thì raise.
- ✅ **Đã xử lý (2026-10-13):** thêm `validate_pisa_raw()`, ngưỡng nằm trong tuple `PISA_CHECKS = (30, 200, 700)`. Kiểm tra:
  - Cả `summary` và `comparison` phải có đủ 3 môn.
  - Năm là số nằm trong khoảng 2000 đến năm hiện tại.
  - Score nằm trong khoảng 200–700.
  - Mỗi (source, subject, year) có ≥ 30 nước có điểm, có rank dạng số, không trùng nước, và có đúng 1 dòng OECD average.

  Validation chạy cho cả dữ liệu cào live lẫn khi đọc cache. Kết quả cào mới không đạt thì **không ghi đè** cache, chỉ cảnh báo rồi dùng lại cache cũ; không có cache thì báo `RuntimeError`.

  Smoke test đã chạy:
  - Đọc cache không gọi mạng.
  - Layout hỏng → có cảnh báo, md5 của cache không đổi.
  - Validation bắt được 4 kiểu sai: mất 1 môn, mất nhãn năm, score bị lệch sang cột rank, mất dòng OECD.
  - Trang thật vẫn qua validation.

### C4 🟡 Chưa làm phần cào thủ công bằng trình duyệt (DevTools)
- **Bằng chứng:** hướng dẫn nằm ở `.scratch/p1-review-fixes/spec.md` mục 7.2 bước 1, nhưng phần cào thực tế làm bằng Python.
- **Rủi ro:** nếu thầy cô muốn thấy thao tác cào trên trình duyệt thì chưa có minh chứng.
- **Xử lý:** chụp màn hình Console chạy snippet liệt kê bảng, đưa vào report hoặc phụ lục.
- ❌ **Lần làm trước (2026-10-13) sai, đã gỡ:** ảnh `images/05_devtools_console.png` là **ảnh dựng** (trang HTML tự viết giả giao diện Console, chụp bằng Chrome headless), không phải chụp màn hình thật. File `data/raw/pisa_manual_check.csv` cũng do Python cào, không phải lệnh `copy(...)` trên trình duyệt. Report lại mô tả như đã thao tác thật, tức là minh chứng sai sự thật.
- ⏭️ **Quyết định (2026-10-13, user chọn):** bỏ hẳn phần DevTools. Đã xoá ảnh, file CSV, test liên quan, và mục "Bước 1 DevTools" trong report EN/VI + `PROJECT_OVERVIEW.md`. Mục 3.2 chỉ mô tả đúng phần cào bằng Python (`requests` + `BeautifulSoup`).
- Nếu sau này cần minh chứng trình duyệt thật: tự mở Chrome → F12 → Console, chạy snippet ở `.scratch/p1-review-fixes/spec.md` mục 7.2 bước 1 rồi chụp màn hình thật.

### C5 🟡 PISA chưa được trực quan hoá
- **Bằng chứng:** đề chỉ yêu cầu 3 biểu đồ (đã đủ). `pisa_context` chỉ nằm trong JSON và report dạng chữ.
- **Xử lý (tuỳ chọn):** thêm 1 line chart "Portugal vs OECD average 2000–2025" vào notebook (không bắt buộc).
- ✅ **Đã xử lý (2026-10-13):**
  - `_plot_pisa()` sinh `images/04_pisa_portugal_oecd.png`: 3 ô (Toán / Đọc hiểu / Khoa học), đường Portugal so với OECD average, có dải cam đánh dấu năm học của dữ liệu UCI (2005–06) và nhãn điểm mới nhất.
  - Ảnh nằm trong report mục 10.2 (định nghĩa, bảng thành phần, kết luận tính tự động, code) và trong notebook mục 9.

### C6 🟡 Attribution và User-Agent
- **Bằng chứng:** User-Agent `P1-edu-project/1.0 (...)` không có email liên hệ (Wikimedia khuyến nghị có).
- **Xử lý:** thêm email vào `HTTP_HEADERS`. *(Phần ghi giấy phép CC BY-SA và revision trong report đã làm ngày 2026-10-13.)*
- ✅ **Đã xử lý (2026-10-13):**
  - `HTTP_HEADERS["User-Agent"]` trong `data_processor.py`: `"P1-edu-project/1.0 (+https://github.com/Stratoze/Python-data-scraping) student coursework"`.
  - Có tên công cụ + link repo GitHub làm thông tin liên hệ, đúng Wikimedia User-Agent policy. Bản đầu có ghi email cá nhân; user quyết định bỏ email (2026-10-13) để không lộ email trong report/PDF/repo công khai.
  - Bảng Provenance ở mục 3.2 của cả bản EN và VI trích xuất trực tiếp chuỗi User-Agent này.
  - Test `test_user_agent_conforms_to_wikimedia_policy` đã xoá (chỉ kiểm chuỗi, không bắt được lỗi thật).
---

## D. Code / kỹ thuật

### D1 🟠 Không có test tự động
- **Bằng chứng:** repo không có file test nào. Các hàm `convert_yes_no`, `classify_risk`, `clean_pisa`, `_parse_pisa_html` mới chỉ được kiểm chứng bằng cách chạy pipeline.
- **Rủi ro:** sửa code sau này dễ phá logic mà không ai phát hiện, nhất là parser PISA và các ngưỡng.
- **Xử lý:** thêm `tests/` với pytest:
  - Test biên cho 4 hàm cơ bản (G3 = 9 / 10; absences = 3 / 4 / 9 / 10; yes/no lạ → None).
  - Test `classify_risk` không phụ thuộc G3.
  - Test `_parse_pisa_html` trên một đoạn HTML mẫu nhỏ.
- ✅ **Đã xử lý (2026-10-13):** thêm `tests/test_data_processor.py`, `tests/conftest.py` và `pytest.ini`. Thêm `pytest` vào venv và `requirements.txt`. Chạy bằng `.\.venv\Scripts\python -m pytest`: **42 passed**, không cần mạng. Các test bao gồm:
  - **Biên của 4 hàm cơ bản:** G3 = 9 / 9.99 / 10; absences = 3 / 4 / 9 / 10; yes/no lạ (kể cả rỗng, None) → None.
  - **`classify_risk`:** kết quả không đổi khi G3 = 0 / 9 / 10 / 20; thứ tự ưu tiên giữa các ngưỡng high/medium/low.
  - **`_holm`:** khớp giá trị tính tay, đảm bảo tính đơn điệu và chặn trên ở 1. **`_wilson`:** khoảng chứa giá trị ước lượng, và xử lý biên n = 0, k = n.
  - **`_parse_pisa_html`** trên HTML mẫu: map đúng môn theo thứ tự header, năm lấy từ heading, dòng OECD 2 ô, bảng comparison chuyển từ rộng sang dài, giữ nguyên `*` / `—`.
  - **`validate_pisa_raw`:** chấp nhận bảng đủ chuẩn; bắt được 6 kiểu hỏng (mất môn, mất năm, điểm ngoài miền, mất dòng OECD, quá ít nước, rank không phải số).
  - **`clean_pisa`:** chuẩn hoá tên nước, bỏ dòng `—`. **`cross_check_pisa`:** alias Korea → South Korea, phân biệt khớp tuyệt đối với ngưỡng ±1, bỏ qua giá trị `m`.
  - **`scrape_pisa_table`:** cache-first không gọi mạng; refresh gặp trang hỏng thì giữ nguyên cache (byte không đổi) và cảnh báo; không có cache thì báo `RuntimeError`.
  - **`clean_data`** trên 6 dòng thật đã chèn lỗi: đếm đúng age ngoài miền, yes/no lạ, dòng trùng, khoảng trắng; gắn cờ dropout; `grade_drop` không trùng với dropout.
  - **`_risk_holdout`:** holdout chặt loại đúng học sinh có mặt ở cả 2 môn.
  - *Cập nhật 2026-10-13:* giờ là **48 passed**. Thêm test cho `_paired_subjects`, gộp mức trượt "2+" (B6, B7), tách CSV theo môn (D5) và `tests/test_report_builder.py` (F3). Đã xoá 3 test chỉ kiểm chuỗi/file (User-Agent, CSV DevTools, docstring `avg_grade`).

### D2 🟠 `matplotlib.use("Agg")` đặt ở cấp module
- **Bằng chứng:** `data_processor.py` dòng 20. Trong notebook, `plt.show()` không hiển thị gì và còn báo warning "FigureCanvasAgg is non-interactive". Lúc build notebook t đã phải đổi sang `display(fig)`.
- **Rủi ro:** m tự viết thêm cell vẽ biểu đồ trong notebook sẽ không thấy hình.
- **Xử lý:** bỏ `matplotlib.use("Agg")`. Matplotlib tự chọn backend phù hợp, hoặc chỉ set Agg trong `main.py`.
- ✅ **Đã xử lý (2026-10-13):**
  - Bỏ `import matplotlib` và `matplotlib.use("Agg")` khỏi `data_processor.py`.
  - `main.py` set Agg trước khi import pipeline, vì chạy script chỉ cần ghi PNG. `tests/conftest.py` cũng set Agg.
  - Notebook đổi lại dùng `plt.show()` cho boxplot: chạy lại thì ra output `image/png`, không còn warning.

### D3 🟡 Notebook có tác dụng phụ (side effects)
- **Bằng chứng:** chạy notebook sẽ tải UCI nếu thiếu file và ghi đè `images/*.png` cùng `data/processed/*`. *(PISA giờ đã cache-first nên notebook không còn cào lại.)*
- **Rủi ro:** thấp hơn trước. Output chỉ đổi khi code hoặc dữ liệu thô đổi.
- **Xử lý:** notebook chỉ đọc output có sẵn nếu muốn hoàn toàn không có side effect.
- 🟡 **Một phần (2026-10-13):** chỉ sửa phần ghi chú ở cell 0 của `analysis.ipynb` cho đúng thực tế: chạy notebook sẽ ghi lại cùng các file như `main.py` (`data/processed/*`, `images/*.png`, `report.md`, `report_vi.md`), không gọi mạng khi đã có file thô và cache PISA.
  - Notebook **vẫn có tác dụng phụ** như cũ (vẫn ghi file). Chưa làm bản notebook chỉ đọc output có sẵn.
  - *(Câu "khớp byte với `main.py`" ghi ở lần trước chưa được kiểm chứng, đã bỏ.)*

### D4 🟡 `requirements.txt` chưa khớp với code thực tế
- **Bằng chứng:**
  - `lxml` có trong requirements nhưng code dùng `html.parser`, nên không cần.
  - `numpy` được import trực tiếp nhưng không khai báo (đang có nhờ cài kèm pandas).
  - Không pin version.
- **Xử lý:**
  - Bỏ `lxml` (hoặc chuyển sang dùng nó).
  - Thêm `numpy`.
  - ~~Thêm `scipy` nếu làm B1.~~ ✅ đã thêm khi làm B1.
  - Pin version bằng `pip freeze`, hoặc dùng `uv lock`.
- 🟡 **Một phần (2026-10-13):**
  - ✅ Đã bỏ `lxml>=4.9` (code dùng `html.parser`).
  - ✅ Đã thêm `numpy>=1.26`.
  - ⬜ **Chưa pin version** (vẫn dùng `>=`). Bản đang chạy trong `.venv`: numpy 2.5.3, pandas 3.0.6, matplotlib 3.11.2, scipy 1.18.1, requests 2.34.2, beautifulsoup4 4.15.0.

### D5 🟡 `cleaned_students.csv` đổi schema
- **Bằng chứng:** file trước có 395 dòng × 45 cột; giờ là **1044 dòng** (mat + por), thêm `subject`, `avg_g1g2` và 6 cột cờ. `summary.json` cũng chuyển số liệu vào `scopes.*`.
- **Rủi ro:** ai mở CSV mà không lọc `subject == "mat"` sẽ tính sai.
- **Xử lý:** đã ghi trong README. Có thể tách thành `cleaned_students_mat.csv` + `cleaned_students_por.csv` cho rõ ràng.
- ✅ **Đã xử lý (2026-10-13):**
  - `export_results()` giờ xuất song song:
    - `data/processed/cleaned_students.csv` (1044 dòng: toàn bộ học sinh cả 2 môn kèm cờ bất thường);
    - `data/processed/cleaned_students_mat.csv` (395 dòng: chỉ môn Toán, dùng ngay không cần lọc);
    - `data/processed/cleaned_students_por.csv` (649 dòng: chỉ môn Bồ Đào Nha).
  - Thêm unit test `test_export_results_writes_combined_and_separate_subject_csvs`.

### D6 🟡 Bắt `PermissionError` không đủ
- **Bằng chứng:** chỉ phần ghi CSV có try/except. Phần ghi `summary.json` thì không, và chart `savefig` cũng không. Ảnh PNG đang mở trong một số trình xem cũng có thể bị khoá.
- **Xử lý:** gom tất cả thao tác ghi file vào một chỗ xử lý lỗi chung.
- ✅ **Đã xử lý (2026-10-13):**
  - Trong `export_results()`: gom toàn bộ thao tác ghi các file CSV và `summary.json` vào khối `try ... except PermissionError`.
  - Thêm hàm hỗ trợ `_save_fig()` cho cả 4 biểu đồ: bắt `PermissionError` khi file ảnh PNG bị trình xem ảnh khoá, kèm thông báo hướng dẫn đóng file rõ ràng.

### D7 🟡 Cột `avg_grade` chứa G3
- **Bằng chứng:** vẫn còn cột `avg_grade` (G1 + G2 + G3)/3 cho đúng rubric "average grade". Đã có thêm `avg_g1g2`.
- **Rủi ro:** nếu ai dùng `avg_grade` để dự đoán G3 thì bị leakage.
- **Xử lý:** đã ghi trong docstring. Cân nhắc nhắc thêm trong report.
- ✅ **Đã xử lý (2026-10-13):**
  - Docstring hàm `calc_average_grade` ghi cảnh báo hoa rõ ràng: `WARNING: Contains the target G3. Descriptive only; NEVER use as a predictor for G3 to prevent target leakage. For early prediction, use avg_g1g2 instead`.
  - Thêm mô tả biến `avg_grade` và `avg_g1g2` vào từ điển `VAR_DESCRIPTIONS`.
  - Báo cáo mục 5 (cả EN và VI) ghi rõ cảnh báo tránh data leakage và hướng dẫn dùng `avg_g1g2`.
  - Test kiểm docstring `test_calc_average_grade_warns_against_prediction_leakage` đã xoá (chỉ kiểm chữ trong docstring, không bắt được lỗi thật).

### D8 🟡 Ngôn ngữ trong code lẫn lộn
- **Bằng chứng:** docstring và log bằng tiếng Anh, riêng thông báo `PermissionError` bằng tiếng Việt.
- **Xử lý:** thống nhất một ngôn ngữ.
- ✅ **Đã xử lý (2026-10-13):** 2 thông báo `PermissionError` (`export_results()` và `_save_fig()`) giờ chỉ bằng tiếng Anh. Không còn chữ tiếng Việt trong `data_processor.py`, `main.py`, `export_pdf.py`, `tests/` (đã grep). Tiếng Việt chỉ còn ở nội dung report tiếng Việt, đúng mục đích.

---

## E. Quy trình / tài liệu

### E1 🟡 Spec cũ ghi `resolved` nhưng vài acceptance không khớp từng chữ
- **Bằng chứng:** acceptance trong `p1-review-fixes/spec.md` ghi "`pisa_reference.csv`: không còn `*`, Rank/Score là số". Thực tế file raw giữ nguyên chuỗi gốc của trang (có `*`, `—`), còn bản sạch là `pisa_clean.csv`. Mục 7.2 bước 1 (DevTools) cũng chưa làm (C4).
- **Xử lý:** sửa lại câu acceptance cho đúng thiết kế raw/clean, và ghi rõ 7.2 bước 1 là chưa làm.
- ✅ **Đã xử lý (2026-10-13):** trong `.scratch/p1-review-fixes/spec.md`, câu acceptance về PISA đã sửa theo thiết kế raw/clean (raw giữ chuỗi gốc, `pisa_clean.csv` là số), và mục 7.2 bước 1 ghi rõ là không làm (C4).

### E2 🟡 Không có ADR cho các quyết định lớn
- **Bằng chứng:** `docs/adr/` không tồn tại. Các quyết định như "flag thay vì xoá G3 = 0", "por chỉ để so sánh", "rule rủi ro không dùng G3" mới chỉ ghi trong spec và `CONTEXT.md`.
- **Xử lý:** viết 2–3 ADR ngắn nếu muốn đúng quy ước repo (`docs/agents/domain.md`).
- ✅ **Đã xử lý (2026-10-13):** thêm `docs/adr/0001-flag-dropout-suspects-not-delete.md`, `0002-risk-group-never-uses-g3.md`, `0003-por-for-comparison-and-holdout-only.md`, dùng từ vựng của `CONTEXT.md`.


---

## F. Phát hiện thêm sau audit + pull (2026-10-13)

### F1 🟠 Slide `presentation/talk.pptx` dùng số liệu cũ
- **Bằng chứng:** slide được pull về từ commit `f2d6d02`, làm từ report cũ:
  - Slide 4 ghi r(G2, G3) = 0.905, là số trên toàn bộ học sinh. Bỏ nhóm G3 = 0 thì là 0.966.
  - Slide 6 dùng nhóm rủi ro kiểu cũ (dính G3) và ghi "chưa test holdout".
  - Slide 7 liệt kê các việc đã làm xong như những bước tiếp theo.
  - Thiếu hẳn: nhóm bỏ thi, kiểm định, hồi quy, đối chiếu OECD.
- **Rủi ro:** thuyết trình bằng slide này sẽ mâu thuẫn với report và PDF.
- **Xử lý:** cập nhật slide theo `summary.json` mới, sau khi thống nhất với Stratoze.
- ⏭️ **Không sửa trong code (2026-10-13):** user sẽ tự làm lại slide.

### F2 🟡 Report chưa nói ý "lần trượt đầu tiên tụt nhiều nhất"
- **Bằng chứng:** đây là ý của commit `97693c0` (Stratoze). Số liệu mới (exclude_dropout) vẫn đúng như vậy: 0→1 lần trượt: −1.79, 1→2: −1.32, 2→3: −0.56. Nhưng `report_builder.py` chưa có câu nào nói ý này.
- **Xử lý:** thêm 1 câu diễn giải tự tính vào mục 7 (EN/VI).
- ✅ **Đã xử lý (2026-10-13):**
  - `_fail_steps()` tính mức thay đổi G3 trung bình giữa 2 mức trượt liền nhau. `_fail_steps_text()` sinh câu EN/VI ngay dưới bảng "theo số lần trượt" ở mục 7.
  - Câu sinh ra: "0→1: −1.79, 1→2: −1.32, 2→3: −0.56. **Lần trượt đầu tiên** đi kèm mức tụt điểm lớn nhất…", kèm lưu ý nhóm 2 (n = 12) và 3 (n = 11) ít học sinh.
  - Câu "lần đầu tụt nhiều nhất" chỉ hiện khi số liệu thật sự đúng như vậy; nếu dữ liệu đổi thì câu tự đổi theo.

### F3 🟡 `build_reports` crash khi thiếu file OECD
- **Bằng chứng:** chạy pipeline không có `oecd_raw` thì `build_reports` báo `TypeError: 'NoneType' object is not iterable`. Không có test cho `report_builder.py`.
- **Rủi ro:** thấp, vì file OECD giờ đã nằm trong repo.
- **Xử lý:** khi thiếu file thì báo lỗi rõ ràng, hoặc bỏ qua mục 3.4; thêm 1 test.
- ✅ **Đã xử lý (2026-10-13):**
  - `build_reports()` kiểm tra `pisa_context` và `pisa_oecd_check` trước khi sinh report. Thiếu thì báo `ValueError` ghi rõ tên file bị thiếu (`pisa_reference.csv` / `oecd_pisa2025_table_I1.csv`) và không ghi file report nào.
  - Chọn báo lỗi thay vì bỏ qua mục 3.4, vì report có nhiều chỗ trích kết quả đối chiếu OECD.
  - Thêm `tests/test_report_builder.py`: thiếu file OECD thì có lỗi nêu tên file và thư mục output vẫn rỗng.

### F4 🟡 G1 và G2 tương quan cao trong mô hình B
- **Bằng chứng:** r(G1, G2) = 0.90. Hệ số riêng của G1 và G2 trong mô hình hồi quy B kém ổn định, nhưng report chưa nhắc.
- **Xử lý:** thêm 1 câu ở mục 7.2: chỉ diễn giải R² và tổng tác động của 2 điểm giữa kỳ, không so sánh b(G1) với b(G2).
- ✅ **Đã xử lý (2026-10-13):** thêm 1 dòng vào phần diễn giải mục 7.2 (EN/VI). r(G1, G2) = 0.902 lấy tự động từ `corr_G1_G2_G3` của scope exclude_dropout, đúng mẫu mà hồi quy dùng (G3 > 0).

### F5 🟡 PDF có thể lệch với `.md`
- **Bằng chứng:** chạy `main.py` hoặc notebook đều ghi đè `report.md` / `report_vi.md`, nhưng không tự chạy `export_pdf.py`.
- **Xử lý:** nhớ chạy `export_pdf.py` trước khi nộp, hoặc cho `main.py` gọi luôn bước xuất PDF nếu máy có Chrome/Edge.
- ⏭️ **Không sửa code (2026-10-13, user quyết định):** chạy `python export_pdf.py` sau `main.py` hoặc notebook là đủ.

---

## Ưu tiên gợi ý trước khi nộp

1. ~~**A2:** số liệu trong report bị gõ tay~~ → ✅ report được sinh tự động.
2. ~~**C1:** PISA cache-first~~ → ✅ đã làm.
3. ~~**B1 + B4:** t-test/ANOVA và đánh giá rule trên `por`~~ → ✅ đã làm. Lưu ý: kết luận về internet đã đổi (không còn ý nghĩa sau hiệu chỉnh Holm).
4. ~~**C2:** đối chiếu số PISA 2025 với OECD~~ → ✅ khớp 274/274.
5. ~~**A1:**~~ → ✅ có bản tóm tắt 2 trang (`report_summary*.pdf`) và bản đầy đủ; nên hỏi giảng viên muốn nộp bản nào.
6. ~~**B6, B7, C6, D5–D8, E1, E2, F2–F4**~~ → ✅ đã làm. C4 bỏ theo quyết định của user.
7. Không làm (user quyết định): pin version (D4), notebook chỉ đọc output (D3).
