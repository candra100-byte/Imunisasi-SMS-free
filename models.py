
from datetime import datetime, date
from app import db
from sqlalchemy import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Baby(db.Model):
    __tablename__ = 'bayi'
    
    id_bayi = db.Column(db.String(10), primary_key=True)
    nama_bayi = db.Column(db.String(50), nullable=False)
    tgl_lahir = db.Column(db.Date, nullable=False)
    nama_ibu = db.Column(db.String(50), nullable=False)
    desa = db.Column(db.String(50), nullable=False)
    no_hp_ortu = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with schedules
    schedules = db.relationship('Schedule', backref='baby_ref', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Baby {self.nama_bayi}>'
    
    def get_completion_rate(self):
        """Calculate immunization completion rate"""
        total_schedules = len(self.schedules)
        if total_schedules == 0:
            return 0
        completed = len([s for s in self.schedules if s.status == 'terlaksana'])
        return round((completed / total_schedules) * 100, 2)

class Schedule(db.Model):
    __tablename__ = 'jadwal'
    
    id_jadwal = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_bayi = db.Column(db.String(10), db.ForeignKey('bayi.id_bayi'), nullable=False)
    jenis_imunisasi = db.Column(db.Enum('BCG', 'Polio', 'DPT', 'Campak', 'Hepatitis', name='immunization_types'), nullable=False)
    tgl_jadwal = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('terjadwal', 'terlaksana', 'lewat', name='schedule_status'), default='terjadwal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Schedule {self.jenis_imunisasi} for {self.id_bayi}>'
    
    def is_overdue(self):
        """Check if schedule is overdue"""
        return self.status == 'terjadwal' and self.tgl_jadwal < date.today()

class Village(db.Model):
    __tablename__ = 'desa'
    
    kode_desa = db.Column(db.String(5), primary_key=True)
    nama_desa = db.Column(db.String(50), nullable=False, unique=True)
    kordinator_adat = db.Column(db.String(50), nullable=True)
    no_hp_kader = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Village {self.nama_desa}>'

class SMSLog(db.Model):
    __tablename__ = 'sms_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(15), nullable=False)
    message_type = db.Column(db.Enum('incoming', 'outgoing', name='message_types'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<SMSLog {self.message_type} to/from {self.phone_number}>'

class HealthWorker(db.Model):
    __tablename__ = 'petugas'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(50), nullable=False)
    jabatan = db.Column(db.String(30), nullable=False)
    no_hp = db.Column(db.String(15), unique=True, nullable=False)
    desa_tugas = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HealthWorker {self.nama}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('admin', 'operator', 'health_worker', name='user_roles'), default='operator')
    full_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

# Create indexes for better performance
from sqlalchemy import Index

Index('idx_baby_desa', Baby.desa)
Index('idx_schedule_status_date', Schedule.status, Schedule.tgl_jadwal)
Index('idx_sms_log_created', SMSLog.created_at)
Index('idx_sms_log_phone', SMSLog.phone_number)
