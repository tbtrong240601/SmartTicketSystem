from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import KnowledgeArticle, Category, Ticket
from app.utils.decorators import roles_required
from app.services.common import audit, text_field, optional_category

knowledge_bp = Blueprint("knowledge", __name__, url_prefix="/knowledge")


@knowledge_bp.before_request
@login_required
def require_login():
    pass


def visible_articles():
    if current_user.role == "Admin":
        return KnowledgeArticle.query
    if current_user.role == "IT Support":
        return KnowledgeArticle.query.filter(or_(KnowledgeArticle.published.is_(True), KnowledgeArticle.author_id == current_user.id))
    return KnowledgeArticle.query.filter_by(published=True)


@knowledge_bp.get("/")
def index():
    query = visible_articles()
    keyword = request.args.get("q", "").strip()[:200]
    if keyword:
        query = query.filter(or_(KnowledgeArticle.title.ilike(f"%{keyword}%"), KnowledgeArticle.content.ilike(f"%{keyword}%")))
    category = request.args.get("category_id", type=int)
    if category:
        query = query.filter_by(category_id=category)
    page = query.order_by(KnowledgeArticle.updated_at.desc()).paginate(page=request.args.get("page", 1, type=int), per_page=12, error_out=False)
    return render_template("knowledge/index.html", page=page, keyword=keyword, categories=Category.query.order_by(Category.name).all())


@knowledge_bp.get("/<int:article_id>")
def detail(article_id):
    article = visible_articles().filter_by(id=article_id).first_or_404()
    return render_template("knowledge/detail.html", article=article)


@knowledge_bp.route("/new", methods=["GET", "POST"])
@knowledge_bp.route("/<int:article_id>/edit", methods=["GET", "POST"])
@roles_required("Admin", "IT Support")
def edit(article_id=None):
    article = db.get_or_404(KnowledgeArticle, article_id) if article_id else None
    if article and current_user.role != "Admin" and (article.author_id != current_user.id or article.published):
        abort(403)
    if request.method == "POST":
        if article is None:
            article = KnowledgeArticle(author_id=current_user.id)
            db.session.add(article)
        article.title = text_field("title", 200)
        article.content = text_field("content", 20000, 20)
        article.category_id = optional_category()
        article.published = current_user.role == "Admin" and request.form.get("published") == "on"
        audit("knowledge.save", article.title)
        db.session.commit()
        flash("Đã lưu bài viết.", "success")
        return redirect(url_for("knowledge.detail", article_id=article.id))
    return render_template("knowledge/edit.html", article=article, categories=Category.query.order_by(Category.name).all())


@knowledge_bp.post("/<int:article_id>/delete")
@roles_required("Admin")
def delete(article_id):
    article = db.get_or_404(KnowledgeArticle, article_id)
    audit("knowledge.delete", article.title)
    db.session.delete(article)
    db.session.commit()
    flash("Đã xóa bài viết.", "success")
    return redirect(url_for("knowledge.index"))


@knowledge_bp.post("/from-ticket/<int:ticket_id>")
@roles_required("Admin", "IT Support")
def from_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)
    if current_user.role != "Admin" and ticket.assigned_to_id != current_user.id:
        abort(403)
    if ticket.status not in ("Resolved", "Closed") or not ticket.resolution_note:
        abort(400, description="Ticket cần có phương án xử lý trước khi tạo bài viết.")
    article = KnowledgeArticle(title=ticket.title, content=ticket.resolution_note,
        category_id=ticket.category_id, author_id=current_user.id, published=False)
    db.session.add(article)
    audit("knowledge.from_ticket", "Tạo bản nháp từ phương án xử lý", ticket.id)
    db.session.commit()
    flash("Đã tạo bản nháp. Hãy bỏ thông tin riêng tư trước khi Admin xuất bản.", "info")
    return redirect(url_for("knowledge.edit", article_id=article.id))
