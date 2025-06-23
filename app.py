
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

class Base(DeclarativeBase):
    pass

# Create global instances
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the Flask app
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("SESSION_SECRET", "imunisasi-lombok-tengah-2024-secure-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
database_url = os.environ.get("DATABASE_URL", "sqlite:///immunization.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Create default admin user if not exists
    from models import User, Village, HealthWorker
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin = User(
            username='admin',
            email='admin@lombok-tengah.go.id',
            full_name='Administrator Sistem',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin user created: admin/admin123")
    
    # Create sample villages if none exist
    if Village.query.count() == 0:
        sample_villages = [
            {'kode_desa': 'PR001', 'nama_desa': 'Praya', 'kordinator_adat': 'H. Ahmad Saleh', 'no_hp_kader': '081234567890'},
            {'kode_desa': 'KP001', 'nama_desa': 'Kopang', 'kordinator_adat': 'H. Muhammad Amin', 'no_hp_kader': '081234567891'},
            {'kode_desa': 'PJ001', 'nama_desa': 'Pujut', 'kordinator_adat': 'H. Abdul Rahman', 'no_hp_kader': '081234567892'},
            {'kode_desa': 'JG001', 'nama_desa': 'Jonggat', 'kordinator_adat': 'H. Zainal Abidin', 'no_hp_kader': '081234567893'},
            {'kode_desa': 'BK001', 'nama_desa': 'Batukliang', 'kordinator_adat': 'H. Lalu Gede', 'no_hp_kader': '081234567894'}
        ]
        
        for village_data in sample_villages:
            village = Village(**village_data)
            db.session.add(village)
        
        db.session.commit()
        logging.info("Sample villages created")
    
    # Create sample health worker if none exist
    if HealthWorker.query.count() == 0:
        health_worker = HealthWorker(
            nama='Bidan Siti Nurhaliza',
            jabatan='Bidan Desa',
            no_hp='081234567888',
            desa_tugas='Praya',
            is_active=True
        )
        db.session.add(health_worker)
        db.session.commit()
        logging.info("Sample health worker created")

# Import routes and initialize scheduler
import routes

# Initialize scheduler
from scheduler import init_scheduler
init_scheduler(app)

# Setup error handlers
from health_monitor import setup_error_handlers
setup_error_handlers(app)
