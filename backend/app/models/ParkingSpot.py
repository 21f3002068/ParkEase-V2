from ... import db


class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'))
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), default='A')  # A or O
    
    #Relationships
    reservations = db.relationship('Reservation', backref='spot')
