#!/usr/bin/env python3
"""
Script to initialize database and create default admin user
Run this script once after setting up the project
"""

from app import app, db
from models import User, Village
import os

def init_database():
    """Initialize database with tables and default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully")
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("Admin user already exists")
            return
        
        # Create default admin user
        admin = User(
            username='admin',
            email='admin@lombok-tengah.go.id',
            full_name='Administrator Sistem',
            role='admin'
        )
        admin.set_password('admin123')  # Default password
        
        db.session.add(admin)
        
        # Create sample villages
        sample_villages = [
            {'kode_desa': 'PR001', 'nama_desa': 'Praya', 'kordinator_adat': 'H. Ahmad Sasak', 'no_hp_kader': '081234567890'},
            {'kode_desa': 'KP001', 'nama_desa': 'Kopang', 'kordinator_adat': 'Hj. Siti Nurhasanah', 'no_hp_kader': '081234567891'},
            {'kode_desa': 'PJ001', 'nama_desa': 'Pujut', 'kordinator_adat': 'H. Muhammad Amin', 'no_hp_kader': '081234567892'},
            {'kode_desa': 'JG001', 'nama_desa': 'Jonggat', 'kordinator_adat': 'Hj. Fatimah', 'no_hp_kader': '081234567893'},
            {'kode_desa': 'BK001', 'nama_desa': 'Batukliang', 'kordinator_adat': 'H. Abdul Rahman', 'no_hp_kader': '081234567894'},
        ]
        
        for village_data in sample_villages:
            existing_village = Village.query.filter_by(kode_desa=village_data['kode_desa']).first()
            if not existing_village:
                village = Village(**village_data)
                db.session.add(village)
        
        db.session.commit()
        
        print("✅ Database initialized successfully!")
        print("📋 Default admin account created:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@lombok-tengah.go.id")
        print("")
        print("🔒 IMPORTANT: Please change the default password after first login!")
        print("🏥 Sample villages have been added to the system")

if __name__ == '__main__':
    init_database()