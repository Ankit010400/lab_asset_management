from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime

# Initialize the app
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab_assets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'supersecretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database
with app.app_context():
    db.create_all()

# Routes for GUI
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
@jwt_required()
def dashboard():
    current_user = get_jwt_identity()
    assets = Asset.query.all()
    user_assets = Asset.query.filter_by(assigned_to=current_user['id']).all()
    if current_user['role'] == 'admin':
        return render_template('admin_dashboard.html', assets=assets)
    return render_template('user_dashboard.html', assets=assets, user_assets=user_assets)

@app.route('/log_asset', methods=['POST'])
@jwt_required()
def log_asset():
    data = request.form
    action = data.get('action')
    asset_id = data.get('asset_id')
    asset = Asset.query.get_or_404(asset_id)

    if action == 'check-out':
        if not asset.is_available:
            return redirect(url_for('dashboard', message='Asset not available'))
        asset.is_available = False
        asset.assigned_to = get_jwt_identity()['id']
    elif action == 'check-in':
        if asset.assigned_to != get_jwt_identity()['id']:
            return redirect(url_for('dashboard', message='Unauthorized return attempt'))
        asset.is_available = True
        asset.assigned_to = None

    transaction = Transaction(asset_id=asset.id, user_id=get_jwt_identity()['id'], action=action)
    db.session.add(transaction)
    db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
