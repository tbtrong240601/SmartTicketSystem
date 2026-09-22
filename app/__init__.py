from flask import Flask

from config import Config
from app.extensions import db, login_manager, migrate



def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    login_manager.init_app(app)
    
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.tickets import ticket_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ticket_bp)

    with app.app_context():

        from app import models

        db.create_all()

    return app