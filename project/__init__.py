import os

from flask import Flask

from .views import main
from .utils import make_celery

def create_app():
    app = Flask(__name__)
    
    app.config["CELERY_CONFIG"] = {"broker_url": os.environ.get("REDIS_URL"), "result_backend": os.environ.get("REDIS_URL")}

    celery = make_celery(app)
    celery.set_default()
    
    app.register_blueprint(main)

    return app, celery