# Đánh giá truy xuất Knowledge Base

Chạy từ thư mục dự án sau khi cài dependencies:

```powershell
python evaluation/run.py
python -m unittest discover -s tests -q
```

Không gọi Groq và không đọc/ghi database. Có 20 bài kiến thức mô phỏng và 48 câu hỏi do nhóm phát triển biên soạn: 20 câu trực tiếp, 20 câu diễn đạt lại, 8 câu ngoài phạm vi hoặc thiếu thông tin để trả lời. Đây không phải bộ dữ liệu độc lập từ người dùng thực tế. Các bài mẫu cần được IT duyệt trước khi đưa vào sử dụng.

So sánh baseline (đếm từ trùng, tiêu đề trọng số 3) với BM25 (k1=1.5, b=0.75; lặp từ tiêu đề 3 lần; chuẩn hóa dấu và cách viết Wi-Fi). Cả hai lấy tối đa 3 bài có điểm dương. Không dùng embedding, không huấn luyện mô hình.

## Kết quả thực đo

| Chỉ số trên 20 câu diễn đạt lại | Baseline | BM25 |
|---|---:|---:|
| Bài đúng ở vị trí đầu | 8/20 (40%) | 11/20 (55%) |
| Bài đúng trong 3 vị trí đầu | 12/20 (60%) | 16/20 (80%) |
| MRR@3 | 0.500 | 0.667 |

Hai phương pháp đều đạt 20/20 trên câu trực tiếp. Trên 8 câu ngoài phạm vi/thiếu thông tin, cả hai vẫn trả về tài liệu: tỷ lệ không trả nguồn là 0/8. Vì vậy không được dùng điểm dương để kết luận câu hỏi chắc chắn có câu trả lời. Một tài liệu có chủ đề liên quan cũng có thể không chứa thông tin cụ thể cần hỏi.

Hit@k là tỷ lệ câu có bài được gán nhãn đúng trong k vị trí đầu; MRR@3 là trung bình nghịch đảo vị trí bài đúng, bằng 0 nếu không nằm trong top 3. Các chỉ số này không đo độ chính xác câu trả lời Groq. Thời gian trong JSON chỉ đo tìm kiếm trên 20 bài trong bộ nhớ, không gồm database hay API.

`results/results.json` lưu thời điểm UTC, mã SHA256 của dữ liệu, từng kết quả và số tổng hợp. `cases.csv` để rà soát câu sai. `human_review.csv` là phiếu trống, được giữ nguyên khi chạy lại để không mất điểm do người chấm nhập.

## Đánh giá câu trả lời AI cần làm tiếp

Cho người phụ trách IT kiểm tra bài kiến thức trước. Chạy từng câu trên hệ thống, lưu nguyên câu trả lời, chế độ Groq/nội bộ, model và ngày thử. Chấm ba tiêu chí 0–2: đúng nội dung (0 sai, 1 một phần, 2 đúng); bám nguồn (0 bịa/không có căn cứ, 1 còn thiếu căn cứ, 2 có căn cứ); khả năng thực hiện (0 không dùng được, 1 còn mơ hồ, 2 rõ ràng và phù hợp). Ghi tên người chấm và lý do; các câu thiếu nguồn phải được xem xét riêng về khả năng từ chối.

Chưa có điểm đánh giá sinh câu trả lời. Không điền số giả hoặc gọi 80% ở bảng trên là độ chính xác AI. Nếu điều chỉnh thuật toán dựa trên các câu này, cần một tập mới để đánh giá tiếp.
