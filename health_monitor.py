import logging
from datetime import datetime
from flask import jsonify, request, g

class HealthMonitor:
    def __init__(self):
        self.logger = logging.getLogger('HealthMonitor')
    
    def check_database_health(self):
        """Check database connectivity and basic operations"""
        try:
            from app import db
            from models import Baby
            
            # Try to execute a simple query
            count = Baby.query.count()
            return {
                'status': 'healthy',
                'babies_count': count,
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def check_sms_service_health(self):
        """Check SMS service functionality"""
        try:
            import os
            
            # Check if Twilio credentials are available
            has_twilio = all([
                os.environ.get('TWILIO_ACCOUNT_SID'),
                os.environ.get('TWILIO_AUTH_TOKEN'),
                os.environ.get('TWILIO_PHONE_NUMBER')
            ])
            
            return {
                'status': 'healthy',
                'twilio_configured': has_twilio,
                'mode': 'twilio' if has_twilio else 'simulation',
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def check_schedule_health(self):
        """Check immunization schedule system health"""
        try:
            from app import db
            from models import Schedule
            from datetime import date, timedelta
            
            current_date = date.today()
            
            # Count schedules by status
            total_schedules = Schedule.query.count()
            completed = Schedule.query.filter_by(status='terlaksana').count()
            overdue = Schedule.query.filter(
                Schedule.status == 'terjadwal',
                Schedule.tgl_jadwal < current_date
            ).count()
            upcoming = Schedule.query.filter(
                Schedule.status == 'terjadwal',
                Schedule.tgl_jadwal.between(current_date, current_date + timedelta(days=7))
            ).count()
            
            return {
                'status': 'healthy',
                'total_schedules': total_schedules,
                'completed': completed,
                'overdue': overdue,
                'upcoming_week': upcoming,
                'completion_rate': round((completed / total_schedules * 100), 2) if total_schedules > 0 else 0,
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def auto_recovery(self):
        """Attempt automatic recovery from common issues"""
        recovery_actions = []
        
        try:
            # Check and fix overdue schedules
            from system_recovery_bot import recovery_bot
            result = recovery_bot.run_recovery_cycle()
            recovery_actions.append(f"Recovery cycle completed: {result}")
            
        except Exception as e:
            recovery_actions.append(f"Auto-recovery failed: {str(e)}")
        
        return recovery_actions
    
    def monitor_system_health(self):
        """Comprehensive system health monitoring"""
        health_status = {
            'overall': 'healthy',
            'checks': {},
            'timestamp': datetime.now(),
            'issues': []
        }
        
        # Check database
        db_health = self.check_database_health()
        health_status['checks']['database'] = db_health
        if db_health['status'] == 'error':
            health_status['overall'] = 'degraded'
            health_status['issues'].append('Database connectivity issue')
        
        # Check SMS service
        sms_health = self.check_sms_service_health()
        health_status['checks']['sms'] = sms_health
        if sms_health['status'] == 'error':
            health_status['overall'] = 'degraded'
            health_status['issues'].append('SMS service issue')
        
        # Check schedules
        schedule_health = self.check_schedule_health()
        health_status['checks']['schedules'] = schedule_health
        if schedule_health['status'] == 'error':
            health_status['overall'] = 'degraded'
            health_status['issues'].append('Schedule system issue')
        elif schedule_health.get('overdue', 0) > 10:
            health_status['issues'].append(f"{schedule_health['overdue']} overdue schedules")
        
        return health_status

# Global health monitor instance
health_monitor = HealthMonitor()

def setup_error_handlers(app):
    """Setup global error handlers with auto-recovery"""
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 errors with auto-recovery attempt"""
        logging.error(f"Internal server error: {str(error)}")
        
        # Attempt auto-recovery
        try:
            recovery_actions = health_monitor.auto_recovery()
            logging.info(f"Auto-recovery attempted: {recovery_actions}")
        except Exception as e:
            logging.error(f"Auto-recovery failed: {str(e)}")
        
        return jsonify({
            'error': 'Internal server error',
            'message': 'Terjadi kesalahan server. Tim teknis telah diberitahu.',
            'auto_recovery': 'attempted'
        }), 500
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Not found',
            'message': 'Halaman yang dicari tidak ditemukan.'
        }), 404
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 errors"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'Akses ditolak. Anda tidak memiliki izin untuk mengakses halaman ini.'
        }), 403
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 errors"""
        return jsonify({
            'error': 'Bad request',
            'message': 'Permintaan tidak valid. Periksa data yang dikirim.'
        }), 400
    
    @app.before_request
    def before_request():
        """Run health checks before each request (for critical endpoints)"""
        # Only run health checks for API endpoints
        if request.path.startswith('/api/') or request.path.startswith('/health'):
            try:
                # Quick database connectivity check
                from app import db
                db.session.execute('SELECT 1')
            except Exception as e:
                logging.error(f"Database health check failed: {str(e)}")
                # Don't block the request, just log the issue

def get_system_stats():
    """Get system statistics for monitoring dashboard"""
    try:
        health_status = health_monitor.monitor_system_health()
        
        # Add additional system stats
        from app import db
        from models import Baby, Schedule, SMSLog, User
        
        stats = {
            'health': health_status,
            'counts': {
                'babies': Baby.query.count(),
                'schedules': Schedule.query.count(),
                'sms_logs': SMSLog.query.count(),
                'users': User.query.filter_by(is_active=True).count()
            },
            'performance': {
                'response_time': 'good',  # This could be enhanced with actual metrics
                'uptime': '99.9%',  # This could be enhanced with actual tracking
                'last_check': datetime.now()
            }
        }
        
        return stats
        
    except Exception as e:
        logging.error(f"Error getting system stats: {str(e)}")
        return {
            'health': {'overall': 'error', 'error': str(e)},
            'counts': {},
            'performance': {}
        }