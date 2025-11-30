"""
Data validation utilities to ensure database consistency
"""
from ..models.ParkingSpot import ParkingSpot
from ..models.Reservation import Reservation
from ... import db


BOOKING_STATUSES = ('Pending', 'Confirmed')


def validate_spot_reservation_consistency():
    """
    Check for inconsistencies between spot status and reservation status
    Returns a list of issues found
    """
    issues = []
    
    # Check 1: Occupied spots should have active reservations
    occupied_spots = ParkingSpot.query.filter_by(status='O').all()
    for spot in occupied_spots:
        active_reservation = Reservation.query.filter_by(
            spot_id=spot.id,
            leaving_timestamp=None
        ).filter(
            Reservation.status.in_(['Parked', 'Active'])
        ).first()
        
        if not active_reservation:
            issues.append({
                'type': 'orphaned_occupied_spot',
                'spot_id': spot.id,
                'lot_id': spot.lot_id,
                'message': f'Spot {spot.id} is marked as Occupied but has no active reservation'
            })
    
    # Check 2: Parked reservations should have occupied spots
    parked_reservations = Reservation.query.filter(
        Reservation.status.in_(['Parked', 'Active']),
        Reservation.leaving_timestamp.is_(None),
        Reservation.parking_timestamp.isnot(None)
    ).all()
    
    for reservation in parked_reservations:
        if reservation.spot and reservation.spot.status != 'O':
            issues.append({
                'type': 'parked_without_occupied_spot',
                'reservation_id': reservation.id,
                'spot_id': reservation.spot_id,
                'spot_status': reservation.spot.status,
                'message': f'Reservation {reservation.id} is Parked but spot {reservation.spot_id} is not Occupied'
            })
    
    # Check 3: Rejected/Cancelled reservations should not have occupied spots
    inactive_reservations = Reservation.query.filter(
        Reservation.status.in_(['Rejected', 'Cancelled', 'Parked Out', 'Completed'])
    ).all()
    
    for reservation in inactive_reservations:
        if reservation.spot and reservation.spot.status == 'O':
            # Check if there's another active reservation for this spot
            other_active = Reservation.query.filter(
                Reservation.spot_id == reservation.spot_id,
                Reservation.id != reservation.id,
                Reservation.status.in_(['Parked', 'Active']),
                Reservation.leaving_timestamp.is_(None)
            ).first()
            
            if not other_active:
                issues.append({
                    'type': 'inactive_reservation_with_occupied_spot',
                    'reservation_id': reservation.id,
                    'spot_id': reservation.spot_id,
                    'reservation_status': reservation.status,
                    'message': f'Reservation {reservation.id} is {reservation.status} but spot {reservation.spot_id} is still Occupied'
                })
    
    # Check 4: Parked status must have parking_timestamp
    parked_without_timestamp = Reservation.query.filter(
        Reservation.status == 'Parked',
        Reservation.parking_timestamp.is_(None)
    ).all()
    
    for reservation in parked_without_timestamp:
        issues.append({
            'type': 'parked_without_timestamp',
            'reservation_id': reservation.id,
            'message': f'Reservation {reservation.id} has status Parked but no parking_timestamp'
        })
    
    # Check 5: Spots marked as Booked must have a pending/confirmed reservation
    booked_spots = ParkingSpot.query.filter_by(status='B').all()
    for spot in booked_spots:
        pending_reservation = Reservation.query.filter(
            Reservation.spot_id == spot.id,
            Reservation.status.in_(BOOKING_STATUSES),
            Reservation.leaving_timestamp.is_(None)
        ).order_by(Reservation.booking_timestamp.desc()).first()

        if not pending_reservation:
            issues.append({
                'type': 'booked_without_pending_reservation',
                'spot_id': spot.id,
                'lot_id': spot.lot_id,
                'message': f'Spot {spot.id} is Booked but has no pending/confirmed reservation'
            })

    return issues


def fix_spot_reservation_inconsistencies(auto_fix=False):
    """
    Find and optionally fix inconsistencies
    
    Args:
        auto_fix: If True, automatically fix issues. If False, just report them.
    
    Returns:
        dict with 'issues' and 'fixes_applied'
    """
    issues = validate_spot_reservation_consistency()
    fixes_applied = []
    
    if not auto_fix:
        return {
            'issues': issues,
            'fixes_applied': [],
            'message': 'Issues found. Set auto_fix=True to apply fixes.'
        }
    
    # Fix orphaned occupied spots
    for issue in issues:
        if issue['type'] == 'orphaned_occupied_spot':
            spot = ParkingSpot.query.get(issue['spot_id'])
            if spot:
                spot.status = 'A'  # Mark as available
                fixes_applied.append(f"Fixed spot {spot.id}: Changed from Occupied to Available")
        
        elif issue['type'] == 'parked_without_occupied_spot':
            spot = ParkingSpot.query.get(issue['spot_id'])
            if spot:
                spot.status = 'O'  # Mark as occupied
                fixes_applied.append(f"Fixed spot {spot.id}: Changed to Occupied to match reservation")
        
        elif issue['type'] == 'inactive_reservation_with_occupied_spot':
            spot = ParkingSpot.query.get(issue['spot_id'])
            if spot:
                spot.status = 'A'  # Mark as available
                fixes_applied.append(f"Fixed spot {spot.id}: Released from inactive reservation {issue['reservation_id']}")
        
        elif issue['type'] == 'parked_without_timestamp':
            reservation = Reservation.query.get(issue['reservation_id'])
            if reservation:
                # This is a critical error - we can't guess the timestamp
                # Best to mark as rejected
                reservation.status = 'Rejected'
                reservation.cancellation_reason = 'Data inconsistency - missing parking timestamp'
                if reservation.spot:
                    reservation.spot.status = 'A'
                fixes_applied.append(f"Fixed reservation {reservation.id}: Marked as Rejected due to missing timestamp")

        elif issue['type'] == 'booked_without_pending_reservation':
            spot = ParkingSpot.query.get(issue['spot_id'])
            if spot:
                spot.status = 'A'
                fixes_applied.append(
                    f"Fixed spot {spot.id}: Released from Booked because no pending reservation exists"
                )
    
    if fixes_applied:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {
                'issues': issues,
                'fixes_applied': [],
                'error': f'Failed to apply fixes: {str(e)}'
            }
    
    return {
        'issues': issues,
        'fixes_applied': fixes_applied,
        'message': f'Applied {len(fixes_applied)} fixes'
    }
