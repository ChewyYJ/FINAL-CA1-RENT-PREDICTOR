from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# user auth
from flask_login import LoginManager

# Create the Flask App
app = Flask(__name__)

# load configuration from config.cfg
app.config.from_pyfile("config.cfg")  

# create db object
db = SQLAlchemy(app)

# ------------ Flask-Login setup ------------
login_manager = LoginManager(app)

# which endpoint to redirect to when @login_required fails
login_manager.login_view = "login"          # create a login() route later
login_manager.login_message_category = "info"   # flash category for "Please log in" msg
# -------------------------------------------

# Import models (need User + Prediction for DB + login_manager)
from application.models import Prediction, User

# tell Flask-Login how to load a user from an ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# import routes so the decorators register with 'app'
from application import routes


# new method for SQLAlchemy version 3 onwards
with app.app_context():
    # db.drop_all()
    db.create_all()
    print('Created Database!')