import os
from flask_sqlalchemy import SQLAlchemy
from . import app

database_url = os.environ["DATABASE_URL"]


# Check if the URL starts with postgres:// and replace it with postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
print(database_url)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
db = SQLAlchemy(app)
