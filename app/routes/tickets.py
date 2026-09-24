from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user

from sqlalchemy import or_
from app.extensions import db
from app.models import Ticket, Category, User, Comment
from app.utils.decorators import roles_required
from app.services.common import audit, text_field, optional_category

ticket_bp = Blueprint("tickets", __name__)


@ticket_bp.route("/create-ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        title = text_field("title", 200)
        desc = text_field("description", 10000)
        category_id = optional_category()

        ticket = Ticket(
            title=title,
            description=desc,
            status="Open",
            created_by_id=current_user.id,
            category_id=category_id or None,
        )

        db.session.add(ticket)
        db.session.flush()
        audit(request.endpoint, ticket.status, ticket.id)
        db.session.commit()
        return redirect(url_for("main.home"))
    return render_template("create_ticket.html", categories=categories)


@ticket_bp.route("/tickets/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):

    ticket = db.get_or_404(Ticket, ticket_id)

    if current_user.role == "User" and ticket.created_by_id != current_user.id:
        abort(403)

    support_users = User.query.filter(User.role.in_(["IT Support", "Admin"]), User.enabled.is_(True)).all()

    # User dùng giao diện hiện tại
    if current_user.role == "User":

        return render_template(
            "ticket_detail.html", ticket=ticket, support_users=support_users
        )

    # IT Support / Admin dùng giao diện CRM mới
    return render_template(
        "it_ticket_detail.html", ticket=ticket, support_users=support_users
    )


@ticket_bp.route("/tickets/<int:ticket_id>/assign", methods=["POST"])
@login_required
@roles_required("Admin", "IT Support")
def assign_ticket(ticket_id):

    ticket = Ticket.query.filter_by(id=ticket_id).with_for_update().first_or_404()

    if current_user.role != "Admin":
        abort(403)
    if ticket.status != "Open":
        abort(400, description="Chỉ phân công Ticket đang Open.")

    assigned_to_id = request.form.get("assigned_to_id", type=int)

    support_user = db.session.get(User, assigned_to_id)

    if not support_user:
        abort(404)

    if not support_user.enabled or support_user.role not in ["Admin", "IT Support"]:
        abort(400)

    ticket.assigned_to_id = support_user.id

    audit(request.endpoint, ticket.status, ticket.id)
    db.session.commit()

    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@ticket_bp.route("/tickets/<int:ticket_id>/comments", methods=["POST"])
@login_required
def add_comment(ticket_id):

    ticket = Ticket.query.filter_by(id=ticket_id).with_for_update().first_or_404()

    # User chỉ được bình luận Ticket do mình tạo
    if current_user.role == "User" and ticket.created_by_id != current_user.id:
        abort(403)

    if ticket.status == "Closed":
        abort(400, description="Không thể bình luận vào Ticket đã đóng.")
    content = text_field("content", 5000)

    if not content:

        flash("Nội dung bình luận không được để trống.", "danger")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    comment = Comment(content=content, ticket_id=ticket.id, user_id=current_user.id)

    db.session.add(comment)
    audit(request.endpoint, ticket.status, ticket.id)
    db.session.commit()

    flash("Đã thêm bình luận.", "success")

    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@ticket_bp.route("/tickets/<int:ticket_id>/status", methods=["POST"])
@login_required
@roles_required("Admin", "IT Support")
def update_status(ticket_id):

    ticket = Ticket.query.filter_by(id=ticket_id).with_for_update().first_or_404()

    if current_user.role == "IT Support" and ticket.assigned_to_id != current_user.id:

        flash("Bạn không phải người đang phụ trách Ticket này.", "danger")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    new_status = request.form.get("status")

    current_status = ticket.status

    allowed_transitions = {
        "Open": ["In Progress"],
        "In Progress": ["Resolved"],
        "Resolved": ["Closed"],
        "Closed": [],
    }

    if new_status not in allowed_transitions.get(current_status, []):

        flash(f"Không thể chuyển từ " f"{current_status} sang {new_status}.", "danger")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    if new_status == "Resolved":
        return resolve_ticket(ticket_id)

    if new_status == "Closed":

        if ticket.resolution_confirmed is not True:

            flash("Người dùng chưa xác nhận " "sự cố đã được khắc phục.", "warning")

            return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

        ticket.status = "Closed"
        ticket.closed_at = datetime.utcnow()

    # Open → In Progress
    ticket.status = new_status

    audit(request.endpoint, ticket.status, ticket.id)
    db.session.commit()

    flash(f"Đã cập nhật trạng thái thành {new_status}.", "success")

    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@ticket_bp.route("/tickets/<int:ticket_id>/confirm-resolution", methods=["POST"])
@login_required
def confirm_resolution(ticket_id):

    ticket = Ticket.query.filter_by(id=ticket_id).with_for_update().first_or_404()

    # Chỉ chủ Ticket được xác nhận
    if ticket.created_by_id != current_user.id:
        abort(403)

    # Chỉ xác nhận khi Ticket đang Resolved
    if ticket.status != "Resolved":

        flash("Ticket chưa ở trạng thái chờ xác nhận.", "danger")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    confirmation = request.form.get("confirmation")

    # User xác nhận đã sửa xong
    if confirmation == "fixed":

        ticket.resolution_confirmed = True

        audit(request.endpoint, ticket.status, ticket.id)
        db.session.commit()

        flash(
            "Bạn đã xác nhận sự cố được khắc phục. " "Ticket đang chờ IT Support đóng.",
            "success",
        )

    # User báo vẫn còn lỗi
    elif confirmation == "not_fixed":

        ticket.resolution_confirmed = False

        ticket.status = "In Progress"

        ticket.resolved_at = None

        audit(request.endpoint, ticket.status, ticket.id)
        db.session.commit()

        flash(
            "Sự cố vẫn chưa được khắc phục. "
            "Ticket đã được chuyển lại cho IT Support.",
            "warning",
        )

    else:

        abort(400)

    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@ticket_bp.route("/tickets/<int:ticket_id>/accept", methods=["POST"])
@login_required
@roles_required("Admin", "IT Support")
def accept_ticket(ticket_id):

    ticket = Ticket.query.filter_by(id=ticket_id).with_for_update().first_or_404()

    if ticket.status != "Open":

        flash("Ticket này không còn ở trạng thái chờ tiếp nhận.", "warning")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    if ticket.assigned_to_id is not None and ticket.assigned_to_id != current_user.id:

        flash("Ticket này đã được phân công cho nhân viên khác.", "warning")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    ticket.assigned_to_id = current_user.id

    ticket.status = "In Progress"

    audit(request.endpoint, ticket.status, ticket.id)
    db.session.commit()

    flash("Bạn đã tiếp nhận Ticket và bắt đầu xử lý.", "success")

    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@ticket_bp.route("/tickets/<int:ticket_id>/transfer", methods=["POST"])
@login_required
@roles_required("Admin", "IT Support")
def transfer_ticket(ticket_id):

    ticket = Ticket.query.filter_by(id=ticket_id).with_for_update().first_or_404()

    # Chỉ chuyển Ticket đang được xử lý
    if ticket.status != "In Progress":

        flash("Chỉ Ticket đang xử lý mới được chuyển.", "warning")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    if current_user.role == "IT Support" and ticket.assigned_to_id != current_user.id:

        flash("Bạn không phải người đang phụ trách Ticket này.", "danger")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    new_assignee_id = request.form.get("assigned_to_id")

    if not new_assignee_id:

        flash("Vui lòng chọn người nhận Ticket.", "danger")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    try:
        new_assignee_id = int(new_assignee_id)

    except ValueError:
        abort(400)

    new_assignee = db.session.get(User, new_assignee_id)

    if not new_assignee:
        abort(404)

    if not new_assignee.enabled or new_assignee.role not in ["IT Support", "Admin"]:
        abort(400)

    if ticket.assigned_to_id == new_assignee.id:

        flash("Ticket đang được người này xử lý.", "warning")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    ticket.assigned_to_id = new_assignee.id

    ticket.status = "In Progress"

    audit(request.endpoint, ticket.status, ticket.id)
    db.session.commit()

    flash(f"Đã chuyển Ticket cho {new_assignee.username}.", "success")

    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@ticket_bp.route("/it/dashboard")
@login_required
@roles_required("IT Support", "Admin")
def it_dashboard():

    tab = request.args.get("tab", "unaccepted")

    keyword = request.args.get("keyword", "").strip()

    category_id = request.args.get("category_id", "").strip()

    if current_user.role == "Admin":

        base_query = Ticket.query

    else:
        base_query = Ticket.query.filter(
            or_(Ticket.status == "Open", Ticket.assigned_to_id == current_user.id),
        )

    count_unaccepted = base_query.filter(Ticket.status == "Open").count()

    count_in_progress = base_query.filter(Ticket.status == "In Progress").count()

    count_waiting_user = base_query.filter(
        Ticket.status == "Resolved", Ticket.resolution_confirmed.is_(None)
    ).count()

    count_done = base_query.filter(
        Ticket.status == "Resolved", Ticket.resolution_confirmed.is_(True)
    ).count()

    count_closed = base_query.filter(Ticket.status == "Closed").count()

    query = base_query

    if tab == "unaccepted":

        query = query.filter(Ticket.status == "Open")

    elif tab == "in_progress":

        query = query.filter(Ticket.status == "In Progress")

    elif tab == "waiting_user":

        query = query.filter(
            Ticket.status == "Resolved", Ticket.resolution_confirmed.is_(None)
        )

    elif tab == "done":

        query = query.filter(
            Ticket.status == "Resolved", Ticket.resolution_confirmed.is_(True)
        )

    elif tab == "closed":

        query = query.filter(Ticket.status == "Closed")

    elif tab == "all":

        pass

    if keyword:

        query = query.filter(Ticket.title.ilike(f"%{keyword}%"))

    if category_id:

        try:
            category_number = int(category_id)
        except ValueError:
            abort(400, description="Danh mục không hợp lệ.")
        query = query.filter(Ticket.category_id == category_number)

    tickets = query.order_by(Ticket.updated_at.desc()).all()

    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "it_dashboard.html",
        tickets=tickets,
        categories=categories,
        current_tab=tab,
        keyword=keyword,
        selected_category_id=category_id,
        count_unaccepted=count_unaccepted,
        count_in_progress=count_in_progress,
        count_waiting_user=count_waiting_user,
        count_done=count_done,
        count_closed=count_closed,
    )


@ticket_bp.route("/tickets/<int:ticket_id>/resolve", methods=["POST"])
@login_required
@roles_required("Admin", "IT Support")
def resolve_ticket(ticket_id):

    ticket = Ticket.query.filter_by(id=ticket_id).with_for_update().first_or_404()

    if ticket.status != "In Progress":

        flash("Chỉ Ticket đang xử lý mới có thể hoàn tất.", "warning")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    if current_user.role == "IT Support" and ticket.assigned_to_id != current_user.id:

        flash("Bạn không phải người đang phụ trách Ticket này.", "danger")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    resolution_note = text_field("resolution_note", 10000)

    if not resolution_note:

        flash("Vui lòng nhập phương án xử lý.", "danger")

        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    ticket.resolution_note = resolution_note

    ticket.status = "Resolved"

    ticket.resolved_at = datetime.utcnow()

    ticket.resolution_confirmed = None

    audit(request.endpoint, ticket.status, ticket.id)
    db.session.commit()

    flash("Đã gửi kết quả xử lý cho người dùng xác nhận.", "success")

    return redirect(url_for("tickets.it_dashboard", tab="waiting_user"))
