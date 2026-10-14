# Cẩm nang Toàn diện: Các Công thức Thống kê & Code Thực thi trong Dự án P1

Tài liệu chi tiết giải thích bản chất toán học, công thức tính, đoạn mã Python thực tế trong dự án, kết quả chạy thực tế và ý nghĩa rút ra cho từng phương pháp thống kê được sử dụng trong codebase.

---

## Mục lục
1. [P-value & Mức ý nghĩa Alpha](#1-p-value--mức-ý-nghĩa-alpha)
2. [Welch's t-test (Kiểm định so sánh 2 nhóm độc lập)](#2-welchs-t-test-kiểm-định-so-sánh-2-nhóm-độc-lập)
3. [Đa kiểm định (Multiple Testing) & Hiệu chỉnh Holm-Bonferroni](#3-đa-kiểm-định-multiple-testing--hiệu-chỉnh-holm-bonferroni)
4. [One-Way ANOVA & Kruskal-Wallis (So sánh từ 3 nhóm trở lên)](#4-one-way-anova--kruskal-wallis-so-sánh-từ-3-nhóm-trở-lên)
5. [Khoảng tin cậy Wilson (Wilson Score Confidence Interval)](#5-khoảng-tin-cậy-wilson-wilson-score-confidence-interval)
6. [Hồi quy Tuyến tính OLS Đa biến & Sai số Chuẩn Vững HC3](#6-hồi-quy-tuyến-tính-ols-đa-biến--sai-số-chuẩn-vững-hc3)
7. [Kiểm định Ghép cặp (Paired t-test & Wilcoxon Signed-Rank)](#7-kiểm-định-ghép-cặp-paired-t-test--wilcoxon-signed-rank)

---

## 1. P-value & Mức ý nghĩa Alpha

### 1.1 Bản chất toán học & Ý nghĩa
- **P-value ($p$):** Là xác suất quan sát được kết quả chênh lệch bằng hoặc cực đoan hơn kết quả thực tế, giả định rằng giả thuyết không $H_0$ (không có sự khác biệt / không có tác động) là đúng.
- **Mức ý nghĩa $\alpha = 0.05$:** Ngưỡng ranh giới chấp nhận rủi ro sai số loại I (kết luận có tác động trong khi thực tế chỉ là do ngẫu nhiên) ở mức $5\%$.
  - Nếu $p < 0.05$: Bác bỏ $H_0 \rightarrow$ Sự khác biệt có ý nghĩa thống kê (**Statistically Significant**).
  - Nếu $p \ge 0.05$: Chưa đủ bằng chứng để bác bỏ $H_0 \rightarrow$ Chênh lệch được coi là do ngẫu nhiên / may rủi.

### 1.2 Đoạn code thực tế trong dự án
Trong `data_processor.py` (dòng 43, 433–435):
```python
ALPHA = 0.05

def _p(x: float) -> float:
    """Làm tròn p-value đến 3 chữ số có nghĩa (để số cực nhỏ vẫn đọc được)."""
    return float(f"{x:.3g}")
```

### 1.3 Tác dụng trong dự án
Làm "trọng tài" vô tư cho mọi kết luận: Tránh việc nhìn bằng mắt thường thấy nhóm này điểm cao hơn nhóm kia vài phẩy rồi vội vàng kết luận là yếu tố đó có tác dụng.

---

## 2. Welch's t-test (Kiểm định so sánh 2 nhóm độc lập)

### 2.1 Bản chất toán học & Công thức
Dùng để so sánh điểm trung bình giữa 2 nhóm học sinh độc lập (ví dụ: có mạng vs không có mạng). Khác với Student t-test cổ điển (bắt buộc 2 nhóm phải có phương sai bằng nhau), **Welch t-test** cho phép 2 nhóm có phương sai khác nhau ($\sigma_1^2 \ne \sigma_2^2$) và cỡ mẫu lệch nhau ($n_1 \ne n_2$).

- **Thống kê kiểm định $t$:**
  $$t = \frac{\bar{X}_1 - \bar{X}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}}$$

- **Bậc tự do Welch–Satterthwaite ($df$):**
  $$df = \frac{\left(\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}\right)^2}{\frac{(s_1^2 / n_1)^2}{n_1 - 1} + \frac{(s_2^2 / n_2)^2}{n_2 - 1}}$$

- **Kích thước hiệu ứng Cohen's $d$ (đo độ lớn chênh lệch theo độ lệch chuẩn gộp):**
  $$d = \frac{\bar{X}_1 - \bar{X}_2}{s_{pooled}}, \quad \text{với } s_{pooled} = \sqrt{\frac{(n_1 - 1)s_1^2 + (n_2 - 1)s_2^2}{n_1 + n_2 - 2}}$$

### 2.2 Đoạn code thực tế trong dự án
Trong `data_processor.py` (dòng 457–471):
```python
for col in BINARY_TEST_COLS:  # ["internet", "famsup", "schoolsup", "paid"]
    yes = df.loc[df[col] == "yes", "G3"].astype(float)
    no = df.loc[df[col] == "no", "G3"].astype(float)
    
    # Welch t-test với equal_var=False
    res = stats.ttest_ind(yes, no, equal_var=False)
    ci = res.confidence_interval(1 - ALPHA)
    
    pooled_sd = np.sqrt(((len(yes) - 1) * yes.var() + (len(no) - 1) * no.var())
                        / (len(yes) + len(no) - 2))
    diff = yes.mean() - no.mean()
    
    tests[col] = {
        "test": "Welch t-test",
        "n_yes": int(len(yes)), "n_no": int(len(no)),
        "mean_yes": round(float(yes.mean()), 2),
        "mean_no": round(float(no.mean()), 2),
        "diff": round(float(diff), 2),
        "ci95": [round(float(ci.low), 2), round(float(ci.high), 2)],
        "stat": round(float(res.statistic), 2),
        "df": round(float(res.df), 1),
        "p": _p(res.pvalue),
        "effect": round(float(diff / pooled_sd), 2),
        "effect_name": "Cohen's d"
    }
```

### 2.3 Kết quả thực tế & Ý nghĩa
Chạy trên 357 học sinh môn Toán (loại trừ nhóm bỏ thi):

| Biến kiểm định | $n_{yes} / n_{no}$ | Điểm trung bình | Chênh lệch (diff) | 95% CI | P-value thô | Cohen's d | Ý nghĩa |
|---|---|---|---|---|---|---|---|
| `internet` | 297 / 60 | 11.89 vs 10.87 | +1.02 điểm | [0.12, 1.93] | **0.0268** | +0.30 | Thô thì $p < 0.05$ (nhưng xem mục 3) |
| `famsup` (gia đình) | 222 / 135 | 11.58 vs 11.95 | -0.37 điểm | [-1.08, 0.35] | **0.202** | -0.14 | **Không có ý nghĩa** |
| `paid` (học thêm) | 165 / 192 | 11.64 vs 11.78 | -0.15 điểm | [-0.86, 0.57] | **0.585** | -0.06 | **Không có ý nghĩa** |
| `schoolsup` (phụ đạo) | 48 / 309 | 9.88 vs 12.00 | -2.13 điểm | [-2.91, -1.34]| **$5.6 \times 10^{-7}$**| -0.71 | Học sinh yếu mới phải phụ đạo |

---

## 3. Đa kiểm định (Multiple Testing) & Hiệu chỉnh Holm-Bonferroni

### 3.1 Bản chất toán học & Công thức
- **Vấn đề Đa kiểm định:** Khi ta kiểm tra $m$ giả thuyết đồng thời ở mức $\alpha = 0.05$, xác suất có **ít nhất một kết quả bị dương tính giả (False Positive - ăn may)** là:
  $$P(\ge 1 \text{ false positive}) = 1 - (1 - \alpha)^m$$
  Với $m = 7$ kiểm định (4 biến nhị phân + 3 biến nhiều mức), xác suất bị ăn may lên tới $1 - (0.95)^7 \approx 30.2\%$!
- **Thuật toán Holm-Bonferroni (Step-down procedure):**
  1. Sắp xếp $m$ giá trị p-value tăng dần: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
  2. Tại mỗi bước $i$ (từ 1 đến $m$), giá trị p-value hiệu chỉnh được tính bằng:
     $$p_{holm,(i)} = \min\left(1.0, \max\left(p_{holm,(i-1)}, (m - i + 1) \times p_{(i)}\right)\right)$$
  3. Bác bỏ $H_0$ nếu $p_{holm,(i)} < \alpha$. Nếu tại bước nào $p_{holm,(i)} \ge \alpha$ thì dừng lại, các giả thuyết sau đều không thể bác bỏ.

### 3.2 Đoạn code thực tế trong dự án
Trong `data_processor.py` (dòng 438–444):
```python
def _holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni điều chỉnh p-values (kiểm soát Family-Wise Error Rate)."""
    out, running, m = {}, 0.0, len(pvals)
    # Sắp xếp các test theo p-value tăng dần
    for i, (k, p) in enumerate(sorted(pvals.items(), key=lambda kv: kv[1])):
        # Nhân với số lượng test còn lại (m - i) và đảm bảo tính đơn điệu
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out
```

### 3.3 Kết quả thực tế & Bước ngoặt "Internet"
Trong `group_tests`, họ 7 kiểm định được đưa qua hàm `_holm`:

```python
adjusted = _holm({k: v["p"] for k, v in tests.items()})
for k, v in tests.items():
    v["p_holm"] = _p(adjusted[k])
    v["significant"] = bool(adjusted[k] < ALPHA)
```

Kết quả so sánh trước và sau khi lọc qua Holm:
- `schoolsup`: $p = 5.61 \times 10^{-7} \rightarrow p_{holm} = 3.37 \times 10^{-6} < 0.05 \rightarrow$ **Vẫn có ý nghĩa**.
- `failures`: $p = 7.52 \times 10^{-8} \rightarrow p_{holm} = 5.26 \times 10^{-7} < 0.05 \rightarrow$ **Vẫn có ý nghĩa**.
- `absence_level`: $p = 6.86 \times 10^{-5} \rightarrow p_{holm} = 0.00034 < 0.05 \rightarrow$ **Vẫn có ý nghĩa**.
- `studytime`: $p = 0.0048 \rightarrow p_{holm} = 0.0193 < 0.05 \rightarrow$ **Vẫn có ý nghĩa**.
- ⚠️ **`internet`:** $p = 0.0268 \rightarrow p_{holm} = 0.0804 > 0.05 \rightarrow$ **MẤT Ý NGHĨA THỐNG KÊ!**

> **Ý nghĩa thực tế:** Ban đầu nhìn $p = 0.0268 < 0.05$ tưởng có internet giúp tăng điểm. Nhờ có thuật toán Holm-Bonferroni, ta nhận ra chênh lệch đó chỉ là **ngẫu nhiên do kiểm định quá nhiều biến**. Dự án kết luận chính xác: *Internet ở nhà không có tác động thực sự đến điểm thi môn Toán*.

---

## 4. One-Way ANOVA & Kruskal-Wallis (So sánh từ 3 nhóm trở lên)

### 4.1 Bản chất toán học & Công thức
Dùng cho các biến có từ 3 phân nhóm trở lên (thời gian tự học 4 mức, vắng học 3 mức, số lần trượt cũ).
- **One-Way ANOVA (Kiểm định tham số):** So sánh phương sai giữa các nhóm ($MS_{between}$) với phương sai nội bộ các nhóm ($MS_{within}$):
  $$F = \frac{MS_{between}}{MS_{within}} = \frac{\frac{\sum_{j=1}^k n_j (\bar{X}_j - \bar{X})^2}{k - 1}}{\frac{\sum_{j=1}^k \sum_{i=1}^{n_j} (X_{ij} - \bar{X}_j)^2}{N - k}}$$
- **Độ lớn hiệu ứng Eta-squared ($\eta^2$):** Đo lường tỷ lệ % phương sai của điểm $G3$ được giải thích bởi biến đó:
  $$\eta^2 = \frac{SS_{between}}{SS_{total}} = \frac{\sum_{j=1}^k n_j (\bar{X}_j - \bar{X})^2}{\sum_{i=1}^N (X_i - \bar{X})^2}$$
- **Kruskal-Wallis (Kiểm định phi tham số):** Xếp hạng toàn bộ $N$ học sinh từ 1 đến $N$, tính tổng hạng $R_j$ của từng nhóm. Không cần giả định dữ liệu phân phối chuẩn:
  $$H = \frac{12}{N(N + 1)} \sum_{j=1}^k \frac{R_j^2}{n_j} - 3(N + 1)$$

### 4.2 Đoạn code thực tế trong dự án
Trong `data_processor.py` (dòng 472–486):
```python
for col in MULTI_TEST_COLS:  # ["studytime", "absence_level", "failures"]
    cap = TEST_LEVEL_CAP.get(col)  # Gộp failures 2 và 3 thành "2+" vì mỗi nhóm chỉ ~10 em
    levels = df[col].clip(upper=cap) if cap is not None else df[col]
    by = df.groupby(levels)
    groups = [g["G3"].astype(float).to_numpy() for _, g in by]
    
    anova = stats.f_oneway(*groups)  # One-way ANOVA
    kw = stats.kruskal(*groups)      # Kruskal-Wallis đối chứng
    
    grand = df["G3"].mean()
    ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
    ss_total = float(((df["G3"] - grand) ** 2).sum())
    
    tests[col] = {
        "test": "one-way ANOVA",
        "k_groups": len(groups),
        "stat": round(float(anova.statistic), 2),
        "p": _p(anova.pvalue),
        "effect": round(float(ss_between / ss_total), 3),
        "effect_name": "eta²",
        "kruskal_H": round(float(kw.statistic), 2),
        "p_kruskal": _p(kw.pvalue)
    }
```

### 4.3 Kết quả thực tế & Ý nghĩa
| Biến kiểm định | Số nhóm ($k$) | ANOVA $F$ | P-value (ANOVA) | Kruskal-Wallis $H$ | P-value (Kruskal) | $\eta^2$ (Eta-squared) | Ý nghĩa rút ra |
|---|---|---|---|---|---|---|---|
| `studytime` | 4 mức (<2h, 2–5h, 5–10h, >10h) | 4.35 | 0.0048 | 12.06 | 0.0072 | **0.036 (3.6%)** | Có tác động nhưng rất yếu (chỉ giải thích 3.6% điểm số) |
| `absence_level`| 3 mức (Low, Med, High) | 9.87 | $6.86 \times 10^{-5}$| 18.73 | $8.57 \times 10^{-5}$| **0.053 (5.3%)** | Vắng nhiều làm tụt điểm rõ rệt |
| `failures` | 3 mức (0, 1, 2+) | 17.37| $7.52 \times 10^{-8}$| 31.95 | $1.15 \times 10^{-7}$| **0.089 (8.9%)** | Yếu tố quá khứ tác động mạnh nhất |

> **Vai trò của Kruskal-Wallis:** Vì điểm $G3$ ở các nhóm nhỏ có thể không chuẩn hoàn hảo, việc Kruskal-Wallis cho ra $p < 0.01$ đồng nhất với ANOVA khẳng định kết luận trên là hoàn toàn vững chắc (robust).

---

## 5. Khoảng tin cậy Wilson (Wilson Score Confidence Interval)

### 5.1 Bản chất toán học & Công thức
Dùng để tính khoảng tin cậy 95% cho các tỉ lệ nhị thức $p = k/n$ (như tỉ lệ đỗ, Recall, Precision).
- **Nhược điểm của công thức Wald cổ điển:** $\hat{p} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$ sẽ bị sai nghiêm trọng khi cỡ mẫu $n$ nhỏ hoặc tỉ lệ $\hat{p}$ gần sát 0 hoặc 1 (thậm chí cận trên vượt quá 100% hoặc cận dưới âm).
- **Công thức Wilson Score:** Giải phương trình bậc 2 đảo ngược từ phân phối chuẩn, luôn đảm bảo khoảng tin cậy nằm chặt trong đoạn $[0, 1]$:
  $$CI_{Wilson} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1 - \hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
  *(với $z = 1.96$ ở độ tin cậy 95%)*.

### 5.2 Đoạn code thực tế trong dự án
Trong `data_processor.py` (dòng 597–602):
```python
def _wilson(k: int, n: int) -> list[float]:
    """Khoảng tin cậy Wilson 95% của một tỷ lệ k/n."""
    if n == 0:
        return [0.0, 0.0]
    # Dùng hàm binomtest chuẩn xác của scipy.stats
    ci = stats.binomtest(k, n).proportion_ci(1 - ALPHA, method="wilson")
    return [round(float(ci.low), 4), round(float(ci.high), 4)]
```

Được gọi trong hàm đánh giá rủi ro `_risk_eval()` (dòng 620–623):
```python
"precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
"precision_ci95": _wilson(tp, tp + fp),
"recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
"recall_ci95": _wilson(tp, tp + fn)
```

### 5.3 Kết quả thực tế & Ý nghĩa
Đánh giá nhóm rủi ro `High` trong việc phát hiện học sinh sẽ trượt môn ($G3 < 10$):

| Tập dữ liệu | Số lượng ($n$) | Recall (Độ nhạy) | Khoảng tin cậy Wilson 95% | Precision (Độ chuẩn xác) | Khoảng tin cậy Wilson 95% |
|---|---|---|---|---|---|
| **Môn Toán (Toàn bộ)** | 395 | **93.8%** (122/130) | **[88.3%, 96.9%]** | **81.9%** (122/149) | **[74.9%, 87.2%]** |
| **Môn Toán (Bỏ nhóm G3=0)**| 357 | **93.5%** (86/92) | **[86.5%, 97.0%]** | **76.1%** (86/113) | **[67.5%, 83.0%]** |
| **Holdout Tiếng BĐN (Chặt)** | 275 | **91.4%** (64/70) | **[82.5%, 96.0%]** | **66.0%** (64/97) | **[56.1%, 74.6%]** |

> **Ý nghĩa thực tế:** Nhờ có khoảng tin cậy Wilson, ta có bằng chứng khoa học khẳng định: Ngay cả trên tập học sinh độc lập chưa từng thấy (Holdout môn Tiếng Bồ Đào Nha), ở kịch bản xấu nhất (cận dưới Wilson), hệ thống cảnh báo sớm vẫn tóm trúng ít nhất **82.5%** số học sinh sẽ trượt môn.

---

## 6. Hồi quy Tuyến tính OLS Đa biến & Sai số Chuẩn Vững HC3

### 6.1 Bản chất toán học & Công thức
Dự án **không dùng scikit-learn** mà tự cài đặt thuật toán hồi quy bình phương tối thiểu (OLS) bằng đại số ma trận thuần túy với NumPy:

1. **Vector hệ số hồi quy $\beta$:**
   $$\beta = (X^T X)^{-1} X^T y$$
   Mỗi hệ số $\beta_j$ thể hiện: *Nếu cố định tất cả các biến khác không đổi, khi biến $j$ tăng 1 đơn vị thì điểm G3 sẽ thay đổi bao nhiêu điểm*.

2. **Ma trận đòn bẩy $H$ (Hat Matrix / Leverage):**
   $$H = X (X^T X)^{-1} X^T \implies h_{ii} = x_i^T (X^T X)^{-1} x_i$$
   Đo lường mức độ ảnh hưởng của từng điểm dữ liệu lên mặt phẳng hồi quy.

3. **Sai số chuẩn vững HC3 (Heteroskedasticity-Consistent Standard Errors):**
   Trong thực tế, phương sai của phần dư $e_i = y_i - \hat{y}_i$ thường không đều (hiện tượng heteroskedasticity). Công thức cổ điển sẽ tính sai $p$-value. Dự án sử dụng ước lượng **HC3** (MacKinnon & White, 1985) với trọng số phạt $(1 - h_{ii})^2$:
   $$\Sigma_{HC3} = (X^T X)^{-1} \left( X^T \cdot \text{diag}\left(\frac{e_i^2}{(1 - h_{ii})^2}\right) \cdot X \right) (X^T X)^{-1}$$
   $$SE(\beta_j) = \sqrt{\Sigma_{HC3}[j, j]}$$

4. **Kiểm định $t$, $p$-value và hệ số xác định $R^2$:**
   $$t_j = \frac{\beta_j}{SE(\beta_j)}, \quad p_j = 2 \times \left(1 - F_t(|t_j|, df = n - k)\right)$$
   $$R^2 = 1 - \frac{\sum e_i^2}{\sum (y_i - \bar{y})^2}$$

### 6.2 Đoạn code thực tế trong dự án
Trong `data_processor.py` (dòng 505–533):
```python
def _ols(df: pd.DataFrame, cols: list[str]) -> dict:
    """Hồi quy OLS với sai số chuẩn vững HC3 chống phương sai thay đổi."""
    X = df.assign(male=(df["sex"] == "M").astype(int),
                  urban=(df["address"] == "U").astype(int))[cols].astype(float).to_numpy()
    y = df["G3"].astype(float).to_numpy()
    
    # Ghép cột số 1 cho hệ số chặn (intercept)
    A = np.column_stack([np.ones(len(y)), X])
    n, k = A.shape
    
    # 1. Tính hệ số beta = (A^T A)^(-1) A^T y
    xtx_inv = np.linalg.inv(A.T @ A)
    beta = xtx_inv @ A.T @ y
    resid = y - A @ beta
    
    # 2. Tính đòn bẩy leverage h_ii
    leverage = np.einsum("ij,jk,ik->i", A, xtx_inv, A)
    
    # 3. Tính ma trận hiệp phương sai HC3
    meat = A.T @ (A * (resid ** 2 / (1 - leverage) ** 2)[:, None])
    se = np.sqrt(np.diag(xtx_inv @ meat @ xtx_inv))
    
    # 4. Tra phân phối Student-t lấy p-value và khoảng tin cậy 95%
    dof = n - k
    p = 2 * stats.t.sf(np.abs(beta / se), dof)
    q = stats.t.ppf(1 - ALPHA / 2, dof)
    r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    
    return {
        "n": int(n), "n_predictors": int(k - 1),
        "r2": round(float(r2), 3),
        "coef": {name: {"b": round(float(b), 3), "se": round(float(s), 3),
                        "ci95": [round(float(b - q * s), 3), round(float(b + q * s), 3)],
                        "p": _p(pv), "significant": bool(pv < ALPHA)}
                 for name, b, s, pv in zip(["intercept"] + cols, beta, se, p)}
    }
```

### 6.3 Kết quả thực tế & Bước ngoặt Mô hình A vs Mô hình B
Chạy trên môn Toán (loại trừ nhóm G3 = 0):

#### 🔹 Mô hình A: 13 yếu tố nền (Gia đình, tự học, vắng, mạng...)
- **$R^2 = 0.234$** (Chỉ giải thích được $23.4\%$ sự biến thiên điểm số).
- Các hệ số tiêu biểu:
  - `failures` (trượt cũ): $\beta = -0.898$ ($SE = 0.248, p = 0.00034 < 0.001$). Cứ từng trượt 1 môn cũ thì điểm cuối kỳ bị kéo tụt gần 1 điểm.
  - `absences` (vắng học): $\beta = -0.064$ ($SE = 0.021, p = 0.0026 < 0.01$). Vắng 10 buổi bị tụt $\approx 0.64$ điểm.
  - `studytime` (tự học): $\beta = +0.412$ ($p = 0.091 > 0.05$). Không đạt mức ý nghĩa thống kê khi đã kiểm soát các biến khác.
  - `internet_bin`: $\beta = +0.527$ ($p = 0.247 > 0.05$). Hoàn toàn không có ý nghĩa.

#### 🔹 Mô hình B: Thêm điểm kỳ 1 ($G1$) và điểm giữa kỳ ($G2$)
- **$R^2 = 0.937$** (Vọt lên giải thích tới $93.7\%$ điểm số).
- Hệ số điểm giữa kỳ:
  - `G2`: $\beta = +0.870$ ($SE = 0.035, p = 4.45 \times 10^{-79}$).
  - Khi đã biết điểm $G2$, toàn bộ các biến nền gia đình, tự học, internet đều bị triệt tiêu ý nghĩa thống kê ($p > 0.05$).

> **Ý nghĩa thực tế:** Chứng minh kết quả học tập mang tính tích lũy cực cao. Muốn dự báo điểm cuối kỳ thì điểm đánh giá giữa kỳ $G2$ là chỉ báo số 1, ăn đứt mọi thông tin về hoàn cảnh gia đình.

---

## 7. Kiểm định Ghép cặp (Paired t-test & Wilcoxon Signed-Rank)

### 7.1 Bản chất toán học & Công thức
Dùng khi so sánh điểm môn Toán và môn Tiếng Bồ Đào Nha.
- **Vì sao không được dùng Independent t-test:** Vì có 358 em học sinh **học đồng thời cả 2 môn**. Điểm môn Toán và Tiếng Bồ Đào Nha của cùng một em học sinh có mối liên hệ nội tại (tương quan $r = 0.589$), vi phạm giả định độc lập của kiểm định 2 mẫu thông thường.
- **Kiểm định ghép cặp (Paired t-test):** Tính độ lệch trực tiếp $D_i = G3_{mat,i} - G3_{por,i}$ cho từng em, rồi kiểm định xem trung bình độ lệch $\bar{D}$ có khác 0 không:
  $$t = \frac{\bar{D} - 0}{s_D / \sqrt{n}}$$
- **Wilcoxon Signed-Rank Test:** Bản phi tham số tương ứng dựa trên thứ hạng độ lệch có dấu, dùng để đối chứng khi phân phối của độ lệch không chuẩn.

### 7.2 Đoạn code thực tế trong dự án
Trong `data_processor.py` (dòng 537–566):
```python
def _paired_subjects(clean: pd.DataFrame, a: str = "mat", b: str = "por") -> dict:
    """So sánh ghép cặp học sinh học cả 2 môn bằng Paired t-test và Wilcoxon."""
    # Ghép 2 môn theo 13 thuộc tính định danh học sinh
    pairs = ga.merge(gb, on=MERGE_KEYS, suffixes=(f"_{a}", f"_{b}"))
    # Chỉ so sánh các cặp có đi thi thật ở cả 2 môn (loại dropout_suspect)
    ok = pairs[~pairs[f"dropout_suspect_{a}"] & ~pairs[f"dropout_suspect_{b}"]]
    
    x = ok[f"G3_{a}"].astype(float)
    y = ok[f"G3_{b}"].astype(float)
    diff = x - y
    
    # 1. Paired t-test
    t = stats.ttest_rel(x, y)
    ci = t.confidence_interval(1 - ALPHA)
    
    # 2. Wilcoxon signed-rank test
    w = stats.wilcoxon(x, y)
    
    # 3. Tương quan Pearson giữa điểm 2 môn của cùng 1 em
    r = stats.pearsonr(x, y)
    
    return {
        "n_pairs_valid": int(len(ok)),
        "mean_diff": round(float(diff.mean()), 2),
        "ci95": [round(float(ci.low), 2), round(float(ci.high), 2)],
        "stat_t": round(float(t.statistic), 2),
        "p_t": _p(t.pvalue),
        "p_wilcoxon": _p(w.pvalue),
        "corr_g3": round(float(r.statistic), 3)
    }
```

### 7.3 Kết quả thực tế & Ý nghĩa
- **Số cặp học sinh thi thật ở cả 2 môn:** $n = 324$ cặp.
- **Độ chênh lệch điểm trung bình (Toán − Tiếng Bồ Đào Nha):** $\bar{D} = -1.26$ điểm [$-1.56, -0.96$].
- **Thống kê $t$:** $t = -8.24$, $p < 0.001$.
- **Wilcoxon:** $p < 0.001$.
- **Tương quan điểm 2 môn:** $r(G3_{mat}, G3_{por}) = 0.589$ ($p < 0.001$).

> **Ý nghĩa thực tế:** Cùng một học sinh thì điểm môn Toán bị chấm khắt khe hơn hoặc khó hơn môn Tiếng Bồ Đào Nha trung bình $1.26$ điểm. Việc dùng Paired t-test thay vì t-test độc lập thể hiện trình độ hiểu sâu về bản chất cấu trúc dữ liệu.

---

## 8. Bảng Tổng hợp Tra cứu Nhanh Phương pháp Thống kê

| Phương pháp | Vị trí hàm trong code | Thư viện / Thuật toán | Đối tượng áp dụng | Chỉ số đầu ra chính | Kết luận cốt lõi |
|---|---|---|---|---|---|
| **P-value & $\alpha$** | Dòng 433–435 | Hàm `_p()`, $\alpha = 0.05$ | Toàn bộ kiểm định | $p$-value làm tròn 3 chữ số | Ngưỡng ra quyết định bác bỏ $H_0$ |
| **Welch t-test** | Dòng 457–471 | `scipy.stats.ttest_ind(equal_var=False)` | `internet`, `famsup`, `paid`, `schoolsup` | $t, df, p$, Cohen's $d$, 95% CI | Mạng và gia đình ko giúp tăng điểm |
| **Holm-Bonferroni**| Dòng 438–444 | Thuật toán Step-down tự viết | Họ 7 kiểm định đồng thời | $p_{holm}$ | Dập tắt ngụy biện về Internet ($p_{holm} = 0.080$) |
| **One-Way ANOVA** | Dòng 472–486 | `scipy.stats.f_oneway` | `studytime`, `failures`, `absence_level` | $F, p$, $\eta^2$ | Tự học chỉ giải thích 3.6% phương sai |
| **Kruskal-Wallis** | Dòng 472–486 | `scipy.stats.kruskal` | Đi kèm ANOVA | $H, p$ | Khẳng định ANOVA đúng kể cả khi ko chuẩn |
| **Wilson Score CI**| Dòng 597–602 | `scipy.stats.binomtest().proportion_ci` | Recall, Precision của `classify_risk` | 95% Wilson CI $[low, high]$ | Khẳng định Recall $\ge 82.5\%$ ở Holdout ngoài mẫu |
| **Hồi quy OLS** | Dòng 505–533 | Tự code $\beta = (X^TX)^{-1}X^Ty$ + HC3 | Model A (13 biến) & Model B (+G1, G2) | $\beta, SE_{HC3}, R^2, p$ | Model A $R^2 = 0.234$; Model B $R^2 = 0.937$ |
| **Paired t-test** | Dòng 537–566 | `scipy.stats.ttest_rel` & `wilcoxon` | 324 học sinh học cả Toán và Bồ Đào Nha | $t, p$, diff 95% CI | Toán thấp hơn Bồ Đào Nha 1.26 điểm |
