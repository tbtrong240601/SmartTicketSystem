from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User

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
        if len(password) < 6:
            flash("Mật khẩu phải có ít nhất 6 ký tự.", "danger")
            return redirect(url_for("auth.register"))

        # Tạo User mới
        user = User(username=username, role="User")

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

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

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):

            login_user(user)

            flash("Đăng nhập thành công.", "success")

            return redirect(url_for("main.home"))

        flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Đăng xuất thành công.", "success")

    return redirect(url_for("auth.login"))
