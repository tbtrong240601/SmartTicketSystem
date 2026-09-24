import click
from app.extensions import db
from app.models import User, Category, KnowledgeArticle


def register_commands(app):
    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.password_option()
    def create_admin(username, password):
        """Create an administrator without default credentials."""
        if not 3 <= len(username.strip()) <= 100 or not 8 <= len(password) <= 128:
            raise click.ClickException("Username 3-100 chars; password 8-128 chars.")
        if User.query.filter_by(username=username.strip()).first():
            raise click.ClickException("Username already exists; no account changed.")
        user = User(username=username.strip(), role="Admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Administrator created.")

    @app.cli.command("seed-knowledge")
    @click.option("--author", required=True, help="Existing Admin username")
    def seed_knowledge(author):
        """Add clearly identified sample knowledge articles; never create users or tickets."""
        admin = User.query.filter_by(username=author, role="Admin", enabled=True).first()
        if not admin:
            raise click.ClickException("An active Admin is required.")
        samples = [
            ("[Mẫu] Không kết nối được Wi-Fi", "Kiểm tra Wi-Fi đã bật và chế độ máy bay đã tắt. Kiểm tra đúng tên mạng được đơn vị cho phép. Thử kết nối lại và kiểm tra thiết bị khác có cùng lỗi không. Ghi lại thời điểm, tên mạng và thông báo lỗi để gửi IT. Không cung cấp mật khẩu qua bình luận Ticket."),
            ("[Mẫu] Máy in không nhận lệnh", "Kiểm tra nguồn, giấy và thông báo trên máy in. Xác nhận đã chọn đúng máy in trong hộp thoại in. Thử in một trang kiểm tra bằng chức năng có sẵn. Nếu hàng đợi bị kẹt hoặc máy báo lỗi, ghi lại mã lỗi và liên hệ IT. Không tự cài trình điều khiển từ nguồn không rõ."),
            ("[Mẫu] Không đăng nhập được tài khoản", "Kiểm tra tên đăng nhập và trạng thái Caps Lock. Dùng quy trình đặt lại mật khẩu chính thức của đơn vị nếu có. Nếu tài khoản bị khóa, gửi Ticket cho IT kèm thời điểm và thông báo lỗi. Không gửi mật khẩu, OTP hay mã khôi phục."),
        ]
        added = 0
        for title, content in samples:
            if not KnowledgeArticle.query.filter_by(title=title).first():
                db.session.add(KnowledgeArticle(title=title, content=content, author_id=admin.id, published=True))
                added += 1
        db.session.commit()
        click.echo(f"Added {added} sample articles.")
