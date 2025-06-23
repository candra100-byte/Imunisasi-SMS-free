
import random
import string
from datetime import date, timedelta
from app import db
from models import Baby

def generate_baby_id():
    """Generate unique baby ID in format LT-XXX"""
    max_attempts = 100
    attempts = 0
    
    while attempts < max_attempts:
        # Generate random 3-digit number
        number = random.randint(1, 999)
        baby_id = f"LT-{number:03d}"
        
        # Check if ID already exists
        existing = Baby.query.get(baby_id)
        if not existing:
            return baby_id
        attempts += 1
    
    # Fallback to timestamp-based ID if all attempts fail
    import time
    timestamp = str(int(time.time()))[-4:]
    return f"LT-{timestamp}"

def calculate_immunization_schedule(birth_date):
    """Calculate immunization schedule based on birth date following Indonesian guidelines"""
    schedules = []
    
    # BCG - at birth or within 2 months
    bcg_date = birth_date + timedelta(days=30)
    schedules.append({
        'type': 'BCG',
        'date': bcg_date,
        'description': 'Vaksin BCG untuk mencegah tuberkulosis'
    })
    
    # Hepatitis B - at birth, 1 month, 6 months
    hep_date = birth_date + timedelta(days=60)
    schedules.append({
        'type': 'Hepatitis',
        'date': hep_date,
        'description': 'Vaksin Hepatitis B'
    })
    
    # Polio 1 - 2 months
    polio1_date = birth_date + timedelta(days=60)
    schedules.append({
        'type': 'Polio',
        'date': polio1_date,
        'description': 'Vaksin Polio dosis pertama'
    })
    
    # DPT 1 - 2 months
    dpt1_date = birth_date + timedelta(days=60)
    schedules.append({
        'type': 'DPT',
        'date': dpt1_date,
        'description': 'Vaksin DPT dosis pertama'
    })
    
    # Campak - 9 months
    campak_date = birth_date + timedelta(days=270)
    schedules.append({
        'type': 'Campak',
        'date': campak_date,
        'description': 'Vaksin Campak'
    })
    
    return schedules

def get_sasak_message(message_type, data=None):
    """Get culturally appropriate messages in Sasak-Indonesian mix"""
    if data is None:
        data = {}
    
    # Sasak greetings and terms
    sasak_terms = {
        'baby': 'anak dedare',
        'mother': 'bung',
        'thank_you': 'matur suksma',
        'dont_forget': 'menangi le',
        'complete': 'belek',
        'healthy': 'waras',
        'village': 'gubuk'
    }
    
    messages = {
        'registration_success': f"""[Lombok Tengah - Sistem Imunisasi]

{sasak_terms['thank_you']}! {sasak_terms['baby'].title()} {data.get('baby_name', '')} (ID: {data.get('baby_id', '')}) telah terdaftar.

Jadwal Imunisasi:
""" + "\n".join([f"{i+1}. {s['type']}: {s['date'].strftime('%d-%m-%Y')}" for i, s in enumerate(data.get('schedules', []))]) + f"""

"Anak sehat, desa kuat" - Adat Sasak
Info: Hubungi Puskesmas terdekat
{sasak_terms['dont_forget']} ngingatang!""",

        'reminder': f"""[Lombok Tengah]
{sasak_terms['mother'].title()}, jadwal imunisasi {data.get('baby_name', '')} ({data.get('immunization', '')}) besok {data.get('date', '')} di Puskesmas {data.get('village', '')}.

"Anak selamat, desa makmur" - Pepatah Sasak
Tepak nane! (Jangan sampai terlewat!)""",

        'overdue_alert': f"""[PENTING - Lombok Tengah]
{sasak_terms['baby'].title()} {data.get('baby_name', '')} belum imunisasi {data.get('immunization', '')} (jadwal: {data.get('scheduled_date', '')}).

Segera ke Puskesmas {data.get('village', '')} atau hubungi bidan desa.
"{sasak_terms['complete']} imunisasi te anak kite" (Lengkapi imunisasi anak kita)""",

        'report_success': f"""Laporan diterima. {sasak_terms['thank_you']} {data.get('health_worker', '')}!
Imunisasi {data.get('immunization', '')} untuk {data.get('baby_name', '')} telah tercatat.

{sasak_terms['thank_you']}!""",

        'weekly_education': f"""[Edukasi Mingguan]
{sasak_terms['mother'].title()} {data.get('mother_name', '')},

"{sasak_terms['dont_forget']}, {sasak_terms['complete']} imunisasi te anak kite"
(Jangan lupa, lengkapi imunisasi anak kita)

Manfaat imunisasi:
- Cegah polio, campak, hepatitis
- Anak tumbuh sehat dan kuat
- Lindungi generasi masa depan

Konsultasi gratis di Puskesmas terdekat.
"Anak {sasak_terms['healthy']}, keluarga bahagia" - Adat Sasak""",

        'invalid_format': """Format SMS tidak tepat.
Ketik HELP atau BANTUAN untuk panduan.

Contoh: REG#AISHA#12-05-2024#SITI#PRAYA""",

        'invalid_registration_format': """Format pendaftaran salah.
Gunakan: REG#NAMA_BAYI#TGL_LAHIR#NAMA_IBU#DESA
Contoh: REG#AISHA#12-05-2024#SITI#PRAYA""",

        'invalid_date_format': """Format tanggal salah.
Gunakan format: DD-MM-YYYY
Contoh: 12-05-2024""",

        'already_registered': f"""Bayi {data.get('baby_name', '')} sudah terdaftar dengan ID: {data.get('baby_id', '')}.
Ketik INFO#{data.get('baby_id', '')} untuk info jadwal.""",

        'registration_error': f"""Maaf, terjadi kesalahan saat pendaftaran.
Silakan coba lagi atau hubungi Puskesmas.
Error: {data.get('error', 'Unknown error')}""",

        'unauthorized_reporter': """Nomor ini tidak terdaftar sebagai petugas kesehatan.
Hubungi admin untuk registrasi petugas.""",

        'schedule_not_found': f"""Jadwal imunisasi {data.get('immunization', '')} untuk bayi {data.get('baby_id', '')} tidak ditemukan atau sudah selesai.""",

        'baby_not_found': f"""Bayi dengan ID {data.get('baby_id', '')} tidak ditemukan.
Pastikan ID benar atau lakukan pendaftaran dulu.""",

        'unauthorized_info_request': """Anda tidak berhak mengakses informasi ini.
Hanya orang tua atau petugas kesehatan yang dapat mengakses.""",

        'info_response': f"""[Info Bayi {data.get('baby_name', '')} - {data.get('baby_id', '')}]

Imunisasi selesai: {data.get('completed_count', 0)}

Jadwal mendatang:
""" + "\n".join([f"- {s.jenis_imunisasi}: {s.tgl_jadwal.strftime('%d-%m-%Y')}" for s in data.get('upcoming_schedules', [])]) + f"""

"{sasak_terms['complete']} imunisasi, anak {sasak_terms['healthy']}" - Adat Sasak""",

        'report_error': f"""Maaf, terjadi kesalahan saat melaporkan.
Silakan coba lagi atau hubungi admin.
Error: {data.get('error', 'Unknown error')}""",

        'info_error': f"""Maaf, terjadi kesalahan saat mengambil informasi.
Silakan coba lagi.
Error: {data.get('error', 'Unknown error')}"""
    }
    
    return messages.get(message_type, "Pesan tidak tersedia.")

def get_village_names():
    """Get list of common village names in Central Lombok"""
    return [
        'Praya', 'Kopang', 'Pujut', 'Jonggat', 'Batukliang',
        'Janapria', 'Praya Timur', 'Praya Barat', 'Pringgarata',
        'Sukamulia', 'Suralaga', 'Aikmel', 'Wanasaba'
    ]

def format_phone_number(phone_number):
    """Format phone number to standard Indonesian format"""
    if not phone_number:
        return phone_number
    
    # Remove any non-digit characters
    clean_number = ''.join(filter(str.isdigit, phone_number))
    
    # Convert to Indonesian format
    if clean_number.startswith('0'):
        return '+62' + clean_number[1:]
    elif clean_number.startswith('62'):
        return '+' + clean_number
    elif clean_number.startswith('8'):
        return '+62' + clean_number
    
    return phone_number

def calculate_age_in_months(birth_date):
    """Calculate age in months from birth date"""
    if not birth_date:
        return 0
    
    today = date.today()
    months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
    
    # Adjust if the day of birth hasn't occurred yet this month
    if today.day < birth_date.day:
        months -= 1
    
    return max(0, months)

def get_immunization_status_color(status):
    """Get Bootstrap color class for immunization status"""
    colors = {
        'terjadwal': 'primary',
        'terlaksana': 'success', 
        'lewat': 'danger'
    }
    return colors.get(status, 'secondary')

def validate_phone_number(phone_number):
    """Validate Indonesian phone number format"""
    if not phone_number:
        return False
    
    clean_number = ''.join(filter(str.isdigit, phone_number))
    
    # Check length (Indonesian mobile numbers are typically 10-13 digits)
    if len(clean_number) < 10 or len(clean_number) > 13:
        return False
    
    # Check if starts with valid Indonesian mobile prefixes
    valid_prefixes = ['08', '628', '8']
    return any(clean_number.startswith(prefix) for prefix in valid_prefixes)

def get_sasak_proverb():
    """Get random Sasak proverb related to health and children"""
    proverbs = [
        "Anak sehat, desa kuat",
        "Anak selamat, desa makmur", 
        "Belek imunisasi te anak kite",
        "Anak waras, keluarge seneng",
        "Tindak becik, hasil becik",
        "Anak dedare mutiare desa",
        "Sehat kuwat, seneng rakyat",
        "Imunisasi wajib, anak selamat",
        "Guru adat bijak, anak desa sehat",
        "Gotong royong jagain anak"
    ]
    return random.choice(proverbs)
