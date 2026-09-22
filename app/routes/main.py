from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Ticket


main_bp = Blueprint(
    "main",
    __name__
)


@main_bp.route("/")
@login_required
def home():

    if current_user.role in ["Admin", "IT Support"]:
        tickets = Ticket.query.order_by(
            Ticket.id.desc()
        ).all()
        
    else:
        tickets = Ticket.query.filter_by(
            created_by_id = current_user.id
        ).order_by(
            Ticket.id.desc()
        ).all()
        
    return render_template("index.html", tickets = tickets)


