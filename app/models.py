from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager

from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="User")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)

    description = db.Column(db.String(255), nullable=True)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(50), nullable=False, default="Open")

    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    created_by = db.relationship(
        "User", foreign_keys=[created_by_id], backref="tickets_created"
    )

    assigned_to = db.relationship(
        "User", foreign_keys=[assigned_to_id], backref="tickets_assigned"
    )

    category = db.relationship("Category", backref="tickets")

    resolution_confirmed = db.Column(db.Boolean, nullable=True, default=None)

    resolution_note = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.func.now(),
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.func.now(),
        onupdate=datetime.utcnow,
    )

    resolved_at = db.Column(db.DateTime, nullable=True)

    closed_at = db.Column(db.DateTime, nullable=True)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticket = db.relationship("Ticket", backref="comments")

    user = db.relationship("User", backref="comments")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
