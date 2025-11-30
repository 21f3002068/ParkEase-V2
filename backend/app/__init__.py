from flask import Flask
from .config import LocalDevelopmentConfig
from flask_cors import CORS
# from app.resources import api
from .. import db
from flask_security import Security, SQLAlchemyUserDatastore
from backend.app.models.User import User, Role, UserRoles
from .setup import initialize_roles_and_users
from flask_migrate import Migrate
from flask_restx import Api
# from flask import current_app
from flask_security import user_registered
from uuid import uuid4



def create_app():
    import os
    # Set static folder to backend/static
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
    app.config.from_object(LocalDevelopmentConfig)
    
    CORS(app, origins=["http://localhost:8080", "http://127.0.0.1:8080"], 
         allow_headers=["Content-Type", "auth-token", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    db.init_app(app)
    
    # Initialize Celery - use shared instance
    from backend.celery_app import celery_app
    app.celery = celery_app

    # Setup Flask-Security
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, datastore)

    migrate = Migrate(app, db)
    
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Initialize roles and users
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'role' in inspector.get_table_names():
                initialize_roles_and_users(security)
        except Exception as e:
            print(f"Warning: Could not initialize roles and users: {e}")
            # This is expected if migrations haven't been run yet

    @user_registered.connect_via(app)
    def assign_username_and_role(sender, user, confirm_token, **extra):
        from . import db
        from .models.User import Role
        from flask import current_app

        # Assign a username
        if not user.username:
            generated_username = user.email.split('@')[0] + uuid4().hex[:5]
            user.username = generated_username

        # Assign the 'user' role if not already there
        datastore = current_app.extensions['security'].datastore
        if not datastore.find_role('user'):
            datastore.create_role(name='user', description='Regular user')
        datastore.add_role_to_user(user, 'user')

        db.session.commit()

    from flask import Blueprint
    from flask_restx import Api
    from .routes.user_api import user_ns
    from .routes.admin_api import admin_ns
    from .routes.cached_user_api import cached_user_ns
    from .routes.cached_admin_api import cached_admin_ns
    from .routes.cache_api import cache_ns
    from .routes.login import auth_bp

    # Register the auth blueprint (for login)
    app.register_blueprint(auth_bp)

    # Register the API blueprint (for user/admin routes)
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    api = Api(api_bp, title="ParkEase API", version="1.0", doc="/docs") 

    api.add_namespace(user_ns, path='/user')
    api.add_namespace(admin_ns, path='/admin')
    api.add_namespace(cached_user_ns, path='/cached_user')
    api.add_namespace(cached_admin_ns, path='/cached_admin')
    api.add_namespace(cache_ns, path='/cache')

    app.register_blueprint(api_bp)


    @app.route("/")
    def index():
        return "Welcome to the ParkEase API. Go to /api/... for available routes."
    
    return app





