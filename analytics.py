"""
Advanced analytics and prediction module for immunization dropout detection
Implements AI-based predictions and comprehensive reporting
"""

from datetime import datetime, date, timedelta
from sqlalchemy import func, case, extract
import logging

def calculate_dropout_risk():
    """Calculate dropout risk for babies based on historical patterns"""
    from app import db
    from models import Baby, Schedule
    
    current_date = date.today()
    
    # Find babies with missed schedules (high risk)
    high_risk_babies = db.session.query(Baby).join(Schedule).filter(
        Schedule.status == 'lewat',
        Schedule.tgl_jadwal < current_date - timedelta(days=30)
    ).distinct().all()
    
    # Find babies with upcoming schedules (medium risk if no recent activity)
    upcoming_schedules = db.session.query(Baby, Schedule).join(Schedule).filter(
        Schedule.status == 'terjadwal',
        Schedule.tgl_jadwal.between(current_date, current_date + timedelta(days=7))
    ).all()
    
    medium_risk_babies = []
    for baby, schedule in upcoming_schedules:
        # Check if baby has any completed immunizations recently
        recent_completed = Schedule.query.filter_by(
            id_bayi=baby.id_bayi,
            status='terlaksana'
        ).filter(Schedule.completed_at >= current_date - timedelta(days=60)).count()
        
        if recent_completed == 0:
            medium_risk_babies.append(baby)
    
    return {
        'high_risk_count': len(high_risk_babies),
        'medium_risk_count': len(medium_risk_babies),
        'high_risk_babies': high_risk_babies,
        'medium_risk_babies': medium_risk_babies
    }

def generate_coverage_report():
    """Generate comprehensive immunization coverage report"""
    from app import db
    from models import Baby, Schedule
    
    # Overall statistics
    total_babies = Baby.query.count()
    total_schedules = Schedule.query.count()
    completed_schedules = Schedule.query.filter_by(status='terlaksana').count()
    overdue_schedules = Schedule.query.filter(
        Schedule.status == 'terjadwal',
        Schedule.tgl_jadwal < date.today()
    ).count()
    
    # Coverage by immunization type
    immunization_coverage = db.session.query(
        Schedule.jenis_imunisasi,
        func.count(Schedule.id_jadwal).label('total'),
        func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed')
    ).group_by(Schedule.jenis_imunisasi).all()
    
    # Coverage by village
    village_coverage = db.session.query(
        Baby.desa,
        func.count(Baby.id_bayi).label('total_babies'),
        func.count(Schedule.id_jadwal).label('total_schedules'),
        func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed_schedules')
    ).outerjoin(Schedule).group_by(Baby.desa).all()
    
    # Monthly registration trends
    monthly_registrations = db.session.query(
        extract('year', Baby.created_at).label('year'),
        extract('month', Baby.created_at).label('month'),
        func.count(Baby.id_bayi).label('count')
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    # Age group analysis
    current_date = date.today()
    age_groups = db.session.query(
        case([
            ((current_date - Baby.tgl_lahir) <= timedelta(days=60), '0-2 bulan'),
            ((current_date - Baby.tgl_lahir) <= timedelta(days=180), '2-6 bulan'),
            ((current_date - Baby.tgl_lahir) <= timedelta(days=365), '6-12 bulan'),
        ], else_='1+ tahun').label('age_group'),
        func.count(Baby.id_bayi).label('count')
    ).group_by('age_group').all()
    
    return {
        'summary': {
            'total_babies': total_babies,
            'total_schedules': total_schedules,
            'completed_schedules': completed_schedules,
            'completion_rate': round((completed_schedules / total_schedules * 100), 2) if total_schedules > 0 else 0,
            'overdue_schedules': overdue_schedules
        },
        'immunization_coverage': immunization_coverage,
        'village_coverage': village_coverage,
        'monthly_trends': monthly_registrations,
        'age_groups': age_groups
    }

def identify_intervention_targets():
    """Identify villages and demographics requiring intervention"""
    from app import db
    from models import Baby, Schedule
    
    # Villages with low coverage
    low_coverage_villages = db.session.query(
        Baby.desa,
        func.count(Baby.id_bayi).label('total_babies'),
        func.count(Schedule.id_jadwal).label('total_schedules'),
        func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed'),
        (func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)) * 100.0 / 
         func.count(Schedule.id_jadwal)).label('coverage_percentage')
    ).outerjoin(Schedule).group_by(Baby.desa).having(
        func.count(Schedule.id_jadwal) > 0
    ).order_by('coverage_percentage').limit(5).all()
    
    # Recent dropouts (babies with missed recent schedules)
    recent_dropouts = db.session.query(Baby, Schedule).join(Schedule).filter(
        Schedule.status == 'lewat',
        Schedule.tgl_jadwal >= date.today() - timedelta(days=30)
    ).all()
    
    # Never started (babies with no completed immunizations)
    never_started = db.session.query(Baby).outerjoin(Schedule).group_by(Baby.id_bayi).having(
        func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)) == 0
    ).all()
    
    return {
        'low_coverage_villages': low_coverage_villages,
        'recent_dropouts': recent_dropouts,
        'never_started': never_started,
        'intervention_recommendations': generate_intervention_recommendations(low_coverage_villages, recent_dropouts)
    }

def generate_intervention_recommendations(low_coverage_villages, recent_dropouts):
    """Generate specific intervention recommendations"""
    recommendations = []
    
    if low_coverage_villages:
        for village in low_coverage_villages[:3]:  # Top 3 priority villages
            recommendations.append({
                'type': 'village_intervention',
                'target': village.desa,
                'priority': 'high',
                'action': f'Intensifkan sosialisasi di desa {village.desa} dengan melibatkan tokoh adat',
                'sasak_message': f'Bebalon khusus imunisasi di desa {village.desa}'
            })
    
    if len(recent_dropouts) > 5:
        recommendations.append({
            'type': 'dropout_follow_up',
            'target': 'recent_dropouts',
            'priority': 'urgent',
            'action': 'Lakukan kunjungan rumah untuk bayi yang terlewat jadwal',
            'sasak_message': 'Kunjungan bidan ke rumah - "Belek imunisasi te anak kite"'
        })
    
    return recommendations

def generate_cultural_insights():
    """Generate insights for cultural integration"""
    from app import db
    from models import SMSLog, Village, Baby, Schedule
    
    # SMS response patterns
    sms_activity = db.session.query(
        SMSLog.message_type,
        func.count(SMSLog.id).label('count'),
        func.avg(case([(SMSLog.processed == True, 1)], else_=0)).label('success_rate')
    ).group_by(SMSLog.message_type).all()
    
    # Village coordinator effectiveness
    village_engagement = db.session.query(
        Village.nama_desa,
        Village.kordinator_adat,
        func.count(Baby.id_bayi).label('registrations'),
        func.avg(case([(Schedule.status == 'terlaksana', 100)], else_=0)).label('completion_rate')
    ).outerjoin(Baby, Village.nama_desa == Baby.desa).outerjoin(Schedule).group_by(
        Village.nama_desa, Village.kordinator_adat
    ).all()
    
    return {
        'sms_effectiveness': sms_activity,
        'village_coordinator_impact': village_engagement,
        'cultural_recommendations': [
            'Tingkatkan penggunaan pepatah Sasak dalam SMS reminder',
            'Libatkan lebih banyak tokoh adat dalam sosialisasi',
            'Gunakan gending Sasak untuk edukasi di posyandu'
        ]
    }

def export_report_data(report_type='comprehensive'):
    """Export report data for external analysis"""
    
    if report_type == 'comprehensive':
        coverage_data = generate_coverage_report()
        dropout_data = calculate_dropout_risk()
        intervention_data = identify_intervention_targets()
        cultural_data = generate_cultural_insights()
        
        return {
            'generated_at': datetime.now().isoformat(),
            'report_type': 'comprehensive',
            'coverage_analysis': coverage_data,
            'dropout_prediction': dropout_data,
            'intervention_targets': intervention_data,
            'cultural_insights': cultural_data
        }
    
    return None

def log_analytics_activity(activity_type, details):
    """Log analytics activities for audit trail"""
    logging.info(f"Analytics: {activity_type} - {details}")
from datetime import datetime, date, timedelta
from sqlalchemy import func, case
from app import db
from models import Baby, Schedule, Village, SMSLog
import logging

def generate_coverage_report():
    """Generate immunization coverage report"""
    try:
        # Overall statistics
        total_babies = Baby.query.count()
        total_schedules = Schedule.query.count()
        completed_schedules = Schedule.query.filter_by(status='terlaksana').count()
        
        coverage_rate = (completed_schedules / total_schedules * 100) if total_schedules > 0 else 0
        
        # Coverage by immunization type
        immunization_coverage = db.session.query(
            Schedule.jenis_imunisasi,
            func.count(Schedule.id_jadwal).label('total'),
            func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed')
        ).group_by(Schedule.jenis_imunisasi).all()
        
        # Coverage by village
        village_coverage = db.session.query(
            Baby.desa,
            func.count(Baby.id_bayi).label('babies'),
            func.count(Schedule.id_jadwal).label('total_schedules'),
            func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed_schedules')
        ).outerjoin(Schedule).group_by(Baby.desa).all()
        
        return {
            'overall': {
                'total_babies': total_babies,
                'total_schedules': total_schedules,
                'completed_schedules': completed_schedules,
                'coverage_rate': round(coverage_rate, 2)
            },
            'by_immunization': [{
                'type': item.jenis_imunisasi,
                'total': item.total,
                'completed': item.completed or 0,
                'rate': round((item.completed or 0) / item.total * 100, 2) if item.total > 0 else 0
            } for item in immunization_coverage],
            'by_village': [{
                'village': item.desa,
                'babies': item.babies,
                'total_schedules': item.total_schedules or 0,
                'completed_schedules': item.completed_schedules or 0,
                'rate': round((item.completed_schedules or 0) / (item.total_schedules or 1) * 100, 2)
            } for item in village_coverage]
        }
    except Exception as e:
        logging.error(f"Error generating coverage report: {str(e)}")
        return {}

def calculate_dropout_risk():
    """Calculate dropout risk analysis"""
    try:
        # Find babies with missed schedules
        missed_schedules = db.session.query(
            Baby.id_bayi,
            Baby.nama_bayi,
            Baby.nama_ibu,
            Baby.desa,
            func.count(Schedule.id_jadwal).label('missed_count')
        ).join(Schedule).filter(
            Schedule.status == 'lewat'
        ).group_by(Baby.id_bayi).all()
        
        high_risk_babies = [baby for baby in missed_schedules if baby.missed_count >= 2]
        
        return {
            'total_at_risk': len(missed_schedules),
            'high_risk': len(high_risk_babies),
            'babies': [{
                'id': baby.id_bayi,
                'name': baby.nama_bayi,
                'mother': baby.nama_ibu,
                'village': baby.desa,
                'missed_count': baby.missed_count,
                'risk_level': 'high' if baby.missed_count >= 2 else 'medium'
            } for baby in missed_schedules]
        }
    except Exception as e:
        logging.error(f"Error calculating dropout risk: {str(e)}")
        return {}

def identify_intervention_targets():
    """Identify villages/areas needing intervention"""
    try:
        # Villages with low coverage
        village_performance = db.session.query(
            Baby.desa,
            func.count(Baby.id_bayi).label('babies'),
            func.count(Schedule.id_jadwal).label('total_schedules'),
            func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed'),
            func.sum(case([(Schedule.status == 'lewat', 1)], else_=0)).label('missed')
        ).outerjoin(Schedule).group_by(Baby.desa).all()
        
        intervention_targets = []
        for village in village_performance:
            if village.total_schedules and village.total_schedules > 0:
                coverage_rate = (village.completed or 0) / village.total_schedules * 100
                if coverage_rate < 80:  # Below 80% coverage
                    intervention_targets.append({
                        'village': village.desa,
                        'babies': village.babies,
                        'coverage_rate': round(coverage_rate, 2),
                        'missed_schedules': village.missed or 0,
                        'priority': 'high' if coverage_rate < 60 else 'medium'
                    })
        
        return {
            'total_targets': len(intervention_targets),
            'villages': sorted(intervention_targets, key=lambda x: x['coverage_rate'])
        }
    except Exception as e:
        logging.error(f"Error identifying intervention targets: {str(e)}")
        return {}

def export_report_data(report_type):
    """Export comprehensive report data"""
    try:
        if report_type == 'coverage':
            return generate_coverage_report()
        elif report_type == 'dropout':
            return calculate_dropout_risk()
        elif report_type == 'intervention':
            return identify_intervention_targets()
        elif report_type == 'complete':
            return {
                'generated_at': datetime.now().isoformat(),
                'coverage': generate_coverage_report(),
                'dropout_risk': calculate_dropout_risk(),
                'intervention_targets': identify_intervention_targets()
            }
        else:
            return None
    except Exception as e:
        logging.error(f"Error exporting report data: {str(e)}")
        return None
