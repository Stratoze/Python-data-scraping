# Bộ Câu hỏi & Trả lời Vấn đáp Dự án P1 (Student Performance & PISA)

Tài liệu ôn tập vấn đáp, bảo vệ đồ án và thuyết trình. Tài liệu tổng quan chính: [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md); chi tiết công thức thống kê: [`METHODS.md`](METHODS.md). Được cấu trúc theo dạng:
- **Trả lời nhanh (30 giây):** Dùng để trả lời dứt khoát, đúng trọng tâm khi thầy cô hỏi trực tiếp.
- **Giải thích sâu & Bằng chứng:** Dùng khi thầy cô hỏi vặn thêm (dẫn đúng số liệu, file code, dòng code).

Mọi số liệu lấy từ `data/processed/summary.json` sau khi chạy `python main.py`; số dòng code theo `data_processor.py` hiện tại (832 dòng).

---

## Mục lục
1. [Tổng quan dự án & Bài toán](#1-tổng-quan-dự-án--bài-toán)
2. [Bộ dữ liệu học sinh UCI & Tiền xử lý (Data Cleaning)](#2-bộ-dữ-liệu-học-sinh-uci--tiền-xử-lý-data-cleaning)
3. [Hiện tượng điểm 0 (G3 = 0) & 6 Cờ bất thường (Anomaly Flags)](#3-hiện-tượng-điểm-0-g3--0--6-cờ-bất-thường-anomaly-flags)
4. [Ý nghĩa 3 Biểu đồ & Kết luận thống kê cốt lõi](#4-ý-nghĩa-3-biểu-đồ--kết-luận-thống-kê-cốt-lõi)
5. [Quy tắc cảnh báo sớm rủi ro (Early Warning Risk Rule)](#5-quy-tắc-cảnh-báo-sớm-rủi-ro-early-warning-risk-rule)
6. [Các kiểm định thống kê được dùng](#6-các-kiểm-định-thống-kê-được-dùng)
7. [Cào dữ liệu PISA Wikipedia & Đối chiếu OECD (Web Scraping)](#7-cào-dữ-liệu-pisa-wikipedia--đối-chiếu-oecd-web-scraping)
8. [Kiến trúc Mã nguồn & Báo cáo](#8-kiến-trúc-mã-nguồn--báo-cáo)
9. [Bảng tóm tắt các con số cốt lõi](#9-bảng-tóm-tắt-các-con-số-cốt-lõi-học-thuộc-trước-khi-vào-phòng-thi)

---

## 1. Tổng quan dự án & Bài toán

### Q1.1: Đề tài này giải quyết bài toán gì trong thực tế?
- **Trả lời nhanh:** Dự án phân tích các yếu tố liên quan đến điểm cuối kỳ (G3) của học sinh THPT Bồ Đào Nha môn Toán, xây dựng quy tắc cảnh báo sớm học sinh có nguy cơ trượt ngay từ giữa kỳ (chỉ nhìn G1, G2, vắng học và số lần trượt cũ), đồng thời cào dữ liệu PISA từ Wikipedia để đặt học sinh vào bối cảnh quốc gia.
- **Giải thích sâu:** Dự án chia làm 2 cấp độ:
  - *Cấp vi mô (học sinh):* Điểm giữa kỳ G2 và lịch sử trượt môn gắn với G3 mạnh hơn hẳn các yếu tố như internet hay thời gian tự học.
  - *Cấp vĩ mô (quốc gia):* Điểm PISA cho thấy thời điểm khảo sát UCI (2005–2006), Bồ Đào Nha thấp hơn trung bình OECD môn Toán (2006: 466 so với 494), trước khi bắt kịp vào năm 2015 (492 so với 490).

### Q1.2: Tại sao chọn môn Toán (`mat`) làm môn phân tích chính mà không phải môn Tiếng Bồ Đào Nha (`por`)?
- **Trả lời nhanh:** Môn Toán có tỉ lệ trượt cao hơn (Toán trượt 32.9%, Tiếng Bồ Đào Nha chỉ trượt 15.4%) nên phân loại đỗ/trượt có ý nghĩa hơn. Môn `por` được giữ làm **tập kiểm chứng ngoài mẫu (holdout)** cho quy tắc rủi ro.
- **Bằng chứng:** `_risk_holdout()` trong `data_processor.py`, dòng 678–694.

### Q1.3: G1, G2, G3 là gì? Thang điểm chấm thế nào? Điểm qua môn là bao nhiêu?
- **Trả lời nhanh:** Thang điểm 0–20 theo hệ thống giáo dục Bồ Đào Nha:
  - `G1`: Điểm kỳ 1 (First Period).
  - `G2`: Điểm kỳ 2 / giữa kỳ (Second Period).
  - `G3`: Điểm tổng kết cuối kỳ (Final Grade) — đây là **biến mục tiêu (Target)**.
  - Điểm qua môn: $G3 \ge 10$ là **Đỗ (Pass)**, $G3 < 10$ là **Trượt (Fail)**.

---

## 2. Bộ dữ liệu học sinh UCI & Tiền xử lý (Data Cleaning)

### Q2.1: Làm sạch dữ liệu gồm những bước nào? Log ra sao?
- **Trả lời nhanh:** Hàm `clean_data()` thực hiện 6 bước:
  1. Cắt khoảng trắng thừa (`strip`) trên toàn bộ cột chuỗi.
  2. Ép kiểu số và kiểm tra miền giá trị hợp lệ theo định nghĩa UCI (`VALID_RANGES`).
  3. Mã hoá nhị phân các cột `yes`/`no` thành `1`/`0`.
  4. Xoá dòng trùng lặp (`drop_duplicates`) và bỏ dòng thiếu cột bắt buộc (`REQUIRED_COLS`).
  5. Tạo các cột dẫn xuất (`pass_fail`, `absence_level`, `avg_grade`, `avg_g1g2`, `risk_group`).
  6. Gắn 6 cờ bất thường (anomaly flags), ngưỡng vắng học bất thường tính bằng IQR riêng cho từng môn.
- **Log:** Mỗi bước đếm số ô/dòng bị xử lý và ghi vào `cleaning_log` trong `summary.json`. Lần chạy thực tế: 1044 dòng vào (mat 395, por 649), 0 ô bị strip, 0 giá trị không phải số, 0 ngoài miền, 0 yes/no sai, 0 dòng trùng, 0 dòng thiếu → 1044 dòng ra. Ngưỡng IQR vắng học: mat 20, por 15. Dữ liệu UCI vốn sạch, nhưng các bước này được kiểm thử bằng dữ liệu cấy lỗi trong `tests/`.
- **Vị trí code:** `data_processor.py`, dòng 573–636.

### Q2.2: Cột `avg_grade` được tính như thế nào và tại sao không được dùng để dự báo?
- **Trả lời nhanh:** `avg_grade = (G1 + G2 + G3) / 3`. Cột này **không được đưa vào quy tắc cảnh báo nào** vì nó chứa biến mục tiêu $G3$ — dùng sẽ gây **rò rỉ dữ liệu (Data Leakage)**. Cột này chỉ dùng cho thống kê mô tả.
- **Bằng chứng:** Docstring của `calc_average_grade` (`data_processor.py`, dòng 133–139) và `VAR_DESCRIPTIONS` (dòng 63–76).

### Q2.3: 2 file `student-mat.csv` và `student-por.csv` có độc lập không? Holdout chặt là gì?
- **Trả lời nhanh:** Không hoàn toàn độc lập: nhiều học sinh học cả 2 môn. Vì vậy ngoài holdout trên toàn bộ 649 học sinh `por`, code còn tạo **holdout chặt**: chỉ giữ học sinh `por` **không** xuất hiện trong file `mat` (so khớp theo các thuộc tính định danh `MERGE_KEYS`, dòng 53–54), còn lại 275 em.
- **Bằng chứng:** `_risk_holdout()`, `data_processor.py` dòng 678–694.

---

## 3. Hiện tượng điểm 0 (G3 = 0) & 6 Cờ bất thường (Anomaly Flags)

### Q3.1: Hiện tượng 38 học sinh bị điểm 0 ($G3 = 0$) môn Toán là gì? Tại sao không xoá đi?
- **Trả lời nhanh:** Trong 395 học sinh môn Toán có 38 em $G3 = 0$. Cả 38 em đều có **`absences = 0`** (trong khi chỉ 21.6% học sinh còn lại có `absences = 0`), 13 em cũng có $G2 = 0$, G1 trung bình vẫn đạt 7.53. Đây là nhóm **nghi bỏ thi / thôi học (Dropout Suspects)**, không phải đi thi được 0 điểm. Không xoá; nhóm này được **gắn cờ `dropout_suspect = True`**.
- **Tại sao không xoá:**
  1. Giữ toàn vẹn dữ liệu gốc.
  2. Bỏ thi là hiện tượng có thật, cần đếm được (38 em = 9.6%).
  3. Các kết luận về yếu tố liên quan đến điểm (tương quan, t-test, ANOVA) tính trên tập **loại nhóm bỏ thi (`exclude_dropout`, 357 em)**. Ví dụ: tỉ lệ đỗ 67.1% (tất cả) → 74.2% (loại bỏ thi); $r(\text{absences}, G3)$ đổi từ $+0.034$ thành $-0.213$.
- **Bằng chứng:** `docs/adr/0001-flag-dropout-suspects-not-delete.md`.

### Q3.2: 6 cờ dữ liệu bất thường (Anomaly Flags) là những cờ nào?
- **Trả lời nhanh:** (số lượng môn Toán / môn Bồ Đào Nha)
  1. `dropout_suspect`: $G3 = 0$ (nghi bỏ thi) — 38 / 15.
  2. `g2_zero`: $G2 = 0$ (nghi vắng thi kỳ 2) — 13 / 7.
  3. `grade_drop`: Tụt điểm đột ngột ($G1 - G3 \ge 8$ hoặc $G2 - G3 \ge 6$) — 0 / 1.
  4. `absence_outlier`: Vắng vượt ngưỡng IQR $Q3 + 1.5 \times IQR$ (Toán $> 20$ buổi) — 15 / 21.
  5. `age_outlier`: $\ge 20$ tuổi — 5 / 9.
  6. `inconsistent_grade`: $G3 > 0$ nhưng $G2 = 0$ — 0 / 0.

---

## 4. Ý nghĩa 3 Biểu đồ & Kết luận thống kê cốt lõi

### Q4.1: Biểu đồ 1 (`01_bar_studytime_internet.png`) cho thấy điều gì? Tại sao cột có internet cao hơn nhưng lại kết luận "không có ý nghĩa thống kê"?
- **Trả lời nhanh:**
  - Nhóm có internet có G3 trung bình 11.68 (n = 299) so với 10.71 (n = 58), chênh $+0.98$, 95% CI $[0.11, 1.84]$, Welch $p = 0.0268$.
  - Nhưng dự án chạy 4 t-test cùng lúc nên phải hiệu chỉnh Holm: $p_{holm} = 0.0804 > 0.05$ → **không đủ bằng chứng để khẳng định internet gắn với điểm Toán cao hơn**.
  - Tự học (`studytime`): trung bình mức 1/2/3/4 = 11.47/11.07/12.56/12.67; ANOVA có ý nghĩa ($p_{holm} = 0.0193$) nhưng hiệu ứng nhỏ ($\eta^2 = 0.036$).
- **Về các cột gạch chéo:** Cột có $n < 10$ (vd tự học >10h không có internet chỉ có $n = 3$) được vẽ **gạch chéo và làm mờ** để cảnh báo mẫu quá nhỏ.
- **Vị trí code:** `_plot_bar` trong `data_processor.py`, dòng 731–765.

### Q4.2: Biểu đồ 2 (`02_hist_g3.png`) chứng minh điều gì về phân phối?
- **Trả lời nhanh:**
  1. Điểm của học sinh thi thật ($G3 > 0$) có dạng gần hình chuông, tập trung quanh 10–11.
  2. Khoảng điểm 1–3 gần như trống, rồi vọt lên 38 em ở mốc 0 (cột đỏ tách biệt) → bằng chứng trực quan điểm 0 là do **bỏ thi**, không phải năng lực.
- **Vị trí code:** `_plot_hist`, dòng 767–788.

### Q4.3: Biểu đồ 3 (`03_heatmap_corr.png`) chỉ ra biến nào gắn với G3 mạnh nhất?
- **Trả lời nhanh:** (tập `exclude_dropout`)
  - **Mạnh nhất:** $G2$ ($r = +0.966$) và $G1$ ($r = +0.892$).
  - **Kéo điểm xuống:** `failures` ($r = -0.294$, $p = 1.5 \times 10^{-8}$) và `absences` ($r = -0.213$, $p = 4.9 \times 10^{-5}$).
  - **Yếu:** `famsup` ($r = -0.067$, $p = 0.205$, không ý nghĩa); `studytime` ($r = +0.127$, $p = 0.0166$).
- **Lưu ý:** Tương quan không phải nhân quả. Vd `schoolsup` gắn với điểm thấp hơn ($-2.21$ điểm) vì trường hỗ trợ chính những em yếu (nhân quả ngược).
- **Vị trí code:** `_plot_heatmap`, dòng 790–808; `_corr_tests`, dòng 480–488.

### Q4.4: Dữ liệu PISA được dùng trong phân tích như thế nào?
- **Trả lời nhanh:** Hàm `_pisa_context()` (dòng 696–711) lấy điểm Bồ Đào Nha và trung bình OECD qua các năm, ghi vào `summary.json` (`pisa_context`). Môn Toán: 2006 466/494, 2015 492/490, 2025 460/463. Đây là **bối cảnh cấp quốc gia**, không ghép vào từng học sinh UCI. Bản này không còn biểu đồ PISA riêng; số liệu được trình bày dạng bảng trong báo cáo.

---

## 5. Quy tắc cảnh báo sớm rủi ro (Early Warning Risk Rule)

### Q5.1: Hàm `classify_risk` hoạt động như thế nào?
- **Trả lời nhanh:** Chia học sinh làm 3 nhóm:
  - **High:** $G2 < 10$ HOẶC `failures >= 2`.
  - **Medium:** $G1 < 10$ HOẶC `failures == 1` HOẶC `absences >= 10`.
  - **Low:** Còn lại.
- **Vị trí code:** `data_processor.py`, dòng 142–156.

### Q5.2: Tại sao `classify_risk` tuyệt đối không dùng G3?
- **Trả lời nhanh:** Đây là **cảnh báo sớm**, phải chạy từ giữa kỳ để giáo viên kịp phụ đạo. Lúc đó chưa có G3. Dùng G3 vừa vô nghĩa thực tế vừa rò rỉ dữ liệu. Có test kiểm tra: đổi G3 thì kết quả `classify_risk` không đổi.
- **Bằng chứng:** `docs/adr/0002-risk-group-never-uses-g3.md`.

### Q5.3: Hiệu quả của rule được đánh giá qua những chỉ số nào? Kết quả ra sao?
- **Trả lời nhanh:** Coi nhóm `high` là "báo động", so với trượt thật ($G3 < 10$):
  - **Recall** = trong số em trượt thật, bao nhiêu % bị báo động.
  - **Precision** = trong số em bị báo động, bao nhiêu % trượt thật.

| Tập | n | Recall | Precision |
|---|---|---|---|
| Toán, tất cả | 395 | 93.8% (122/130) | 81.9% (122/149) |
| Toán, loại bỏ thi | 357 | 93.5% | 76.1% |
| Holdout `por` (toàn bộ) | 649 | 90.0% | 59.2% |
| Holdout chặt `por` | 275 | 91.4% (64/70) | 66.0% (64/97) |

- Recall trên 90% ở cả tập ngoài mẫu → rule ít bỏ sót em có nguy cơ. Precision giảm trên `por` vì môn này tỉ lệ trượt thấp hơn.
- **Vị trí code:** `_risk_eval`, dòng 519–535; `_risk_holdout`, dòng 678–694.

### Q5.4: Tại sao phân tầng 3 mức (Low, Medium, High) mà không chia đôi?
- **Trả lời nhanh:** Nguồn lực phụ đạo có hạn, nên cần thứ tự ưu tiên. Tỉ lệ trượt thật theo nhóm:

| Nhóm | Toán (tất cả) | Holdout chặt `por` |
|---|---|---|
| High | 81.9% | 66.0% |
| Medium | 7.8% | 9.8% |
| Low | 1.2% | 0.8% |

- High → can thiệp ngay; Medium → theo dõi, nhắc nhở; Low → an toàn. Nếu gộp High + Medium làm báo động (Toán, tất cả): recall 98.5% nhưng precision chỉ 56.6%.
- 36/38 em nghi bỏ thi nằm trong nhóm High, 2 em Medium, 0 em Low.

---

## 6. Các kiểm định thống kê được dùng

### Q6.1: Dự án dùng những kiểm định nào?
- **Trả lời nhanh:** Ngưỡng $\alpha = 0.05$ (`ALPHA`, dòng 43). Tất cả chạy trên tập `exclude_dropout`:
  - **Welch t-test** + 95% CI của chênh lệch trung bình cho 4 biến nhị phân (`internet`, `famsup`, `schoolsup`, `paid`).
  - **ANOVA một chiều** + $\eta^2$ cho 3 biến nhiều mức (`studytime`, `absence_level`, `failures` gộp 0/1/2+).
  - **Hiệu chỉnh Holm** cho từng họ kiểm định.
  - **Kiểm định tương quan Pearson** ($r$, $p$, 95% CI) cho G1, G2, studytime, failures, absences, famsup với G3.
- **Vị trí code:** `_p` 427–429, `_holm` 432–438, `_group_tests` 441–477, `_corr_tests` 480–488.

### Q6.2: Kết quả các kiểm định nhóm là gì?

| Biến | Kiểm định | Kết quả | $p_{holm}$ | Kết luận |
|---|---|---|---|---|
| internet | Welch | 11.68 vs 10.71 | 0.0804 | Không ý nghĩa |
| famsup | Welch | 11.35 vs 11.80 | 0.404 | Không |
| schoolsup | Welch | 9.62 vs 11.83 | $3.4 \times 10^{-6}$ | Có (nhân quả ngược) |
| paid | Welch | 11.43 vs 11.61 | 0.585 | Không |
| studytime | ANOVA | $F = 4.38$, $\eta^2 = 0.036$ | 0.0193 | Có, hiệu ứng nhỏ |
| absence_level | ANOVA | $F = 9.85$, $\eta^2 = 0.053$ | 0.00034 | Có |
| failures | ANOVA | $F = 17.19$, $\eta^2 = 0.089$ | $5.3 \times 10^{-7}$ | Có, mạnh nhất |

### Q6.3: Đa kiểm định là gì và tại sao dùng hiệu chỉnh Holm?
- **Trả lời nhanh:** Chạy $k$ kiểm định cùng lúc ở $\alpha = 0.05$ thì xác suất có ít nhất một dương tính giả tăng lên $1 - (1 - \alpha)^k$. **Holm** sắp $p$-value tăng dần, nhân $p_{(i)}$ với $(k - i + 1)$ và giữ tính đơn điệu, kiểm soát sai số cho cả họ mà ít khắt khe hơn Bonferroni. Ví dụ internet: $p = 0.0268$ nhưng $p_{holm} = 0.0804$.
- **Vị trí code:** `_holm()`, dòng 432–438.

### Q6.4: Vì sao bản này bỏ hồi quy OLS?
- **Trả lời nhanh:** Đề bài P1 yêu cầu phân tích mô tả, kiểm định và cảnh báo sớm — không yêu cầu mô hình dự báo. Hồi quy OLS tự viết (cùng HC3, Kruskal-Wallis, Wilson CI, Fisher, phân tích độ nhạy, so sánh ghép cặp 2 môn) làm code phình gấp ~3 lần và khó giải thích khi vấn đáp, trong khi các câu hỏi chính đã được trả lời bằng tương quan, t-test, ANOVA và đánh giá rule. Branch `slim-down` cắt bỏ các phần này: code (không tính test) giảm từ ~2817 xuống 904 dòng.
- **Nếu bị hỏi "biến nào quan trọng nhất?":** Trả lời bằng tương quan ($G2$ $r = 0.966$) và $\eta^2$ của ANOVA (`failures` 0.089 > `absence_level` 0.053 > `studytime` 0.036), không cần hệ số hồi quy.

---

## 7. Cào dữ liệu PISA Wikipedia & Đối chiếu OECD (Web Scraping)

### Q7.1: Luồng cào dữ liệu PISA hoạt động như thế nào?
- **Trả lời nhanh:** Cơ chế **cache-first**:
  1. Mặc định đọc cache `data/raw/pisa_reference.csv` và chạy `validate_pisa_raw()`. Không gọi mạng vô cớ.
  2. Khi chạy `python main.py --refresh-pisa` hoặc thiếu cache: gửi 1 HTTP GET bằng `requests` kèm `User-Agent` (`HTTP_HEADERS`).
  3. `BeautifulSoup` bóc tách bảng tóm tắt 2025 và xoay bảng lịch sử 2000–2022 từ dạng rộng sang dạng dài.
  4. `validate_pisa_raw()` kiểm tra 6 tiêu chí. Hợp lệ mới ghi đè cache và `pisa_reference.meta.json` (URL, `revision_id`, permalink, thời gian cào).
  5. Lỗi mạng/parse: fallback về cache cũ, phát `warnings.warn`, không làm sập chương trình.
- **Lần cào hiện tại:** revision 1378067005, 2026-10-13 06:44 UTC, 2342 dòng thô (274 tóm tắt 2025 + 2068 so sánh) → 1662 dòng sạch.
- **Vị trí code:** `_parse_pisa_html` 197–251, `validate_pisa_raw` 258–290, `scrape_pisa_table` 309–347, `clean_pisa` 350–366.

### Q7.2: Parser nhận diện các bảng trên trang Wikipedia như thế nào?
- **Trả lời nhanh:** Dựa trên **cấu trúc nội dung**, không dựa vào thứ tự bảng:
  - Bảng 2025: tiêu đề chứa 3 môn (`mathematics`, `science`, `reading`) và có đúng 3 bảng con lồng nhau.
  - Bảng so sánh 2000–2022: hàng đầu là tên môn, hàng 2 bắt đầu bằng `Country` rồi các năm; các cặp (năm, điểm, hạng) được chuyển sang dạng dài.
  - Wikipedia thêm/bớt bảng khác thì code vẫn tìm đúng bảng.

### Q7.3: `validate_pisa_raw` kiểm tra những gì?
- **Trả lời nhanh:** 6 điều kiện:
  1. Đủ 3 môn cho cả bảng tóm tắt và bảng so sánh.
  2. Năm là số từ 2000 đến năm hiện tại.
  3. Điểm trong khoảng 200–700.
  4. Mỗi năm / môn có ít nhất 30 quốc gia.
  5. Không quốc gia nào lặp trong cùng một kỳ.
  6. Có đúng 1 dòng `OECD average`.

### Q7.4: Làm sao chứng minh dữ liệu PISA cào từ Wikipedia là đáng tin?
- **Trả lời nhanh:** `cross_check_pisa()` (dòng 369–410) đối chiếu với **Table I.1, *PISA 2025 Results (Volume I)*** của OECD (file `data/raw/` kèm nguồn):
  - 2025: so trực tiếp → **274/274 khớp tuyệt đối**.
  - 2022: OECD chỉ cho `điểm 2025 − mức thay đổi`, làm tròn nên cho phép sai $\pm 1$ → **208/211 trong sai số**; 3 dòng lệch đều là Palestinian Authority.
- **Bằng chứng:** `pisa_oecd_check` trong `summary.json`.

---

## 8. Kiến trúc Mã nguồn & Báo cáo

### Q8.1: Kiến trúc mã nguồn được phân chia như thế nào?
- **Trả lời nhanh:** 2 file code (904 dòng, không tính test):
  1. `main.py` (72 dòng): entry point, đặt backend `Agg`, nhận cờ `--refresh-pisa`, chạy pipeline và xuất kết quả.
  2. `data_processor.py` (832 dòng): cấu hình ngưỡng, hàm thuần (`classify_risk`, `calc_pass_fail`...), cào/kiểm tra PISA, class `StudentDataProcessor` (load → clean → analyze → vẽ 3 biểu đồ → export).
- **Đầu ra:** `data/processed/cleaned_students.csv`, CSV riêng từng môn, `summary.json`, 3 ảnh trong `images/`.

### Q8.2: Báo cáo được viết thế nào?
- **Trả lời nhanh:** `report.md` (tiếng Anh) và `report_vi.md` (tiếng Việt) là **báo cáo viết tay 1–2 trang**, đúng yêu cầu đề bài. Mọi số trong báo cáo lấy từ `summary.json` của lần chạy `main.py`; nếu dữ liệu đổi, chạy lại `main.py` rồi cập nhật số trong báo cáo. Giải thích chi tiết code nằm ở `PROJECT_GUIDE.md`, công thức thống kê ở `METHODS.md`.

### Q8.3: Dự án có bao nhiêu unit test? Test những gì?
- **Trả lời nhanh:** **43 test** `pytest` trong `tests/test_data_processor.py` (100% pass):
  - Biên đỗ/trượt (9.0, 9.99, 10.0), biên vắng học (3, 4, 9, 10).
  - Rule rủi ro không phụ thuộc G3 (chống rò rỉ).
  - Parser PISA, các ca lỗi của validation, cache-first không gọi mạng.
  - Làm sạch dữ liệu với các dòng cấy lỗi.
  - Holdout chặt.
  - Xuất CSV riêng cho `mat` và `por`.
  - Báo lỗi rõ tên file khi thiếu dữ liệu OECD.

---

## 9. Bảng tóm tắt các con số cốt lõi (Học thuộc trước khi vào phòng thi)

| Chỉ số | Con số thực tế | Ý nghĩa |
|---|---|---|
| **Số học sinh** | 1044 (mat 395, por 649) | Sau làm sạch không mất dòng nào |
| **Học sinh nghi bỏ thi môn Toán ($G3 = 0$)** | 38 em (9.6%) | Gắn cờ `dropout_suspect`, đều có `absences = 0` |
| **Tỉ lệ đỗ môn Toán** | 67.1% (tất cả) $\rightarrow$ **74.2%** (loại bỏ thi) | Mốc đỗ $G3 \ge 10$ |
| **Tỉ lệ đỗ môn Bồ Đào Nha** | 84.6% (tất cả) $\rightarrow$ 86.6% (loại bỏ thi) | Môn ngôn ngữ dễ đỗ hơn |
| **Tương quan G2 với G3** | $r = +0.966$ | Gắn với điểm cuối kỳ mạnh nhất |
| **Tương quan vắng học với G3** | $+0.034$ (tất cả) $\rightarrow$ $-0.213$ (loại bỏ thi) | Nhóm bỏ thi làm méo tương quan |
| **Tương quan trượt cũ với G3** | $r = -0.294$ | Yếu tố quá khứ kéo điểm mạnh nhất |
| **Internet** | 11.68 vs 10.71, $p_{holm} = 0.0804$ | **Không có ý nghĩa** sau Holm |
| **ANOVA failures** | $\eta^2 = 0.089$ | Hiệu ứng lớn nhất trong 3 biến nhiều mức |
| **Rule rủi ro (Toán)** | Recall 93.8%, Precision 81.9% | Bắt gần hết em sẽ trượt |
| **Rule rủi ro (holdout chặt, 275 em)** | Recall 91.4%, Precision 66.0% | Kiểm chứng ngoài mẫu |
| **Tỉ lệ trượt theo nhóm (Toán)** | High 81.9% / Medium 7.8% / Low 1.2% | Phân tầng có ý nghĩa |
| **Đối chiếu PISA 2025 với OECD** | **274/274 khớp** | Dữ liệu cào chính xác |
| **Số unit test** | **43/43 passed** | |
