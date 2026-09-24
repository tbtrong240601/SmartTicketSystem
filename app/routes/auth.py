from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    # Nếu đã đăng nhập thì không cho vào trang đăng ký
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Kiểm tra dữ liệu rỗng
        if not username or not password:
            flash("Vui lòng nhập đầy đủ thông tin.", "danger")
            return redirect(url_for("auth.register"))

        # Kiểm tra username đã tồn tại
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Tên đăng nhập đã tồn tại.", "danger")
            return redirect(url_for("auth.register"))

        # Kiểm tra độ dài mật khẩu
        if not 8 <= len(password) <= 128 or not 3 <= len(username) <= 100:
            flash("Tên đăng nhập cần 3–100 ký tự; mật khẩu cần 8–128 ký tự.", "danger")
            return redirect(url_for("auth.register"))

        # Tạo User mới
        user = User(username=username, role="User")

        user.set_password(password)

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Tên đăng nhập đã tồn tại.", "warning")
            return redirect(url_for("auth.register"))

        flash("Đăng ký thành công. Vui lòng đăng nhập.", "success")

        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        from app.services.throttle import allow_login, record_failure, clear_failures
        key = (request.remote_addr or "local", username.lower())
        if not allow_login(key):
            abort(429, description="Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 15 phút.")
        user = User.query.filter_by(username=username).first()

        if user and user.enabled and user.check_password(password):

            clear_failures(key)
            login_user(user)

            flash("Đăng nhập thành công.", "success")

            return redirect(url_for("main.home"))

        record_failure(key)
        flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash("Đăng xuất thành công.", "success")

    return redirect(url_for("auth.login"))


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        old = request.form.get("old_password", "")
        new = request.form.get("password", "")
        if not current_user.check_password(old):
            flash("Mật khẩu hiện tại chưa đúng.", "danger")
        elif not 8 <= len(new) <= 128:
            flash("Mật khẩu mới cần từ 8 đến 128 ký tự.", "danger")
        else:
            current_user.set_password(new)
            db.session.commit()
            flash("Đã đổi mật khẩu.", "success")
            return redirect(url_for("main.home"))
    return render_template("account.html")
