from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

class Employee(db.Model):
    __tablename__ = 'employees'
    
    employee_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    registration_date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    
    face_templates = db.relationship('FaceTemplate', backref='employee', lazy=True)
    attendance_logs = db.relationship('AttendanceLog', backref='employee', lazy=True)

class FaceTemplate(db.Model):
    __tablename__ = 'face_templates'
    
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.employee_id'), primary_key=True)
    encrypted_template = db.Column(db.LargeBinary, nullable=False)
    created_date = db.Column(db.String(50), nullable=False)

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.employee_id'), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    checkin_type = db.Column(db.String(10), default='IN')
    timezone = db.Column(db.String(50), default='Asia/Kolkata')