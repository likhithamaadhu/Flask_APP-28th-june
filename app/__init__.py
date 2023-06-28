from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()
migrate = Migrate()

def create_app():
    app= Flask(__name__)

    app.config.from_pyfile('config.py')
    db.init_app(app)
    migrate.init_app(app,db)

    from app.models import Book,post_books_schema
    from app.routes import book_api
    app.register_blueprint(book_api)

    return app