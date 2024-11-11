from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dreams.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


class Dream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image_filename = db.Column(db.String(100), nullable=True)


# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Registration route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None  # Initialize an error variable
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email and password:  # Ensure both fields are provided
            # Check if the email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error = 'There is already a registered account with that email.'  # Set error message
            else:
                # Hash the password and create a new user
                password = generate_password_hash(password, method='pbkdf2:sha256')
                new_user = User(email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful!')
                return redirect(url_for('login'))
        else:
            error = 'Please provide both email and password.'  # Error for empty fields
    return render_template('signup.html', error=error)  # Pass the error to the template

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']  # This must match the input name
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('diary'))
        flash('Login failed. Check your email and password.')
    return render_template('login.html')

# Diary route
@app.route('/diary', methods=['GET', 'POST'])
def diary():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        new_dream = Dream(title=title, description=description, date=date, user_id=session['user_id'])
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_dream.image_filename = filename
        db.session.add(new_dream)
        db.session.commit()
        flash('Dream added successfully!')
    dreams = Dream.query.filter_by(user_id=session['user_id']).all()
    return render_template('diary.html', dreams=dreams)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Edit Dream route
@app.route('/edit_dream/<int:dream_id>', methods=['GET', 'POST'])
def edit_dream(dream_id):
    dream = Dream.query.get_or_404(dream_id)
    if request.method == 'POST':
        dream.title = request.form['title']
        dream.description = request.form['description']
        dream.date = request.form['date']
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                dream.image_filename = filename
        db.session.commit()
        flash('Dream updated successfully!')
        return redirect(url_for('diary'))
    return render_template('edit_dream.html', dream=dream)

# Delete Dream route
@app.route('/delete_dream/<int:dream_id>', methods=['POST'])
def delete_dream(dream_id):
    dream = Dream.query.get_or_404(dream_id)
    db.session.delete(dream)
    db.session.commit()
    flash('Dream deleted successfully!')
    return redirect(url_for('diary'))

# About route
@app.route('/about')
def about():
    return render_template('about.html')

# 404 error handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
