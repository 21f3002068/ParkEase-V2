from ... import db
from datetime import datetime, timedelta

class TaskLog(db.Model):
    __tablename__ = 'task_log'
    
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, error, running
    message = db.Column(db.Text)
    details = db.Column(db.JSON)  # Store additional details as JSON
    triggered_by = db.Column(db.String(50), nullable=True, default='system')  # system, admin, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        # Convert UTC to IST (UTC+5:30) and format to minutes precision
        formatted_timestamp = None
        if self.created_at:
            # Add 5 hours 30 minutes to convert UTC to IST
            ist_time = self.created_at + timedelta(hours=5, minutes=30)
            formatted_timestamp = ist_time.strftime('%Y-%m-%d %H:%M')
        
        return {
            'id': self.id,
            'taskName': self.task_name or 'Unknown Task',  # camelCase for frontend
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'triggeredBy': self.triggered_by or 'system',  # camelCase for frontend
            'timestamp': formatted_timestamp
        }
    
    def __repr__(self):
        return f'<TaskLog {self.id}: {self.task_name} - {self.status}>'
