# P1 — Plan sửa lỗi + mở rộng dữ liệu

Status: resolved

Số liệu dưới đây đo trực tiếp trên `data/raw/student-mat.csv` (n=395) và `data/processed/*` ngày 2026-10-12.

---

## 0. Đối chiếu đề bài

| Yêu cầu đề | Hiện trạng | Việc cần làm |
|---|---|---|
| 4 hàm cơ bản + list of dicts / dict / set / tuple | Đủ | — |
| Câu hỏi chính có **hỗ trợ gia đình (famsup)** | **Thiếu**: không có groupby famsup/schoolsup/paid | Mục 1.4 |
| "Thu thập UCI" (ucimlrepo hoặc tải `student.zip`) | Raw CSV có sẵn, code không tự tải | Mục 2.7 |
| `StudentDataProcessor.load_data/clean_data/analyze/export_results` | Đủ | Sửa logic bên trong (mục 1–3) |
| `main.py` → `cleaned_students.csv` + `summary.json` | Đủ | Chạy lại sau khi sửa |
| Scrape bảng PISA (Wikipedia) | Có, nhưng CSV lỗi | Mục 3 |
| 3 biểu đồ: bar, histogram, heatmap | Đủ loại, nhưng số liệu và cách trình bày chưa ổn | Mục 4 |
| Notebook phân tích | 8 cell code, **0 output** | Restart & Run All rồi lưu lại |
| Report 1–2 trang | Có, nhưng 2 kết luận sai | Mục 5 |

---

## 1. Lỗi phân tích (ưu tiên cao nhất)

### 1.1 G3 = 0 chưa được xử lý

- 38/395 em có `G3 == 0`. **Cả 38 em đều có `absences == 0`**, và 13 em có `G2 == 0`.
- Điểm 0 trên thang 0–20 đi kèm 0 buổi vắng gần như chắc chắn là **bỏ thi / không còn học** (vắng không được ghi nhận), không phải điểm thật.
- Hệ quả:
  - "Absences paradox" trong report là **ảo**. Bỏ G3 = 0 thì mean G3 là low 12.26 / medium 11.38 / high 10.37, giảm đều theo mức vắng. Corr absences–G3 là **−0.21** (report đang ghi +0.03).
  - Tương quan G1/G2/G3 khi bỏ G3 = 0 (n=357) là G1–G3 0.892, G2–G3 **0.966**.
  - Pass rate khi bỏ G3 = 0 là 0.742 (đang ghi 0.671).

**Cách sửa:**

1. Trong `clean_data()`, thêm cột `dropout_suspect = (G3 == 0)`. **Không xoá dòng.**
2. Trong `analyze()`, tính 2 bộ số: `all` (n=395) và `exclude_dropout` (n=357). Ghi cả hai vào `summary.json`.
3. Biểu đồ và insight chính dùng bộ `exclude_dropout`. Report ghi rõ 38 em bị loại và lý do.
4. Thêm term **Dropout Suspect** vào `CONTEXT.md`.

### 1.2 `classify_risk` bị circular (leakage)

- Rule hiện tại: `G3 < 10 → high`. Nhưng `pass_fail` cũng là `G3 < 10`, nên "risk triage tách 8 điểm" là hiển nhiên và không chứng minh được gì.
- Report ghi rule là "flag G2 < 10 or failures ≥ 1", **không khớp code**.

**Cách sửa:**

1. Bỏ G3 khỏi rule. Chỉ dùng thông tin có trước kỳ cuối: G1, G2, failures, absences.
   - high: `G2 < 10` hoặc `failures >= 2`
   - medium: `G1 < 10` hoặc `failures == 1` hoặc `absence_level == "high"`
   - low: còn lại
2. Đánh giá rule so với `pass_fail` (thực tế), bằng bảng confusion + precision/recall.
   - Rule thô `G2 < 10 or failures >= 1` cho precision **0.71**, recall **0.95** (174 em bị flag).
   - Ghi số này vào `summary.json` (`risk_eval`) và report.
3. Cập nhật docstring `classify_risk` và định nghĩa **Risk Group** trong `CONTEXT.md`.

### 1.3 `avg_grade` chứa G3

- Giữ cột này để mô tả là được, nhưng **không** dùng làm biến giải thích cho G3.
- Thêm `avg_g1g2 = (G1 + G2) / 2` nếu cần một biến "điểm giữa kỳ" tổng hợp.

### 1.4 Thiếu phân tích "hỗ trợ gia đình" (câu hỏi chính của đề)

- Đề hỏi: thời gian học, vắng học, **hỗ trợ gia đình**, điểm giữa kỳ → G3. Code hiện chưa có groupby theo `famsup`.
- Sửa: thêm `by_famsup`, `by_schoolsup`, `by_paid` (mean/std/n, bộ `exclude_dropout`) vào `summary.json`, report và notebook.

---

## 2. Làm sạch dữ liệu student (chưa triệt để)

| # | Vấn đề | Sửa |
|---|---|---|
| 2.1 | `convert_yes_no` biến mọi giá trị khác "yes" (NaN, typo) thành 0 | Validate giá trị ∈ {yes, no}, ngoài tập này thì raise hoặc NaN, rồi đếm vào `summary.json` |
| 2.2 | Cột dẫn xuất được tính **trước** `dropna` | Đổi thứ tự: cast → validate → dropna → derive |
| 2.3 | Không kiểm tra miền giá trị | Thêm dict `VALID_RANGES` gồm G1–G3 0–20, age 15–22, Medu/Fedu 0–4, traveltime/studytime 1–4, failures 0–3, famrel..health 1–5. Đếm vi phạm |
| 2.4 | Không check duplicate / khoảng trắng | Thêm `strip()` cho cột chuỗi và `drop_duplicates()`, kèm số dòng bị ảnh hưởng (hiện là 0, nhưng phải có bước kiểm tra) |
| 2.5 | Outlier `absences` (75, 56, 54, 40, 38…) | Gắn cờ `absence_outlier` (mục 6), **không xoá** |
| 2.6 | `summary.json` không có log làm sạch | Thêm khối `cleaning_log`: rows_in, rows_out, n_invalid theo cột, n_flag theo cờ |
| 2.7 | Không tự thu thập UCI | Thêm `fetch_uci_raw()`: nếu thiếu `student-mat.csv`/`student-por.csv` thì tải `student.zip` từ UCI rồi giải nén vào `data/raw/` |

---

## 3. PISA scrape (`scrape_pisa_table`, `pisa_reference.csv`)

| # | Vấn đề | Sửa |
|---|---|---|
| 3.1 | Dòng 31 `International Average (OECD),482,` bị lệch cột | Chỉ giữ dòng có Rank là số. Lưu dòng trung bình OECD riêng vào `summary.json` (`pisa_oecd_avg`) |
| 3.2 | Tên nước còn dấu footnote `*` (`Canada *`) | `str.replace(r"\s*\*$", "", regex=True)` |
| 3.3 | Rank, Score còn là chuỗi | `pd.to_numeric(..., errors="coerce")` |
| 3.4 | Bug precedence: `target = target or tables[1] if len(tables) > 1 else tables[0]` | `target = target or (tables[1] if len(tables) > 1 else tables[0])` |
| 3.5 | Không biết bảng là môn gì, năm nào | Thêm cột `year`, `subject` lấy từ caption hoặc heading gần nhất |
| 3.6 | Header dòng đầu có thể là `<th>` gộp | Dùng `pd.read_html(StringIO(html), match="Rank")` hoặc giữ BeautifulSoup nhưng chuẩn hoá header |

---

## 4. Biểu đồ

### 01 — bar studytime × internet

- Nhóm no-internet ở studytime 3 và 4 chỉ có **n = 6 và n = 4**. Cột cao/thấp ở đó là nhiễu, đọc dễ hiểu sai.
- Sửa:
  1. Dùng dữ liệu `exclude_dropout`.
  2. Thêm error bar (std hoặc 95% CI) và ghi `n=` trên mỗi cột.
  3. `rotation=0` cho nhãn trục x.
  4. Hoặc đổi thành 2 bar riêng (theo studytime, theo internet) nếu giữ chung khó đọc.

### 02 — histogram G3

- Đúng loại biểu đồ, vạch pass mark đúng.
- Sửa:
  1. `bins = range(0, 22)`, vì G3 là số nguyên nên mỗi cột là 1 điểm.
  2. Tô màu khác cho cột G3 = 0 và chú thích "dropout suspect (n=38)".
  3. Có thể thêm dòng chữ pass rate trên biểu đồ.

### 03 — heatmap tương quan

- Số đúng. Nhưng viridis không có tâm 0, nên −0.36 và +0.10 khó phân biệt về dấu.
- Sửa:
  1. `cmap="RdBu_r"`, `vmin=-1`, `vmax=1`.
  2. Dùng dữ liệu `exclude_dropout`.
  3. Có thể mask nửa tam giác trên.
  4. Màu chữ trắng/đen tuỳ theo độ đậm của ô.

---

## 5. Report + notebook

1. Viết lại gạch đầu dòng **Absences paradox** thành "vắng nhiều → điểm thấp hơn (−0.21), sau khi loại 38 em dropout suspect".
2. Viết lại **Risk triage** bằng rule mới + precision/recall, bỏ câu "8-point spread".
3. Thêm 1 đoạn **Data quality**: G3 = 0, outlier absences, sửa PISA, các cờ bất thường.
4. Cập nhật mọi số (pass rate, corr, mean theo nhóm) theo `summary.json` mới.
5. Notebook:
   - Thêm section "Data quality & anomaly flags" (bảng đếm cờ, histogram absences).
   - Thêm section "Risk rule evaluation".
   - **Restart & Run All** rồi lưu, để có output.

---

## 6. Gắn nhãn bất thường (anomaly flags)

Nguyên tắc: **gắn cờ, không xoá.** Mỗi cờ là 1 cột bool. Ngưỡng lấy từ tuple cấu hình (giống `THRESHOLDS`), không hardcode trong hàm.

| Cột cờ | Điều kiện | Số dòng (mat) | Ý nghĩa |
|---|---|---|---|
| `dropout_suspect` | `G3 == 0` | 38 | Bỏ thi / bỏ học |
| `g2_zero` | `G2 == 0` | 13 | Vắng kỳ 2 (luôn kèm G3 = 0) |
| `grade_drop` | `G1 - G3 >= 8` hoặc `G2 - G3 >= 6` | ~15–18 | Tụt điểm đột ngột |
| `absence_outlier` | `absences > Q3 + 1.5·IQR` (= 20) | 15 | Vắng bất thường |
| `age_outlier` | `age >= 20` | 5 | Học muộn / lưu ban |
| `inconsistent_grade` | `G3 > 0 and G2 == 0` | 0 | Mâu thuẫn (check để chứng minh dữ liệu sạch) |

Quy trình chọn ngưỡng cho mỗi cờ:

1. **Nhìn phân phối:** dùng histogram/boxplot, tìm cột nhọn bất thường (như cột G3 = 0) hoặc đuôi dài (absences).
2. **Chọn quy tắc thống kê:** IQR (`Q3 + 1.5·IQR`) cho biến lệch, z-score (`|z| > 3`) cho biến gần chuẩn, còn quy tắc nghiệp vụ (G3 = 0) cho trường hợp có ý nghĩa rõ.
3. **Ghi lý do** vào `CONTEXT.md` (term mới) và docstring.
4. **Đếm** số dòng mỗi cờ và ghi vào `summary.json → anomaly_counts`.
5. **Chạy độ nhạy:** so sánh kết quả có / không có dòng bị cờ. Nếu kết luận đổi (như absences), ghi rõ vào report.

Code mẫu cho `clean_data()`:

```python
q1, q3 = df["absences"].quantile([0.25, 0.75])
abs_fence = q3 + 1.5 * (q3 - q1)
df["dropout_suspect"] = df["G3"] == 0
df["g2_zero"] = df["G2"] == 0
df["grade_drop"] = ((df["G1"] - df["G3"]) >= 8) | ((df["G2"] - df["G3"]) >= 6)
df["absence_outlier"] = df["absences"] > abs_fence
df["age_outlier"] = df["age"] >= 20
df["inconsistent_grade"] = (df["G3"] > 0) & (df["G2"] == 0)
```

---

## 7. Cào / mở rộng dữ liệu

### 7.1 Dùng data đã có sẵn (không cần cào): `student-por.csv`

- `data/raw/student-por.csv` có 649 dòng (môn tiếng Bồ Đào Nha), 15 em G3 = 0.
- Cách 1, gộp dọc:
  - `pd.concat` hai file, thêm cột `subject` ∈ {mat, por}.
  - Groupby thêm theo `subject`.
  - Lưu ý: một số học sinh có mặt ở cả 2 file.
- Cách 2, tìm học sinh chung: làm theo `data/raw/student-merge.R`, merge trên 13 cột (`school, sex, age, address, famsize, Pstatus, Medu, Fedu, Mjob, Fjob, reason, nursery, internet`), được ~382 em có cả hai môn. Dùng để so sánh điểm Toán và Văn của cùng một em.
- Thêm param `subject`/`raw_paths` cho `StudentDataProcessor`. `main.py` chạy cho cả 2 file.

### 7.2 Cào thêm bảng PISA trên Wikipedia bằng trình duyệt

Trang: <https://en.wikipedia.org/wiki/Programme_for_International_Student_Assessment>

**Bước 1: khảo sát trong trình duyệt (DevTools)** — *không làm (user quyết định 2026-10-13, xem `.scratch/p1-known-issues/spec.md` mục C4). Phần cào chỉ làm bằng Python (bước 2).*

1. Mở trang, bấm **F12 → Console**.
2. Liệt kê các bảng:
   ```js
   [...document.querySelectorAll('table.wikitable')].map((t, i) => ({
     i,
     rows: t.rows.length,
     cols: t.rows[1]?.cells.length,
     caption: t.caption?.innerText,
     heading: t.closest('section, div')?.querySelector('h2,h3')?.innerText,
     head: t.rows[0]?.innerText.slice(0, 80)
   }))
   ```
3. Ghi lại index của các bảng xếp hạng Math / Reading / Science và năm tương ứng.
4. Chuột phải vào bảng → **Inspect** để xem cấu trúc: header nhiều tầng (`rowspan`/`colspan`), footnote `*`, ô gộp.
5. (Tuỳ chọn) Copy nhanh 1 bảng ra CSV để đối chiếu:
   ```js
   copy([...document.querySelectorAll('table.wikitable')[IDX].rows]
     .map(r => [...r.cells].map(c => '"' + c.innerText.trim().replace(/"/g, '""') + '"').join(','))
     .join('\n'))
   ```
   Sau đó paste vào `data/raw/pisa_manual_check.csv`. File này chỉ để đối chiếu, pipeline vẫn phải tự cào bằng Python.

**Bước 2: chuyển sang Python (tái lập được)**

```python
from io import StringIO
import pandas as pd, requests

URL = "https://en.wikipedia.org/wiki/Programme_for_International_Student_Assessment"
html = requests.get(URL, timeout=25,
                    headers={"User-Agent": "P1-edu-project (student; contact: <email>)"}).text
tables = pd.read_html(StringIO(html), attrs={"class": "wikitable"})

def tidy(df, year, subject):
    df = df.copy()
    df.columns = [" ".join(map(str, c)).strip() if isinstance(c, tuple) else str(c)
                  for c in df.columns]
    df = df.rename(columns=lambda c: "rank" if "Rank" in c
                   else "country" if "Country" in c
                   else "score" if "Score" in c else c)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df = df.dropna(subset=["rank"])                     # bỏ dòng OECD average
    df["country"] = df["country"].str.replace(r"\s*\*$", "", regex=True).str.strip()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["year"], df["subject"] = year, subject
    return df[["year", "subject", "rank", "country", "score"]]

# IDX lấy từ bước 1
pisa = pd.concat([tidy(tables[i], y, s) for i, y, s in [
    # (IDX_MATH, 2022, "math"), (IDX_READ, 2022, "reading"), (IDX_SCI, 2022, "science"),
]])
pisa.to_csv("data/raw/pisa_rankings_long.csv", index=False)
```

- Nếu bảng chứa 3 môn trong 1 bảng lớn (bảng 0 trên trang, hơn 800 cột), tách theo nhóm cột Math/Reading/Science thay vì bỏ qua.
- Dữ liệu cũ hơn (2015, 2018) có trên các trang con của Wikipedia hoặc OECD PISA Data Explorer. Làm tương tự, chỉ đổi `year`.

**Bước 3: dùng PISA thế nào cho đúng**

- PISA là điểm **cấp quốc gia** (thang ~300–600). Student data là **cấp học sinh** (thang 0–20). **Không join theo dòng.**
- Dùng hợp lệ:
  - Vị trí Portugal so với OECD average (bối cảnh cho dữ liệu UCI, vốn từ trường ở Bồ Đào Nha).
  - Biểu đồ phụ: điểm Math của Portugal qua các năm.
  - Phân bố điểm các nước.
- Trong report ghi rõ nguồn, URL, **ngày truy cập**, và giới hạn "khác quần thể, khác năm".

**Bước 4: quy tắc cào an toàn**

- Gửi User-Agent có thông tin liên hệ. Mỗi lần chạy chỉ 1 request, cache raw HTML/CSV vào `data/raw/`, chạy lại thì đọc từ cache.
- Không cào trang cần đăng nhập, không bypass captcha.
- Wikipedia dùng giấy phép CC BY-SA, nên phải ghi nguồn trong report.

---

## 8. Thứ tự thực hiện

1. `data_processor.py`: làm mục 2 (thứ tự clean, validate, range), sau đó mục 6 (các cờ), rồi mục 1.1 (2 bộ số).
2. Sửa `classify_risk` và thêm `risk_eval` (mục 1.2).
3. Sửa `scrape_pisa_table` (mục 3), cào lại.
4. Sửa 3 biểu đồ (mục 4).
5. (Mở rộng) Thêm `student-por.csv` và nhiều bảng PISA (mục 7).
6. `python main.py`, kiểm tra `summary.json` có `cleaning_log`, `anomaly_counts`, `risk_eval`, bộ `exclude_dropout`.
7. Cập nhật `CONTEXT.md` (Dropout Suspect, Anomaly Flag, Risk Group mới).
8. Viết lại `report.md`, rồi Restart & Run All `analysis.ipynb`.

## Acceptance

- Absences–G3 corr (exclude_dropout) ≈ −0.21 có trong `summary.json` và report.
- Không còn G3 trong `classify_risk`. Có precision/recall của rule.
- `pisa_reference.csv` (raw) giữ nguyên chuỗi gốc của trang (có thể có `*`, `—`), nhưng không còn dòng lệch cột. Bản sạch `data/processed/pisa_clean.csv`: không còn `*`, Rank/Score/Year là số. *(Sửa 2026-10-13 cho khớp thiết kế raw/clean.)*
- 3 biểu đồ được vẽ lại: bar có n + error bar, histogram bins nguyên + đánh dấu G3 = 0, heatmap dùng colormap phân kỳ.
- Notebook có output ở mọi cell code.

## Comments

**2026-10-13: Implemented (mục 1–4, 6, 7.1, 7.2-scrape, report/notebook/CONTEXT).** Kết quả thực tế từ `python main.py`:

- Mục 1.1: corr absences–G3 = −0.213 (exclude_dropout), G2–G3 = 0.966, pass rate 0.742. Đã có trong `summary.json → scopes`.
- Mục 1.2: rule cuối cùng là high = `G2 < 10 or failures >= 2`. Trên n=395: precision **0.819**, recall **0.939** (TP 122, FP 27, FN 8). Con số 0.71/0.95 trong plan là của rule thô `failures >= 1`.
- Mục 1.4: `famsup` yes 11.35 vs no 11.80 (r = −0.07); `schoolsup` yes 9.62 vs no 11.83.
- Mục 2: mọi check đều cho 0 lỗi (log nằm ở `cleaning_log`). `fetch_uci_raw()` tải zip UCI khi thiếu file.
- Mục 3/7.2: `pisa_reference.csv` giờ là raw long table (2342 dòng, gồm summary 2025 + comparison 2000–2022, 3 môn). `pisa_clean.csv` có 1662 dòng. Bảng cũ thực ra là **Science**, không phải ranking chung.
- Mục 6: `grade_drop` loại trừ dropout (nếu không, 23/23 dòng mat bị gắn đều là dropout). Mat: dropout 38, g2_zero 13, grade_drop 0, absence_outlier 15 (fence 20), age_outlier 5, inconsistent 0.
- Mục 7.1: `por` chỉ dùng cho `subject_comparison`. Mọi phân tích chính vẫn trên `mat`.
