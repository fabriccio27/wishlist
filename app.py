from datetime import datetime
from flask import Flask, flash,redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session 
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, apology, url_checker
import random
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pwl.db'
db = SQLAlchemy(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(40), nullable=False)
    active = db.Column(db.DateTime, default=datetime.now)
    products = db.relationship("Product", backref="user")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    link = db.Column(db.Text, nullable=False)
    store = db.Column(db.String(5), nullable=False) # puede ser nullable esto?
    additional = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Checked(db.Model):
    checked_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False) # si le pongo foreignkey, cuando quiera borrar producto no me va a dejar
    giver_id = db.Column(db.Integer, db.ForeignKey("user.id")) # puede ser nulo, si yo mismo estoy descartando
    taker_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    completed = db.Column(db.Boolean, nullable=False)
    discarded = db.Column(db.Boolean, nullable=False)

class Candidate(db.Model):
    proposal_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    candidate_id = db.Column(db.Integer, nullable=False)
    proposal_date = db.Column(db.DateTime, default=datetime.now)


@app.route("/")
@login_required
def index():
    user_id = session["user_id"] 
    elements = Product.query.filter_by(user_id=user_id).all()
    others = User.query.filter(User.id.isnot(user_id)).all()
    
    print(elements)
    print(f"These are the other users:\n{others}")
    # muestro los 3 primeros?
    
    return render_template("index.html", cards=elements[:3], users=others)

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("You must provide a username")
        coincidence = User.query.filter_by(username=request.form.get("username")).all() 
        #all() me devuelve lista con un elemento. Si hubiera puesto first() me da el elemento directamente, y ese no tiene funcion len
        if len(coincidence)!=0:
            return apology("Username already exist")

        if (request.form.get("password")!=request.form.get("confirmation")):
            return apology("Password and confirmation didn't match") 
        
        user = User(
            username = request.form.get("username"),
            password = generate_password_hash(request.form.get("password")),
            email =  request.form.get("email")
        )
        db.session.add(user)
        db.session.commit()

        flash("You've successfully registered. Log in.")
        return redirect("/login")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = User.query.filter_by(username=request.form.get("username")).all()
        
        if len(rows) != 1 or not check_password_hash(rows[0].password, request.form.get("password")):
            return apology("invalid username and/or password", 403)
        # Remember which user has logged in
        session["user_id"] = rows[0].id
        flash("Welcome!")
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/add-product", methods = ["GET", "POST"])
@login_required
def add_product():
    if request.method=="POST":
        if not request.form.get("product_url"):
            return apology("Sorry, you didn't provide a link to the object")
    
        link = request.form.get("product_url")
        store = request.form.get("store")

        if url_checker(link,store)!=200:
            return apology("The link you're trying to add is down or product not found")

        prod = Product(
            name=request.form.get("title"),
            link=link,
            additional=request.form.get("optional"),
            store=store,
            user_id=session["user_id"]
        )
        db.session.add(prod)
        db.session.commit()
        flash("wish added successfully")
        return redirect("/")
    else:
        return render_template("add.html")

@app.route("/user/<int:id>/wishes", methods = ["GET", "POST"])
def view_user(id):
    
    if request.method == "POST":
        visitor = session["user_id"]
        card_id = request.form.get("card_id")
        
        candidate = Candidate(
            product_id = card_id,
            candidate_id = visitor
        )
        #tengo que dejar registrado que un usuario se anoto para un regalo
        db.session.add(candidate)
        db.session.commit()
        flash("You've postulated to this wish")
        
        return "working on post branch"
    else:
        visited_user = User.query.get_or_404(id)
        #tengo que hacer query de candidatos de cada card
        print(f"Name of visited user {visited_user.username}")
        return render_template("viewuser.html", user=visited_user)

@app.route("/mywishes", methods = ["GET", "POST"])
def my_wishes():

    if request.method=="POST":
        # get the specified product
        state = request.form.get("checkout")
        target = request.form.get("card_id")
        print(f"State is: {state}")
        print(f"Target ID is: {target}")
        # assume state is 'complete'
        completed = 1
        discarded = 0
        receiver = session["user_id"]

        #if state is discard I don't need further information. Create data in checked, delete in product and redirect
        if state=='discard':
            #modify state if it's not completed
            completed=0
            discarded=1

            checked = Checked(
                product_id = target,
                taker_id = receiver,
                completed = completed,
                discarded = discarded
            )
            db.session.add(checked)
            # para borrar el elemento de Product, tengo que hacer query, db.session.delete y luego el commit
            to_delete = Product.query.filter_by(id=target).first()
            db.session.delete(to_delete)
            db.session.commit()
            flash(f"You've discarded successfully item #{target}")
            return redirect("/")
        
        # if state is completed I need info about who completed the task
        return "working on post branch"

    else:
        myself = User.query.get_or_404(session["user_id"])
        return render_template('mywishes.html', user=myself)
    
    

'''funciones para generar data'''
from faker import Faker
fake = Faker()

def add_users():
    for _ in range(10):
        first_name = fake.unique.first_name()
        email_service = random.choices(["@gmail.com", "@outlook.com", "@aol.com"],[40,30,20])[0]
        email = first_name + email_service
        
        user =  User(
            username = first_name, #esto es un string
            password = fake.last_name(),
            email = email
        )
        '''username tiene que ser unico, porque es la manera en que voy a rechazar usernames ya utilizados
        como el password es cualquier cosa le voy a pasar apellidos, no hace falta que sean unicos
        para los usuarios reales tendria que hacer algo como hash_pw = generate_password_hash(password)'''
        db.session.add(user)
    db.session.commit()

def add_products():
    pass

def generate_data():
    db.create_all()
    add_users()


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

