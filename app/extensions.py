from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate


db = SQLAlchemy()

login_manager = LoginManager()

migrate = Migrate()
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
