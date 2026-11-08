# SPAFS V5.2 — Báo cáo sửa lỗi mô hình, tái cấu trúc và chạy lại kết quả

- **Ngày chạy:** 2026-11-07
- **Nhánh:** `feature/spafs-v5-2-multi-horizon-complete` (thay đổi chưa commit)
- **Môi trường:** Python 3.11 (`D:\Test\env_prj`), pandas 3.0.6, statsmodels 0.15.0 (nâng từ 0.14.4), LightGBM 4.6.0, PyTorch 2.8.0
- **Kiểm thử:** `python -m pytest -q tests` cho **54/54 test đạt**. Trước khi sửa là 36 test; có 18 test mới.

---

## 1. Tóm tắt

Có **8 lỗi** ảnh hưởng tới con số trong báo cáo. Ba lỗi nghiêm trọng nhất là:

1. **M1 (ARMA) không thực sự dự báo trong walk-forward.** Dự báo OOS gần như là một hằng số (độ lệch chuẩn 0,004%, trong khi lợi suất có độ lệch chuẩn khoảng 2%).
2. **M0b ở Stream 1 bị đánh giá trên nhãn hướng 0/1** thay vì trên lợi suất. Vì vậy RMSE, R²_OOS và các kiểm định DM/CW của M0b đều vô nghĩa.
3. **Có 4 bản cài đặt Pesaran–Timmermann, 3 bản DM và 3 bản CW, cho kết quả khác nhau.** Bản trong `metrics.py`, dùng cho leaderboard chính, cộng phương sai thay vì trừ. Bản trong consolidate thì đảo dấu DM và áp dụng CW cho cả các cặp mô hình không lồng nhau.

Sau khi sửa, mọi metric và kiểm định đi qua **một module duy nhất** (`forecast_tests.py`). Mọi walk-forward đi qua **một engine duy nhất** có purging/embargo. Mọi kỳ hạn dùng **cùng các model class** M0a…M5.

**Thay đổi kết luận đáng chú ý nhất:** trước đây, CW được áp cho cặp không lồng nhau nên cho thấy RNN/LSTM "vượt" M2/M4/M5 có ý nghĩa thống kê (p < 0,05 ở nhiều cặp, trên cả ba kỳ hạn). Đây là kết luận sai. DM, kiểm định đúng cho cặp không lồng nhau, cho thấy **không có mô hình DL nào tốt hơn có ý nghĩa** so với ADL hay LightGBM. Ở kỳ hạn ngày, RNN và LSTM còn **kém hơn M2** có ý nghĩa.

---

## 2. Các lỗi đã sửa

| # | Lỗi | File (trước khi sửa) | Hậu quả |
|---|---|---|---|
| 1 | `ArmaModel.predict` gọi `results_.apply(r_τ).predict(start=0)`, tức trả về kỳ vọng **trước khi** quan sát r_τ. Bản in-sample cũng lệch một kỳ, dự báo r_t thay vì r_{t+1}. | `econometric/arma.py` | M1 OOS ≈ trung bình vô điều kiện. Kết luận "ARMA ≈ zero" không phản ánh mô hình thật. |
| 2 | M0b có target trong schema là `target_direction` (0/1), và runner truyền thẳng giá trị này vào walk-forward như lợi suất. | `runner_econometric.py` | `actual_return` của M0b là 0/1. RMSE 2,227 và R²_OOS −8,57 (thực chất là −857%) đều sai. DM/CW với M0b cũng sai. |
| 3 | PT trong `metrics.py`: mẫu số là `√(V̂ + V*)` thay vì `√(V̂ − V*)`, p-value hai phía. | `evaluation/metrics.py` | PT của toàn bộ leaderboard Stream 1/2 bị lệch, và PT của M0a cũng được báo cáo dù không xác định. |
| 4 | PT trong consolidate: mẫu số là `√max(V*, V̂)`. PT còn được báo cáo cho h=5 và h=21, trong khi target chồng lấp vi phạm giả định độc lập. | `consolidate_multi_horizon_analysis.py` | PT tuần/tháng (ví dụ M2 tuần: 3,34) không hợp lệ. |
| 5 | DM trong consolidate: `d = e_gốc² − e_ứngviên²` (ngược dấu so với `pairwise.py`), suy ra `h = max_lags + 1`, và cờ "significant" dùng p-value chưa hiệu chỉnh HLN. | `consolidate_multi_horizon_analysis.py` | Dấu DM ngược giữa các báo cáo, gây nhầm hướng kết luận. |
| 6 | CW được áp cho cả các cặp **không lồng nhau** (M1→M2, M2→M4, mọi cặp DL). Ở h=1, DM dùng 1 lag thay vì h−1 = 0. | consolidate, `pairwise.py` | Sinh ra các kết luận "DL vượt LightGBM" giả. |
| 7 | Runner đa kỳ hạn: M1 thực chất là **trung bình lịch sử** nhưng được gắn nhãn "AR(1)". Có `train_end = 50` khi cửa sổ quá ngắn, tức một lối rò rỉ tiềm ẩn. Siêu tham số M2–M5 bị chép inline thay vì dùng model class. | `runner_multi_horizon_traditional.py` | Bảng đa kỳ hạn của M1 không phải ARMA. Không bảo đảm M2–M5 ở đây giống hệt Stream 1/2. |
| 8 | Audit tái lập: in cứng chuỗi "p < 10^-28", có đường dẫn cứng `C:/Users/.../Downloads`, gắn nhãn M0b là "Historical Expanding Mean" (sai), JSON chứa `NaN`. | `reproducible_pairwise_audit.py` | Báo cáo in ra p-value không lấy từ tính toán thật. |

Ngoài ra còn hai việc:

- **Môi trường:** statsmodels 0.14.4 không tương thích với pandas 3.0.6, nên `import src.models` lỗi `deprecate_kwarg()`. Tôi đã nâng lên 0.15.0.
- **Ngưỡng sốc trong phân tích lỗi:** ±2% và ±3% trước đây áp nguyên cho lợi suất 5 và 21 ngày. Giờ ngưỡng nhân theo √h (tuần: 4,5%/6,7%; tháng: 9,2%/13,7%).

---

## 3. Thay đổi thiết kế (deep module)

| Module | Interface | Thay thế cho |
|---|---|---|
| `src/models/evaluation/forecast_tests.py` | `forecast_metrics(y, pred, *, benchmark, horizon)`, `dm_test(y, cand, bench, *, loss, horizon)`, `cw_test(y, cand, bench, *, horizon)`, `pt_test(y, pred)` | `evaluation/pairwise.py`, `evaluation/metrics.py` (đã xoá), 3 bản trùng trong `reproducible_pairwise_audit.py`, `consolidate_multi_horizon_analysis.py`, `dl/sequence_models.py`, `runner_multi_horizon_traditional.py` |
| `src/models/validation/walk_forward.py` | `run_walk_forward_evaluation(factory, X, y, *, initial_train_size, refit_every, horizon, embargo)` | Engine chỉ hỗ trợ h=1 cũ, vòng lặp inline trong runner đa kỳ hạn, và `purging_and_embargo_partition.py` (đã xoá, vì chỉ dùng trong demo) |
| `ArmaModel(horizon=h)`, `NaiveDirectionModel(horizon=h)` | Thêm tham số `horizon` | Code inline M0b/M1 trong runner đa kỳ hạn |
| `dl/sequence_models.py` → `artifacts/deep_learning/oos_predictions_dl_{h}.csv` | Consolidate chỉ đọc file dự báo | Kiến trúc RNN/LSTM và `create_sequences` chép lại trong consolidate để nạp checkpoint |

Các quy ước được khoá bên trong module, nên caller không thể dùng sai:

- Mọi kiểm định nhận **dự báo**, không nhận sai số.
- Hướng luôn là *ứng viên so với gốc*: DM < 0 hoặc CW > 0 nghĩa là ứng viên tốt hơn, và `p_value_one_sided` luôn kiểm định giả thuyết "ứng viên tốt hơn".
- Băng thông HAC = h−1, suy ra từ `horizon`. DM và CW dùng chung một ước lượng phương sai dài hạn (trọng số uniform như DM 1995 và R `forecast::dm.test`, fallback Bartlett khi phương sai âm).
- PT chỉ báo cáo khi h=1, và là `NaN` khi một chuỗi không đổi dấu (ví dụ M0a).
- Walk-forward huấn luyện trên `t ≤ τ − h − E`, kèm assert chống rò rỉ, và báo lỗi thay vì âm thầm kẹp `train_end`.
- Chuỗi đầu vào được căn theo index và bỏ NaN đồng thời.

---

## 4. Review và kiểm thử

**Test mới** (`tests/test_forecast_tests_and_walk_forward.py`), mỗi test đối chiếu với một công thức đóng hoặc thư viện độc lập:

- DM h=1 khớp công thức đóng. DM đối xứng dấu khi hoán đổi ứng viên/gốc. DM đa bước khớp tổng h−1 tự hiệp phương sai uniform. DM tự căn index Series và bỏ NaN.
- CW h=1 khớp t-stat OLS của statsmodels. CW đa bước dùng cùng phương sai với DM.
- PT khớp công thức Pesaran–Timmermann (1992), là NaN với dự báo hằng, và bị tắt khi h>1.
- Walk-forward với (h, E, refit) ∈ {(1,0,1), (5,2,20), (21,5,7)}: mọi lần fit thoả `train_end + h + E ≤ τ`, và `predict` nhận đúng các dòng `train_end+1..τ`.
- ARMA walk-forward cho dự báo có thông tin (corr > 0,3 trên dữ liệu ARMA mô phỏng). `ArmaModel(horizon=5)` khớp `forecast(5).sum()` của statsmodels.
- M0b với h=5 bằng tổng 5 lợi suất ngày gần nhất.

**Review độc lập:** một agent riêng đã đọc toàn bộ diff và kiểm tra số học trên dữ liệu mô phỏng lẫn parquet thật.

- Agent xác nhận đúng: DM, CW, PT, R²_OOS, purging, ARMA, M0b, cách đấu nối runner, và đẳng thức `target_return_h = Σ r_{t+j}` (sai số 1e-13).
- Agent nêu 5 điểm, đều đã xử lý:
  1. PT cho h>1 → tắt.
  2. CW dùng Bartlett, không nhất quán với DM → thống nhất kernel.
  3. Ngưỡng sốc không theo h → nhân theo √h.
  4. Audit có thể trộn artifact cũ và mới → audit giờ kiểm tra khớp `actual_return` và được chạy cuối cùng.
  5. NaN trong JSON → ghi thành `null`.

**Tái lập DL:** chạy `sequence_models.py` hai lần cho dự báo giống hệt nhau (sai khác tuyệt đối tối đa bằng 0).

---

## 5. Kết quả chạy lại

Thứ tự chạy: `runner_econometric.py` (5 phút 18 giây) → `dl/sequence_models.py` (1 phút 05 giây) → `runner_multi_horizon_traditional.py` (khoảng 3 phút 25 giây) → `runner_ml.py --model all` (khoảng 35 giây) → `consolidate_multi_horizon_analysis.py` → `reproducible_pairwise_audit.py`.

Quy ước:
- R²_OOS tính bằng % so với dự báo 0 (M0a).
- p1 là p-value một phía cho giả thuyết "ứng viên tốt hơn"; p2 là hai phía.
- "—" là không xác định hoặc không áp dụng.

### 5.1 Stream 1 — M0a…M3, 2008–2025, walk-forward refit mỗi ngày, N_OOS = 925 (2022-04-22 → 2025-12-29)

| Model | RMSE mới | RMSE cũ | R²_OOS % mới | R²_OOS % cũ | DA % mới | PT mới | PT cũ | p(PT) mới |
|---|---|---|---|---|---|---|---|---|
| M0a | 2.125 | 2.125 | 0.000 | 0.000 | 48.216 | — | 0.000 | — |
| M0b | 2.921 | 2.227 | -88.986 | -857.472 | 51.568 | 0.916 | 0.914 | 0.180 |
| M1 | 2.139 | 2.125 | -1.355 | -0.017 | 48.108 | -1.107 | -0.047 | 0.866 |
| M2 | 1.709 | 1.709 | 35.293 | 35.293 | 70.054 | 12.266 | 12.224 | 0.000 |
| M3 | 1.710 | 1.710 | 35.197 | 35.197 | 70.162 | 12.335 | 12.291 | 0.000 |

*R²_OOS cũ của M0b là −857% vì RMSE được tính trên nhãn 0/1. PT cũ dùng công thức sai.*

### 5.2 Stream 1 — Kiểm định cặp (h = 1)

| Cặp | DM-HLN mới | p1 mới | p2 mới | DM cũ | CW mới | p(CW) mới | CW cũ |
|---|---|---|---|---|---|---|---|
| M1 vs M0a | 2.389 | 0.991 | 0.017 | 0.836 | -1.649 | 0.950 | -0.781 |
| M2 vs M1 | -7.102 | 0.000 | 0.000 | -7.006 | 10.726 | 0.000 | 10.633 |
| M3 vs M2 | 0.632 | 0.736 | 0.528 | 0.582 | -0.408 | 0.659 | -0.377 |

*Kiểm định Wald RQ1 (Branch A, in-sample) **không thay đổi**: H0 đồng thời F = 0,003 (p = 0,953); H0 tích luỹ F = 0,224 (p = 0,636); H0 lồng nhau F = 0,248 (p = 0,883). Không có bằng chứng truyền dẫn bất đối xứng.*

### 5.3 Stream 2 — Cửa sổ OOS chung 754 phiên (2022-12-28 → 2025-12-29), `reproducible_statistical_tests.json`

M0a…M3 là dự báo walk-forward của Stream 1, giới hạn trên cửa sổ OOS của Stream 2.

| Model | n | rmse | mae | r2_oos_pct | da_pct | mcc | pt_stat |
|---|---|---|---|---|---|---|---|
| M0a | 754 | 1.800 | 1.339 | 0.000 | 48.408 | 0.000 | — |
| M0b | 754 | 2.539 | 1.909 | -98.937 | 51.194 | 0.023 | 0.629 |
| M1 | 754 | 1.803 | 1.345 | -0.291 | 49.072 | -0.017 | -0.456 |
| M2 | 754 | 1.388 | 1.052 | 40.565 | 70.292 | 0.408 | 11.211 |
| M3 | 754 | 1.389 | 1.052 | 40.497 | 70.292 | 0.408 | 11.219 |
| M4 | 754 | 1.422 | 1.071 | 37.609 | 70.822 | 0.416 | 11.420 |
| M5 | 754 | 1.416 | 1.064 | 38.118 | 70.424 | 0.408 | 11.206 |

| Kiểm định | Thống kê | p một phía |
|---|---|---|
| CW M5 vs M4 | 1.807 | 0.035 |
| CW M3 vs M2 | -0.333 | 0.630 |
| CW M5 vs M0a | 10.529 | 0.000 |
| CW M4 vs M0a | 10.650 | 0.000 |
| DM[squared] M5 vs M4 | -0.699 | 0.242 |
| DM[absolute] M5 vs M4 | -1.185 | 0.118 |
| DM[squared] M3 vs M2 | 0.611 | 0.729 |
| DM[absolute] M3 vs M2 | 0.028 | 0.511 |

### 5.4 Đa kỳ hạn — leaderboard tổng hợp (`master_multi_horizon_leaderboard.csv`)

Warmup 1500, refit mỗi 20 phiên, purge = h, embargo E ∈ {0, 2, 5}. DL là ensemble 5 seed huấn luyện một lần (train/validation có purge).

| Kỳ hạn | Model | N | RMSE | R²_OOS % mới | R²_OOS % cũ | DA % | MCC | PT mới | PT cũ |
|---|---|---|---|---|---|---|---|---|---|
| daily | M0a | 754 | 1.800 | 0.000 | 0.000 | 48.408 | 0.000 | — | -0.000 |
| daily | M0b | 754 | 2.539 | -98.937 | -98.937 | 51.194 | 0.023 | 0.629 | 0.628 |
| daily | M1 | 754 | 1.813 | -1.425 | -0.078 | 48.541 | -0.030 | -0.835 | -0.071 |
| daily | M2 | 754 | 1.397 | 39.795 | 39.795 | 69.098 | 0.383 | 10.531 | 10.514 |
| daily | M3 | 754 | 1.401 | 39.446 | 39.446 | 68.833 | 0.379 | 10.405 | 10.382 |
| daily | M4 | 754 | 1.422 | 37.609 | 37.609 | 70.822 | 0.416 | 11.420 | 11.343 |
| daily | M5 | 754 | 1.416 | 38.118 | 38.118 | 70.424 | 0.408 | 11.206 | 11.187 |
| daily | RNN | 754 | 1.440 | 35.998 | 35.998 | 68.833 | 0.383 | 10.535 | 10.447 |
| daily | LSTM | 754 | 1.468 | 33.503 | 33.503 | 67.905 | 0.380 | 10.430 | 10.060 |
| weekly | M0a | 750 | 4.053 | 0.000 | 0.000 | 49.333 | 0.000 | — | 0.000 |
| weekly | M0b | 750 | 6.209 | -134.711 | -134.711 | 42.800 | -0.144 | — | -3.951 |
| weekly | M1 | 750 | 4.058 | -0.263 | -0.331 | 49.733 | -0.010 | — | 0.000 |
| weekly | M2 | 750 | 3.966 | 4.214 | 4.214 | 56.000 | 0.123 | — | 3.338 |
| weekly | M3 | 750 | 3.986 | 3.288 | 3.288 | 56.667 | 0.134 | — | 3.673 |
| weekly | M4 | 750 | 3.959 | 4.559 | 4.559 | 56.533 | 0.130 | — | 3.560 |
| weekly | M5 | 750 | 4.011 | 2.065 | 2.065 | 55.867 | 0.117 | — | 3.192 |
| weekly | RNN | 750 | 4.067 | -0.717 | 1.861 | 54.000 | 0.093 | — | 2.839 |
| weekly | LSTM | 750 | 4.140 | -4.375 | -3.767 | 50.267 | 0.016 | — | -0.243 |
| monthly | M0a | 734 | 6.683 | 0.000 | 0.000 | 50.409 | 0.000 | — | 0.000 |
| monthly | M0b | 734 | 10.603 | -151.696 | -151.696 | 41.144 | -0.177 | — | -4.863 |
| monthly | M1 | 734 | 6.723 | -1.209 | -1.802 | 49.046 | -0.025 | — | 0.000 |
| monthly | M2 | 734 | 7.195 | -15.895 | -15.895 | 50.817 | 0.014 | — | 0.362 |
| monthly | M3 | 734 | 7.218 | -16.640 | -16.640 | 50.136 | -0.001 | — | -0.026 |
| monthly | M4 | 734 | 7.725 | -33.615 | -33.615 | 53.134 | 0.063 | — | 1.702 |
| monthly | M5 | 734 | 7.931 | -40.826 | -40.826 | 51.090 | 0.021 | — | 0.579 |
| monthly | RNN | 734 | 6.956 | -8.343 | -20.541 | 50.136 | -0.036 | — | -0.361 |
| monthly | LSTM | 734 | 9.614 | -106.965 | -99.548 | 52.589 | 0.053 | — | 0.730 |

### 5.5 Đa kỳ hạn — kiểm định cặp (`master_pairwise_hac_tests.csv`, HAC lags = h−1)

Cột "DM cũ" được ghi với dấu ngược (dương nghĩa là ứng viên tốt hơn). CW chỉ báo cáo cho cặp lồng nhau.

| Kỳ hạn | Ứng viên vs Gốc | Lồng? | DM-HLN mới | p1 DM mới | DM cũ (dấu ngược) | CW mới | p1 CW mới | CW cũ | p1 CW cũ |
|---|---|---|---|---|---|---|---|---|---|
| daily | M1 vs M0a | có | 1.339 | 0.909 | -1.210 | 0.147 | 0.441 | -1.101 | 0.864 |
| daily | M2 vs M0a | có | -6.715 | 0.000 | 6.601 | 10.697 | 0.000 | 10.294 | 0.000 |
| daily | M4 vs M0a | có | -7.210 | 0.000 | 7.066 | 10.650 | 0.000 | 10.182 | 0.000 |
| daily | M5 vs M0a | có | -7.213 | 0.000 | 7.052 | 10.529 | 0.000 | 10.013 | 0.000 |
| daily | M2 vs M1 | không | -6.939 | 0.000 | 6.593 | — | — | 10.279 | 0.000 |
| daily | M3 vs M2 | có | 2.966 | 0.998 | -2.905 | -2.735 | 0.997 | -2.688 | 0.996 |
| daily | M4 vs M2 | không | 1.231 | 0.891 | -1.237 | — | — | 3.167 | 0.001 |
| daily | M5 vs M4 | có | -0.699 | 0.242 | 0.774 | 1.807 | 0.035 | 1.969 | 0.024 |
| daily | RNN vs M2 | không | 2.169 | 0.985 | -2.223 | — | — | 1.886 | 0.030 |
| daily | LSTM vs M2 | không | 2.843 | 0.998 | -2.900 | — | — | 2.172 | 0.015 |
| daily | RNN vs M4 | không | 0.865 | 0.806 | -0.861 | — | — | 3.818 | 0.000 |
| daily | LSTM vs M4 | không | 1.930 | 0.973 | -1.915 | — | — | 3.278 | 0.001 |
| daily | RNN vs M5 | không | 1.224 | 0.889 | -1.239 | — | — | 3.167 | 0.001 |
| daily | LSTM vs M5 | không | 2.347 | 0.990 | -2.338 | — | — | 2.510 | 0.006 |
| weekly | M1 vs M0a | có | 0.651 | 0.742 | -1.209 | -0.138 | 0.555 | -1.077 | 0.859 |
| weekly | M2 vs M0a | có | -1.769 | 0.039 | 1.744 | 5.086 | 0.000 | 5.211 | 0.000 |
| weekly | M4 vs M0a | có | -1.393 | 0.082 | 1.509 | 3.923 | 0.000 | 4.302 | 0.000 |
| weekly | M5 vs M0a | có | -0.740 | 0.230 | 0.782 | 3.432 | 0.000 | 3.687 | 0.000 |
| weekly | M2 vs M1 | không | -1.732 | 0.042 | 1.811 | — | — | 5.243 | 0.000 |
| weekly | M3 vs M2 | có | 1.839 | 0.967 | -1.788 | -0.947 | 0.828 | -0.911 | 0.819 |
| weekly | M4 vs M2 | không | -0.128 | 0.449 | 0.138 | — | — | 2.418 | 0.008 |
| weekly | M5 vs M4 | có | 0.923 | 0.822 | -1.019 | 0.743 | 0.229 | 0.835 | 0.202 |
| weekly | RNN vs M2 | không | 1.913 | 0.972 | -1.406 | — | — | 0.304 | 0.381 |
| weekly | LSTM vs M2 | không | 2.227 | 0.987 | -2.788 | — | — | 0.981 | 0.163 |
| weekly | RNN vs M4 | không | 1.353 | 0.912 | -0.864 | — | — | 1.453 | 0.073 |
| weekly | LSTM vs M4 | không | 1.812 | 0.965 | -2.242 | — | — | 1.077 | 0.141 |
| weekly | RNN vs M5 | không | 0.783 | 0.783 | -0.073 | — | — | 2.735 | 0.003 |
| weekly | LSTM vs M5 | không | 1.431 | 0.924 | -1.788 | — | — | 1.887 | 0.030 |
| monthly | M1 vs M0a | có | 0.762 | 0.777 | -1.186 | -0.580 | 0.719 | -1.044 | 0.852 |
| monthly | M2 vs M0a | có | 1.394 | 0.918 | -1.515 | 0.720 | 0.236 | 0.791 | 0.214 |
| monthly | M4 vs M0a | có | 2.435 | 0.992 | -2.858 | -0.355 | 0.639 | -0.408 | 0.658 |
| monthly | M5 vs M0a | có | 2.500 | 0.994 | -2.930 | -0.092 | 0.537 | -0.104 | 0.541 |
| monthly | M2 vs M1 | không | 1.159 | 0.877 | -1.199 | — | — | 1.109 | 0.134 |
| monthly | M3 vs M2 | có | 0.570 | 0.716 | -0.622 | -0.024 | 0.509 | -0.026 | 0.510 |
| monthly | M4 vs M2 | không | 0.894 | 0.814 | -1.009 | — | — | 1.493 | 0.068 |
| monthly | M5 vs M4 | có | 0.396 | 0.654 | -0.466 | 1.529 | 0.063 | 1.768 | 0.039 |
| monthly | RNN vs M2 | không | -1.098 | 0.136 | -0.569 | — | — | 2.219 | 0.013 |
| monthly | LSTM vs M2 | không | 1.437 | 0.924 | -1.790 | — | — | 1.761 | 0.039 |
| monthly | RNN vs M4 | không | -1.261 | 0.104 | 0.694 | — | — | 3.268 | 0.001 |
| monthly | LSTM vs M4 | không | 1.167 | 0.878 | -1.436 | — | — | 2.478 | 0.007 |
| monthly | RNN vs M5 | không | -1.634 | 0.051 | 1.179 | — | — | 3.769 | 0.000 |
| monthly | LSTM vs M5 | không | 1.193 | 0.883 | -1.452 | — | — | 1.846 | 0.032 |

---

## 6. Kết luận sau khi sửa

1. **Kỳ hạn ngày:** M2, M3, M4 và M5 đều vượt dự báo 0 rất rõ (CW ≈ 10,5, p < 10⁻²⁰). Năng lực dự báo hướng cũng có ý nghĩa (PT ≈ 10,4–12,3). Kết luận này **không đổi**.
2. **M5 so với M4 (spread lọc dầu, RQ2):**
   - CW = 1,81, p = 0,035: có ý nghĩa ở mức 5%, yếu hơn so với trước (1,97, p = 0,024).
   - DM bình phương: p1 = 0,24; DM tuyệt đối: p1 = 0,12. Không có ý nghĩa.
   - Kết luận vẫn là *bằng chứng yếu, chỉ có ý nghĩa theo CW*.
3. **M3 so với M2 (bất đối xứng, RQ1):** không có ý nghĩa ở bất kỳ kỳ hạn nào. Ở kỳ hạn ngày của bộ đa kỳ hạn, M3 còn **kém hơn** M2 (DM p2 ≈ 0,004).
4. **M1 ARMA thật:** kém hơn dự báo 0 một chút. Ở Stream 1: R²_OOS = −1,36%, DM p2 = 0,017, tức kém hơn có ý nghĩa ở kiểm định hai phía.
5. **M0b (persistence):** RMSE thực là 2,92 (Stream 1). Rất kém ở mọi kỳ hạn: R²_OOS từ −89% đến −152%.
6. **Kỳ hạn tuần:** M2 vượt M0a theo CW (5,09) và theo DM một phía (p = 0,039). M4 và M5 vượt theo CW. Mức cải thiện nhỏ (R²_OOS 2–4,6%).
7. **Kỳ hạn tháng:** không mô hình nào vượt dự báo 0. Mọi R²_OOS đều âm (M2 −15,9%, M5 −40,8%, LSTM −107%).
8. **Deep learning:** không có cặp nào DL tốt hơn ADL hay LightGBM có ý nghĩa theo DM. Kết luận cũ dựa trên CW cho cặp không lồng nhau đã bị **loại bỏ**.

---

## 7. Hạn chế và việc chưa làm

- **Chưa cập nhật** `SPAFS_DELIVERABLES_PACKAGE/` (cả bản `.zip`) và các báo cáo `.docx` hay `.md` cũ. Các file đó vẫn chứa số liệu cũ. Script `generate_training_logs_and_package.py` vẫn tham chiếu `purging_and_embargo_partition.py`; script này tự sinh lại file đó nên vẫn chạy được, nhưng file sinh ra là bản demo tách rời.
- DL chỉ huấn luyện **một lần** (không refit theo walk-forward như M0a…M5), nên so sánh với các mô hình truyền thống chưa hoàn toàn cùng giao thức.
- Registry `PAIRWISE_COMPARISONS` của Stream 1 vẫn yêu cầu CW cho cặp M2 vs M1. Cặp này không lồng nhau theo nghĩa chặt (ARMA so với ADL), nên nên đọc theo DM. Registry cũng có một dòng M3 vs M2 bị trùng.
- Các file `.joblib`, checkpoint DL và manifest trong `artifacts/` đã được ghi đè bằng kết quả mới. Bản sao kết quả cũ chỉ được giữ tạm để so sánh và không nằm trong repo.
