# Báo cáo P1 — Các yếu tố ảnh hưởng đến điểm cuối kỳ (UCI Student Performance)

**Câu hỏi chính:** Thời gian tự học, số buổi vắng, hỗ trợ từ gia đình và điểm giữa kỳ (G1, G2) liên quan thế nào đến điểm cuối kỳ (G3)?

**Dữ liệu:** UCI Student Performance, 2 trường THPT ở Bồ Đào Nha (GP, MS), năm học 2005–06. Phân tích chính trên `student-mat.csv` (395 học sinh, môn Toán). `student-por.csv` (649 học sinh) dùng để thử quy tắc rủi ro trên học sinh mới. Bối cảnh: điểm PISA cào từ Wikipedia (2342 dòng thô → 1662 dòng sạch), đối chiếu với bảng chính thức Table I.1 của OECD PISA 2025 (2025: khớp 274/274; 2022: 208/211 lệch không quá ±1).

## 1. Thu thập và làm sạch dữ liệu

- **Thu thập:** `fetch_uci_raw` tải `student.zip` từ UCI nếu máy chưa có file gốc. `scrape_pisa_table` đọc các bảng PISA bằng `requests` + BeautifulSoup, kiểm tra bảng (đủ 3 môn, năm ≥ 2000, điểm 200–700, ≥ 30 nước, đúng 1 dòng trung bình OECD), rồi lưu cache vào `data/raw/pisa_reference.csv` (Wikipedia revision 1378067005).
- **Làm sạch (`clean_data`, 6 bước):** cắt khoảng trắng → ép kiểu số và kiểm tra miền giá trị hợp lệ từng cột (theo `student.txt`) → mã hoá yes/no thành 1/0 → bỏ dòng trùng và dòng thiếu cột bắt buộc → tạo cột dẫn xuất (`pass_fail`, `absence_level`, `avg_grade`, `avg_g1g2`, `risk_group`) → gắn 6 cờ bất thường (giữ nguyên dòng, không xoá).
- **Kết quả:** dữ liệu UCI gốc sạch về mặt kỹ thuật: 0 giá trị ngoài miền, 0 giá trị yes/no lạ, 0 dòng trùng, 0 dòng thiếu cột bắt buộc; giữ đủ 1044 dòng. `avg_grade` có chứa G3 nên chỉ dùng để mô tả, không bao giờ dùng để dự đoán G3.
- **Phát hiện chính về chất lượng dữ liệu:** 38 học sinh môn Toán có **G3 = 0**, và **cả 38 em đều có số buổi vắng = 0** (trong khi chỉ 21,6% học sinh còn lại vắng 0 buổi), điểm G1 trung bình 7,5. Nhiều khả năng các em bỏ thi cuối kỳ, nên được gắn cờ `dropout_suspect`. Nếu không gắn cờ, r(vắng, G3) đổi từ **−0,213** thành **+0,034** và che mất tác động thật. Các kết luận dưới đây dùng 357 học sinh có G3 > 0.

## 2. Kết quả (môn Toán, 357 học sinh)

| Yếu tố | Điểm G3 trung bình theo nhóm | Kiểm định (đã hiệu chỉnh Holm, α = 0,05) |
|---|---|---|
| Điểm giữa kỳ | — | r(G2, G3) = **0,966**, r(G1, G3) = 0,892 |
| Số lần trượt trước đó (0 / 1 / 2 / 3) | 11,94 / 10,15 / 8,83 / 8,27 | ANOVA p_holm < 0,001, η² = 0,089; r = −0,294 |
| Vắng học (thấp / vừa / cao) | 12,26 / 11,38 / 10,37 | ANOVA p_holm < 0,001, η² = 0,053; r = −0,213 |
| Tự học (<2h / 2–5h / 5–10h / >10h) | 11,47 / 11,07 / 12,56 / 12,67 | ANOVA p_holm = 0,019, nhưng η² = 0,036 (nhỏ) |
| Internet ở nhà (có / không) | 11,68 / 10,71 | Welch t-test p = 0,027 → p_holm = **0,080, không có ý nghĩa** |
| Gia đình hỗ trợ (có / không) | 11,35 / 11,80 | p_holm = 0,404, không khác biệt |
| Trường phụ đạo (có / không) | 9,62 / 11,83 | p_holm < 0,001; học sinh yếu mới được phụ đạo (quan hệ ngược chiều) |

- **Tỉ lệ đỗ:** 67,1% trên toàn bộ 395 học sinh; 74,2% sau khi bỏ 38 em nghi bỏ thi.
- **Quy tắc cảnh báo sớm** (`risk_group`, chỉ dùng G1, G2, số lần trượt, số buổi vắng, không bao giờ dùng G3): `high` = G2 < 10 hoặc trượt ≥ 2 lần. Trên môn Toán bắt được 93,8% số em trượt (precision 81,9%). Trên 275 học sinh môn Bồ Đào Nha không có trong file Toán vẫn bắt được **91,4%** (precision 66,0%). Tỉ lệ trượt theo nhóm (môn Toán): thấp 1,2%, vừa 7,8%, cao 81,9%.
- **Bối cảnh PISA:** năm 2006 Bồ Đào Nha thấp hơn trung bình OECD môn Toán (466 so với 494); bắt kịp vào năm 2015 (492 so với 490) và ngang mức năm 2025 (460 so với 463).

**Biểu đồ:** `images/01_bar_studytime_internet.png` (G3 trung bình theo tự học × internet, khoảng tin cậy 95%), `02_hist_g3.png` (phân phối G3, nhóm G3 = 0 tô đỏ), `03_heatmap_corr.png` (tương quan Pearson).

## 3. Giới hạn

- 2 trường, 1 năm học, dữ liệu cắt ngang: mọi kết quả là mối liên hệ, không phải quan hệ nhân quả.
- Tự học và vắng học là số liệu khai báo/ghi nhận theo mức; các yếu tố không đo được (động lực, giáo viên, thu nhập) không có trong dữ liệu.
- Nhãn "nghi bỏ thi" là suy luận từ dữ liệu, chưa được nhà trường xác nhận.
- Nhóm nhỏ cho trung bình không đáng tin (vd tự học > 10h mà không có internet: n = 3).
- Ngưỡng của quy tắc rủi ro được chọn trên môn Toán; tập holdout cùng trường và cùng năm học.
- PISA chỉ là bối cảnh cấp quốc gia, không ghép với từng học sinh; số liệu 2000–2018 chỉ lấy từ Wikipedia.

*Chạy lại: `pip install -r requirements.txt`, rồi `python main.py` (thêm `--refresh-pisa` để cào lại Wikipedia). Phân tích từng bước: `analysis.ipynb`.*
