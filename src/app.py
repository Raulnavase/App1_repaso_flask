from flask import Flask, render_template, request, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user, logout_user
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from dotenv import load_dotenv
from os import getenv

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = getenv('MONGO_URI')
app.secret_key = getenv('SECRET_KEY')

mongo = PyMongo(app)
users_collection = mongo.db.users
mouses_collection = mongo.db.mouses

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.name = user_data['name']
        self.username = user_data['username']

@login_manager.user_loader
def load_user(id):
    user_data = users_collection.find_one({'_id': ObjectId(id)})
    return User(user_data) if user_data else None



@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Por favor, completa todos los campos.", "warning")
            return redirect(url_for('login'))

        user_data = users_collection.find_one({ "username": username })
        if user_data and check_password_hash(user_data['password'], password):
            login_user(User(user_data))

            return redirect(url_for('home'))
        
        flash("Nombre de usuario o contraseña incorrectos.", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        if not name or not username or not password:
            flash("Por favor, completa todos los campos.", "danger")
            return redirect(url_for('register'))

        user_data = users_collection.find_one({ "username": username })
        if user_data:
            flash("Nombre de usuario ya en uso, vuelva a intentarlo", "error")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({ "name": name, "username": username, "password": hashed_password })

        flash("Usuario registrado correctamente! Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html')


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.username != 'admin':
        return redirect(url_for('home'))
    
    return render_template('admin.html')


@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    if current_user.username != 'admin':
        if not users_collection.find():
            flash("NO HAY NADA")

        

            
    
        return redirect(url_for('home'))
    









@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
