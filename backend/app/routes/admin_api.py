from flask import request, jsonify, current_app
from flask_security import auth_required, roles_required, current_user
from flask_restx import Namespace, Resource, fields
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from datetime import time

from ..models import ParkingLot, ParkingSpot, Reservation, User, Role, Vehicle, Payment, Favorite
from .. import db

admin_ns = Namespace('admin', description='Admin related operations')

# ===== Schemas =====
lot_model = admin_ns.model('ParkingLot', {
    'prime_location_name': fields.String(required=True),
    'address': fields.String(required=True),
    'pincode': fields.String(required=True),
    'price': fields.Float(required=True),
    'number_of_spots': fields.Integer(required=True)
})

spot_model = admin_ns.model('ParkingSpot', {
    'lot_id': fields.Integer(required=True),
    'spot_number': fields.String(required=True),
    'status': fields.String(required=False, default='A')
})

# ===== Routes =====

@admin_ns.route('/search')
class AdminSearch(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Search functionality for admin"""
        query = request.args.get('query', '').strip()
        
        if not query:
            return {"message": "No search query provided"}, 400
        
        # Search across multiple entities
        results = {
            'users': [],
            'parking_lots': [],
            'reservations': []
        }
        
        # Search users
        users = User.query.filter(
            db.or_(
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.username.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        results['users'] = [{
            'id': user.id,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'email': user.email,
            'username': user.username,
            'active': user.active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in users]
        
        # Search parking lots
        lots = ParkingLot.query.filter(
            ParkingLot.prime_location_name.ilike(f'%{query}%')
        ).limit(10).all()
        
        results['parking_lots'] = [{
            'id': lot.id,
            'name': lot.prime_location_name,
            'address': lot.address,
            'price': lot.price,
            'total_spots': lot.number_of_spots,
            'available_spots': ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        } for lot in lots]
        
        # Search reservations by ID
        reservations = []
        if query.isdigit():
            reservations = Reservation.query.filter(
                Reservation.id == int(query)
            ).limit(10).all()
        
        results['reservations'] = [{
            'id': r.id,
            'user_id': r.user_id,
            'spot_id': r.spot_id,
            'start': r.parking_timestamp.isoformat() if r.parking_timestamp else None,
            'end': r.leaving_timestamp.isoformat() if r.leaving_timestamp else None,
            'cost': r.parking_cost
        } for r in reservations]
        
        return {
            'query': query,
            'results': results,
            'total_found': sum(len(v) for v in results.values())
        }


@admin_ns.route('/auth/check')
class AdminAuthCheck(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Lightweight endpoint for admin role verification"""
        return {
            "status": "ok",
            "role": "admin",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@admin_ns.route('/users')
class AdminUsers(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get all users for admin management"""
        users = User.query.all()
        
        data = []
        for user in users:
            user_data = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "active": user.active,
                "is_flagged": user.is_flagged,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "roles": [{"name": role.name, "description": role.description} for role in user.roles]
            }
            data.append(user_data)
        
        return data
    
    @admin_ns.expect(admin_ns.model('CreateUser', {
        'email': fields.String(required=True, description='User email'),
        'username': fields.String(required=True, description='Username'),
        'password': fields.String(required=True, description='Password'),
        'first_name': fields.String(description='First name'),
        'last_name': fields.String(description='Last name'),
        'roles': fields.List(fields.String(), description='List of role names')
    }))
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Create a new user"""
        data = request.get_json()
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == data['email']) | (User.username == data['username'])
        ).first()
        
        if existing_user:
            return {"error": "User with this email or username already exists"}, 400
        
        try:
            from flask_security.utils import hash_password
            
            # Create user
            user_datastore = current_app.extensions['security'].datastore
            user = user_datastore.create_user(
                email=data['email'],
                username=data['username'],
                password=hash_password(data['password']),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                active=True,
                fs_uniquifier=str(__import__('uuid').uuid4())
            )
            
            # Assign roles
            role_names = data.get('roles', ['user'])
            for role_name in role_names:
                role = Role.query.filter_by(name=role_name).first()
                if role:
                    user_datastore.add_role_to_user(user, role)
            
            db.session.commit()
            
            return {
                "message": "User created successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "roles": [role.name for role in user.roles]
                }
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to create user: {str(e)}"}, 500


@admin_ns.route('/users/<int:user_id>')
class AdminUserDetail(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, user_id):
        """Get specific user details"""
        user = User.query.get_or_404(user_id)
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "active": user.active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "roles": [{"name": role.name, "description": role.description} for role in user.roles],
            "total_reservations": Reservation.query.filter_by(user_id=user.id).count(),
            "total_vehicles": Vehicle.query.filter_by(user_id=user.id).count()
        }
    
    @admin_ns.expect(admin_ns.model('UpdateUser', {
        'email': fields.String(description='User email'),
        'username': fields.String(description='Username'),
        'first_name': fields.String(description='First name'),
        'last_name': fields.String(description='Last name'),
        'active': fields.Boolean(description='User active status'),
        'roles': fields.List(fields.String(), description='List of role names')
    }))
    @auth_required('token')
    @roles_required('admin')
    def put(self, user_id):
        """Update user details"""
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        try:
            # Update basic fields
            if 'email' in data:
                # Check if email is already taken by another user
                existing = User.query.filter(User.email == data['email'], User.id != user_id).first()
                if existing:
                    return {"error": "Email already taken by another user"}, 400
                user.email = data['email']
            
            if 'username' in data:
                # Check if username is already taken by another user
                existing = User.query.filter(User.username == data['username'], User.id != user_id).first()
                if existing:
                    return {"error": "Username already taken by another user"}, 400
                user.username = data['username']
            
            if 'first_name' in data:
                user.first_name = data['first_name']
            
            if 'last_name' in data:
                user.last_name = data['last_name']
            
            if 'active' in data:
                user.active = data['active']
            
            # Update roles if provided
            if 'roles' in data:
                user_datastore = current_app.extensions['security'].datastore
                
                # Clear existing roles
                user.roles.clear()
                
                # Add new roles
                for role_name in data['roles']:
                    role = Role.query.filter_by(name=role_name).first()
                    if role:
                        user_datastore.add_role_to_user(user, role)
            
            db.session.commit()
            
            return {
                "message": "User updated successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "active": user.active,
                    "roles": [role.name for role in user.roles]
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to update user: {str(e)}"}, 500
    
    @auth_required('token')
    @roles_required('admin')
    def delete(self, user_id):
        """Delete a user (admin only)"""
        user = User.query.get_or_404(user_id)

        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return {"error": "Cannot delete your own account"}, 400

        try:
            # Check for active reservations and release the spot if found
            active_reservation = Reservation.query.filter_by(
                user_id=user_id,
                leaving_timestamp=None
            ).first()

            if active_reservation:
                spot = ParkingSpot.query.get(active_reservation.spot_id)
                if spot:
                    spot.status = 'A'  # Set status to Available
                    db.session.add(spot)

            # The database models are now configured with cascading deletes,
            # so manual deletion of related records is no longer necessary.

            # Remove user roles
            user.roles.clear()

            # Delete the user
            db.session.delete(user)
            db.session.commit()

            return {"message": "User deleted successfully"}

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to delete user: {str(e)}"}, 500


@admin_ns.route('/parking_lots')
class AdminParkingLots(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get all parking lots for admin management"""
        lots = ParkingLot.query.all()
        
        data = []
        for lot in lots:
            available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
            
            
            is_24x7 = (
                lot.available_from == time(0, 0) and 
                lot.available_to == time(0, 0)
            )
            
            data.append({
                "id": lot.id,
                "location": lot.prime_location_name,
                "address": lot.address,
                "pincode": lot.pincode,
                "price": lot.price,
                "total_spots": lot.number_of_spots,
                "available_spots": available_spots,
                "occupied_spots": occupied_spots,
                "is_24x7": is_24x7,
                "available_from": lot.available_from.strftime('%H:%M') if lot.available_from else None,
                "available_to": lot.available_to.strftime('%H:%M') if lot.available_to else None,
                "is_active": lot.is_active
            })
        
        return data
    
    @admin_ns.expect(admin_ns.model('CreateParkingLot', {
        'prime_location_name': fields.String(required=True, description='Parking lot name'),
        'address': fields.String(required=True, description='Address'),
        'pincode': fields.String(required=True, description='PIN code'),
        'price': fields.Float(required=True, description='Price per hour'),
        'number_of_spots': fields.Integer(required=True, description='Number of parking spots')
    }))
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Create a new parking lot"""
        data = request.get_json()
        
        try:
            from datetime import datetime
            
            # Create parking lot
            lot = ParkingLot(
                prime_location_name=data['prime_location_name'],
                address=data['address'],
                pincode=data['pincode'],
                price=data['price'],
                number_of_spots=data['number_of_spots']
            )
            
            # If both values are supplied
            if 'available_from' in data and 'available_to' in data:
                if data['available_from'] == '00:00' and data['available_to'] == '00:00':
                    # 24x7 shorthand
                    lot.available_from = time(0, 0)
                    lot.available_to = time(0, 0)
                else:
                    if data['available_from']:
                        lot.available_from = datetime.strptime(data['available_from'], '%H:%M').time()
                    if data['available_to']:
                        lot.available_to = datetime.strptime(data['available_to'], '%H:%M').time()

            db.session.add(lot)
            db.session.flush()  # Get the lot ID
            
            # Create parking spots
            for i in range(data['number_of_spots']):
                spot = ParkingSpot(
                    lot_id=lot.id,
                    spot_number=i + 1,
                    status='A'  # Available
                )
                db.session.add(spot)
            
            db.session.commit()
            
            return {
                "message": "Parking lot created successfully",
                "lot": {
                    "id": lot.id,
                    "location": lot.prime_location_name,
                    "address": lot.address,
                    "total_spots": lot.number_of_spots
                }
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to create parking lot: {str(e)}"}, 500


@admin_ns.route('/parking_lots/<int:lot_id>')
class AdminParkingLotDetail(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, lot_id):
        """Get specific parking lot details"""
        lot = ParkingLot.query.get_or_404(lot_id)
        available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        
        return {
            "id": lot.id,
            "location": lot.prime_location_name,
            "address": lot.address,
            "pincode": lot.pincode,
            "price": lot.price,
            "total_spots": lot.number_of_spots,
            "available_spots": available_spots,
            "occupied_spots": occupied_spots,
            "is_active": lot.is_active
        }
    
    @admin_ns.expect(admin_ns.model('UpdateParkingLot', {
        'prime_location_name': fields.String(description='Parking lot name'),
        'address': fields.String(description='Address'),
        'pincode': fields.String(description='PIN code'),
        'price': fields.Float(description='Price per hour'),
        'number_of_spots': fields.Integer(description='Number of parking spots')
    }))
    @auth_required('token')
    @roles_required('admin')
    def put(self, lot_id):
        """Update parking lot details"""
        lot = ParkingLot.query.get_or_404(lot_id)
        data = request.get_json()
        
        try:
            from datetime import datetime
            
            # Update basic fields
            if 'prime_location_name' in data:
                lot.prime_location_name = data['prime_location_name']
            if 'address' in data:
                lot.address = data['address']
            if 'pincode' in data:
                lot.pincode = data['pincode']
            if 'price' in data:
                lot.price = data['price']
            
            # Update operating hours if provided
            if 'available_from' in data and data['available_from']:
                lot.available_from = datetime.strptime(data['available_from'], '%H:%M').time()
            if 'available_to' in data and data['available_to']:
                lot.available_to = datetime.strptime(data['available_to'], '%H:%M').time()
            
            # Handle spot count changes
            if 'number_of_spots' in data:
                new_count = data['number_of_spots']
                current_spots = ParkingSpot.query.filter_by(lot_id=lot_id).count()
                
                if new_count > current_spots:
                    # Add new spots
                    for i in range(current_spots + 1, new_count + 1):
                        spot = ParkingSpot(
                            lot_id=lot_id,
                            spot_number=i,
                            status='A'
                        )
                        db.session.add(spot)
                elif new_count < current_spots:
                    # Remove spots (only available ones)
                    spots_to_remove = ParkingSpot.query.filter_by(
                        lot_id=lot_id, status='A'
                    ).order_by(ParkingSpot.spot_number.desc()).limit(current_spots - new_count).all()
                    
                    if len(spots_to_remove) < (current_spots - new_count):
                        return {"error": "Cannot remove spots that are occupied"}, 400
                    
                    for spot in spots_to_remove:
                        db.session.delete(spot)
                
                lot.number_of_spots = new_count
            
            db.session.commit()
            
            return {
                "message": "Parking lot updated successfully",
                "lot": {
                    "id": lot.id,
                    "location": lot.prime_location_name,
                    "address": lot.address,
                    "total_spots": lot.number_of_spots
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to update parking lot: {str(e)}"}, 500
    
    @auth_required('token')
    @roles_required('admin')
    def delete(self, lot_id):
        """Delete a parking lot"""
        lot = ParkingLot.query.get_or_404(lot_id)
        
        try:
            # Check if any spots are occupied
            occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').count()
            if occupied_spots > 0:
                return {"error": f"Cannot delete parking lot with {occupied_spots} occupied spots"}, 400
            
            # Check for active reservations
            active_reservations = db.session.query(Reservation).join(ParkingSpot).filter(
                ParkingSpot.lot_id == lot_id,
                Reservation.leaving_timestamp.is_(None)
            ).count()
            
            if active_reservations > 0:
                return {"error": f"Cannot delete parking lot with {active_reservations} active reservations"}, 400
            
            # The database models are now configured with cascading deletes,
            # so manual deletion of related records is no longer necessary.
            
            # Delete the parking lot
            db.session.delete(lot)
            db.session.commit()
            
            return {"message": "Parking lot deleted successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to delete parking lot: {str(e)}"}, 500


@admin_ns.route('/parking_lots/<int:lot_id>/toggle')
class AdminParkingLotToggle(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self, lot_id):
        """Toggle parking lot active status"""
        lot = ParkingLot.query.get_or_404(lot_id)
        
        try:
            # Toggle the is_active status
            lot.is_active = not lot.is_active
            db.session.commit()
            
            status_text = "activated" if lot.is_active else "deactivated"
            
            return {
                "message": f"Parking lot {status_text} successfully",
                "lot": {
                    "id": lot.id,
                    "location": lot.prime_location_name,
                    "is_active": lot.is_active
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to toggle parking lot status: {str(e)}"}, 500


@admin_ns.route('/users/export')
class AdminExportUsers(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        try:
            from backend.app.tasks.tasks import export_admin_users_csv

            data = request.get_json() or {}
            admin_email = data.get('admin_email') or current_user.email

            celery_app = current_app.celery
            result = export_admin_users_csv.delay(admin_email)

            response = {
                "task_id": getattr(result, 'id', None),
                "message": f"User data export started. You will receive an email at {admin_email} when the CSV is ready.",
                "status": "started",
                "admin_email": admin_email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if celery_app.conf.task_always_eager:
                try:
                    payload = result.get(timeout=5)
                    response.update({
                        "task_status": payload.get("status"),
                        "task_message": payload.get("message"),
                        "email_sent": payload.get("email_sent"),
                        "email_message": payload.get("email_message"),
                        "download_url": payload.get("download_url"),
                        "filename": payload.get("filename")
                    })
                    if not payload.get("email_sent"):
                        response["status"] = payload.get("status", "warning")
                        response["message"] = payload.get("message")
                except Exception as eager_error:
                    response["status"] = "error"
                    response["message"] = f"Export generated but status unknown: {str(eager_error)}"

            return response

        except Exception as e:
            return {"error": f"Failed to start export: {str(e)}"}, 500


@admin_ns.route('/reservations/export')
class AdminExportReservations(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        try:
            from backend.app.tasks.tasks import export_admin_reservations_csv

            data = request.get_json() or {}
            admin_email = data.get('admin_email') or current_user.email
            status_filter = data.get('status') or 'all'

            celery_app = current_app.celery
            result = export_admin_reservations_csv.delay(admin_email, status_filter)

            response = {
                "task_id": getattr(result, 'id', None),
                "message": f"Reservation export started. You will receive an email at {admin_email} when the CSV is ready.",
                "status": "started",
                "admin_email": admin_email,
                "filter": status_filter,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if celery_app.conf.task_always_eager:
                try:
                    payload = result.get(timeout=5)
                    response.update({
                        "task_status": payload.get("status"),
                        "task_message": payload.get("message"),
                        "email_sent": payload.get("email_sent"),
                        "email_message": payload.get("email_message"),
                        "download_url": payload.get("download_url"),
                        "filename": payload.get("filename"),
                        "total_records": payload.get("total_records")
                    })
                    if not payload.get("email_sent"):
                        response["status"] = payload.get("status", "warning")
                        response["message"] = payload.get("message")
                except Exception as eager_error:
                    response["status"] = "error"
                    response["message"] = f"Export generated but status unknown: {str(eager_error)}"

            return response

        except Exception as e:
            return {"error": f"Failed to start export: {str(e)}"}, 500


@admin_ns.route('/users/flagged')
class AdminFlaggedUsers(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get all flagged users"""
        try:
            flagged_users = User.query.filter_by(is_flagged=True).all()
            
            data = []
            for user in flagged_users:
                user_data = {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "active": user.active,
                    "is_flagged": user.is_flagged,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "roles": [{"name": role.name, "description": role.description} for role in user.roles],
                    "total_reservations": Reservation.query.filter_by(user_id=user.id).count(),
                    "total_vehicles": Vehicle.query.filter_by(user_id=user.id).count()
                }
                data.append(user_data)
            
            return {"flagged_users": data, "total": len(data)}
            
        except Exception as e:
            return {"error": f"Failed to fetch flagged users: {str(e)}"}, 500


@admin_ns.route('/users/<int:user_id>/flag')
class AdminUserFlag(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self, user_id):
        """Flag a user"""
        user = User.query.get_or_404(user_id)
        
        try:
            user.is_flagged = True
            db.session.commit()
            
            return {
                "message": f"User {user.username} has been flagged successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_flagged": user.is_flagged
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to flag user: {str(e)}"}, 500
    
    @auth_required('token')
    @roles_required('admin')
    def delete(self, user_id):
        """Unflag a user"""
        user = User.query.get_or_404(user_id)
        
        try:
            user.is_flagged = False
            db.session.commit()
            
            return {
                "message": f"User {user.username} has been unflagged successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_flagged": user.is_flagged
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to unflag user: {str(e)}"}, 500


@admin_ns.route('/users/<int:user_id>/toggle-active')
class AdminUserToggleActive(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self, user_id):
        """Toggle user active status"""
        user = User.query.get_or_404(user_id)
        
        try:
            user.active = not user.active
            db.session.commit()
            
            status_text = "activated" if user.active else "deactivated"
            
            return {
                "message": f"User {user.username} has been {status_text} successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "active": user.active
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to toggle user status: {str(e)}"}, 500


@admin_ns.route('/users/<int:user_id>/details')
class AdminUserDetails(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, user_id):
        """Get detailed user information including vehicles and reservations"""
        user = User.query.get_or_404(user_id)
        
        try:
            # Get user's vehicles
            vehicles = Vehicle.query.filter_by(user_id=user_id).all()
            vehicles_data = [{
                "id": vehicle.id,
                "license_plate": vehicle.vehicle_number,
                "model": vehicle.vehicle_name,
                "color": getattr(vehicle, 'color', None),
                "created_at": getattr(vehicle, 'created_at', None)
            } for vehicle in vehicles]
            
            # Get user's reservations (last 20)
            reservations = Reservation.query.filter_by(user_id=user_id).order_by(
                Reservation.booking_timestamp.desc()
            ).limit(20).all()
            
            reservations_data = []
            for reservation in reservations:
                spot = ParkingSpot.query.get(reservation.spot_id)
                lot = ParkingLot.query.get(spot.lot_id) if spot else None
                
                reservations_data.append({
                    "id": reservation.id,
                    "booking_id": reservation.booking_id,
                    "status": reservation.status,
                    "parking_lot": lot.prime_location_name if lot else "Unknown",
                    "spot_number": spot.spot_number if spot else "Unknown",
                    "booking_timestamp": reservation.booking_timestamp.isoformat() if reservation.booking_timestamp else None,
                    "parking_timestamp": reservation.parking_timestamp.isoformat() if reservation.parking_timestamp else None,
                    "leaving_timestamp": reservation.leaving_timestamp.isoformat() if reservation.leaving_timestamp else None,
                    "parking_cost": reservation.parking_cost,
                    "duration_hours": None if not reservation.leaving_timestamp or not reservation.parking_timestamp else 
                        round((reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600, 2)
                })
            
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "active": user.active,
                    "is_flagged": user.is_flagged,
                    "phone_number": user.phone_number,
                    "address": user.address,
                    "pincode": user.pincode,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "roles": [{"name": role.name, "description": role.description} for role in user.roles]
                },
                "vehicles": vehicles_data,
                "reservations": reservations_data,
                "statistics": {
                    "total_reservations": len(reservations_data),
                    "total_vehicles": len(vehicles_data),
                    "active_reservations": len([r for r in reservations_data if r["status"] in ["Confirmed", "Parked"]])
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch user details: {str(e)}"}, 500


@admin_ns.route('/reservations')
class AdminReservations(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get all reservations for admin management"""
        try:
            # Get query parameters for pagination and filtering
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            status = request.args.get('status', None)  # 'active', 'completed', 'all'
            
            # Base query
            query = db.session.query(Reservation)
            
            # Apply status filter
            if status == 'active':
                query = query.filter(Reservation.status.in_(['Confirmed', 'Parked']))
            elif status == 'completed':
                query = query.filter(Reservation.status.in_(['Parked Out', 'Cancelled', 'Rejected']))
            
            # Order by most recent first
            query = query.order_by(Reservation.booking_timestamp.desc())
            
            # Get total count before pagination
            total_count = query.count()
            
            # Get paginated results
            reservations = query.limit(per_page).offset((page - 1) * per_page).all()
            
            data = []
            for reservation in reservations:
                user = User.query.get(reservation.user_id)
                spot = ParkingSpot.query.get(reservation.spot_id)
                lot = ParkingLot.query.get(spot.lot_id) if spot else None
                vehicle = Vehicle.query.get(reservation.vehicle_id) if reservation.vehicle_id else None
                
                data.append({
                    "id": reservation.id,
                    "booking_id": reservation.booking_id,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    },
                    "parking_lot": {
                        "id": lot.id if lot else None,
                        "name": lot.prime_location_name if lot else "Unknown",
                        "address": lot.address if lot else "Unknown"
                    },
                    "spot": {
                        "id": spot.id if spot else None,
                        "spot_number": spot.spot_number if spot else "Unknown"
                    },
                    "vehicle": {
                        "license_plate": vehicle.vehicle_number if vehicle else "Unknown",
                        "model": vehicle.vehicle_name if vehicle else "Unknown"
                    } if vehicle else None,
                    "booking_timestamp": reservation.booking_timestamp.isoformat() if reservation.booking_timestamp else None,
                    "expected_arrival": reservation.expected_arrival.isoformat() if reservation.expected_arrival else None,
                    "expected_departure": reservation.expected_departure.isoformat() if reservation.expected_departure else None,
                    "parking_timestamp": reservation.parking_timestamp.isoformat() if reservation.parking_timestamp else None,
                    "leaving_timestamp": reservation.leaving_timestamp.isoformat() if reservation.leaving_timestamp else None,
                    "parking_cost": reservation.parking_cost,
                    "status": reservation.status,
                    "duration_hours": None if not reservation.leaving_timestamp or not reservation.parking_timestamp else 
                        round((reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600, 2)
                })
            
            return {
                "reservations": data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_count,
                    "pages": (total_count + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch reservations: {str(e)}"}, 500


@admin_ns.route('/analytics/dashboard')
class AdminAnalytics(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get admin analytics dashboard data"""
        # Overview statistics
        total_lots = ParkingLot.query.count()
        total_spots = db.session.query(func.sum(ParkingLot.number_of_spots)).scalar() or 0
        occupied_spots = ParkingSpot.query.filter_by(status='O').count()
        occupancy_rate = round((occupied_spots / total_spots * 100), 1) if total_spots > 0 else 0
        total_users = User.query.count()
        
        # Net earnings from completed reservations
        net_earnings = db.session.query(func.sum(Reservation.parking_cost)).filter(
            Reservation.status == 'Parked Out'
        ).scalar() or 0
        
        overview = {
            "total_lots": total_lots,
            "total_spots": total_spots,
            "occupancy_rate": occupancy_rate,
            "total_users": total_users,
            "net_earnings": round(net_earnings, 2)
        }
        
        # Revenue chart (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        revenue_data = db.session.query(
            func.date(Reservation.leaving_timestamp).label('date'),
            func.sum(Reservation.parking_cost).label('revenue')
        ).filter(
            Reservation.leaving_timestamp >= thirty_days_ago,
            Reservation.parking_cost.isnot(None)
        ).group_by(func.date(Reservation.leaving_timestamp)).all()
        
        revenue_chart = [
            {"date": str(item.date), "revenue": float(item.revenue or 0)}
            for item in revenue_data
        ]
        
        # Lot utilization
        lot_utilization = []
        lots = ParkingLot.query.all()
        for lot in lots:
            occupied = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
            utilization_rate = round((occupied / lot.number_of_spots * 100), 1) if lot.number_of_spots > 0 else 0
            lot_utilization.append({
                "name": lot.prime_location_name,
                "utilization_rate": utilization_rate
            })
        
        # Daily activity (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        activity_data = db.session.query(
            func.date(Reservation.parking_timestamp).label('date'),
            func.count(Reservation.id).label('total_bookings')
        ).filter(
            Reservation.parking_timestamp >= seven_days_ago
        ).group_by(func.date(Reservation.parking_timestamp)).all()
        
        daily_activity = [
            {"date": str(item.date), "total_bookings": item.total_bookings}
            for item in activity_data
        ]
        
        # Top users (last 30 days)
        top_users_data = db.session.query(
            User.username,
            User.email,
            func.count(Reservation.id).label('total_bookings'),
            func.sum(Reservation.parking_cost).label('total_spent')
        ).join(Reservation).filter(
            Reservation.parking_timestamp >= thirty_days_ago
        ).group_by(User.id).order_by(func.count(Reservation.id).desc()).limit(10).all()
        
        top_users = [
            {
                "username": item.username,
                "email": item.email,
                "total_bookings": item.total_bookings,
                "total_spent": float(item.total_spent or 0)
            }
            for item in top_users_data
        ]
        
        # Peak hours data (today's hourly distribution)
        today = datetime.now(timezone.utc).date()
        peak_hours = [0] * 24  # Initialize 24 hours
        
        # Get all active reservations for today
        today_reservations = Reservation.query.filter(
            func.date(Reservation.parking_timestamp) == today
        ).all()
        
        for reservation in today_reservations:
            if reservation.parking_timestamp:
                hour = reservation.parking_timestamp.hour
                peak_hours[hour] += 1
        
        # Duration distribution (last 7 days)
        duration_buckets = {
            '<1 hour': 0,
            '1-2 hours': 0,
            '2-4 hours': 0,
            '4-8 hours': 0,
            '8+ hours': 0
        }
        
        completed_reservations = Reservation.query.filter(
            Reservation.leaving_timestamp.isnot(None),
            Reservation.leaving_timestamp >= seven_days_ago
        ).all()
        
        for reservation in completed_reservations:
            if reservation.parking_timestamp and reservation.leaving_timestamp:
                duration_hours = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600
                
                if duration_hours < 1:
                    duration_buckets['<1 hour'] += 1
                elif duration_hours < 2:
                    duration_buckets['1-2 hours'] += 1
                elif duration_hours < 4:
                    duration_buckets['2-4 hours'] += 1
                elif duration_hours < 8:
                    duration_buckets['4-8 hours'] += 1
                else:
                    duration_buckets['8+ hours'] += 1
        
        duration_distribution = list(duration_buckets.values())
        
        # Status distribution
        status_counts = db.session.query(
            Reservation.status,
            func.count(Reservation.id).label('count')
        ).group_by(Reservation.status).all()
        
        status_map = {
            'Pending': 0,
            'Confirmed': 0,
            'Parked': 0,
            'Parked Out': 0,
            'Cancelled/Rejected': 0
        }
        
        for status, count in status_counts:
            if status in ['Pending']:
                status_map['Pending'] += count
            elif status in ['Confirmed']:
                status_map['Confirmed'] += count
            elif status in ['Parked', 'Active']:
                status_map['Parked'] += count
            elif status in ['Parked Out', 'Completed']:
                status_map['Parked Out'] += count
            elif status in ['Cancelled', 'Rejected']:
                status_map['Cancelled/Rejected'] += count
        
        status_distribution = list(status_map.values())
        
        # Calculate available spots for overview
        available_spots = total_spots - occupied_spots
        overview['available_spots'] = available_spots
        
        return {
            "overview": overview,
            "revenue_chart": revenue_chart,
            "lot_utilization": lot_utilization,
            "daily_activity": daily_activity,
            "top_users": top_users,
            "peak_hours": peak_hours,
            "duration_distribution": duration_distribution,
            "status_distribution": status_distribution
        }


@admin_ns.route('/parking_lots/visualization')
class AllParkingLotsVisualization(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get parking lot visualization data for all lots"""
        try:
            lots = ParkingLot.query.all()
            
            visualization_data = []
            for lot in lots:
                spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.id).all()
                
                spot_data = []
                for index, spot in enumerate(spots, 1):  # Create spot numbers starting from 1
                    spot_info = {
                        "id": spot.id,
                        "spot_number": index,  # Use index as spot number
                        "status": spot.status,
                        "lot_id": spot.lot_id
                    }
                    
                    # Add reservation info if occupied
                    if spot.status == 'O':
                        active_reservation = Reservation.query.filter(
                            Reservation.spot_id == spot.id,
                            Reservation.leaving_timestamp == None,
                            Reservation.status.notin_(['Cancelled', 'Rejected'])
                        ).first()
                        if active_reservation:
                            spot_info["reservation"] = {
                                "user_id": active_reservation.user_id,
                                "start_time": active_reservation.parking_timestamp.isoformat() if active_reservation.parking_timestamp else None
                            }
                    
                    spot_data.append(spot_info)
                
                lot_info = {
                    "id": lot.id,
                    "name": lot.prime_location_name,
                    "address": lot.address,
                    "totalSpots": lot.number_of_spots,  # Frontend expects camelCase
                    "occupiedSpots": len([s for s in spots if s.status == 'O']),  # Frontend expects camelCase
                    "availableSpots": len([s for s in spots if s.status == 'A']),  # Frontend expects camelCase
                    "isActive": lot.is_active,  # Frontend expects camelCase
                    "spots": spot_data
                }
                
                visualization_data.append(lot_info)
            
            return visualization_data
            
        except Exception as e:
            return {"error": f"Failed to fetch visualization data: {str(e)}"}, 500


@admin_ns.route('/dashboard')
class AdminDashboard(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        lots = ParkingLot.query.all()
        data = [{
            "id": lot.id,
            "location": lot.prime_location_name,
            "address": lot.address,
            "pincode": lot.pincode,
            "price": lot.price,
            "total_spots": lot.number_of_spots
        } for lot in lots]
        return data

    @admin_ns.expect([lot_model])
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        data = request.get_json()
        lots = data if isinstance(data, list) else [data]
        
        for lot in lots:
            lot_data = ParkingLot(
                prime_location_name=lot['prime_location_name'],
                address=lot['address'],
                pincode=lot['pincode'],
                price=float(lot['price']),
                number_of_spots=int(lot['number_of_spots'])
            )
            db.session.add(lot_data)
            db.session.flush()
            
            for _ in range(lot['number_of_spots']):
                spot = ParkingSpot(lot_id=lot_data.id, status='A')
                db.session.add(spot)
            
        db.session.commit()
        return {"message": f"{len(lots)} parking lots created"}, 201


@admin_ns.route('/parking_lots/<int:lot_id>/spots/<int:spot_id>')
class ParkingSpotStatus(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, lot_id, spot_id):
        spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
        if not spot:
            return {"error": "Spot not found in specified parking lot"}, 404
        return {
            "id": spot.id,
            "lot_id": spot.lot_id,
            "status": spot.status
        }

    @auth_required('token')
    @roles_required('admin')
    def put(self, lot_id, spot_id):
        data = request.get_json()
        spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
        if not spot:
            return {"error": "Spot not found in specified parking lot"}, 404

        new_status = data.get('status')
        if new_status not in ['A', 'X', 'U']:
            return {"error": "Invalid status. Use 'A' for Available, 'X' for Unavailable, or 'U' for Unavailable."}, 400

        if spot.status in ['B', 'P']:
            return {"error": f"Cannot change status while spot is '{spot.status}'."}, 400

        spot.status = new_status
        db.session.commit()

        return {"message": f"Spot status updated to '{new_status}'"}


@admin_ns.route('/spots/<int:spot_id>/current-reservation')
class SpotCurrentReservation(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, spot_id):
        """Get current active reservation for a spot"""
        try:
            # Find active reservation for this spot (not cancelled or rejected)
            reservation = Reservation.query.filter(
                Reservation.spot_id == spot_id,
                Reservation.leaving_timestamp == None,
                Reservation.status.notin_(['Cancelled', 'Rejected'])
            ).first()
            
            if not reservation:
                return {"error": "No active reservation found for this spot"}, 404
            
            # Get user and vehicle details
            user = User.query.get(reservation.user_id)
            vehicle = Vehicle.query.get(reservation.vehicle_id) if reservation.vehicle_id else None
            
            # Calculate current cost
            current_cost = 0
            if reservation.parking_timestamp:
                try:
                    # Use local time (IST) for both current time and parking time
                    parking_time = reservation.parking_timestamp
                    current_time = datetime.now()
                    
                    duration_minutes = (current_time - parking_time).total_seconds() / 60
                    parking_lot = ParkingLot.query.get(ParkingSpot.query.get(spot_id).lot_id)
                    current_cost = round((duration_minutes / 60) * parking_lot.price, 2) if parking_lot else 0
                except Exception as e:
                    print(f"Error calculating cost: {str(e)}")
                    current_cost = 0
            
            # Format vehicle info
            vehicle_info = "N/A"
            if vehicle:
                vehicle_info = f"{vehicle.vehicle_name}"
                if vehicle.color:
                    vehicle_info += f" ({vehicle.color})"
            
            # Format timestamps (naive datetimes, treat as IST)
            parking_ts = reservation.parking_timestamp.isoformat() if reservation.parking_timestamp else None
            booking_ts = reservation.booking_timestamp.isoformat() if reservation.booking_timestamp else None
            expected_arr = reservation.expected_arrival.isoformat() if reservation.expected_arrival else None
            expected_dep = reservation.expected_departure.isoformat() if reservation.expected_departure else None
            
            return {
                "id": reservation.id,
                "booking_id": reservation.booking_id,
                "username": user.username if user else "Unknown",
                "user_name": f"{user.first_name} {user.last_name}" if user and user.first_name else user.username if user else "Unknown",
                "email": user.email if user else "Unknown",
                "vehicle_plate": vehicle.vehicle_number if vehicle else "Unknown",
                "vehicle_model": vehicle_info,
                "parking_timestamp": parking_ts,
                "booking_timestamp": booking_ts,
                "expected_arrival": expected_arr,
                "expected_departure": expected_dep,
                "status": reservation.status,
                "parking_cost": current_cost
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch reservation details: {str(e)}"}, 500


@admin_ns.route('/spots/<int:spot_id>/upcoming-reservations')
class SpotUpcomingReservations(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, spot_id):
        """Get upcoming reservations for a spot"""
        try:
            # Find all active reservations for this spot (not yet completed)
            # This includes Confirmed, Pending, and any other active statuses
            reservations = Reservation.query.filter(
                Reservation.spot_id == spot_id,
                Reservation.leaving_timestamp.is_(None),
                Reservation.status.notin_(['Completed', 'Cancelled', 'Rejected', 'Parked Out'])
            ).order_by(Reservation.booking_timestamp.desc()).limit(5).all()
            
            result = []
            for reservation in reservations:
                user = User.query.get(reservation.user_id)
                vehicle = Vehicle.query.get(reservation.vehicle_id) if reservation.vehicle_id else None
                
                # Format vehicle info
                vehicle_info = "N/A"
                if vehicle:
                    vehicle_info = f"{vehicle.vehicle_name}"
                    if vehicle.color:
                        vehicle_info += f" ({vehicle.color})"
                
                # Format timestamps (naive datetimes, treat as IST)
                booking_ts = reservation.booking_timestamp.isoformat() if reservation.booking_timestamp else None
                expected_arr = reservation.expected_arrival.isoformat() if reservation.expected_arrival else None
                expected_dep = reservation.expected_departure.isoformat() if reservation.expected_departure else None
                
                result.append({
                    "id": reservation.id,
                    "booking_id": reservation.booking_id,
                    "username": user.username if user else "Unknown",
                    "user_name": f"{user.first_name} {user.last_name}" if user and user.first_name else user.username if user else "Unknown",
                    "email": user.email if user else "Unknown",
                    "vehicle_plate": vehicle.vehicle_number if vehicle else "Unknown",
                    "vehicle_model": vehicle_info,
                    "booking_timestamp": booking_ts,
                    "expected_arrival": expected_arr,
                    "expected_departure": expected_dep,
                    "status": reservation.status
                })
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to fetch upcoming reservations: {str(e)}"}, 500


@admin_ns.route('/spots/<int:spot_id>/force-release')
class ForceReleaseSpot(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self, spot_id):
        """Force release a spot by ending the current reservation"""
        # Find the spot
        spot = ParkingSpot.query.get_or_404(spot_id)
        
        # Find active reservation
        reservation = Reservation.query.filter(
            Reservation.spot_id == spot_id,
            Reservation.leaving_timestamp == None,
            Reservation.status.notin_(['Cancelled', 'Rejected'])
        ).first()
        
        if not reservation:
            return {"error": "No active reservation found for this spot"}, 404
        
        # Get user info for notification
        user = User.query.get(reservation.user_id)
        
        # End the reservation
        reservation.leaving_timestamp = datetime.now()  # Use local time (IST)
        reservation.status = 'Force_Released'
        reservation.cancellation_reason = 'Force released by admin'
        
        # Calculate cost
        duration = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 60
        cost = duration * spot.lot.price / 60
        reservation.parking_cost = round(cost, 2)
        
        # Update spot status
        spot.status = 'A'
        
        db.session.commit()
        
        # Invalidate cache
        from ..utils.cache_hooks import invalidate_user_cache, invalidate_lot_cache, invalidate_admin_cache
        if user:
            invalidate_user_cache(user.id)
        invalidate_lot_cache(spot.lot_id)
        invalidate_admin_cache()
        
        # Send notification to user (optional - can be implemented later)
        # TODO: Send email/notification to user about force release
        # send_force_release_notification(user, reservation, spot)
        
        return {
            "message": f"Spot has been force released. User {user.username if user else 'Unknown'} has been charged ₹{reservation.parking_cost}",
            "reservation_id": reservation.id,
            "cost": reservation.parking_cost,
            "user_notified": False  # Set to True when notification is implemented
        }


@admin_ns.route('/parking_lots/<int:lot_id>/visualization')
class ParkingLotVisualization(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, lot_id):
        """Get detailed visualization data for a parking lot"""
        lot = ParkingLot.query.get_or_404(lot_id)
        spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
        
        # Count occupied spots
        occupied_spots = sum(1 for spot in spots if spot.status == 'O')
        
        # Format spots data
        spots_data = [{
            "id": spot.id,
            "status": spot.status
        } for spot in spots]
        
        return {
            "id": lot.id,
            "name": lot.prime_location_name,
            "address": lot.address,
            "totalSpots": lot.number_of_spots,
            "occupiedSpots": occupied_spots,
            "spots": spots_data
        }




# ===== Data Consistency Management =====

@admin_ns.route('/data/consistency-check')
class DataConsistencyCheck(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Check for data inconsistencies between spots and reservations"""
        from ..utils.data_validation import validate_spot_reservation_consistency
        
        issues = validate_spot_reservation_consistency()
        
        return {
            "total_issues": len(issues),
            "issues": issues,
            "message": "Use POST to auto-fix these issues" if issues else "No issues found"
        }
    
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Fix data inconsistencies automatically"""
        from ..utils.data_validation import fix_spot_reservation_inconsistencies
        
        result = fix_spot_reservation_inconsistencies(auto_fix=True)
        
        return result


# ===== Background Tasks Management =====

@admin_ns.route('/tasks/daily-update')
class TriggerDailyUpdate(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Manually trigger daily update task"""
        try:
            from backend.app.tasks.daily_updates import daily_update
            result = daily_update.delay()
            return {
                "task_id": result.id,
                "message": "Daily update task started",
                "status_url": f"/admin/tasks/status/{result.id}"
            }
        except ImportError:
            return {"error": "Daily update task not available"}, 500


@admin_ns.route('/tasks/monthly-report')
class TriggerMonthlyReport(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Manually trigger monthly report generation"""
        try:
            from backend.app.tasks.monthly_report import monthly_report
            result = monthly_report.delay()
            return {
                "task_id": result.id,
                "message": "Monthly report generation started",
                "status_url": f"/admin/tasks/status/{result.id}"
            }
        except ImportError:
            return {"error": "Monthly report task not available"}, 500


@admin_ns.route('/tasks/csv-export')
class TriggerCSVExport(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        """Manually trigger CSV export"""
        try:
            from backend.app.tasks.csv_report import csv_report
            result = csv_report.delay()
            return {
                "task_id": result.id,
                "message": "CSV export started",
                "status_url": f"/admin/tasks/status/{result.id}"
            }
        except ImportError:
            return {"error": "CSV export task not available"}, 500


@admin_ns.route('/tasks/status/<task_id>')
class TaskStatus(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, task_id):
        """Check status of any background task"""
        try:
            from celery.result import AsyncResult
            result = AsyncResult(task_id)
            
            if result.ready():
                if result.successful():
                    return {
                        "status": "completed",
                        "result": result.result
                    }
                else:
                    return {
                        "status": "failed",
                        "error": str(result.result)
                    }
            else:
                return {
                    "status": "pending",
                    "message": "Task is still running"
                }
        except ImportError:
            return {"error": "Celery not available"}, 500


@admin_ns.route('/tasks/debug')
class DebugTasks(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Debug task system"""
        try:
            import redis
            
            # Get Celery app from Flask app
            celery_app = current_app.celery
            
            debug_info = {
                "broker_url": celery_app.conf.broker_url,
                "result_backend": celery_app.conf.result_backend,
                "registered_tasks": list(celery_app.tasks.keys()),
                "redis_connection": "unknown",
                "celery_connection": "unknown"
            }
            
            # Test Redis connection
            try:
                r = redis.Redis.from_url(celery_app.conf.broker_url)
                r.ping()
                debug_info["redis_connection"] = "success"
            except Exception as e:
                debug_info["redis_connection"] = f"failed: {str(e)}"
            
            # Test Celery connection
            try:
                with celery_app.connection() as conn:
                    conn.ensure_connection(max_retries=1)
                debug_info["celery_connection"] = "success"
            except Exception as e:
                debug_info["celery_connection"] = f"failed: {str(e)}"
            
            return debug_info
            
        except Exception as e:
            return {"error": f"Debug failed: {str(e)}"}, 500

@admin_ns.route('/tasks/trigger/<string:task_name>')
class TriggerAnyTask(Resource):
    @auth_required('token')
    @roles_required('admin')
    def post(self, task_name):
        """Trigger any available task for testing"""
        try:
            # Import all tasks from consolidated tasks module
            from backend.app.tasks.tasks import (
                send_daily_reminders,
                send_monthly_reports,
                export_user_csv,
                cleanup_old_csv_files,
                auto_release_expired_reservations,
                export_admin_users_csv,
                system_health_check,
                daily_update
            )
            
            task_map = {
                'send_daily_reminders': send_daily_reminders,
                'send_monthly_reports': send_monthly_reports,
                'export_user_csv': export_user_csv,
                'cleanup_old_csv_files': cleanup_old_csv_files,
                'auto_release_expired_reservations': auto_release_expired_reservations,
                'export_admin_users_csv': export_admin_users_csv,
                'system_health_check': system_health_check,
                'daily_update': daily_update
            }
            
            # Filter out None values (tasks that couldn't be imported)
            task_map = {k: v for k, v in task_map.items() if v is not None}
            
            instant_tasks = {
                'system_health_check',
                'cleanup_old_csv_files',
                'auto_release_expired_reservations',
                'daily_update'
            }
            
            # Tasks that need admin email parameter
            tasks_needing_email = {
                'export_admin_users_csv'
            }

            if task_name not in task_map:
                return {
                    "error": f"Unknown task: {task_name}",
                    "available_tasks": list(task_map.keys())
                }, 400

            task_func = task_map[task_name]
            
            # Get request data for tasks that need parameters
            request_data = request.get_json(silent=True) or {}
            admin_email = request_data.get('admin_email') or current_user.email

            if task_name in instant_tasks:
                try:
                    result_data = task_func.apply(args=(), kwargs={}).get()
                    return {
                        "status": "completed",
                        "result": result_data,
                        "task_name": task_name,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                except Exception as sync_error:
                    return {
                        "error": f"Task execution failed: {str(sync_error)}",
                        "task_name": task_name
                    }, 500

            # For tasks that need email parameter
            if task_name in tasks_needing_email:
                try:
                    celery_app = current_app.celery
                    result = task_func.delay(admin_email)
                    return {
                        "task_id": result.id,
                        "message": f"{task_name} task started successfully. Email will be sent to {admin_email} when ready.",
                        "status": "started",
                        "admin_email": admin_email,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                except Exception as celery_error:
                    return {
                        "error": f"Failed to trigger Celery task: {str(celery_error)}",
                        "task_name": task_name,
                        "error_type": type(celery_error).__name__
                    }, 500

            # For true background tasks, call with .delay() using the Flask app's Celery instance
            if hasattr(task_func, 'delay'):
                try:
                    # Use the Flask app's Celery instance
                    celery_app = current_app.celery
                    
                    # Trigger the task
                    result = task_func.delay()
                    
                    return {
                        "task_id": result.id,
                        "message": f"{task_name} task started successfully",
                        "status": "started",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                except Exception as celery_error:
                    return {
                        "error": f"Failed to trigger Celery task: {str(celery_error)}",
                        "task_name": task_name,
                        "error_type": type(celery_error).__name__
                    }, 500
            else:
                # For simple functions, call directly
                result = task_func()
                return {
                    "message": f"{task_name} task completed successfully",
                    "status": "completed",
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except ImportError as e:
            return {"error": f"Task module not available: {str(e)}"}, 500
        except Exception as e:
            return {"error": f"Failed to trigger task: {str(e)}"}, 500



@admin_ns.route('/tasks/list')
class ListTasks(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """List all available tasks and their status"""
        try:
            tasks = {
                'csv_report': {
                    'name': 'CSV Report Generation',
                    'description': 'Generate CSV export of all reservations',
                    'type': 'async',
                    'schedule': 'Manual trigger only'
                },
                'monthly_report': {
                    'name': 'Monthly Report',
                    'description': 'Generate and email monthly analytics report',
                    'type': 'async',
                    'schedule': 'Every 10 minutes (testing mode)'
                },
                'daily_update': {
                    'name': 'Daily Maintenance',
                    'description': 'Daily system maintenance and cleanup',
                    'type': 'async',
                    'schedule': 'Every 5 minutes (testing mode)'
                },
                'health_check': {
                    'name': 'System Health Check',
                    'description': 'Check system health and send alerts',
                    'type': 'sync',
                    'schedule': 'Every 2 minutes (testing mode)'
                },
                'cleanup_csv': {
                    'name': 'CSV Cleanup',
                    'description': 'Clean up old CSV export files',
                    'type': 'sync',
                    'schedule': 'Every 15 minutes (testing mode)'
                },
                'user_reminders': {
                    'name': 'User Reminders',
                    'description': 'Send reminder emails to users',
                    'type': 'sync',
                    'schedule': 'Every 3 minutes (testing mode)'
                },
                'auto_release': {
                    'name': 'Auto-release Expired',
                    'description': 'Release expired reservations automatically',
                    'type': 'sync',
                    'schedule': 'Every 7 minutes (testing mode)'
                }
            }
            
            return {
                "tasks": tasks,
                "total_tasks": len(tasks),
                "testing_mode": True,
                "note": "All schedules are reduced for testing purposes"
            }
            
        except Exception as e:
            return {"error": f"Failed to list tasks: {str(e)}"}, 500


@admin_ns.route('/tasks/logs')
class TaskLogs(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get recent task execution logs"""
        try:
            from ..utils.task_logger import get_recent_task_logs
            
            limit = request.args.get('limit', 50, type=int)
            logs = get_recent_task_logs(limit=limit)
            
            return {
                "logs": logs,
                "count": len(logs)
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch task logs: {str(e)}"}, 500

    @auth_required('token')
    @roles_required('admin')
    def delete(self):
        """Clear all task execution logs"""
        try:
            from ..utils.task_logger import clear_all_task_logs
            
            cleared_count = clear_all_task_logs()
            
            return {
                "message": f"Successfully cleared {cleared_count} task logs.",
                "count": cleared_count
            }
            
        except Exception as e:
            return {"error": f"Failed to clear task logs: {str(e)}"}, 500



