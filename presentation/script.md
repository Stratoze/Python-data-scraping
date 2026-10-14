# Kịch bản thuyết trình P1 (12–15 phút)

Viết chuẩn theo bộ slide `presentation/index.html` (22 slide). Văn phong mạch lạc, xưng "em", dùng được trực tiếp khi bảo vệ đồ án.

## Thời lượng

- Tổng cộng **1948 từ**. Nói tốc độ vừa phải, rõ chữ (135 từ/phút) mất đúng **14:26 phút**.
- Nói nhanh (145 từ/phút): 13:26. Nói chậm (125 từ/phút): 15:35.
- Cả 3 tốc độ đều nằm chắc chắn trong khung **12–15 phút**.

| Slide | Tiêu đề | Số từ | Thời gian | Cộng dồn |
|---|---|---|---|---|
| 1 | Bìa | 59 | 0:26 | 0:26 |
| 2 | Đặt vấn đề | 100 | 0:44 | 1:11 |
| 3 | Bố cục bài trình bày | 67 | 0:30 | 1:40 |
| 4 | Nguồn dữ liệu | 62 | 0:28 | 2:08 |
| 5 | Thu thập dữ liệu | 73 | 0:32 | 2:40 |
| 6 | Cấu trúc dữ liệu | 69 | 0:31 | 3:11 |
| 7 | Từ điển thuộc tính | 62 | 0:28 | 3:39 |
| 8 | Thống kê mô tả | 65 | 0:29 | 4:08 |
| 9 | Quy trình làm sạch | 55 | 0:24 | 4:32 |
| 10 | Làm sạch: bước 1–4 | 62 | 0:28 | 5:00 |
| 11 | Làm sạch: bước 5–6 | 74 | 0:33 | 5:32 |
| 12 | Kết quả làm sạch | 48 | 0:21 | 5:54 |
| 13 | Kiểm chứng bộ làm sạch | 78 | 0:35 | 6:28 |
| 14 | Trường hợp G3 = 0 | 161 | 1:12 | 7:40 |
| 15 | Biểu đồ 1: tự học và internet | 101 | 0:45 | 8:25 |
| 16 | Biểu đồ 3: tương quan Pearson | 108 | 0:48 | 9:13 |
| 17 | Kiểm định và hiệu chỉnh Holm | 139 | 1:02 | 10:15 |
| 18 | Quy tắc cảnh báo sớm | 126 | 0:56 | 11:11 |
| 19 | Kiểm chứng ngoài mẫu (holdout) | 130 | 0:58 | 12:08 |
| 20 | Bối cảnh PISA | 99 | 0:44 | 12:52 |
| 21 | Kết luận và đề xuất | 127 | 0:56 | 13:49 |
| 22 | Hỏi đáp và cảm ơn | 83 | 0:37 | 14:26 |

## Nếu bị quá giờ (cắt theo thứ tự này)

1. **Slide 3** (bố cục): bỏ, chỉ nói 1 câu: *"Sau đây em xin đi vào nội dung chi tiết."*
2. **Slide 12** (kết quả làm sạch): lướt qua trong 5 giây vì slide 10 đã nói kết quả là toàn bộ bằng 0.
3. **Slide 6 & 7**: mỗi slide chỉ nói 1 câu trọng tâm.
4. **Slide 13**: chỉ nói câu cấy lỗi và câu chốt *"43 bài kiểm thử đều đạt"*.

**Tuyệt đối KHÔNG cắt** slide 14 (G3 = 0), 17 (Holm) và 19 (holdout): đây là 3 slide giảng viên hỏi vấn đáp nhiều nhất.

## Nếu còn dư giờ

- **Slide 17**: phân tích sâu hơn ví dụ biến internet (xếp hạng 5 trong 7 kiểm định, hệ số phạt là 3, nên p ban đầu 0,0268 nhân 3 ra 0,0804 > 0,05, mất ý nghĩa).
- **Slide 19**: đọc thêm tỉ lệ trượt thực tế theo từng nhóm trên tập holdout chặt (High 66,0%, Medium 9,8%, Low 0,8%).

---

## Kịch bản chi tiết từng slide

### Slide 1 · Bìa (~0:26)

Kính thưa quý thầy cô, em tên là [họ tên em]. Hôm nay em xin trình bày đồ án P1: phân tích các yếu tố ảnh hưởng đến kết quả học tập của học sinh trung học, trên dữ liệu UCI Student Performance từ hai trường ở Bồ Đào Nha, kết hợp dữ liệu PISA em cào từ Wikipedia.

### Slide 2 · Đặt vấn đề (~0:44)

Nhà trường muốn nhận diện sớm học sinh có nguy cơ trượt môn để can thiệp kịp thời. Câu hỏi nghiên cứu chính là: thời gian tự học, số buổi vắng, hỗ trợ gia đình và điểm giữa kỳ liên quan thế nào đến điểm cuối kỳ G3. Em phân tích chính trên 395 học sinh môn Toán, và dùng 649 học sinh môn Tiếng Bồ Đào Nha làm tập kiểm chứng. Em xin lưu ý đây là dữ liệu quan sát, nên các kết luận chỉ là mối liên hệ thống kê, không khẳng định quan hệ nhân quả.

### Slide 3 · Bố cục bài trình bày (~0:30)

*[Chỉ lướt qua cấu trúc 7 phần, không đọc từng mục.]*

Bài trình bày bám sát quy trình khoa học dữ liệu gồm 7 phần: từ bài toán, thu thập, làm sạch và kiểm soát chất lượng, đến phân tích khám phá, kiểm định thống kê, quy tắc cảnh báo sớm, đối chiếu PISA và cuối cùng là kết luận, đề xuất. Em sẽ dành nhiều thời gian nhất cho phần làm sạch và kiểm soát chất lượng.

### Slide 4 · Nguồn dữ liệu (~0:28)

*[Chỉ vào ô cam clean_data() ở sơ đồ pipeline cuối slide.]*

Đồ án kết hợp ba nguồn dữ liệu: Thứ nhất là UCI Student Performance dùng phân tích chính. Thứ hai là bảng xếp hạng PISA trên Wikipedia, được cào bằng requests và BeautifulSoup. Thứ ba là bảng chính thức của OECD dùng để đối chiếu xác thực dữ liệu cào. Toàn bộ quy trình chạy tự động bằng một lệnh python main.py.

### Slide 5 · Thu thập dữ liệu (~0:32)

Cả hai hàm thu thập chỉ gọi mạng khi cần. Với PISA, mặc định đọc bản lưu cục bộ để chạy ngoại tuyến. Khi cào mới, dữ liệu phải qua kiểm tra: đủ 3 môn, điểm từ 200 đến 700, ít nhất 30 nước mỗi bảng. Nếu trang lỗi hoặc cấu trúc thay đổi, chương trình giữ nguyên bản cũ, không ghi đè dữ liệu hỏng. Kết quả thu được 2342 dòng thô.

### Slide 6 · Cấu trúc dữ liệu (~0:31)

Về cấu trúc, đơn vị quan sát là một học sinh trong một môn học. Dữ liệu gồm hai file: môn Toán 395 dòng và môn Tiếng Bồ Đào Nha 649 dòng. Cả hai đều có 33 cột, thang điểm từ 0 đến 20, đỗ khi từ 10 điểm trở lên. Khi nạp vào, chương trình ghép thành bảng 1044 dòng và thêm cột subject để phân biệt môn.

### Slide 7 · Từ điển thuộc tính (~0:28)

33 thuộc tính chia làm 5 nhóm: nhân khẩu học, bối cảnh gia đình, thói quen học tập, hỗ trợ ngoài trường, và quá trình học tập gồm số lần trượt, số buổi vắng cùng điểm G1, G2, G3. Miền giá trị chuẩn từ file student.txt của UCI là căn cứ thiết lập các ngưỡng kiểm tra lỗi ở bước làm sạch.

### Slide 8 · Thống kê mô tả (~0:29)

*[Chỉ vào số liệu absences max = 75 và G3 min = 0.]*

Thống kê mô tả môn Toán cho thấy hai điểm định hướng khâu làm sạch: Thứ nhất, số buổi vắng lệch phải mạnh, trung vị 4 buổi nhưng có em vắng tới 75 buổi. Thứ hai, điểm cuối năm G3 có giá trị nhỏ nhất là 0, trong khi G1 thấp nhất là 3. Đây là dấu hiệu bất thường em sẽ phân tích riêng.

### Slide 9 · Quy trình làm sạch (~0:24)

Quy trình làm sạch 6 bước nằm trong hàm clean_data theo ba nguyên tắc: Không sửa đoán — giá trị sai phạm vi chuyển thành rỗng. Không xoá dữ liệu bất thường mà chỉ gắn cờ cảnh báo để giữ nguyên mẫu. Và mọi thao tác đều được đếm, ghi vết vào nhật ký cleaning_log.

### Slide 10 · Làm sạch: bước 1–4 (~0:28)

*[Chỉ vào bảng nhật ký bên phải: toàn bộ cột lỗi đều bằng 0.]*

Bốn bước đầu xử lý hình thức: cắt khoảng trắng; ép kiểu số và kiểm tra miền hợp lệ; mã hoá yes/no thành 1 và 0, giá trị lạ để rỗng; loại bỏ dòng trùng và dòng thiếu cột bắt buộc. Kết quả trên bộ UCI là toàn bộ bằng 0, giữ nguyên 1044 dòng: dữ liệu sạch về mặt cú pháp.

### Slide 11 · Làm sạch: bước 5–6 (~0:33)

*[Nhấn mạnh cột avg_g1g2 tránh rò rỉ dữ liệu và cờ dropout_suspect.]*

Bước 5 tạo cột dẫn xuất: kết quả đỗ trượt, mức vắng mặt. Cột avg_grade chứa cả G3 nên chỉ dùng để mô tả; khi cần tính trung bình dự báo thì dùng avg_g1g2 để tránh rò rỉ dữ liệu. Bước 6 gắn 6 cờ bất thường, dùng ngưỡng IQR tính riêng từng môn để bắt outlier vắng mặt. Cờ quan trọng nhất là dropout_suspect: 38 học sinh môn Toán có G3 bằng 0.

### Slide 12 · Kết quả làm sạch (~0:21)

*[Chỉ vào 4 ô tóm tắt trên cùng: 1044 dòng, 53 cột, 3 file CSV.]*

Kết quả: 1044 dòng vào, 1044 dòng ra nguyên vẹn. Số cột tăng từ 33 lên 53 nhờ thêm các cột mã hoá, biến dẫn xuất và cờ cảnh báo. Dữ liệu sạch được xuất thành 3 file CSV, cùng nhật ký xử lý chi tiết trong summary.json.

### Slide 13 · Kiểm chứng bộ làm sạch (~0:35)

Vì bộ UCI không có lỗi cú pháp, con số 0 trong nhật ký chưa đủ chứng minh bộ làm sạch hoạt động. Em viết bài kiểm thử cấy lỗi vào 6 dòng thật: tuổi 30, yes/no lạ, khoảng trắng thừa, dòng trùng và G3 bằng 0. Bộ làm sạch đã phát hiện và đếm chính xác từng lỗi, lọc từ 7 dòng vào còn 5 dòng ra. Toàn bộ 43 unit test của dự án đều đạt.

### Slide 14 · Trường hợp G3 = 0 (~1:12)

*[Chỉ vào cột đỏ trên histogram và dòng hệ số tương quan đổi chiều (+0,034 thành −0,213).]*

Đây là phát hiện quan trọng nhất về chất lượng dữ liệu. 38 học sinh điểm 0 tách hẳn trên biểu đồ, không có em nào 1, 2 hay 3 điểm. Cả 38 em đều vắng 0 buổi, trong khi học sinh khác chỉ 21,6% vắng 0 buổi. Phân tích này dẫn đến suy luận: các em bỏ thi hoặc thôi học trước kỳ thi cuối, không phản ánh năng lực học tập thực. Đây là suy luận từ dữ liệu, chưa có xác nhận từ nhà trường. Em gắn cờ chứ không xoá bỏ. Lý do: nếu để nguyên 38 em này, tương quan giữa vắng mặt và điểm số bị đảo dấu thành dương 0,034 — tức vắng nhiều lại điểm cao hơn, trái thực tế. Khi tách 38 em ra, tương quan là âm 0,213, đúng chiều. Vì vậy, các kiểm định thống kê tiếp theo em đều chạy trên 357 học sinh có G3 lớn hơn 0.

### Slide 15 · Biểu đồ 1: tự học và internet (~0:45)

*[Chỉ vào chênh lệch 1 điểm ở nhóm internet và giá trị eta bình phương 0,036.]*

Biểu đồ 1 phân tích điểm G3 theo thời gian tự học và việc có internet. Về tự học, ANOVA có ý nghĩa sau hiệu chỉnh, nhưng eta bình phương chỉ 0,036 — thời gian tự học chỉ giải thích 3,6% biến thiên điểm số. Về internet, nhóm có internet điểm cao hơn khoảng 1 điểm, t-test cho p ban đầu là 0,027. Tuy nhiên sau hiệu chỉnh Holm thì p là 0,080, lớn hơn 0,05, tức chưa đủ bằng chứng kết luận. Các cột dưới 10 học sinh được vẽ gạch chéo cảnh báo và em không dùng kết luận.

### Slide 16 · Biểu đồ 3: tương quan Pearson (~0:48)

*[Chỉ vào các ô G2 (0,966), G1 (0,892) và failures (−0,294).]*

Biểu đồ 3 là ma trận tương quan Pearson trên 357 học sinh, đo mức liên hệ tuyến tính từ âm 1 đến dương 1. Điểm giữa kỳ G2 và G1 liên hệ rất mạnh với điểm cuối năm, lần lượt là 0,966 và 0,892. Trong các yếu tố khác, số lần trượt môn quá khứ liên hệ âm rõ nhất với âm 0,294, rồi đến số buổi vắng với âm 0,213. Hỗ trợ gia đình gần như không liên quan với r chỉ âm 0,067 và khoảng tin cậy bao trùm số 0. Tương quan chỉ phản ánh liên hệ quan sát, không khẳng định nhân quả.

### Slide 17 · Kiểm định và hiệu chỉnh Holm (~1:02)

*[Chỉ vào dòng internet: p 0,0268 nhân 3 thành p Holm 0,0804.]*

Để biết khác biệt là thật hay ngẫu nhiên, em dùng Welch t-test cho biến yes/no vì không giả định phương sai bằng nhau, và ANOVA cho biến nhiều mức. Chạy 7 kiểm định cùng lúc ở mức alpha 0,05 thì xác suất có ít nhất một dương tính giả lên tới khoảng 30%. Em dùng hiệu chỉnh Holm–Bonferroni kiểm soát sai số cho cả họ kiểm định bằng cách nhân phạt p theo thứ hạng. Sau hiệu chỉnh, chỉ 4 yếu tố có ý nghĩa: số lần trượt, phụ đạo ở trường, mức vắng và thời gian tự học. Internet, hỗ trợ gia đình và học thêm có phí đều không có ý nghĩa. Riêng phụ đạo mang dấu âm vì học sinh yếu mới được chọn vào phụ đạo, chứ không phải phụ đạo làm giảm điểm.

### Slide 18 · Quy tắc cảnh báo sớm (~0:56)

Phần ứng dụng là quy tắc phân nhóm rủi ro ba mức High, Medium, Low để cảnh báo sớm học sinh có nguy cơ trượt. Nguyên tắc cốt tử: chỉ dùng thông tin có trước kỳ thi cuối gồm G1, G2, số lần trượt, số buổi vắng, tuyệt đối không dùng G3 để tránh rò rỉ dữ liệu. Nhóm High kích hoạt khi G2 dưới 10 hoặc đã trượt từ hai lần; Medium khi G1 dưới 10, từng trượt, hoặc vắng từ 10 buổi; còn lại là Low. Trên môn Toán, tỉ lệ trượt của ba nhóm lần lượt là 81,9% ở nhóm High, 7,8% ở Medium và 1,2% ở Low, tương ứng ba mức hành động: can thiệp, theo dõi và chưa cần can thiệp.

### Slide 19 · Kiểm chứng ngoài mẫu (holdout) (~0:58)

*[Chỉ vào hai số: Recall giữ 91,4% và Precision giảm còn 66,0%.]*

Trên môn Toán, quy tắc bắt được 122 trên 130 em trượt, đạt Recall 93,8% và Precision 81,9%. Vì ngưỡng chọn khi nhìn môn Toán nên số này có phần lạc quan. Để kiểm chứng khách quan, em áp dụng quy tắc đã đóng băng sang môn Tiếng Bồ Đào Nha. Em thực hiện holdout chặt bằng 13 khoá MERGE_KEYS loại bỏ 374 học sinh học cả hai môn, chỉ giữ 275 học sinh hoàn toàn mới. Kết quả: Recall vẫn giữ mức 91,4%, tức bắt được 64 trên 70 em trượt. Precision giảm còn 66,0% vì tỉ lệ trượt nền ở môn Bồ Đào Nha thấp hơn. Với cảnh báo sớm, bỏ sót học sinh trượt tốn kém hơn hỗ trợ nhầm, nên em ưu tiên tối đa Recall.

### Slide 20 · Bối cảnh PISA (~0:44)

Dữ liệu PISA là số liệu vĩ mô cấp quốc gia, không ghép với từng học sinh. Ở kỳ 2006, điểm Toán của Bồ Đào Nha thấp hơn trung bình OECD 28 điểm; nhưng khoảng cách đã thu hẹp dần và tiệm cận trung bình OECD từ 2015. Đồng thời, để kiểm tra độ tin cậy của mã nguồn cào, em đối chiếu với bảng chính thức của OECD: năm 2025 khớp tuyệt đối 274 trên 274 điểm; năm 2022 có 208 trên 211 điểm trong dung sai 1 điểm do làm tròn, 3 sai khác đều thuộc Palestine.

### Slide 21 · Kết luận và đề xuất (~0:56)

Để trả lời câu hỏi chính: Điểm giữa kỳ G1 và đặc biệt G2 liên hệ mạnh nhất và là chỉ báo sớm tốt nhất cho điểm cuối năm. Trong các yếu tố phi học thuật, số lần trượt và số buổi vắng là hai bất lợi rõ nhất. Thời gian tự học có liên hệ nhưng hiệu ứng nhỏ. Hỗ trợ gia đình, internet và học thêm có phí không cho thấy khác biệt có ý nghĩa. Em đề xuất ba hành động: rà soát học sinh bằng quy tắc cảnh báo sớm ngay khi có G2; chủ động theo dõi từ đầu năm học sinh từng trượt môn hoặc vắng nhiều; và luôn kiểm tra tính chất của các điểm 0 trước khi phân tích.

### Slide 22 · Hỏi đáp và cảm ơn (~0:37)

*[Dừng slide ở đây trong suốt phần hỏi đáp.]*

Đồ án đã đi qua đủ quy trình khoa học dữ liệu: thu thập và cào PISA, làm sạch có kiểm soát với 43 bài kiểm thử đạt, phát hiện 38 trường hợp điểm 0 bất thường, kiểm định có hiệu chỉnh Holm, quy tắc rủi ro đạt Recall 91,4% trên tập kiểm chứng độc lập, và đối chiếu nguồn OECD. Em xin trân trọng cảm ơn quý thầy cô đã lắng nghe và rất mong nhận được câu hỏi từ hội đồng.

---

## Mẹo khi thuyết trình

- **Tương tác trực quan:** Mỗi slide chỉ chỉ vào 1 đến 2 con số/vùng biểu đồ trọng tâm (đã ghi chú cụ thể trong dấu `[...]`), không đọc lướt cả bảng biểu.
- **Phát âm chậm rãi các thuật ngữ chuyên môn:** `dropout_suspect`, `Holm–Bonferroni`, `Recall`, `Precision`, `Strict Holdout`, `IQR`.
- **Phản xạ câu hỏi vấn đáp:** Các công thức toán và ý nghĩa thực tế đã có sẵn trong `METHODS.md`, các câu hỏi vặn thường gặp nằm trong `QA.md`.
- **Trước giờ G:** Điền họ tên, MSSV, tên giảng viên hướng dẫn vào slide 1 trong `presentation/index.html`.
