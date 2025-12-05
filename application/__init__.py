from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create the Flask App
app = Flask(__name__)

# load configuration from config.cfg
app.config.from_pyfile("config.cfg")  

# create db object
db = SQLAlchemy(app)

# import routes so the decorators register with 'app'
from application import routes

from application.models import Prediction

# new method for SQLAlchemy version 3 onwards
with app.app_context():
    db.create_all()
    print('Created Database!')