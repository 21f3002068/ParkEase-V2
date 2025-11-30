from flask import request, jsonify, Blueprint
from flask_security.utils import verify_and_update_password, hash_password
from backend.app.models.User import User, Role
from backend.app import db
from datetime import datetime
import re

# Create a blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if user and verify_and_update_password(password, user):
        # Generate authentication token using Flask-Security's method
        from flask import current_app
        token_data = current_app.extensions['security'].remember_token_serializer.dumps([str(user.fs_uniquifier)])
        
        # Get user roles
        user_roles = [{"name": role.name, "description": role.description} for role in user.roles]
        
        return jsonify({
            "response": {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "authentication_token": token_data,
                    "roles": user_roles,
                    "active": user.active
                }
            }
        })
    else:
        return jsonify({
            "response": {
                "errors": {
                    "email": ["Invalid credentials"]
                }
            }
        }), 401


@auth_bp.route('/api/signup', methods=['POST'])
def api_signup():
    """User registration endpoint - simplified to only require email and password"""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    # Extract form data
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validation
    errors = {}
    
    # Required fields
    if not email:
        errors['email'] = ['Email is required']
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors['email'] = ['Please enter a valid email address']
    elif User.query.filter_by(email=email).first():
        errors['email'] = ['Email already registered']
    
    if not password:
        errors['password'] = ['Password is required']
    elif len(password) < 6:
        errors['password'] = ['Password must be at least 6 characters long']
    
    if password != confirm_password:
        errors['confirm_password'] = ['Passwords do not match']
    
    # Return validation errors
    if errors:
        return jsonify({
            "response": {
                "errors": errors
            }
        }), 400
    
    try:
        # Create new user
        from flask import current_app
        user_datastore = current_app.extensions['security'].datastore
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Generate username from email (before @ symbol) and make it unique
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user with Flask-Security
        user = user_datastore.create_user(
            email=email,
            password=hashed_password,
            username=username,
            active=True,
            created_at=datetime.utcnow(),
            fs_uniquifier=str(__import__('uuid').uuid4())
        )
        
        # Assign default 'user' role
        user_role = Role.query.filter_by(name='user').first()
        if user_role:
            user_datastore.add_role_to_user(user, user_role)
        
        # Commit to database
        db.session.commit()
        
        return jsonify({
            "response": {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "active": user.active
                }
            },
            "message": "Account created successfully! Please login to continue."
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "response": {
                "errors": {
                    "general": [f"Registration failed: {str(e)}"]
                }
            }
        }), 500


@auth_bp.route('/api/check-availability', methods=['POST'])
def check_availability():
    """Check if email or username is available"""
    data = request.get_json()
    field = data.get('field')  # 'email' or 'username'
    value = data.get('value', '').strip()
    
    if field == 'email':
        exists = User.query.filter_by(email=value.lower()).first() is not None
    elif field == 'username':
        exists = User.query.filter_by(username=value).first() is not None
    else:
        return jsonify({"error": "Invalid field"}), 400
    
    return jsonify({
        "available": not exists,
        "message": f"{field.title()} {'already taken' if exists else 'is available'}"
    })
    