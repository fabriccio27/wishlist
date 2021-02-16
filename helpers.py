from flask import request, session, render_template, redirect
from functools import wraps
import requests

def url_checker(potential_url, store):
    try:
        response = requests.get(potential_url)
        #no pongo aca lo de content-length porque no todos las paginas tienen ese header
    except:
        #va a entrar acá cuando haga por ejemplo "www.lsf.co" o ".lsf.co" algo que no se parezca nada a url
        print("excepcion")
        return apology("The link (url) you're trying to add is not valid")
    #tengo que ver devolver un codigo, o un 200 mas content-length > 55000 en el caso de lsf
    #ya que lsf devuelve un 200 para libros no encontrados, pero el content-length siempre esta por 53k
    
    if store=="lsf" and int(response.headers['content-length'])<55000:
        return 400

    return response.status_code


def apology(message, code=400):
    return render_template("apology.html", bottom=message, top=code),code

def login_required(f):
    """
    Decorate routes to require login.
    f seria por ejemplo quote() en la ruta /quote
    wraps(f) como que guarda todo

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function