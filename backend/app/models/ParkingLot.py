from ... import db

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100))
    
    number_of_spots = db.Column(db.Integer)
    price = db.Column(db.Float)
    
    address = db.Column(db.String(200))
    pincode = db.Column(db.String(10))
    
    available_from = db.Column(db.Time, default=db.text("'06:00:00'"))  # Default opening at 6 AM
    available_to = db.Column(db.Time, default=db.text("'22:00:00'"))    # Default closing at 10 PM
    
    is_active = db.Column(db.Boolean, default=True)
    
    #Relationships
    spots = db.relationship('ParkingSpot', backref='lot', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='parking_lot', cascade='all, delete-orphan')
