"""
Cached User API Routes for Performance
"""
from flask import request, jsonify
from flask_security import auth_required, current_user
from flask_restx import Namespace, Resource
from datetime import datetime, timedelta
from sqlalchemy import func
from ..models import ParkingLot, ParkingSpot, Reservation, User, Vehicle, Favorite
from .. import db
from ..utils.cache import cached, cache_key_for_user, cache_key_for_lot, cache

cached_user_ns = Namespace('cached_user', description='Cached user operations for performance')

@cached_user_ns.route('/lots')
class CachedAvailableLots(Resource):
    @auth_required('token')
    @cached(expiry=180, key_prefix="available_lots")  # Cache for 3 minutes
    def get(self):
        """Get all available parking lots with caching"""
        try:
            lots = db.session.query(ParkingLot).all()
            
            lots_data = []
            for lot in lots:
                # Count available spots
                available_spots = db.session.query(ParkingSpot).filter_by(
                    lot_id=lot.id, 
                    status='A'
                ).count()
                
                lots_data.append({
                    "id": lot.id,
                    "name": lot.prime_location_name,
                    "address": lot.address,
                    "pincode": lot.pincode,
                    "price": lot.price,
                    "capacity": lot.number_of_spots,
                    "available_spots": available_spots,
                    "occupancy_rate": round(((lot.number_of_spots - available_spots) / lot.number_of_spots) * 100, 1) if lot.number_of_spots > 0 else 0
                })
            
            return {
                "lots": lots_data,
                "total_lots": len(lots_data),
                "cached_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to fetch lots: {str(e)}"}, 500

@cached_user_ns.route('/lots/<int:lot_id>/availability')
class CachedLotAvailability(Resource):
    @auth_required('token')
    def get(self, lot_id):
        """Get real-time availability for a specific lot with caching"""
        cache_key = cache_key_for_lot(lot_id, "availability")
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return {**cached_data, "from_cache": True}
        
        try:
            lot = ParkingLot.query.get_or_404(lot_id)
            
            # Get spot statistics
            spots_query = db.session.query(ParkingSpot).filter_by(lot_id=lot_id)
            total_spots = spots_query.count()
            available_spots = spots_query.filter_by(status='A').count()
            occupied_spots = spots_query.filter_by(status='O').count()
            booked_spots = spots_query.filter_by(status='B').count()
            unavailable_spots = spots_query.filter_by(status='X').count()
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_reservations = db.session.query(Reservation).join(ParkingSpot).filter(
                ParkingSpot.lot_id == lot_id,
                Reservation.parking_timestamp >= yesterday
            ).count()
            
            availability_data = {
                "lot_id": lot_id,
                "lot_name": lot.prime_location_name,
                "total_spots": total_spots,
                "available_spots": available_spots,
                "occupied_spots": occupied_spots,
                "booked_spots": booked_spots,
                "unavailable_spots": unavailable_spots,
                "occupancy_rate": round((occupied_spots / total_spots) * 100, 1) if total_spots > 0 else 0,
                "availability_rate": round((available_spots / total_spots) * 100, 1) if total_spots > 0 else 0,
                "recent_activity": recent_reservations,
                "price_per_hour": lot.price,
                "last_updated": datetime.utcnow().isoformat(),
                "from_cache": False
            }
            
            # Cache for 1 minute (high frequency data)
            cache.set(cache_key, availability_data, expiry=60)
            
            return availability_data
            
        except Exception as e:
            return {"error": f"Failed to get availability: {str(e)}"}, 500

@cached_user_ns.route('/dashboard')
class CachedUserDashboard(Resource):
    @auth_required('token')
    def get(self):
        """Get user dashboard data with caching"""
        user_id = current_user.id
        cache_key = cache_key_for_user(user_id, "dashboard")
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return {**cached_data, "from_cache": True}
        
        try:
            # Get user reservations
            reservations = db.session.query(Reservation).filter_by(user_id=user_id).all()
            
            # Calculate statistics
            total_reservations = len(reservations)
            completed_reservations = len([r for r in reservations if r.leaving_timestamp])
            total_spent = sum([r.parking_cost or 0 for r in reservations])
            
            # Get active reservation
            active_reservation = db.session.query(Reservation).filter_by(
                user_id=user_id,
                leaving_timestamp=None
            ).first()
            
            # Get favorite lots
            favorite_lots = db.session.query(Favorite).filter_by(user_id=user_id).count()
            
            # Get vehicles count
            vehicles_count = db.session.query(Vehicle).filter_by(user_id=user_id).count()
            
            dashboard_data = {
                "user_id": user_id,
                "statistics": {
                    "total_reservations": total_reservations,
                    "completed_reservations": completed_reservations,
                    "completion_rate": round((completed_reservations / total_reservations) * 100, 1) if total_reservations > 0 else 0,
                    "total_spent": round(total_spent, 2),
                    "average_cost": round(total_spent / completed_reservations, 2) if completed_reservations > 0 else 0,
                    "favorite_lots": favorite_lots,
                    "vehicles_count": vehicles_count
                },
                "has_active_reservation": active_reservation is not None,
                "active_reservation_id": active_reservation.id if active_reservation else None,
                "last_updated": datetime.utcnow().isoformat(),
                "from_cache": False
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, dashboard_data, expiry=300)
            
            return dashboard_data
            
        except Exception as e:
            return {"error": f"Failed to get dashboard data: {str(e)}"}, 500

@cached_user_ns.route('/analytics')
class CachedUserAnalytics(Resource):
    @auth_required('token')
    def get(self):
        """Get user analytics with caching"""
        user_id = current_user.id
        cache_key = cache_key_for_user(user_id, "analytics")
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return {**cached_data, "from_cache": True}
        
        try:
            # Get user reservations with lot information
            reservations = db.session.query(Reservation).join(ParkingSpot).join(ParkingLot).filter(
                Reservation.user_id == user_id
            ).all()
            
            # Monthly spending (last 6 months)
            monthly_spending = {}
            for reservation in reservations:
                if reservation.parking_timestamp and reservation.parking_cost:
                    month_key = reservation.parking_timestamp.strftime('%Y-%m')
                    monthly_spending[month_key] = monthly_spending.get(month_key, 0) + (reservation.parking_cost or 0)
            
            # Most used parking lots
            lot_usage = {}
            for reservation in reservations:
                lot_name = reservation.spot.lot.prime_location_name
                lot_usage[lot_name] = lot_usage.get(lot_name, 0) + 1
            
            # Recent activity (last 10 reservations)
            recent_reservations = sorted(reservations, key=lambda x: x.parking_timestamp or datetime.min, reverse=True)[:10]
            recent_activity = []
            for reservation in recent_reservations:
                recent_activity.append({
                    "id": reservation.id,
                    "lot_name": reservation.spot.lot.prime_location_name,
                    "start_time": reservation.parking_timestamp.isoformat() if reservation.parking_timestamp else None,
                    "end_time": reservation.leaving_timestamp.isoformat() if reservation.leaving_timestamp else None,
                    "cost": reservation.parking_cost,
                    "status": "Completed" if reservation.leaving_timestamp else "Active"
                })
            
            analytics_data = {
                "user_id": user_id,
                "monthly_spending": [
                    {"month": month, "amount": round(amount, 2)}
                    for month, amount in sorted(monthly_spending.items())
                ],
                "favorite_lots": [
                    {"lot_name": lot, "usage_count": count}
                    for lot, count in sorted(lot_usage.items(), key=lambda x: x[1], reverse=True)[:5]
                ],
                "recent_activity": recent_activity,
                "total_reservations": len(reservations),
                "last_updated": datetime.utcnow().isoformat(),
                "from_cache": False
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, analytics_data, expiry=600)
            
            return analytics_data
            
        except Exception as e:
            return {"error": f"Failed to get analytics: {str(e)}"}, 500