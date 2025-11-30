# backend/app/models/__init__.py
from .User import User, Role, UserRoles
from .ParkingLot import ParkingLot
from .ParkingSpot import ParkingSpot
from .Reservation import Reservation
from .Review import Review
from .Vehicle import Vehicle
from .Payment import Payment
from .Favorite import Favorite
from .TaskLog import TaskLog

__all__ = ['User', 'Role', 'UserRoles', 'ParkingLot', 'ParkingSpot', 'Reservation', 'Review', 'Vehicle', 'Payment', 'Favorite', 'TaskLog']
