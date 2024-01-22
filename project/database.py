import os
from flask_sqlalchemy import SQLAlchemy
from . import app

DATABASE_URL = os.environ["DATABASE_URL"]

if __name__ == "__main__":
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    db = SQLAlchemy(app)
