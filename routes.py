from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash
import logging
import traceback
from app import app, db
from models import Baby, Schedule, Village, SMSLog, HealthWorker, User
from sms_service import process_incoming_sms, send_sms
from utils import generate_baby_id, calculate_immunization_schedule, get_sasak_message
from sqlalchemy import func, desc, case
from health_monitor import health_monitor

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username dan password harus diisi', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout', 'info')
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        health_status = health_monitor.monitor_system_health()
        status_code = 200 if health_status.get('database', False) else 503
        return jsonify(health_status), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 503

@app.route('/')
@login_required
def dashboard():
    # Get statistics
    total_babies = Baby.query.count()
    total_schedules = Schedule.query.count()
    completed_immunizations = Schedule.query.filter_by(status='terlaksana').count()
    overdue_schedules = Schedule.query.filter(
        Schedule.status == 'terjadwal',
        Schedule.tgl_jadwal < date.today()
    ).count()
    
    # Update overdue schedules
    overdue = Schedule.query.filter(
        Schedule.status == 'terjadwal',
        Schedule.tgl_jadwal < date.today()
    ).all()
    for schedule in overdue:
        schedule.status = 'lewat'
    db.session.commit()
    
    # Get recent activities
    recent_babies = Baby.query.order_by(desc(Baby.created_at)).limit(5).all()
    recent_sms = SMSLog.query.order_by(desc(SMSLog.created_at)).limit(10).all()
    
    # Get immunization completion rates by village
    village_stats = db.session.query(
        Baby.desa,
        func.count(Baby.id_bayi).label('total_babies'),
        func.count(Schedule.id_jadwal).label('total_schedules'),
        func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed')
    ).outerjoin(Schedule).group_by(Baby.desa).all()
    
    return render_template('dashboard.html', 
                         total_babies=total_babies,
                         total_schedules=total_schedules,
                         completed_immunizations=completed_immunizations,
                         overdue_schedules=overdue_schedules,
                         recent_babies=recent_babies,
                         recent_sms=recent_sms,
                         village_stats=village_stats)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Akses ditolak. Hanya administrator yang dapat mengakses halaman ini.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(desc(User.created_at)).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    if not current_user.is_admin():
        flash('Akses ditolak. Hanya administrator yang dapat menambah user.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        
        if not all([username, email, password, confirm_password, full_name, role]):
            flash('Semua field harus diisi', 'error')
            return render_template('admin/add_user.html')
        
        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok', 'error')
            return render_template('admin/add_user.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan', 'error')
            return render_template('admin/add_user.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email sudah digunakan', 'error')
            return render_template('admin/add_user.html')
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} berhasil ditambahkan', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/add_user.html')

@app.route('/admin/users/<int:user_id>/toggle')
@login_required
def admin_toggle_user(user_id):
    if not current_user.is_admin():
        flash('Akses ditolak', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Tidak dapat menonaktifkan akun sendiri', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'diaktifkan' if user.is_active else 'dinonaktifkan'
    flash(f'User {user.username} berhasil {status}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/babies')
@login_required
def babies():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    village_filter = request.args.get('village', '')
    
    query = Baby.query
    
    if search:
        query = query.filter(
            (Baby.nama_bayi.contains(search)) |
            (Baby.nama_ibu.contains(search)) |
            (Baby.id_bayi.contains(search))
        )
    
    if village_filter:
        query = query.filter(Baby.desa == village_filter)
    
    babies = query.order_by(desc(Baby.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    villages = db.session.query(Baby.desa).distinct().all()
    villages = [v[0] for v in villages]
    
    return render_template('babies.html', babies=babies, villages=villages, 
                         search=search, village_filter=village_filter)

@app.route('/schedules')
@login_required
def schedules():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    immunization_filter = request.args.get('immunization', '')
    
    query = db.session.query(Schedule, Baby).join(Baby)
    
    if status_filter:
        query = query.filter(Schedule.status == status_filter)
        
    if immunization_filter:
        query = query.filter(Schedule.jenis_imunisasi == immunization_filter)
    
    schedules = query.order_by(Schedule.tgl_jadwal).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('schedules.html', schedules=schedules,
                         status_filter=status_filter,
                         immunization_filter=immunization_filter)

@app.route('/sms-logs')
@login_required
def sms_logs():
    page = request.args.get('page', 1, type=int)
    message_type = request.args.get('type', '')
    
    query = SMSLog.query
    
    if message_type:
        query = query.filter(SMSLog.message_type == message_type)
    
    logs = query.order_by(desc(SMSLog.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('sms_logs.html', logs=logs, message_type=message_type)

@app.route('/villages')
@login_required
def villages():
    villages = Village.query.all()
    return render_template('villages.html', villages=villages)

@app.route('/process-sms', methods=['POST'])
@login_required
def process_sms():
    """Simulate receiving SMS messages"""
    phone_number = request.form.get('phone_number')
    message = request.form.get('message')
    
    if not phone_number or not message:
        flash('Phone number and message are required', 'error')
        return redirect(url_for('sms_logs'))
    
    # Log incoming SMS
    sms_log = SMSLog(
        phone_number=phone_number,
        message_type='incoming',
        content=message,
        processed=False
    )
    db.session.add(sms_log)
    db.session.commit()
    
    # Process the SMS
    try:
        response = process_incoming_sms(phone_number, message)
        sms_log.processed = True
        
        # Send response SMS
        if response:
            send_sms(phone_number, response)
            flash('SMS processed successfully', 'success')
        else:
            flash('SMS processed but no response generated', 'info')
            
    except Exception as e:
        sms_log.error_message = str(e)
        flash(f'Error processing SMS: {str(e)}', 'error')
    
    db.session.commit()
    return redirect(url_for('sms_logs'))

@app.route('/send-reminder/<int:schedule_id>')
@login_required
def send_reminder(schedule_id):
    """Send manual reminder for a specific schedule"""
    schedule = Schedule.query.get_or_404(schedule_id)
    baby = Baby.query.get(schedule.id_bayi)
    
    try:
        message = get_sasak_message('reminder', {
            'baby_name': baby.nama_bayi,
            'immunization': schedule.jenis_imunisasi,
            'date': schedule.tgl_jadwal.strftime('%d-%m-%Y'),
            'village': baby.desa
        })
        
        send_sms(baby.no_hp_ortu, message)
        flash(f'Reminder sent to {baby.nama_ibu} for {baby.nama_bayi}', 'success')
    except Exception as e:
        flash(f'Failed to send reminder: {str(e)}', 'error')
    
    return redirect(url_for('schedules'))

@app.route('/mark-completed/<int:schedule_id>')
@login_required
def mark_completed(schedule_id):
    """Mark a schedule as completed"""
    schedule = Schedule.query.get_or_404(schedule_id)
    schedule.status = 'terlaksana'
    schedule.completed_at = datetime.utcnow()
    db.session.commit()
    
    flash('Immunization marked as completed', 'success')
    return redirect(url_for('schedules'))

@app.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    """API endpoint for dashboard statistics"""
    # Immunization completion by type
    immunization_stats = db.session.query(
        Schedule.jenis_imunisasi,
        func.count(Schedule.id_jadwal).label('total'),
        func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed')
    ).group_by(Schedule.jenis_imunisasi).all()
    
    # Monthly registration trends
    monthly_registrations = db.session.query(
        func.strftime('%Y-%m', Baby.created_at).label('month'),
        func.count(Baby.id_bayi).label('count')
    ).group_by(func.strftime('%Y-%m', Baby.created_at)).order_by('month').all()
    
    # Village coverage
    village_coverage = db.session.query(
        Baby.desa,
        func.count(Baby.id_bayi).label('babies'),
        func.count(Schedule.id_jadwal).label('schedules'),
        func.sum(case([(Schedule.status == 'terlaksana', 1)], else_=0)).label('completed')
    ).outerjoin(Schedule).group_by(Baby.desa).all()
    
    return jsonify({
        'immunization_stats': [{
            'type': stat.jenis_imunisasi,
            'total': stat.total,
            'completed': stat.completed or 0,
            'percentage': round((stat.completed or 0) / stat.total * 100, 1) if stat.total > 0 else 0
        } for stat in immunization_stats],
        'monthly_registrations': [{
            'month': reg.month,
            'count': reg.count
        } for reg in monthly_registrations],
        'village_coverage': [{
            'village': cov.desa,
            'babies': cov.babies,
            'schedules': cov.schedules or 0,
            'completed': cov.completed or 0,
            'coverage': round((cov.completed or 0) / (cov.schedules or 1) * 100, 1)
        } for cov in village_coverage]
    })

@app.route('/analytics')
@login_required
def analytics_dashboard():
    """Advanced analytics dashboard"""
    from analytics import generate_coverage_report, calculate_dropout_risk, identify_intervention_targets
    from cultural_integration import generate_adat_integration_report
    
    coverage_data = generate_coverage_report()
    dropout_data = calculate_dropout_risk()
    intervention_data = identify_intervention_targets()
    cultural_data = generate_adat_integration_report()
    
    return render_template('analytics/dashboard.html',
                         coverage=coverage_data,
                         dropout=dropout_data,
                         interventions=intervention_data,
                         cultural=cultural_data)

@app.route('/cultural-integration')
@login_required
def cultural_integration():
    """Cultural integration management"""
    from cultural_integration import get_village_coordinator_contacts, create_cultural_content_calendar
    
    coordinators = get_village_coordinator_contacts()
    calendar = create_cultural_content_calendar()
    
    return render_template('cultural/integration.html',
                         coordinators=coordinators,
                         calendar=calendar)

@app.route('/reports/export/<report_type>')
@login_required
def export_report(report_type):
    """Export comprehensive reports"""
    from analytics import export_report_data
    import json
    from flask import Response
    
    if not current_user.is_admin():
        flash('Akses ditolak. Hanya administrator yang dapat mengekspor laporan.', 'error')
        return redirect(url_for('dashboard'))
    
    report_data = export_report_data(report_type)
    
    if report_data:
        json_data = json.dumps(report_data, indent=2, default=str)
        
        return Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename=report_{report_type}_{date.today().isoformat()}.json'}
        )
    
    flash('Gagal mengekspor laporan', 'error')
    return redirect(url_for('analytics_dashboard'))

@app.route('/community-engagement/<village_name>')
@login_required
def community_engagement_plan(village_name):
    """Generate community engagement plan for specific village"""
    from cultural_integration import generate_community_engagement_plan
    
    plan = generate_community_engagement_plan(village_name)
    
    return render_template('cultural/engagement_plan.html', 
                         plan=plan, 
                         village_name=village_name)
