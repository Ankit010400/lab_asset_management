
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

# Flask app setup
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')

# Asset model
class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    is_available = db.Column(db.Boolean, default=True)

# BorrowLog model
class BorrowLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    borrowed_at = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime, nullable=True)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Check if user exists
        if User.query.filter_by(username=username).first():
            return "User already exists. Please choose another username."

        new_user = User(username=username, password=hashed_password, role='user')
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password. Please try again."

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    assets = Asset.query.all()
    return render_template('dashboard.html', assets=assets)

@app.route('/borrow/<int:asset_id>')
def borrow(asset_id):
    asset = Asset.query.get(asset_id)
    if asset and asset.is_available:
        # Borrow logic here
        return f"Asset {asset.name} borrowed."
    return "Asset not available."

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
