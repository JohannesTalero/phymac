import os
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import bleach
import markdown
from database import db
from utils.docx_converter import import_docx_to_blog
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

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

from models import Post, Book, Contact, User

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
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('blog.html', posts=posts)

@app.route('/blog/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        # Sanitize input
        title = bleach.clean(title)
        content = bleach.clean(content, tags=['p', 'h1', 'h2', 'h3', 'pre', 'code'])

        post = Post(
            title=title, 
            content=content,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('post', post_id=post.id))

    return render_template('editor.html')

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
    books = Book.query.all()
    return render_template('books.html', books=books)

@app.route('/import-document', methods=['GET', 'POST'])
@login_required
def import_document():
    if not current_user.is_admin:
        flash('No tienes permiso para acceder a esta página')
        return redirect(url_for('index'))

    if request.method == 'POST':
        success, message = import_docx_to_blog('attached_assets/Estatutos_Fundacion_Final (1).docx')
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        return redirect(url_for('blog'))
    return render_template('import_document.html')

with app.app_context():
    db.create_all()
    # Create admin user if it doesn't exist
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin')  # Change this password in production!
        db.session.add(admin)
        db.session.commit()