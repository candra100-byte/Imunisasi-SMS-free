import re
from datetime import datetime, date
from app import db
from models import Baby, Schedule, SMSLog, HealthWorker
from utils import generate_baby_id, calculate_immunization_schedule, get_sasak_message

def send_sms(phone_number, message):
    """Send SMS message via Twilio or simulate if credentials not available"""
    import os
    
    # Try to use Twilio if credentials are available
    twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
    
    success = False
    error_message = None
    
    if twilio_sid and twilio_token and twilio_phone:
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            
            message_obj = client.messages.create(
                body=message,
                from_=twilio_phone,
                to=phone_number
            )
            success = True
            print(f"SMS sent via Twilio (SID: {message_obj.sid}) to {phone_number}")
        except Exception as e:
            error_message = str(e)
            print(f"Twilio SMS failed: {error_message}. Using simulation mode.")
    else:
        print(f"SMS simulated to {phone_number}: {message[:50]}...")
        success = True  # Simulation is considered successful
    
    # Log the SMS
    sms_log = SMSLog(
        phone_number=phone_number,
        message_type='outgoing',
        content=message,
        processed=success,
        error_message=error_message if not success else None
    )
    db.session.add(sms_log)
    db.session.commit()

def process_incoming_sms(phone_number, message):
    """Process incoming SMS and return response with enhanced cultural integration"""
    message = message.strip().upper()
    
    # Registration format: REG#NAMA_BAYI#TGL_LAHIR#NAMA_IBU#DESA
    if message.startswith('REG#'):
        return process_registration(phone_number, message)
    
    # Health worker report format: LAPOR#ID_BAYI#JENIS_IMUNISASI#TANGGAL
    elif message.startswith('LAPOR#'):
        return process_health_worker_report(phone_number, message)
    
    # Info request format: INFO#ID_BAYI
    elif message.startswith('INFO#'):
        return process_info_request(phone_number, message)
    
    # Enhanced cultural commands
    elif message.startswith('ADAT#'):
        return process_cultural_query(phone_number, message)
    
    # Help command
    elif message in ['HELP', 'BANTUAN', 'TOLONGAN']:
        return get_enhanced_help_message()
    
    else:
        return get_sasak_message('invalid_format')

def process_registration(phone_number, message):
    """Process baby registration"""
    try:
        parts = message.split('#')
        if len(parts) != 5:
            return get_sasak_message('invalid_registration_format')
        
        _, nama_bayi, tgl_lahir_str, nama_ibu, desa = parts
        
        # Parse birth date
        try:
            tgl_lahir = datetime.strptime(tgl_lahir_str, '%d-%m-%Y').date()
        except ValueError:
            return get_sasak_message('invalid_date_format')
        
        # Check if baby is already registered
        existing_baby = Baby.query.filter_by(
            nama_bayi=nama_bayi.title(),
            nama_ibu=nama_ibu.title(),
            tgl_lahir=tgl_lahir
        ).first()
        
        if existing_baby:
            return get_sasak_message('already_registered', {
                'baby_id': existing_baby.id_bayi,
                'baby_name': existing_baby.nama_bayi
            })
        
        # Generate unique baby ID
        baby_id = generate_baby_id()
        
        # Create new baby record
        baby = Baby(
            id_bayi=baby_id,
            nama_bayi=nama_bayi.title(),
            tgl_lahir=tgl_lahir,
            nama_ibu=nama_ibu.title(),
            desa=desa.title(),
            no_hp_ortu=phone_number
        )
        
        db.session.add(baby)
        
        # Calculate and create immunization schedules
        schedules = calculate_immunization_schedule(tgl_lahir)
        for schedule_data in schedules:
            schedule = Schedule(
                id_bayi=baby_id,
                jenis_imunisasi=schedule_data['type'],
                tgl_jadwal=schedule_data['date']
            )
            db.session.add(schedule)
        
        db.session.commit()
        
        # Use enhanced cultural messaging
        from cultural_integration import generate_culturally_appropriate_message
        return generate_culturally_appropriate_message('registration_with_culture', {
            'baby_name': nama_bayi.title(),
            'baby_id': baby_id,
            'schedules': schedules,
            'village_coordinator': get_village_coordinator(desa.title())
        })
        
    except Exception as e:
        db.session.rollback()
        return get_sasak_message('registration_error', {'error': str(e)})

def process_health_worker_report(phone_number, message):
    """Process health worker immunization report"""
    try:
        parts = message.split('#')
        if len(parts) != 4:
            return get_sasak_message('invalid_report_format')
        
        _, baby_id, immunization_type, date_str = parts
        
        # Verify health worker
        health_worker = HealthWorker.query.filter_by(no_hp=phone_number, is_active=True).first()
        if not health_worker:
            return get_sasak_message('unauthorized_reporter')
        
        # Parse date
        try:
            report_date = datetime.strptime(date_str, '%d-%m-%Y').date()
        except ValueError:
            return get_sasak_message('invalid_date_format')
        
        # Find the schedule
        schedule = Schedule.query.filter_by(
            id_bayi=baby_id,
            jenis_imunisasi=immunization_type,
            status='terjadwal'
        ).first()
        
        if not schedule:
            return get_sasak_message('schedule_not_found', {
                'baby_id': baby_id,
                'immunization': immunization_type
            })
        
        # Update schedule status
        schedule.status = 'terlaksana'
        schedule.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Get baby info for response
        baby = Baby.query.get(baby_id)
        
        return get_sasak_message('report_success', {
            'baby_name': baby.nama_bayi,
            'immunization': immunization_type,
            'health_worker': health_worker.nama
        })
        
    except Exception as e:
        db.session.rollback()
        return get_sasak_message('report_error', {'error': str(e)})

def process_info_request(phone_number, message):
    """Process information request about a baby"""
    try:
        parts = message.split('#')
        if len(parts) != 2:
            return get_sasak_message('invalid_info_format')
        
        _, baby_id = parts
        
        baby = Baby.query.get(baby_id)
        if not baby:
            return get_sasak_message('baby_not_found', {'baby_id': baby_id})
        
        # Check if requester is authorized (parent or health worker)
        if baby.no_hp_ortu != phone_number:
            health_worker = HealthWorker.query.filter_by(no_hp=phone_number, is_active=True).first()
            if not health_worker:
                return get_sasak_message('unauthorized_info_request')
        
        # Get upcoming schedules
        upcoming_schedules = Schedule.query.filter_by(
            id_bayi=baby_id,
            status='terjadwal'
        ).filter(Schedule.tgl_jadwal >= date.today()).order_by(Schedule.tgl_jadwal).all()
        
        completed_schedules = Schedule.query.filter_by(
            id_bayi=baby_id,
            status='terlaksana'
        ).count()
        
        return get_sasak_message('info_response', {
            'baby_name': baby.nama_bayi,
            'baby_id': baby_id,
            'completed_count': completed_schedules,
            'upcoming_schedules': upcoming_schedules
        })
        
    except Exception as e:
        return get_sasak_message('info_error', {'error': str(e)})

def get_help_message():
    """Return help message in Sasak-Indonesian"""
    return """[Sistem Imunisasi Lombok Tengah]

Format SMS yang bisa digunakan:

1. DAFTAR BAYI:
REG#NAMA_BAYI#TGL_LAHIR#NAMA_IBU#DESA
Contoh: REG#AISHA#12-05-2024#SITI#PRAYA

2. INFO JADWAL:
INFO#ID_BAYI
Contoh: INFO#LT-001

3. LAPORAN PETUGAS:
LAPOR#ID_BAYI#JENIS_IMUNISASI#TANGGAL
Contoh: LAPOR#LT-001#POLIO#12-07-2024

4. BANTUAN:
HELP atau BANTUAN

Untuk pertanyaan lebih lanjut, hubungi Puskesmas terdekat.

"Anak sehat, desa kuat" - Adat Sasak"""

def send_reminder_batch():
    """Send batch reminders for upcoming immunizations"""
    from datetime import timedelta
    
    # Get schedules due in 3 days
    reminder_date = date.today() + timedelta(days=3)
    schedules = Schedule.query.filter_by(
        tgl_jadwal=reminder_date,
        status='terjadwal'
    ).all()
    
    for schedule in schedules:
        baby = Baby.query.get(schedule.id_bayi)
        if baby:
            message = get_sasak_message('reminder', {
                'baby_name': baby.nama_bayi,
                'immunization': schedule.jenis_imunisasi,
                'date': schedule.tgl_jadwal.strftime('%d-%m-%Y'),
                'village': baby.desa
            })
            send_sms(baby.no_hp_ortu, message)
    
    return len(schedules)

def send_overdue_alerts():
    """Send alerts for overdue immunizations with cultural integration"""
    overdue_schedules = Schedule.query.filter(
        Schedule.status == 'terjadwal',
        Schedule.tgl_jadwal < date.today()
    ).all()
    
    for schedule in overdue_schedules:
        baby = Baby.query.get(schedule.id_bayi)
        if baby:
            from cultural_integration import generate_culturally_appropriate_message
            message = generate_culturally_appropriate_message('reminder_with_adat', {
                'baby_name': baby.nama_bayi,
                'mother_name': baby.nama_ibu,
                'immunization': schedule.jenis_imunisasi,
                'date': 'TERLEWAT - Segera ke Puskesmas',
                'village': baby.desa,
                'village_coordinator': get_village_coordinator(baby.desa)
            })
            send_sms(baby.no_hp_ortu, message)
            
            # Update status to 'lewat'
            schedule.status = 'lewat'
    
    db.session.commit()
    return len(overdue_schedules)

def process_cultural_query(phone_number, message):
    """Process cultural/traditional queries about immunization"""
    try:
        parts = message.split('#')
        if len(parts) < 2:
            return get_sasak_message('invalid_format')
        
        query_type = parts[1].upper()
        
        if query_type == 'PEPATAH':
            from cultural_integration import SASAK_PROVERBS
            import random
            proverb = random.choice(SASAK_PROVERBS)
            return f"[Kearifan Sasak]\n\"{proverb}\"\n\nPepatah ini mengingatkan pentingnya menjaga kesehatan anak sebagai tanggung jawab bersama desa."
        
        elif query_type == 'ISTILAH':
            from cultural_integration import SASAK_HEALTH_TERMS
            terms = []
            for indo, sasak in list(SASAK_HEALTH_TERMS.items())[:5]:
                terms.append(f"{indo.title()}: {sasak}")
            return f"[Istilah Kesehatan Sasak]\n" + "\n".join(terms) + "\n\nMatur suksma!"
        
        elif query_type == 'BEBALON':
            return """[Info Bebalon Imunisasi]
Rapat desa khusus membahas:
• Cakupan imunisasi desa
• Jadwal posyandu
• Peran guru adat
• Gotong royong kesehatan

Hubungi kepala desa untuk jadwal bebalon."""
        
        else:
            return get_sasak_message('invalid_format')
            
    except Exception as e:
        return "Maaf, terjadi kesalahan. Ketik HELP untuk panduan."

def get_enhanced_help_message():
    """Enhanced help message with cultural integration"""
    return """[Sistem Imunisasi Lombok Tengah]

Format SMS yang bisa digunakan:

1. DAFTAR BAYI:
REG#NAMA_BAYI#TGL_LAHIR#NAMA_IBU#DESA
Contoh: REG#AISHA#12-05-2024#SITI#PRAYA

2. INFO JADWAL:
INFO#ID_BAYI
Contoh: INFO#LT-001

3. LAPORAN PETUGAS:
LAPOR#ID_BAYI#JENIS_IMUNISASI#TANGGAL
Contoh: LAPOR#LT-001#POLIO#12-07-2024

4. KEARIFAN LOKAL:
ADAT#PEPATAH - Pepatah Sasak
ADAT#ISTILAH - Istilah kesehatan Sasak
ADAT#BEBALON - Info rapat desa

5. BANTUAN:
HELP, BANTUAN, atau TOLONGAN

"Anak sehat, desa kuat" - Adat Sasak
Matur suksma!"""

def get_village_coordinator(village_name):
    """Get village coordinator name"""
    from models import Village
    village = Village.query.filter_by(nama_desa=village_name).first()
    return village.kordinator_adat if village and village.kordinator_adat else "Koordinator desa"
import os
import logging
import re
from datetime import datetime, date
from twilio.rest import Client
from app import app, db
from models import Baby, Schedule, SMSLog, HealthWorker
from utils import generate_baby_id, calculate_immunization_schedule, get_sasak_message, format_phone_number

# Initialize Twilio client
try:
    twilio_client = Client(
        os.environ.get('TWILIO_ACCOUNT_SID', 'demo_account'),
        os.environ.get('TWILIO_AUTH_TOKEN', 'demo_token')
    )
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER', '+1234567890')
except Exception as e:
    logging.warning(f"Twilio not configured: {e}")
    twilio_client = None

def send_sms(to_number, message):
    """Send SMS message"""
    try:
        # Log outgoing SMS
        sms_log = SMSLog(
            phone_number=to_number,
            message_type='outgoing',
            content=message,
            processed=True
        )
        db.session.add(sms_log)
        db.session.commit()
        
        # Send via Twilio if configured
        if twilio_client and os.environ.get('TWILIO_ACCOUNT_SID') != 'demo_account':
            message_obj = twilio_client.messages.create(
                body=message,
                from_=twilio_number,
                to=format_phone_number(to_number)
            )
            logging.info(f"SMS sent successfully: {message_obj.sid}")
        else:
            logging.info(f"Demo mode - SMS would be sent to {to_number}: {message}")
            
        return True
    except Exception as e:
        logging.error(f"Failed to send SMS: {str(e)}")
        return False

def process_incoming_sms(phone_number, message):
    """Process incoming SMS messages"""
    try:
        message = message.strip().upper()
        
        # Registration: REG#NAMA_BAYI#TGL_LAHIR#NAMA_IBU#DESA
        if message.startswith('REG#'):
            return handle_registration(phone_number, message)
        
        # Report: LAPOR#ID_BAYI#JENIS_IMUNISASI
        elif message.startswith('LAPOR#'):
            return handle_report(phone_number, message)
        
        # Info: INFO#ID_BAYI
        elif message.startswith('INFO#'):
            return handle_info_request(phone_number, message)
        
        # Help
        elif message in ['HELP', 'BANTUAN']:
            return """[Panduan SMS Sistem Imunisasi]
            
REG#NAMA_BAYI#TGL_LAHIR#NAMA_IBU#DESA
Contoh: REG#AISHA#12-05-2024#SITI#PRAYA

LAPOR#ID_BAYI#JENIS_IMUNISASI
Contoh: LAPOR#LT-001#BCG

INFO#ID_BAYI
Contoh: INFO#LT-001

BANTUAN - Tampilkan panduan ini"""
        
        else:
            return get_sasak_message('invalid_format')
            
    except Exception as e:
        logging.error(f"Error processing SMS: {str(e)}")
        return "Maaf, terjadi kesalahan sistem. Silakan coba lagi."

def handle_registration(phone_number, message):
    """Handle baby registration"""
    try:
        parts = message.split('#')
        if len(parts) != 5:
            return get_sasak_message('invalid_registration_format')
        
        _, nama_bayi, tgl_lahir_str, nama_ibu, desa = parts
        
        # Parse birth date
        try:
            tgl_lahir = datetime.strptime(tgl_lahir_str, '%d-%m-%Y').date()
        except ValueError:
            return get_sasak_message('invalid_date_format')
        
        # Check if baby already registered
        existing = Baby.query.filter_by(
            nama_bayi=nama_bayi,
            nama_ibu=nama_ibu,
            tgl_lahir=tgl_lahir
        ).first()
        
        if existing:
            return get_sasak_message('already_registered', {
                'baby_name': existing.nama_bayi,
                'baby_id': existing.id_bayi
            })
        
        # Generate unique baby ID
        baby_id = generate_baby_id()
        
        # Create baby record
        baby = Baby(
            id_bayi=baby_id,
            nama_bayi=nama_bayi,
            tgl_lahir=tgl_lahir,
            nama_ibu=nama_ibu,
            desa=desa,
            no_hp_ortu=phone_number
        )
        db.session.add(baby)
        
        # Calculate immunization schedule
        schedules = calculate_immunization_schedule(tgl_lahir)
        
        # Create schedule records
        for schedule_data in schedules:
            schedule = Schedule(
                id_bayi=baby_id,
                jenis_imunisasi=schedule_data['type'],
                tgl_jadwal=schedule_data['date']
            )
            db.session.add(schedule)
        
        db.session.commit()
        
        return get_sasak_message('registration_success', {
            'baby_name': nama_bayi,
            'baby_id': baby_id,
            'schedules': schedules
        })
        
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return get_sasak_message('registration_error', {'error': str(e)})

def handle_report(phone_number, message):
    """Handle immunization completion report"""
    try:
        # Check if sender is authorized health worker
        health_worker = HealthWorker.query.filter_by(no_hp=phone_number, is_active=True).first()
        if not health_worker:
            return get_sasak_message('unauthorized_reporter')
        
        parts = message.split('#')
        if len(parts) != 3:
            return "Format: LAPOR#ID_BAYI#JENIS_IMUNISASI"
        
        _, baby_id, immunization_type = parts
        
        # Find the schedule
        schedule = Schedule.query.filter_by(
            id_bayi=baby_id,
            jenis_imunisasi=immunization_type,
            status='terjadwal'
        ).first()
        
        if not schedule:
            return get_sasak_message('schedule_not_found', {
                'immunization': immunization_type,
                'baby_id': baby_id
            })
        
        # Update schedule status
        schedule.status = 'terlaksana'
        schedule.completed_at = datetime.utcnow()
        db.session.commit()
        
        baby = Baby.query.get(baby_id)
        
        return get_sasak_message('report_success', {
            'health_worker': health_worker.nama,
            'immunization': immunization_type,
            'baby_name': baby.nama_bayi
        })
        
    except Exception as e:
        logging.error(f"Report error: {str(e)}")
        return get_sasak_message('report_error', {'error': str(e)})

def handle_info_request(phone_number, message):
    """Handle information request"""
    try:
        parts = message.split('#')
        if len(parts) != 2:
            return "Format: INFO#ID_BAYI"
        
        _, baby_id = parts
        
        baby = Baby.query.get(baby_id)
        if not baby:
            return get_sasak_message('baby_not_found', {'baby_id': baby_id})
        
        # Check if requester is authorized (parent or health worker)
        is_parent = baby.no_hp_ortu == phone_number
        is_health_worker = HealthWorker.query.filter_by(no_hp=phone_number, is_active=True).first()
        
        if not (is_parent or is_health_worker):
            return get_sasak_message('unauthorized_info_request')
        
        # Get schedule information
        completed_schedules = Schedule.query.filter_by(
            id_bayi=baby_id,
            status='terlaksana'
        ).count()
        
        upcoming_schedules = Schedule.query.filter_by(
            id_bayi=baby_id,
            status='terjadwal'
        ).all()
        
        return get_sasak_message('info_response', {
            'baby_name': baby.nama_bayi,
            'baby_id': baby_id,
            'completed_count': completed_schedules,
            'upcoming_schedules': upcoming_schedules
        })
        
    except Exception as e:
        logging.error(f"Info request error: {str(e)}")
        return get_sasak_message('info_error', {'error': str(e)})
