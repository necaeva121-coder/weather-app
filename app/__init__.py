# app/__init__.py
from flask import Flask
from .extensions import db, migrate, login_manager
from .config import Config

from .routes.user import user
from .routes.weather import weather


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.register_blueprint(user)
    app.register_blueprint(weather)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # ensure models are loaded for migrations and create_all
    from .models import user as user_models  # noqa: F401
    from .models import weather as weather_models  # noqa: F401

    # Login manager
    login_manager.login_view = 'user.login'
    login_manager.login_message = 'Вы не можете перейти на данную страницу. Авторизуйтесь!'
 
    with app.app_context():
        db.create_all()

    return app