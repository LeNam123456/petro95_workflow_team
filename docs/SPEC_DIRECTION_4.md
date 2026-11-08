# Spec: Tối ưu hóa & Tái cấu trúc Hệ thống Dự báo Khoảng dao động và Rủi ro Đa kỳ hạn (SPAFS V5.2 — Hướng 4)

Status: ready-for-agent

---

## Problem Statement

Trong bài toán dự báo chuẩn giá xăng thành phẩm bán buôn **Platts Mogas 95 Assessment (MG95)** tại thị trường Singapore ở 3 kỳ hạn **Horizon Return ($r_{t,h}$)** gồm 1 ngày ($h = 1$), 1 tuần ($h = 5$) và 1 tháng ($h = 21$):

1. **Giới hạn của dự báo điểm ở kỳ hạn trung và dài hạn:** Ở kỳ hạn 1 ngày ($h = 1$), độ trễ múi giờ từ giá thanh toán hợp đồng tương lai **ICE Brent Futures (Brent)** chốt phiên đêm qua trước mốc **Forecast Origin ($\tau = \text{08:30 SGT}$)** giúp mô hình hồi quy động tuyến tính dự báo đúng hướng ~70% và giảm ~39.8% sai số bình phương trung bình. Tuy nhiên, ở kỳ hạn 1 tuần ($h = 5$) và 1 tháng ($h = 21$), hướng đi của lợi suất gần như là bước đi ngẫu nhiên đối với tập thông tin giá giao ngay và tin tức quá khứ ($R^2_{\text{OOS}} < 0$ ở kỳ hạn tháng). Doanh nghiệp nhập khẩu xăng dầu, thương nhân phân phối và cơ quan điều hành Quỹ bình ổn giá không thể dựa vào dự báo điểm trung hạn để lập ngân sách hay phòng vệ rủi ro.
2. **Hiện tượng trượt dồn cục (Miss Clustering) trong khủng hoảng của mô hình hồi quy phân vị tuyến tính ban đầu (`Q3`):** Khi ước lượng **Quantile Forecast** bằng hồi quy phân vị tuyến tính dùng biên độ biến động trung bình trượt mũ (EWMA), mô hình thu hẹp **Prediction Interval (Khoảng dự báo 80% và 95%)** rất tốt ở kỳ hạn 1 ngày nhưng phản ứng chậm khi thị trường bước vào chuỗi sốc khủng hoảng liên tiếp trên **Stream 1 (Long-Horizon Robustness Sample, 2008–2025)**, dẫn đến vi phạm **Independence Test (Kiểm định Christoffersen)** ($p = 0.007 < 0.05$).
3. **Hiện tượng khoảng dự báo quá rộng (Over-coverage) khi chuyển chế độ thị trường trên Luồng 2:** Trên **Stream 2 (Primary Aligned Sample, 2017–2025)**, cửa sổ huấn luyện (2017–2022) chứa hai cuộc khủng hoảng lớn (COVID-19 năm 2020 và xung đột Nga–Ukraine năm 2022), trong khi giai đoạn kiểm tra ngoài mẫu (2023–2025) lại rất yên ả. Cơ chế **Filtered Historical Simulation (FHS)** lấy phân vị đồng đều trên toàn bộ lịch sử huấn luyện làm phình bộ nhân phân vị, khiến **Empirical Coverage** của khoảng 80% vọt lên 88.6%–95.0% ở kỳ hạn tháng và bị bác bỏ bởi **Unconditional Coverage Test (Kiểm định Kupiec)**.
4. **Mất nhãn rủi ro đầu kỳ và méo tham chiếu trong phân loại `Ex-Ante Risk Regime`:** Việc chỉ xếp hạng độ rộng khoảng dự báo 80% nội bộ trong tập kiểm tra ngoài mẫu làm mất trắng nhãn rủi ro ở 60 phiên đầu tiên (`NaN`), đồng thời khiến giai đoạn yên ả 2023–2025 tự so sánh nội bộ và gắn nhãn "Rủi ro Cao" giả tạo cho những phiên biến động nhẹ.
5. **Thiếu hụt chỉ số rủi ro đuôi bất đối xứng và bảng quyết định vận hành hợp nhất:** Các bên liên quan cần biết rõ **Upside & Downside Tail Risk** ở mức 95%/97.5% và cần một **Unified Multi-Horizon Decision Card** kết nối dự báo điểm ngắn hạn với dự báo khoảng/rủi ro đa kỳ hạn trên một cấu trúc kho mã nguồn tinh gọn, tuân thủ nghiêm ngặt quản trị Point-in-Time và các quyết định kiến trúc (`ADR-0001` đến `ADR-0005`).

---

## Solution

Xây dựng và hoàn thiện hệ thống **Dự báo Khoảng dao động, Phân vị Lợi suất và Phân tầng Rủi ro Đa kỳ hạn (Hướng 4)** trên nền tảng SPAFS V5.2 với 4 trụ cột giải pháp đã được kiểm chứng qua bản mẫu (`/prototype`):

1. **Nâng cấp kiến trúc mô hình phân vị (`Q0–Q4`) với Phân rã Vị trí – Quy mô Có điều kiện và FHS Thích ứng Thời gian:**
   - Áp dụng **Conditional Location–Scale Decomposition** cho mô hình `Q3`: kết hợp thành phần dịch chuyển vị trí (Location) từ truyền dẫn lợi suất dầu thô **ICE Brent Futures (Brent)** qua đêm (cả dấu và độ lớn) cùng **Lagged Equilibrium Spread ($\text{Spread}_{t-1}$)** với thành phần co giãn biên độ (Scale) từ căn bậc hai phương sai dự báo $h$ bước của GARCH(1,1)-$t$. Giải pháp này giữ nguyên lợi thế giảm ~26% **Pinball Loss** ở kỳ hạn 1 ngày đồng thời triệt tiêu hoàn toàn hiện tượng trượt dồn cục trong khủng hoảng (**Independence Test** $p = 0.068 > 0.05$, **Conditional Coverage Test** $LR_{cc}\ p = 0.124 > 0.05$).
   - Áp dụng **Filtered Historical Simulation (FHS)** có trọng số suy giảm mũ theo thời gian (`half_life = 756` phiên giao dịch $\approx 3$ năm) cho các mô hình dựa trên FHS (`Q1, Q2`), giúp khoảng dự báo tự động thu hẹp hợp lý khi thị trường chuyển sang chế độ yên ả trên **Stream 2** mà vẫn bảo toàn đuôi dày thực nghiệm trên **Stream 1**.
   - Trang bị bộ ước lượng hợp lý cực đại (MLE) GARCH(1,1) phân phối Student-$t$ tự chủ kèm cơ chế đóng băng trạng thái phương sai sau khi huấn luyện (`Frozen Post-Fit State`), đảm bảo tính lũy đẳng 100% khi gọi dự báo lặp giữa hai chu kỳ ước lượng lại (mỗi 20 phiên).
2. **Chuẩn hóa Phân tầng Chế độ Rủi ro Tiền nghiệm (`Ex-Ante Risk Regime`) & Bộ Kiểm định Khoảng:**
   - Khởi tạo lịch sử xếp hạng độ rộng khoảng dự báo 80% từ tập huấn luyện (`Seeded Expanding Historical Rank`) kết hợp xếp hạng trên cửa sổ trượt 1 năm giao dịch (252 phiên), đảm bảo 100% các phiên ngoài mẫu đều có nhãn rủi ro hợp lệ ngay từ ngày đầu tiên và phản ánh trung thực mặt bằng rủi ro lịch sử.
   - Bổ sung kiểm định hợp nhất **Conditional Coverage Test ($LR_{cc} = LR_{uc} + LR_{ind} \sim \chi^2_2$)** trên **Non-Overlapping Evaluation Subsample** (lấy mẫu mỗi $h$ phiên) và thống kê Mincer–Zarnowitz $R^2$ / Spearman $p$-value để đánh giá toàn diện cả 4 câu hỏi nghiên cứu `RQ4a`–`RQ4d`.
3. **Đóng gói Sản phẩm Ra Quyết định Thực tiễn (`Unified Multi-Horizon Decision Card` & `Upside/Downside Tail Risk`):**
   - Trích xuất trực tiếp **Upside & Downside Tail Risk** ($q_{0.95}, q_{0.975}$ cho rủi ro vọt giá nhập khẩu; $q_{0.05}, q_{0.025}$ cho rủi ro sụt giảm giá trị tồn kho).
   - Tự động xuất **Unified Multi-Horizon Decision Card** tại mỗi mốc **Forecast Origin ($\tau = \text{08:30 SGT}$)**, ghép nối dự báo điểm/hướng kỳ hạn 1 ngày ($M2$) với **Prediction Interval (80% & 95%)**, **Probability of Increase ($P(\text{tăng})$)**, rủi ro đuôi và **Ex-Ante Risk Regime** của mô hình khuyến nghị ở từng kỳ hạn (1 ngày: `Q3`, 1 tuần: `Q3`, 1 tháng: `Q2`).
4. **Quy hoạch Kho mã nguồn & Tài liệu Miền Chuẩn hóa:**
   - Tổ chức kho dự án xoay quanh 3 luồng thực thi độc lập (`data`, `point`, `risk`) với tầng quản trị kiến trúc tập trung (`GLOSSARY.md`, `ADR 0001–0005`, `issue-tracker.md`, `domain.md`, `triage-labels.md`) và mục lục báo cáo phân nhánh rõ ràng.

---

## User Stories

1. **As a** petroleum import manager (doanh nghiệp nhập khẩu xăng dầu), **I want** a calibrated 80% and 95% **Prediction Interval** for 1-day, 1-week, and 1-month **Horizon Return ($r_{t,h}$)** before 08:30 SGT each trading day, **so that** I can set fuel procurement budgets and hedge exposure within known probability bounds.
2. **As a** petroleum import manager, **I want** explicit **Upside Tail Risk** metrics ($q_{0.95}$ and $q_{0.975}$) across 5-session and 21-session horizons, **so that** I can quantify worst-case import price spikes when scheduling physical cargo deliveries 15–30 days out.
3. **As a** refinery and inventory risk officer (quản trị tồn kho xăng dầu), **I want** explicit **Downside Tail Risk** metrics ($q_{0.05}$ and $q_{0.025}$), **so that** I can measure potential inventory valuation drawdowns during sharp crude oil sell-offs.
4. **As a** price stabilization fund regulator (cơ quan điều hành Quỹ bình ổn giá), **I want** an **Ex-Ante Risk Regime** classification (Low / Normal / High Risk) that discriminates high-volatility periods where realized price swings are $2.1\text{–}3.4\times$ larger than low-risk periods, **so that** I can prepare stabilization fund buffers ahead of market turbulence.
5. **As a** short-term trading analyst, **I want** the 1-day **Quantile Forecast** (`Q3`) to shift its location dynamically in response to overnight **ICE Brent Futures (Brent)** returns and **Lagged Equilibrium Spread ($\text{Spread}_{t-1}$)**, **so that** the 1-day 80% interval is ~25–32% narrower than naive historical simulation while capturing directional momentum.
6. **As a** short-term trading analyst, **I want** a calibrated **Probability of Increase ($P(\text{tăng})$)** derived consistently from the 9-quantile forecast distribution, **so that** I can evaluate directional conviction alongside interval width.
7. **As a** quantitative researcher, **I want** `Q3` to scale its quantile dispersion using $h$-step conditional volatility from GARCH(1,1)-$t$ rather than slow-moving EWMA variance, **so that** 1-day intervals expand rapidly during crisis shocks and pass both the **Independence Test (Christoffersen $LR_{ind}$)** and **Conditional Coverage Test ($LR_{cc}$)**.
8. **As a** quantitative researcher, **I want** **Filtered Historical Simulation (FHS)** to weight standardized historical residuals with exponential time decay (`half_life = 756` sessions), **so that** forecasts during prolonged calm periods (**Stream 2**, 2023–2025) do not suffer from severe over-coverage caused by legacy crisis shocks (2020, 2022).
9. **As a** quantitative researcher, **I want** `Q0` (Historical Simulation) to remain an unweighted, full-history static benchmark, **so that** dynamic models (`Q1–Q4`) are evaluated against a true unconditional baseline via **Pinball Loss** and Diebold–Mariano tests.
10. **As a** quantitative researcher, **I want** the GARCH(1,1)-$t$ volatility engine to include a self-contained Student-$t$ maximum likelihood estimator alongside the external econometric library wrapper, **so that** `Q2` and `Q3` execute deterministically and pass all tests even in minimal Python environments.
11. **As a** quantitative model validator, **I want** the post-fit variance recursion state ($\sigma^2_{\text{fit}}$) of EWMA and GARCH models to be frozen at the end of each training window, **so that** repeated predictions between two 20-session refit points are 100% idempotent and never compound variance state across calls.
12. **As a** quantitative model validator, **I want** both point forecasters ($M0a\text{–}M5$) and quantile forecasters ($Q0\text{–}Q4$) to share a single **Purge Gap ($h$) & Embargo ($E$)** walk-forward loop where training rows satisfy $t \le \tau - h - E$, **so that** multi-horizon evaluations are guaranteed free of lookahead leakage.
13. **As a** data governance auditor, **I want** every feature entering `Q0–Q4` to be strictly available at or before **Forecast Origin ($\tau = \text{08:30 SGT}$)**, **so that** no same-calendar-day London/NY Brent settlement or future Platts MOC assessment leaks into the forecast.
14. **As a** statistical reviewer, **I want** **Unconditional Coverage Test (Kupiec)**, **Independence Test (Christoffersen)**, and **Conditional Coverage Test ($LR_{cc}$)** to be computed on the **Non-Overlapping Evaluation Subsample** (every $h$-th origin for $h \in \{5, 21\}$), **so that** mechanical serial correlation from overlapping target windows does not cause false test rejections.
15. **As a** statistical reviewer, **I want** Diebold–Mariano pairwise comparisons on **Pinball Loss** to use Harvey–Leybourne–Newbold small-sample adjustment and Newey–West HAC variance with $h - 1$ lags across all origins, **so that** model ranking significance is statistically rigorous.
16. **As a** statistical reviewer, **I want** all 5 models (`Q0–Q4`) evaluated on both **Stream 2 (Primary Aligned Sample, 2017–2025)** and **Stream 1 (Long-Horizon Robustness Sample, 2008–2025)**, **so that** model calibration and **Risk Discrimination Ratio** are proven across both tranquil and crisis-heavy market regimes.
17. **As a** statistical reviewer, **I want** the **Ex-Ante Risk Regime** percentile rank to support seeding from historical training widths as well as a 252-session rolling window, **so that** the first 60 out-of-sample forecasts are not discarded as `NaN` and calm regimes are benchmarked against realistic historical volatility distributions.
18. **As a** thesis advisor or executive decision-maker, **I want** a single **Unified Multi-Horizon Decision Card** combining the 1-day point forecast, median, 80%/95% intervals, $P(\text{tăng})$, 95% Upside/Downside Tail VaR, and risk regime label across 1-day, 1-week, and 1-month horizons, **so that** I can interpret the system's operational recommendation at a glance.
19. **As a** project maintainer or AI engineering agent, **I want** all domain terms, architectural trade-offs, and issue tracking conventions documented in `GLOSSARY.md`, `ADR 0001–0005`, and agent configuration docs, **so that** future changes preserve domain language and architectural invariants.

---

## Implementation Decisions

1. **Unified Quantile Forecaster Contract (`make_risk_model`):**
   - Mọi mô hình trong thang `RISK_MODEL_IDS = ("Q0", "Q1", "Q2", "Q3", "Q4")` đều được khởi tạo qua một hàm nhà máy duy nhất nhận `(model_id, horizon)` và cung cấp đúng 2 phương thức công khai: `.fit(X, y)` và `.predict_quantiles(X) -> DataFrame`.
   - Đầu ra của `.predict_quantiles(X)` luôn là bảng 9 mức xác suất `LEVELS = (0.025, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.975)` đã được sắp xếp chống cắt chéo phân vị (non-crossing quantile rearrangement theo Chernozhukov et al., 2010).
2. **Immutable Post-Fit Volatility Recursion State:**
   - Các bộ lọc phương sai có trạng thái (`_EwmaVariance` và `GarchFHS`) chạy đệ quy trên cửa sổ huấn luyện trong lúc `.fit()` và đóng băng trạng thái phương sai cuối tập huấn luyện (`fit_state` / `_state`).
   - Khi `.predict_quantiles(X)` được gọi trên các dòng nối tiếp sau cửa sổ huấn luyện (từ `train_end + 1` đến $\tau$), phép đệ quy phương sai $h$ bước luôn khởi động lại từ trạng thái đóng băng mà không bao giờ ghi đè trạng thái nội tại, đảm bảo gọi dự báo lặp bao nhiêu lần giữa hai kỳ refit (20 phiên) vẫn cho kết quả y hệt nhau.
3. **Conditional Location–Scale Decomposition cho `Q3`:**
   - Thay thế biến quy mô EWMA đơn thuần trong hồi quy phân vị tuyến tính (`Q3`) bằng căn bậc hai phương sai dự báo $h$ bước của GARCH(1,1)-$t$:
     $$\hat{q}_{\alpha}(X_\tau) = \beta_{0,\alpha} + \beta_{\sigma,\alpha}\hat{\sigma}_{\text{GARCH}, h, \tau} + \beta_{b,\alpha} r_{\text{Brent},\tau} + \beta_{|b|,\alpha} |r_{\text{Brent},\tau}| + \beta_{m,\alpha} r_{\text{MG95},\tau} + \beta_{s,\alpha}\text{Spread}_{\tau-1} + \beta_{\text{shock},\alpha}\mathbb{I}_{\text{shock},\tau}$$
   - Thiết kế này tách bạch sự dịch chuyển trung tâm theo cú sốc dầu Brent qua đêm và sự nở rộng biên độ theo phương sai có điều kiện GARCH(1,1)-$t$.
4. **Time-Decayed Filtered Historical Simulation (FHS) & Self-Contained GARCH(1,1)-$t$ MLE:**
   - Trong lớp cơ sở `_ScaleFHS` (dùng cho `Q1` và `Q2`), các phần dư chuẩn hóa $z_t = y_t / \hat{\sigma}_{h,t}$ (sau giai đoạn burn-in 63 phiên) được lấy phân vị có trọng số suy giảm mũ theo thời gian với chu kỳ bán rã `fhs_half_life = 756` phiên giao dịch ($\approx 3$ năm). Riêng `Q0` giữ `fhs_half_life = None` để đóng vai trò chuẩn đối chứng lịch sử tĩnh.
   - Bộ ước lượng tham số GARCH(1,1)-$t$ ưu tiên gọi thư viện kinh tế lượng chuyên dụng và tự động chuyển sang tối ưu hợp lý cực đại (L-BFGS-B trên hàm hợp lý Student-$t$ chuẩn hóa phương sai với độ trễ nhân quả $\sigma_t^2 = \omega + \alpha \varepsilon_{t-1}^2 + \beta \sigma_{t-1}^2$) nếu môi trường thiếu thư viện ngoài.
5. **Purged Split Conformal Quantile Regression (`Q4`):**
   - Tách 20% cuối cửa sổ huấn luyện (`calib_frac = 0.2`, tối thiểu 50 phiên) làm tập hiệu chỉnh conformal, đồng thời đặt một khoảng **Purge Gap ($h$)** giữa phần proper-training và phần calibration (`train_end = cal_start - horizon`) để không có nhãn $h$ bước nào chồng lấp giữa tập học cây LightGBM và tập tính điểm bất tương thích $E_i = \max(\hat{q}_{\alpha/2} - y_i, y_i - \hat{q}_{1-\alpha/2})$.
   - Ngưỡng điều chỉnh conformal được lấy theo thống kê thứ tự hữu hạn mẫu (`method="higher"` ở mức $\lceil (n_{\text{cal}} + 1)(1 - \alpha) \rceil / n_{\text{cal}}$).
6. **State & Decision Card Schema (Từ bản mẫu Logic Prototype):**
   - Bản mẫu `/prototype` đã xác lập cấu trúc trạng thái bất biến tại mỗi mốc dự báo và lược đồ đầu ra của **Unified Multi-Horizon Decision Card**:

```ts
// Trimmed from logic prototype: invariant state & decision card contract at Forecast Origin tau
interface ForecastOriginState {
  originTimestamp: "08:30 SGT";
  purgedTrainEnd: number;          // train_end <= tau - horizon - embargo
  frozenGarchSigma1d: number;      // immutable post-fit variance state from train_end
  liveGarchSigma1d: number;        // causally filtered from frozenGarchSigma1d through tau
  fhsHalfLifeSessions: number | null; // 756 for adaptive Q1/Q2; null for static Q0
}

interface UnifiedDecisionCardRow {
  horizon: "daily" | "weekly" | "monthly";
  origin_date: string;
  recommended_model: "Q3" | "Q2";  // Q3 for daily/weekly; Q2 for monthly
  point_forecast_pct: number;      // M2 point forecast at h=1, median q0.50 at h=5, 21
  median_q50_pct: number;
  interval_80_pct: string;         // [q0.10, q0.90]
  interval_95_pct: string;         // [q0.025, q0.975]
  prob_up_pct: number;             // 1 - CDF(0) interpolated across 9 quantiles
  upside_tail_q95_pct: number;     // importer upside price-spike VaR (95%)
  downside_tail_q05_pct: number;   // inventory downside valuation VaR (95%)
  risk_regime_percentile: number;  // ex-ante historical rank of width_80
  ex_ante_risk_regime: "THẤP (Low)" | "TRUNG BÌNH (Normal)" | "CAO (High)";
}
```

7. **Comprehensive Interval & Risk Evaluation Contract (`evaluate_quantile_forecast`):**
   - Tính toán đầy đủ trong một lần gọi hàm:
     - **Bao phủ & Độ sắc:** `coverage_80`, `coverage_95`, `width_80`, `width_95`, `winkler_80`, `winkler_95`, `pinball`, `qlike`.
     - **Kiểm định hiệu chỉnh trên mẫu không chồng lấp (`miss[::horizon]`):** `kupiec_p_80`, `kupiec_p_95` ($LR_{uc}$), `christoffersen_p_80`, `christoffersen_p_95` ($LR_{ind}$), và `cc_p_80`, `cc_p_95` ($LR_{cc} = LR_{uc} + LR_{ind} \sim \chi^2_2$).
     - **Rủi ro đuôi & Xác suất hướng:** `upside_var_95_mean`, `upside_var_975_mean`, `downside_var_05_mean`, `downside_var_025_mean`, `brier`, `log_loss`, `brier_skill_pct`.
     - **Phân biệt chế độ rủi ro tiền nghiệm:** `spearman_width_absret`, `spearman_p_width_absret`, `mz_r2`, `realized_sd_high_risk`, `realized_sd_low_risk`, `risk_ratio_high_low` (hỗ trợ `history_width_80` khởi tạo từ tập train) và `risk_ratio_rolling_252` (cửa sổ trượt 252 phiên).

---

## Seams & Testing Decisions

### Primary Seams (3 Seams tối giản, bậc cao nhất)

Toàn bộ tính năng của Hướng 4 được kiểm thử đi qua đúng **3 seam giao diện bậc cao đã có sẵn** (không tạo thêm seam phụ hay mock chi tiết nội bộ):

1. **Seam 1 — Model Factory & Quantile Forecaster Seam (`make_risk_model(model_id, horizon)`):**
   - Giao diện: `.fit(X, y) -> self` và `.predict_quantiles(X) -> DataFrame[index=X.index, columns=LEVELS]`.
   - Che giấu hoàn toàn bên trong: phép đệ quy EWMA/GARCH, bộ ước lượng MLE Student-$t$, chuẩn hóa FHS có trọng số thời gian, ma trận thiết kế Location–Scale của `Q3`, tập hiệu chỉnh conformal có purge của `Q4` và bước sắp xếp chống cắt chéo phân vị.
2. **Seam 2 — Shared Walk-Forward Validation Seam (`run_walk_forward_quantiles(model_factory, X, y, *, initial_train_size, refit_every, horizon, embargo)`):**
   - Giao diện: Nhận hàm khởi tạo mô hình và chuỗi thời gian $(X, y)$, trả về `DataFrame` gồm `actual_return` và 9 cột phân vị `LEVELS` trên toàn bộ cửa sổ ngoài mẫu.
   - Bảo chứng bất biến chống rò rỉ dữ liệu: tại mọi mốc $\tau$, `train_end + horizon + embargo <= tau`, và mô hình nhận đúng lát cắt `X.iloc[train_end + 1 : tau + 1]`.
3. **Seam 3 — Interval Evaluation & Decision Card Seam (`evaluate_quantile_forecast`, `compare_quantile_forecasts`, `build_unified_decision_card`):**
   - Giao diện: Nhận chuỗi thực tế `y` và bảng phân vị dự báo `quantiles`, trả về từ điển chỉ số kiểm định chuẩn hóa, đối tượng `TestResult` của kiểm định Diebold–Mariano (HLN HAC $h-1$ lags), và bảng `DataFrame` của **Unified Multi-Horizon Decision Card**.

### What Makes a Good Test & Prior Art

- **Chỉ kiểm thử hành vi quan sát được từ bên ngoài qua 3 Seam trên (Black-box behavioral testing):**
  - *Kiểm thử công thức đóng (Closed-form analytical verification):* Đối chiếu `pinball_loss`, `kupiec_test`, `christoffersen_test`, `conditional_coverage_test` và công thức cộng dồn phương sai $h$ bước của GARCH với kết quả tính giải tích tường minh.
  - *Kiểm thử bất biến máy trạng thái (State invariants):* Kiểm thử tính lũy đẳng giữa hai kỳ refit (`test_predict_is_idempotent_between_refits` — gọi `predict_quantiles` lặp 19 lần liên tiếp không làm trôi trạng thái phương sai so với bản sao độc lập) và kiểm thử điều kiện cắt bỏ nhãn chồng lấp (`test_quantile_walk_forward_purges` cho $h \in \{1, 5, 21\}$).
  - *Kiểm thử năng lực thống kê trên dữ liệu mô phỏng (Monte Carlo DGP):* Trên chuỗi GARCH(1,1)-$t$ tổng hợp, mô hình có biến động động (`Q1, Q2, Q3`) phải đạt độ bao phủ 80% trong khoảng hợp lý, thắng mô hình biên độ tĩnh (`Q0`) về Pinball Loss và đạt tỷ số phân biệt rủi ro $> 1.5\times$.
- **Prior Art trong kho mã nguồn:** Tuân thủ cấu trúc kiểm thử hiện có tại `tests/test_risk_models_and_interval_tests.py` và `tests/test_forecast_tests_and_walk_forward.py`.

---

## Out of Scope

1. **Không mua hoặc tích hợp thêm nguồn dữ liệu phái sinh trả phí mới** (như đường cong kỳ hạn Singapore Mogas 95 Forward Swaps hay Implied Volatility từ quyền chọn dầu thô ICE Brent — nội dung này thuộc lộ trình nghiên cứu riêng của **Hướng 1**).
2. **Không thay đổi biến mục tiêu dự báo điểm ở kỳ hạn 1 ngày ($M0a\text{–}M5$)** hay huấn luyện lại từ đầu 30 checkpoint mạng nơ-ron sâu (`RNN/LSTM`), vốn đã được đóng băng để làm mốc đối chứng cố định.
3. **Không xây dựng giao diện web/dashboard thời gian thực có cơ sở dữ liệu riêng:** Tệp HTML từ bước `/prototype` chỉ là bản mẫu kiểm chứng logic có thể bỏ đi (throwaway logic prototype); sản phẩm vận hành chính thức của pipeline là các tệp CSV/JSON chuẩn hóa, biểu đồ tĩnh độ phân giải cao và báo cáo Markdown.
4. **Không thay đổi mốc khóa sổ Point-in-Time (`08:30 SGT`)** hay cấu trúc 8 cổng kiểm toán dữ liệu trong tầng kỹ nghệ dữ liệu (`src/data_proccessing/`).

---

## Further Notes

- **Khuyến nghị vận hành theo kỳ hạn (Empirical Verdict):**
  - **Kỳ hạn 1 ngày ($h = 1$):** Sử dụng **`Q3` (Location–Scale Quantile Regression với GARCH-$t$ scale)** kết hợp dự báo điểm **`M2`** — đạt Pinball Loss thấp nhất (giảm ~25–26% so với `Q0`), Brier Skill $+25\%$, và vượt qua đồng thời cả Kupiec ($p = 0.36$), Christoffersen ($p = 0.068$) lẫn Conditional Coverage ($p = 0.124$) trên chuỗi kiểm tra 14 năm.
  - **Kỳ hạn 1 tuần ($h = 5$):** Sử dụng **`Q3`** — đạt độ bao phủ ~79.0–80.5% trên cả hai luồng dữ liệu, giảm 5.5–9.1% Pinball Loss ($p < 0.001$).
  - **Kỳ hạn 1 tháng ($h = 21$):** Sử dụng **`Q2` (GARCH(1,1)-$t$ + Time-Decayed FHS)** làm mô hình chính — đạt độ bao phủ thực tế **79.98%** (mục tiêu 80.0%, Kupiec $p = 0.91$, Conditional Coverage $p = 0.99$) và phân biệt được thời kỳ rủi ro cao có độ biến động thực tế gấp **$2.56\times$** thời kỳ rủi ro thấp.
- **Tài liệu tham chiếu liên kết:**
  - Từ điển thuật ngữ miền: `docs/GLOSSARY.md` (và `GLOSSARY.md` ở gốc).
  - Các quyết định kiến trúc: `docs/adr/0001` đến `docs/adr/0005`.
