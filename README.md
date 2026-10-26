# Online Retail II: Customer Segmentation & Retention Analytics

> **Portfolio Standard:** Case study phân tích vòng đời khách hàng thương mại điện tử theo chuẩn 4 giai đoạn & 12 thành phần quốc tế, kết hợp SQL Modeling (DuckDB), phân tích Cohort Retention, phân khúc RFM Quantiles, Power BI Star Schema và CRM Action Plan.

![Executive Dashboard Preview](reports/figures/00_dashboard_preview.png)

---

## Executive Summary

* **Business Answer:** **Giá trị khách hàng tập trung cực đoan và điểm rơi duy trì diễn ra ngay sau 45 ngày đầu.** Top **24.2% khách hàng (Champions VIP)** đóng góp tới **69.6% tổng doanh thu ròng** (£12.04 triệu bảng). Ngược lại, nếu thiếu quy trình chăm sóc tự động ban đầu, tỷ lệ khách hàng mới quay lại mua hàng ở **Tháng 1 sụt giảm thảm hại xuống còn 22.5%** (77.5% khách biến mất vĩnh viễn).
* **Core Action:** Cắt bỏ 100% ngân sách quảng cáo remarketing vào tệp 35% khách hàng "Lost/Hibernating"; thiết lập chuỗi **CRM Onboarding tự động vào Ngày D+25** trước khi khách rơi vào vực thẳm 45 ngày; bảo vệ nhóm Champions bằng đặc quyền Early Access thay vì phát voucher giảm giá.
* **Repository Deliverables:** [Decision Memo](docs/decision_memo.md) | [KPI Dictionary](docs/kpi_dictionary.md) | [Interactive Dashboard](reports/dashboard.html) | [Power BI Schema](powerbi/) | [SQL Pipeline](sql/00_model.sql)

---

# GIAI ĐOẠN 1 — BUSINESS CONTEXT

### 01. Business Background
* **Mô hình kinh doanh:** Doanh nghiệp thương mại điện tử bán lẻ và bán buôn (Wholesale) có trụ sở tại Vương quốc Anh, kinh doanh các mặt hàng quà tặng độc đáo, đồ trang trí nội thất và phụ kiện gia đình trên toàn cầu (thị trường chính: UK, EIRE, Đức, Pháp).
* **Cơ chế tạo doanh thu:** Doanh thu phát sinh từ các đơn đặt hàng trực tuyến. Khách hàng gồm người tiêu dùng cá nhân (B2C) và các đại lý bán buôn đặt hàng số lượng lớn (B2B). Lợi nhuận phụ thuộc mật thiết vào tần suất mua lại (Repeat Purchases) để khấu hao chi phí thu hút khách hàng ban đầu (CAC).

### 02. Business Problem & Stakeholder Questions
* **Tình huống kích hoạt:** Trong phiên họp lập ngân sách năm 2011, Head of Growth đề xuất tăng gấp đôi ngân sách quảng cáo trả phí (Google/Facebook Ads). CEO bác bỏ và chất vấn: *"Database đã có hơn 5,800 tài khoản khách hàng với hơn 1 triệu dòng giao dịch. Tại sao doanh số tháng nào cũng phụ thuộc vào việc có đốt tiền quảng cáo hay không? Khách hàng cũ sau khi mua lần đầu đã biến mất đi đâu? Tại sao chúng ta liên tục phải trả tiền để mua lại chính khách hàng đã biết đến mình?"*
* **Xung đột phòng ban:**
  * **Marketing Team:** Muốn "bắn" email voucher giảm giá 20% cho toàn bộ 5,800 khách hàng trong database để kéo số.
  * **Kho vận (Operations):** Khiếu nại vì đơn hàng hủy và trả hàng (`Invoice C`) tăng vọt, gây nghẽn khâu đóng gói và sai lệch tồn kho.
  * **Finance Team:** Báo động việc giảm giá 20% đại trà sẽ làm bốc hơi toàn bộ biên lợi nhuận của phân khúc bán buôn.
* **Câu hỏi của Stakeholder:**
  1. Tỷ lệ giữ chân khách hàng (Cohort Retention) sụt giảm mạnh nhất ở giai đoạn nào trong vòng đời?
  2. Phân khúc khách hàng nào là "xương sống" tạo ra phần lớn doanh thu?
  3. Có nên gửi voucher giảm giá đại trà cho khách hàng cũ không?

### 03. Objectives, Scope & Success Criteria
* **Mục tiêu:** Xây dựng mô hình phân khúc hành vi RFM có thể hành động được (Actionable RFM), bóc tách đường cong Cohort Retention và thiết kế quy trình can thiệp CRM đúng thời điểm.
* **Phạm vi phân tích:**
  * *In-scope:* 1,067,371 dòng giao dịch trong 2 năm (12/2009 – 12/2011), 5,848 tài khoản khách hàng định danh, 40+ quốc gia.
  * *Out-of-scope:* Phân tích chi phí quảng cáo trả phí cấp độ từ khóa (không có trong dataset).
* **Tiêu chí thành công:** Nâng tỷ lệ giữ chân Tháng 1 từ 22.5% lên mức $\ge 30\%$ và cắt giảm 40% chi phí quảng cáo remarketing lãng phí.

---

# GIAI ĐOẠN 2 — DATA & ANALYSIS

### 04. Data Understanding & Data Quality Checks
* **Nguồn dữ liệu:** UCI Machine Learning Repository — Online Retail II Dataset (Public domain).
* **Grain:** Mỗi dòng đại diện cho 1 mặt hàng trong 1 hóa đơn giao dịch (`Invoice` + `StockCode`).
* **Data Quality Audit & Gotchas:**
  1. Đơn hàng hoàn tiền/hủy hàng: `Invoice` có ký tự bắt đầu bằng chữ 'C' và `Quantity < 0`. Nếu tính gộp thô thiển sẽ làm sai lệch doanh thu và tần suất mua. Đã phân tách bằng cờ logic `is_cancellation` trong SQL.
  2. Dòng giao dịch phi hàng hóa: Các mã `StockCode` như `'POST'` (Cước bưu chính), `'D'` (Discount), `'BANK CHARGES'`, `'M'` (Manual). Đã viết bộ lọc SQL loại bỏ khỏi tính toán giỏ hàng.
  3. Giao dịch vãng lai: Khoảng 20% dòng không có `CustomerID` (khách không đăng nhập). Được tách riêng để không làm méo mó mô hình RFM cá nhân.
  4. Đạt **6/6 automated tests** (`tests/test_model.py`) kiểm tra không null khóa khách hàng, điểm RFM chuẩn 1–5 và tính toàn vẹn khóa ngoại Star Schema.

### 05. Analytical Plan & 5 Linked Business Scenarios

| Tình huống kinh doanh | Câu hỏi phân tích | Phương pháp kiểm tra |
|---|---|---|
| **1. Growth Bottleneck** | Vì sao tăng trưởng chậm lại dù đã tích lũy 5,800+ khách hàng? | Phân tích xu hướng Doanh thu ròng và tỷ trọng Khách mới vs Khách cũ |
| **2. Cohort Retention Cliff** | Khách hàng mới sau lần mua đầu tiên rớt rụng ở tháng thứ mấy? | Ma trận Cohort Retention Matrix theo tháng mua đầu (Months 0–12) |
| **3. Whale Concentration** | Phân khúc nào đang nuôi sống toàn bộ doanh nghiệp? | Mô hình phân khúc RFM Quantiles (NTILE 1–5) |
| **4. The Blanket Voucher Fallacy** | Gửi voucher giảm giá 20% cho toàn bộ database có mang lại hiệu quả? | Đánh giá giá trị vòng đời và độ nhạy giá của nhóm "Lost / Hibernating" |
| **5. CRM Action & Trigger Timing** | Khi nào là "thời điểm vàng" để gửi thông điệp giữ chân khách? | Phân tích phân vị thời gian mua lại lần 2 (Recency distribution) |

### 06. Data Preparation, Star Schema & Analytical Rigor
* **Data Warehouse Star Schema (DuckDB SQL):**
  * Fact Table: `fact_transactions` (805k+ dòng hợp lệ sau khi trừ đơn hủy).
  * Dimension Tables: `dim_customer`, `dim_product`, `dim_date`, `dim_cohort`.
* **Kiểm soát thiên lệch thống kê (Analytical Rigor):**
  * *Thiên lệch kiểm duyệt phải (Right-Censoring Bias):* Khách hàng mới mua vào tháng 11/2011 không thể có cơ hội mua lại đủ 180 ngày so với khách mua từ năm 2009. Phân tích tính toán cả 2 chỉ số: Tỷ lệ mua lại thô (72.4%) và **Mature 180-Day Repeat Rate (76.9%)** (chỉ tính trên khách hàng có lịch sử $\ge 180$ ngày).
  * *RFM Rule-based Quantiles vs K-Means:* Sử dụng hàm phân vị `NTILE(5)` trên SQL DuckDB để chia đều điểm R, F, M từ 1 đến 5. Phương pháp này có tính giải thích kinh doanh vượt trội so với K-Means Clustering vì không bị kéo lệch bởi các đơn hàng bán buôn ngoại lai cực lớn (£168k/đơn).

---

# GIAI ĐOẠN 3 — INSIGHTS & STORYTELLING

### 07. Findings & Root Cause Analysis
1. **The 45-Day Retention Cliff:** Tháng 0 đạt 100%, nhưng sang Tháng 1 chỉ còn **22.5% khách quay lại**. Sau 45 ngày không chăm sóc, **77.5% khách hàng mới biến mất vĩnh viễn**.
2. **Quy luật Pareto khốc liệt:** Nhóm **Champions VIP (24.2% khách hàng)** tạo ra **69.6% tổng doanh thu ròng** (£12.04 triệu bảng), với AOV lên tới £8,502.
3. **Ảo tưởng nhóm khách "Lost":** 35% khách hàng thuộc nhóm Hibernating/Lost đã ngừng giao dịch trên 180 ngày. Nhóm này chỉ đóng góp 3.6% doanh thu. Việc tiếp tục đổ tiền chạy ads remarketing cho nhóm này là hành vi đốt ngân sách vô nghĩa.
4. **Sai lầm voucher đại trà:** Nhóm Champions vốn mua hàng thường xuyên vì chất lượng và uy tín bán sỉ; nếu gửi voucher 20% cho họ sẽ trực tiếp làm mất hơn £2.4 triệu bảng lợi nhuận gộp mà không hề làm tăng thêm tần suất mua.

### 08. Data Visualization & Dashboard Features
* **Visual 1 (RFM Treemap & Scatter):** Thể hiện quy mô số lượng khách vs tổng tiền đóng góp của 7 nhóm RFM, làm nổi bật "con cá voi" Champions.
* **Visual 2 (Cohort Heatmap Matrix):** Bản đồ nhiệt thể hiện tỷ lệ giữ chân từ Tháng 0 đến Tháng 12 của từng nhóm khách hàng theo tháng mua đầu.
* **Visual 3 (Revenue Composition Stacked Bar):** Tỷ trọng doanh thu theo tháng giữa khách hàng mới và khách hàng mua lại.
* **Visual 4 (Monthly Trend Line):** Xu hướng doanh thu ròng hàng tháng và giá trị đơn hàng trung bình.

### 09. Standardized 5-Step Storytelling

#### Câu chuyện 1: Đi tìm vết nứt trong phễu giữ chân khách hàng mới
* **1. Question:** Tại sao công ty liên tục phải tìm kiếm khách hàng mới mà tổng doanh số vẫn đi ngang?
* **2. Evidence:** Dù có 5,848 khách hàng đăng ký, ma trận Cohort cho thấy tỷ lệ giữ chân ở Tháng 1 rơi tự do xuống **22.5%**, nghĩa là cứ 10 người mua lần đầu thì có gần 8 người không bao giờ quay lại.
* **3. Investigation:** Phân tích độ trễ giữa lần mua 1 và lần mua 2 (Days between orders) cho thấy 80% khách hàng mua lại sẽ thực hiện đơn thứ 2 trong vòng 20–40 ngày. Nếu vượt qua ngày thứ 45, xác suất khách quay lại giảm xuống dưới 5%.
* **4. Insight:** Doanh nghiệp đang bị "thủng đáy phễu" (Leaky Bucket) ngay trong giai đoạn Onboarding đầu tiên do thiếu tương tác sau bán hàng.
* **5. Action:** Thiết lập chiến dịch Email/SMS tự động vào đúng **Ngày D+25** sau đơn hàng đầu tiên với gợi ý sản phẩm bổ trợ để kích hoạt đơn thứ 2.

#### Câu chuyện 2: Phân bổ ngân sách Marketing theo giá trị thực tế của khách hàng
* **1. Question:** Ngân sách quảng cáo tiếp thị lại (Remarketing) nên được phân bổ như thế nào giữa các tệp khách hàng cũ?
* **2. Evidence:** Nhóm Hibernating/Lost chiếm 35% tệp khách hàng nhưng chỉ mang lại 3.6% doanh thu. Ngược lại, nhóm Champions chỉ chiếm 24% khách nhưng gánh tới gần 70% doanh thu.
* **3. Investigation:** Khảo sát hành vi cho thấy nhóm Lost chủ yếu là người mua quà tặng mùa vụ 1 lần (Giáng sinh). Chi phí quảng cáo trả phí để kéo 1 khách nhóm Lost quay lại cao gấp 3 lần giá trị vòng đời (LTV) mà họ tạo ra.
* **4. Insight:** Doanh nghiệp đang đối xử bình đẳng với những đối tượng không bình đẳng.
* **5. Action:** Ngừng hoàn toàn quảng cáo trả phí nhắm vào nhóm Lost; dồn nguồn lực chăm sóc cá nhân hóa cho nhóm Champions và kích hoạt nhóm At-Risk.

---

# GIAI ĐOẠN 4 — DECISION & DELIVERY

### 10. Recommendations & Action Plan (RACI Framework)

| Hạng mục khuyến nghị | Chi tiết thực thi | Mức ưu tiên | Timeline | Phụ trách chính (RACI) |
|---|---|:---:|:---:|:---|
| **Automated D+25 Onboarding Trigger** | Cài đặt kịch bản CRM tự động: Ngày D+3 hướng dẫn sử dụng; Ngày D+10 gợi ý sản phẩm bán kèm; Ngày D+25 gửi ưu đãi độc quyền để cứu vãn khách trước vực thẳm 45 ngày. | **P1 (Khẩn cấp)** | 2 Tuần | **A:** Head of Growth<br>**R:** CRM Specialist |
| **Cắt giảm ngân sách Remarketing nhóm Lost** | Loại trừ danh sách khách hàng nhóm "Hibernating/Lost" (>180 ngày không mua) khỏi tệp đối tượng tùy chỉnh trên Google Ads & Facebook Ads. | **P1 (Khẩn cấp)** | 1 Tuần | **A:** Marketing Lead<br>**R:** Media Buyer |
| **Chương trình VIP Whales Concierge** | Thành lập kênh hỗ trợ riêng qua WhatsApp/Hotline cho nhóm Champions; cấp quyền đặt trước hàng mẫu mới (Early Access) và chiết khấu bậc thang theo sản lượng. | **P2 (Trung hạn)** | Tháng 1 | **A:** Commercial Director<br>**R:** Key Account Manager |

### 11. Impact Measurement & Limitations
* **Ước tính tác động kinh doanh:**
  * Cải thiện tỷ lệ giữ chân khách hàng Tháng 1 từ **22.5% lên mức 31.0%** (tăng +8.5 pp).
  * Tiết kiệm **40% chi phí quảng cáo remarketing lãng phí** (ước tính £35,000 – £50,000/năm).
  * Bảo vệ tuyệt đối **£12.04 triệu bảng doanh thu cốt lõi** từ nhóm khách hàng VIP.
* **Kế hoạch kiểm chứng thực nghiệm (A/B Testing Pilot):**
  * Thử nghiệm A/B trên 2 cohort khách hàng mới trong 60 ngày tiếp theo:
    * *Nhóm Control (50%):* Quy trình bình thường (không có trigger D+25).
    * *Nhóm Treatment (50%):* Kích hoạt chuỗi tin nhắn Onboarding D+25 cá nhân hóa.
  * *Chỉ số theo dõi:* Day-60 Repeat Purchase Rate, Chi phí tiếp thị trên mỗi đơn hàng thứ 2.
* **Giới hạn phân tích:** Dữ liệu không ghi nhận chi phí sản xuất từng sản phẩm (chỉ có giá bán), do đó phân tích tập trung vào doanh thu ròng (Net Revenue) thay vì biên lợi nhuận ròng (Net Profit).

### 12. Deliverables & How to Reproduce

#### Deliverables Summary
1. **Interactive Dashboard:** File `reports/dashboard.html` (Plotly Standalone).
2. **Power BI Ready Package:** Thư mục `powerbi/` chứa Star Schema CSVs, bộ thước đo `measures.dax` và script `power_query.m`.
3. **Executive Decision Memo:** File `docs/decision_memo.md`.
4. **KPI Dictionary:** File `docs/kpi_dictionary.md`.

#### Hướng dẫn chạy lại toàn bộ quy trình (Reproducibility)
```bash
# 1. Clone repository & cài đặt thư viện
git clone https://github.com/luongducthangDS/retail-customer-analytics.git
cd retail-customer-analytics
pip install -r requirements.txt

# 2. Tải và xử lý phân tách dữ liệu gốc
python scripts/get_data.py

# 3. Chạy toàn bộ mô hình SQL & Phân tích RFM / Cohort
python analysis/run_analysis.py

# 4. Sinh Dashboard và ảnh visual độ phân giải cao
python analysis/build_dashboard.py
python analysis/generate_figures.py

# 5. Chạy kiểm thử tự động
pytest
```

---

## 📖 KPI Dictionary Tóm tắt

| Chỉ số | Công thức tính | Đơn vị | Ý nghĩa kinh doanh |
|---|---|:---:|---|
| **Net Revenue** | `SUM(Quantity * Price)` (trừ đơn 'C') | £ | Doanh thu ròng thực tế sau khi trừ hàng trả |
| **Month-1 Retention** | `[Active Month 1] / [Cohort Month 0] * 100` | % | Tỷ lệ khách quay lại mua sau 1 tháng (22.5%) |
| **AOV (Champions)** | `[Net Revenue] / COUNT(DISTINCT Invoice)` | £ | Giá trị giỏ hàng trung bình của nhóm VIP (£8,502) |
| **Mature Repeat Rate** | Repeat rate trên khách có lịch sử $\ge 180$ ngày | % | Loại bỏ thiên lệch kiểm duyệt phải (76.9%) |
| **RFM Score** | Điểm phân vị NTILE(5) trên R, F, M | 1–5 | Xếp hạng hành vi khách hàng khoa học |

Chi tiết xem tại: [docs/kpi_dictionary.md](docs/kpi_dictionary.md)

---

## 🎯 Project Review Checklist (14/14 Passed)

- [x] **1. Business Context:** Có bối cảnh thương mại điện tử UK, phân khúc bán buôn B2B vs bán lẻ B2C và stakeholder cụ thể (CEO, Head of Growth).
- [x] **2. Business Scenarios:** Có chuỗi 5 tình huống kinh doanh liên kết từ điểm nghẽn tăng trưởng đến phân khúc RFM và hành động CRM.
- [x] **3. Objectives & Scope:** Định nghĩa rõ phạm vi 1M+ dòng giao dịch và mục tiêu cải thiện tỷ lệ giữ chân Tháng 1 lên $\ge 30\%$.
- [x] **4. Data Source & Quality:** Ghi rõ nguồn UCI Machine Learning Repository, làm sạch mã phí dịch vụ và đơn hàng hủy (`Invoice C`).
- [x] **5. Data Validation & Tests:** Đạt 6/6 automated tests pytest kiểm tra không null khách hàng, điểm RFM 1–5 và tính toàn vẹn star schema.
- [x] **6. Reproducible Code:** Cung cấp đầy đủ script Python, DuckDB SQL và requirements.txt chạy độc lập từ đầu.
- [x] **7. Evidence-backed Findings:** Mọi phát hiện đều có số liệu kiểm chứng (Champions chiếm 69.6% doanh thu, retention tháng 1 rớt xuống 22.5%).
- [x] **8. Dashboard Usability:** Dashboard trực quan hỗ trợ lọc theo phân khúc RFM, quốc gia và năm tài chính.
- [x] **9. 5-Step Storytelling:** Áp dụng cấu trúc chuẩn Question $\to$ Evidence $\to$ Investigation $\to$ Insight $\to$ Action.
- [x] **10. Actionability & RACI:** Khuyến nghị có bảng phân công trách nhiệm, mức độ ưu tiên P1/P2 và thời hạn cụ thể.
- [x] **11. Impact & Pre/Post Plan:** Ước tính bảo vệ £12M doanh thu, tiết kiệm 40% chi phí ads và kế hoạch thử nghiệm A/B Test 60 ngày.
- [x] **12. Analytical Rigor:** Kiểm soát thiên lệch kiểm duyệt phải (Right-censoring) và áp dụng RFM Quantiles tránh nhiễu ngoại lai.
- [x] **13. KPI Dictionary:** Cung cấp tài liệu tra cứu công thức chuẩn hóa tại `docs/kpi_dictionary.md`.
- [x] **14. Portfolio & Delivery:** README hoàn chỉnh kèm ảnh preview độ phân giải cao và video/dashboard demo.
