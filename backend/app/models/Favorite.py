from ... import db


class Favorite(db.Model):
    """Model for user's favorite parking lots"""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    user = db.relationship('User', backref='favorites')
    lot = db.relationship('ParkingLot', backref='favorited_by')
    
    # Ensure unique user-lot combination
    __table_args__ = (db.UniqueConstraint('user_id', 'lot_id', name='unique_user_lot_favorite'),)
    
    def __repr__(self):
        return f'<Favorite User:{self.user_id} Lot:{self.lot_id}>'