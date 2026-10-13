# Báo cáo P1 — Các yếu tố ảnh hưởng đến điểm cuối kỳ (UCI Student Performance, `mat`)

*Bản tóm tắt. Báo cáo đầy đủ (dữ liệu, code, biểu đồ, kiểm định): `report_vi.pdf`.*

**Câu hỏi chính:** Thời gian tự học, số buổi vắng, hỗ trợ từ gia đình và điểm giữa kỳ (G1, G2) liên quan
thế nào đến điểm cuối kỳ (G3)?

## 1. Tóm tắt

| Câu hỏi | Trả lời (môn Toán, 357 học sinh có G3 > 0, trừ khi ghi khác) |
|---|---|
| Điểm giữa kỳ → G3 | Liên hệ mạnh nhất: r(G2, G3) = **0.966**, r(G1, G3) = 0.892 |
| Số lần trượt trước → G3 | 0 lần: **11.94**, 1: 10.15, 2: 8.83, 3: 8.27 (r = -0.294) |
| Vắng học → G3 | thấp 12.26 / trung bình 11.38 / cao 10.37 (r = **-0.213**, ANOVA p Holm < 0.001) |
| Thời gian tự học → G3 | dương nhưng yếu, r = 0.127 (ANOVA p Holm 0.019, eta² = 0.036: rất nhỏ) |
| Internet ở nhà → G3 | có 11.68 vs không 10.71; p gốc 0.027, p Holm 0.080 → **không còn ý nghĩa sau hiệu chỉnh** |
| Xét tất cả yếu tố cùng lúc (hồi quy) | các yếu tố nền giải thích R² = 0.234; có ý nghĩa ở cả 2 môn khi giữ các yếu tố khác cố định: **studytime (+1 mức), failures (+1 lần trượt), absences (+1 buổi vắng), schoolsup (có vs không)**; internet sau điều chỉnh b = +0.53 (p 0.247) |
| Hỗ trợ gia đình (`famsup`) → G3 | có 11.35 vs không 11.8 (p Holm 0.404): **không có khác biệt có ý nghĩa** |
| Tỉ lệ đỗ | 67.1% trên toàn bộ 395 học sinh; 74.2% sau khi bỏ 38 em nghi bỏ thi |
| Rule cảnh báo sớm (không dùng G3) | đặt trên mat: recall 93.8%, precision 81.9%; **kiểm tra trên học sinh môn Bồ Đào Nha chưa từng thấy: recall 91.4%, precision 66.0%** |

**Phát hiện quan trọng về chất lượng dữ liệu:** 38 học sinh có G3 = 0 và **38 em trong số đó có
0 buổi vắng được ghi nhận**. Nhóm này được gắn cờ *dropout suspect* (nghi bỏ thi), không xoá. Nếu để lẫn vào, tương quan
vắng học–G3 thành r = 0.034 và che mất ảnh hưởng tiêu cực thật sự của vắng học.

## 2. Giới hạn và hướng tiếp theo

- Chỉ 1 môn / 1 năm học làm nhóm chính; các nhóm nhỏ (xem nhãn `n=` ở Biểu đồ 1) có khoảng tin cậy rộng.
- Hồi quy chỉ điều chỉnh cho các biến có trong dữ liệu; các yếu tố không đo được (động lực, giáo viên, thu nhập) vẫn có thể gây nhiễu, nên đây là quan hệ tương quan, không phải nhân quả.
- "Nghi bỏ thi" là suy luận từ dữ liệu, chưa được trường xác nhận; phân tích độ nhạy (6.1) cho thấy kết luận về vắng học không phụ thuộc vào giả định này.
- Tập holdout cùng trường, cùng năm học với dữ liệu gốc, và holdout chặt khá nhỏ (n = 275); precision ở trường khác có thể khác.
- Điểm PISA 2025 và 2022 đã đối chiếu với báo cáo OECD; các kỳ cũ hơn (2000–2018) chỉ dựa vào Wikipedia.
- Mọi kết luận là tương quan, không phải nhân quả.

*Tái tạo: `pip install -r requirements.txt` rồi `python main.py` (thêm `--refresh-pisa` để cào lại Wikipedia).*
