from ... import db
from datetime import datetime

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    
    # Booking information
    booking_id = db.Column(db.String(50), unique=True)
    booking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Time slots
    expected_arrival = db.Column(db.DateTime)
    expected_departure = db.Column(db.DateTime)
    
    # Actual parking times
    parking_timestamp = db.Column(db.DateTime)
    leaving_timestamp = db.Column(db.DateTime)
    
    # Status and cost
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, Parked, Parked Out, Cancelled, Rejected
    parking_cost = db.Column(db.Float)
    cancellation_reason = db.Column(db.String(200))
    
    # Note: Relationships are defined via backrefs in other models:
    # - spot: backref from ParkingSpot.reservations
    # - user: backref from User.reservations (if exists)
    # - vehicle: backref from Vehicle.reservations (if exists)


