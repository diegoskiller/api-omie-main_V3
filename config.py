
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from models import *
import pymysql
import os
from dotenv import load_dotenv

from flask_cors import CORS

load_dotenv()

app = Flask (__name__)
db = SQLAlchemy(app)
CORS(app)

app_key = os.getenv('APP_KEY')
app_secret = os.getenv('APP_SECRET') 
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)

db.init_app(app)
conexao = os.getenv('URL_MYSQL') 

migrate = Migrate(app, db)

app.config['SECRET_KEY'] = 'my-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = conexao
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure Flask-SocketIO
socketio = SocketIO(app)

# Restante das configurações e importações

# flask db init
# flask db migrate -m "teste de migraçãoo"
# flask db upgrade

# flask db stamp head
# flask db migrate
# flask db upgrade