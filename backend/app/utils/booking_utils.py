# backend/app/utils/booking_utils.py
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from ..models.Reservation import Reservation
from ..models.ParkingSpot import ParkingSpot
from ..models.ParkingLot import ParkingLot
from .. import db


def assign_pending_reservation(spot):
    """
    Assign pending reservations to a newly available spot.
    This function is called when a spot becomes available (user parks out or cancels).
    
    Args:
        spot: ParkingSpot object that just became available
    """
    try:
        # Find pending reservations for this lot, ordered by booking timestamp (FIFO)
        # Find pending reservations that don't have a spot assigned yet
        # Since pending reservations don't have spots assigned, we can't filter by lot
        # Instead, we'll get all pending reservations and let the conflict checking handle assignment
        pending_reservations = Reservation.query.filter(
            Reservation.status == 'Pending',
            Reservation.spot_id.is_(None)  # Not yet assigned a spot
        ).order_by(Reservation.booking_timestamp.asc()).all()
        
        current_time = datetime.now()
        
        for reservation in pending_reservations:
            # Check if this reservation's time slot conflicts with existing confirmed reservations for this spot
            conflict = Reservation.query.filter(
                Reservation.spot_id == spot.id,
                Reservation.status == 'Confirmed',
                and_(
                    Reservation.expected_departure > reservation.expected_arrival,
                    Reservation.expected_arrival < reservation.expected_departure
                )
            ).first()
            
            if not conflict:
                # No conflict - assign this spot to the pending reservation
                reservation.spot_id = spot.id
                reservation.status = 'Confirmed'
                spot.status = 'B'  # Booked
                
                db.session.commit()
                
                # TODO: Send notification to user about confirmed booking
                # send_booking_confirmation_notification(reservation)
                
                return True
        
        return False
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in assign_pending_reservation: {str(e)}")
        return False


def enhanced_booking_logic(lot_id, user, vehicle_id, expected_arrival_time, expected_departure_time):
    """
    Enhanced booking logic based on Version 1 patterns with comprehensive validation
    and smart spot assignment.
    
    Args:
        lot_id: ID of the parking lot
        user: User object making the booking
        vehicle_id: ID of the selected vehicle
        expected_arrival_time: Time object for expected arrival
        expected_departure_time: Time object for expected departure
        
    Returns:
        dict: Result containing spot assignment, status, and datetime objects
    """
    try:
        parking_lot = ParkingLot.query.get_or_404(lot_id)
        
        # 1. Validate time slot is within lot operating hours
        is_24_hrs = parking_lot.available_from == parking_lot.available_to

        if not is_24_hrs:
            # If closing time is earlier than opening, it crosses midnight
            crosses_midnight = parking_lot.available_to < parking_lot.available_from

            if crosses_midnight:
                # Valid if booking is either after opening OR before closing
                if not (
                    expected_arrival_time >= parking_lot.available_from
                    or expected_departure_time <= parking_lot.available_to
                ):
                    return {
                        "error": f"Booking must be between {parking_lot.available_from.strftime('%I:%M %p')} and {parking_lot.available_to.strftime('%I:%M %p')}"
                    }
            else:
                # Normal same-day range
                if (expected_arrival_time < parking_lot.available_from or
                        expected_departure_time > parking_lot.available_to):
                    return {
                        "error": f"Booking must be between {parking_lot.available_from.strftime('%I:%M %p')} and {parking_lot.available_to.strftime('%I:%M %p')}"
                    }
        
        # 2. Check for user's existing conflicting reservations
        # Only check for active reservations (Confirmed, Pending, Parked)
        existing_reservations = Reservation.query.filter(
            Reservation.user_id == user.id,
            Reservation.status.in_(['Confirmed', 'Pending', 'Parked'])
        ).all()
        
        for reservation in existing_reservations:
            if not (expected_departure_time <= reservation.expected_arrival.time() or 
                   expected_arrival_time >= reservation.expected_departure.time()):
                return {"error": "You already have an active reservation during this time period"}
        
        # 3. Convert time to datetime for today
        # Store as naive datetime (treat as IST)
        today = datetime.today().date()
        expected_arrival_dt = datetime.combine(today, expected_arrival_time)
        expected_departure_dt = datetime.combine(today, expected_departure_time)
        
        # 4. Smart spot allocation with conflict checking
        available_spot = None
        status = "Pending"
        
        # Get all spots in the lot that are not marked as unavailable
        all_spots = [s for s in parking_lot.spots if s.status not in ['X', 'U']]
        
        # First, try to find a spot without any time conflicts
        for spot in all_spots:
            conflict = False
            
            # Check all reservations for this spot
            for reservation in spot.reservations:
                if reservation.status not in ['Cancelled', 'Parked Out', 'Rejected']:
                    # Check for time overlap
                    if not (expected_departure_dt <= reservation.expected_arrival or 
                           expected_arrival_dt >= reservation.expected_departure):
                        conflict = True
                        break
            
            if not conflict:
                available_spot = spot
                status = "Confirmed"
                break
        
        # 5. If no immediate spot available, check occupied spots that will be free
        if not available_spot:
            occupied_spots = [spot for spot in all_spots if spot.status == 'O']
            
            for spot in occupied_spots:
                will_be_free = True
                
                for reservation in spot.reservations:
                    if reservation.status not in ['Cancelled', 'Parked Out', 'Rejected']:
                        # Check if this reservation will conflict with our requested time
                        if not (expected_departure_dt <= reservation.expected_arrival or 
                               expected_arrival_dt >= reservation.expected_departure):
                            will_be_free = False
                            break
                
                if will_be_free:
                    available_spot = spot
                    status = "Pending"  # Will be confirmed when spot becomes available
                    break
        
        # 6. If still no spot, the booking is pending without a spot assigned
        if not available_spot:
            status = "Pending"
        
        return {
            "spot": available_spot,
            "status": status,
            "arrival_dt": expected_arrival_dt,
            "departure_dt": expected_departure_dt,
            "success": True
        }
        
    except Exception as e:
        return {"error": f"Booking logic error: {str(e)}"}


def check_spot_availability(spot_id, expected_arrival, expected_departure):
    """
    Check if a specific spot is available for the given time slot.
    
    Args:
        spot_id: ID of the parking spot
        expected_arrival: datetime object
        expected_departure: datetime object
        
    Returns:
        bool: True if available, False if conflicted
    """
    try:
        conflicting_reservations = Reservation.query.filter(
            Reservation.spot_id == spot_id,
            Reservation.status.in_(['Confirmed', 'Parked']),
            and_(
                Reservation.expected_departure > expected_arrival,
                Reservation.expected_arrival < expected_departure
            )
        ).first()
        
        return conflicting_reservations is None
        
    except Exception as e:
        print(f"Error checking spot availability: {str(e)}")
        return False


def get_lot_availability_for_time_slot(lot_id, expected_arrival, expected_departure):
    """
    Get detailed availability information for a lot during a specific time slot.
    
    Args:
        lot_id: ID of the parking lot
        expected_arrival: datetime object
        expected_departure: datetime object
        
    Returns:
        dict: Availability information including available spots count and details
    """
    try:
        parking_lot = ParkingLot.query.get(lot_id)
        if not parking_lot:
            return {"error": "Parking lot not found"}
        
        available_spots = []
        occupied_spots = []
        conflicted_spots = []
        
        for spot in parking_lot.spots:
            if check_spot_availability(spot.id, expected_arrival, expected_departure):
                available_spots.append({
                    "spot_number": spot.spot_number,
                    "current_status": spot.status
                })
            else:
                # Find the conflicting reservation
                conflict = Reservation.query.filter(
                    Reservation.spot_id == spot.id,
                    Reservation.status.in_(['Confirmed', 'Parked']),
                    and_(
                        Reservation.expected_departure > expected_arrival,
                        Reservation.expected_arrival < expected_departure
                    )
                ).first()
                
                if conflict:
                    conflicted_spots.append({
                        "spot_id": spot.id,
                        "spot_number": spot.spot_number,
                        "conflict_with": {
                            "booking_id": conflict.booking_id,
                            "expected_arrival": conflict.expected_arrival.isoformat(),
                            "expected_departure": conflict.expected_departure.isoformat(),
                            "status": conflict.status
                        }
                    })
        
        return {
            "lot_id": lot_id,
            "lot_name": parking_lot.prime_location_name,
            "total_spots": len(parking_lot.spots),
            "available_spots_count": len(available_spots),
            "available_spots": available_spots,
            "conflicted_spots_count": len(conflicted_spots),
            "conflicted_spots": conflicted_spots,
            "can_book_immediately": len(available_spots) > 0
        }
        
    except Exception as e:
        return {"error": f"Error getting lot availability: {str(e)}"}


def validate_booking_time_constraints(parking_lot, expected_arrival_time, expected_departure_time):
    """
    Validate booking time constraints including operating hours and minimum duration.
    """
    try:
        # Detect 24-hour parking
        is_24_hrs = parking_lot.available_from == parking_lot.available_to


        # If not 24 hours, validate against operating hours
        if not is_24_hrs:
            # If closing time is the same or earlier than opening, it crosses midnight
            crosses_midnight = parking_lot.available_to < parking_lot.available_from

            if crosses_midnight:
                # Valid if booking is either after opening OR before closing
                if not (
                    expected_arrival_time >= parking_lot.available_from
                    or expected_departure_time <= parking_lot.available_to
                ):
                    return {
                        "valid": False,
                        "error": f"Booking must be between {parking_lot.available_from.strftime('%I:%M %p')} and {parking_lot.available_to.strftime('%I:%M %p')}"
                    }
            else:
                # Normal same-day range
                if (
                    expected_arrival_time < parking_lot.available_from
                    or expected_departure_time > parking_lot.available_to
                ):
                    return {
                        "valid": False,
                        "error": f"Booking must be between {parking_lot.available_from.strftime('%I:%M %p')} and {parking_lot.available_to.strftime('%I:%M %p')}"
                    }

        # Check departure after arrival
        if expected_arrival_time >= expected_departure_time:
            return {
                "valid": False,
                "error": "Departure time must be after arrival time"
            }

        # Duration calculations
        from datetime import datetime, timedelta

        arrival_dt = datetime.combine(datetime.today(), expected_arrival_time)
        departure_dt = datetime.combine(datetime.today(), expected_departure_time)

        # If departure is next day
        if departure_dt <= arrival_dt:
            departure_dt += timedelta(days=1)

        duration_minutes = (departure_dt - arrival_dt).total_seconds() / 60

        if duration_minutes < 30:
            return {
                "valid": False,
                "error": "Minimum booking duration is 30 minutes"
            }

        if duration_minutes > 720:
            return {
                "valid": False,
                "error": "Maximum booking duration is 12 hours"
            }

        return {
            "valid": True,
            "duration_minutes": duration_minutes,
            "duration_hours": duration_minutes / 60
        }

    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation error: {str(e)}"
        }


def calculate_booking_cost(parking_lot, expected_arrival_dt, expected_departure_dt):
    """
    Calculate the cost for a booking based on duration and lot pricing.
    
    Args:
        parking_lot: ParkingLot object
        expected_arrival_dt: datetime object
        expected_departure_dt: datetime object
        
    Returns:
        dict: Cost calculation details
    """
    try:
        duration_hours = (expected_departure_dt - expected_arrival_dt).total_seconds() / 3600
        base_cost = parking_lot.price * duration_hours
        
        # Apply any time-based pricing rules
        # For example, different rates for peak/off-peak hours
        hour = expected_arrival_dt.hour
        
        # Peak hours (8 AM - 6 PM) might have higher rates
        if 8 <= hour < 18:
            peak_multiplier = 1.2  # 20% higher during peak hours
            final_cost = base_cost * peak_multiplier
            pricing_type = "peak"
        else:
            final_cost = base_cost
            pricing_type = "standard"
        
        return {
            "base_cost": round(base_cost, 2),
            "final_cost": round(final_cost, 2),
            "duration_hours": round(duration_hours, 2),
            "hourly_rate": parking_lot.price,
            "pricing_type": pricing_type
        }
        
    except Exception as e:
        return {
            "error": f"Cost calculation error: {str(e)}"
        }


def get_user_booking_conflicts(user_id, expected_arrival_dt, expected_departure_dt):
    """
    Check for conflicts with user's existing bookings.
    
    Args:
        user_id: ID of the user
        expected_arrival_dt: datetime object
        expected_departure_dt: datetime object
        
    Returns:
        list: List of conflicting reservations
    """
    try:
        # Only check for active reservations (Confirmed, Pending, Parked)
        # Exclude completed statuses: Parked Out, Cancelled, Rejected, Force Released
        conflicts = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.status.in_(['Confirmed', 'Pending', 'Parked']),
            and_(
                Reservation.expected_departure > expected_arrival_dt,
                Reservation.expected_arrival < expected_departure_dt
            )
        ).all()
        
        print(f"Conflict check for user {user_id}: Found {len(conflicts)} conflicts")
        for c in conflicts:
            print(f"  - Reservation {c.id}, Status: {c.status}, Times: {c.expected_arrival} to {c.expected_departure}")
        
        return [{
            "booking_id": conflict.booking_id,
            "lot_name": conflict.spot.lot.prime_location_name if conflict.spot and conflict.spot.lot else "Unknown",
            "expected_arrival": conflict.expected_arrival.isoformat(),
            "expected_departure": conflict.expected_departure.isoformat(),
            "status": conflict.status
        } for conflict in conflicts]
        
    except Exception as e:
        print(f"Error checking user booking conflicts: {str(e)}")
        return []


def auto_cancel_expired_pending_reservations():
    """
    Automatically cancel pending reservations that have expired.
    This should be run periodically (e.g., every hour) as a background task.
    """
    try:
        current_time = datetime.now()
        
        # Find pending reservations where expected arrival time has passed
        expired_reservations = Reservation.query.filter(
            Reservation.status == 'Pending',
            Reservation.expected_arrival < current_time - timedelta(minutes=30)  # 30 min grace period
        ).all()
        
        cancelled_count = 0
        
        for reservation in expired_reservations:
            reservation.status = 'Rejected'
            reservation.cancellation_reason = 'Expired - arrival time passed'
            cancelled_count += 1
        
        if cancelled_count > 0:
            db.session.commit()
        
        return {
            "success": True,
            "cancelled_count": cancelled_count,
            "message": f"Cancelled {cancelled_count} expired pending reservations"
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "error": f"Error cancelling expired reservations: {str(e)}"
        }