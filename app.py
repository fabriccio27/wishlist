from datetime import datetime
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session 

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pwl.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    active =  db.Column(db.DateTime, default=datetime.now)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    # tengo que pasar el password a un hash
    pass
