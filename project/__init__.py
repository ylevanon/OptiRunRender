import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .views import main

# from .utils import make_celery


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

    app.register_blueprint(main)

    return app
