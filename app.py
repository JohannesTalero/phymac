import os
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import bleach
import markdown
from database import db
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from slugify import slugify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key_123"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from models import Post, Book, Contact, User, Category

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Has iniciado sesión correctamente')
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente')
    return redirect(url_for('index'))

@app.route('/blog')
def blog():
    category_id = request.args.get('category', type=int)
    if category_id:
        posts = Post.query.filter_by(category_id=category_id).order_by(Post.created_at.desc()).all()
        category = Category.query.get_or_404(category_id)
    else:
        posts = Post.query.order_by(Post.created_at.desc()).all()
        category = None
    categories = Category.query.filter_by(type='post').all()
    return render_template('blog.html', posts=posts, categories=categories, current_category=category)

@app.route('/blog/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():
    categories = Category.query.filter_by(type='post').all()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id', type=int)

        # Sanitize input
        title = bleach.clean(title)
        content = bleach.clean(content, tags=['p', 'h1', 'h2', 'h3', 'pre', 'code'])

        post = Post(
            title=title, 
            content=content,
            author=current_user,
            category_id=category_id
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('post', post_id=post.id))

    return render_template('editor.html', categories=categories)

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if not current_user.is_admin:
        flash('Acceso denegado')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        type = request.form.get('type')
        if name and type:
            slug = slugify(name)
            category = Category(name=name, slug=slug, type=type)
            db.session.add(category)
            db.session.commit()
            flash('Categoría creada correctamente')
            return redirect(url_for('manage_categories'))

    post_categories = Category.query.filter_by(type='post').all()
    book_categories = Category.query.filter_by(type='book').all()
    return render_template('categories.html', 
                         post_categories=post_categories, 
                         book_categories=book_categories)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = bleach.clean(request.form.get('name'))
        email = bleach.clean(request.form.get('email'))
        message = bleach.clean(request.form.get('message'))

        contact = Contact(name=name, email=email, message=message)
        db.session.add(contact)
        db.session.commit()
        flash('Mensaje enviado correctamente')
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/books')
def books():
    category_id = request.args.get('category', type=int)
    if category_id:
        books = Book.query.filter_by(category_id=category_id).all()
        category = Category.query.get_or_404(category_id)
    else:
        books = Book.query.all()
        category = None
    categories = Category.query.filter_by(type='book').all()
    return render_template('books.html', 
                         books=books, 
                         categories=categories, 
                         current_category=category)

with app.app_context():
    db.create_all()
    # Create admin user if it doesn't exist
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin')  # Change this password in production!
        db.session.add(admin)
        db.session.commit()