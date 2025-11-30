from ... import db
from datetime import datetime


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)  # UPI, Card, Cash, etc.
    transaction_id = db.Column(db.String(100), nullable=True)  # Payment gateway transaction ID
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    reservation = db.relationship('Reservation', backref='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'reservation_id': self.reservation_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'payment_status': self.payment_status,
            'payment_timestamp': self.payment_timestamp.isoformat() if self.payment_timestamp else None
        }

    def __repr__(self):
        return f'<Payment {self.id} for Reservation {self.reservation_id} - ₹{self.amount}>'