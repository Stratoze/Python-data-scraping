# Bộ Câu hỏi & Trả lời Vấn đáp Dự án P1 (Student Performance & PISA)

Tài liệu ôn tập vấn đáp, bảo vệ đồ án và thuyết trình. Được cấu trúc theo dạng:
- **Trả lời nhanh (30 giây):** Dùng để trả lời dứt khoát, đúng trọng tâm khi thầy cô hỏi trực tiếp.
- **Giải thích sâu & Bằng chứng:** Dùng khi thầy cô hỏi vặn thêm (dẫn đúng số liệu, file code, dòng code).

---

## Mục lục
1. [Tổng quan dự án & Bài toán](#1-tổng-quan-dự-án--bài-toán)
2. [Bộ dữ liệu học sinh UCI & Tiền xử lý (Data Cleaning)](#2-bộ-dữ-liệu-học-sinh-uci--tiền-xử-lý-data-cleaning)
3. [Hiện tượng điểm 0 (G3 = 0) & 6 Cờ bất thường (Anomaly Flags)](#3-hiện-tượng-điểm-0-g3--0--6-cờ-bất-thường-anomaly-flags)
4. [Ý nghĩa 4 Biểu đồ & Kết luận thống kê cốt lõi](#4-ý-nghĩa-4-biểu-đồ--kết-luận-thống-kê-cốt-lõi)
5. [Quy tắc cảnh báo sớm rủi ro (Early Warning Risk Rule)](#5-quy-tắc-cảnh-báo-sớm-rủi-ro-early-warning-risk-rule)
6. [Mô hình Hồi quy Tuyến tính OLS & Kiểm định Nâng cao](#6-mô-hình-hồi-quy-tuyến-tính-ols--kiểm-định-nâng-cao)
7. [Cào dữ liệu PISA Wikipedia & Đối chiếu OECD (Web Scraping)](#7-cào-dữ-liệu-pisa-wikipedia--đối-chiếu-oecd-web-scraping)
8. [Kiến trúc Mã nguồn & Quy trình Xuất Báo cáo tự động](#8-kiến-trúc-mã-nguồn--quy-trình-xuất-báo-cáo-tự-động)

---

## 1. Tổng quan dự án & Bài toán

### Q1.1: Đề tài này giải quyết bài toán gì trong thực tế?
- **Trả lời nhanh:** Dự án phân tích các yếu tố ảnh hưởng đến kết quả thi cuối kỳ (G3) của học sinh THPT Bồ Đào Nha môn Toán, xây dựng hệ thống quy tắc cảnh báo sớm học sinh có nguy cơ trượt môn ngay từ giữa kỳ (chỉ nhìn G1, G2, vắng học và trượt cũ), đồng thời cào dữ liệu PISA quốc tế từ Wikipedia để đặt trình độ của học sinh vào bối cảnh toàn cầu.
- **Giải thích sâu:** Dự án chia làm 2 cấp độ:
  - *Cấp vi mô (học sinh):* Trả lời câu hỏi yếu tố nào thực sự quyết định điểm số (điểm giữa kỳ G2 và lịch sử trượt môn áp đảo hoàn toàn các yếu tố như internet hay thời gian tự học).
  - *Cấp vĩ mô (quốc gia):* Điểm PISA cho thấy thời điểm khảo sát UCI (2005–2006), Bồ Đào Nha thấp hơn trung bình OECD ở cả 3 môn, trước khi vươn lên bắt kịp vào năm 2015.

### Q1.2: Tại sao lại chọn môn Toán (`mat`) làm môn phân tích chính mà không phải môn Tiếng Bồ Đào Nha (`por`)?
- **Trả lời nhanh:** Môn Toán có tính phân loại cao hơn, tỉ lệ trượt cao hơn (Toán trượt 32.9%, Tiếng Bồ Đào Nha chỉ trượt 15.4%), và phân phối điểm trải rộng hơn. Môn Tiếng Bồ Đào Nha được dùng làm tập kiểm chứng độc lập (Holdout validation) ngoài mẫu để kiểm tra độ tin cậy của bộ quy tắc rủi ro.
- **Bằng chứng:** Quy định trong `docs/adr/0003-por-for-comparison-and-holdout-only.md`.

### Q1.3: G1, G2, G3 là gì? Thang điểm chấm thế nào? Điểm qua môn là bao nhiêu?
- **Trả lời nhanh:** Thang điểm 0–20 theo hệ thống giáo dục Bồ Đào Nha:
  - `G1`: Điểm kỳ 1 (First Period).
  - `G2`: Điểm kỳ 2 / giữa kỳ (Second Period).
  - `G3`: Điểm tổng kết cuối kỳ (Final Grade) — đây là **biến mục tiêu (Target)**.
  - Điểm qua môn: $G3 \ge 10$ là **Đỗ (Pass)**, $G3 < 10$ là **Trượt (Fail)**.

---

## 2. Bộ dữ liệu học sinh UCI & Tiền xử lý (Data Cleaning)

### Q2.1: Quy trình làm sạch dữ liệu trong dự án diễn ra qua các bước nào?
- **Trả lời nhanh:** Hàm `clean_data()` thực hiện 6 bước chặt chẽ:
  1. Cắt tỉa khoảng trắng thừa (`strip`) trên toàn bộ cột chuỗi.
  2. Ép kiểu số và kiểm tra miền giá trị hợp lệ theo định nghĩa UCI (`VALID_RANGES`).
  3. Mã hoá nhị phân các cột `yes`/`no` thành `1`/`0`.
  4. Xoá dòng trùng lặp (`drop_duplicates`) và kiểm tra giá trị thiếu (`dropna` trên các cột điểm bắt buộc).
  5. Tạo các cột dẫn xuất (`pass_fail`, `absence_level`, `avg_grade`, `avg_g1g2`, `risk_group`).
  6. Gắn 6 cờ bất thường (`anomaly flags`), tính ngưỡng vắng học bất thường bằng phương pháp IQR riêng cho từng môn.
- **Vị trí code:** `data_processor.py`, dòng 681–744.

### Q2.2: Cột `avg_grade` được tính như thế nào và tại sao không được đưa vào mô hình dự báo?
- **Trả lời nhanh:** `avg_grade = (G1 + G2 + G3) / 3`. Cột này **tuyệt đối không được đưa vào bất kỳ mô hình dự báo hay quy tắc cảnh báo nào** vì nó chứa biến mục tiêu $G3$. Đưa vào sẽ gây ra lỗi **rò rỉ dữ liệu (Data Leakage)** — dùng kết quả tương lai để dự đoán chính nó. Cột này chỉ có ý nghĩa thống kê mô tả.
- **Bằng chứng:** Đã ghi rõ cảnh báo trong docstring của `calc_average_grade` (`data_processor.py`, dòng 139–145) và `VAR_DESCRIPTIONS`.

### Q2.3: Trong 2 file `student-mat.csv` và `student-por.csv`, có bao nhiêu học sinh học cả hai môn? Ghép như thế nào?
- **Trả lời nhanh:** Có **382 học sinh trùng** xuất hiện ở cả 2 file (theo 13 thuộc tính định danh trong file gốc `student-merge.R`). Sau khi làm sạch và loại bỏ các khoá bị lặp nội bộ trong cùng 1 môn, ghép được **358 học sinh duy nhất**, trong đó có **324 cặp học sinh có điểm thi thật ($G3 > 0$) ở cả 2 môn**.
- **Giải thích sâu:** Vì cùng một em học sinh học cả 2 môn nên 2 file này **không phải 2 mẫu độc lập**. Do đó, so sánh điểm 2 môn phải dùng **kiểm định ghép cặp (Paired t-test)** chứ không được dùng t-test độc lập. Điểm Toán thấp hơn môn Tiếng Bồ Đào Nha trung bình $-1.26$ điểm ($p < 0.001$).
- **Bằng chứng:** `docs/adr/0003-por-for-comparison-and-holdout-only.md` và hàm `_paired_subjects()` (`data_processor.py`, dòng 537–566).

---

## 3. Hiện tượng điểm 0 (G3 = 0) & 6 Cờ bất thường (Anomaly Flags)

### Q3.1: Hiện tượng 38 học sinh bị điểm 0 ($G3 = 0$) môn Toán là gì? Tại sao không xoá đi?
- **Trả lời nhanh:** Trong 395 học sinh môn Toán, có 38 em bị $G3 = 0$. Cả 38 em này đều có **số buổi vắng học bằng 0 (`absences = 0`)** và điểm G1 trung bình vẫn đạt ~7.5. Điều này chỉ ra đây là nhóm **bỏ thi / thôi học giữa chừng (Dropout Suspects)** chứ không phải đi thi làm bài bị 0 điểm. Không xoá vì xoá dữ liệu gốc là sai lệch thực tế; nhóm này được **gắn nhãn cờ `dropout_suspect = True`** và bóc tách riêng khi phân tích.
- **Tại sao không xoá:**
  1. Giữ tính toàn vẹn dữ liệu gốc (Data Integrity).
  2. Bỏ học/bỏ thi là một hiện tượng quản lý giáo dục có thật, cần đếm được số lượng (38 em = 9.6%).
  3. Mọi kết luận khoa học (tương quan, OLS, biểu đồ) được tính trên tập **loại trừ nhóm bỏ thi (`exclude_dropout`)** để tránh kết quả bị méo mó (ví dụ: kéo tỉ lệ đỗ từ 74.2% tụt xuống 67.1%).
- **Bằng chứng:** `docs/adr/0001-flag-dropout-suspects-not-delete.md`.

### Q3.2: 6 cờ dữ liệu bất thường (Anomaly Flags) trong dự án là những cờ nào?
- **Trả lời nhanh:**
  1. `dropout_suspect`: $G3 = 0$ (nghi bỏ thi/thôi học).
  2. `g2_zero`: $G2 = 0$ (nghi vắng thi kỳ 2).
  3. `grade_drop`: Tụt điểm đột ngột giữa các kỳ ($G1 - G3 \ge 8$ hoặc $G2 - G3 \ge 6$).
  4. `absence_outlier`: Vắng học nhiều bất thường (vượt ngưỡng IQR $Q3 + 1.5 \times IQR$, môn Toán là $> 20$ buổi).
  5. `age_outlier`: Học muộn / lưu ban ($\ge 20$ tuổi).
  6. `inconsistent_grade`: Mâu thuẫn logic ($G3 > 0$ nhưng $G2 = 0$, vắng thi giữa kỳ nhưng lại có điểm cuối kỳ).

---

## 4. Ý nghĩa 4 Biểu đồ & Kết luận thống kê cốt lõi

### Q4.1: Biểu đồ 1 (`01_bar_studytime_internet.png`) cho thấy điều gì? Tại sao nhìn cột có internet cao hơn nhưng lại kết luận "không có ý nghĩa thống kê"?
- **Trả lời nhanh:**
  - Nhìn mắt thường, nhóm có internet có điểm trung bình cao hơn ~1 điểm. Nhưng **thanh sai số 95% CI (error bar) chồng lấn lên nhau rất nhiều**.
  - Kiểm định Welch t-test sau khi hiệu chỉnh đa kiểm định Holm cho thấy: $p_{holm} = 0.080 > 0.05$. Do đó, **không đủ bằng chứng thống kê để khẳng định có internet ở nhà giúp tăng điểm Toán**.
  - Tự học (`studytime`) có làm tăng nhẹ điểm từ mức 1 (<2h) lên mức 3 (5–10h), nhưng tự học trên 10h không làm điểm tăng thêm (hiệu ứng tăng chậm dần).
- **Về các cột gạch chéo:** Cột nào có cỡ mẫu $n < 10$ học sinh (như nhóm tự học >10h không có internet chỉ có đúng $n=3$ em) được code vẽ **gạch chéo và làm mờ**, cảnh báo rằng mẫu quá nhỏ, không được suy diễn khái quát.
- **Vị trí code:** `_plot_bar` trong `data_processor.py`, dòng 912–946.

### Q4.2: Biểu đồ 2 (`02_hist_g3.png`) chứng minh điều gì về mặt phân phối?
- **Trả lời nhanh:** Biểu đồ histogram điểm G3 chứng minh 2 điều:
  1. Phân phối điểm của học sinh thi thật ($G3 > 0$) có dạng **chuẩn hình chuông**, đỉnh tập trung quanh 10–11 điểm và trải đều 2 phía.
  2. Khoảng điểm 1, 2, 3 hoàn toàn **trống trơn (0 học sinh nào)**, rồi đột ngột vọt lên 38 em ở mốc 0 (cột màu đỏ đứng tách biệt). Đây là bằng chứng thép trực quan chứng minh điểm 0 là do **bỏ thi** chứ không phải do năng lực làm bài kém.

### Q4.3: Biểu đồ 3 (`03_heatmap_corr.png`) chỉ ra biến nào tác động mạnh nhất đến điểm cuối kỳ G3?
- **Trả lời nhanh:**
  - **Tác động mạnh nhất (áp đảo):** Điểm giữa kỳ $G2$ ($r = +0.966$) và $G1$ ($r = +0.892$).
  - **Yếu tố kéo tụt điểm mạnh nhất:** Số môn từng trượt trong quá khứ (`failures`, $r = -0.294$) và số buổi vắng học (`absences`, $r = -0.213$). Cả hai đều có $p < 0.001$.
  - **Yếu tố bất ngờ:** Hỗ trợ từ gia đình (`famsup`) hầu như không tương quan với điểm ($r = -0.067, p = 0.205$). Thời gian tự học (`studytime`) tương quan dương nhẹ ($r = +0.127$) nhưng chỉ giải thích được $3.6\%$ phương sai ($\eta^2 = 0.036$).

### Q4.4: Biểu đồ 4 (`04_pisa_portugal_oecd.png`) mang lại giá trị gì cho bài phân tích?
- **Trả lời nhanh:** Biểu đồ đường so sánh điểm PISA của Bồ Đào Nha với trung bình OECD từ 2000–2025 ở cả 3 môn (Toán, Đọc hiểu, Khoa học):
  - Năm 2005–2006 (thời điểm thu thập dữ liệu UCI), Bồ Đào Nha thấp hơn trung bình OECD ở cả 3 môn (môn Toán đạt 466 so với OECD 494).
  - Đến năm 2015, Bồ Đào Nha bắt kịp OECD môn Toán.
  - Năm 2025, cả Bồ Đào Nha và OECD đều đi xuống nhẹ, Bồ Đào Nha ở mức ngang bằng OECD (Toán 460 so với 463).
  - Biểu đồ này cung cấp **bối cảnh cấp quốc gia**, hoàn toàn tách biệt và không ghép vào từng học sinh UCI.

---

## 5. Quy tắc cảnh báo sớm rủi ro (Early Warning Risk Rule)

### Q5.1: Hàm `classify_risk` hoạt động như thế nào? Điều kiện từng nhóm là gì?
- **Trả lời nhanh:** Quy tắc chia học sinh làm 3 phân tầng rủi ro:
  - **High (Nguy cơ cao):** Nếu $G2 < 10$ HOẶC từng trượt $\ge 2$ môn (`failures >= 2`).
  - **Medium (Nguy cơ vừa):** Nếu $G1 < 10$ HOẶC từng trượt 1 môn (`failures == 1`) HOẶC vắng học nhiều (`absences >= 10`).
  - **Low (Nguy cơ thấp):** Các trường hợp còn lại.
- **Vị trí code:** `data_processor.py`, dòng 148–162.

### Q5.2: Tại sao trong hàm `classify_risk` tuyệt đối không được dùng điểm G3?
- **Trả lời nhanh:** Vì đây là **hệ thống cảnh báo sớm (Early Warning System)**, phải chạy **ngay từ giữa kỳ** để thầy cô có thời gian phụ đạo cho học sinh trước khi kỳ thi cuối diễn ra. Lúc đó chưa thi nên chưa có G3. Nếu dùng G3 vào rule thì vừa vô nghĩa trong thực tế vừa phạm lỗi rò rỉ dữ liệu.
- **Bằng chứng:** `docs/adr/0002-risk-group-never-uses-g3.md`.

### Q5.3: Hiệu quả của rule được đánh giá qua những chỉ số nào? Kết quả ra sao?
- **Trả lời nhanh:** Đánh giá bằng **Recall (Độ nhạy - bắt trúng bao nhiêu % em trượt)** và **Precision (Độ chuẩn xác - trong số em bị báo động thì bao nhiêu % trượt thật)**:
  - Trên môn Toán (tập huấn luyện): **Recall = 93.8%** [86.2%, 97.3%], **Precision = 81.9%** [73.2%, 88.2%].
  - Trên môn Tiếng Bồ Đào Nha tập Holdout chặt (275 em chưa từng thấy): **Recall = 91.4%** [77.6%, 97.0%], **Precision = 66.0%** [51.7%, 77.8%].
  - Độ nhạy trên 91% chứng minh quy tắc này cực kỳ an toàn cho mục đích sư phạm: gần như không bỏ sót học sinh nào có nguy cơ trượt môn.

### Q5.4: Tại sao cần phân tầng 3 mức (Low, Medium, High) mà không chia đôi Đỗ/Trượt?
- **Trả lời nhanh:** Vì nguồn lực phụ đạo của nhà trường có hạn:
  - Nhóm **High** có tỉ lệ trượt thật là **81.9%** $\rightarrow$ Cần can thiệp khẩn cấp 1-kèm-1.
  - Nhóm **Medium** có tỉ lệ trượt là **22.5%** $\rightarrow$ Nhắc nhở, gửi thông báo cho phụ huynh, cho làm thêm bài tập (kiểm định Fisher khẳng định nhóm Medium trượt nhiều hơn nhóm Low rõ rệt với $p < 0.001$).
  - Nhóm **Low** tỉ lệ trượt chỉ **4.0%** $\rightarrow$ An toàn, không cần can thiệp.

---

## 6. Mô hình Hồi quy Tuyến tính OLS & Kiểm định Nâng cao

### Q6.1: Tại sao nhóm tự viết thuật toán hồi quy OLS bằng đại số tuyến tính mà không dùng thư viện `scikit-learn` hay `statsmodels`?
- **Trả lời nhanh:** Để chứng minh khả năng làm chủ toán học và lập trình khoa học từ con số 0:
  - Tính vector hệ số hồi quy bằng công thức ma trận: $\beta = (X^T X)^{-1} X^T y$.
  - Tính ma trận độ đòn bẩy: $H = X (X^T X)^{-1} X^T$.
  - Tính ma trận hiệp phương sai sai số chuẩn vững **HC3** (chống phương sai thay đổi): $\Sigma_{HC3} = (X^T X)^{-1} X^T \text{diag}\left(\frac{e_i^2}{(1 - h_{ii})^2}\right) X (X^T X)^{-1}$.
  - Tính $t$-statistic, tra phân phối Student-t lấy $p$-value và khoảng tin cậy 95% của từng biến.
- **Vị trí code:** Hàm `_ols()` trong `data_processor.py`, dòng 505–533.

### Q6.2: Mô hình A và Mô hình B khác nhau thế nào? R² của từng mô hình là bao nhiêu?
- **Trả lời nhanh:**
  - **Mô hình A (Chỉ dùng 13 yếu tố nền, không có điểm):** $R^2 = 0.234$. Nghĩa là toàn bộ hoàn cảnh gia đình, tự học, internet, vắng học chỉ giải thích được $23.4\%$ sự biến thiên của điểm số. Trong đó chỉ có lịch sử trượt (`failures`, $\beta = -1.65$) và vắng học (`absences`, $\beta = -0.06$) là có ý nghĩa thống kê ($p < 0.01$).
  - **Mô hình B (Thêm điểm kỳ 1 G1 và giữa kỳ G2):** $R^2 = 0.937$. Điểm $G2$ có hệ số $\beta = +0.94$ ($p < 0.001$). Khi đã biết điểm G2, hầu hết các yếu tố nền gia đình đều mất sạch ý nghĩa thống kê.
- **Lưu ý đa cộng tuyến:** $r(G1, G2) = 0.902$, nên không diễn giải riêng lẻ hệ số của G1 và G2 trong mô hình B.

### Q6.3: Đa kiểm định (Multiple Testing) là gì và tại sao phải dùng hiệu chỉnh Holm-Bonferroni?
- **Trả lời nhanh:** Khi chạy nhiều kiểm định thống kê đồng thời với ngưỡng $\alpha = 0.05$, xác suất mắc phải sai số loại I (dương tính giả — kết luận có ý nghĩa trong khi thực tế là do ngẫu nhiên) sẽ tăng vọt theo công thức $1 - (1 - \alpha)^k$. Hiệu chỉnh **Holm-Bonferroni** sắp xếp các $p$-value tăng dần và điều chỉnh ngưỡng kiểm định từng bước, giúp kiểm soát sai số cho toàn bộ họ giả thuyết mà không quá khắt khe như Bonferroni cổ điển.
- **Vị trí code:** Hàm `_holm()` trong `data_processor.py`, dòng 438–444.

---

## 7. Cào dữ liệu PISA Wikipedia & Đối chiếu OECD (Web Scraping)

### Q7.1: Luồng cào dữ liệu PISA hoạt động như thế nào?
- **Trả lời nhanh:** Hoạt động theo cơ chế **Cache-first**:
  1. Mặc định đọc file cache offline `data/raw/pisa_reference.csv` (nếu đã có) và chạy kiểm định tính toàn vẹn `validate_pisa_raw()`. Tuyệt đối không gọi mạng vô cớ.
  2. Khi chạy cờ lệnh `python main.py --refresh-pisa` hoặc thiếu cache: Gửi 1 HTTP GET request bằng `requests` kèm `User-Agent` hợp lệ.
  3. Dùng `BeautifulSoup` bóc tách cây DOM HTML, lấy bảng tóm tắt 2025 và xoay bảng lịch sử 2000–2022 từ dạng rộng sang dạng dài.
  4. Chạy `validate_pisa_raw()` kiểm tra 6 tiêu chí. Hợp lệ mới được ghi đè cache và ghi file `pisa_reference.meta.json` lưu nguồn gốc (URL, mã phiên bản Wikipedia `revision_id`, permalink, thời gian cào).
  5. Nếu cào lỗi hoặc mạng mất: Tự động fallback về file cache cũ, phát cảnh báo `warnings.warn` chứ không làm sập chương trình.
- **Vị trí code:** `data_processor.py`, dòng 203–353.

### Q7.2: Parser nhận diện các bảng trên trang Wikipedia như thế nào?
- **Trả lời nhanh:** Parser nhận diện bảng **dựa trên cấu trúc nội dung** chứ không dựa vào thứ tự bảng trên trang:
  - Bảng 2025: Nhận diện bằng thẻ tiêu đề chứa 3 môn (`mathematics`, `science`, `reading`) và chứa đúng 3 bảng con lồng nhau bên trong.
  - Bảng so sánh 2000–2022: Nhận diện bằng hàng đầu là tên môn, hàng 2 có ô đầu là `Country` theo sau là các năm, rồi chuyển đổi các cặp (năm, điểm, hạng) từ dạng rộng sang dạng dài.
  - Nhờ vậy, nếu Wikipedia có thêm bớt các bảng khác trên trang, code vẫn tìm đúng bảng cần lấy.

### Q7.3: Hàm `validate_pisa_raw` kiểm tra những gì trước khi cho phép lưu dữ liệu?
- **Trả lời nhanh:** Kiểm tra 6 điều kiện bắt buộc:
  1. Đủ cả 3 môn cho cả bảng tóm tắt và bảng so sánh lịch sử.
  2. Năm thi phải là số từ 2000 đến năm hiện tại.
  3. Điểm PISA nằm trong khoảng hợp lý từ 200 đến 700.
  4. Mỗi năm / mỗi môn phải có ít nhất 30 quốc gia tham gia.
  5. Không có quốc gia nào bị lặp tên trong cùng một kỳ thi.
  6. Phải có đúng 1 dòng điểm trung bình OECD (`OECD average`).

### Q7.4: Làm sao chứng minh dữ liệu PISA cào từ Wikipedia là chính xác và đáng tin cậy?
- **Trả lời nhanh:** Code có hàm `cross_check_pisa()` tự động đối chiếu dữ liệu cào được với bảng chính thức **Table I.1 trong báo cáo *PISA 2025 Results (Volume I)* của OECD**:
  - Năm 2025: So khớp điểm trực tiếp $\rightarrow$ **274/274 điểm khớp tuyệt đối 100%**.
  - Năm 2022: OECD tính điểm 2022 bằng công thức `điểm 2025 - mức thay đổi`. Do OECD làm tròn từ số thực, cho phép sai số $\pm 1$ điểm $\rightarrow$ **208/211 dòng nằm trong sai số $\pm 1$**.
- **Bằng chứng:** Kết quả đối chiếu lưu trong `summary.json` và in trực tiếp trong báo cáo.

---

## 8. Kiến trúc Mã nguồn & Quy trình Xuất Báo cáo tự động

### Q8.1: Kiến trúc mã nguồn được phân chia như thế nào?
- **Trả lời nhanh:** Gồm 4 file code chính theo nguyên lý phân tách trách nhiệm (Separation of Concerns):
  1. `main.py`: Điểm điều phối (Entry point), thiết lập chạy ngầm `Agg`, nhận cờ lệnh, chạy pipeline và xuất kết quả.
  2. `data_processor.py`: Trọng tâm thuật toán: cấu hình ngưỡng, tiền xử lý, kiểm định, OLS, rule rủi ro, cào web và vẽ 4 biểu đồ.
  3. `report_builder.py`: Dùng `inspect` đọc trực tiếp code và số dòng thật, kết hợp với từ điển kết quả `_facts` để sinh tự động 4 file Markdown báo cáo (`report.md`, `report_vi.md`, `report_summary.md`, `report_summary_vi.md`).
  4. `export_pdf.py`: Dùng `markdown-it-py`, `pygments` tô màu code và gọi Chromium/Edge headless in ra 4 file PDF chuẩn in ấn A4.

### Q8.2: Tại sao báo cáo lại được sinh tự động bằng code mà không viết tay bằng Word/Markdown?
- **Trả lời nhanh:** Để đảm bảo tính **tái lập (Reproducibility)** và nguyên tắc **Single Source of Truth**:
  - Mọi con số trong báo cáo (từ 0.742, -0.213, R² 0.937 đến số nước PISA) được trích trực tiếp từ đối tượng `proc.results`. Khi dữ liệu thay đổi, chỉ cần chạy lại `main.py` là báo cáo cập nhật 100%, không bao giờ có hiện tượng "chữ một đằng, biểu đồ một nẻo".
  - Các đoạn code nhúng trong báo cáo được hàm `inspect` đọc từ file `.py` kèm số dòng thực tế, không bị lỗi thời khi sửa code.

### Q8.3: Dự án có bao nhiêu ca kiểm thử tự động (Unit Tests)? Test những nghiệp vụ gì?
- **Trả lời nhanh:** Có **48 tests tự động** viết bằng `pytest` trong thư mục `tests/` (100% pass):
  - Kiểm thử điểm biên đỗ/trượt (9.0, 9.99, 10.0), biên buổi vắng (3, 4, 9, 10).
  - Kiểm thử tính độc lập của rule rủi ro: Đảm bảo đổi G3 thì kết quả `classify_risk` không bị đổi (chống rò rỉ dữ liệu).
  - Kiểm thử parser PISA, 6 ca lỗi trong validation, cơ chế cache-first không gọi mạng.
  - Kiểm thử 6 dòng cấy lỗi làm sạch dữ liệu.
  - Kiểm thử thuật toán OLS tự code trên dữ liệu giả lập.
  - Kiểm thử tập holdout chặt và thuật toán ghép cặp 2 môn.
  - Kiểm thử xuất file CSV riêng cho từng môn `mat` và `por`.
  - Kiểm thử báo lỗi rõ tên file khi thiếu dữ liệu OECD.

### Q8.4: Tại sao project có cả bản báo cáo đầy đủ (~33 trang) và bản tóm tắt (2 trang)?
- **Trả lời nhanh:** Để linh hoạt theo yêu cầu chấm điểm:
  - Bản đầy đủ (`report.pdf`, `report_vi.pdf` ~33 trang): Phục vụ thuyết trình, chiếu slide, chứa toàn bộ phân tích chi tiết, code minh hoạ, 4 ảnh biểu đồ và các bảng kiểm định.
  - Bản tóm tắt (`report_summary.pdf`, `report_summary_vi.pdf` đúng **2 trang A4**): Đáp ứng yêu cầu đề bài nộp bản executive summary 1–2 trang. Bản tóm tắt được cắt trực tiếp từ bản đầy đủ (tiêu đề, câu hỏi chính, tóm tắt kết quả, giới hạn nghiên cứu) nên số liệu giống hệt nhau 100%.

---

## 9. Bảng tóm tắt các con số cốt lõi (Học thuộc trước khi vào phòng thi)

| Chỉ số | Con số thực tế | Ý nghĩa |
|---|---|---|
| **Số học sinh môn Toán** | 395 học sinh | Tập dữ liệu phân tích chính |
| **Số học sinh bỏ thi ($G3 = 0$)** | 38 em (9.6%) | Gắn cờ `dropout_suspect`, đều có `absences = 0` |
| **Tỉ lệ đỗ môn Toán** | 67.1% (tất cả) $\rightarrow$ **74.2%** (loại bỏ thi) | Mốc đỗ $G3 \ge 10$ |
| **Tỉ lệ đỗ môn Tiếng Bồ Đào Nha** | 84.6% (tất cả) $\rightarrow$ **86.6%** (loại bỏ thi) | Môn ngôn ngữ dễ đỗ hơn nhiều |
| **Tương quan G2 với G3** | $r = +0.966$ ($p < 0.001$) | Yếu tố dự báo điểm cuối kỳ mạnh nhất |
| **Tương quan vắng học với G3** | $r = -0.213$ ($p < 0.001$) | Càng vắng nhiều điểm càng tụt |
| **Tương quan trượt cũ với G3** | $r = -0.294$ ($p < 0.001$) | Yếu tố quá khứ kéo điểm mạnh nhất |
| **Ảnh hưởng của Internet** | $p_{holm} = 0.080$ | **Không có ý nghĩa thống kê** sau hiệu chỉnh Holm |
| **Hồi quy Mô hình A (yếu tố nền)** | $R^2 = 0.234$ | Chỉ giải thích được 23.4% biến thiên điểm |
| **Hồi quy Mô hình B (thêm G1, G2)** | $R^2 = 0.937$ | Biết điểm giữa kỳ giải thích được 93.7% |
| **Độ nhạy Rule rủi ro (Toán)** | **Recall = 93.8%**, Precision = 81.9% | Bắt trúng gần như toàn bộ học sinh sẽ trượt |
| **Độ nhạy Rule rủi ro (Holdout)** | **Recall = 91.4%**, Precision = 66.0% | Kiểm chứng trên 275 học sinh môn Bồ Đào Nha |
| **Đối chiếu PISA 2025 với OECD** | **274/274 khớp 100%** | Khẳng định dữ liệu Wikipedia cào về chuẩn xác |
| **Số lượng Unit Tests** | **48/48 passed** | Đảm bảo phần mềm không có lỗi ngầm |
