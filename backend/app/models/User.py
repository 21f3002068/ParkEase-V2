from ... import db
from flask_security import UserMixin, RoleMixin

class User(db.Model, UserMixin):
    """
    This is a model for the User table in the database. Required for flask security.
    It defines the structure of the table and the fields it contains.
    """
        
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False) # Unique identifier for Flask-Security, used for user identification using their credentials. Helps creating token for user authentication.
    active = db.Column(db.Boolean(), default=True, nullable=False)  # Indicates if the user account is active or not.
    is_flagged = db.Column(db.Boolean(), default=False, nullable=False)  # Indicates if the user has been flagged by admin.
    
    
    #Extra fields for user profile
    first_name = db.Column(db.String(50), nullable=True)  # Optional field for the user's first name.
    last_name = db.Column(db.String(50), nullable=True)   # Optional field for the user's last name.
    username = db.Column(db.String(80), unique=True, nullable=False)  # Unique username for the user.
    phone_number = db.Column(db.String(15), unique=True, nullable=True)  # Optional field for the user's phone number.
    address = db.Column(db.String(255), nullable=True)  # Optional field for the user's address.
    pincode = db.Column(db.String(10), nullable=True)  # Optional field for the user's pincode.
    google_chat_webhook = db.Column(db.String(500), nullable=True)  # Optional Google Chat webhook URL for notifications
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

    # Relationships
    roles = db.relationship('Role', secondary='user_roles', 
                            # backref=db.backref('users', lazy='dynamic')
                            backref='bearer') 

    reservations = db.relationship(
        'Reservation',
        backref='user',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    vehicles = db.relationship(
        'Vehicle',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    favorites = db.relationship(
        'Favorite',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    reviews = db.relationship(
        'Review',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f'<User {self.username}>'
    
    
class Role(db.Model, RoleMixin):
    """
    Represents a role in the system, which can be assigned to users.
    This model is used to define different roles such as admin and user.
    """
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Role {self.name}>'
    
#many-to-many
class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)


