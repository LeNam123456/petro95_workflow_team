# Spec — Pipeline Dự báo Điểm & Chiều hướng Platts Singapore Mogas 95 (Naive, XGBoost, LSTM, GRU)

Status: ready-for-agent
Type: spec
Branch: `feature/traditional-deep-learning-pipeline`
Nguồn tổng hợp: `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md` (đặc tả chi phối), `docs/GLOSSARY.md` Phần 1, ADR-0006, ADR-0007, phiên `/grill-with-docs`.
Không áp dụng: ADR-0001 → ADR-0005 và GLOSSARY Phần 2 (di sản SPAFS V5.2, đã tuyên bố non-binding trong ADR-0006).

---

## Problem Statement

Tôi là nghiên cứu sinh cần trả lời ba câu hỏi nghiên cứu thực nghiệm về dự báo giá Platts Singapore Mogas 95 tại ba kỳ hạn h ∈ {1, 5, 21} phiên Mogas:

- **RQ1 — Target Representation**: dự báo Relative Change có tốt hơn dự báo trực tiếp Price Level không, sau khi cả hai được tái lập về USD/thùng?
- **RQ2 — Exogenous Information**: thêm Brent (Multivariate) có cải thiện so với chỉ dùng lịch sử Mogas (Univariate) không?
- **RQ3 — Model Comparison**: XGBoost, LSTM, GRU có vượt Naive Persistence theo từng kỳ hạn không?

Hiện repository đã được reset: chỉ còn Canonical Market Panel bất biến, các tập chia vật lý trong thư mục splits kèm manifest, tài liệu đặc tả, Glossary và ADR. Không có mã nguồn pipeline, không có test. Tôi không có cách nào chạy lại một benchmark công bằng, không có rò rỉ thời gian (lookahead), có thể kiểm toán và tái lập để báo cáo với giảng viên hướng dẫn. Bất kỳ kết quả nào sinh ra thủ công trong notebook đều không đủ tin cậy về mặt Point-in-Time và không tái lập được.

## Solution

Một pipeline tự động, chạy bằng một lệnh, đọc Canonical Market Panel và các tập chia vật lý (chỉ đọc), xây dựng mẫu supervised theo quy tắc PIT tại Forecast Origin 08:30 SGT với Lookback Window L = 30, huấn luyện theo Direct Multi-Horizon Strategy, và chạy đủ **33 cấu hình MVP**:

- 18 cấu hình Relative Change: {XGBoost, LSTM, GRU} × {Univariate, Multivariate} × {1, 5, 21}.
- 3 cấu hình Naive Persistence Baseline (h = 1, 5, 21; không nhân theo scenario).
- 12 cấu hình Price Level ablation: {XGBoost, LSTM} × {Univariate, Multivariate} × {1, 5, 21}.

Mọi dự báo được tái lập về USD/thùng trước khi tính MAE, MSE, RMSE, MAPE, R², Directional Accuracy. Pipeline xuất leaderboard 33 dòng, file dự báo theo từng horizon, biểu đồ, checkpoint tốt nhất của mô hình neural và experiment manifest đủ để tái lập. Pipeline dừng lại nếu PIT audit phát hiện feature đến từ tương lai. Kết quả âm hoặc không vượt Naive vẫn là kết quả hợp lệ.

## User Stories

### Dữ liệu & PIT governance

1. As a researcher, I want the pipeline to read the Canonical Market Panel strictly read-only, so that the immutable source dataset can never be modified by any run.
2. As a researcher, I want the pipeline to verify the SHA-256 checksums of the source panel and of each physical split against the splits manifest before doing anything else, so that I know the benchmark is running on exactly the audited data.
3. As a researcher, I want the pipeline to re-verify schema, row counts (4,428 total; 3,099 / 664 / 665), date bounds, missing values in `MG95` and `brent_close`, and duplicate market dates at run time, so that snapshot metadata is confirmed by execution rather than assumed.
4. As a researcher, I want every supervised sample to carry `forecast_origin`, `feature_available_at`, `target_timestamp`, `horizon` and `target_value`, so that the temporal validity of each sample can be audited.
5. As a researcher, I want the Forecast Origin to be 08:30 Asia/Singapore on the trading day following the latest available Mogas assessment, so that all models share one well-defined information set.
6. As a researcher, I want Mogas inputs to be the latest assessment whose availability timestamp is ≤ forecast origin, so that the Mogas history respects the PIT Rule.
7. As a researcher, I want Brent inputs to be as-of joined by their own availability timestamp (latest settlement available ≤ forecast origin), not by calendar date, so that calendar-only alignment cannot leak future Brent prices.
8. As a researcher, I want an automated PIT audit that checks `feature_available_at ≤ forecast_origin` for every feature of every sample used, and checks that `target_timestamp` is strictly after the forecast origin at exactly h Mogas sessions, so that "Zero Lookahead Bias" is only claimed when the check actually passed.
9. As a researcher, I want the pipeline to halt with a non-zero exit and a violation report if any PIT violation is found, so that leaking results are never produced.
10. As a researcher, I want the PIT audit report to state how many availability timestamps are proxies versus observed, so that I can honestly qualify the Zero Lookahead Bias claim in my thesis.
11. As a researcher, I want timestamps to be handled in UTC internally and interpreted in Asia/Singapore only for business-calendar purposes, so that London DST shifts in ICE Brent data cannot silently corrupt alignment.

### Splits & sample construction

12. As a researcher, I want to use the existing physical Sequential 70/15/15 Split (Train 2008-05-02 → 2020-09-16, Validation 2020-09-17 → 2023-05-09, Test 2023-05-10 → 2025-12-30) as fixed by ADR-0006, so that every configuration evaluates on identical partitions.
13. As a researcher, I want samples assigned to a partition by their forecast origin, so that partition membership follows the agreed rule.
14. As a researcher, I want early Validation and Test samples to borrow up to 29 preceding observations from the prior partition as lookback context, so that no valid history is discarded and PIT is still respected.
15. As a researcher, I want samples whose target `o + h` falls past the end of their partition to be dropped, so that targets never cross a partition boundary.
16. As a researcher, I want the evaluated Test sample counts to be exactly 664 (h=1), 660 (h=5) and 644 (h=21), so that the sample-truncation rule is verifiable.
17. As a researcher, I want all models compared at the same horizon to use exactly the same set of forecast origins, so that comparisons across models, scenarios and target representations are fair.
18. As a researcher, I want Univariate inputs shaped 30 × 1 (Mogas) and Multivariate inputs shaped 30 × 2 (Mogas + PIT-aligned Brent) for the sequence models, so that the two data scenarios differ only by Brent.

### Target representation

19. As a researcher, I want the primary target to be Relative Change R(o,h) = (P(o+h) − P(o)) / P(o), so that RQ1's primary method is implemented exactly as specified.
20. As a researcher, I want inputs for Relative Change models to use Local Window Normalization z(j,o,k) = P(j, o−k) / P(j, o) − 1 per series for k = 0…29, so that each series is expressed relative to its own latest available value.
21. As a researcher, I want Relative Change predictions reconstructed as P̂(o+h) = P(o) · (1 + R̂(o,h)), so that metrics are computed in USD/thùng.
22. As a researcher, I want the Price Level ablation to predict y(o,h) = P(o+h) directly, with any scaler fit only on Train samples, so that RQ1's control is free of Validation/Test leakage.
23. As a researcher, I want Price Level Validation and Test values never clipped to the Train range and neural models to use a linear output layer, so that out-of-range prices can still be predicted.
24. As a researcher, I want the two target representations compared only after reconstruction to USD/thùng on the same valid forecast origins, so that RQ1 is answered on a like-for-like basis.

### Models

25. As a researcher, I want Naive Persistence (P̂(o+h) = P(o)) evaluated at all three horizons, so that every model has a mandatory minimum benchmark.
26. As a researcher, I want XGBoost Univariate to use exactly 32 features (30 Mogas relative lags z(M,o,k), k = 0…29, plus R1 and R5 Mogas momentum), so that the feature set fixed in ADR-0007 is respected.
27. As a researcher, I want XGBoost Multivariate to use exactly 64 features (the 32 Mogas features plus the corresponding 32 Brent features), so that RQ2 isolates Brent's contribution.
28. As a researcher, I want the raw Mogas − Brent price spread excluded from all MVP feature sets and never labelled a crack spread, so that non-stationary level information and unit-incompatible spreads do not contaminate the benchmark.
29. As a researcher, I want LSTM and GRU sequence models consuming the 30-session window, so that the recurrent representatives of RQ3 are implemented.
30. As a researcher, I want one independently trained model per horizon (Direct Multi-Horizon Strategy), so that losses of different horizons never share one objective in the MVP.
31. As a researcher, I want LSTM and GRU trained with Early Stopping on Validation loss (patience = 15) and the best checkpoint saved, so that model selection never touches Test.
32. As a researcher, I want all tuning and configuration choices made on Train/Validation only, with Test opened only at final evaluation, so that the reported Test numbers are unbiased.

### Evaluation

33. As a researcher, I want MAE, MSE, RMSE, MAPE and R² computed on reconstructed USD/thùng prices, so that all configurations are compared in the same unit.
34. As a researcher, I want negative R² on Test reported as-is, so that poor fits are not hidden or mistaken for bugs.
35. As a researcher, I want Directional Accuracy computed with the 3-state sign rule of ADR-0006 against the price at the forecast origin (a flat actual move is correct only if the prediction is also flat), so that the tie rule is fixed before seeing Test.
36. As a researcher, I want the actual Up / Down / Flat distribution reported per horizon alongside DA, so that DA is not judged against an implicit 50% threshold.
37. As a researcher, I want a simple directional baseline (majority direction class on Train, per horizon) reported next to model DA, so that DA has an objective reference point.
38. As a researcher, I want DA described only as an evaluation metric, never as the training objective, so that claims match how models were actually optimised.

### Outputs & reproducibility

39. As a researcher, I want a benchmark leaderboard with one row per configuration (33 rows) identified by model, scenario, target representation and horizon, so that RQ1–RQ3 can be read off one table.
40. As a researcher, I want per-horizon prediction files with columns `forecast_origin`, `target_timestamp`, `horizon`, `model`, `scenario`, `target_representation`, `actual_price`, `predicted_price` (USD/thùng), so that every prediction is traceable.
41. As a researcher, I want LSTM/GRU checkpoints named by model, scenario, representation and horizon, so that each best model can be reloaded.
42. As a researcher, I want actual-vs-predicted figures for h = 1, 5, 21, a directional confusion matrix (Actual Up/Down × Predicted Up/Down) and training/validation loss curves, so that I can present results visually to my advisor.
43. As a researcher, I want XGBoost feature importance exported, so that I can discuss which lags (and whether Brent features) drive predictions.
44. As a researcher, I want an experiment manifest recording data checksums, split bounds, PIT audit result, seed, hyperparameters, training time per configuration and library versions, so that any run can be reproduced and audited.
45. As a researcher, I want a single command to run all 33 configurations with the canonical seed 42 controlling Python hash seed, NumPy, PyTorch (CPU/CUDA) and XGBoost, so that the canonical leaderboard is deterministic.
46. As a researcher, I want an optional seeds argument (e.g. 42,43,44) that reports mean and standard deviation for LSTM/GRU without altering the canonical run, so that seed sensitivity can be shown honestly instead of cherry-picking.
47. As a researcher, I want to be able to run the 18 Relative Change + 3 Naive configurations first and the 12 Price Level configurations afterwards, so that I can deliver the main benchmark before the ablation if time is short.
48. As a researcher, I want all official data, training and evaluation logic in the source package rather than notebooks, so that notebooks are only used for EDA and presentation.

## Implementation Decisions

### Modules (theo Mục 9 REVISED và ADR-0006 quyết định 6: đặt trực tiếp dưới `src/` ở gốc repo)

- **Data module** — `validation` (schema, checksum, counts, missing, duplicates), `alignment` (PIT as-of join theo availability timestamp), `splitting` (đọc tập chia vật lý đã có; **không** tạo lại split), `dataset` (supervised sample builder — **Seam B**).
- **Features module** — `engineering`: Local Window Normalization, R1/R5 momentum, tạo vector 32/64 feature cho XGBoost.
- **Models module** — `baseline` (Naive), `xgboost_model`, `lstm`, `gru`. Mọi mô hình phơi bày cùng một hợp đồng fit/predict trên tập mẫu của Seam B và trả về dự báo trong không gian target của chính nó.
- **Training module** — `trainer`, `callbacks` (early stopping patience 15 theo Validation loss, best checkpoint, seeding).
- **Evaluation module** — `reconstruction` (về USD/thùng), `metrics` (6 metric, DA 3 trạng thái, phân phối Up/Down/Flat, directional baseline), `visualization`.
- **Experiments** — `benchmark`: dựng ma trận 33 cấu hình từ config, điều phối chạy, ghi artifact. Đây là **Seam A**.
- **Configs** — `data`, `experiment`, `models` (YAML). Mọi hyperparameter nằm trong config và được chép vào manifest.
- **Entry point** — `run_benchmark` ở gốc repo, CLI tùy chọn `--seeds`. Tệp `run_pipeline.py` hiện có ở gốc là orchestrator di sản SPAFS V5.2, không phải entry point của pipeline này.

### Hợp đồng Seam B — Supervised sample builder

Đầu vào: panel đã PIT-align, partition (train/val/test), horizon h, scenario (uni/multi), target representation (relative_change/price_level).
Đầu ra: tập mẫu, mỗi mẫu gồm cửa sổ đầu vào L = 30, target, và metadata `forecast_origin`, `feature_available_at` (lớn nhất trong cửa sổ, theo từng biến), `target_timestamp`, `horizon`, `target_value`, cùng `P(o)` (cần cho tái lập và DA).
Bất biến:
- `feature_available_at ≤ forecast_origin` với mọi feature; `target_timestamp` sau origin đúng h phiên Mogas.
- Mẫu đầu Validation/Test được mượn tối đa 29 quan sát từ partition liền trước; Train không có partition trước nên origin đầu tiên là quan sát thứ 30.
- Bỏ mẫu có `o + h` vượt cuối partition. Số mẫu kỳ vọng — Test: 664 / 660 / 644; Validation (suy ra cùng quy tắc): 663 / 659 / 643; Train: 3,069 / 3,065 / 3,049 với h = 1 / 5 / 21.
- Với Price Level, scaler (nếu có) chỉ fit trên mẫu Train và được truyền vào cho Validation/Test; không clipping.

### Hợp đồng Seam A — Benchmark runner

Đầu vào: config thí nghiệm (danh sách cấu hình cần chạy, seed, hyperparameter, có thể rút gọn epoch cho test).
Đầu ra: leaderboard, file dự báo theo horizon, checkpoint, figures, manifest, báo cáo PIT audit; exit code ≠ 0 khi PIT audit thất bại hoặc checksum lệch.

### Quy ước thời gian (dựa trên cột thực tế của panel)

- Panel có sẵn `observation_datetime` (Mogas 16:30 SGT), `availability_datetime`, `brent_availability_datetime`, `brent_observed_date`, `target_market_date`, `forecast_origin_datetime` (08:30 SGT ngày giao dịch kế tiếp) và cờ `*_is_proxy`.
- Pipeline dùng các cột availability này làm `feature_available_at`; không suy ra từ ngày lịch.
- Với h > 1, forecast origin giữ nguyên (08:30 SGT sau quan sát o); target là assessment Mogas thứ h tính từ o.

### Định nghĩa đã chốt (Glossary + ADR)

- Relative Change là phương pháp chính; không dùng log-return hay chênh lệch tuyệt đối thô.
- DA: `sgn ∈ {−1, 0, +1}`; đúng khi và chỉ khi `sgn(P̂(o+h) − P(o)) == sgn(P(o+h) − P(o))`.
- Naive Persistence chạy riêng 3 horizon; không sử dụng Brent nên không nhân đôi theo scenario.
- Seed canonical = 42 cho cả 33 cấu hình.
- Schema dự báo và tên checkpoint theo ADR-0007.

## Testing Decisions

- **Nguyên tắc**: chỉ kiểm tra hành vi quan sát được ở seam, không kiểm tra chi tiết nội bộ (tên hàm private, cấu trúc layer, thứ tự gọi). Test phải sống sót qua việc refactor bên trong module.
- **Seam B — Supervised sample builder** (test chính về tính hợp lệ thời gian):
  - Không có mẫu nào vi phạm PIT trên cả ba partition, mọi horizon, cả hai scenario.
  - Số mẫu đúng như kỳ vọng ở trên.
  - Mẫu đầu tiên của Validation/Test dùng 29 quan sát cuối của partition trước làm context.
  - Không target nào vượt ranh giới partition.
  - Một panel tổng hợp có availability timestamp bị đẩy sau forecast origin phải bị phát hiện và làm pipeline dừng.
  - Price Level: thống kê scaler chỉ phụ thuộc vào Train (thay đổi dữ liệu Test không làm đổi scaler); giá trị Test vượt miền Train không bị clip.
  - Relative Change: z tại k = 0 bằng 0; tái lập từ target thật trả lại đúng giá thật.
  - Multivariate khác Univariate đúng ở chiều Brent; số feature XGBoost là 32 / 64.
- **Seam A — Benchmark runner** (test end-to-end với config rút gọn: ít epoch, có thể chỉ một tập con cấu hình):
  - Sinh đủ artifact, leaderboard có đúng số dòng tương ứng cấu hình đã chạy (33 với cấu hình đầy đủ), file dự báo đúng schema và đơn vị USD/thùng.
  - Kiểm tra metrics/DA qua Naive Persistence: với Naive, giá dự báo bằng P(o) nên DA chỉ đúng ở các mẫu Flat; MAE/RMSE của Naive phải khớp giá trị tính độc lập từ panel. Đây là cách kiểm tra DA 3 trạng thái, tái lập giá và metrics mà không cần seam riêng.
  - Phân phối Up/Down/Flat và directional baseline xuất hiện trong kết quả.
  - Chạy hai lần với seed 42 cho cùng leaderboard (tái lập được, trong dung sai số thực cho phép trên CPU).
  - Checksum dữ liệu bị lệch hoặc PIT audit thất bại cho exit code ≠ 0 và không sinh leaderboard.
  - Canonical panel và tập chia vật lý không bị thay đổi sau khi chạy (checksum trước = sau).
- **Prior art**: không có — thư mục tests hiện rỗng sau khi reset (bộ test SPAFS V5.2 đã bị xóa và không được tái sử dụng). Dùng pytest; fixture panel tổng hợp nhỏ cho Seam B và config rút gọn cho Seam A.

## Out of Scope

- CNN-LSTM và mọi kiến trúc khác ngoài Naive, XGBoost, LSTM, GRU.
- Joint/MIMO multi-output.
- Tối ưu lookback (7/14/60); L cố định = 30.
- Walk-forward evaluation, purged CV, embargo (di sản SPAFS V5.2).
- Dự báo khoảng, quantile Q0–Q4, GARCH/FHS và mọi thuật ngữ trong GLOSSARY Phần 2.
- Crack spread và biến ngoại sinh khác (tồn kho, FX, freight, MG92, DO_001, DO_005…) dù có trong panel.
- Kiểm định thống kê so sánh forecast error (DM, HAC…) có xét chồng lấn horizon.
- Mô phỏng giao dịch, transaction costs, slippage; dashboard.
- Tạo lại hay sửa đổi các tập chia vật lý hoặc Canonical Market Panel.
- Đặt ngưỡng nghiệm thu dựa trên DA 60–70% hoặc yêu cầu một mô hình phải thắng.

## Further Notes

### Mâu thuẫn tài liệu đã biết (ADR-0006 là nguồn quyết định)

- Mục 4.2 REVISED và AGENTS.md ghi Train 2008–2020 / Val 2021–2023 / Test 2024–2025, nhưng số dòng 3,099 / 664 / 665 là chia 70/15/15 theo chỉ số. Ranh giới thật theo manifest là 2020-09-16 / 2023-05-09. Tên file chỉ là nhãn giai đoạn. Báo cáo kết quả phải ghi ngày thật.
- GLOSSARY ghi Test "2023–2025", AGENTS.md ghi "2024–2025"; cả hai chỉ là nhãn, ngày thật như trên.
- `docs/agents/domain.md` vẫn mô tả GLOSSARY là di sản, trong khi GLOSSARY hiện có Phần 1 là ngôn ngữ chuẩn của pipeline này. Phần 1 có hiệu lực, Phần 2 thì không.

### Giới hạn dữ liệu cần nêu trung thực

- 100% availability timestamp của Mogas và Brent trong panel là **proxy** (`*_is_proxy = True`). PIT audit chỉ chứng minh tính nhất quán với quy tắc proxy. Mọi tuyên bố Zero Lookahead Bias phải kèm điều kiện này.
- ~96.25% dòng có `brent_calendar_exact_match = True`; phần còn lại phụ thuộc vào as-of join, đúng như chủ đích của alignment.

### Chưa chốt — agent không được tự bịa, phải đưa vào config, ghi vào manifest và chỉ chọn dựa trên Validation

- Hyperparameter của XGBoost, LSTM, GRU (hidden size, số layer, learning rate, batch size, max epochs, dropout) và loss huấn luyện. Đặc tả chỉ quy định early stopping theo Validation loss.
- Loại scaler cho Price Level (đặc tả chỉ yêu cầu fit trên Train và không clipping) và biểu diễn đầu vào cho mô hình Price Level (ADR-0007 chỉ định nghĩa feature cho Relative Change).
- Mô hình/cấu hình nào được vẽ trong biểu đồ actual-vs-predicted và confusion matrix.
- Leaderboard có thêm metric Validation bên cạnh Test hay không.

Những điểm này nên được giải quyết bằng một ADR mới (từ ADR-0008) hoặc trong ticket tương ứng trước khi chạy benchmark canonical.

### Bước tiếp theo

`/to-tickets` đọc spec này để chia thành ticket tracer-bullet trong `.scratch/traditional-pipeline/issues/`.
