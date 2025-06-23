"""
Sistem Recovery Bot untuk Imunisasi Lombok Tengah
Bot otomatis untuk memantau dan memperbaiki sistem
"""

import time
import logging
from datetime import datetime, date, timedelta
from threading import Thread

class SystemRecoveryBot:
    def __init__(self):
        self.is_running = False
        self.logger = logging.getLogger('SystemRecoveryBot')
        
    def log_activity(self, message):
        """Log bot activity with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logger.info(f"[{timestamp}] {message}")
        print(f"[Recovery Bot {timestamp}] {message}")
    
    def check_and_fix_overdue_schedules(self):
        """Check for overdue schedules and update status"""
        try:
            from app import db
            from models import Schedule
            
            current_date = date.today()
            overdue_count = 0
            
            # Find schedules that are overdue but still marked as 'terjadwal'
            overdue_schedules = Schedule.query.filter(
                Schedule.status == 'terjadwal',
                Schedule.tgl_jadwal < current_date - timedelta(days=1)
            ).all()
            
            for schedule in overdue_schedules:
                schedule.status = 'lewat'
                overdue_count += 1
            
            if overdue_count > 0:
                db.session.commit()
                self.log_activity(f"Updated {overdue_count} overdue schedules to 'lewat' status")
            
            return overdue_count
            
        except Exception as e:
            self.log_activity(f"Error checking overdue schedules: {str(e)}")
            return 0
    
    def cleanup_old_logs(self):
        """Clean up old SMS logs to free up space"""
        try:
            from app import db
            from models import SMSLog
            
            # Keep only last 30 days of logs
            cutoff_date = datetime.now() - timedelta(days=30)
            
            old_logs = SMSLog.query.filter(
                SMSLog.created_at < cutoff_date
            ).count()
            
            if old_logs > 100:  # Only cleanup if there are many old logs
                SMSLog.query.filter(
                    SMSLog.created_at < cutoff_date
                ).delete()
                db.session.commit()
                self.log_activity(f"Cleaned up {old_logs} old SMS logs")
                return old_logs
            
            return 0
            
        except Exception as e:
            self.log_activity(f"Error cleaning up logs: {str(e)}")
            return 0
    
    def validate_data_integrity(self):
        """Validate and fix data integrity issues"""
        try:
            from app import db
            from models import Baby, Schedule
            
            issues_fixed = 0
            
            # Check for babies without any schedules
            babies_without_schedules = Baby.query.outerjoin(Schedule).filter(
                Schedule.id_bayi.is_(None)
            ).all()
            
            for baby in babies_without_schedules:
                # Auto-generate missing schedules
                from utils import calculate_immunization_schedule
                schedules = calculate_immunization_schedule(baby.tgl_lahir)
                
                for schedule_data in schedules:
                    schedule = Schedule(
                        id_bayi=baby.id_bayi,
                        jenis_imunisasi=schedule_data['type'],
                        tgl_jadwal=schedule_data['date'],
                        status='terjadwal'
                    )
                    db.session.add(schedule)
                    issues_fixed += 1
            
            if issues_fixed > 0:
                db.session.commit()
                self.log_activity(f"Generated {issues_fixed} missing immunization schedules")
            
            return issues_fixed
            
        except Exception as e:
            self.log_activity(f"Error validating data integrity: {str(e)}")
            return 0
    
    def monitor_system_health(self):
        """Monitor overall system health and alert if needed"""
        try:
            from app import db
            from models import Baby, Schedule, SMSLog
            
            # Check database connectivity
            total_babies = Baby.query.count()
            total_schedules = Schedule.query.count()
            total_sms = SMSLog.query.count()
            
            # Basic health metrics
            health_report = {
                'babies': total_babies,
                'schedules': total_schedules,
                'sms_logs': total_sms,
                'timestamp': datetime.now()
            }
            
            self.log_activity(f"System Health: {total_babies} babies, {total_schedules} schedules, {total_sms} SMS logs")
            
            # Alert if numbers seem unusual
            if total_schedules < total_babies:
                self.log_activity("WARNING: Fewer schedules than babies - possible data integrity issue")
            
            return health_report
            
        except Exception as e:
            self.log_activity(f"Error monitoring system health: {str(e)}")
            return None
    
    def send_daily_summary(self):
        """Send daily summary to admin"""
        try:
            from sms_service import send_sms
            from models import User
            
            # Get admin users
            admin_users = User.query.filter_by(role='admin', is_active=True).all()
            
            # Generate summary
            summary = f"""[Sistem Imunisasi - Ringkasan Harian]
Tanggal: {date.today().strftime('%d-%m-%Y')}

Status sistem: Normal
Auto-recovery berhasil dijalankan

Laporan lengkap tersedia di dashboard admin.
"""
            
            # Send SMS to admins (if SMS is configured)
            for admin in admin_users:
                if hasattr(admin, 'phone') and admin.phone:
                    # send_sms(admin.phone, summary)
                    pass  # Skip SMS for now, just log
            
            self.log_activity("Daily summary prepared for administrators")
            
        except Exception as e:
            self.log_activity(f"Error sending daily summary: {str(e)}")
    
    def run_recovery_cycle(self):
        """Run complete recovery cycle"""
        self.log_activity("Starting system recovery cycle")
        
        # Run all recovery tasks
        overdue_fixed = self.check_and_fix_overdue_schedules()
        logs_cleaned = self.cleanup_old_logs()
        integrity_fixed = self.validate_data_integrity()
        health_report = self.monitor_system_health()
        
        # Summary
        self.log_activity(f"Recovery cycle completed: {overdue_fixed} overdue fixed, {logs_cleaned} logs cleaned, {integrity_fixed} integrity issues fixed")
        
        return {
            'overdue_fixed': overdue_fixed,
            'logs_cleaned': logs_cleaned,
            'integrity_fixed': integrity_fixed,
            'health_report': health_report
        }
    
    def start_bot(self):
        """Start the recovery bot with scheduled tasks"""
        self.is_running = True
        self.log_activity("System Recovery Bot started")
        
        def bot_loop():
            while self.is_running:
                try:
                    # Run recovery cycle every 4 hours
                    self.run_recovery_cycle()
                    
                    # Sleep for 4 hours (14400 seconds)
                    for _ in range(1440):  # Check every 10 seconds for stop signal
                        if not self.is_running:
                            break
                        time.sleep(10)
                        
                except Exception as e:
                    self.log_activity(f"Error in bot loop: {str(e)}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        # Start bot in background thread
        bot_thread = Thread(target=bot_loop, daemon=True)
        bot_thread.start()
        
        return bot_thread
    
    def stop_bot(self):
        """Stop the recovery bot"""
        self.is_running = False
        self.log_activity("System Recovery Bot stopped")

# Global bot instance
recovery_bot = SystemRecoveryBot()

def start_recovery_bot():
    """Start the global recovery bot"""
    return recovery_bot.start_bot()

def stop_recovery_bot():
    """Stop the global recovery bot"""
    recovery_bot.stop_bot()

if __name__ == '__main__':
    # Manual run for testing
    recovery_bot.run_recovery_cycle()