from datetime import datetime, timedelta
from flask import Blueprint, abort, current_app, render_template, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Ticket, AIRequest, User
from app.services.ai import retrieve, answer
from app.services.common import text_field

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
        db.session.commit()
    elif ticket:
        question = f"{ticket.title}\n{ticket.description}"[:2000]
    return render_template("ai.html", result=result, articles=articles, question=question,
        ticket=ticket, groq_ready=bool(current_app.config["GROQ_API_KEY"]))
