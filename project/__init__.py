from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

from .extensions import db
from .views import main

# from .utils import make_celery


def create_app():
    app = Flask(__name__)

    database_url = os.environ["DATABASE_URL"]
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    app.register_blueprint(main)

    return app
