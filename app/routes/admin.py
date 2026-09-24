import csv
import io
from datetime import datetime, timedelta
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for, Response, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import User, Category, Ticket, KnowledgeArticle, AuditEvent, AIRequest
from app.utils.decorators import roles_required
from app.services.common import audit, text_field

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
ROLES = ("User", "IT Support", "Admin")


@admin_bp.before_request
@login_required
@roles_required("Admin")
def restrict_admin():
    pass


@admin_bp.get("/")
def dashboard():
    counts = dict(db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all())
    days = []
    for offset in range(6, -1, -1):
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=offset)
        days.append((start.strftime("%d/%m"), Ticket.query.filter(Ticket.created_at >= start, Ticket.created_at < start + timedelta(days=1)).count()))
    return render_template("admin/dashboard.html", counts=counts, total=sum(counts.values()),
        users=User.query.count(), articles=KnowledgeArticle.query.count(), days=days,
        ai_count=AIRequest.query.count(), groq_ready=bool(current_app.config["GROQ_API_KEY"]),
        recent=Ticket.query.order_by(Ticket.updated_at.desc()).limit(10).all(),
        workload=db.session.query(User.username, func.count(Ticket.id)).join(Ticket, Ticket.assigned_to_id == User.id).filter(Ticket.status.in_(["Open", "In Progress", "Resolved"])).group_by(User.id, User.username).all())


@admin_bp.route("/categories", methods=["GET", "POST"])
def categories():
    if request.method == "POST":
        category = Category(name=text_field("name", 100), description=text_field("description", 255, 0))
        db.session.add(category)
        audit("category.create", category.name)
        try:
            db.session.commit()
            flash("Đã tạo danh mục.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Tên danh mục đã tồn tại.", "warning")
        return redirect(url_for("admin.categories"))
    return render_template("admin/categories.html", categories=Category.query.order_by(Category.name).all())


@admin_bp.post("/categories/<int:category_id>/edit")
def edit_category(category_id):
    category = db.get_or_404(Category, category_id)
    category.name = text_field("name", 100)
    category.description = text_field("description", 255, 0)
    audit("category.edit", str(category_id))
    try:
        db.session.commit()
        flash("Đã cập nhật danh mục.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Tên danh mục đã tồn tại.", "warning")
    return redirect(url_for("admin.categories"))


@admin_bp.post("/categories/<int:category_id>/delete")
def delete_category(category_id):
    category = db.get_or_404(Category, category_id)
    if Ticket.query.filter_by(category_id=category_id).first() or KnowledgeArticle.query.filter_by(category_id=category_id).first():
        flash("Danh mục đang được sử dụng. Hãy đổi danh mục của Ticket/bài viết trước.", "warning")
    else:
        audit("category.delete", category.name)
        db.session.delete(category)
        db.session.commit()
        flash("Đã xóa danh mục.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/users", methods=["GET", "POST"])
def users():
    if request.method == "POST":
        role = request.form.get("role")
        if role not in ROLES:
            abort(400)
        user = User(username=text_field("username", 100, 3), role=role)
        user.set_password(text_field("password", 128, 8))
        db.session.add(user)
        audit("user.create", user.username)
        try:
            db.session.commit()
            flash("Đã tạo tài khoản.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Tên đăng nhập đã tồn tại.", "warning")
        return redirect(url_for("admin.users"))
    return render_template("admin/users.html", users=User.query.order_by(User.id).all(), roles=ROLES)


@admin_bp.post("/users/<int:user_id>/edit")
def edit_user(user_id):
    # Lock accounts in deterministic order to protect the last-admin invariant.
    accounts = User.query.order_by(User.id).with_for_update().all()
    user = next((u for u in accounts if u.id == user_id), None)
    if not user:
        abort(404)
    role = request.form.get("role")
    enabled = request.form.get("enabled") == "on"
    if role not in ROLES:
        abort(400)
    if user.id == current_user.id and (role != "Admin" or not enabled):
        abort(400, description="Không thể tự khóa hoặc hạ quyền tài khoản đang sử dụng.")
    if user.role == "Admin" and user.enabled and (role != "Admin" or not enabled):
        if sum(u.role == "Admin" and u.enabled for u in accounts) <= 1:
            abort(400, description="Hệ thống cần ít nhất một Admin hoạt động.")
    if not enabled or role == "User":
        if Ticket.query.filter(Ticket.assigned_to_id == user.id, Ticket.status != "Closed").first():
            abort(400, description="Hãy chuyển các Ticket chưa đóng trước khi khóa hoặc đổi người xử lý thành User.")
    user.role, user.enabled = role, enabled
    password = request.form.get("password", "")
    if password:
        if not 8 <= len(password) <= 128:
            abort(400, description="Mật khẩu cần từ 8 đến 128 ký tự.")
        user.set_password(password)
    audit("user.edit", f"User #{user.id}: {role}; enabled={enabled}")
    db.session.commit()
    flash("Đã cập nhật tài khoản.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.get("/audit")
def audit_log():
    page = AuditEvent.query.order_by(AuditEvent.id.desc()).paginate(page=request.args.get("page", 1, type=int), per_page=50, error_out=False)
    return render_template("admin/audit.html", page=page)


@admin_bp.get("/export.csv")
def export():
    def safe(value):
        value = str(value or "")
        return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Tiêu đề", "Trạng thái", "Danh mục", "Người tạo", "Người xử lý", "Ngày tạo", "Ngày đóng"])
    for ticket in Ticket.query.order_by(Ticket.id).yield_per(100):
        writer.writerow([ticket.id, safe(ticket.title), ticket.status, safe(ticket.category.name if ticket.category else ""),
            safe(ticket.created_by.username if ticket.created_by else ""), safe(ticket.assigned_to.username if ticket.assigned_to else ""), ticket.created_at, ticket.closed_at])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=tickets.csv"})
