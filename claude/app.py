from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)
    unit_price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'incoming' or 'outgoing'
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    reference_number = db.Column(db.String(50))
    notes = db.Column(db.Text)

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(" ")[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
        
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        password=hashed_password,
        role=data.get('role', 'user')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password, data['password']):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        return jsonify({'token': token})
        
    return jsonify({'message': 'Invalid credentials'}), 401

# Product endpoints
@app.route('/api/products', methods=['GET'])
@token_required
def get_products(current_user):
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'quantity': p.quantity,
        'unit_price': p.unit_price,
        'category': p.category,
        'reorder_level': p.reorder_level
    } for p in products])

@app.route('/api/products', methods=['POST'])
@token_required
def add_product(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    new_product = Product(
        name=data['name'],
        description=data.get('description', ''),
        sku=data['sku'],
        quantity=data.get('quantity', 0),
        reorder_level=data.get('reorder_level', 10),
        unit_price=data['unit_price'],
        category=data.get('category')
    )
    
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({'message': 'Product added successfully', 'id': new_product.id}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
        
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(product, key):
            setattr(product, key, value)
    
    db.session.commit()
    return jsonify({'message': 'Product updated successfully'})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
        
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})

# Inventory transaction endpoints
@app.route('/api/transactions', methods=['POST'])
@token_required
def add_transaction(current_user):
    data = request.get_json()
    product = Product.query.get_or_404(data['product_id'])
    
    new_transaction = Transaction(
        product_id=data['product_id'],
        transaction_type=data['transaction_type'],
        quantity=data['quantity'],
        reference_number=data.get('reference_number'),
        notes=data.get('notes', '')
    )
    
    # Update product quantity
    if data['transaction_type'] == 'incoming':
        product.quantity += data['quantity']
    elif data['transaction_type'] == 'outgoing':
        if product.quantity < data['quantity']:
            return jsonify({'message': 'Insufficient inventory'}), 400
        product.quantity -= data['quantity']
    
    db.session.add(new_transaction)
    db.session.commit()
    
    return jsonify({'message': 'Transaction recorded successfully', 'id': new_transaction.id}), 201

@app.route('/api/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    transactions = Transaction.query.all()
    return jsonify([{
        'id': t.id,
        'product_id': t.product_id,
        'transaction_type': t.transaction_type,
        'quantity': t.quantity,
        'timestamp': t.timestamp,
        'reference_number': t.reference_number,
        'notes': t.notes
    } for t in transactions])

# Reports endpoints
@app.route('/api/reports/low-stock', methods=['GET'])
@token_required
def get_low_stock_report(current_user):
    low_stock_products = Product.query.filter(
        Product.quantity <= Product.reorder_level
    ).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'current_quantity': p.quantity,
        'reorder_level': p.reorder_level
    } for p in low_stock_products])

@app.route('/api/reports/inventory-value', methods=['GET'])
@token_required
def get_inventory_value_report(current_user):
    products = Product.query.all()
    total_value = sum(p.quantity * p.unit_price for p in products)
    
    return jsonify({
        'total_value': total_value,
        'products': [{
            'id': p.id,
            'name': p.name,
            'quantity': p.quantity,
            'unit_price': p.unit_price,
            'total_value': p.quantity * p.unit_price
        } for p in products]
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)