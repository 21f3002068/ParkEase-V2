"""
Cached Admin API Routes for Performance
"""
from flask import request, jsonify
from flask_security import auth_required, roles_required
from flask_restx import Namespace, Resource
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from ..models import ParkingLot, ParkingSpot, Reservation, User, Payment
from .. import db
from ..utils.cache import cached, cache_key_for_admin, cache

cached_admin_ns = Namespace('cached_admin', description='Cached admin operations for performance')

@cached_admin_ns.route('/dashboard')
class CachedAdminDashboard(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get admin dashboard overview with caching"""
        cache_key = cache_key_for_admin("dashboard")
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return {**cached_data, "from_cache": True}
        
        try:
            # System overview statistics
            total_lots = db.session.query(ParkingLot).count()
            total_spots = db.session.query(ParkingSpot).count()
            total_users = db.session.query(User).count()
            
            # Occupancy statistics
            occupied_spots = db.session.query(ParkingSpot).filter_by(status='O').count()
            available_spots = db.session.query(ParkingSpot).filter_by(status='A').count()
            occupancy_rate = round((occupied_spots / total_spots) * 100, 1) if total_spots > 0 else 0
            
            # Revenue statistics (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_reservations = db.session.query(Reservation).filter(
                Reservation.parking_timestamp >= thirty_days_ago
            ).all()
            
            total_revenue = sum([r.parking_cost or 0 for r in recent_reservations])
            total_reservations = len(recent_reservations)
            
            # Active reservations
            active_reservations = db.session.query(Reservation).filter_by(leaving_timestamp=None).count()
            
            # Calculate net earnings from actual payments
            from backend.app.models.Payment import Payment
            net_earnings = db.session.query(
                func.sum(Payment.amount)
            ).filter(
                Payment.payment_status == 'completed'
            ).scalar() or 0
            
            dashboard_data = {
                "overview": {
                    "total_lots": total_lots,
                    "total_spots": total_spots,
                    "total_users": total_users,
                    "occupancy_rate": occupancy_rate,
                    "available_spots": available_spots,
                    "occupied_spots": occupied_spots,
                    "active_reservations": active_reservations,
                    "net_earnings": f"₹{round(float(net_earnings), 2)}"
                },
                "revenue": {
                    "last_30_days": round(total_revenue, 2),
                    "total_reservations": total_reservations,
                    "average_per_reservation": round(total_revenue / total_reservations, 2) if total_reservations > 0 else 0
                },
                "last_updated": datetime.utcnow().isoformat(),
                "from_cache": False
            }
            
            # Cache for 2 minutes
            cache.set(cache_key, dashboard_data, expiry=120)
            
            return dashboard_data
            
        except Exception as e:
            return {"error": f"Failed to get dashboard data: {str(e)}"}, 500

@cached_admin_ns.route('/analytics')
class CachedAdminAnalytics(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        """Get admin analytics with caching"""
        cache_key = cache_key_for_admin("analytics")
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return {**cached_data, "from_cache": True}
        
        try:
            # Revenue trend (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            daily_revenue = db.session.query(
                func.date(Reservation.parking_timestamp).label('date'),
                func.sum(Reservation.parking_cost).label('revenue')
            ).filter(
                Reservation.parking_timestamp >= thirty_days_ago,
                Reservation.parking_cost.isnot(None)
            ).group_by(func.date(Reservation.parking_timestamp)).all()
            
            revenue_chart = [
                {
                    "date": str(day.date),
                    "revenue": float(day.revenue or 0)
                }
                for day in daily_revenue
            ]
            
            # Parking lot utilization
            lot_utilization = db.session.query(
                ParkingLot.prime_location_name,
                ParkingLot.number_of_spots,
                func.count(ParkingSpot.id).filter(ParkingSpot.status == 'O').label('occupied')
            ).join(ParkingSpot).group_by(ParkingLot.id).all()
            
            utilization_chart = [
                {
                    "lot_name": lot.prime_location_name,
                    "capacity": lot.number_of_spots,
                    "occupied": lot.occupied,
                    "utilization_rate": round((lot.occupied / lot.number_of_spots) * 100, 1) if lot.number_of_spots > 0 else 0
                }
                for lot in lot_utilization
            ]
            
            # Daily activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            daily_activity = db.session.query(
                func.date(Reservation.parking_timestamp).label('date'),
                func.count(Reservation.id).label('reservations')
            ).filter(
                Reservation.parking_timestamp >= seven_days_ago
            ).group_by(func.date(Reservation.parking_timestamp)).all()
            
            activity_chart = [
                {
                    "date": str(day.date),
                    "reservations": day.reservations
                }
                for day in daily_activity
            ]
            
            # Top users (last 30 days)
            top_users = db.session.query(
                User.username,
                User.email,
                func.count(Reservation.id).label('total_bookings'),
                func.sum(Reservation.parking_cost).label('total_spent')
            ).join(Reservation).filter(
                Reservation.parking_timestamp >= thirty_days_ago
            ).group_by(User.id).order_by(desc('total_spent')).limit(10).all()
            
            top_users_data = [
                {
                    "username": user.username,
                    "email": user.email,
                    "total_bookings": user.total_bookings,
                    "total_spent": round(float(user.total_spent or 0), 2)
                }
                for user in top_users
            ]
            
            # Peak hours data (Average hourly distribution)
            peak_hours_query = db.session.query(
                func.extract('hour', Reservation.parking_timestamp).label('hour'),
                func.count(Reservation.id).label('count')
            ).group_by('hour').order_by('hour').all()

            peak_hours = [0] * 24
            for row in peak_hours_query:
                if row.hour is not None:
                    peak_hours[int(row.hour)] = row.count
            
            # Duration distribution (last 7 days)
            duration_buckets = {
                '<1 hour': 0,
                '1-2 hours': 0,
                '2-4 hours': 0,
                '4-8 hours': 0,
                '8+ hours': 0
            }
            
            completed_reservations = Reservation.query.filter(
                Reservation.leaving_timestamp.isnot(None),
                Reservation.leaving_timestamp >= seven_days_ago
            ).all()
            
            for reservation in completed_reservations:
                if reservation.parking_timestamp and reservation.leaving_timestamp:
                    duration_hours = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600
                    
                    if duration_hours < 1:
                        duration_buckets['<1 hour'] += 1
                    elif duration_hours < 2:
                        duration_buckets['1-2 hours'] += 1
                    elif duration_hours < 4:
                        duration_buckets['2-4 hours'] += 1
                    elif duration_hours < 8:
                        duration_buckets['4-8 hours'] += 1
                    else:
                        duration_buckets['8+ hours'] += 1
            
            duration_distribution = list(duration_buckets.values())
            
            # Status distribution
            status_counts = db.session.query(
                Reservation.status,
                func.count(Reservation.id).label('count')
            ).group_by(Reservation.status).all()
            
            status_map = {
                'Pending': 0,
                'Confirmed': 0,
                'Parked': 0,
                'Parked Out': 0,
                'Cancelled/Rejected': 0
            }
            
            for status, count in status_counts:
                if status in ['Pending']:
                    status_map['Pending'] += count
                elif status in ['Confirmed']:
                    status_map['Confirmed'] += count
                elif status in ['Parked', 'Active']:
                    status_map['Parked'] += count
                elif status in ['Parked Out', 'Completed']:
                    status_map['Parked Out'] += count
                elif status in ['Cancelled', 'Rejected']:
                    status_map['Cancelled/Rejected'] += count
            
            status_distribution = list(status_map.values())
            
            # Overview statistics
            total_lots = ParkingLot.query.count()
            total_spots = db.session.query(func.sum(ParkingLot.number_of_spots)).scalar() or 0
            occupied_spots = ParkingSpot.query.filter_by(status='O').count()
            available_spots = total_spots - occupied_spots
            occupancy_rate = round((occupied_spots / total_spots * 100), 1) if total_spots > 0 else 0
            total_users = User.query.count()
            
            # Calculate net earnings from actual payments
            from backend.app.models.Payment import Payment
            net_earnings = db.session.query(
                func.sum(Payment.amount)
            ).filter(
                Payment.payment_status == 'completed'
            ).scalar() or 0
            
            overview = {
                "total_lots": total_lots,
                "total_spots": total_spots,
                "available_spots": available_spots,
                "occupancy_rate": occupancy_rate,
                "total_users": total_users,
                "net_earnings": f"₹{round(float(net_earnings), 2)}"
            }
            
            analytics_data = {
                "overview": overview,
                "revenue_chart": revenue_chart,
                "lot_utilization": utilization_chart,
                "daily_activity": activity_chart,
                "top_users": top_users_data,
                "peak_hours": peak_hours,
                "duration_distribution": duration_distribution,
                "status_distribution": status_distribution,
                "summary": {
                    "total_revenue_30d": sum([day["revenue"] for day in revenue_chart]),
                    "avg_daily_reservations": round(sum([day["reservations"] for day in activity_chart]) / len(activity_chart), 1) if activity_chart else 0,
                    "most_utilized_lot": max(utilization_chart, key=lambda x: x["utilization_rate"])["lot_name"] if utilization_chart else "N/A"
                },
                "last_updated": datetime.utcnow().isoformat(),
                "from_cache": False
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, analytics_data, expiry=300)
            
            return analytics_data
            
        except Exception as e:
            return {"error": f"Failed to get analytics: {str(e)}"}, 500

@cached_admin_ns.route('/lots/summary')
class CachedLotsummary(Resource):
    @auth_required('token')
    @roles_required('admin')
    @cached(expiry=240, key_prefix="admin_lots_summary")  # Cache for 4 minutes
    def get(self):
        """Get parking lots summary with performance metrics"""
        try:
            lots = db.session.query(ParkingLot).all()
            
            lots_summary = []
            for lot in lots:
                # Get spot statistics
                spots = db.session.query(ParkingSpot).filter_by(lot_id=lot.id)
                total_spots = spots.count()
                available = spots.filter_by(status='A').count()
                occupied = spots.filter_by(status='O').count()
                booked = spots.filter_by(status='B').count()
                
                # Get revenue (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                revenue = db.session.query(func.sum(Reservation.parking_cost)).join(ParkingSpot).filter(
                    ParkingSpot.lot_id == lot.id,
                    Reservation.parking_timestamp >= thirty_days_ago,
                    Reservation.parking_cost.isnot(None)
                ).scalar() or 0
                
                # Get reservation count
                reservations_count = db.session.query(Reservation).join(ParkingSpot).filter(
                    ParkingSpot.lot_id == lot.id,
                    Reservation.parking_timestamp >= thirty_days_ago
                ).count()
                
                lots_summary.append({
                    "id": lot.id,
                    "name": lot.prime_location_name,
                    "address": lot.address,
                    "capacity": total_spots,
                    "available": available,
                    "occupied": occupied,
                    "booked": booked,
                    "occupancy_rate": round((occupied / total_spots) * 100, 1) if total_spots > 0 else 0,
                    "revenue_30d": round(float(revenue), 2),
                    "reservations_30d": reservations_count,
                    "avg_revenue_per_reservation": round(float(revenue) / reservations_count, 2) if reservations_count > 0 else 0,
                    "price_per_hour": lot.price
                })
            
            return {
                "lots": lots_summary,
                "total_lots": len(lots_summary),
                "system_summary": {
                    "total_capacity": sum([lot["capacity"] for lot in lots_summary]),
                    "total_available": sum([lot["available"] for lot in lots_summary]),
                    "total_occupied": sum([lot["occupied"] for lot in lots_summary]),
                    "system_occupancy": round((sum([lot["occupied"] for lot in lots_summary]) / sum([lot["capacity"] for lot in lots_summary])) * 100, 1) if sum([lot["capacity"] for lot in lots_summary]) > 0 else 0,
                    "total_revenue_30d": sum([lot["revenue_30d"] for lot in lots_summary])
                },
                "cached_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to get lots summary: {str(e)}"}, 500