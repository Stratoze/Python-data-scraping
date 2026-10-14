# Các phương pháp thống kê trong Dự án P1 (bản gọn)

Mỗi phương pháp gồm: bản chất, công thức, code thật trong `data_processor.py` (kèm số dòng), kết quả chạy thật và ý nghĩa. Tổng quan dự án, quy trình làm sạch và cào dữ liệu: xem `PROJECT_GUIDE.md`.

## Mục lục
1. p-value và mức ý nghĩa α
2. Welch t-test (biến yes/no)
3. Hiệu chỉnh đa kiểm định Holm
4. One-way ANOVA + η² (biến nhiều mức)
5. Kiểm định tương quan Pearson
6. Đánh giá rule cảnh báo sớm (precision, recall, holdout)
7. Bảng tra nhanh

---

## Phạm vi

Toàn bộ kiểm định chạy trên môn Toán, phạm vi **core** = 357 học sinh sau khi bỏ 38 em G3 = 0 (`dropout_suspect`), trừ khi ghi khác. Kết quả nằm ở `data/processed/summary.json` → `scopes.exclude_dropout.group_tests` / `corr_tests` và `risk_eval`.

## 1. p-value và mức ý nghĩa α (`_p`, `ALPHA`)

**Bản chất:** p-value là xác suất thấy chênh lệch ít nhất lớn như quan sát **nếu thật ra không có khác biệt** ($H_0$). p nhỏ hơn $\alpha$ → bác bỏ $H_0$. Dự án dùng $\alpha = 0.05$ (dòng 43: `ALPHA = 0.05`), và khoảng tin cậy $1-\alpha = 95\%$.

```python
# data_processor.py, dòng 427–429
def _p(x: float) -> float:
    """Round a p-value to 3 significant digits (keeps tiny values readable)."""
    return float(f"{x:.3g}")
```

Làm tròn 3 chữ số có nghĩa để giá trị rất nhỏ như `1.5e-08` không bị làm tròn thành 0.

## 2. Welch t-test (biến yes/no)

**Bản chất:** so sánh G3 trung bình giữa 2 nhóm (yes/no) mà **không giả định phương sai bằng nhau** — phù hợp vì cỡ nhóm lệch nhiều (vd internet 299 vs 58).

$$t = \frac{\bar x_{yes} - \bar x_{no}}{\sqrt{\dfrac{s_{yes}^2}{n_{yes}} + \dfrac{s_{no}^2}{n_{no}}}}$$

Bậc tự do Welch–Satterthwaite:

$$df = \frac{\left(\dfrac{s_{yes}^2}{n_{yes}} + \dfrac{s_{no}^2}{n_{no}}\right)^2}{\dfrac{(s_{yes}^2/n_{yes})^2}{n_{yes}-1} + \dfrac{(s_{no}^2/n_{no})^2}{n_{no}-1}}$$

Khoảng tin cậy 95% của chênh lệch: $(\bar x_{yes} - \bar x_{no}) \pm t_{0.975,\,df} \cdot SE$.

```python
# data_processor.py, dòng 449–459
    for col in BINARY_TEST_COLS:
        yes = df.loc[df[col] == "yes", "G3"].astype(float)
        no = df.loc[df[col] == "no", "G3"].astype(float)
        res = stats.ttest_ind(yes, no, equal_var=False)
        ci = res.confidence_interval(1 - ALPHA)
        tests[col] = {"test": "Welch t-test", "n_yes": int(len(yes)), "n_no": int(len(no)),
                      "mean_yes": round(float(yes.mean()), 2), "mean_no": round(float(no.mean()), 2),
                      "diff": round(float(yes.mean() - no.mean()), 2),
                      "ci95": [round(float(ci.low), 2), round(float(ci.high), 2)],
                      "stat": round(float(res.statistic), 2), "df": round(float(res.df), 1),
                      "p": _p(res.pvalue)}
```

`BINARY_TEST_COLS = ["internet", "famsup", "schoolsup", "paid"]` (dòng 44).

**Kết quả thật (core):**

| Biến | Mean yes (n) | Mean no (n) | Diff | 95% CI | p | p_holm | Có ý nghĩa? |
|---|---|---|---|---|---|---|---|
| internet | 11.68 (299) | 10.71 (58) | +0.98 | [0.11, 1.84] | 0.0268 | 0.0804 | Không |
| famsup | 11.35 (219) | 11.80 (138) | −0.45 | [−1.13, 0.24] | 0.202 | 0.404 | Không |
| schoolsup | 9.62 (50) | 11.83 (307) | −2.21 | [−3.02, −1.41] | 5.6e-07 | 3.4e-06 | **Có** |
| paid | 11.43 (173) | 11.61 (184) | −0.19 | [−0.86, 0.48] | 0.585 | 0.585 | Không |

Với internet: $t = 2.25$, $df = 85.8$.

**Ý nghĩa:**
- `schoolsup` có ý nghĩa nhưng **ngược chiều**: em được phụ đạo điểm thấp hơn 2.21 — vì trường phụ đạo cho em yếu (nhân quả ngược), không phải phụ đạo làm điểm tụt.
- `internet`: riêng lẻ p = 0.0268 < 0.05 nhưng sau Holm thì không (xem mục 3).
- `famsup`, `paid`: CI chứa 0 → không có bằng chứng khác biệt.

## 3. Hiệu chỉnh đa kiểm định Holm (`_holm`)

**Bản chất:** chạy 7 kiểm định (4 t-test + 3 ANOVA) cùng lúc thì xác suất có ít nhất 1 "phát hiện" giả tăng lên nhiều so với 5%. Holm–Bonferroni kiểm soát **sai số loại I cho cả họ** (FWER) ở mức $\alpha$.

Sắp p tăng dần $p_{(1)} \le \dots \le p_{(m)}$, với $m = 7$:

$$\tilde p_{(i)} = \max_{j \le i} \Big( \min\big(1,\ (m - j + 1)\, p_{(j)}\big) \Big)$$

```python
# data_processor.py, dòng 432–438
def _holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values (controls the family-wise error rate)."""
    out, running, m = {}, 0.0, len(pvals)
    for i, (k, p) in enumerate(sorted(pvals.items(), key=lambda kv: kv[1])):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out
```

(`i` đếm từ 0 nên hệ số là `m - i`; `running` giữ tính đơn điệu.) Áp dụng ở dòng 473–476:

```python
# data_processor.py, dòng 473–476
    adjusted = _holm({k: v["p"] for k, v in tests.items()})
    for k, v in tests.items():
        v["p_holm"] = _p(adjusted[k])
        v["significant"] = bool(adjusted[k] < ALPHA)
```

**Kết quả thật — thứ tự Holm:**

| Thứ hạng | Kiểm định | p | Hệ số | p_holm | < 0.05? |
|---|---|---|---|---|---|
| 1 | failures (ANOVA) | 7.5e-08 | ×7 | 5.3e-07 | Có |
| 2 | schoolsup (t) | 5.6e-07 | ×6 | 3.4e-06 | Có |
| 3 | absence_level (ANOVA) | 6.9e-05 | ×5 | 0.00034 | Có |
| 4 | studytime (ANOVA) | 0.00482 | ×4 | 0.0193 | Có |
| 5 | **internet (t)** | **0.0268** | ×3 | **0.0804** | **Không** |
| 6 | famsup (t) | 0.202 | ×2 | 0.404 | Không |
| 7 | paid (t) | 0.585 | ×1 | 0.585 | Không |

**Điểm bước ngoặt:** internet $0.0268 \times 3 = 0.0804 > 0.05$ → chênh lệch ~1 điểm nhìn thấy ở biểu đồ 1 (`01_bar_studytime_internet.png`) **không đủ bằng chứng** khi tính tới việc đã thử 7 giả thuyết.

## 4. One-way ANOVA + $\eta^2$ (biến nhiều mức)

**Bản chất:** kiểm tra G3 trung bình của $k$ nhóm có bằng nhau không, bằng tỉ số phương sai giữa nhóm / trong nhóm:

$$F = \frac{SS_{between}/(k-1)}{SS_{within}/(N-k)}, \quad SS_{between} = \sum_g n_g(\bar x_g - \bar x)^2$$

**Độ lớn hiệu ứng** — phần phương sai G3 do nhóm giải thích:

$$\eta^2 = \frac{SS_{between}}{SS_{total}}, \quad SS_{total} = \sum_i (x_i - \bar x)^2$$

p nhỏ chỉ nói "có khác biệt", $\eta^2$ nói "khác biệt lớn cỡ nào".

```python
# data_processor.py, dòng 460–472
    for col in MULTI_TEST_COLS:
        cap = TEST_LEVEL_CAP.get(col)
        levels = df[col].clip(upper=cap) if cap is not None else df[col]
        by = df.groupby(levels)
        groups = [g["G3"].astype(float).to_numpy() for _, g in by]
        anova = stats.f_oneway(*groups)
        grand = df["G3"].mean()
        ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
        ss_total = float(((df["G3"] - grand) ** 2).sum())
        tests[col] = {"test": "one-way ANOVA", "k_groups": len(groups),
                      "levels": [f"{k}+" if cap is not None and k == cap else str(k) for k in by.groups],
                      "stat": round(float(anova.statistic), 2), "p": _p(anova.pvalue),
                      "eta2": round(float(ss_between / ss_total), 3)}
```

**Gộp mức thưa (`TEST_LEVEL_CAP`):**

```python
# data_processor.py, dòng 45–47
MULTI_TEST_COLS = ["studytime", "absence_level", "failures"]
# Sparse levels merged before ANOVA: failures 2 and 3 have ~12 students each -> one "2+" group
TEST_LEVEL_CAP = {"failures": 2}
```

Trên core, failures 0/1/2/3 có n = 294/40/12/11 (G3 trung bình 11.94/10.15/8.83/8.27). Mức 2 và 3 chỉ ~12 em nên `clip(upper=2)` gộp thành **"2+"** (n = 23) → ANOVA với 3 nhóm, ước lượng ổn định hơn.

**Kết quả thật (core):**

| Biến | k | Nhóm (G3 trung bình, n) | F | p | p_holm | $\eta^2$ |
|---|---|---|---|---|---|---|
| studytime | 4 | 1: 11.47 (92), 2: 11.07 (182), 3: 12.56 (59), 4: 12.67 (24) | 4.38 | 0.00482 | 0.0193 | 0.036 |
| absence_level | 3 | low 12.26 (153), medium 11.38 (121), high 10.37 (83) | 9.85 | 6.9e-05 | 0.00034 | 0.053 |
| failures | 3 | 0, 1, 2+ | 17.19 | 7.5e-08 | 5.3e-07 | 0.089 |

**Ý nghĩa:** cả 3 có ý nghĩa sau Holm, nhưng hiệu ứng **nhỏ**: studytime chỉ giải thích 3.6% phương sai G3, vắng học 5.3%, số lần trượt 8.9% (mạnh nhất trong 3).

## 5. Kiểm định tương quan Pearson (`_corr_tests`)

**Bản chất:** hệ số $r \in [-1, 1]$ đo mức liên hệ tuyến tính với G3:

$$r = \frac{\sum (x_i - \bar x)(y_i - \bar y)}{\sqrt{\sum (x_i - \bar x)^2 \sum (y_i - \bar y)^2}}, \qquad t = r\sqrt{\frac{n-2}{1-r^2}} \sim t_{n-2}$$

Khoảng tin cậy 95% của $r$ dựa trên biến đổi Fisher $z = \operatorname{artanh}(r)$, $SE = 1/\sqrt{n-3}$, tính CI trên $z$ rồi đổi ngược bằng $\tanh$ (đây là cách `scipy` dùng cho `confidence_interval`). Vì vậy CI không đối xứng quanh $r$ khi $|r|$ lớn.

```python
# data_processor.py, dòng 480–488
def _corr_tests(df: pd.DataFrame) -> dict:
    """Pearson r with G3: p-value and 95% CI for each variable."""
    out = {}
    for col in CORR_TEST_COLS:
        res = stats.pearsonr(df[col].astype(float), df["G3"].astype(float))
        ci = res.confidence_interval(1 - ALPHA)
        out[col] = {"r": round(float(res.statistic), 3), "p": _p(res.pvalue),
                    "ci95": [round(float(ci.low), 3), round(float(ci.high), 3)]}
    return out
```

`CORR_TEST_COLS = ["G1", "G2", "studytime", "failures", "absences", "famsup_bin"]` (dòng 50).

**Kết quả thật (core):**

| Biến | r | p | 95% CI |
|---|---|---|---|
| G1 | 0.892 | 2.47e-124 | [0.868, 0.911] |
| G2 | 0.966 | 1.03e-209 | [0.958, 0.972] |
| studytime | 0.127 | 0.0166 | [0.023, 0.228] |
| failures | −0.294 | 1.5e-08 | [−0.386, −0.196] |
| absences | −0.213 | 4.9e-05 | [−0.310, −0.112] |
| famsup | −0.067 | 0.205 | [−0.170, 0.037] |

**Ý nghĩa:** G2 gần như quyết định G3; `failures` và `absences` liên hệ âm vừa phải; `studytime` dương nhưng yếu; `famsup` CI chứa 0 → không có liên hệ. Tương quan không phải nhân quả.

## 6. Đánh giá rule cảnh báo sớm (`_risk_eval`)

**Bản chất:** coi `risk_group == "high"` là "dự báo trượt", so với thực tế `pass_fail == "fail"` qua ma trận nhầm lẫn:

| | Thực tế fail | Thực tế pass |
|---|---|---|
| Rule báo high | TP | FP |
| Rule không báo | FN | TN |

$$\text{Recall} = \frac{TP}{TP + FN} \quad (\text{bắt được bao nhiêu em sẽ trượt}), \qquad \text{Precision} = \frac{TP}{TP + FP} \quad (\text{báo động đúng bao nhiêu})$$

### Recall và Precision nói bằng lời

Cả hai đều lấy tử số là **TP** (rule báo `high` và em đó thật sự trượt), chỉ khác mẫu số:

| | Câu hỏi trả lời | Mẫu số | Lỗi nó phạt |
|---|---|---|---|
| **Recall** (độ phủ) | Trong các em **thật sự trượt**, rule bắt được bao nhiêu em? | TP + FN = tổng số em trượt | **Bỏ sót** (FN): em trượt mà rule ko báo |
| **Precision** (độ chính xác) | Trong các em **rule báo high**, bao nhiêu em thật sự trượt? | TP + FP = tổng số em bị báo | **Báo nhầm** (FP): rule báo mà em vẫn đỗ |

Ví dụ với môn Toán (mat all, n = 395): có 130 em trượt thật (TP 122 + FN 8) và rule báo `high` cho 149 em (TP 122 + FP 27).
- Recall = 122 / 130 = **93.8%** → bỏ sót 8 em trượt.
- Precision = 122 / 149 = **81.9%** → 27 em bị báo nhầm (báo high mà vẫn đỗ).

**Hai chỉ số đánh đổi nhau.** Báo rộng tay (cả `high_or_medium`) thì recall tăng lên 98.5% nhưng precision tụt còn 56.6%. Với cảnh báo sớm, **bỏ sót tốn kém hơn báo nhầm** (em trượt ko được hỗ trợ, còn báo nhầm chỉ tốn thêm một buổi phụ đạo), nên dự án ưu tiên **recall** và chấp nhận precision thấp hơn.

Ko dùng accuracy (tỉ lệ đoán đúng chung) vì lớp "đỗ" chiếm đa số; rule chỉ cần luôn đoán "đỗ" vẫn đúng ~67%.

```python
# data_processor.py, dòng 519–535
def _risk_eval(df: pd.DataFrame) -> dict:
    """Confusion counts of risk flags vs. actual fail (G3 < PASS_MARK): precision and recall."""
    actual = df["pass_fail"] == "fail"
    out = {"n": int(len(df)), "fail_rate": round(float(actual.mean()), 4),
           "fail_rate_by_group": {
               g: round(float(actual[df["risk_group"] == g].mean()), 4)
               for g in ["low", "medium", "high"] if (df["risk_group"] == g).any()}}
    for name, flagged in {"high": df["risk_group"] == "high",
                          "high_or_medium": df["risk_group"] != "low"}.items():
        tp = int((flagged & actual).sum())
        fp = int((flagged & ~actual).sum())
        fn = int((~flagged & actual).sum())
        tn = int((~flagged & ~actual).sum())
        out[name] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                     "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
                     "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0}
    return out
```

### Holdout trên môn Bồ Đào Nha (`_risk_holdout`)

Ngưỡng rule được chọn khi nhìn môn Toán, nên đánh giá trên chính môn Toán dễ lạc quan. Môn `por` đóng vai dữ liệu **ngoài mẫu**. Nhưng nhiều em học cả 2 môn → 2 file không độc lập. **Holdout chặt** bỏ mọi em `por` có bộ `MERGE_KEYS` (13 cột định danh, theo `student-merge.R`) trùng với một em `mat`:

```python
# data_processor.py, dòng 53–54
MERGE_KEYS = ["school", "sex", "age", "address", "famsize", "Pstatus", "Medu", "Fedu",
              "Mjob", "Fjob", "reason", "nursery", "internet"]
```

```python
# data_processor.py, dòng 678–694
    def _risk_holdout(self) -> dict:
        """Evaluate the frozen risk rule on the other subject(s) (out-of-sample).

        The rule thresholds were chosen on the primary subject, so other
        subjects act as holdout data. `holdout_<s>_only` keeps only students
        whose MERGE_KEYS do not appear in the primary subject (no shared pupils).
        """
        primary = self.clean[self.clean["subject"] == self.primary_subject]
        seen = set(map(tuple, primary[MERGE_KEYS].astype(str).to_numpy()))
        out: dict = {}
        for subj, g in self.clean.groupby("subject"):
            if subj == self.primary_subject:
                continue
            shared = g[MERGE_KEYS].astype(str).apply(tuple, axis=1).isin(seen)
            out[f"holdout_{subj}"] = _risk_eval(g)
            out[f"holdout_{subj}_only"] = _risk_eval(g[~shared])
        return out
```

**Vì sao phải "chặt"?** Môn Toán và môn Bồ Đào Nha có nhiều em học **cả hai môn** (cùng một học sinh nằm ở cả 2 file). Nếu lấy cả `por` làm holdout thì phần lớn em trong đó rule đã "nhìn thấy" ở `mat`, nên kết quả vẫn lạc quan. Cách làm của dự án:

1. Mỗi em định danh bằng bộ 13 cột `MERGE_KEYS` (school, sex, age, ... internet). Bộ này lấy theo `student-merge.R` của tác giả UCI, dùng để ghép em xuất hiện ở cả 2 môn.
2. Em `por` nào có bộ khoá trùng một em `mat` → xem là **em đã thấy**, bỏ đi. Từ 649 em `por` bị loại 374 em, còn **275 em**.
3. Giữ nguyên ngưỡng rule (ko tinh chỉnh lại), chỉ chạy `_risk_eval` trên 275 em còn lại.

Vậy **strict holdout** = đánh giá rule **đã đóng băng** trên những học sinh **chưa từng xuất hiện** ở dữ liệu chọn ngưỡng. Đây là ước lượng trung thực nhất vì mô phỏng đúng tình huống thật: dùng rule cho học sinh mới.

**Đọc kết quả:** recall gần như giữ nguyên (93.8% → 91.4%), tức rule vẫn bắt được 64/70 em trượt. Precision tụt (81.9% → 66.0%) một phần vì **precision phụ thuộc tỉ lệ trượt nền**: nhóm `mat` có 32.9% trượt còn holdout chặt chỉ 25.5% trượt, nên cùng một rule sẽ báo nhầm nhiều hơn. Recall ko bị ảnh hưởng bởi tỉ lệ nền này. Đó là lý do chọn recall làm chỉ số chính khi báo cáo.

Caveat: holdout vẫn cùng 2 trường, cùng năm học, nên chưa chứng minh rule dùng được ở trường khác.

**Kết quả thật (rule `high`):**

| Tập | n | TP | FP | FN | TN | Recall | Precision |
|---|---|---|---|---|---|---|---|
| mat all | 395 | 122 | 27 | 8 | 238 | 93.8% | 81.9% |
| mat core | 357 | 86 | 27 | 6 | 238 | 93.5% | 76.1% |
| por all (holdout) | 649 | 90 | 62 | 10 | 487 | 90.0% | 59.2% |
| **por_only (holdout chặt)** | **275** | **64** | **33** | **6** | **172** | **91.4%** | **66.0%** |

Tỉ lệ trượt theo nhóm: mat all low 1.2% / medium 7.8% / high 81.9%; holdout chặt low 0.8% / medium 9.8% / high 66.0%. Nếu báo động cả `high_or_medium` (mat all): recall 98.5%, precision 56.6%.

**Ý nghĩa:** rule bắt được hơn 90% em sẽ trượt cả trên dữ liệu chưa thấy; đổi lại khoảng 1/3 em bị báo `high` trên holdout chặt vẫn đỗ — chấp nhận được với mục đích phụ đạo sớm (bỏ sót tốn kém hơn báo nhầm).

---

## 7. Bảng tra nhanh

| Phương pháp | Hàm (dòng) | Thư viện | Áp dụng cho | Đầu ra | Kết luận chính |
|---|---|---|---|---|---|
| p-value, α | `_p` (427–429), `ALPHA` (43) | — | mọi kiểm định | p làm tròn 3 chữ số | ngưỡng 0.05 để kết luận |
| Welch t-test | `_group_tests` (449–459) | `scipy.stats.ttest_ind(equal_var=False)` | internet, famsup, schoolsup, paid | t, df, p, CI 95% của chênh lệch | internet +0.98 điểm nhưng không có ý nghĩa sau Holm |
| Holm | `_holm` (432–438), gọi ở 473–476 | tự viết | 7 kiểm định cùng họ | p_holm | internet p 0.0268 → 0.0804 |
| One-way ANOVA + η² | `_group_tests` (460–472) | `scipy.stats.f_oneway` | studytime, absence_level, failures (0/1/2+) | F, p, η² | failures η² 0.089 > absences 0.053 > studytime 0.036 |
| Pearson | `_corr_tests` (480–488) | `scipy.stats.pearsonr` | G1, G2, studytime, failures, absences, famsup | r, p, CI 95% | r(G2, G3) = 0.966 |
| Precision / recall + holdout | `_risk_eval` (519–535), `_risk_holdout` (678–694) | pandas | rule `high` vs trượt thật | TP/FP/FN/TN, precision, recall | mat recall 93.8%; holdout chặt recall 91.4%, precision 66.0% |
