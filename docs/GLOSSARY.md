# SPAFS V5.2 — Hướng 4 (Multi-Horizon Interval & Risk Forecasting)

Hệ thống dự báo khoảng dao động, phân vị lợi suất và phân tầng rủi ro đa kỳ hạn (1 ngày, 1 tuần, 1 tháng) cho chuẩn giá xăng thành phẩm bán buôn Platts FOB Singapore Mogas 95, kết hợp dự báo điểm ngắn hạn và quản trị dữ liệu Point-in-Time nghiêm ngặt.

## 1. Thị trường & Chuẩn giá Lọc hóa dầu (Market & Benchmark Assessment)

**Platts Mogas 95 Assessment (MG95)**:
Chỉ số đánh giá giá chuẩn bán buôn xăng RON 95 FOB Singapore do S&P Global Platts công bố vào cuối phiên Market-on-Close (16:30 SGT), đại diện cho các lô hàng giao nhận từ 15 đến 30 ngày tới.
_Avoid_: Giá giao dịch vật lý giao ngay tại cổng nhà máy, giá bán lẻ xăng dầu nội địa, spot physical transaction price.

**ICE Brent Futures (Brent)**:
Giá thanh toán hợp đồng tương lai dầu thô chuẩn quốc tế ICE Brent chốt phiên tại London/New York (~02:30–03:30 SGT sáng hôm sau), đóng vai trò biến nguyên liệu đầu vào dẫn dắt qua đêm (overnight lead) cho thị trường Singapore.
_Avoid_: Giá dầu thô giao ngay (dated Brent spot), WTI.

**Refining Spread (Biên giá liên sản phẩm & lọc dầu)**:
Chênh lệch giá giữa xăng MG95 và các sản phẩm/nguyên liệu liên quan tại cùng thời điểm hợp lệ, bao gồm Octane Spread ($\text{MG95} - \text{MG92}$), Diesel Spread ($\text{MG95} - \text{Gasoil 0.05\%}$), và Gasoline-Brent Crack Spread ($\text{MG95} - \text{Brent}$).
_Avoid_: Biên lợi nhuận ròng kế toán của nhà máy lọc dầu.

**Lagged Equilibrium Spread ($\text{Spread}_{t-1}$)**:
Chênh lệch giá trễ 1 phiên giữa MG95 và dầu thô Brent, đóng vai trò mỏ neo cân bằng dài hạn trong mô hình lợi suất dừng $I(0)$ mà không cần dùng cơ chế hiệu chỉnh sai số (ECM) trên chuỗi giá gốc.
_Avoid_: Phần dư đồng liên kết (cointegration residual) ước lượng trên toàn mẫu.

## 2. Quản trị Thời gian & Khung Dữ liệu (Point-in-Time & Sample Governance)

**Forecast Origin ($\tau$ / 08:30 SGT Cutoff)**:
Mốc thời gian khóa sổ thông tin cứng lúc 08:30 sáng giờ Singapore của ngày dự báo; chỉ những dữ liệu đã xuất bản và khả dụng trước hoặc tại mốc này mới được phép đi vào tập đặc trưng.
_Avoid_: Giờ đóng cửa cuối ngày (end-of-day cutoff), thời điểm chạy code thực tế.

**Horizon Return ($r_{t,h}$ / Lợi suất kỳ hạn $h$ phiên)**:
Tổng lợi suất logarit cộng dồn trong $h$ phiên giao dịch kế tiếp tính từ phiên gốc, với $h \in \{1, 5, 21\}$ tương ứng kỳ hạn 1 ngày, 1 tuần giao dịch và 1 tháng giao dịch.
_Avoid_: Mức giá danh nghĩa tương lai ($P_{t+h}$), lợi suất tính theo ngày lịch dương (calendar days).

**Purge Gap ($h$) & Embargo ($E$)**:
Khoảng cách an toàn bắt buộc trong đánh giá Walk-Forward: tại mốc dự báo $\tau$, tập huấn luyện chỉ được phép dùng các quan sát tới $t \le \tau - h - E$ để đảm bảo nhãn lợi suất $h$ phiên đã hoàn toàn hiện thực hóa và triệt tiêu rò rỉ tự tương quan.
_Avoid_: Chia tập train/test ngẫu nhiên (random K-fold), cửa sổ trượt không cắt bỏ nhãn chồng lấp (unpurged rolling window).

**Stream 2 (Primary Aligned Sample, 2017–2025)**:
Tập dữ liệu chính có giai đoạn kiểm tra ngoài mẫu từ 28/12/2022 đến 29/12/2025, dùng để đối chiếu trực tiếp giữa hệ thống mô hình điểm ($M0a\text{–}M5$, Deep Learning) và hệ thống mô hình khoảng/rủi ro ($Q0\text{–}Q4$).
_Avoid_: Tập dữ liệu duy nhất để kết luận về năng lực phân biệt khủng hoảng.

**Stream 1 (Long-Horizon Robustness Sample, 2008–2025)**:
Tập dữ liệu lịch sử dài hạn có giai đoạn kiểm tra ngoài mẫu 14 năm (2012–2025) bao hàm các đợt khủng hoảng lớn (2014–2015, COVID-19 2020, xung đột 2022), bắt buộc dùng để kiểm định khả năng phân biệt chế độ rủi ro cao/thấp.
_Avoid_: Tập dữ liệu phụ không bắt buộc.

## 3. Dự báo Khoảng, Phân vị & Rủi ro — Trọng tâm Hướng 4 (Interval, Quantile & Risk)

**Quantile Forecast (Dự báo phân vị)**:
Bộ 9 mức phân vị có điều kiện ($2.5\%, 5\%, 10\%, 25\%, 50\%, 75\%, 90\%, 95\%, 97.5\%$) của lợi suất kỳ hạn $h$ phiên được sắp xếp không giảm (non-crossing), phản ánh toàn bộ hình dạng phân phối dự báo tại mốc $\tau$.
_Avoid_: Dự báo điểm cộng trừ biên độ cố định.

**Prediction Interval (Khoảng dự báo 80% và 95%)**:
Biên độ dao động kỳ vọng của lợi suất kỳ hạn $h$ phiên, được trích xuất trực tiếp từ cặp phân vị $[q_{0.10}, q_{0.90}]$ (khoảng 80%) và $[q_{0.025}, q_{0.975}]$ (khoảng 95%).
_Avoid_: Khoảng tin cậy của tham số hồi quy (parameter confidence interval).

**Filtered Historical Simulation (FHS)**:
Phương pháp dựng phân vị dự báo bằng cách chuẩn hóa lợi suất lịch sử trong tập huấn luyện theo độ biến động dự báo tương ứng ($z_t = y_t / \hat{\sigma}_{h,t}$), sau đó nhân các phân vị thực nghiệm (có trọng số mũ giảm dần theo thời gian / time-decayed để thích ứng với chế độ biến động gần đây) của $z$ với độ biến động dự báo hiện tại $\hat{\sigma}_{h,\tau}$ nhằm bảo toàn đuôi dày (fat tails) và độ lệch thực tế.
_Avoid_: Khoảng dự báo giả định phân phối chuẩn Gaussian đóng ($\pm 1.28\sigma$).

**Conditional Location–Scale Decomposition (Phân rã Vị trí – Quy mô Có điều kiện)**:
Kiến trúc mô hình phân vị lai ghép (áp dụng trong `Q3`), trong đó thành phần dịch chuyển vị trí (Location) được dẫn dắt bởi truyền dẫn lợi suất dầu thô Brent qua đêm và chênh lệch giá trễ, còn thành phần co giãn biên độ (Scale) được neo theo căn bậc hai phương sai dự báo $h$ bước của GARCH(1,1)-t để vừa thu hẹp khoảng dự báo vừa chống trượt dồn cục trong khủng hoảng.
_Avoid_: Hồi quy phân vị tuyến tính chỉ dùng biên độ tĩnh hoặc biến động EWMA đơn thuần.

**Conformal Quantile Regression (CQR)**:
Cơ chế hiệu chỉnh độ rộng khoảng dự báo phi tham số bằng cách dùng tập hiệu chỉnh tách biệt ở cuối cửa sổ huấn luyện (đã trừ khoảng purge $h$, ưu tiên cửa sổ hiệu chỉnh gần nhất) để nới hoặc co biên phân vị sao cho đạt tỷ lệ bao phủ mục tiêu.
_Avoid_: Hiệu chỉnh hậu kiểm trên tập kiểm tra ngoài mẫu (test-set post-hoc tuning).

**Probability of Increase ($P(\text{tăng})$)**:
Xác suất lợi suất kỳ hạn $h$ phiên mang dấu dương ($P(r_{t,h} > 0)$), được suy ra nhất quán bằng nội suy tuyến tính hàm phân phối tích lũy (CDF) đi qua 9 phân vị dự báo tại ngưỡng $0\%$.
_Avoid_: Điểm tự tin chủ quan, nhãn phân loại cứng không hiệu chỉnh xác suất.

**Upside & Downside Tail Risk (Rủi ro đuôi tăng giá & giảm giá)**:
Các phân vị cực trị ở hai đầu phân phối dự báo: Upside Tail Risk ($q_{0.95}, q_{0.975}$) đo lường mức tăng giá bất lợi cho doanh nghiệp nhập khẩu xăng dầu; Downside Tail Risk ($q_{0.05}, q_{0.025}$) đo lường mức sụt giảm giá trị tồn kho cho nhà máy lọc dầu và thương nhân phân phối.
_Avoid_: Độ lệch chuẩn đối xứng hai chiều.

**Unified Multi-Horizon Decision Card (Bảng Quyết định Tích hợp Đa kỳ hạn)**:
Sản phẩm đầu ra vận hành tổng hợp tại mỗi mốc dự báo $\tau$, ghép nối dự báo điểm/hướng ngắn hạn 1 ngày của mô hình tuyến tính động $M2$ với khoảng dự báo 80%/95%, xác suất tăng $P(\text{tăng})$, rủi ro đuôi 95% và nhãn chế độ rủi ro tiền nghiệm của cả 3 kỳ hạn (1 ngày, 1 tuần, 1 tháng).
_Avoid_: Các bảng kết quả rời rạc tách biệt giữa dự báo điểm và dự báo khoảng.

**Ex-Ante Risk Regime (Nhãn mức rủi ro tiền nghiệm)**:
Phân loại mức độ rủi ro tại thời điểm dự báo (Thấp: dưới phân vị 25%; Trung bình: 25%–75%; Cao: trên phân vị 75%) dựa trên việc xếp hạng độ rộng khoảng dự báo 80% hiện tại so với **phân phối lịch sử tiền nghiệm được khởi tạo từ tập huấn luyện và mở rộng dần qua từng phiên** (Seeded Expanding Historical Rank) hoặc cửa sổ trượt 252 phiên giao dịch trước đó.
_Avoid_: Nhãn rủi ro hậu nghiệm tính bằng phân vị của toàn bộ chuỗi kiểm tra (in-sample / full-sample hindsight regime), hoặc xếp hạng chỉ dùng nội bộ tập kiểm tra làm mất 60 phiên đầu tiên.

## 4. Đánh giá Hiệu chỉnh & Kiểm định Thống kê (Calibration & Statistical Evaluation)

**Empirical Coverage (Tỷ lệ bao phủ thực tế)**:
Tỷ lệ phần trăm số phiên ngoài mẫu mà lợi suất thực tế rơi vào bên trong khoảng dự báo 80% hoặc 95% đã công bố.
_Avoid_: Độ chính xác phân loại hướng (directional accuracy).

**Pinball Loss (Quantile Loss)**:
Hàm mất mát bất đối xứng đo lường đồng thời độ hiệu chỉnh và độ sắc (độ hẹp) của toàn bộ 9 phân vị dự báo (xấp xỉ một nửa CRPS), đóng vai trò thước đo chính để xếp hạng các mô hình $Q0\text{–}Q4$ và kiểm định Diebold–Mariano.
_Avoid_: Sai số bình phương trung bình (RMSE) của dự báo điểm.

**Unconditional Coverage Test (Kiểm định Kupiec)**:
Kiểm định tỷ số hợp lý (LR) đánh giá xem tần suất lợi suất thực tế trượt ra ngoài khoảng dự báo có khớp thống kê với mức ý nghĩa danh nghĩa ($20\%$ cho khoảng 80%, $5\%$ cho khoảng 95%) hay không.
_Avoid_: Kiểm định trung bình sai số.

**Independence Test (Kiểm định Christoffersen)**:
Kiểm định chuỗi Markov bậc nhất ($LR_{ind}$) đánh giá xem các lần trượt khỏi khoảng dự báo có độc lập theo thời gian hay bị dồn cục (miss clustering) do mô hình phản ứng quá chậm khi thị trường chuyển sang khủng hoảng.
_Avoid_: Kiểm định tự tương quan chuỗi lợi suất gốc.

**Conditional Coverage Test (Kiểm định Bao phủ Có điều kiện Christoffersen $LR_{cc}$)**:
Kiểm định hợp nhất $LR_{cc} = LR_{uc} + LR_{ind} \sim \chi^2(2)$ đánh giá đồng thời cả tính đúng đắn của tỷ lệ bao phủ vô điều kiện (Kupiec) lẫn tính độc lập không trượt dồn cục của các lần vi phạm khoảng dự báo.
_Avoid_: Chỉ nhìn riêng lẻ Kupiec $p$-value mà bỏ qua hiện tượng trượt liên tiếp trong khủng hoảng.

**Non-Overlapping Evaluation Subsample (Mẫu kiểm định không chồng lấp)**:
Tập con lấy mỗi $h$ phiên một điểm dự báo độc lập (mỗi 5 phiên cho kỳ hạn tuần, mỗi 21 phiên cho kỳ hạn tháng) khi chạy kiểm định Kupiec và Christoffersen nhằm tránh hiện tượng một cú sốc đơn lẻ bị đếm lặp trên các cửa sổ chồng lấp.
_Avoid_: Chạy Kupiec/Christoffersen trực tiếp trên toàn bộ các ngày chồng lấp ở kỳ hạn dài.

**Risk Discrimination Ratio (Tỷ số phân biệt rủi ro Cao/Thấp)**:
Tỷ số giữa độ lệch chuẩn lợi suất thực tế trong các phiên được mô hình gắn nhãn "Rủi ro Cao" (top 25% độ rộng dự báo) chia cho độ lệch chuẩn thực tế trong các phiên gắn nhãn "Rủi ro Thấp" (bottom 25%).
_Avoid_: Tỷ số phương sai dự báo lý thuyết của mô hình.
