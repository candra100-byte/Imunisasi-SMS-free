from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
import logging

scheduler = None

def init_scheduler(app):
    """Initialize the background scheduler"""
    global scheduler
    
    if scheduler is None:
        scheduler = BackgroundScheduler()
        
        # Schedule reminder sending every day at 9 AM
        scheduler.add_job(
            func=send_daily_reminders,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_reminders',
            name='Send daily immunization reminders',
            replace_existing=True
        )
        
        # Schedule overdue alerts every day at 10 AM
        scheduler.add_job(
            func=send_overdue_alerts_job,
            trigger=CronTrigger(hour=10, minute=0),
            id='overdue_alerts',
            name='Send overdue immunization alerts',
            replace_existing=True
        )
        
        # Schedule weekly educational messages on Sundays at 8 AM
        scheduler.add_job(
            func=send_weekly_education,
            trigger=CronTrigger(day_of_week=6, hour=8, minute=0),
            id='weekly_education',
            name='Send weekly educational messages',
            replace_existing=True
        )
        
        scheduler.start()
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
        
        logging.info("Scheduler initialized successfully")

def send_daily_reminders():
    """Job function to send daily reminders"""
    with scheduler.app.app_context():
        from sms_service import send_reminder_batch
        count = send_reminder_batch()
        logging.info(f"Sent {count} reminder messages")

def send_overdue_alerts_job():
    """Job function to send overdue alerts"""
    with scheduler.app.app_context():
        from sms_service import send_overdue_alerts
        count = send_overdue_alerts()
        logging.info(f"Sent {count} overdue alert messages")

def send_weekly_education():
    """Job function to send weekly educational content"""
    with scheduler.app.app_context():
        from models import Baby
        from sms_service import send_sms
        from utils import get_sasak_message
        
        # Get all registered parents
        babies = Baby.query.all()
        unique_parents = {}
        
        for baby in babies:
            if baby.no_hp_ortu not in unique_parents:
                unique_parents[baby.no_hp_ortu] = baby.nama_ibu
        
        # Send educational message
        for phone_number, mother_name in unique_parents.items():
            message = get_sasak_message('weekly_education', {
                'mother_name': mother_name
            })
            send_sms(phone_number, message)
        
        logging.info(f"Sent {len(unique_parents)} weekly educational messages")
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, timedelta
import logging
from app import app, db
from models import Schedule, Baby
from sms_service import send_sms
from utils import get_sasak_message

scheduler = BackgroundScheduler()

def send_daily_reminders():
    """Send daily immunization reminders"""
    with app.app_context():
        try:
            # Get schedules for tomorrow
            tomorrow = date.today() + timedelta(days=1)
            upcoming_schedules = db.session.query(Schedule, Baby).join(Baby).filter(
                Schedule.tgl_jadwal == tomorrow,
                Schedule.status == 'terjadwal'
            ).all()
            
            for schedule, baby in upcoming_schedules:
                message = get_sasak_message('reminder', {
                    'baby_name': baby.nama_bayi,
                    'immunization': schedule.jenis_imunisasi,
                    'date': schedule.tgl_jadwal.strftime('%d-%m-%Y'),
                    'village': baby.desa
                })
                
                send_sms(baby.no_hp_ortu, message)
                logging.info(f"Reminder sent to {baby.no_hp_ortu} for {baby.nama_bayi}")
                
        except Exception as e:
            logging.error(f"Error sending daily reminders: {str(e)}")

def send_overdue_alerts():
    """Send alerts for overdue immunizations"""
    with app.app_context():
        try:
            # Get overdue schedules
            overdue_schedules = db.session.query(Schedule, Baby).join(Baby).filter(
                Schedule.tgl_jadwal < date.today(),
                Schedule.status == 'terjadwal'
            ).all()
            
            for schedule, baby in overdue_schedules:
                # Update status to overdue
                schedule.status = 'lewat'
                
                message = get_sasak_message('overdue_alert', {
                    'baby_name': baby.nama_bayi,
                    'immunization': schedule.jenis_imunisasi,
                    'scheduled_date': schedule.tgl_jadwal.strftime('%d-%m-%Y'),
                    'village': baby.desa
                })
                
                send_sms(baby.no_hp_ortu, message)
                logging.info(f"Overdue alert sent to {baby.no_hp_ortu} for {baby.nama_bayi}")
            
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Error sending overdue alerts: {str(e)}")

def send_weekly_education():
    """Send weekly educational messages"""
    with app.app_context():
        try:
            # Get all babies with active schedules
            active_babies = Baby.query.join(Schedule).filter(
                Schedule.status.in_(['terjadwal', 'lewat'])
            ).distinct().all()
            
            for baby in active_babies:
                message = get_sasak_message('weekly_education', {
                    'mother_name': baby.nama_ibu
                })
                
                send_sms(baby.no_hp_ortu, message)
                logging.info(f"Educational message sent to {baby.no_hp_ortu}")
                
        except Exception as e:
            logging.error(f"Error sending educational messages: {str(e)}")

def init_scheduler(app):
    """Initialize scheduler with app context"""
    # Schedule daily reminders at 9 AM
    scheduler.add_job(
        func=send_daily_reminders,
        trigger="cron",
        hour=9,
        minute=0,
        id='daily_reminders',
        name='Send daily immunization reminders',
        replace_existing=True
    )
    
    # Schedule overdue alerts at 10 AM
    scheduler.add_job(
        func=send_overdue_alerts,
        trigger="cron",
        hour=10,
        minute=0,
        id='overdue_alerts',
        name='Send overdue immunization alerts',
        replace_existing=True
    )
    
    # Schedule weekly education on Sundays at 8 AM
    scheduler.add_job(
        func=send_weekly_education,
        trigger="cron",
        day_of_week=0,
        hour=8,
        minute=0,
        id='weekly_education',
        name='Send weekly educational messages',
        replace_existing=True
    )
    
    scheduler.start()
    logging.info("Scheduler initialized successfully")
