from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from .models.User import User, Role
from .. import db

# This will be called inside app context during setup
def initialize_roles_and_users(security):
    try:
        # Create roles
        security.datastore.find_or_create_role(
            name='admin', description='Administrator role. SuperUser. Has all permissions.')
        security.datastore.find_or_create_role(
            name='user', description='General user role. Can access basic features.')

        # Commit the roles
        db.session.commit()

        # Create Admin
        if not security.datastore.find_user(email="admin@parkease.com"):
            security.datastore.create_user(
                email="admin@parkease.com",
                username="admin",
                password=hash_password("admin"),
                roles=['admin', 'user']
            )

        # Create Normal User
        if not security.datastore.find_user(email="user@user.com"):
            security.datastore.create_user(
                email="user@user.com",
                username="user01",
                password=hash_password("user123"),
                roles=['user']
            )

        db.session.commit()
    except Exception as e:
        print(f"Warning: Could not initialize roles and users: {e}")
        # This is expected if migrations haven't been run yet
        db.session.rollback()


