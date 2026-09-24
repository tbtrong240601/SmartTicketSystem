from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models import Ticket

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
@login_required
def home():
    query = Ticket.query
    if current_user.role == "User":
        query = query.filter_by(created_by_id=current_user.id)
    keyword = request.args.get("q", "").strip()[:200]
    status = request.args.get("status", "")
    if keyword:
        query = query.filter(Ticket.title.ilike(f"%{keyword}%"))
    if status in ("Open", "In Progress", "Resolved", "Closed"):
        query = query.filter_by(status=status)
    page = query.order_by(Ticket.updated_at.desc()).paginate(page=request.args.get("page", 1, type=int), per_page=20, error_out=False)
    return render_template("index.html", tickets=page.items, page=page, keyword=keyword, status=status)
