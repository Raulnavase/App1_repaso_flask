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
        self.rol = user_data['rol']


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
        users_collection.insert_one({ "name": name, "username": username, "password": hashed_password, "rol": "user" })

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
    if current_user.rol != 'admin':
        return redirect(url_for('home'))
    
    return render_template('admin.html')

# ---------------------------------------------------------------------------------------------

@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    if current_user.rol != 'admin':
        return redirect(url_for('home'))

    if users_collection.count_documents({}) == 0:
        return render_template("usuarios.html", msg="No hay usuarios")
    
    data = users_collection.find({ "rol": "user" })
    return render_template('usuarios.html', usuarios=data)
    

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.rol != 'admin':
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        rol = request.form['rol']

        if not name or not username or not password:
            flash("Por favor, completa todos los campos.", "warning")
            return redirect(url_for('add_user'))
        
        hashed_password = generate_password_hash(password)
        users_collection.insert_one({ "name": name, "username": username, "password": password, "rol": rol })

        flash("Usuario agregado con exito!", "success")
    
    return render_template("add_user.html")

# ---------------------------------------------------------------------------------------------

@app.route('/productos', methods=['GET', 'POST'])
@login_required
def productos():
    if current_user.rol != 'admin':
        return redirect(url_for('home'))

    if mouses_collection.count_documents({}) == 0:
        return render_template("productos.html", msg="No hay productos")
    
    data = mouses_collection.find()
    return render_template('productos.html', productos=data)


@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.rol != "admin":
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        img = request.form['img']

        if not name or not description or not price or not img:
            flash("Completa todos los campos", "danger")
            return redirect(url_for('add_product'))

        mouses_collection.insert_one({ "name": name, "description": description, "price": price, "img": img })
        flash("Producto agregado correctamente!", "success")

    return render_template("add_product.html")


@app.route('/delete_product/<string:id>')
@login_required
def delete_product(id):
    if current_user.rol != "admin":
        return redirect(url_for('home'))
    
    mouses_collection.delete_one({ "_id": ObjectId(id) })
    flash("Producto eliminado correctamente", "success")
    return redirect(url_for('productos'))

@app.route('/edit_product/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    if current_user.rol != "admin":
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        img = request.form['img']

        if not name or not description or not price or not img:
            flash("Completa todos los campos")
            return redirect(url_for('edit_product'))

        mouses_collection.update_one({ "_id": ObjectId(id) },
                                     { "$set": { "name": name, "description": description, "price": price, "img": img } })
    
        flash("Producto actualizado!", "success")
        return redirect(url_for('productos'))

    data = mouses_collection.find({ "_id": ObjectId(id) })
    return render_template("edit_product.html", product=data)


# ---------------------------------------------------------------------------------------------


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
