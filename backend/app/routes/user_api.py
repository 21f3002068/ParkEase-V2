from flask import request, jsonify, current_app
from flask_security import auth_required, roles_required, current_user
from flask_restx import Namespace, Resource, fields
from ..models.ParkingLot import ParkingLot
from ..models.ParkingSpot import ParkingSpot
from ..models.Reservation import Reservation
from ..models.Vehicle import Vehicle
from ..models.User import User
from ..models.Payment import Payment
from ..models.Favorite import Favorite
from sqlalchemy import func
from .. import db
from datetime import datetime, timezone
from flask import jsonify
from ..tasks import export_user_csv, send_monthly_reports
from flask import send_from_directory
from celery.result import AsyncResult

user_ns = Namespace('user', description='User related operations')

# =========================
# Schemas for documentation 
# =========================
vehicle_model = user_ns.model('Vehicle', {
    'vehicle_number': fields.String(required=True),
    'vehicle_name': fields.String(required=True),
    'color': fields.String(required=False),
})

# =========================
# Routes using Resource classes
# =========================

@user_ns.route('/dashboard')
class UserDashboard(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        return {"message": "Welcome to the User Dashboard"}


@user_ns.route('/parking_lots')
class ParkingLotList(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        lots = ParkingLot.query.all()
        data = [{
            "id": lot.id,
            "location": lot.prime_location_name,
            "address": lot.address,
            "pincode": lot.pincode,
            "price": lot.price,
            "total_spots": lot.number_of_spots,
            "available_spots": ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count(),
            "available_from": lot.available_from.strftime('%H:%M') if lot.available_from else None,
            "available_to": lot.available_to.strftime('%H:%M') if lot.available_to else None,
            "is_active": lot.is_active
        } for lot in lots]
        return data


@user_ns.route('/parking_lots/<int:lot_id>')
class ParkingLotDetail(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self, lot_id):
        lot = ParkingLot.query.get_or_404(lot_id)
        return {
            "id": lot.id,
            "location": lot.prime_location_name,
            "address": lot.address,
            "pincode": lot.pincode,
            "price": lot.price,
            "available_spots": ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        }


@user_ns.route('/booking_data/<int:lot_id>')
class BookingData(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self, lot_id):
        user_id = current_user.id
        
        # Get user vehicles
        vehicles = Vehicle.query.filter_by(user_id=user_id).all()
        vehicle_data = [{
            "id": v.id,
            "vehicle_number": v.vehicle_number,
            "vehicle_name": v.vehicle_name,
            "color": v.color
        } for v in vehicles]
        
        # Get lot details
        lot = ParkingLot.query.get_or_404(lot_id)
        available_spots = ParkingSpot.query.filter_by(
            lot_id=lot_id, status='A'
        ).count()
        
        # Note: We don't check for has_active_reservation here anymore
        # Time conflict checking is done in the booking endpoint
        # Users can have multiple bookings as long as times don't overlap
        
        return {
            "lot": {
                "id": lot.id,
                "name": lot.prime_location_name,
                "address": lot.address,
                "available_spots": available_spots,
                "price": lot.price,
                "available_from": lot.available_from.strftime('%H:%M') if lot.available_from else "06:00",
                "available_to": lot.available_to.strftime('%H:%M') if lot.available_to else "22:00"
            },
            "vehicles": vehicle_data,
            "has_vehicles": len(vehicle_data) > 0,
            "has_active_reservation": False  # Always False - conflict checking done at booking time
        }


@user_ns.route('/book/<int:lot_id>')
class BookSpot(Resource):
    @user_ns.expect(user_ns.model('BookingRequest', {
        'vehicle_id': fields.Integer(required=True, description='Vehicle ID'),
        'expected_arrival': fields.String(required=True, description='Expected arrival time (HH:MM format)'),
        'expected_departure': fields.String(required=True, description='Expected departure time (HH:MM format)')
    }))
    @auth_required('token')
    @roles_required('user')
    def post(self, lot_id):
        """Enhanced booking with time slot reservations"""
        from ..utils.booking_utils import enhanced_booking_logic, validate_booking_time_constraints, calculate_booking_cost, get_user_booking_conflicts
        import uuid
        
        user_id = current_user.id
        user = current_user
        data = request.get_json() or {}
        
        # Check if user profile is complete enough for booking
        if not user.first_name or not user.first_name.strip():
            return {"error": "Please complete your profile. First name is required for booking."}, 400
        
        if not user.last_name or not user.last_name.strip():
            return {"error": "Please complete your profile. Last name is required for booking."}, 400
        
        if not user.phone_number or not user.phone_number.strip():
            return {"error": "Please complete your profile. Phone number is required for booking."}, 400
        
        # Check if user has vehicles
        user_vehicles = Vehicle.query.filter_by(user_id=user_id).all()
        if not user_vehicles:
            return {"error": "Please add at least one vehicle before booking."}, 400
        
        # Get parking lot
        parking_lot = ParkingLot.query.get_or_404(lot_id)
        
        if not parking_lot.is_active:
            return {"error": "This parking lot is currently unavailable"}, 400
        
        # Validate selected vehicle
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return {"error": "Please select a vehicle"}, 400
            
        selected_vehicle = Vehicle.query.filter_by(
            id=vehicle_id, user_id=user_id
        ).first()
        if not selected_vehicle:
            return {"error": "Invalid vehicle selection"}, 400
        
        # Parse time inputs
        expected_arrival = data.get('expected_arrival')
        expected_departure = data.get('expected_departure')
        
        if not expected_arrival or not expected_departure:
            return {"error": "Expected arrival and departure times are required"}, 400
        
        try:
            expected_arrival_time = datetime.strptime(expected_arrival, '%H:%M').time()
            expected_departure_time = datetime.strptime(expected_departure, '%H:%M').time()
        except ValueError:
            return {"error": "Invalid time format. Use HH:MM format"}, 400
        
        # Validate time constraints
        time_validation = validate_booking_time_constraints(
            parking_lot, expected_arrival_time, expected_departure_time
        )
        if not time_validation['valid']:
            return {"error": time_validation['error']}, 400
        
        # Check for user's existing conflicting reservations
        # Store as naive datetime (treat as IST)
        today = datetime.today().date()
        expected_arrival_dt = datetime.combine(today, expected_arrival_time)
        expected_departure_dt = datetime.combine(today, expected_departure_time)
        
        user_conflicts = get_user_booking_conflicts(user_id, expected_arrival_dt, expected_departure_dt)
        if user_conflicts:
            return {
                "error": "You already have a reservation during this time period",
                "conflicts": user_conflicts
            }, 400
        
        # Use enhanced booking logic
        booking_result = enhanced_booking_logic(
            lot_id, user, vehicle_id, expected_arrival_time, expected_departure_time
        )
        
        if 'error' in booking_result:
            return {"error": booking_result['error']}, 400
        
        # Calculate cost
        cost_info = calculate_booking_cost(
            parking_lot, booking_result['arrival_dt'], booking_result['departure_dt']
        )
        
        if 'error' in cost_info:
            return {"error": cost_info['error']}, 400
        
        # Create reservation
        try:
            vehicle_number = selected_vehicle.vehicle_number[-2:].upper()
            booking_id = f"BK-{vehicle_number}-{user_id}-{uuid.uuid4().hex[:3].upper()}"
            
            reservation = Reservation(
                booking_id=booking_id,
                spot_id=booking_result['spot'].id if booking_result['status'] == "Confirmed" else None,
                user_id=user_id,
                vehicle_id=vehicle_id,
                expected_arrival=booking_result['arrival_dt'],
                expected_departure=booking_result['departure_dt'],
                parking_cost=cost_info['final_cost'],
                status=booking_result['status'],
                booking_timestamp=datetime.now()  # Use local time (IST)
            )
            
            # Update spot status if confirmed
            if booking_result['status'] == "Confirmed":
                booking_result['spot'].status = 'B'  # Booked
            
            db.session.add(reservation)
            db.session.commit()
            
            return {
                "message": f"Booking {booking_result['status'].lower()}!",
                "booking_id": booking_id,
                "status": booking_result['status'],
                "spot_number": booking_result['spot'].spot_number if booking_result['spot'] else None,
                "expected_arrival": booking_result['arrival_dt'].isoformat(),
                "expected_departure": booking_result['departure_dt'].isoformat(),
                "cost_info": cost_info,
                "vehicle": selected_vehicle.vehicle_number
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Booking failed: {str(e)}"}, 500


@user_ns.route('/park/<int:reservation_id>')
class ParkVehicle(Resource):
    @auth_required('token')
    @roles_required('user')
    def post(self, reservation_id):
        """Park vehicle - transition from booking to actual parking"""
        from ..utils.booking_utils import assign_pending_reservation
        
        user_id = current_user.id
        reservation = Reservation.query.filter_by(
            id=reservation_id, user_id=user_id
        ).first_or_404()
        
        # Validation checks
        if reservation.status != 'Confirmed':
            return {"error": "Only confirmed reservations can be parked"}, 400
        
        if reservation.parking_timestamp:
            return {"error": "Vehicle already parked"}, 400
        
        if not reservation.spot:
            return {"error": "No parking spot assigned to this reservation"}, 400
        
        current_time = datetime.now()  # Use local time instead of UTC
        arrival_time = reservation.expected_arrival
        time_diff = (current_time - arrival_time).total_seconds()
        
        # Check if user is too late (more than 30 minutes)
        if time_diff > 1800:  # 30 minutes = 1800 seconds
            try:
                reservation.status = 'Rejected'
                reservation.cancellation_reason = 'Showed up too late'
                
                if reservation.spot:
                    reservation.spot.status = 'A'
                    # Try to assign to pending reservations
                    assign_pending_reservation(reservation.spot)
                
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error rejecting late reservation: {str(e)}")
            
            return {"error": "You have missed your parking time. Booking rejected."}, 400
        
        # Check if user is too early (more than 15 minutes before expected arrival)
        if time_diff < -900:  # 15 minutes = 900 seconds
            minutes_early = abs(int(time_diff / 60))
            return {"error": f"Your vehicle is not expected for parking yet. Please come back in {minutes_early} minutes."}, 400
        
        # Check if assigned spot is still available
        if reservation.spot.status == 'O':
            # Spot is occupied, try to find another available spot in the same lot
            available_spot = ParkingSpot.query.filter_by(
                lot_id=reservation.spot.lot_id,
                status='A'
            ).first()
            
            if not available_spot:
                return {"error": "No spot currently available in your lot. Please wait or contact support."}, 400
            
            # Reassign to new spot
            reservation.spot = available_spot
        
        # ATOMIC UPDATE: All changes together with transaction
        try:
            # Update spot status
            reservation.spot.status = 'O'  # Occupied
            
            # Update reservation
            reservation.parking_timestamp = datetime.now()  # Use local time
            reservation.status = 'Parked'
            
            # Commit all changes atomically
            db.session.commit()
            
            return {
                "message": "You have successfully parked your vehicle",
                "parking_timestamp": current_time.isoformat(),
                "spot_id": reservation.spot.id,
                "spot_number": reservation.spot.spot_number if hasattr(reservation.spot, 'spot_number') else None
            }
        except Exception as e:
            # Rollback on any error
            db.session.rollback()
            print(f"Error during park-in: {str(e)}")
            return {"error": "Failed to park vehicle. Please try again."}, 500


@user_ns.route('/park_out/<int:reservation_id>')
class ParkOut(Resource):
    @auth_required('token')
    @roles_required('user')
    def post(self, reservation_id):
        """Park out - complete the parking session"""
        from ..utils.booking_utils import assign_pending_reservation
        
        user_id = current_user.id
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            user_id=user_id,
            status="Parked"
        ).first_or_404()
        
        if reservation.leaving_timestamp:
            return {"error": "Vehicle already parked out"}, 400
        
        try:
            current_time = datetime.now()  # Use local time (IST)
            
            # Calculate parking duration and cost
            parking_duration = current_time - reservation.parking_timestamp
            hours_parked = parking_duration.total_seconds() / 3600
            chargeable_hours = max(1, hours_parked)  # Minimum 1 hour charge
            
            # Calculate final cost based on actual parking time
            if reservation.spot and reservation.spot.lot:
                hourly_rate = reservation.spot.lot.price
                final_cost = chargeable_hours * hourly_rate
            else:
                # Fallback to original estimated cost
                final_cost = reservation.parking_cost
            
            # Update reservation
            reservation.leaving_timestamp = current_time
            reservation.parking_cost = round(final_cost, 2)
            reservation.status = 'Parked Out'
            
            # Free up the spot
            if reservation.spot:
                print(f"Park out: Freeing spot {reservation.spot.id}, current status: {reservation.spot.status}")
                reservation.spot.status = 'A'
                print(f"Park out: Set spot {reservation.spot.id} to Available")
                # Try to assign to pending reservations
                assigned = assign_pending_reservation(reservation.spot)
                if assigned:
                    print(f"Park out: Spot {reservation.spot.id} was assigned to pending reservation")
                else:
                    print(f"Park out: No pending reservations, spot {reservation.spot.id} remains Available")
            else:
                print(f"Park out: Warning - reservation {reservation.id} has no spot assigned!")
            
            db.session.commit()
            print(f"Park out: Changes committed for reservation {reservation.id}")
            
            # Invalidate cache after park out
            from ..utils.cache_hooks import invalidate_user_cache, invalidate_lot_cache, invalidate_admin_cache
            invalidate_user_cache(user_id)
            if reservation.spot:
                invalidate_lot_cache(reservation.spot.lot_id)
            invalidate_admin_cache()
            
            return {
                "message": "Park out successful",
                "final_cost": reservation.parking_cost,
                "duration_hours": hours_parked,
                "parking_duration": str(parking_duration),
                "leaving_timestamp": current_time.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error processing park out: {str(e)}"}, 500


@user_ns.route('/release/<int:reservation_id>')
class ReleaseSpot(Resource):
    @auth_required('token')
    @roles_required('user')
    def post(self, reservation_id):
        """Legacy endpoint - redirects to park_out"""
        return self.park_out(reservation_id)


@user_ns.route('/cancel_booking/<int:reservation_id>')
class CancelBooking(Resource):
    @auth_required('token')
    @roles_required('user')
    def post(self, reservation_id):
        """Cancel a booking/reservation"""
        from ..utils.booking_utils import assign_pending_reservation
        
        user_id = current_user.id
        reservation = Reservation.query.filter_by(
            id=reservation_id, user_id=user_id
        ).first_or_404()
        
        if reservation.status not in ['Confirmed', 'Pending']:
            return {"error": "Only confirmed or pending bookings can be cancelled"}, 400
        
        if reservation.status == 'Parked':
            return {"error": "Cannot cancel a booking that is already parked. Use park_out instead."}, 400
        
        try:
            # Update reservation status
            reservation.status = 'Cancelled'
            reservation.cancellation_reason = "Cancelled by user"
            
            # Free up the spot if it was assigned
            if reservation.spot:
                reservation.spot.status = 'A'
                # Try to assign to pending reservations
                assign_pending_reservation(reservation.spot)
            
            db.session.commit()
            
            return {
                "message": "Booking cancelled successfully",
                "booking_id": reservation.booking_id,
                "cancelled_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error cancelling booking: {str(e)}"}, 500


@user_ns.route('/lot_availability/<int:lot_id>')
class LotAvailability(Resource):
    @user_ns.expect(user_ns.model('AvailabilityCheck', {
        'expected_arrival': fields.String(required=True, description='Expected arrival time (HH:MM format)'),
        'expected_departure': fields.String(required=True, description='Expected departure time (HH:MM format)')
    }))
    @auth_required('token')
    @roles_required('user')
    def post(self, lot_id):
        """Check availability for a specific time slot"""
        from ..utils.booking_utils import get_lot_availability_for_time_slot
        
        data = request.get_json() or {}
        
        # Parse time inputs
        expected_arrival = data.get('expected_arrival')
        expected_departure = data.get('expected_departure')
        
        if not expected_arrival or not expected_departure:
            return {"error": "Expected arrival and departure times are required"}, 400
        
        try:
            expected_arrival_time = datetime.strptime(expected_arrival, '%H:%M').time()
            expected_departure_time = datetime.strptime(expected_departure, '%H:%M').time()
        except ValueError:
            return {"error": "Invalid time format. Use HH:MM format"}, 400
        
        # Convert to datetime for today
        # Store as naive datetime (treat as IST)
        today = datetime.today().date()
        expected_arrival_dt = datetime.combine(today, expected_arrival_time)
        expected_departure_dt = datetime.combine(today, expected_departure_time)
        
        # Get availability information
        availability = get_lot_availability_for_time_slot(
            lot_id, expected_arrival_dt, expected_departure_dt
        )
        
        if 'error' in availability:
            return {"error": availability['error']}, 400
        
        return availability 


@user_ns.route('/my_reservations')
class MyReservations(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        from ..models.Review import Review
        
        user_id = current_user.id
        reservations = Reservation.query.filter_by(user_id=user_id).all()
        
        data = []
        for r in reservations:
            # Get review if exists for this parking lot
            review = None
            if r.spot and r.spot.lot_id:
                review = Review.query.filter_by(
                    user_id=user_id,
                    parking_lot_id=r.spot.lot_id
                ).order_by(Review.created_at.desc()).first()
            
            data.append({
                "id": r.id,
                "spot_id": r.spot_id,
                "spot_number": r.spot.spot_number if r.spot else None,
                "lot_id": r.spot.lot_id if r.spot else None,
                "vehicle_id": r.vehicle_id,
                "booking_id": r.booking_id,
                "status": r.status,
                "expected_arrival": r.expected_arrival.isoformat() if r.expected_arrival else None,
                "expected_departure": r.expected_departure.isoformat() if r.expected_departure else None,
                "start": r.parking_timestamp.isoformat() if r.parking_timestamp else None,
                "end": r.leaving_timestamp.isoformat() if r.leaving_timestamp else None,
                "cost": r.parking_cost,
                "parking_timestamp": r.parking_timestamp.isoformat() if r.parking_timestamp else None,
                "leaving_timestamp": r.leaving_timestamp.isoformat() if r.leaving_timestamp else None,
                "cancellation_reason": r.cancellation_reason,
                "rating": review.rating if review else None,
                "review": review.comment if review else None
            })
        
        return data


@user_ns.route('/reservations/<int:reservation_id>')
class ReservationDetail(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self, reservation_id):
        """Get detailed information about a specific reservation including review"""
        from ..models.Review import Review
        
        user_id = current_user.id
        reservation = Reservation.query.filter_by(
            id=reservation_id, user_id=user_id
        ).first_or_404()
        
        # Get review if exists (check by lot_id and user_id)
        review = None
        if reservation.spot and reservation.spot.lot_id:
            review = Review.query.filter_by(
                user_id=user_id,
                parking_lot_id=reservation.spot.lot_id
            ).order_by(Review.created_at.desc()).first()
        
        
        spot_data = None
        if reservation.spot:
            spot_data = {
                "id": reservation.spot.id,
                "spot_number": reservation.spot.spot_number
            }

        data = {
            "id": reservation.id,
            "spot_id": reservation.spot_id,
            "spot": spot_data,
            "lot_id": reservation.spot.lot_id if reservation.spot else None,
            "vehicle_id": reservation.vehicle_id,
            "booking_id": reservation.booking_id,
            "status": reservation.status,
            "expected_arrival": reservation.expected_arrival.isoformat() if reservation.expected_arrival else None,
            "expected_departure": reservation.expected_departure.isoformat() if reservation.expected_departure else None,
            "start": reservation.parking_timestamp.isoformat() if reservation.parking_timestamp else None,
            "end": reservation.leaving_timestamp.isoformat() if reservation.leaving_timestamp else None,
            "cost": reservation.parking_cost,
            "cancellation_reason": reservation.cancellation_reason,
            "rating": review.rating if review else None,
            "review": review.comment if review else None
        }
        
        return {"reservation": data}


@user_ns.route('/my_active_reservation')
class ActiveReservation(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        user_id = current_user.id
        reservation = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.leaving_timestamp == None,
            Reservation.status.notin_(['Cancelled', 'Rejected'])
        ).first()
        if not reservation:
            return {"message": "No active reservation"}, 404

        return {
            "id": reservation.id,
            "spot_id": reservation.spot_id,
            "lot_id": reservation.spot.lot_id,
            "start": reservation.parking_timestamp.isoformat() if reservation.parking_timestamp else None
        }


@user_ns.route('/my_vehicles')
class MyVehicles(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        user_id = current_user.id
        vehicles = Vehicle.query.filter_by(user_id=user_id).all()
        data = [{
            "id": v.id,
            "vehicle_number": v.vehicle_number,
            "name": v.vehicle_name,
            "color": v.color
        } for v in vehicles]
        return data


@user_ns.route('/add_vehicle')
class AddVehicle(Resource):
    @user_ns.expect(vehicle_model)
    @auth_required('token')
    @roles_required('user')
    def post(self):
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        if not data.get('vehicle_number') or not data.get('vehicle_name'):
            return {"error": "Vehicle number and name are required"}, 400
        
        vehicle_number = data['vehicle_number'].strip()
        
        # Check if vehicle number already exists
        existing_vehicle = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()
        if existing_vehicle:
            return {"error": f"Vehicle with number '{vehicle_number}' already exists"}, 400
        
        try:
            vehicle = Vehicle(
                user_id=user_id,
                vehicle_number=vehicle_number,
                vehicle_name=data['vehicle_name'],
                color=data.get('color', '').strip() if data.get('color') else None
            )
            db.session.add(vehicle)
            db.session.commit()
            return {"message": "Vehicle added successfully"}, 201
            
        except Exception as e:
            db.session.rollback()
            # Handle any other database errors
            if "UNIQUE constraint failed" in str(e):
                return {"error": f"Vehicle with number '{vehicle_number}' already exists"}, 400
            else:
                return {"error": "Failed to add vehicle. Please try again."}, 500


@user_ns.route('/remove_vehicle/<int:vehicle_id>')
class RemoveVehicle(Resource):
    @auth_required('token')
    @roles_required('user')
    def delete(self, vehicle_id):
        user_id = current_user.id
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first_or_404()
        db.session.delete(vehicle)
        db.session.commit()
        return {"message": "Vehicle removed"} 


@user_ns.route('/update_vehicle/<int:vehicle_id>')
class UpdateVehicle(Resource):
    @user_ns.expect(vehicle_model)
    @auth_required('token')
    @roles_required('user')
    def put(self, vehicle_id):
        user_id = current_user.id
        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first_or_404()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('vehicle_number') or not data.get('vehicle_name'):
            return {"error": "Vehicle number and name are required"}, 400
        
        new_vehicle_number = data['vehicle_number'].strip()
        
        # Check if vehicle number already exists (excluding current vehicle)
        if new_vehicle_number != vehicle.vehicle_number:
            existing_vehicle = Vehicle.query.filter_by(vehicle_number=new_vehicle_number).first()
            if existing_vehicle:
                return {"error": f"Vehicle with number '{new_vehicle_number}' already exists"}, 400
        
        try:
            vehicle.vehicle_number = new_vehicle_number
            vehicle.vehicle_name = data.get('vehicle_name', vehicle.vehicle_name)
            vehicle.color = data.get('color', '').strip() if data.get('color') else None
            
            db.session.commit()
            return {"message": "Vehicle updated successfully"}
            
        except Exception as e:
            db.session.rollback()
            # Handle any other database errors
            if "UNIQUE constraint failed" in str(e):
                return {"error": f"Vehicle with number '{new_vehicle_number}' already exists"}, 400
            else:
                return {"error": "Failed to update vehicle. Please try again."}, 500 


# =========================================================================== #
# PROFILE MANAGEMENT
# =========================================================================== #

@user_ns.route('/profile')
class UserProfile(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        """Get current user profile information with completion tracking"""
        user_id = current_user.id
        user = User.query.get(user_id)
        
        # Define required fields for profile completion
        required_fields = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'address': user.address,
            'pincode': user.pincode
        }
        
        # Check if user has vehicles (required for booking)
        has_vehicles = Vehicle.query.filter_by(user_id=user.id).count() > 0
        
        # Calculate completion
        completed_required = sum(1 for field in required_fields.values() if field and field.strip())
        total_required = len(required_fields)
        
        # Add vehicle requirement
        if has_vehicles:
            completed_required += 1
        total_required += 1
        
        profile_completion = int((completed_required / total_required) * 100)
        
        # Check if profile is complete enough for booking
        can_book = (
            user.first_name and user.first_name.strip() and
            user.last_name and user.last_name.strip() and
            user.phone_number and user.phone_number.strip() and
            has_vehicles
        )
        
        # Missing fields for completion
        missing_fields = []
        for field_name, field_value in required_fields.items():
            if not field_value or not field_value.strip():
                missing_fields.append(field_name.replace('_', ' ').title())
        
        if not has_vehicles:
            missing_fields.append('At least one vehicle')
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "address": user.address,
            "pincode": user.pincode,
            "google_chat_webhook": user.google_chat_webhook,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "profile_completion": profile_completion,
            "can_book": can_book,
            "missing_fields": missing_fields,
            "has_vehicles": has_vehicles,
            "total_reservations": Reservation.query.filter_by(user_id=user.id).count(),
            "total_favorites": Favorite.query.filter_by(user_id=user.id).count()
        }

    @user_ns.expect(user_ns.model('ProfileUpdate', {
        'username': fields.String(description='Username'),
        'first_name': fields.String(description='First name'),
        'last_name': fields.String(description='Last name'),
        'phone_number': fields.String(description='Phone number'),
        'address': fields.String(description='Address'),
        'pincode': fields.String(description='PIN code'),
        'google_chat_webhook': fields.String(description='Google Chat webhook URL for notifications'),
        'current_password': fields.String(description='Current password for verification'),
        'new_password': fields.String(description='New password (optional)')
    }))
    @auth_required('token')
    @roles_required('user')
    def put(self):
        """Update user profile"""
        user_id = current_user.id
        user = User.query.get(user_id)
        data = request.get_json()
        
        # Verify current password if provided
        current_password = data.get('current_password')
        if current_password:
            from flask_security.utils import verify_password
            if not verify_password(current_password, user.password):
                return {"error": "Current password is incorrect"}, 400
        
        # Update fields
        if 'username' in data and data['username'] != user.username:
            # Check if username is already taken
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return {"error": "Username already taken"}, 400
            user.username = data['username']
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        if 'phone_number' in data:
            # Validate phone number format if provided
            phone = data['phone_number'].strip()
            if phone and not phone.isdigit():
                return {"error": "Phone number must contain only digits"}, 400
            user.phone_number = phone
        
        if 'address' in data:
            user.address = data['address']
        
        if 'pincode' in data:
            # Validate pincode format if provided
            pincode = (data.get('pincode') or '').strip()
            if pincode and (not pincode.isdigit() or len(pincode) != 6):
                return {"error": "PIN code must be exactly 6 digits"}, 400
            user.pincode = pincode
        
        if 'google_chat_webhook' in data:
            webhook = data.get('google_chat_webhook')
            if webhook:
                webhook = webhook.strip()
                # Basic validation for Google Chat webhook URL
                if webhook and not webhook.startswith('https://chat.googleapis.com/v1/spaces/'):
                    return {"error": "Invalid Google Chat webhook URL. Must start with https://chat.googleapis.com/v1/spaces/"}, 400
            user.google_chat_webhook = webhook if webhook else None
        
        # Update password if provided
        if 'new_password' in data and data['new_password']:
            from flask_security.utils import hash_password
            user.password = hash_password(data['new_password'])
        
        db.session.commit()
        return {"message": "Profile updated successfully"}


@user_ns.route('/delete-account')
class DeleteAccount(Resource):
    @user_ns.expect(user_ns.model('DeleteAccount', {
        'password': fields.String(required=True, description='Current password for verification'),
        'confirmation': fields.String(required=True, description='Must be "DELETE" to confirm')
    }))
    @auth_required('token')
    @roles_required('user')
    def delete(self):
        """Delete user account permanently"""
        user_id = current_user.id
        user = User.query.get(user_id)
        data = request.get_json()
        
        # Verify password
        password = data.get('password')
        if not password:
            return {"error": "Password is required"}, 400
        
        from flask_security.utils import verify_password
        if not verify_password(password, user.password):
            return {"error": "Incorrect password"}, 400
        
        # Verify confirmation
        confirmation = data.get('confirmation')
        if confirmation != "DELETE":
            return {"error": "Please type 'DELETE' to confirm account deletion"}, 400
        
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
            
            # Delete the user account
            db.session.delete(user)
            
            # Commit all changes
            db.session.commit()
            
            return {
                "message": "Account deleted successfully. We're sorry to see you go!",
                "deleted_at": datetime.utcnow().isoformat()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                "error": f"Failed to delete account: {str(e)}"
            }, 500


# =========================================================================== #
# FAVORITES MANAGEMENT
# =========================================================================== #

@user_ns.route('/favorites')
class UserFavorites(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        """Get user's favorite parking lots"""
        user_id = current_user.id
        
        # Get favorites with parking lot details
        favorites = db.session.query(ParkingLot).join(
            Favorite, Favorite.lot_id == ParkingLot.id
        ).filter(Favorite.user_id == user_id).all()
        
        data = []
        for lot in favorites:
            available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            data.append({
                "id": lot.id,
                "location": lot.prime_location_name,
                "address": lot.address,
                "pincode": lot.pincode,
                "price": lot.price,
                "total_spots": lot.number_of_spots,
                "available_spots": available_spots
            })
        
        return data


@user_ns.route('/favorites/<int:lot_id>')
class ManageFavorite(Resource):
    @auth_required('token')
    @roles_required('user')
    def post(self, lot_id):
        """Add parking lot to favorites"""
        user_id = current_user.id
        
        # Check if lot exists
        lot = ParkingLot.query.get_or_404(lot_id)
        
        # Check if already favorited
        existing = Favorite.query.filter_by(user_id=user_id, lot_id=lot_id).first()
        if existing:
            return {"message": "Already in favorites"}, 200
        
        # Add to favorites
        favorite = Favorite(user_id=user_id, lot_id=lot_id)
        db.session.add(favorite)
        db.session.commit()
        
        return {"message": "Added to favorites"}, 201
    
    @auth_required('token')
    @roles_required('user')
    def delete(self, lot_id):
        """Remove parking lot from favorites"""
        user_id = current_user.id
        
        favorite = Favorite.query.filter_by(user_id=user_id, lot_id=lot_id).first()
        if not favorite:
            return {"message": "Not in favorites"}, 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        return {"message": "Removed from favorites"}


# =========================================================================== #
# REVIEWS
# =========================================================================== #

@user_ns.route('/reviews')
class UserReviews(Resource):
    @auth_required('token')
    @roles_required('user')
    def post(self):
        """Submit a review for a parking lot"""
        from ..models.Review import Review
        
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        if not data.get('parking_lot_id') or not data.get('rating'):
            return {"error": "parking_lot_id and rating are required"}, 400
        
        # Validate rating range
        rating = data.get('rating')
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return {"error": "Rating must be between 1 and 5"}, 400
        
        try:
            # Check if user has already reviewed this lot
            existing_review = Review.query.filter_by(
                user_id=user_id,
                parking_lot_id=data['parking_lot_id']
            ).first()
            
            if existing_review:
                # Update existing review
                existing_review.rating = rating
                existing_review.comment = data.get('comment', '')
                existing_review.created_at = datetime.utcnow()
                message = "Review updated successfully"
            else:
                # Create new review
                review = Review(
                    user_id=user_id,
                    parking_lot_id=data['parking_lot_id'],
                    rating=rating,
                    comment=data.get('comment', '')
                )
                db.session.add(review)
                message = "Review submitted successfully"
            
            db.session.commit()
            
            return {
                "message": message,
                "review": {
                    "rating": rating,
                    "comment": data.get('comment', '')
                }
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to submit review: {str(e)}"}, 500


@user_ns.route('/reviews/check/<int:lot_id>')
class CheckReview(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self, lot_id):
        """Check if user has already reviewed a parking lot"""
        from ..models.Review import Review
        
        user_id = current_user.id
        
        existing_review = Review.query.filter_by(
            user_id=user_id,
            parking_lot_id=lot_id
        ).first()
        
        return {
            "has_review": existing_review is not None,
            "review": {
                "rating": existing_review.rating,
                "comment": existing_review.comment
            } if existing_review else None
        }


# =========================================================================== #
# USER STATISTICS & ANALYTICS
# =========================================================================== #

@user_ns.route('/statistics')
class UserStatistics(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        """Get user statistics and analytics"""
        user_id = current_user.id
        
        # Status counts
        status_counts = {
            'total': Reservation.query.filter_by(user_id=user_id).count(),
            'completed': Reservation.query.filter_by(user_id=user_id).filter(
                Reservation.leaving_timestamp.isnot(None)
            ).count(),
            'active': Reservation.query.filter_by(user_id=user_id, leaving_timestamp=None).count()
        }
        
        # Spending by location
        spending_data = db.session.query(
            ParkingLot.prime_location_name,
            func.sum(Reservation.parking_cost).label('total_spent'),
            func.count(Reservation.id).label('visit_count')
        ).join(ParkingSpot, ParkingSpot.id == Reservation.spot_id)\
         .join(ParkingLot, ParkingLot.id == ParkingSpot.lot_id)\
         .filter(
             Reservation.user_id == user_id,
             Reservation.parking_cost.isnot(None)
         ).group_by(ParkingLot.id).all()
        
        spending_by_location = [{
            'location': item[0],
            'total_spent': float(item[1] or 0),
            'visit_count': item[2]
        } for item in spending_data]
        
        # Vehicle usage
        vehicle_usage = db.session.query(
            Vehicle.vehicle_number,
            Vehicle.vehicle_name,
            func.count(Reservation.id).label('usage_count')
        ).join(Reservation, Reservation.vehicle_id == Vehicle.id)\
         .filter(Reservation.user_id == user_id)\
         .group_by(Vehicle.id).all()
        
        vehicle_stats = [{
            'vehicle_number': item[0],
            'vehicle_name': item[1],
            'usage_count': item[2]
        } for item in vehicle_usage]
        
        # Total spending
        total_spent = db.session.query(func.sum(Reservation.parking_cost))\
                               .filter_by(user_id=user_id)\
                               .scalar() or 0
        
        return {
            'status_counts': status_counts,
            'spending_by_location': spending_by_location,
            'vehicle_usage': vehicle_stats,
            'total_spent': float(total_spent),
            'favorite_locations_count': Favorite.query.filter_by(user_id=user_id).count()
        }


@user_ns.route('/analytics/dashboard')
class UserAnalyticsDashboard(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        """Get comprehensive analytics for user dashboard"""
        from ..models.Review import Review
        user_id = current_user.id
        
        # Overview stats
        total_reservations = Reservation.query.filter_by(user_id=user_id).count()
        completed_reservations = Reservation.query.filter_by(user_id=user_id).filter(
            Reservation.leaving_timestamp.isnot(None)
        ).count()
        
        # Only count spending from completed parkings (Parked Out status)
        total_spent = db.session.query(func.sum(Reservation.parking_cost))\
                               .filter(
                                   Reservation.user_id == user_id,
                                   Reservation.status == 'Parked Out',
                                   Reservation.leaving_timestamp.isnot(None),
                                   Reservation.parking_cost.isnot(None)
                               ).scalar() or 0
        
        completion_rate = int((completed_reservations / total_reservations * 100)) if total_reservations > 0 else 0
        
        # Monthly spending (last 12 months for better visibility)
        from datetime import datetime, timedelta
        twelve_months_ago = datetime.now() - timedelta(days=365)
        
        # Get all completed reservations with costs
        # Use parking_timestamp or leaving_timestamp, whichever is available
        completed_reservations_with_cost = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.parking_cost.isnot(None)
        ).filter(
            db.or_(
                Reservation.leaving_timestamp.isnot(None),
                Reservation.parking_timestamp.isnot(None)
            )
        ).all()
        
        # Group by month manually
        monthly_map = {}
        for reservation in completed_reservations_with_cost:
            # Use leaving_timestamp if available, otherwise parking_timestamp, otherwise booking_timestamp
            timestamp = reservation.leaving_timestamp or reservation.parking_timestamp or reservation.booking_timestamp
            if timestamp:
                # Only include if within last 12 months
                if timestamp >= twelve_months_ago:
                    month_key = timestamp.strftime('%Y-%m')
                    if month_key not in monthly_map:
                        monthly_map[month_key] = 0
                    monthly_map[month_key] += float(reservation.parking_cost or 0)
        
        # Convert to sorted list
        monthly_data = [
            {'month': month, 'spent': spent}
            for month, spent in sorted(monthly_map.items())
        ]
        
        # Favorite lots (most visited)
        favorite_lots = db.session.query(
            ParkingLot.prime_location_name.label('name'),
            func.count(Reservation.id).label('visits'),
            func.sum(Reservation.parking_cost).label('total_spent')
        ).join(ParkingSpot, ParkingSpot.id == Reservation.spot_id)\
         .join(ParkingLot, ParkingLot.id == ParkingSpot.lot_id)\
         .filter(Reservation.user_id == user_id)\
         .group_by(ParkingLot.id)\
         .order_by(func.count(Reservation.id).desc())\
         .limit(5).all()
        
        favorite_lots_data = [{
            'name': item[0],
            'usage_count': item[1],
            'total_spent': float(item[2] or 0)
        } for item in favorite_lots]
        
        # Weekly activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        weekly_activity = db.session.query(
            func.date(Reservation.booking_timestamp).label('date'),
            func.count(Reservation.id).label('bookings')
        ).filter(
            Reservation.user_id == user_id,
            Reservation.booking_timestamp >= seven_days_ago
        ).group_by('date').order_by('date').all()
        
        weekly_data = [{
            'date': str(item[0]),
            'bookings': item[1]
        } for item in weekly_activity]
        
        # Recent activity
        recent_reservations = Reservation.query.filter_by(user_id=user_id)\
                                               .order_by(Reservation.booking_timestamp.desc())\
                                               .limit(10).all()
        
        recent_activity = []
        for r in recent_reservations:
            lot_name = 'Unknown'
            if r.spot and r.spot.lot:
                lot_name = r.spot.lot.prime_location_name
            
            recent_activity.append({
                'lot_name': lot_name,
                'start': r.parking_timestamp.isoformat() if r.parking_timestamp else None,
                'status': r.status,
                'cost': float(r.parking_cost) if r.parking_cost else 0
            })
        
        # Average rating given by user
        avg_rating = db.session.query(func.avg(Review.rating))\
                               .filter_by(user_id=user_id)\
                               .scalar() or 0
        
        return {
            'overview': {
                'total_reservations': total_reservations,
                'total_spent': float(total_spent),
                'completion_rate': completion_rate,
                'avg_rating_given': round(float(avg_rating), 1) if avg_rating else 0
            },
            'monthly_spending': monthly_data,
            'favorite_lots': favorite_lots_data,
            'weekly_activity': weekly_data,
            'recent_activity': recent_activity
        }


# =========================================================================== #
# SEARCH
# =========================================================================== #

@user_ns.route('/search')
class UserSearch(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        """Search parking lots by location, name, or address"""
        query = request.args.get('query', '').strip()
        
        if not query:
            return {"message": "No search query provided"}, 400
        
        # Search parking lots
        lots = ParkingLot.query.filter(
            db.or_(
                ParkingLot.prime_location_name.ilike(f'%{query}%'),
                ParkingLot.address.ilike(f'%{query}%'),
                ParkingLot.pincode.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        results = []
        for lot in lots:
            available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            results.append({
                "id": lot.id,
                "location": lot.prime_location_name,
                "address": lot.address,
                "pincode": lot.pincode,
                "price": lot.price,
                "total_spots": lot.number_of_spots,
                "available_spots": available_spots
            })
        
        return {
            'query': query,
            'results': results,
            'total_found': len(results)
        }


# =========================================================================== #
# BACKGROUND TASKS
# =========================================================================== #

@user_ns.route('/export')
class ExportCSV(Resource):
    @auth_required('token')
    @roles_required('user')
    def post(self):
        """Export user's parking history as CSV - async job that sends email when ready"""
        try:
            from backend.app.tasks.tasks import export_user_csv
            
            user_id = current_user.id
            
            # Trigger async task
            celery_app = current_app.celery
            result = export_user_csv.delay(user_id)
            
            response = {
                "task_id": getattr(result, 'id', None),
                "message": f"Parking history export started. You will receive an email at {current_user.email} when the CSV is ready.",
                "status": "started",
                "user_email": current_user.email,
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

@user_ns.route('/export/status/<task_id>')
class CSVStatus(Resource):
    def get(self, task_id):
        result = AsyncResult(task_id)
        if result.ready():
            if result.successful():
                return {
                    "status": "completed",
                    "filename": result.result,
                    "download_url": f"/user/csv_result/{task_id}"
                }
            else:
                return {
                    "status": "failed",
                    "error": str(result.result)
                }
        else:
            return {
                "status": "pending",
                "message": "CSV generation in progress"
            }

@user_ns.route('/csv_result/<task_id>')
class CSVResult(Resource):
    def get(self, task_id):
        res = AsyncResult(task_id)
        if res.ready() and res.successful():
            return send_from_directory('static', res.result)
        else:
            return {"error": "File not ready or task failed"}, 404

@user_ns.route('/mail')
class SendReports(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        res = send_monthly_reports.delay()
        return {
            "task_id": res.id,
            "status": "Monthly report generation started",
            "message": "Check /mail/status/<task_id> for progress"
        }

@user_ns.route('/mail/status/<task_id>')
class ReportStatus(Resource):
    def get(self, task_id):
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
                "message": "Report generation in progress"
            }


# =========================================================================== #
# PAYMENT ENDPOINTS
# =========================================================================== #

@user_ns.route('/payments/<int:reservation_id>')
class PaymentInfo(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self, reservation_id):
        """Get payment information for a reservation"""
        user_id = current_user.id
        reservation = Reservation.query.filter_by(
            id=reservation_id, user_id=user_id
        ).first_or_404()
        
        # Check if payment already exists
        payment = Payment.query.filter_by(reservation_id=reservation_id).first()
        
        return {
            "reservation_id": reservation.id,
            "booking_id": reservation.booking_id,
            "amount": reservation.parking_cost,
            "status": reservation.status,
            "payment_exists": payment is not None,
            "payment": payment.to_dict() if payment else None
        }


@user_ns.route('/payments/process')
class ProcessPayment(Resource):
    @user_ns.expect(user_ns.model('PaymentRequest', {
        'reservation_id': fields.Integer(required=True, description='Reservation ID'),
        'payment_method': fields.String(required=True, description='Payment method (UPI, Card, Cash)'),
        'transaction_id': fields.String(required=False, description='Transaction ID from payment gateway')
    }))
    @auth_required('token')
    @roles_required('user')
    def post(self):
        """Process payment for a reservation"""
        import uuid
        
        user_id = current_user.id
        data = request.get_json() or {}
        
        reservation_id = data.get('reservation_id')
        payment_method = data.get('payment_method')
        transaction_id = data.get('transaction_id')
        
        if not reservation_id or not payment_method:
            return {"error": "Reservation ID and payment method are required"}, 400
        
        # Validate reservation
        reservation = Reservation.query.filter_by(
            id=reservation_id, user_id=user_id
        ).first_or_404()
        
        # Check if reservation is in correct status
        if reservation.status != 'Parked Out':
            return {"error": "Payment can only be made for parked out reservations"}, 400
        
        # Check if payment already exists
        existing_payment = Payment.query.filter_by(reservation_id=reservation_id).first()
        if existing_payment:
            return {"error": "Payment already processed for this reservation"}, 400
        
        # Validate payment amount
        if not reservation.parking_cost or reservation.parking_cost <= 0:
            return {"error": "Invalid parking cost"}, 400
        
        try:
            # Generate transaction ID if not provided
            if not transaction_id:
                transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            
            # Create payment record
            payment = Payment(
                reservation_id=reservation_id,
                amount=reservation.parking_cost,
                payment_method=payment_method,
                transaction_id=transaction_id,
                payment_status='completed',
                payment_timestamp=datetime.now()
            )
            
            db.session.add(payment)
            db.session.commit()
            
            # Invalidate cache
            from ..utils.cache_hooks import invalidate_user_cache, invalidate_admin_cache
            invalidate_user_cache(user_id)
            invalidate_admin_cache()
            
            return {
                "message": "Payment processed successfully",
                "payment": payment.to_dict(),
                "reservation_id": reservation_id,
                "amount": payment.amount
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {"error": f"Payment processing failed: {str(e)}"}, 500


@user_ns.route('/payments/history')
class PaymentHistory(Resource):
    @auth_required('token')
    @roles_required('user')
    def get(self):
        """Get user's payment history"""
        user_id = current_user.id
        
        # Get all user reservations with payments
        reservations = Reservation.query.filter_by(user_id=user_id).all()
        reservation_ids = [r.id for r in reservations]
        
        payments = Payment.query.filter(
            Payment.reservation_id.in_(reservation_ids)
        ).order_by(Payment.payment_timestamp.desc()).all()
        
        payment_data = []
        for payment in payments:
            reservation = Reservation.query.get(payment.reservation_id)
            payment_info = payment.to_dict()
            payment_info['booking_id'] = reservation.booking_id if reservation else None
            payment_info['lot_name'] = reservation.spot.lot.prime_location_name if reservation and reservation.spot and reservation.spot.lot else 'Unknown'
            payment_data.append(payment_info)
        
        return {
            "payments": payment_data,
            "total_payments": len(payment_data),
            "total_amount": sum(p.amount for p in payments)
        }


# User Analytics Endpoints
# Note: Analytics moved to /api/cached_user/analytics for better performance


# Task triggering moved to admin-only for security
