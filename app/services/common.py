from flask import abort, request
from flask_login import current_user
from app.extensions import db
from app.models import AuditEvent


def audit(action, detail="", ticket_id=None):
    db.session.add(AuditEvent(actor_id=current_user.id if current_user.is_authenticated else None,
                              action=action, detail=detail[:500], ticket_id=ticket_id))


def text_field(name, maximum, minimum=1):
    value = request.form.get(name, "").strip()
    if not minimum <= len(value) <= maximum:
        abort(400, description=f"Trường {name} cần từ {minimum} đến {maximum} ký tự.")
    return value


def optional_category():
    from app.models import Category
    value = request.form.get("category_id", "")
    if not value:
        return None
    try:
        identifier = int(value)
    except ValueError:
        abort(400, description="Danh mục không hợp lệ.")
    if not db.session.get(Category, identifier):
        abort(400, description="Danh mục không tồn tại.")
    return identifier
