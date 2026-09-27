# Hoàn thiện đồ án trong 3 ngày

Đề tài: Xây dựng hệ thống quản lý hỗ trợ IT tích hợp AI.

Phạm vi đóng góp: quản lý vòng đời Ticket và phân quyền; tái sử dụng kiến thức xử lý; tích hợp Groq để tổng hợp hướng dẫn từ nguồn được truy xuất. Mô hình được sử dụng qua API, không phải mô hình do sinh viên tự huấn luyện. Trợ lý không tự xử lý sự cố hoặc thay đổi trạng thái Ticket.

## Ngày 1: Chốt phần mềm và bằng chứng

- Chạy kiểm thử tự động; kiểm tra trên máy demo bằng cả ba vai trò.
- Demo một Ticket từ tạo, nhận xử lý, nhập phương án, xác nhận đến đóng; thử trường hợp trả lại xử lý.
- Duyệt nội dung Knowledge Base; thử Groq với nguồn liên quan, không có nguồn và khi API lỗi.
- Chụp giao diện thật, ghi phiên bản mã nguồn, model và ngày thử. Sao lưu database riêng, không đưa mật khẩu/API key vào báo cáo.
- Chạy bộ đánh giá trong `evaluation/`; sử dụng kết quả thực đo và ghi rõ giới hạn.

## Ngày 2: Hoàn thiện báo cáo

1. Tổng quan: vấn đề hỗ trợ IT phân tán, mục tiêu, phạm vi.
2. Cơ sở công nghệ: Flask, cơ sở dữ liệu quan hệ, xác thực/phân quyền, truy xuất từ khóa và sinh câu trả lời qua API.
3. Phân tích thiết kế: tác nhân, use case, luồng Ticket, mô hình dữ liệu, kiến trúc, luồng hỏi đáp và quyền truy cập.
4. Cài đặt: chức năng theo vai trò, xử lý lỗi Groq, nguồn kiến thức và cơ chế dự phòng.
5. Kiểm thử/đánh giá: kiểm thử chức năng, so sánh baseline–BM25, ví dụ thành công/thất bại, đánh giá thủ công câu trả lời nếu đã thực hiện.
6. Kết luận: kết quả đã đạt và hạn chế; hướng phát triển như truy xuất ngữ nghĩa, nhận biết thiếu nguồn, đánh giá với người dùng thực.

Tham khảo `REPORT_GUIDE.md` cho kiến trúc và nghiệp vụ; phần truy xuất mới và số liệu lấy từ `evaluation/README.md`. Không mô tả chức năng chưa có như tự động phân loại/ưu tiên/phân công Ticket bằng AI.

## Ngày 3: Tổng duyệt và nộp

- Đối chiếu báo cáo với giao diện/code thực tế và biểu mẫu trường.
- Chuẩn bị demo 7–10 phút, thử lại trên đúng máy trình bày.
- Chuẩn bị tình huống Groq không kết nối được và giải thích chế độ tra cứu nội bộ.
- Chốt bản nộp; chỉ sửa lỗi cản trở chạy hoặc sai nghiệp vụ.

## Hạn chế cần trình bày trung thực

Dữ liệu đánh giá nhỏ và tự biên soạn; chưa có nghiên cứu người dùng độc lập. Tìm kiếm BM25 dựa vào từ, chưa hiểu đầy đủ ý nghĩa. Các câu ngoài phạm vi vẫn có thể lấy tài liệu không phù hợp. Chưa có số đo chất lượng câu trả lời Groq do người chấm đánh giá. Kiểm thử tự động không thay thế kiểm tra trực quan và chạy trên máy demo. Kết quả hiện tại hỗ trợ báo cáo kỹ thuật, không bảo đảm đạt tiêu chí chấm của trường.
