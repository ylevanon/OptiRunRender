from flask import Flask
from flask_login import LoginManager
import os
from .extensions import db
from .commands import create_tables
from .models import User  # Import the User model
from flask_migrate import Migrate


from .extensions import db

# from .utils import make_celery


def create_app():
    app = Flask(__name__)

    database_url = os.environ["DATABASE_URL"]
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    db.init_app(app)

    migrate = Migrate(app, db)
    # Initialize Flask-Login
    login_manager = LoginManager(app)
    login_manager.login_view = "main.login"  # Specify the login view

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .views import main

    app.register_blueprint(main)
    app.cli.add_command(create_tables)
    return app
