# Kịch bản thuyết trình P1 (12–15 phút)

Viết theo bộ slide `presentation/index.html` (24 slide). Văn nói, xưng "em", dùng được trực tiếp.

## Thời lượng

- Tổng cộng **1786 từ**. Nói 140 từ/phút (vừa phải, rõ chữ) thì mất khoảng **12:45 phút**.
- Nói nhanh 160 từ/phút: 11:10. Nói chậm 120 từ/phút: 14:53.
- Số từ đếm bằng máy, còn tốc độ nói thật thì m cần tự đo: đọc to cả kịch bản một lần có bấm giờ rồi so với bảng dưới. Nếu vượt 15 phút thì dùng mục "Nếu bị quá giờ".

| Slide | Nội dung | Số từ | Thời gian | Cộng dồn |
|---|---|---|---|---|
| 1 | Bìa | 58 | 0:25 | 0:25 |
| 2 | Đặt vấn đề | 110 | 0:47 | 1:12 |
| 3 | Nội dung | 33 | 0:14 | 1:26 |
| 4 | Nguồn dữ liệu | 68 | 0:29 | 1:55 |
| 5 | Thu thập dữ liệu | 70 | 0:30 | 2:25 |
| 6–8 | Cấu trúc, thuộc tính, thống kê mô tả | 76 | 0:33 | 2:58 |
| 9 | Quy trình làm sạch | 43 | 0:18 | 3:16 |
| 10 | Làm sạch bước 1–4 | 69 | 0:30 | 3:46 |
| 11 | Làm sạch bước 5–6 | 72 | 0:31 | 4:17 |
| 12 | Kết quả làm sạch | 39 | 0:17 | 4:33 |
| 13 | Kiểm chứng làm sạch | 67 | 0:29 | 5:02 |
| 14 | Trường hợp G3 = 0 | 150 | 1:04 | 6:06 |
| 15 | Biểu đồ 1: tự học và internet | 108 | 0:46 | 6:53 |
| 16 | Biểu đồ 3: tương quan Pearson | 85 | 0:36 | 7:29 |
| 17 | Kiểm định và hiệu chỉnh Holm | 139 | 1:00 | 8:29 |
| 18 | Quy tắc cảnh báo sớm | 114 | 0:49 | 9:18 |
| 19 | Kiểm chứng ngoài mẫu (holdout) | 108 | 0:46 | 10:04 |
| 20 | Bối cảnh PISA | 88 | 0:38 | 10:42 |
| 21 | Mã nguồn và kiểm thử | 40 | 0:17 | 10:59 |
| 22 | Kết luận | 107 | 0:46 | 11:45 |
| 23 | Hạn chế | 84 | 0:36 | 12:21 |
| 24 | Cảm ơn | 58 | 0:25 | 12:45 |

## Nếu bị quá giờ (cắt theo thứ tự này)

1. **Slide 3** (nội dung): bỏ, chỉ nói 1 câu chuyển ý.
2. **Slide 12** (kết quả làm sạch): bỏ, vì slide 10 đã nói kết quả là toàn số 0.
3. **Slide 21** (đối chiếu mã nguồn): chỉ nói câu cuối "43 bài kiểm thử đều đạt".
4. **Slide 6–8**: rút còn 2 câu (mỗi dòng là một học sinh trong một môn; G3 có giá trị 0 sẽ nói sau).
5. **Slide 13**: chỉ nói câu cấy lỗi và câu "43 bài kiểm thử đều đạt".

**Ko cắt** slide 14, 17, 19: đây là 3 slide thầy cô hay hỏi nhất.

## Nếu còn dư giờ

- Slide 17: nói thêm ví dụ Holm cho internet. Nó xếp hạng 5 trong 7 kiểm định, hệ số nhân là 3, nên 0,0268 nhân 3 ra 0,0804.
- Slide 19: nói thêm tỉ lệ trượt theo nhóm trên holdout: high 66,0%, medium 9,8%, low 0,8%.

---

## Kịch bản từng slide

### Slide 1 · Bìa (~0:25)

Kính thưa quý thầy cô, em tên là [họ tên em]. Hôm nay em xin trình bày đồ án P1: phân tích các yếu tố ảnh hưởng đến kết quả học tập của học sinh trung học, trên dữ liệu UCI Student Performance từ hai trường ở Bồ Đào Nha, kèm dữ liệu PISA em cào từ Wikipedia.

### Slide 2 · Đặt vấn đề (~0:47)

Nhà trường muốn biết sớm học sinh nào có nguy cơ không đạt môn, thay vì chỉ biết sau kỳ thi cuối năm. Câu hỏi chính của đề là: thời gian tự học, số buổi vắng, hỗ trợ gia đình và điểm giữa kỳ liên quan thế nào đến điểm cuối kỳ, gọi là G3. Em phân tích chủ yếu trên môn Toán, 395 học sinh. Môn Tiếng Bồ Đào Nha, 649 học sinh, em dùng để thử lại quy tắc cảnh báo trên học sinh mới. Em xin lưu ý: đây là dữ liệu quan sát, nên em chỉ nói về mối liên hệ, không nói về nhân quả.

### Slide 3 · Nội dung (~0:14)

*[Lướt nhanh, không đọc từng mục.]*

Bài trình bày đi theo quy trình khoa học dữ liệu: thu thập, làm sạch, khám phá, kiểm định, ứng dụng, kết luận. Em dành nhiều thời gian nhất cho phần làm sạch.

### Slide 4 · Nguồn dữ liệu (~0:29)

*[Chỉ vào ô cam clean_data() ở sơ đồ cuối slide.]*

Đồ án dùng ba nguồn. Thứ nhất là UCI, nguồn phân tích chính. Thứ hai là các bảng xếp hạng PISA trên Wikipedia, được cào bằng requests và BeautifulSoup, đây là phần web scraping. Thứ ba là bảng của OECD, em không dùng để phân tích mà để kiểm tra xem dữ liệu cào có chính xác không. Toàn bộ quy trình chạy bằng một lệnh python main.py.

### Slide 5 · Thu thập dữ liệu (~0:30)

Cả hai hàm thu thập chỉ gọi mạng khi cần. Với PISA, mặc định chương trình đọc bản đã lưu nên mỗi lần chạy cho cùng kết quả. Khi cào mới, bảng phải qua bước kiểm tra: đủ ba môn, điểm trong khoảng 200 đến 700, ít nhất 30 nước mỗi bảng. Nếu dữ liệu hỏng, chương trình giữ bản cũ, không ghi đè. Kết quả là 2342 dòng thô.

### Slide 6–8 · Cấu trúc, thuộc tính, thống kê mô tả (~0:33)

*[Ba slide gộp làm một đoạn; bấm qua nhanh, dừng ở slide 8 phần G3 có giá trị 0.]*

Mỗi dòng dữ liệu là một học sinh trong một môn; hai file có cùng 33 cột, ghép lại thành 1044 dòng. Biến mục tiêu là G3, thang điểm 20, đỗ khi từ 10 trở lên. Từ thống kê mô tả em rút ra hai điều: số buổi vắng lệch phải mạnh, có em vắng tới 75 buổi; và G3 có giá trị 0 dù G1 thấp nhất là 3. Em sẽ quay lại điểm này.

### Slide 9 · Quy trình làm sạch (~0:18)

Phần làm sạch có sáu bước trong hàm clean_data, theo ba nguyên tắc. Không sửa đoán: giá trị sai chuyển thành rỗng. Không xoá dữ liệu bất thường mà chỉ gắn cờ. Và mỗi bước đều được đếm và ghi vào nhật ký.

### Slide 10 · Làm sạch bước 1–4 (~0:30)

*[Chỉ vào bảng kết quả bên phải: toàn số 0.]*

Bốn bước đầu: cắt khoảng trắng; ép kiểu số và kiểm tra miền giá trị, ví dụ tuổi phải từ 15 đến 22; mã hoá yes/no thành 1 và 0, giá trị lạ để rỗng chứ không ép thành 0; bỏ dòng trùng và dòng thiếu cột bắt buộc. Kết quả thực tế là tất cả bằng 0, giữ nguyên 1044 dòng: bộ UCI sạch về mặt hình thức.

### Slide 11 · Làm sạch bước 5–6 (~0:31)

Bước 5 tạo các cột dẫn xuất như đỗ trượt, mức vắng, nhóm rủi ro. Cột avg_grade có chứa G3 nên em chỉ dùng để mô tả, không dùng để dự đoán, tránh rò rỉ dữ liệu. Bước 6 gắn sáu cờ bất thường; ngưỡng số buổi vắng dùng phương pháp IQR, tính riêng từng môn. Cờ đáng chú ý nhất là dropout_suspect: 38 học sinh môn Toán có G3 bằng 0.

### Slide 12 · Kết quả làm sạch (~0:17)

*[Đọc nhanh 4 ô số ở trên.]*

Kết quả: 1044 dòng vào, 1044 dòng ra; số cột tăng từ 33 lên 53 nhờ cột mã hoá, cột dẫn xuất và cờ; dữ liệu sạch được xuất thành ba file, cùng nhật ký làm sạch trong summary.json.

### Slide 13 · Kiểm chứng làm sạch (~0:29)

Vì dữ liệu UCI không có lỗi hình thức, em chứng minh bộ làm sạch hoạt động bằng cách cấy lỗi vào sáu dòng thật: tuổi 30, yes/no lạ, khoảng trắng thừa, một dòng trùng và một điểm G3 bằng 0. Mỗi lỗi đều được đếm đúng, bảy dòng vào còn năm dòng ra như kỳ vọng. Cả 43 bài kiểm thử của dự án đều đạt.

### Slide 14 · Trường hợp G3 = 0 (~1:04)

*[Chỉ vào cột đỏ ở biểu đồ, rồi vào dòng tô nền trong bảng (+0,034 so với −0,213).]*

Đây là phát hiện quan trọng nhất của phần kiểm soát chất lượng. 38 học sinh điểm 0 tách hẳn khỏi phần còn lại: không có em nào được 1, 2 hay 3 điểm. Cả 38 em đều có số buổi vắng bằng 0, trong khi ở học sinh khác chỉ 21,6% vắng 0 buổi. Cách giải thích hợp lý là các em không dự thi hoặc đã thôi học. Em nhấn mạnh đây là suy luận từ dữ liệu, chưa được nhà trường xác nhận. Em không xoá mà gắn cờ, vì nếu tính gộp, tương quan giữa số buổi vắng và điểm là cộng 0,034, tức vắng nhiều lại có vẻ điểm cao hơn, một kết luận trái thực tế. Khi tách 38 em ra, tương quan là âm 0,213, đúng chiều. Vì vậy các kết luận sau đều dùng 357 học sinh có G3 lớn hơn 0.

### Slide 15 · Biểu đồ 1: tự học và internet (~0:46)

Biểu đồ 1 so sánh điểm trung bình theo thời gian tự học và việc có internet. Về tự học, ANOVA có ý nghĩa sau hiệu chỉnh, nhưng eta bình phương chỉ 0,036, nghĩa là tự học chỉ giải thích khoảng 3,6% sự khác nhau của điểm. Về internet, nhóm có internet cao hơn khoảng 1 điểm; kiểm định t cho p bằng 0,027, nhưng vì chạy nhiều kiểm định cùng lúc nên phải hiệu chỉnh, và sau hiệu chỉnh p là 0,080, lớn hơn 0,05. Vậy chưa đủ bằng chứng. Các cột dưới 10 học sinh được vẽ gạch chéo và em không dùng để kết luận.

### Slide 16 · Biểu đồ 3: tương quan Pearson (~0:36)

Biểu đồ 3 là ma trận tương quan Pearson; hệ số r cho biết chiều và độ mạnh của liên hệ, từ âm 1 đến dương 1. G2 và G1 liên hệ rất mạnh với G3, lần lượt 0,966 và 0,892. Trong các biến còn lại, số lần trượt trước đây liên hệ âm rõ nhất, âm 0,294, rồi đến số buổi vắng, âm 0,213. Hỗ trợ gia đình gần như không liên quan. Tương quan chỉ đo liên hệ, không khẳng định nhân quả.

### Slide 17 · Kiểm định và hiệu chỉnh Holm (~1:00)

*[Chỉ vào dòng internet (nền nổi bật): p 0,027 → p Holm 0,080.]*

Để biết các khác biệt là thật hay do ngẫu nhiên, em dùng Welch t-test cho biến yes/no và ANOVA cho biến nhiều mức. Em chạy 7 kiểm định cùng lúc, nên nếu không hiệu chỉnh thì xác suất có ít nhất một kết quả dương tính giả lên tới khoảng 30%. Vì vậy em dùng hiệu chỉnh Holm, nhân p với số kiểm định chưa được xác nhận. Sau hiệu chỉnh có bốn yếu tố có ý nghĩa: số lần trượt, phụ đạo ở trường, mức vắng và thời gian tự học. Internet, hỗ trợ gia đình và học thêm có trả phí thì không. Riêng phụ đạo cần thận trọng: nhóm được phụ đạo điểm thấp hơn, nhiều khả năng vì học sinh yếu mới được chọn phụ đạo, chứ không phải phụ đạo làm giảm điểm.

### Slide 18 · Quy tắc cảnh báo sớm (~0:49)

Phần ứng dụng là quy tắc phân nhóm rủi ro. Nguyên tắc quan trọng nhất là quy tắc chỉ dùng thông tin có trước kỳ thi cuối: G1, G2, số lần trượt, số buổi vắng, tuyệt đối không dùng G3, vì nếu dùng thì đánh giá bằng kết quả đỗ trượt không còn ý nghĩa. Nhóm high là G2 dưới 10 hoặc đã trượt từ hai lần; medium là G1 dưới 10, hoặc từng trượt, hoặc vắng từ 10 buổi; còn lại là low. Trên môn Toán, tỉ lệ trượt thực tế của ba nhóm là 81,9%, 7,8% và 1,2%, tương ứng ba mức hành động: can thiệp, theo dõi, chưa cần can thiệp.

### Slide 19 · Kiểm chứng ngoài mẫu (holdout) (~0:46)

*[Chỉ vào hai ô: 93,8% → 91,4% (giữ) và 81,9% → 66,0% (giảm).]*

Trên môn Toán, quy tắc cảnh báo được 122 trên 130 em trượt, recall 93,8%. Nhưng ngưỡng được chọn khi nhìn môn Toán nên con số này lạc quan. Vì vậy em kiểm chứng trên môn Bồ Đào Nha, chỉ giữ 275 học sinh không có trong file Toán và giữ nguyên ngưỡng. Kết quả: recall vẫn 91,4%, tức 64 trên 70 em trượt được cảnh báo. Precision giảm từ 81,9% xuống 66%, nghĩa là khoảng một phần ba số em bị cảnh báo vẫn đỗ. Với cảnh báo sớm, bỏ sót một học sinh sẽ trượt tốn kém hơn hỗ trợ thừa, nên em ưu tiên recall.

### Slide 20 · Bối cảnh PISA (~0:38)

Dữ liệu PISA là cấp quốc gia, em không ghép với từng học sinh. Ở kỳ 2006, gần thời điểm thu thập dữ liệu UCI, điểm Toán của Bồ Đào Nha thấp hơn trung bình OECD 28 điểm; khoảng cách thu hẹp dần và từ 2015 chỉ còn trong khoảng cộng trừ 3 điểm. Để kiểm tra dữ liệu cào, em đối chiếu với bảng chính thức của OECD: năm 2025 khớp 274 trên 274 điểm, năm 2022 có 208 trên 211 điểm trong dung sai 1 điểm.

### Slide 21 · Mã nguồn và kiểm thử (~0:17)

*[Slide để thầy cô đối chiếu; nói ngắn.]*

Slide này đối chiếu từng yêu cầu của đề với mã nguồn, từ bốn hàm cơ bản, các cấu trúc dữ liệu, lớp StudentDataProcessor đến web scraping. Dự án có 43 bài kiểm thử tự động, tất cả đều đạt.

### Slide 22 · Kết luận (~0:46)

Trả lời câu hỏi chính: điểm giữa kỳ G1, G2 liên hệ mạnh nhất với điểm cuối năm, G2 là chỉ báo sớm tốt nhất. Trong các yếu tố khác, số lần trượt trước đây bất lợi rõ nhất, rồi đến số buổi vắng. Thời gian tự học có liên hệ nhưng nhỏ. Hỗ trợ gia đình, internet và học thêm có phí không cho thấy khác biệt có ý nghĩa. Em đề xuất rà soát học sinh bằng quy tắc rủi ro ngay khi có G2, theo dõi sớm học sinh từng trượt hoặc vắng nhiều, và luôn kiểm tra điểm 0 trước khi phân tích.

### Slide 23 · Hạn chế (~0:36)

Về hạn chế: dữ liệu chỉ gồm hai trường trong một năm học nên kết quả là mối liên hệ chứ không phải nhân quả; nhãn nghi bỏ thi là suy luận; và tập holdout vẫn cùng trường, cùng năm học nên khả năng tổng quát còn hạn chế. Hướng phát triển là kiểm chứng trên dữ liệu trường khác, xác nhận nhãn bỏ thi với nhà trường, và thử các mô hình đa biến để so với quy tắc đơn giản hiện tại.

### Slide 24 · Cảm ơn (~0:25)

*[Dừng slide ở đây trong phần hỏi đáp.]*

Tóm lại, đồ án đã đi qua đủ quy trình: thu thập, làm sạch có kiểm soát, kiểm định có hiệu chỉnh, quy tắc cảnh báo đạt recall 91,4% trên tập độc lập, và đối chiếu dữ liệu cào với OECD. Em xin cảm ơn quý thầy cô đã lắng nghe và rất mong nhận được câu hỏi.

---

## Mẹo khi nói

- Mỗi slide chỉ chỉ vào 1 đến 2 chỗ chính (ghi trong dấu `[...]`), đừng đọc cả bảng.
- Các thuật ngữ nên nói chậm lại: **dropout_suspect**, **Holm**, **recall**, **precision**, **holdout**.
- Khi thầy cô hỏi vặn về công thức: `METHODS.md` giải thích từng phương pháp, `QA.md` có câu hỏi vấn đáp mẫu.
- Slide 1: điền họ tên, MSSV, giảng viên và tên học phần vào chỗ `[...]` trong `index.html` trước khi trình bày.
