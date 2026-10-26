# KPI Dictionary: Online Retail II Customer Segmentation & Retention

Tài liệu định nghĩa chuẩn hóa toàn bộ các chỉ số đo lường vòng đời khách hàng (Customer Lifecycle), mô hình RFM và phân tích duy trì (Cohort Retention) theo chuẩn mực quốc tế.

---

## 1. Bảng tra cứu KPI cốt lõi

| Mã KPI | Tên chỉ số | Công thức tính toán | Đơn vị | Grain / Phạm vi tính | Ý nghĩa kinh doanh & Ngưỡng chuẩn |
|:---|:---|:---|:---:|:---|:---|
| **KPI-01** | **Net Revenue** (Doanh thu ròng) | `SUM(Quantity * Price)` (chỉ tính dòng hợp lệ, trừ đơn hủy `Invoice C`) | GBP (£) | Toàn công ty / Khách hàng | Doanh thu thực tế sau khi đã trừ đi các đơn hàng trả hàng, hoàn tiền và phí dịch vụ. |
| **KPI-02** | **Active Customer Base** | `COUNT(DISTINCT CustomerID)` (với `CustomerID IS NOT NULL`) | Khách hàng | Tháng / Năm / Toàn thời gian | Số lượng tài khoản khách hàng phát sinh ít nhất 1 giao dịch thành công trong kỳ. |
| **KPI-03** | **Overall Repeat Rate** | `COUNT(Distinct Customers with orders >= 2) / Total Customers * 100` | % | Toàn công ty | Tỷ lệ khách hàng mua từ 2 lần trở lên trong lịch sử giao dịch. Đạt: **72.4%**. |
| **KPI-04** | **Mature 180-Day Repeat Rate** | Repeat rate tính trên tập khách hàng có thời gian theo dõi $\ge 180$ ngày | % | Khách hàng trưởng thành | Loại trừ thiên lệch kiểm duyệt phải (Right-censoring) đối với khách mới. Đạt: **76.9%**. |
| **KPI-05** | **Month-1 Cohort Retention Rate** | `[Active Customers Month 1] / [Cohort Size Month 0] * 100` | % | Từng Cohort tháng mua đầu | Tỷ lệ khách hàng quay lại mua hàng vào tháng tiếp theo sau tháng mua đầu tiên. Hiện trạng: **22.5%** (Vực thẳm 45 ngày). |
| **KPI-06** | **Average Order Value (AOV)** | `[Net Revenue] / COUNT(DISTINCT Invoice)` | GBP (£) | Khách hàng / Phân khúc RFM | Giá trị trung bình trên một giỏ hàng thành công. Toàn công ty: £345. Nhóm Champions: **£8,502**. |
| **KPI-07** | **Recency (R Score)** | Số ngày tính từ ngày giao dịch gần nhất của khách đến mốc 2011-12-10 | Ngày (1–5) | Từng khách hàng (`CustomerID`) | Đánh giá mức độ "tươi mới" của khách hàng. R=5: Vừa mua gần đây; R=1: Đã im lặng rất lâu. |
| **KPI-08** | **Frequency (F Score)** | Tổng số hóa đơn đơn lẻ (`Invoice`) khách hàng đã đặt trong lịch sử | Lần (1–5) | Từng khách hàng (`CustomerID`) | Đánh giá tần suất trung thành. F=5: Mua thường xuyên; F=1: Chỉ mua 1 lần duy nhất. |
| **KPI-09** | **Monetary (M Score)** | Tổng chi tiêu ròng (£) của khách hàng sau khi trừ đơn hủy | GBP (1–5) | Từng khách hàng (`CustomerID`) | Đánh giá giá trị tiền tệ mang lại. M=5: Chi tiêu khủng (Whale); M=1: Chi tiêu tối thiểu. |
| **KPI-10** | **Cancellation / Return Rate** | `COUNT(Invoices with 'C') / COUNT(Total Invoices) * 100` | % | Toàn sàn / Danh mục hàng | Tỷ lệ hóa đơn bị hủy hoặc trả hàng hoàn tiền. Ngưỡng theo dõi: **~1.8%** số đơn hàng. |

---

## 2. Ma trận phân khúc 7 nhóm khách hàng RFM

| Tên phân khúc | Điều kiện RFM (NTILE 1–5) | Tỷ trọng Khách (%) | Tỷ trọng Doanh thu (%) | Hành động kinh doanh chiến lược |
|:---|:---:|:---:|:---:|:---|
| **Champions (VIP Whales)** | $R \ge 4, F \ge 4, M \ge 4$ | **24.2%** | **69.6%** | Không giảm giá! Chăm sóc VIP Concierge, quyền đặt hàng trước (Early Access). |
| **Loyal Customers** | $R \ge 3, F \ge 3, M \ge 3$ | **18.4%** | **15.2%** | Giới thiệu chương trình thành viên thân thiết, đề xuất sản phẩm bán kèm (Cross-sell). |
| **Recent New Customers** | $R \ge 4, F \le 2$ | **19.5%** | **8.1%** | Kích hoạt chuỗi onboarding D+25 trước khi khách rơi vào vực thẳm 45 ngày. |
| **Promising** | $R \ge 3, F \le 2, M \ge 3$ | **7.1%** | **3.8%** | Gửi gợi ý sản phẩm phù hợp lịch sử mua sắm để thúc đẩy đơn hàng thứ 2. |
| **At Risk / Need Attention**| $R \le 2, F \ge 3, M \ge 3$ | **8.4%** | **2.1%** | Khách hàng giá trị cao sắp rời đi! Gửi email khảo sát lý do kèm ưu đãi cá nhân hóa. |
| **Can't Lose Them** | $R \le 1, F \ge 4, M \ge 4$ | **1.6%** | **0.8%** | Quản lý gọi điện trực tiếp hoặc gửi quà tri ân đặc biệt để tái kích hoạt. |
| **Hibernating / Lost** | $R \le 2, F \le 2, M \le 2$ | **20.8%** | **0.4%** | Cắt bỏ 100% ngân sách quảng cáo remarketing trả phí để tránh lãng phí. |
