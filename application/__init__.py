from flask import Flask
#create the Flask app
app = Flask(__name__)
# load configuration from config.cfg
app.config.from_pyfile('config.cfg')
#run the file routes.py
from application import routes