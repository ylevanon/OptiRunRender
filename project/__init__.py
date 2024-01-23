from flask import Flask


from .views import main

# from .utils import make_celery


def create_app():
    app = Flask(__name__)
    app.register_blueprint(main)
    return app
