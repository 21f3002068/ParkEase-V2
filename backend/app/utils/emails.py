# backend/app/utils/emails.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Ensure we always load the backend/.env file, even when the process is started
# from the repository root (e.g., Celery worker/beat).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / '.env'
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # Fall back to default lookup so user-level environment variables still work.
    load_dotenv()

def send_monthly_report_email(report_data, recipient_emails=None):
    """
    Send monthly report via email to administrators
    
    Args:
        report_data: Dictionary containing the monthly report data
        recipient_emails: List of email addresses to send to (defaults to admin emails)
    """
    
    class task_config:
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
        ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', 'admin@parkease.com').split(',')
    
    # Default admin emails from config
    if recipient_emails is None:
        recipient_emails = task_config.ADMIN_EMAILS
    
    # Use unified config values
    smtp_server = task_config.SMTP_SERVER
    smtp_port = task_config.SMTP_PORT
    sender_email = task_config.SENDER_EMAIL
    sender_password = task_config.SENDER_PASSWORD
    
    if not sender_password:
        return {"error": "Email configuration not set up"}
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = f"🚗 Your ParkEase Monthly Report - {report_data['report_period']}"
        
        # Create HTML email body
        html_body = generate_report_html(report_data)
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach JSON report as file
        json_report = json.dumps(report_data, indent=2, default=str)
        attachment = MIMEBase('application', 'json')
        attachment.set_payload(json_report.encode())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="monthly_report_{report_data["report_period"].replace(" ", "_")}.json"'
        )
        msg.attach(attachment)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return {"success": f"Monthly report sent to {len(recipient_emails)} recipients"}
        
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}


def generate_report_html(report_data):
    """Generate HTML email body for the monthly report"""
    
    summary = report_data.get('summary', {})
    reservations = report_data.get('reservations', [])
    user_name = report_data.get('user_name', 'User')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: white; }}
            .header {{ background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white; padding: 30px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
            .greeting {{ padding: 20px; font-size: 16px; color: #333; }}
            .metrics {{ display: flex; flex-wrap: wrap; padding: 10px 20px; }}
            .metric {{ flex: 1; min-width: 120px; text-align: center; padding: 15px; margin: 10px; background-color: #f9f9f9; border-radius: 8px; }}
            .metric-value {{ font-size: 32px; font-weight: bold; color: #1976d2; margin-bottom: 5px; }}
            .metric-label {{ font-size: 13px; color: #666; text-transform: uppercase; }}
            .section {{ padding: 20px; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 15px; border-bottom: 2px solid #1976d2; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background-color: #f5f5f5; padding: 10px; text-align: left; font-size: 12px; color: #666; text-transform: uppercase; }}
            td {{ padding: 10px; border-bottom: 1px solid #eee; font-size: 14px; }}
            .footer {{ background-color: #f9f9f9; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            .highlight {{ background-color: #fff3cd; padding: 15px; margin: 10px 20px; border-radius: 8px; border-left: 4px solid #ffc107; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 Your Monthly Parking Report</h1>
                <p>{report_data.get('report_period', 'N/A')}</p>
            </div>
            
            <div class="greeting">
                <p>Hi <strong>{user_name}</strong>,</p>
                <p>Here's your parking activity summary for the past month!</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{summary.get('total_bookings', 0)}</div>
                    <div class="metric-label">Total Bookings</div>
                </div>
                <div class="metric">
                    <div class="metric-value">₹{summary.get('total_spent', 0):.0f}</div>
                    <div class="metric-label">Amount Spent</div>
                </div>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{summary.get('avg_session_duration_hours', 0):.1f}h</div>
                    <div class="metric-label">Avg Duration</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary.get('most_used_lot_count', 0)}</div>
                    <div class="metric-label">Favorite Lot Visits</div>
                </div>
            </div>
            
            <div class="highlight">
                <strong>🏆 Your Favorite Parking Spot:</strong><br>
                {summary.get('most_used_lot', 'None')} ({summary.get('most_used_lot_count', 0)} visits)
            </div>
    """
    
    if reservations:
        html += """
            <div class="section">
                <div class="section-title">📋 Recent Bookings</div>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Location</th>
                        <th>Duration</th>
                        <th>Cost</th>
                    </tr>
        """
        
        for res in reservations:
            html += f"""
                    <tr>
                        <td>{res['date']}</td>
                        <td>{res['lot']}</td>
                        <td>{res['duration']}</td>
                        <td>{res['cost']}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        """
    
    html += """
            <div class="footer">
                <p><strong>Thank you for using ParkEase!</strong></p>
                <p>This is an automated monthly report. For questions, contact support.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_admin_monthly_report_email(report_data, recipient_emails=None):
    """
    Send admin monthly report via email
    
    Args:
        report_data: Dictionary containing the admin monthly report data
        recipient_emails: List of email addresses to send to (defaults to admin emails)
    """
    
    class task_config:
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
        ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', 'admin@parkease.com').split(',')
    
    # Default admin emails from config
    if recipient_emails is None:
        recipient_emails = task_config.ADMIN_EMAILS
    
    # Use unified config values
    smtp_server = task_config.SMTP_SERVER
    smtp_port = task_config.SMTP_PORT
    sender_email = task_config.SENDER_EMAIL
    sender_password = task_config.SENDER_PASSWORD
    
    if not sender_password:
        return {"error": "Email configuration not set up"}
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = f"📊 ParkEase Admin Monthly Report - {report_data['report_period']}"
        
        # Create HTML email body
        html_body = generate_admin_report_html(report_data)
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach JSON report as file
        json_report = json.dumps(report_data, indent=2, default=str)
        attachment = MIMEBase('application', 'json')
        attachment.set_payload(json_report.encode())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="admin_monthly_report_{report_data["report_period"].replace(" ", "_")}.json"'
        )
        msg.attach(attachment)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return {"success": f"Admin monthly report sent to {len(recipient_emails)} recipients"}
        
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}


def generate_admin_report_html(report_data):
    """Generate HTML email body for the admin monthly report"""
    
    summary = report_data.get('summary', {})
    top_lots = report_data.get('top_parking_lots', [])
    top_users = report_data.get('top_users', [])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 20px auto; background-color: white; }}
            .header {{ background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%); color: white; padding: 30px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 32px; }}
            .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
            .metrics {{ display: flex; flex-wrap: wrap; padding: 20px; }}
            .metric {{ flex: 1; min-width: 150px; text-align: center; padding: 20px; margin: 10px; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 36px; font-weight: bold; color: #d32f2f; margin-bottom: 5px; }}
            .metric-label {{ font-size: 13px; color: #666; text-transform: uppercase; }}
            .section {{ padding: 20px; }}
            .section-title {{ font-size: 20px; font-weight: bold; color: #333; margin-bottom: 15px; border-bottom: 3px solid #d32f2f; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background-color: #f5f5f5; padding: 12px; text-align: left; font-size: 12px; color: #666; text-transform: uppercase; font-weight: bold; }}
            td {{ padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; }}
            .rank {{ background-color: #d32f2f; color: white; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px; }}
            .footer {{ background-color: #f9f9f9; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            .highlight {{ background-color: #ffebee; padding: 15px; margin: 10px 20px; border-radius: 8px; border-left: 4px solid #d32f2f; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Admin Monthly Report</h1>
                <p>{report_data.get('report_period', 'N/A')}</p>
                <p style="font-size: 12px; margin-top: 5px;">Generated: {datetime.fromisoformat(report_data.get('generated_at', '')).strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{summary.get('total_reservations', 0)}</div>
                    <div class="metric-label">Total Bookings</div>
                </div>
                <div class="metric">
                    <div class="metric-value">₹{summary.get('total_revenue', 0):,.0f}</div>
                    <div class="metric-label">Total Revenue</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary.get('active_users', 0)}</div>
                    <div class="metric-label">Active Users</div>
                </div>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{summary.get('avg_session_duration_hours', 0):.1f}h</div>
                    <div class="metric-label">Avg Duration</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary.get('occupancy_rate', 0):.1f}%</div>
                    <div class="metric-label">Occupancy Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">₹{summary.get('avg_revenue_per_booking', 0):.0f}</div>
                    <div class="metric-label">Avg per Booking</div>
                </div>
            </div>
    """
    
    if top_lots:
        html += """
            <div class="section">
                <div class="section-title">🏆 Top Performing Parking Lots</div>
                <table>
                    <tr>
                        <th>Rank</th>
                        <th>Location</th>
                        <th>Bookings</th>
                        <th>Revenue</th>
                        <th>Utilization</th>
                    </tr>
        """
        
        for idx, lot in enumerate(top_lots[:5], 1):
            html += f"""
                    <tr>
                        <td><span class="rank">{idx}</span></td>
                        <td><strong>{lot['lot_name']}</strong></td>
                        <td>{lot['bookings']}</td>
                        <td>₹{lot['revenue']:,.0f}</td>
                        <td>{lot['utilization']:.1f}%</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        """
    
    if top_users:
        html += """
            <div class="section">
                <div class="section-title">👥 Top Users</div>
                <table>
                    <tr>
                        <th>Rank</th>
                        <th>User</th>
                        <th>Bookings</th>
                        <th>Total Spent</th>
                    </tr>
        """
        
        for idx, user in enumerate(top_users[:5], 1):
            html += f"""
                    <tr>
                        <td><span class="rank">{idx}</span></td>
                        <td>{user['user_name']}</td>
                        <td>{user['bookings']}</td>
                        <td>₹{user['total_spent']:,.0f}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        """
    
    html += """
            <div class="footer">
                <p><strong>ParkEase Admin Dashboard</strong></p>
                <p>This is an automated monthly report for administrators.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_reminder_email(user, available_spots, new_lots):
    """Send reminder email to a specific user with HTML formatting"""
    user_name = user.first_name or user.username
    
    class task_config:
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
    
    smtp_server = task_config.SMTP_SERVER
    smtp_port = task_config.SMTP_PORT
    sender_email = task_config.SENDER_EMAIL
    sender_password = task_config.SENDER_PASSWORD
    
    if not sender_password:
        return {"error": "Email configuration not set up"}
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = user.email
        msg['Subject'] = f"🚗 {user_name}, don't miss out on parking spots!"
        
        # Create beautiful HTML email
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 20px auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white; padding: 40px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }}
                .content {{ padding: 30px 20px; }}
                .greeting {{ font-size: 18px; color: #333; margin-bottom: 20px; }}
                .message {{ font-size: 16px; color: #666; line-height: 1.6; margin-bottom: 25px; }}
                .stats-box {{ background-color: #f9f9f9; border-left: 4px solid #1976d2; padding: 20px; margin: 20px 0; border-radius: 4px; }}
                .stats-box h3 {{ margin: 0 0 15px 0; color: #1976d2; font-size: 18px; }}
                .stat-item {{ margin: 10px 0; font-size: 15px; color: #333; }}
                .stat-item strong {{ color: #1976d2; }}
                .lots-list {{ background-color: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; }}
                .lots-list h4 {{ margin: 0 0 10px 0; color: #856404; }}
                .lot-item {{ padding: 8px 0; color: #856404; font-size: 15px; }}
                .cta-container {{ text-align: center; margin: 30px 0; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3); }}
                .cta-button:hover {{ background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%); }}
                .footer {{ background-color: #f9f9f9; padding: 20px; text-align: center; color: #666; font-size: 13px; }}
                .emoji {{ font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 ParkEase Reminder</h1>
                    <p>Your parking spot is waiting!</p>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        Hi <strong>{user_name}</strong>! 👋
                    </div>
                    
                    <div class="message">
                        We noticed you haven't booked a parking spot recently. Don't let your favorite spots get taken!
                    </div>
                    
                    <div class="stats-box">
                        <h3>📊 Current Availability</h3>
                        <div class="stat-item">
                            <strong>{available_spots}</strong> parking spots available right now
                        </div>
                    </div>
        """
        
        if new_lots:
            html_body += """
                    <div class="lots-list">
                        <h4>🆕 Recently Added Parking Lots:</h4>
            """
            for lot in new_lots:
                html_body += f'<div class="lot-item">📍 {lot}</div>'
            html_body += """
                    </div>
            """
        
        html_body += """
                    <div class="cta-container">
                        <a href="http://localhost:5173/user/dashboard" class="cta-button">
                            Book Your Spot Now →
                        </a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>ParkEase</strong> - Smart Parking Made Simple</p>
                    <p>You're receiving this because you're an active ParkEase user.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return {"success": f"Reminder sent to {user.email}"}
        
    except Exception as e:
        return {"error": f"Failed to send reminder: {str(e)}"}



def send_daily_alert_email(alert_data, recipient_emails=None):
    """Send daily operational alerts to administrators"""
    
    # Load config from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    class task_config:
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
        ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', 'admin@parkease.com').split(',')
    
    # Default admin emails from config
    if recipient_emails is None:
        recipient_emails = task_config.ADMIN_EMAILS
    
    # Use unified config values
    smtp_server = task_config.SMTP_SERVER
    smtp_port = task_config.SMTP_PORT
    sender_email = task_config.SENDER_EMAIL
    sender_password = task_config.SENDER_PASSWORD
    
    if not sender_password:
        return {"error": "Email configuration not set up"}
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = f"ParkEase Daily Update - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Simple text email for daily updates
        body = f"""
Daily ParkEase System Update

Status: {alert_data.get('status', 'Unknown')}
Timestamp: {alert_data.get('timestamp', 'N/A')}

Details:
"""
        
        for detail in alert_data.get('details', []):
            body += f"• {detail}\n"
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return {"success": f"Daily alert sent to {len(recipient_emails)} recipients"}
        
    except Exception as e:
        return {"error": f"Failed to send daily alert: {str(e)}"}


def send_admin_csv_export_email(admin_email, filename, download_url):
    """
    Send email to admin with CSV export download link
    
    Args:
        admin_email: Email address of the admin
        filename: Name of the CSV file
        download_url: URL to download the CSV file
    """
    # Load config
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    class task_config:
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
    
    smtp_server = task_config.SMTP_SERVER
    smtp_port = task_config.SMTP_PORT
    sender_email = task_config.SENDER_EMAIL
    sender_password = task_config.SENDER_PASSWORD
    
    if not sender_password:
        return {"error": "Email configuration not set up"}
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = admin_email
        msg['Subject'] = f"📊 ParkEase User Data Export Ready - {filename}"
        
        # Create beautiful HTML email
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 20px auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white; padding: 40px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }}
                .content {{ padding: 30px 20px; }}
                .greeting {{ font-size: 18px; color: #333; margin-bottom: 20px; }}
                .message {{ font-size: 16px; color: #666; line-height: 1.6; margin-bottom: 25px; }}
                .info-box {{ background-color: #f9f9f9; border-left: 4px solid #1976d2; padding: 20px; margin: 20px 0; border-radius: 4px; }}
                .info-box h3 {{ margin: 0 0 15px 0; color: #1976d2; font-size: 18px; }}
                .info-item {{ margin: 10px 0; font-size: 15px; color: #333; }}
                .info-item strong {{ color: #1976d2; }}
                .cta-container {{ text-align: center; margin: 30px 0; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3); }}
                .cta-button:hover {{ background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%); }}
                .footer {{ background-color: #f9f9f9; padding: 20px; text-align: center; color: #666; font-size: 13px; }}
                .download-link {{ word-break: break-all; color: #1976d2; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 User Data Export Ready</h1>
                    <p>Your CSV file is ready for download</p>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        Hello Admin! 👋
                    </div>
                    
                    <div class="message">
                        Your user data export has been generated successfully. The CSV file contains all user information including their details, reservations, and statistics.
                    </div>
                    
                    <div class="info-box">
                        <h3>📄 Export Details</h3>
                        <div class="info-item">
                            <strong>Filename:</strong> {filename}
                        </div>
                        <div class="info-item">
                            <strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                        </div>
                    </div>
                    
                    <div class="cta-container">
                        <a href="{download_url}" class="cta-button" download>
                            📥 Download CSV File
                        </a>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 4px; color: #856404;">
                        <strong>Note:</strong> If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{download_url}" class="download-link">{download_url}</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>ParkEase</strong> - Smart Parking Made Simple</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return {"success": True, "message": f"CSV export email sent to {admin_email}"}
        
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}", "success": False}


def send_user_csv_export_email(user_email, user_name, filename, download_url, total_records):
    """
    Send email to user with CSV export download link
    
    Args:
        user_email: Email address of the user
        user_name: Name of the user
        filename: Name of the CSV file
        download_url: URL to download the CSV file
        total_records: Total number of records in the CSV
    """
    # Load config
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    class task_config:
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
    
    smtp_server = task_config.SMTP_SERVER
    smtp_port = task_config.SMTP_PORT
    sender_email = task_config.SENDER_EMAIL
    sender_password = task_config.SENDER_PASSWORD
    
    if not sender_password:
        return {"error": "Email configuration not set up"}
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = user_email
        msg['Subject'] = f"📊 Your ParkEase Parking History Export - {filename}"
        
        # Create beautiful HTML email
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 20px auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white; padding: 40px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }}
                .content {{ padding: 30px 20px; }}
                .greeting {{ font-size: 18px; color: #333; margin-bottom: 20px; }}
                .message {{ font-size: 16px; color: #666; line-height: 1.6; margin-bottom: 25px; }}
                .info-box {{ background-color: #f9f9f9; border-left: 4px solid #1976d2; padding: 20px; margin: 20px 0; border-radius: 4px; }}
                .info-box h3 {{ margin: 0 0 15px 0; color: #1976d2; font-size: 18px; }}
                .info-item {{ margin: 10px 0; font-size: 15px; color: #333; }}
                .info-item strong {{ color: #1976d2; }}
                .cta-container {{ text-align: center; margin: 30px 0; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3); }}
                .cta-button:hover {{ background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%); }}
                .footer {{ background-color: #f9f9f9; padding: 20px; text-align: center; color: #666; font-size: 13px; }}
                .download-link {{ word-break: break-all; color: #1976d2; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Your Parking History Export</h1>
                    <p>Your CSV file is ready for download</p>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        Hi {user_name}! 👋
                    </div>
                    
                    <div class="message">
                        Your parking history export has been generated successfully. The CSV file contains all your parking bookings with detailed information.
                    </div>
                    
                    <div class="info-box">
                        <h3>📄 Export Details</h3>
                        <div class="info-item">
                            <strong>Filename:</strong> {filename}
                        </div>
                        <div class="info-item">
                            <strong>Total Records:</strong> {total_records} booking(s)
                        </div>
                        <div class="info-item">
                            <strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                        </div>
                    </div>
                    
                    <div class="cta-container">
                        <a href="{download_url}" class="cta-button" download>
                            📥 Download CSV File
                        </a>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 4px; color: #856404;">
                        <strong>Note:</strong> If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{download_url}" class="download-link">{download_url}</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>ParkEase</strong> - Smart Parking Made Simple</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return {"success": True, "message": f"CSV export email sent to {user_email}"}
        
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}", "success": False}



def send_payment_reminder_email(user, reservation, amount):
    """
    Send payment reminder email to user for unpaid parking session
    
    Args:
        user: User object
        reservation: Reservation object
        amount: Amount to be paid
    """
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
    sender_password = os.getenv('SENDER_PASSWORD', '')
    
    if not sender_password or not user.email:
        return {"error": "Email configuration not set up or user email missing"}
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = user.email
        msg['Subject'] = f"⏰ Payment Reminder - ParkEase Booking {reservation.booking_id}"
        
        # Get parking lot name
        lot_name = "Unknown Location"
        if reservation.spot and reservation.spot.lot:
            lot_name = reservation.spot.lot.prime_location_name or reservation.spot.lot.location
        
        # Calculate days since park out
        days_unpaid = 0
        if reservation.leaving_timestamp:
            days_unpaid = (datetime.utcnow() - reservation.leaving_timestamp).days
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 20px auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); color: white; padding: 30px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.95; }}
                .content {{ padding: 30px 20px; }}
                .reminder-box {{ background: #fff3e0; border-left: 4px solid #ff9800; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                .reminder-box h3 {{ margin: 0 0 10px 0; color: #e65100; }}
                .info-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #f0f0f0; }}
                .info-row:last-child {{ border-bottom: none; }}
                .info-label {{ color: #666; font-weight: 500; }}
                .info-value {{ color: #333; font-weight: 600; }}
                .amount-highlight {{ background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; border: 2px solid #ff9800; }}
                .amount-highlight .label {{ color: #e65100; font-size: 14px; font-weight: 600; text-transform: uppercase; }}
                .amount-highlight .value {{ color: #e65100; font-size: 32px; font-weight: 700; margin: 10px 0; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; font-size: 16px; }}
                .cta-button:hover {{ background: linear-gradient(135deg, #f57c00 0%, #e65100 100%); }}
                .footer {{ background-color: #f5f5f5; padding: 20px; text-align: center; color: #666; font-size: 13px; }}
                .note {{ background: #e3f2fd; padding: 15px; border-radius: 6px; margin: 20px 0; color: #1565c0; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Payment Reminder</h1>
                    <p>Your parking payment is pending</p>
                </div>
                <div class="content">
                    <p>Hi {user.first_name or user.username},</p>
                    
                    <div class="reminder-box">
                        <h3>Payment Pending for {days_unpaid} day(s)</h3>
                        <p>We noticed that your parking session payment is still pending. Please complete the payment at your earliest convenience.</p>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">Booking ID:</span>
                        <span class="info-value">{reservation.booking_id}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Location:</span>
                        <span class="info-value">{lot_name}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Vehicle:</span>
                        <span class="info-value">{reservation.vehicle.vehicle_number if reservation.vehicle else 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Park Out Date:</span>
                        <span class="info-value">{reservation.leaving_timestamp.strftime('%B %d, %Y at %I:%M %p') if reservation.leaving_timestamp else 'N/A'}</span>
                    </div>
                    
                    <div class="amount-highlight">
                        <div class="label">Amount Due</div>
                        <div class="value">₹{amount:.2f}</div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:5173/user" class="cta-button">Pay Now</a>
                    </div>
                    
                    <div class="note">
                        <strong>💡 Tip:</strong> You can pay anytime from your dashboard. Go to your booking history and click on the booking to make payment.
                    </div>
                </div>
                <div class="footer">
                    <p><strong>ParkEase</strong></p>
                    <p>Smart Parking Management System</p>
                    <p>This is an automated reminder. Please do not reply to this email.</p>
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
        
        return {"success": True, "message": f"Payment reminder sent to {user.email}"}
    except Exception as exc:
        return {"error": f"Failed to send payment reminder: {exc}", "success": False}


def send_admin_reservations_export_email(admin_email, filename, download_url, total_records):
    """
    Send email to admin with reservation export download link
    
    Args:
        admin_email: Email address of the admin
        filename: Name of the CSV file
        download_url: URL to download the CSV file
        total_records: Total number of records in the CSV
    """
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL', 'noreply@parkease.com')
    sender_password = os.getenv('SENDER_PASSWORD', '')

    if not sender_password:
        return {"error": "Email configuration not set up", "success": False}

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
            <div class="container">
                <div class="header">
                    <h1>📊 Reservation Export Ready</h1>
                    <p>Your CSV file is ready for download</p>
                </div>
                <div class="content">
                    <p>Hi Admin,</p>
                    <p>Your reservation history export has been generated successfully. Use the button below to download the CSV file.</p>
                    <div class="info-box">
                        <div class="info-item"><strong>Filename:</strong> {filename}</div>
                        <div class="info-item"><strong>Total records:</strong> {total_records}</div>
                        <div class="info-item"><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
                    </div>
                    <div style="text-align:center;">
                        <a href="{download_url}" class="cta-button">📥 Download CSV</a>
                    </div>
                    <p>If the button above doesn't work, copy and paste this link into your browser:</p>
                    <p class="download-link">{download_url}</p>
                </div>
                <div class="footer">
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
