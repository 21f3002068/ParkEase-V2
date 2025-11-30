from ... import db


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_name = db.Column(db.String(50), nullable=False)  
    color = db.Column(db.String(20), nullable=True)

    # Relationships
    user = db.relationship('User', backref='vehicles')

    def __repr__(self):
        return f'<Vehicle {self.vehicle_number} ({self.vehicle_name})>'