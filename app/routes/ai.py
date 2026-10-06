from datetime import datetime, timedelta
from flask import Blueprint, abort, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Ticket, AIRequest, User, Category
from app.services.ai import retrieve, answer
from app.services.common import text_field, audit
from app.utils.decorators import roles_required
from app.services.triage import analyze

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")


@ai_bp.route("/", methods=["GET", "POST"])
@login_required
def assistant():
    ticket_id = request.values.get("ticket_id", type=int)
    ticket = db.get_or_404(Ticket, ticket_id) if ticket_id else None
    if ticket and current_user.role == "User" and ticket.created_by_id != current_user.id:
        abort(403)
    result = None
    articles = []
    question = ""
    if request.method == "POST":
        question = text_field("question", 2000, 5)
        # Serialize quota reservation across workers using the current user's row.
        db.session.query(User).filter_by(id=current_user.id).with_for_update().first()
        used = AIRequest.query.filter(AIRequest.user_id == current_user.id,
            AIRequest.created_at >= datetime.utcnow() - timedelta(hours=1)).count()
        if used >= current_app.config["AI_REQUESTS_PER_HOUR"]:
            abort(429, description="Bạn đã đạt giới hạn lượt hỏi trong giờ này. Vui lòng thử lại sau.")
        entry = AIRequest(user_id=current_user.id, ticket_id=ticket_id, mode="pending")
        db.session.add(entry)
        db.session.commit()
        # A ticket's title/description is sent only when explicitly included in the editable question.
        articles = retrieve(question)
        result = answer(question, articles, allow_external=request.form.get("external") == "on")
        entry.mode = result["mode"]
        entry.result = result
        entry.model = current_app.config["GROQ_MODEL"] if result["mode"] == "groq" else None
        db.session.commit()
    elif ticket:
        question = f"{ticket.title}\n{ticket.description}"[:2000]
    return render_template("ai.html", result=result, articles=articles, question=question,
        ticket=ticket, groq_ready=bool(current_app.config["GROQ_API_KEY"]))


@ai_bp.post("/tickets/<int:ticket_id>/analyze")
@login_required
@roles_required("Admin", "IT Support")
def analyze_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)
    if request.form.get("external") != "on":
        abort(400, description="Cần đồng ý gửi tiêu đề và mô tả Ticket đến Groq.")
    db.session.query(User).filter_by(id=current_user.id).with_for_update().first()
    used = AIRequest.query.filter(AIRequest.user_id == current_user.id,
        AIRequest.created_at >= datetime.utcnow() - timedelta(hours=1)).count()
    if used >= current_app.config["AI_REQUESTS_PER_HOUR"]:
        abort(429)
    entry = AIRequest(user_id=current_user.id, ticket_id=ticket.id, purpose="triage", mode="pending")
    db.session.add(entry)
    db.session.commit()
    result = analyze(ticket, Category.query.order_by(Category.name).all())
    entry.mode, entry.result = result["mode"], result
    entry.model = current_app.config["GROQ_MODEL"] if result["mode"] == "groq" else None
    audit("ai.analyze_ticket", result["mode"], ticket.id)
    db.session.commit()
    flash(result["notice"], "info")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))
