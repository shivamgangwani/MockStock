from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_session import Session


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'session_data'
app.config['SECRET_KEY'] = 'xK9os0zsA8hBAHsj'

Session(app)
csrf = CSRFProtect(app)

from app import routes