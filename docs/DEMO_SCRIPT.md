# Kịch bản demo 10–15 phút

## Chuẩn bị

Bật MySQL/XAMPP, chạy `start.bat` từ đúng thư mục đã cập nhật, mở http://127.0.0.1:5000. Đăng nhập bằng tài khoản Admin đã chuẩn bị; không chiếu mật khẩu lên màn hình báo cáo. Dùng hồ sơ/cửa sổ riêng tư tách phiên cho mỗi vai trò hoặc đăng xuất trước khi đổi tài khoản; các tab thường trong cùng hồ sơ dùng chung phiên.

Ghi commit đang chạy, ngày thử và model trong `GROQ_MODEL`; kiểm tra dependencies đã được cập nhật và đã khởi động lại server sau khi sửa `.env`. Chuẩn bị một bài Knowledge Base đã xuất bản, được kiểm tra nội dung và có từ khóa “máy in”. Giữ API key trong `.env`, không đưa lên màn hình. Sao lưu database riêng trước tổng duyệt; các bản ghi được tạo dưới đây phải ghi rõ là dữ liệu demo.

Đây là kịch bản cần thực hiện và ghi kết quả; không phải biên bản chứng minh các bước đã chạy thành công. Kiểm tra trực quan trên máy demo và đánh giá câu trả lời Groq bằng người chấm vẫn cần hoàn tất.

## Các bước

1. **Admin:** mở Tổng quan, kiểm tra thống kê, mở Người dùng & vai trò, tạo tài khoản User và IT Support dùng cho demo với mật khẩu riêng.
2. **Danh mục:** tạo danh mục “Demo - thiết bị văn phòng”, sửa mô tả.
3. **User:** tạo Ticket “Máy in không nhận lệnh”, chọn danh mục demo vừa tạo; mô tả thời điểm và triệu chứng; xem trạng thái Open.
4. **Admin:** mở Ticket, phân công nhân viên IT Support vừa tạo.
5. **IT:** mở Bàn xử lý IT, tiếp nhận; Ticket thành In Progress. Thêm bình luận và nhập phương án xử lý.
6. **User:** xem kết quả Resolved; chọn “Vẫn còn lỗi” để minh họa quay lại In Progress.
7. **IT:** bổ sung phương án và gửi lại. **User:** xác nhận “Đã khắc phục”. **IT:** đóng Ticket; kiểm tra Closed, timestamp và lịch sử.
8. **Knowledge Base:** IT tạo bài nháp từ phương án. Admin chỉnh sửa bỏ dữ liệu riêng và xuất bản. User tìm và đọc bài mới.
9. **Trợ lý:** hỏi “Máy in không nhận lệnh”. Lần đầu không chọn gửi ra ngoài để thấy tra cứu nội bộ và bài nguồn. Sau đó chọn cho phép gửi để thử Groq; chỉ gọi đó là câu trả lời Groq khi giao diện ghi chế độ Groq. Nếu hiện dự phòng, đọc thông báo và trình bày đúng là kết quả tra cứu nội bộ. Giải thích BM25 chọn tối đa 3 bài xuất bản, còn mô hình qua API tổng hợp gợi ý; AI không tự xử lý sự cố hoặc cập nhật Ticket.
10. **Quản trị:** xem nhật ký, xuất CSV, kiểm tra thống kê. Minh họa không xóa được danh mục đang được dùng.

## Ảnh nên chụp cho báo cáo

Đăng nhập; dashboard Admin; danh sách Ticket; chi tiết In Progress; User xác nhận; bài KB; trợ lý và nguồn; trang quản lý người dùng; nhật ký. Ghi “dữ liệu demo” khi dùng tài khoản/Ticket minh họa. Che thông tin riêng của dữ liệu cũ.

## Kiểm tra bổ sung trước buổi trình bày

| Tình huống | Điều cần quan sát và ghi lại |
|---|---|
| User mở Ticket của người khác | Yêu cầu bị từ chối; không hiện nội dung Ticket |
| IT chưa được User xác nhận đã khắc phục | Không thể đóng Ticket |
| Bài KB còn nháp | User không đọc được và trợ lý không dùng bài này làm nguồn |
| Câu hỏi có nguồn, đồng ý gửi ra ngoài | Nếu Groq thành công: ghi câu trả lời, nguồn, model, ngày thử; đối chiếu từng hướng dẫn với nguồn |
| Câu không trùng token, ví dụ `xyz987` nếu KB không chứa token này | Không có bài được lấy thì không gọi Groq; đề nghị mô tả thêm hoặc liên hệ IT |
| Câu ngoài phạm vi, ví dụ “Hướng dẫn nấu phở” | Ghi đúng kết quả thực tế; có thể vẫn lấy nhầm bài vì từ trùng. Không hứa hệ thống tự từ chối mọi câu ngoài phạm vi |
| API không kết nối được | Trên môi trường thử riêng, tạm ngắt kết nối mạng trước khi gửi câu có nguồn; chờ kết thúc rồi ghi thông báo dự phòng, sau đó kết nối lại. Không thay khóa thật chỉ để minh họa |

Các câu sinh bởi Groq cần người phụ trách IT chấm theo ba tiêu chí 0–2 trong `evaluation/README.md`: đúng nội dung, bám nguồn và khả năng thực hiện. `evaluation/results/human_review.csv` là phiếu chấm, không phải bảng kết quả đã có điểm. Kiểm thử tự động dùng API giả lập không thay thế bước này.

Nếu giới thiệu bộ đánh giá, nói: “Trên 20 câu diễn đạt lại tự biên soạn, BM25 tìm được bài đúng trong 3 kết quả đầu ở 16 câu; đây là đánh giá truy xuất.” Đồng thời nêu giới hạn: cả 8 câu ngoài phạm vi/thiếu thông tin vẫn nhận nguồn. Không diễn đạt thành “AI chính xác 80%”.

## Sau demo

Giữ Ticket demo để thể hiện nhật ký hoặc sao lưu trước khi dọn dữ liệu. Không xóa database thật. Đổi mật khẩu Admin được bàn giao và giữ file thông tin đăng nhập ở nơi riêng.
