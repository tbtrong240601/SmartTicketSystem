from flask import Flask, render_template
from config import Config
from app.extensions import db, login_manager, migrate, csrf


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.tickets import ticket_bp
    from app.routes.admin import admin_bp
    from app.routes.knowledge import knowledge_bp
    from app.routes.ai import ai_bp
    for blueprint in (main_bp, auth_bp, ticket_bp, admin_bp, knowledge_bp, ai_bp):
        app.register_blueprint(blueprint)
    from app.cli import register_commands
    register_commands(app)

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "same-origin"
        if response.mimetype == "text/html":
            response.headers["Cache-Control"] = "no-store"
        return response

    def render_error(error):
        db.session.rollback()
        return render_template("error.html", code=error.code, message=error.description), error.code
    for code in (400, 403, 404, 413, 429):
        app.register_error_handler(code, render_error)
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("error.html", code=500, message="Không thể xử lý yêu cầu. Vui lòng thử lại hoặc liên hệ quản trị viên."), 500
    return app
