# Tổng quan Dự án P1 — Phân tích Điểm số Học sinh (Student Performance)

Tài liệu tóm tắt phục vụ thuyết trình, vấn đáp và nắm bắt nhanh toàn bộ dự án.

---

## 1. Dự án này dùng để làm gì?

Dự án này là một bài toán **Data Science trong giáo dục**, giải quyết 3 mục tiêu cốt lõi:

1. **Tìm nguyên nhân thực sự ảnh hưởng đến điểm số:** 
   - Phân tích dữ liệu học sinh THPT môn Toán (bộ dữ liệu UCI từ 2 trường học tại Bồ Đào Nha).
   - Trả lời câu hỏi: Trong các yếu tố như thời gian tự học, số buổi vắng học, hỗ trợ từ gia đình, internet và điểm giữa kỳ, yếu tố nào thực sự tác động mạnh nhất đến kết quả cuối kỳ?
2. **Xây dựng hệ thống cảnh báo sớm (Early Warning System):**
   - Đặt ra bộ quy tắc phân loại rủi ro học tập (`classify_risk`) **ngay từ giữa kỳ** (chỉ nhìn vào G1, G2, số lần trượt cũ và số buổi vắng; tuyệt đối không dùng điểm cuối kỳ G3).
   - Giúp nhà trường nhận diện sớm học sinh có nguy cơ trượt môn (bắt trúng hơn 91% số em sẽ trượt trên dữ liệu kiểm chứng độc lập) để thầy cô có kế hoạch phụ đạo kịp thời trước kỳ thi cuối.
3. **Mở rộng dữ liệu & đối chiếu thực tế:**
   - Cào dữ liệu điểm PISA quốc tế từ Wikipedia để so sánh tương quan trình độ của học sinh Bồ Đào Nha với chuẩn trung bình thế giới (OECD).

---

## 2. G1, G2, G3 là gì?

Đây là hệ thống điểm số của học sinh phổ thông Bồ Đào Nha, chấm theo **thang điểm từ 0 đến 20**:

| Điểm | Tên gọi | Ý nghĩa |
|---|---|---|
| **G1** | First Period Grade | Điểm đánh giá kỳ 1 (0–20) |
| **G2** | Second Period Grade | Điểm đánh giá kỳ 2 / giữa kỳ (0–20) |
| **G3** | Final Grade | **Điểm thi cuối kỳ / tổng kết năm học** (0–20). Đây là **biến mục tiêu quan trọng nhất (Target Variable)** cần phân tích và dự đoán. |

- **Quy định đỗ/trượt:**
  - $G3 \ge 10$: **Đỗ (Pass)**
  - $G3 < 10$: **Trượt (Fail)**

### ⚠️ Phát hiện quan trọng về nhóm $G3 = 0$ (Dropout Suspects):
- Trong 395 học sinh môn Toán, có **38 em bị $G3 = 0$**.
- Điểm đặc biệt: **toàn bộ 38 em này đều có số buổi vắng học bằng 0 (`absences = 0`)** và điểm G1 trung bình vẫn đạt ~7.5.
- **Ý nghĩa:** Các em này **bỏ thi / thôi học giữa chừng** (chứ không phải đi thi làm bài bị 0 điểm).
- **Cách xử lý trong code:** Gắn nhãn cờ `dropout_suspect = True` để bóc tách riêng, **không xoá dữ liệu**. Mọi kết luận khoa học chính đều được tính trên tập đã loại trừ nhóm này để tránh số liệu bị méo mó.

---

## 3. Dữ liệu có những trường nào?

Dữ liệu gốc từ UCI có **33 cột (thuộc tính)**, được phân thành 5 nhóm logic:

### Nhóm 1: Thông tin cá nhân & Trường học
- `school`: Trường học (`GP`: Gabriel Pereira, `MS`: Mousinho da Silveira).
- `sex`: Giới tính (`F`: nữ, `M`: nam).
- `age`: Tuổi học sinh (từ 15 đến 22).
- `address`: Nơi cư trú (`U`: thành thị - urban, `R`: nông thôn - rural).
- `famsize`: Quy mô gia đình (`LE3`: $\le 3$ người, `GT3`: $> 3$ người).
- `Pstatus`: Tình trạng bố mẹ (`T`: sống chung, `A`: sống riêng/ly thân).

### Nhóm 2: Hoàn cảnh & Học vấn gia đình
- `Medu`, `Fedu`: Trình độ học vấn của mẹ / bố (0: không đi học/mù chữ, 1: tiểu học, 2: cấp 2, 3: cấp 3, 4: đại học).
- `Mjob`, `Fjob`: Nghề nghiệp của mẹ / bố (`teacher`, `health`, `services`, `at_home`, `other`).
- `guardian`: Người giám hộ chính (`mother`, `father`, `other`).

### Nhóm 3: Học tập & Các hỗ trợ giáo dục
- `studytime`: Thời gian tự học mỗi tuần (1: <2h, 2: 2–5h, 3: 5–10h, 4: >10h).
- `failures`: Số môn từng thi trượt trong quá khứ (0 đến 3).
- `schoolsup`: Hỗ trợ phụ đạo thêm từ trường (`yes` / `no`).
- `famsup`: Gia đình có hỗ trợ học tập không (`yes` / `no`).
- `paid`: Có học thêm trả phí ngoài giờ môn này không (`yes` / `no`).
- `higher`: Có nguyện vọng học lên đại học không (`yes` / `no`).
- `internet`: Ở nhà có kết nối mạng internet không (`yes` / `no`).

### Nhóm 4: Đời sống cá nhân, Bạn bè & Sức khỏe
- `activities`: Có tham gia hoạt động ngoại khóa không (`yes` / `no`).
- `nursery`: Hồi nhỏ có học mẫu giáo không (`yes` / `no`).
- `romantic`: Có đang có người yêu không (`yes` / `no`).
- `famrel`: Mức độ hòa thuận trong gia đình (1: rất tệ đến 5: rất tốt).
- `freetime`: Thời gian rảnh rỗi sau giờ học (1 đến 5).
- `goout`: Tần suất đi chơi với bạn bè (1 đến 5).
- `Dalc`: Mức độ uống rượu bia vào ngày thường (1 đến 5).
- `Walc`: Mức độ uống rượu bia vào cuối tuần (1 đến 5).
- `health`: Tình trạng sức khỏe hiện tại (1 đến 5).
- `traveltime`: Thời gian đi từ nhà đến trường (1: <15 phút, 2: 15–30 phút, 3: 30–60 phút, 4: >1 giờ).

### Nhóm 5: Quá trình đi học & Điểm số
- `absences`: Số buổi vắng học trong năm (0 đến 93).
- `G1`, `G2`, `G3`: Điểm số 3 kỳ (thang 0–20).

---

### 🛠️ Các cột dẫn xuất & Cờ bất thường (Do code tự tạo thêm)
- `subject`: Phân biệt môn (`mat`: Toán, `por`: Tiếng Bồ Đào Nha).
- `pass_fail`: Đỗ (`pass`) hoặc Trượt (`fail`).
- `absence_level`: Mức độ vắng (`low`: 0–3, `medium`: 4–9, `high`: $\ge 10$).
- `avg_grade`: Điểm trung bình cả năm (G1 + G2 + G3) / 3.
- `avg_g1g2`: Điểm trung bình giữa kỳ (G1 + G2) / 2.
- `risk_group`: Nhóm nguy cơ trượt sớm (`low`, `medium`, `high`).
- **6 cờ dữ liệu bất thường (Anomaly Flags - giữ nguyên dòng, chỉ đánh dấu True/False):**
  1. `dropout_suspect`: $G3 = 0$ (nghi bỏ thi/bỏ học).
  2. `g2_zero`: $G2 = 0$ (nghi vắng thi kỳ 2).
  3. `grade_drop`: Tụt điểm đột ngột giữa các kỳ (G1–G3 $\ge 8$ hoặc G2–G3 $\ge 6$).
  4. `absence_outlier`: Vắng nhiều bất thường (vượt ngưỡng IQR: > 20 buổi ở môn Toán).
  5. `age_outlier`: Học muộn / lưu ban ($\ge 20$ tuổi).
  6. `inconsistent_grade`: Mâu thuẫn logic ($G3 > 0$ nhưng $G2 = 0$).

---

# 4. Ý nghĩa của 5 ảnh biểu đồ & minh chứng trong dự án

Các ảnh được lưu tại thư mục `images/`. Ảnh 1–3 là 3 biểu đồ đề yêu cầu; ảnh 4 là biểu đồ bối cảnh PISA; ảnh 5 là ảnh minh chứng khảo sát trực tiếp cấu trúc bảng trên trình duyệt qua DevTools Console:

```
images/
├── 01_bar_studytime_internet.png
├── 02_hist_g3.png
├── 03_heatmap_corr.png
├── 04_pisa_portugal_oecd.png
└── 05_devtools_console.png
```
---

### 📊 Ảnh 1: `01_bar_studytime_internet.png` (Biểu đồ cột nhóm)
- **Thành phần biểu đồ:**
  - **Trục X:** 4 mức thời gian tự học mỗi tuần (1: <2h, 2: 2–5h, 3: 5–10h, 4: >10h).
  - **Trục Y:** Điểm cuối kỳ G3 trung bình (cố định thang 0–20 để so sánh trực quan).
  - **Cột xanh:** Nhóm không có internet ở nhà (`no`).
  - **Cột cam:** Nhóm có internet ở nhà (`yes`).
  - **Thanh chữ I màu đen trên đầu cột (Error bar):** Khoảng tin cậy 95% của điểm trung bình. Thanh càng dài tức ước lượng điểm càng kém chắc chắn do mẫu ít.
  - **Nhãn `n=...`:** Số lượng học sinh thực tế ở từng nhóm.
- **Ý nghĩa & Kết luận rút ra:**
  1. **Tự học giúp tăng nhẹ điểm:** Điểm trung bình tăng từ ~11.5 điểm (<2h) lên ~12.6 điểm (5–10h), nhưng tự học trên 10h không làm điểm tăng vọt (hiệu ứng tăng chậm dần).
  2. **Yếu tố internet không còn ý nghĩa sau kiểm định:** Nhìn bằng mắt thường thì nhóm có internet cao hơn khoảng 1 điểm, nhưng các thanh sai số (error bar) chồng lấn lên nhau rất nhiều. Kiểm định thống kê Welch t-test sau khi hiệu chỉnh đa kiểm định Holm cho thấy chênh lệch này **không còn ý nghĩa thống kê** ($p_{holm} = 0.080 > 0.05$).
  3. **Cảnh báo mẫu nhỏ:** Nhóm tự học >10h mà không có internet chỉ có đúng $n = 3$ em (thanh sai số dài ngoằng), không được vội vàng đưa ra kết luận khái quát cho nhóm này.

---

### 📊 Ảnh 2: `02_hist_g3.png` (Histogram phân phối điểm G3)
- **Thành phần biểu đồ:**
  - **Trục X:** Điểm cuối kỳ G3 từ 0 đến 20 (mỗi cột ứng đúng 1 điểm nguyên).
  - **Trục Y:** Số lượng học sinh đạt mức điểm đó.
  - **Đường đứt nét đen dọc tại mốc 9.5:** Vạch phân cách đỗ ($\ge 10$) và trượt ($< 10$).
  - **Các cột màu xanh dương:** Học sinh có đi thi và có điểm thật ($G3 > 0$).
  - **Cột màu đỏ đứng riêng tại mốc 0:** 38 học sinh bị điểm 0 ($G3 = 0$).
  - **Khung chữ:** Thể hiện tỉ lệ đỗ toàn bộ (67.1%) và tỉ lệ đỗ sau khi bỏ nhóm bỏ thi (74.2%).
- **Ý nghĩa & Kết luận rút ra:**
  1. **Điểm thi thật phân phối chuẩn hình chuông:** Phân phối điểm của học sinh thi thật tập trung cao nhất quanh mốc 10–11 điểm và trải đều về 2 phía rất đẹp.
  2. **Bằng chứng trực quan thép về việc bỏ thi:** Khoảng điểm từ 1 đến 3 hoàn toàn **trống trơn (0 học sinh nào bị 1, 2, 3 điểm)**, rồi đột ngột vọt lên 38 em bị điểm 0 (cột đỏ). Điều này chứng minh điểm 0 không phải là điểm kém của học sinh đi thi, mà là một hiện tượng tách biệt: **học sinh bỏ thi / thôi học**.

---

### 📊 Ảnh 3: `03_heatmap_corr.png` (Ma trận nhiệt tương quan)
- **Thành phần biểu đồ:**
  - Thể hiện **hệ số tương quan Pearson ($r$)** giữa các biến số với điểm cuối kỳ G3 (trên tập học sinh đã loại bỏ nhóm bỏ thi).
  - **Thang màu phân kỳ (RdBu_r):** Màu đỏ biểu thị tương quan dương (biến này tăng thì điểm tăng), màu xanh biểu thị tương quan âm (biến này tăng thì điểm tụt), màu trắng là không tương quan ($r \approx 0$).
  - Che nửa tam giác trên vì ma trận đối xứng.
- **Ý nghĩa & Bảng xếp hạng ảnh hưởng đến điểm G3:**
  1. **Điểm giữa kỳ G2 quyết định tất cả ($r = +0.966$):** Điểm G2 có liên hệ cực mạnh với G3, tiếp theo là G1 ($+0.892$). Biết điểm G2 là gần như biết trước kết quả G3.
  2. **Yếu tố kéo tụt điểm mạnh nhất:**
     - Số môn từng trượt trong quá khứ (`failures`): $r = -0.294$ ($p < 0.001$).
     - Số buổi vắng học (`absences`): $r = -0.213$ ($p < 0.001$). Vắng càng nhiều thì điểm càng thấp rõ rệt.
  3. **Yếu tố bất ngờ:**
     - Hỗ trợ gia đình (`famsup`): $r = -0.067$ ($p = 0.205$, không có ý nghĩa thống kê). Việc gia đình có hỗ trợ hay không hầu như không ảnh hưởng đến điểm số môn Toán của học sinh.
     - Thời gian tự học (`studytime`): $r = +0.127$, có tác động dương nhưng mức độ giải thích phương sai rất nhỏ ($\eta^2 = 3.6\%$).

---

### 📈 Ảnh 4: `04_pisa_portugal_oecd.png` (Biểu đồ đường — bối cảnh PISA)
- **Thành phần biểu đồ:**
  - **3 ô:** Toán (Mathematics), Đọc hiểu (Reading), Khoa học (Science).
  - **Trục X:** Năm của kỳ thi PISA (2000, 2003, …, 2022, 2025; môn Khoa học bắt đầu từ 2006).
  - **Trục Y:** Điểm PISA trung bình của cả nước (dùng chung cho cả 3 ô).
  - **Đường xanh liền, chấm tròn:** Bồ Đào Nha.
  - **Đường xám đứt nét, ô vuông:** Trung bình OECD.
  - **Số ở cuối mỗi đường:** Điểm năm 2025.
  - **Dải màu cam:** Năm học 2005–06, thời điểm khảo sát học sinh trong dữ liệu UCI.
- **Nguồn & độ tin cậy:** Dữ liệu cào từ Wikipedia, sau đó đối chiếu với bảng chính thức Table I.1 trong báo cáo *PISA 2025 Results (Volume I)* của OECD: **274/274 điểm năm 2025 khớp tuyệt đối**.
- **Ý nghĩa & Kết luận rút ra:**
  1. Ở thời điểm dữ liệu UCI (2006), Bồ Đào Nha **thấp hơn trung bình OECD ở cả 3 môn** (môn Toán 466 so với 494).
  2. Môn Toán, Bồ Đào Nha tăng từ 454 điểm (2000) và **lần đầu bắt kịp trung bình OECD vào năm 2015**.
  3. Từ 2018 đến 2025, cả Bồ Đào Nha lẫn OECD cùng đi xuống; năm 2025 Bồ Đào Nha ngang mức OECD (Toán 460 so với 463).
  4. Đây chỉ là bối cảnh **cấp quốc gia**, không ghép với từng học sinh trong dữ liệu UCI.


### 🖥️ Ảnh 5: `05_devtools_console.png` (Minh chứng khảo sát DevTools Console F12)
- **Thành phần ảnh:**
  - Chụp giao diện Chrome DevTools Console (F12) trên bài viết Wikipedia PISA.
  - **Lệnh 1:** Quét và in bảng `console.table()` liệt kê toàn bộ 12 thẻ `table.wikitable` trên DOM, định vị chính xác:
    - Bảng index 1, 2, 3: Bảng xếp hạng PISA 2025 (Khoa học, Toán, Đọc hiểu);
    - Bảng index 5, 6, 7: Bảng so sánh lịch sử 2000–2022.
  - **Lệnh 2:** Dùng hàm `copy(...)` của DevTools trích xuất bảng Toán 2025 sang clipboard dạng CSV, lưu thành file đối chiếu độc lập `data/raw/pisa_manual_check.csv` (92 dòng).
- **Ý nghĩa:** Minh chứng rõ ràng rằng việc cào dữ liệu được thực hiện bài bản qua 2 bước: khảo sát cấu trúc thực tế trên trình duyệt bằng DevTools trước, sau đó mới viết script Python tự động hoá.
---

## 5. Các thư viện cài đặt & Vai trò thực tế trong dự án

Dự án được quản lý qua `requirements.txt` và cài đặt trong môi trường ảo `.venv`. Dưới đây là các thư viện bên thứ ba (Third-party packages) được sử dụng và nhiệm vụ cụ thể của từng thư viện trong project:

### 1. `pandas` (>= 2.0)
- **Nhiệm vụ:** Là xương sống quản lý, làm sạch và biến đổi dữ liệu dạng bảng (DataFrame).
  - Đọc/ghi các file CSV dữ liệu học sinh (`student-mat.csv`, `student-por.csv`) và dữ liệu PISA.
  - Hợp nhất dữ liệu 2 môn học qua cột `subject`, loại bỏ trùng lặp và các dòng thiếu dữ liệu bắt buộc.
  - Gom nhóm (`groupby`) để tính toán điểm trung bình, độ lệch chuẩn và số lượng học sinh theo từng phân lớp (thời gian tự học, mức vắng, internet, hỗ trợ gia đình...).
  - Tính ma trận hệ số tương quan Pearson giữa các biến số.

### 2. `numpy`
- **Nhiệm vụ:** Xử lý mảng ma trận và tính toán đại số tuyến tính tốc độ cao.
  - Tự cài đặt thuật toán hồi quy tuyến tính OLS đa biến từ con số 0: tính vector hệ số $\beta = (X^T X)^{-1} X^T y$.
  - Tính ma trận độ đòn bẩy (Leverage) và sai số chuẩn vững **HC3** (chống hiện tượng phương sai thay đổi heteroskedasticity).
  - Xử lý mảng số nguyên làm các khoảng chia (bins) cho biểu đồ histogram và hỗ trợ vector hóa tính khoảng tin cậy.

### 3. `scipy` (`scipy.stats` >= 1.11)
- **Nhiệm vụ:** Chạy toàn bộ hệ thống kiểm định thống kê khoa học và khoảng tin cậy:
  - **Welch t-test** (`stats.ttest_ind`): So sánh điểm trung bình giữa 2 nhóm có/không (internet, hỗ trợ gia đình, phụ đạo) mà không cần giả định phương sai bằng nhau.
  - **One-way ANOVA** (`stats.f_oneway`): So sánh điểm trung bình giữa các nhóm nhiều mức (thời gian tự học 4 mức, vắng học 3 mức, số lần trượt 4 mức).
  - **Kruskal-Wallis** (`stats.kruskal`): Kiểm tra phi tham số (dựa trên thứ hạng) để đối chứng lại ANOVA khi dữ liệu không phân phối chuẩn.
  - **Pearson Correlation test** (`stats.pearsonr`): Kiểm định giá trị $p$ và khoảng tin cậy 95% của hệ số tương quan với G3.
  - **Fisher's Exact Test** (`stats.fisher_exact`): Kiểm định tỉ lệ trượt giữa nhóm rủi ro Medium so với Low trên cỡ mẫu nhỏ.
  - **Wilson Score Interval** (`stats.binomtest`): Tính khoảng tin cậy 95% cho các tỉ lệ (độ nhạy Recall, độ chuẩn xác Precision).

### 4. `matplotlib` (`matplotlib.pyplot` >= 3.7)
- **Nhiệm vụ:** Trực quan hóa dữ liệu và xuất toàn bộ 4 biểu đồ trong thư mục `images/`:
  - `01_bar_studytime_internet.png`: Biểu đồ cột nhóm kết hợp thanh sai số 95% CI (error bar).
  - `02_hist_g3.png`: Histogram phân phối điểm G3, tô màu đỏ riêng cho nhóm bỏ thi $G3=0$.
  - `03_heatmap_corr.png`: Ma trận nhiệt tương quan dùng dải màu phân kỳ `RdBu_r`, che nửa tam giác trên.
  - `04_pisa_portugal_oecd.png`: Biểu đồ đường 3 ô so sánh điểm PISA của Bồ Đào Nha với trung bình OECD từ 2000–2025.
  - Thiết lập cấu hình `matplotlib.use("Agg")` trong `main.py` để chạy ngầm và xuất file ảnh PNG mà không mở cửa sổ GUI.

### 5. `requests` (>= 2.31)
- **Nhiệm vụ:** Giao tiếp mạng (HTTP Client).
  - Tự động tải file zip chứa dữ liệu gốc `student+performance.zip` từ kho lưu trữ của UCI khi máy chưa có dữ liệu.
  - Gửi HTTP GET request lên Wikipedia để cào mã nguồn HTML bài viết PISA, kèm tiêu đề định danh `User-Agent` tuân thủ nghiêm ngặt chính sách của Wikimedia (chứa tên công cụ, đường dẫn GitHub repo và email liên hệ `mailto:vohoangquocminh2k5@gmail.com`).
### 6. `beautifulsoup4` (`bs4.BeautifulSoup` >= 4.12)
- **Nhiệm vụ:** Bóc tách dữ liệu từ trang web (HTML Parser).
  - Phân tích cây cấu trúc DOM của trang Wikipedia PISA, tìm các thẻ bảng `table.wikitable`.
  - Bóc tách cấu trúc bảng lồng nhau của bảng tóm tắt 2025 và chuyển đổi bảng so sánh lịch sử 2000–2022 từ dạng rộng sang dạng dài (wide to long).

### 7. `pytest` (>= 8.0)
- **Nhiệm vụ:** Bộ công cụ kiểm thử phần mềm tự động (Unit Test).
  - Chạy 51 ca kiểm thử tự động trong thư mục `tests/` để đảm bảo code hoạt động chính xác: kiểm tra điểm biên đỗ/trượt, tính độc lập của rule rủi ro với G3, độ chính xác của cào dữ liệu PISA, kiểm thử hồi quy OLS, đối chứng holdout, ghép cặp 2 môn, chuẩn User-Agent Wikimedia, file đối chiếu DevTools, xuất file theo môn, chống rò rỉ biến mục tiêu và bắt lỗi thiếu file OECD.

### 8. `notebook` / `jupyter` / `IPython`
- **Nhiệm vụ:** Môi trường thực thi file sổ tay tương tác `analysis.ipynb`.
  - Trình bày toàn bộ quy trình Data Science từng bước: từ thu thập, làm sạch, EDA, vẽ biểu đồ đến kiểm định giả thuyết và nhận định kết quả.

---

## 6. Bản đồ mã nguồn & Chi tiết các đoạn code xử lý (Code Architecture)

Dưới đây là chi tiết từng file, từng hàm và các đoạn code cụ thể chịu trách nhiệm xử lý các nghiệp vụ trong project. *Số dòng đúng với code ngày 2026-10-13; nếu sửa code thì số dòng sẽ dịch, nên tra theo **tên hàm** là chắc nhất.*

### 6.1 `main.py` — File điều phối chính (Entry Point)
- **Dòng 5–7:** Thiết lập `matplotlib.use("Agg")` ngay trước khi import để đảm bảo khi chạy script bằng dòng lệnh, hệ thống chỉ xuất file ảnh PNG ngầm, không mở cửa sổ đồ họa GUI làm đơ ứng dụng.
- **Dòng 21–25:** Khởi tạo bộ đọc tham số `argparse`, hỗ trợ cờ lệnh `python main.py --refresh-pisa` khi muốn chủ động cào mới lại dữ liệu từ Wikipedia.
- **Dòng 27–36:** Gọi `fetch_uci_raw(RAW)` để tải data UCI (nếu thiếu) và `scrape_pisa_table(...)` để đọc bảng PISA (ưu tiên đọc file cache offline).
- **Dòng 38–68:** Thực thi quy trình Data Science chuẩn 4 bước của `StudentDataProcessor`: `load_data()` $\rightarrow$ `clean_data()` $\rightarrow$ `analyze()` $\rightarrow$ `export_results()`, in kết quả kiểm định, holdout và đối chiếu OECD.
- **Dòng 70–71:** Gọi `build_reports(proc, ROOT)` để tự động sinh 2 file báo cáo chi tiết `report.md` và `report_vi.md`.

---

### 6.2 `data_processor.py` — Trọng tâm xử lý dữ liệu & Thuật toán

File này gồm 5 khối chức năng lớn:

#### 🔹 Khối 1: Cấu hình ngưỡng & Miền giá trị (Dòng 27–110)
- **Dòng 31–32 (`THRESHOLDS`):** Tuple bất biến chứa các ngưỡng cơ bản: điểm đỗ `PASS_MARK = 10`, cảnh báo trượt `G_WARN = 10`, vắng trung bình `ABS_MED = 4`, vắng cao `ABS_HIGH = 10`, số lần trượt cao `FAIL_HIGH = 2`.
- **Dòng 35–36 (`ANOMALY_THRESHOLDS`):** Ngưỡng phát hiện dị biệt: hệ số `IQR_K = 1.5`, tụt điểm `G1_DROP = 8`, `G2_DROP = 6`, tuổi lưu ban `AGE_OUTLIER = 20`.
- **Dòng 39–50 (`PISA_CHECKS`, `ALPHA` & các biến kiểm định):** Ngưỡng kiểm định bảng PISA (tối thiểu 30 nước/kỳ, điểm từ 200–700), mức ý nghĩa $\alpha = 0.05$, danh sách biến đưa vào t-test/ANOVA/tương quan, `TEST_LEVEL_CAP` (gộp mức trượt 2 và 3 thành "2+" khi kiểm định) và `MIN_RELIABLE_N = 10` (cột ít hơn 10 học sinh trên biểu đồ 1 bị gạch chéo).
- **Dòng 53–60 (`MERGE_KEYS` & `REG_FACTORS`):** 13 thuộc tính định danh học sinh trùng giữa 2 môn và danh sách 13 biến số đưa vào mô hình hồi quy đa biến OLS.
- **Dòng 65–67 (`OECD_NAME_ALIASES`):** Ánh xạ 5 tên nước khác nhau giữa báo cáo OECD và Wikipedia.
- **Dòng 69–106 (`VAR_DESCRIPTIONS`, `VALID_RANGES`, `REQUIRED_COLS`, `YES_NO_COLS`, `FLAG_COLS`, `SAMPLE_STUDENTS`):** Dict mô tả biến, miền giá trị hợp lệ của 16 cột số (theo `student.txt`), các cột bắt buộc, cột yes/no, tên 6 cờ bất thường và list of dicts học sinh mẫu.

#### 🔹 Khối 2: 4 hàm cơ bản & Rule phân loại rủi ro (Dòng 112–156)
- **Dòng 112–119 (`convert_yes_no`):** Mã hoá chuỗi `"yes"` $\rightarrow 1$, `"no"` $\rightarrow 0$, chuỗi lạ/trống $\rightarrow None$.
- **Dòng 122–124 (`calc_pass_fail`):** Điểm cuối kỳ $G3 \ge 10 \rightarrow$ `"pass"`, ngược lại $\rightarrow$ `"fail"`.
- **Dòng 127–134 (`classify_absences`):** Phân loại số buổi vắng thành 3 mức: `"low"` (0–3), `"medium"` (4–9), `"high"` ($\ge 10$).
- **Dòng 137–139 (`calc_average_grade`):** Tính trung bình cộng 3 kỳ $(G1 + G2 + G3) / 3$ (chỉ dùng mô tả, không dùng dự báo vì dính G3).
- **Dòng 142–156 (`classify_risk`):** **Quy tắc cảnh báo sớm rủi ro trượt môn** (hoàn toàn không dùng G3 để tránh rò rỉ dữ liệu):
  - `"high"`: nếu $G2 < 10$ hoặc từng trượt $\ge 2$ môn.
  - `"medium"`: nếu $G1 < 10$ hoặc từng trượt 1 môn hoặc vắng học mức cao.
  - `"low"`: các trường hợp còn lại.

#### 🔹 Khối 3: Thu thập, Cào & Kiểm định dữ liệu Web (Dòng 165–416)
- **Dòng 172–175 (`HTTP_HEADERS`):** Định danh `User-Agent` tuân thủ Wikimedia policy, khai báo repo GitHub và email tác giả.
- **Dòng 179–192 (`fetch_uci_raw`):** Tải file nén `student+performance.zip` từ UCI qua `requests` và giải nén lấy các file CSV.
- **Dòng 203–257 (`_parse_pisa_html`):** Dùng `BeautifulSoup` bóc tách cây DOM của Wikipedia: lấy bảng tóm tắt xếp hạng 2025 và chuyển bảng so sánh lịch sử 2000–2022 từ dạng ngang nhiều năm sang dạng dọc (wide-to-long).
- **Dòng 264–296 (`validate_pisa_raw`):** Thuật toán kiểm tra tính toàn vẹn của bảng PISA: đảm bảo đủ 3 môn, năm thi từ 2000 trở đi, điểm từ 200–700, có dòng trung bình OECD, không trùng lặp nước. Bảng lỗi sẽ bị từ chối ngay.
- **Dòng 315–353 (`scrape_pisa_table`):** Cơ chế **Cache-first**: ưu tiên đọc file raw đã lưu `pisa_reference.csv`; nếu mất mạng hoặc cào lỗi thì tự động fallback về cache cũ mà không làm sập chương trình.
- **Dòng 356–372 (`clean_pisa`):** Làm sạch bảng PISA: bỏ ký tự trích dẫn `[41]`, bỏ dấu sao `*` sau tên nước, ép kiểu số, chuẩn hoá tên `OECD average`.
- **Dòng 375–416 (`cross_check_pisa`):** Đối chiếu dữ liệu Wikipedia với bảng chính thức Table I.1 của OECD: so khớp điểm năm 2025 và suy diễn điểm 2022 qua mức thay đổi (cho phép sai số làm tròn $\pm 1$).

#### 🔹 Khối 4: Thuật toán thống kê, OLS & Đánh giá rủi ro (Dòng 422–643)
- **Dòng 422–427 (`_grp`):** Tiện ích gom nhóm tính `mean`, `std`, `count`.
- **Dòng 438–444 (`_holm`):** Thuật toán hiệu chỉnh đa kiểm định Holm-Bonferroni: kiểm soát tỷ lệ sai số loại I cho cả họ giả thuyết ở mức $\alpha = 0.05$.
- **Dòng 447–491 (`_group_tests`):** Chạy kiểm định Welch t-test (kèm khoảng tin cậy 95% và Cohen's d) cho biến nhị phân; chạy ANOVA một chiều (kèm $\eta^2$) và Kruskal-Wallis cho biến nhiều mức (số lần trượt 2 và 3 được gộp thành "2+" vì mỗi mức chỉ khoảng chục học sinh).
- **Dòng 494–502 (`_corr_tests`):** Tính tương quan Pearson với G3 kèm khoảng tin cậy 95% và p-value.
- **Dòng 505–533 (`_ols`):** Thuật toán hồi quy OLS ma trận tự code: tính hệ số $\beta = (X^T X)^{-1} X^T y$, đòn bẩy $H$, ma trận hiệp phương sai sai số vững **HC3**, tra phân phối Student-t ra p-value và khoảng tin cậy 95% của từng hệ số.
- **Dòng 537–566 (`_paired_subjects`):** Ghép cùng một học sinh ở 2 môn theo `MERGE_KEYS` (bỏ các key bị lặp trong cùng file), rồi so G3 bằng t-test ghép cặp và Wilcoxon, vì 2 file Toán và Bồ Đào Nha không phải 2 mẫu độc lập.
- **Dòng 569–594 (`_scope_stats`):** Gom toàn bộ thống kê của một tập dữ liệu (tỉ lệ đỗ, các bảng groupby, ma trận tương quan, kết quả kiểm định) vào một dict.
- **Dòng 597–602 (`_wilson`):** Tính khoảng tin cậy Wilson 95% cho các tỷ lệ nhị thức.
- **Dòng 605–624 (`_risk_eval`):** Lập bảng ma trận nhầm lẫn (Confusion Matrix) tính độ nhạy Recall và độ chuẩn xác Precision kèm khoảng tin cậy Wilson.
- **Dòng 627–643 (`_tier_eval`):** Đo lường tỷ lệ trượt của từng phân tầng rủi ro và chạy kiểm định chính xác Fisher kiểm tra xem nhóm Medium có thực sự rủi ro hơn Low không.

#### 🔹 Khối 5: Class hướng đối tượng `StudentDataProcessor` (Dòng 646–1043)
- **Dòng 667–678 (`load_data`):** Đọc cả 2 file `student-mat.csv` và `student-por.csv`, gắn cột `subject`, nạp file PISA và file OECD.
- **Dòng 681–744 (`clean_data`):** Quy trình làm sạch 6 bước triệt để:
  1. Cắt khoảng trắng các cột chuỗi (`strip`).
  2. Ép kiểu số và soi theo `VALID_RANGES`.
  3. Mã hoá nhị phân `convert_yes_no`.
  4. Xóa dòng trùng (`drop_duplicates`) và xóa dòng thiếu điểm bắt buộc (`dropna`).
  5. Tạo cột dẫn xuất (`pass_fail`, `absence_level`, `avg_grade`, `avg_g1g2`, `risk_group`). Cột `avg_grade` được gắn cờ chỉ dùng mô tả vì dính target G3 (tránh rò rỉ dữ liệu).
  6. Gắn 6 nhãn cờ dữ liệu bất thường (tính ngưỡng vắng học IQR theo từng môn). Ghi log toàn bộ vào `cleaning_log`.
- **Dòng 747–789 (`analyze`):** Điều phối phân tích thống kê trên 2 tập `all` và `exclude_dropout`, gọi hồi quy, độ nhạy, holdout, so sánh ghép cặp 2 môn và vẽ biểu đồ.
- **Dòng 791–802 (`_regression`):** Chạy 2 mô hình OLS: Mô hình A (13 yếu tố nền) và Mô hình B (thêm G1, G2) cho cả 2 môn.
- **Dòng 804–839 (`_sensitivity`):** Phân tích độ nhạy của biến vắng học trên 3 kịch bản xử lý điểm 0 và vắng 0.
- **Dòng 841–857 (`_risk_holdout`):** Thử nghiệm rule rủi ro ngoài mẫu (Out-of-sample) trên môn Bồ Đào Nha (cả tập đầy đủ và tập holdout chặt không trùng học sinh).
- **Dòng 859–890 (`_subject_comparison`, `_pisa_context`):** So sánh 2 môn (tỉ lệ đỗ, tương quan chính) và trích điểm PISA của Bồ Đào Nha so với trung bình OECD theo từng năm.
- **Dòng 892–1019 (Các hàm vẽ biểu đồ, `_plot_charts` gọi lần lượt):**
  - `_save_fig` (Dòng 900–910): Tiện ích lưu ảnh chuẩn, tự động bắt lỗi `PermissionError` nếu file PNG đang bị trình xem ảnh khoá.
  - `_plot_bar` (Dòng 912–946): Vẽ Biểu đồ 1 (cột nhóm studytime $\times$ internet, 95% CI error bar; cột dưới 10 học sinh bị gạch chéo, làm mờ).
  - `_plot_hist` (Dòng 948–969): Vẽ Biểu đồ 2 (histogram G3, tô đỏ cột điểm 0, vạch đứt mốc 10).
  - `_plot_heatmap` (Dòng 971–989): Vẽ Biểu đồ 3 (ma trận nhiệt tương quan RdBu_r che nửa trên).
  - `_plot_pisa` (Dòng 991–1019): Vẽ Biểu đồ 4 (đường xu hướng 3 môn Bồ Đào Nha vs OECD từ 2000–2025).
- **Dòng 1022–1043 (`export_results`):** Xuất song song 3 file CSV: `cleaned_students.csv` (1044 dòng hợp nhất), `cleaned_students_mat.csv` (395 dòng môn Toán) và `cleaned_students_por.csv` (649 dòng môn Văn), cùng `pisa_clean.csv` và `summary.json`. Bắt lỗi `PermissionError` trên toàn bộ file nếu đang bị mở bên Excel/WPS.
### 6.3 `report_builder.py` — Bộ sinh báo cáo Markdown tự động

- **Dòng 30–47 (`code` & `code_region`):** Dùng thư viện `inspect` đọc trực tiếp mã nguồn thật từ file `.py` kèm số dòng thực tế để nhúng vào báo cáo, đảm bảo báo cáo không bao giờ bị lệch code so với thực tế.
- **Dòng 72–135 (`_facts`):** Trích xuất toàn bộ chỉ số thống kê, kết quả kiểm định, mô hình OLS, tỷ lệ holdout và độ nhạy từ `proc.results` thành một từ điển sự thật duy nhất (single source of truth).
- **Dòng 138–426:** Các hàm dựng câu chữ và bảng Markdown: `_fail_steps`/`_fail_steps_text` (mức tụt điểm theo số lần trượt), `_paired_text` (mục 10.1: 2 môn không độc lập + so sánh ghép cặp), `_portugal_check`, `_reg_rows` (hệ số hồi quy), `_sens_rows` (độ nhạy), `_tier_rows` (3 nhóm rủi ro), `_oecd_rows` (đối chiếu OECD), `_pisa_rows`, `_test_rows` (kiểm định), `_corr_rows`, `_holdout_rows`, `_clean_rows`, `_flag_rows`.
- **Dòng 432–995 (`render_en`):** Sinh toàn bộ nội dung báo cáo tiếng Anh `report.md`.
- **Dòng 1001–1556 (`render_vi`):** Sinh toàn bộ nội dung báo cáo tiếng Việt `report_vi.md`.
- **Dòng 1562–1596 (`_codes`, `build_reports`):** Gom các đoạn code cần nhúng, kiểm tra đủ dữ liệu PISA và file OECD (thiếu thì báo lỗi rõ tên file, không ghi report), rồi ghi đè 2 file báo cáo ra thư mục gốc sau mỗi lần chạy pipeline.

---

### 6.4 `export_pdf.py` — Bộ xuất báo cáo PDF chuẩn in ấn A4
- **Dòng 31–50 (`CSS`):** Định dạng trang in chuẩn A4 (căn lề 16mm, font chữ Segoe UI/Consolas hỗ trợ 100% tiếng Việt có dấu, quy định ngắt trang thông minh tránh làm đứt đôi hình ảnh hay hàng của bảng biểu).
- **Dòng 53–60 (`_highlight`):** Tích hợp Pygments tô màu cú pháp (Syntax Highlighting) cho tất cả các khối code Python trong file báo cáo.
- **Dòng 63–67 (`md_to_html`):** Dùng `markdown-it-py` biên dịch Markdown (chuẩn CommonMark hỗ trợ bảng biểu) sang HTML trung gian.
- **Dòng 70–87 (`find_browser`, `html_to_pdf`):** Tự động phát hiện trình duyệt Chrome/Edge trên máy và chạy ở chế độ ngầm (`--headless=new`, `--print-to-pdf`) để xuất ra 2 file PDF chất lượng cao: `report.pdf` và `report_vi.pdf`.

---
### 6.5 Thư mục `tests/` — Hệ thống 51 ca kiểm thử tự động (Unit Tests)
- **`conftest.py`:** Khởi tạo dữ liệu mẫu: lấy 6 dòng dữ liệu thật từ `student-mat.csv` làm phôi thử nghiệm và tạo hàm `valid_pisa_raw()` dựng bảng PISA nhỏ nhất đạt chuẩn.
- **`test_report_builder.py` (1 ca test):** Thiếu file OECD thì `build_reports` báo lỗi ghi rõ tên file và không ghi report nào.
- **`test_data_processor.py` (50 ca test):**
  - **Test tính độc lập của Rule rủi ro:** Đảm bảo hàm `classify_risk` chỉ nhìn G1, G2, số lần trượt, số buổi vắng mà không đổi kết quả khi thay đổi G3.
  - **Test thống kê:** Kiểm tra thuật toán Holm đảm bảo tính đơn điệu và chặn trên 1.0; kiểm tra khoảng tin cậy Wilson.
  - **Test cào PISA:** Kiểm tra parser đọc đúng HTML mẫu, hàm validation bắt trúng 6 dạng lỗi cấu trúc bảng, cơ chế cache-first không gọi mạng khi đã có file.
  - **Test làm sạch dữ liệu:** Kiểm thử trên 6 dòng cố ý cấy lỗi (tuổi 30, yes/no lạ, dòng trùng, thừa khoảng trắng) xem code có đếm và xử lý chính xác không.
  - **Test mô hình OLS:** Chạy thử nghiệm trên dữ liệu giả lập có biến nhiễu để đảm bảo thuật toán OLS tự viết ước lượng chính xác hệ số thật.
  - **Test kiểm chứng Holdout:** Đảm bảo tập holdout chặt loại bỏ đúng các học sinh học chung cả 2 môn Toán và Bồ Đào Nha.
  - **Test ghép cặp 2 môn:** Đảm bảo `_paired_subjects` chỉ ghép đúng cùng một học sinh, bỏ các key bị lặp và các cặp có G3 = 0.
  - **Test gộp nhóm nhỏ:** Đảm bảo khi kiểm định, mức trượt 2 và 3 được gộp thành "2+".
  - **Test User-Agent Wikimedia:** Kiểm tra User-Agent chứa link repo và email liên hệ theo đúng chính sách Wikimedia.
  - **Test đối chiếu DevTools:** Kiểm tra file `data/raw/pisa_manual_check.csv` tồn tại và đúng cấu trúc bảng Toán 2025.
  - **Test xuất file tách môn:** Đảm bảo `export_results` xuất song song cả file hợp nhất và 2 file riêng cho từng môn `mat` và `por`.
  - **Test cảnh báo rò rỉ biến mục tiêu:** Kiểm tra hàm `calc_average_grade` và mô tả biến luôn có cảnh báo chống target leakage đối với G3.
