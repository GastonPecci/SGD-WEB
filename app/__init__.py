from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from dotenv import load_dotenv
from flask_migrate import Migrate
import os

# Cargar las variables del archivo .env
load_dotenv()

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)

    # Configuración desde variables de entorno
    app.secret_key = os.getenv('SECRET_KEY', 'clave_por_defecto')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    mail.init_app(app)
    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app

app = create_app()
