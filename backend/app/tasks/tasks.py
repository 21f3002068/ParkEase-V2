# backend/app/tasks/tasks.py
"""
Consolidated Celery tasks for ParkEase
Handles all scheduled and async jobs
"""

import os
import glob
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from backend.celery_app import celery_app
from backend.app.models import User, ParkingLot, Reservation, ParkingSpot, Vehicle
from backend.app import db
from sqlalchemy import func, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / '.env'
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


def _send_admin_reservations_export_email(admin_email, filename, download_url, total_records):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
    sender_password = os.getenv('SENDER_PASSWORD', '')

    if not sender_password:
        return {"error": "Email configuration not set up"}

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = admin_email
        msg['Subject'] = f"📊 ParkEase Reservation Export Ready - {filename}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 20px auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1a237e 0%, #283593 100%); color: white; padding: 40px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 26px; }}
                .content {{ padding: 30px 20px; }}
                .info-box {{ background-color: #f4f6ff; border-left: 4px solid #1a237e; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                .info-item {{ margin: 10px 0; font-size: 15px; color: #333; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #1a237e 0%, #303f9f 100%); color: white; padding: 15px 35px; text-decoration: none; border-radius: 30px; font-weight: bold; margin: 30px 0; }}
                .footer {{ background-color: #f5f5f5; padding: 20px; text-align: center; color: #666; font-size: 13px; }}
                .download-link {{ color: #1a237e; word-break: break-all; }}
            </style>
        </head>
        <body>
            <div class=\"container\">
                <div class=\"header\">
                    <h1>Reservation Export Ready</h1>
                    <p>Your CSV file is ready for download</p>
                </div>
                <div class=\"content\">
                    <p>Hi Admin,</p>
                    <p>Your reservation history export has been generated successfully. Use the button below to download the CSV file.</p>
                    <div class=\"info-box\">
                        <div class=\"info-item\"><strong>Filename:</strong> {filename}</div>
                        <div class=\"info-item\"><strong>Total records:</strong> {total_records}</div>
                        <div class=\"info-item\"><strong>Generated:</strong> {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</div>
                    </div>
                    <div style=\"text-align:center;\">
                        <a href=\"{download_url}\" class=\"cta-button\">Download CSV</a>
                    </div>
                    <p>If the button above doesn't work, copy and paste this link into your browser:</p>
                    <p class=\"download-link\">{download_url}</p>
                </div>
                <div class=\"footer\">
                    <p><strong>ParkEase Admin Console</strong></p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        return {"success": True, "message": f"Reservation export email sent to {admin_email}"}
    except Exception as exc:
        return {"error": f"Failed to send email: {exc}", "success": False}



# ============================================================================
# 1. DAILY REMINDERS - Send to users via Google Chat/Email
# ============================================================================

@celery_app.task(ignore_result=False, name='send_daily_reminders', bind=True)
def send_daily_reminders(self):
    """
    Send daily reminders to inactive users via Google Chat or Email
    
    Criteria:
    - Users who haven't made a reservation in last 7 days
    - OR new parking lots were created by admin
    
    Priority: Google Chat → Email fallback
    """
    from backend.app.utils.task_logger import log_task
    
    print("\n" + "="*60)
    print("SEND_DAILY_REMINDERS TASK STARTED")
    print("="*60)
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', 'Task started')
        try:
            from backend.app.utils.google_chat import send_parking_reminder
            from backend.app.utils.emails import send_reminder_email
            
            # Find inactive users (no reservations in 2 minutes for TESTING)
            # TODO: Change back to 7 days for production
            two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
            
            inactive_users = db.session.query(User).filter(
                User.roles.any(name='user'),
                User.active == True,
                ~User.id.in_(
                    db.session.query(Reservation.user_id).filter(
                        Reservation.booking_timestamp >= two_minutes_ago
                    ).distinct()
                )
            ).all()
            
            # Get top 3 parking lots with most available spots
            top_lots = db.session.query(ParkingLot).join(ParkingSpot).filter(
                ParkingSpot.status == 'A'
            ).group_by(ParkingLot.id).order_by(
                func.count(ParkingSpot.id).desc()
            ).limit(3).all()
            
            new_lot_names = [lot.prime_location_name or lot.location for lot in top_lots] if top_lots else []
            
            # Get available spots
            available_spots = ParkingSpot.query.filter_by(status='A').count()
            
            # Send reminders
            google_chat_sent = 0
            email_sent = 0
            failed = 0
            
            for user in inactive_users:
                user_name = user.first_name or user.username
                
                # Try Google Chat first if webhook configured
                if user.google_chat_webhook:
                    try:
                        result = send_parking_reminder(
                            webhook_url=user.google_chat_webhook,
                            user_name=user_name,
                            available_spots=available_spots,
                            new_lots=new_lot_names if new_lot_names else None
                        )
                        
                        if result.get('success'):
                            google_chat_sent += 1
                        else:
                            # Fallback to email
                            if user.email:
                                send_reminder_email(user, available_spots, new_lot_names)
                                email_sent += 1
                    except Exception as e:
                        print(f"Error sending to {user.email}: {e}")
                        failed += 1
                
                # Send email if no webhook
                elif user.email:
                    try:
                        send_reminder_email(user, available_spots, new_lot_names)
                        email_sent += 1
                    except Exception as e:
                        print(f"Error sending email to {user.email}: {e}")
                        failed += 1
            
            result = {
                "status": "success",
                "inactive_users": len(inactive_users),
                "google_chat_sent": google_chat_sent,
                "email_sent": email_sent,
                "failed": failed,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_task(self.name, 'success', f'Task completed. Sent {google_chat_sent} Google Chat messages and {email_sent} emails.', result)
            
            print("\n" + "="*60)
            print("TASK COMPLETED SUCCESSFULLY")
            print(f"Inactive users: {len(inactive_users)}")
            print(f"Google Chat sent: {google_chat_sent}")
            print(f"Email sent: {email_sent}")
            print(f"Failed: {failed}")
            print("="*60 + "\n")
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_task(self.name, 'error', str(e), error_result)
            
            print("\n" + "="*60)
            print("TASK FAILED")
            print(f"Error: {e}")
            print("="*60 + "\n")
            
            return error_result


# ============================================================================
# 2. MONTHLY ACTIVITY REPORT - HTML report via email
# ============================================================================

@celery_app.task(ignore_result=False, name='send_monthly_reports', bind=True)
def send_monthly_reports(self):
    """
    Generate and send monthly activity reports to all users
    
    Report includes:
    - Parking spots booked per month
    - Most used parking lot
    - Amount spent on parking
    - Other relevant statistics
    
    Runs on 1st day of every month
    """
    from backend.app.utils.task_logger import log_task

    print("\n" + "="*60)
    print("SEND_MONTHLY_REPORTS TASK STARTED")
    print("="*60)
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', 'Task started')
        try:
            from backend.app.utils.emails import send_monthly_report_email
            
            # Get all active users
            users = db.session.query(User).filter_by(active=True).filter(
                User.roles.any(name='user')
            ).all()
            
            # Calculate date range for the previous calendar month
            today = datetime.utcnow()
            first_day_current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = first_day_current_month - timedelta(microseconds=1)
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            reports_sent = 0
            reports_failed = 0
            
            for user in users:
                try:
                    # Generate report data for this user
                    report_data = _generate_user_monthly_report(
                        user, 
                        start_date, 
                        end_date
                    )
                    
                    # Send email
                    if user.email:
                        result = send_monthly_report_email(report_data, [user.email])
                        if result.get('success'):
                            reports_sent += 1
                            print(f"✓ Report sent to {user.email}")
                        else:
                            reports_failed += 1
                            print(f"✗ Failed to send to {user.email}: {result.get('error')}")
                    else:
                        print(f"⚠ No email for user {user.username}")
                            
                except Exception as e:
                    print(f"Error generating report for {user.email}: {e}")
                    reports_failed += 1
            
            result = {
                "status": "success",
                "reports_sent": reports_sent,
                "reports_failed": reports_failed,
                "total_users": len(users),
                "report_period": "Previous Month",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_task(self.name, 'success', f'Task completed. Sent {reports_sent} reports.', result)

            print("\n" + "="*60)
            print("TASK COMPLETED SUCCESSFULLY")
            print(f"Total users: {len(users)}")
            print(f"Reports sent: {reports_sent}")
            print(f"Reports failed: {reports_failed}")
            print("="*60 + "\n")
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_task(self.name, 'error', str(e), error_result)
            
            print("\n" + "="*60)
            print("TASK FAILED")
            print(f"Error: {e}")
            print("="*60 + "\n")
            
            return error_result


def _generate_user_monthly_report(user, start_date, end_date):
    """Generate monthly report data for a specific user"""
    
    # Get user's reservations for the period
    reservations = db.session.query(Reservation).filter(
        Reservation.user_id == user.id,
        Reservation.booking_timestamp >= start_date,
        Reservation.booking_timestamp <= end_date
    ).order_by(Reservation.booking_timestamp.desc()).all()
    
    # Calculate statistics
    total_bookings = len(reservations)
    total_spent = sum(r.parking_cost or 0 for r in reservations)
    
    # Most used parking lot
    lot_usage = {}
    for r in reservations:
        if r.spot and r.spot.lot:
            lot_name = r.spot.lot.prime_location_name or r.spot.lot.location
            lot_usage[lot_name] = lot_usage.get(lot_name, 0) + 1
    
    most_used_lot = max(lot_usage.items(), key=lambda x: x[1]) if lot_usage else ("None", 0)
    
    # Average session duration (only for completed reservations)
    completed_reservations = [r for r in reservations if r.leaving_timestamp and r.parking_timestamp]
    if completed_reservations:
        total_duration = sum(
            abs((r.leaving_timestamp - r.parking_timestamp).total_seconds() / 3600)
            for r in completed_reservations
        )
        avg_duration = total_duration / len(completed_reservations)
    else:
        avg_duration = 0
    
    # Format reservation list
    reservation_list = []
    for r in reservations[:10]:  # Top 10 recent
        lot_name = "Unknown"
        if r.spot and r.spot.lot:
            lot_name = r.spot.lot.prime_location_name or r.spot.lot.location
        
        duration = "Ongoing"
        if r.leaving_timestamp and r.parking_timestamp:
            hours = abs((r.leaving_timestamp - r.parking_timestamp).total_seconds() / 3600)
            duration = f"{hours:.1f}h"
        
        cost = f"₹{r.parking_cost:.2f}" if r.parking_cost else "₹0.00"
        
        reservation_list.append({
            "date": r.booking_timestamp.strftime('%Y-%m-%d'),
            "lot": lot_name,
            "duration": duration,
            "cost": cost
        })
    
    return {
        "user_name": f"{user.first_name} {user.last_name}" if user.first_name else user.username,
        "user_email": user.email,
        "report_period": f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_bookings": total_bookings,
            "total_spent": round(total_spent, 2),
            "most_used_lot": most_used_lot[0],
            "most_used_lot_count": most_used_lot[1],
            "avg_session_duration_hours": round(avg_duration, 2)
        },
        "reservations": reservation_list
    }


# ============================================================================
# 3. EXPORT AS CSV - User-triggered async job
# ============================================================================

@celery_app.task(ignore_result=False, name='export_user_csv', bind=True)
def export_user_csv(self, user_id):
    """
    Export user's parking history as CSV
    
    User-triggered async job that:
    1. Generates CSV with all parking details
    2. Saves to static folder
    3. Sends email to user with download link
    
    CSV includes: slot_id, spot_id, timestamps, cost, remarks, etc.
    """
    from backend.app.utils.task_logger import log_task
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', f'Task started for user {user_id}', triggered_by='user')

        try:
            import csv
            
            user = User.query.get(user_id)
            if not user:
                log_task(self.name, 'error', f'User {user_id} not found', triggered_by='user')
                return {"status": "error", "error": "User not found"}
            
            if not user.email:
                log_task(self.name, 'error', f'User {user_id} email not found', triggered_by='user')
                return {"status": "error", "error": "User email not found"}
            
            # Get all user reservations
            reservations = Reservation.query.filter_by(user_id=user_id).order_by(
                Reservation.booking_timestamp.desc()
            ).all()
            
            # Generate CSV filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"parking_history_{user_id}_{timestamp}.csv"
            static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static')
            os.makedirs(static_dir, exist_ok=True)
            filepath = os.path.join(static_dir, filename)
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Booking ID', 'Lot Name', 'Spot Number', 'Vehicle Number',
                    'Booking Time', 'Arrival Time', 'Departure Time',
                    'Duration (hours)', 'Cost (₹)', 'Status', 'Remarks'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for r in reservations:
                    duration = None
                    if r.parking_timestamp and r.leaving_timestamp:
                        duration = round((r.leaving_timestamp - r.parking_timestamp).total_seconds() / 3600, 2)
                    
                    # Get vehicle info
                    vehicle_number = "N/A"
                    if r.vehicle_id:
                        vehicle = Vehicle.query.get(r.vehicle_id)
                        if vehicle:
                            vehicle_number = vehicle.vehicle_number
                    
                    writer.writerow({
                        'Booking ID': f"BOOK-{r.id}",
                        'Lot Name': r.spot.lot.prime_location_name if r.spot and r.spot.lot else "N/A",
                        'Spot Number': r.spot.spot_number if r.spot else "N/A",
                        'Vehicle Number': vehicle_number,
                        'Booking Time': r.booking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.booking_timestamp else "N/A",
                        'Arrival Time': r.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.parking_timestamp else "Not arrived",
                        'Departure Time': r.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.leaving_timestamp else "Not departed",
                        'Duration (hours)': duration if duration else "N/A",
                        'Cost (₹)': f"{r.parking_cost:.2f}" if r.parking_cost else "0.00",
                        'Status': r.status or "Unknown",
                        'Remarks': ""
                    })
            
            # Send email to user with download link
            from backend.app.utils.emails import send_user_csv_export_email
            
            download_url = f"http://localhost:5000/static/{filename}"
            email_result = send_user_csv_export_email(user.email, user.first_name or user.username, filename, download_url, len(reservations))
            
            result = {
                "status": "success",
                "message": "Parking history CSV generated and email sent",
                "filename": filename,
                "file_path": f"/static/{filename}",
                "download_url": download_url,
                "total_records": len(reservations),
                "email_sent": email_result.get('success', False),
                "email_message": email_result.get('message', ''),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'success', f'Task completed for user {user_id}', result, triggered_by='user')
            return result
            
        except Exception as e:
            import traceback
            error_result = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'error', str(e), error_result, triggered_by='user')
            return error_result


@celery_app.task(ignore_result=False, name='system_health_check', bind=True)
def system_health_check(self):
    """Perform lightweight diagnostics for the admin dashboard"""
    from backend.app.utils.task_logger import log_task
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', 'Task started')
        try:
            db_status = "ok"
            try:
                db.session.execute(text('SELECT 1'))
            except Exception as db_err:
                db_status = f"error: {db_err}"

            overview = {
                "users": User.query.count(),
                "active_users": User.query.filter_by(active=True).count(),
                "parking_lots": ParkingLot.query.count(),
                "parking_spots": ParkingSpot.query.count(),
                "active_reservations": Reservation.query.filter(
                    Reservation.status.in_(['Parked', 'Active']),
                    Reservation.leaving_timestamp.is_(None)
                ).count()
            }

            available_spots = ParkingSpot.query.filter_by(status='A').count()
            occupied_spots = ParkingSpot.query.filter_by(status='O').count()
            booked_spots = ParkingSpot.query.filter_by(status='B').count()
            total_spots = overview["parking_spots"] or 1
            utilization = ((occupied_spots + booked_spots) / total_spots) * 100

            summary = []
            if db_status != "ok":
                summary.append("Database connectivity issues detected")
            if utilization > 90:
                summary.append("Parking utilization above 90% - nearing capacity")
            if overview["active_reservations"] == 0:
                summary.append("No active reservations detected")
            if not summary:
                summary_text = "All core systems healthy"
            else:
                summary_text = "; ".join(summary)

            result = {
                "status": "success" if db_status == "ok" and utilization <= 90 else "warning",
                "summary": summary_text,
                "db": db_status,
                "utilization_percent": round(utilization, 2),
                "overview": overview,
                "spot_distribution": {
                    "available": available_spots,
                    "occupied": occupied_spots,
                    "booked": booked_spots
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'success', 'Task completed', result)
            return result
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'error', str(e), error_result)
            return error_result


@celery_app.task(ignore_result=False, name='daily_update', bind=True)
def daily_update(self):
    """Run daily maintenance helpers (cleanup files + release expired)"""
    from backend.app.utils.task_logger import log_task
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', 'Task started')
        try:
            cleanup_result = cleanup_old_csv_files()
            release_result = auto_release_expired_reservations()

            result = {
                "status": "success",
                "csv_cleanup": cleanup_result,
                "auto_release": release_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'success', 'Task completed', result)
            return result
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'error', str(e), error_result)
            return error_result


# ============================================================================
# 4. CLEANUP TASKS - Maintenance
# ============================================================================

@celery_app.task(ignore_result=False, name='cleanup_old_csv_files', bind=True)
def cleanup_old_csv_files(self):
    """Clean up ALL CSV and PDF files from static directory immediately"""
    from backend.app.utils.task_logger import log_task
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', 'Task started')
        try:
            static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static')
            if not os.path.exists(static_dir):
                log_task(self.name, 'success', 'No static directory found')
                return {"status": "No static directory found"}
            
            deleted_files = []
            
            # Delete ALL CSV files
            csv_files = glob.glob(os.path.join(static_dir, '*.csv'))
            for file_path in csv_files:
                try:
                    os.remove(file_path)
                    deleted_files.append(os.path.basename(file_path))
                    print(f"Deleted: {os.path.basename(file_path)}")
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}")
            
            # Delete ALL PDF files
            pdf_files = glob.glob(os.path.join(static_dir, '*.pdf'))
            for file_path in pdf_files:
                try:
                    os.remove(file_path)
                    deleted_files.append(os.path.basename(file_path))
                    print(f"Deleted: {os.path.basename(file_path)}")
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}")
            
            result = {
                "status": "success",
                "deleted_count": len(deleted_files),
                "deleted_files": deleted_files,
                "cleanup_type": "immediate_all_files",
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'success', f'Task completed. Deleted {len(deleted_files)} files (CSV and PDF).', result)
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'error', str(e), error_result)
            return error_result


@celery_app.task(ignore_result=False, name='export_admin_users_csv', bind=True)
def export_admin_users_csv(self, admin_email):
    """
    Export all user data as CSV for admin
    
    Admin-triggered async job that:
    1. Generates CSV with all user data
    2. Saves to static folder
    3. Sends email to admin with download link
    
    CSV includes: user_id, email, username, name, status, roles, created_at, 
                  total_reservations, total_vehicles, etc.
    """
    from backend.app.utils.task_logger import log_task
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', f'Task started by {admin_email}', triggered_by='admin')
        try:
            import csv
            
            now = datetime.utcnow()
            
            # Get all users
            users = User.query.all()
            
            # Generate CSV filename
            timestamp = now.strftime('%Y%m%d_%H%M%S')
            filename = f"users_export_{timestamp}.csv"
            static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static')
            os.makedirs(static_dir, exist_ok=True)
            filepath = os.path.join(static_dir, filename)
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'User ID', 'Email', 'Username', 'First Name', 'Last Name',
                    'Phone Number', 'Address', 'Pincode', 'Active', 'Flagged',
                    'Roles', 'Created At', 'Total Reservations', 'Total Vehicles',
                    'Total Spent (₹)'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for user in users:
                    # Get user statistics
                    total_reservations = Reservation.query.filter_by(user_id=user.id).count()
                    total_vehicles = Vehicle.query.filter_by(user_id=user.id).count()
                    total_spent = db.session.query(func.coalesce(func.sum(Reservation.parking_cost), 0)).filter(
                        Reservation.user_id == user.id
                    ).scalar() or 0
                    
                    # Get roles
                    roles = ', '.join([role.name for role in user.roles]) if user.roles else 'user'
                    
                    writer.writerow({
                        'User ID': user.id,
                        'Email': user.email or '',
                        'Username': user.username or '',
                        'First Name': user.first_name or '',
                        'Last Name': user.last_name or '',
                        'Phone Number': getattr(user, 'phone_number', '') or '',
                        'Address': getattr(user, 'address', '') or '',
                        'Pincode': getattr(user, 'pincode', '') or '',
                        'Active': 'Yes' if user.active else 'No',
                        'Flagged': 'Yes' if getattr(user, 'is_flagged', False) else 'No',
                        'Roles': roles,
                        'Created At': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                        'Total Reservations': total_reservations,
                        'Total Vehicles': total_vehicles,
                        'Total Spent (₹)': f"{total_spent:.2f}"
                    })
            
            # Send email to admin with download link
            from backend.app.utils.emails import send_admin_csv_export_email
            
            download_url = f"http://localhost:5000/static/{filename}"
            email_result = send_admin_csv_export_email(admin_email, filename, download_url)
            
            result = {
                "status": "success" if email_result.get('success') else "warning",
                "message": "User data CSV generated and email notification sent" if email_result.get('success') else "CSV generated but email could not be sent",
                "filename": filename,
                "file_path": f"/static/{filename}",
                "download_url": download_url,
                "email_sent": email_result.get('success', False),
                "email_message": email_result.get('message', '') or email_result.get('error', ''),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'success', f'Task completed. Exported {len(users)} users.', result, triggered_by='admin')
            return result

        except Exception as e:
            import traceback
            error_result = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'error', str(e), error_result, triggered_by='admin')
            return error_result


@celery_app.task(ignore_result=False, name='export_admin_reservations_csv', bind=True)
def export_admin_reservations_csv(self, admin_email, status_filter=None):
    """Export all reservations data as CSV for admin"""
    from backend.app.utils.task_logger import log_task
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', f'Task started by {admin_email}', triggered_by='admin')
        try:
            import csv

            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"reservations_export_{timestamp}.csv"
            static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static')
            os.makedirs(static_dir, exist_ok=True)
            filepath = os.path.join(static_dir, filename)

            query = Reservation.query.order_by(Reservation.booking_timestamp.desc())
            if status_filter and status_filter.lower() != 'all':
                query = query.filter(Reservation.status.ilike(status_filter))

            reservations = query.all()

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Reservation ID', 'User Name', 'User Email', 'Parking Lot', 'Spot Number',
                    'Vehicle', 'Booking Time', 'Check-in', 'Check-out', 'Duration (hours)',
                    'Status', 'Cost (₹)'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for reservation in reservations:
                    # Fetch related objects using foreign keys
                    user = User.query.get(reservation.user_id) if reservation.user_id else None
                    spot = reservation.spot
                    lot = spot.lot if spot else None
                    vehicle = Vehicle.query.get(reservation.vehicle_id) if reservation.vehicle_id else None

                    duration = None
                    if reservation.parking_timestamp and reservation.leaving_timestamp:
                        duration = round((reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600, 2)

                    writer.writerow({
                        'Reservation ID': reservation.id,
                        'User Name': f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip() if user else 'Unknown',
                        'User Email': user.email if user else '',
                        'Parking Lot': lot.prime_location_name if lot else 'N/A',
                        'Spot Number': spot.spot_number if spot else 'N/A',
                        'Vehicle': vehicle.vehicle_number if vehicle else 'N/A',
                        'Booking Time': reservation.booking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if reservation.booking_timestamp else 'N/A',
                        'Check-in': reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if reservation.parking_timestamp else 'N/A',
                        'Check-out': reservation.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if reservation.leaving_timestamp else 'N/A',
                        'Duration (hours)': duration if duration is not None else 'N/A',
                        'Status': reservation.status or 'Unknown',
                        'Cost (₹)': f"{reservation.parking_cost or 0:.2f}"
                    })

            from backend.app.utils.emails import send_admin_reservations_export_email

            download_url = f"http://localhost:5000/static/{filename}"
            email_result = send_admin_reservations_export_email(admin_email, filename, download_url, len(reservations))

            result = {
                "status": "success" if email_result.get('success') else "warning",
                "message": "Reservation CSV generated and email notification sent" if email_result.get('success') else "Reservation CSV generated but email could not be sent",
                "filename": filename,
                "file_path": f"/static/{filename}",
                "download_url": download_url,
                "total_records": len(reservations),
                "email_sent": email_result.get('success', False),
                "email_message": email_result.get('message', '') or email_result.get('error', ''),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'success', f'Task completed. Exported {len(reservations)} reservations.', result, triggered_by='admin')
            return result

        except Exception as e:
            import traceback
            error_result = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'error', str(e), error_result, triggered_by='admin')
            return error_result


@celery_app.task(ignore_result=False, name='auto_release_expired_reservations', bind=True)
def auto_release_expired_reservations(self):
    """Auto-release reservations that have been parked for more than 24 hours"""
    from backend.app.utils.task_logger import log_task
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', 'Task started')
        try:
            expired_cutoff = datetime.utcnow() - timedelta(hours=24)
            
            expired_reservations = Reservation.query.filter(
                Reservation.leaving_timestamp.is_(None),
                Reservation.parking_timestamp < expired_cutoff
            ).all()
            
            released_count = 0
            for reservation in expired_reservations:
                reservation.leaving_timestamp = datetime.utcnow()
                duration_hours = 24
                reservation.parking_cost = round(duration_hours * reservation.spot.lot.price, 2)
                reservation.spot.status = 'A'
                released_count += 1
            
            if released_count > 0:
                db.session.commit()
            
            result = {
                "status": "success",
                "released_count": released_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'success', f'Task completed. Released {released_count} reservations.', result)
            return result
            
        except Exception as e:
            db.session.rollback()
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            log_task(self.name, 'error', str(e), error_result)
            return error_result



@celery_app.task(ignore_result=False, name='send_payment_reminders', bind=True)
def send_payment_reminders(self):
    """
    Send payment reminder emails to users with unpaid parking sessions
    Runs daily to remind users about pending payments after 24 hours
    """
    from backend.app.utils.task_logger import log_task
    from backend.app.utils.emails import send_payment_reminder_email
    from backend.app.models.Payment import Payment
    
    print("\n" + "="*60)
    print("SEND_PAYMENT_REMINDERS TASK STARTED")
    print("="*60)
    
    # Create Flask app context
    from backend.app import create_app
    app = create_app()
    
    with app.app_context():
        log_task(self.name, 'running', 'Task started')
        try:
            # Find all "Parked Out" reservations without payment
            # that are older than 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Get all parked out reservations
            unpaid_reservations = Reservation.query.filter(
                Reservation.status == 'Parked Out',
                Reservation.leaving_timestamp.isnot(None),
                Reservation.leaving_timestamp < cutoff_time
            ).all()
            
            reminders_sent = 0
            reminders_failed = 0
            
            for reservation in unpaid_reservations:
                # Check if payment exists
                payment = Payment.query.filter_by(reservation_id=reservation.id).first()
                
                if not payment:  # No payment found
                    # Get user
                    user = User.query.get(reservation.user_id)
                    
                    if user and user.email:
                        try:
                            result = send_payment_reminder_email(
                                user=user,
                                reservation=reservation,
                                amount=reservation.parking_cost or 0
                            )
                            
                            if result.get('success'):
                                reminders_sent += 1
                                print(f"✓ Reminder sent to {user.email} for booking {reservation.booking_id}")
                            else:
                                reminders_failed += 1
                                print(f"✗ Failed to send to {user.email}: {result.get('error')}")
                        except Exception as e:
                            reminders_failed += 1
                            print(f"✗ Error sending to {user.email}: {str(e)}")
            
            result = {
                "status": "success",
                "reminders_sent": reminders_sent,
                "reminders_failed": reminders_failed,
                "total_unpaid": len(unpaid_reservations),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_task(self.name, 'success', f'Task completed. Sent {reminders_sent} payment reminders.', result)
            
            print("\n" + "="*60)
            print("TASK COMPLETED SUCCESSFULLY")
            print(f"Total unpaid reservations: {len(unpaid_reservations)}")
            print(f"Reminders sent: {reminders_sent}")
            print(f"Reminders failed: {reminders_failed}")
            print("="*60 + "\n")
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_task(self.name, 'error', str(e), error_result)
            
            print("\n" + "="*60)
            print("TASK FAILED")
            print(f"Error: {e}")
            print("="*60 + "\n")
            
            return error_result
