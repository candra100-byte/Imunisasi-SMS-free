"""
Enhanced cultural integration module for Sasak traditions and local wisdom
Implements deeper cultural features and community engagement tools
"""

from datetime import datetime, date
import random

# Extended Sasak vocabulary for health and immunization
SASAK_HEALTH_TERMS = {
    'imunisasi': 'imunisasi',
    'bayi': 'anak dedare',
    'sehat': 'waras',
    'sakit': 'getel',
    'obat': 'tamba',
    'dokter': 'mantri',
    'bidan': 'dukun bayi',
    'puskesmas': 'pustu',
    'jadwal': 'waktu',
    'penting': 'perlu',
    'jangan_lupa': 'menangi le',
    'segera': 'enggal-enggal',
    'terima_kasih': 'matur suksma',
    'maaf': 'ampure',
    'baik': 'becik',
    'buruk': 'jelek',
    'keluarga': 'keluarge',
    'desa': 'gubuk',
    'ibu': 'inaq',
    'bapak': 'amaq'
}

# Traditional Sasak proverbs related to health and children
SASAK_PROVERBS = [
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

# Traditional meeting formats and channels
TRADITIONAL_CHANNELS = {
    'bebalon': {
        'name': 'Bebalon (Rapat Desa)',
        'frequency': 'monthly',
        'participants': 'Kepala desa, tokoh adat, warga',
        'health_integration': 'Agenda khusus imunisasi dan kesehatan anak'
    },
    'pengajian': {
        'name': 'Pengajian/Ceramah Agama',
        'frequency': 'weekly',
        'participants': 'Jamaah masjid, keluarga muslim',
        'health_integration': 'Pesan kesehatan dalam ceramah agama'
    },
    'gending_sasak': {
        'name': 'Gending Sasak (Nyanyian Tradisional)',
        'frequency': 'cultural_events',
        'participants': 'Masyarakat umum, anak-anak',
        'health_integration': 'Lagu edukasi tentang imunisasi'
    },
    'dewan_masjid': {
        'name': 'Dewan Kemakmuran Masjid',
        'frequency': 'monthly',
        'participants': 'Pengurus masjid, tokoh agama',
        'health_integration': 'Program kesehatan berbasis masjid'
    }
}

def generate_culturally_appropriate_message(message_type, context=None):
    """Generate SMS messages with deep cultural integration"""
    
    if context is None:
        context = {}
    
    # Select appropriate Sasak terms
    baby_term = SASAK_HEALTH_TERMS['bayi']
    health_term = SASAK_HEALTH_TERMS['sehat']
    
    # Add random proverb for cultural authenticity
    proverb = random.choice(SASAK_PROVERBS)
    
    messages = {
        'registration_with_culture': f"""[Lombok Tengah - Imunisasi]
Matur suksma! {baby_term} {context.get('baby_name', '')} (ID: {context.get('baby_id', '')}) sampun kadaftar.

Jadwal imunisasi:
{format_schedule_sasak(context.get('schedules', []))}

"{proverb}" - Adat Sasak
Kader desa: {context.get('village_coordinator', 'Hubungi Pustu')}""",
        
        'reminder_with_adat': f"""[Lombok Tengah]
Bung {context.get('mother_name', '')}, 

Esok ({context.get('date', '')}) jadwal imunisasi {context.get('baby_name', '')} - {context.get('immunization', '')} di Pustu {context.get('village', '')}.

Guru adat {context.get('village_coordinator', '')} ngingatang: "{proverb}"

Tepak nane berangkat! (Jangan sampai terlewat!)""",
        
        'cultural_education': f"""[Edukasi Sasak]
"Menangi le, belek imunisasi te {baby_term} kite"

Dalam adat Sasak, menjaga kesehatan {baby_term} adalah tanggung jawab bersama:
• Keluarge (keluarga)
• Gubuk (desa) 
• Krama adat

{translate_health_benefits_sasak()}

"{proverb}" - Kearifan Lokal Sasak""",
        
        'community_mobilization': f"""[Bebalon Khusus]
Krama desa {context.get('village', '')},

Bebalon khusus imunisasi:
📅 {context.get('date', 'Minggu depan')}
📍 Balai desa
👥 Guru adat + Bidan desa

Agenda: Cakupan imunisasi & peran adat
"Gotong royong jagain {baby_term}" - Adat Sasak""",
        
        'health_worker_appreciation': f"""Matur suksma, {context.get('health_worker', 'petugas')}!

Laporan imunisasi {context.get('immunization', '')} untuk {context.get('baby_name', '')} telah tercatat.

Jerih payah petugas sangat dihargai krama adat.
"{proverb}"

Semangat melayani masyarakat!"""
    }
    
    return messages.get(message_type, get_sasak_message(message_type, context))

def format_schedule_sasak(schedules):
    """Format immunization schedule with Sasak cultural elements"""
    if not schedules:
        return "Jadwal akan dikirim segera"
    
    formatted = []
    sasak_numbers = ['sik', 'dua', 'telu', 'empat', 'lime']
    
    for i, schedule in enumerate(schedules[:5]):
        number = sasak_numbers[i] if i < len(sasak_numbers) else str(i+1)
        formatted.append(f"{number.title()}. {schedule['type']}: {schedule['date'].strftime('%d-%m-%Y')}")
    
    return "\n".join(formatted)

def translate_health_benefits_sasak():
    """Translate health benefits using Sasak terms"""
    benefits = [
        f"Cegah penyakit (hindarin getel)",
        f"Anak {SASAK_HEALTH_TERMS['sehat']} dan kuwat",
        f"Lindungi {SASAK_HEALTH_TERMS['keluarga']}",
        f"Desa bebas wabah"
    ]
    return "\n• ".join(benefits)

def generate_community_engagement_plan(village_name):
    """Generate culturally-informed community engagement strategy"""
    from models import Village
    
    # Get village data
    village = Village.query.filter_by(nama_desa=village_name).first()
    
    plan = {
        'village': village_name,
        'coordinator': village.kordinator_adat if village else 'Belum ditentukan',
        'phone': village.no_hp_kader if village else None,
        'strategies': []
    }
    
    # Bebalon (Village Meeting) Strategy
    plan['strategies'].append({
        'channel': 'Bebalon Desa',
        'frequency': 'Bulanan',
        'approach': f'Agenda khusus imunisasi dalam rapat desa {village_name}',
        'key_message': 'Gotong royong jagain anak dedare',
        'implementation': [
            'Koordinasi dengan kepala desa',
            'Libatkan guru adat sebagai pembicara',
            'Presentasi data cakupan imunisasi desa',
            'Diskusi tantangan dan solusi bersama'
        ]
    })
    
    # Religious Integration Strategy
    plan['strategies'].append({
        'channel': 'Pengajian & Ceramah',
        'frequency': 'Mingguan', 
        'approach': 'Integrasi pesan kesehatan dalam ceramah agama',
        'key_message': 'Menjaga kesehatan anak adalah ibadah',
        'implementation': [
            'Koordinasi dengan pengurus masjid',
            'Pelatihan ustaz tentang imunisasi',
            'Materi ceramah tentang kesehatan dalam Islam',
            'Pengumuman jadwal imunisasi setelah sholat'
        ]
    })
    
    # Cultural Arts Strategy
    plan['strategies'].append({
        'channel': 'Gending Sasak',
        'frequency': 'Acara budaya',
        'approach': 'Nyanyian tradisional dengan lirik edukasi kesehatan',
        'key_message': 'Belek imunisasi te anak kite',
        'implementation': [
            'Buat lirik gending tentang imunisasi',
            'Latih kader desa untuk menyanyikan',
            'Tampilkan di acara-acara desa',
            'Rekam dan sebarkan via WhatsApp'
        ]
    })
    
    return plan

def create_cultural_content_calendar():
    """Create content calendar based on Sasak cultural events"""
    
    current_month = datetime.now().month
    
    cultural_calendar = {
        1: {'event': 'Tahun Baru Sasak', 'message_theme': 'Resolusi kesehatan anak'},
        2: {'event': 'Bulan Pantang', 'message_theme': 'Perawatan ibu dan bayi'},
        3: {'event': 'Musim Tanam', 'message_theme': 'Kesehatan untuk produktivitas'},
        4: {'event': 'Bulan Ngaben', 'message_theme': 'Doa kesehatan keluarga'},
        5: {'event': 'Bulan Puasa', 'message_theme': 'Kesehatan selama puasa'},
        6: {'event': 'Lebaran Sasak', 'message_theme': 'Silaturahmi dan kesehatan'},
        7: {'event': 'Musim Panen', 'message_theme': 'Syukur kesehatan anak'},
        8: {'event': 'Bulan Kemerdekaan', 'message_theme': 'Anak sehat, bangsa kuat'},
        9: {'event': 'Bulan Pendidikan', 'message_theme': 'Anak sehat untuk sekolah'},
        10: {'event': 'Bulan Kesehatan', 'message_theme': 'Imunisasi lengkap'},
        11: {'event': 'Persiapan Panen', 'message_theme': 'Investasi kesehatan masa depan'},
        12: {'event': 'Akhir Tahun', 'message_theme': 'Evaluasi kesehatan anak'}
    }
    
    return cultural_calendar.get(current_month, {'event': 'Bulan Biasa', 'message_theme': 'Kesehatan rutin'})

def get_village_coordinator_contacts():
    """Get contact information for all village coordinators"""
    from models import Village
    
    coordinators = Village.query.filter(
        Village.kordinator_adat.isnot(None),
        Village.no_hp_kader.isnot(None)
    ).all()
    
    contact_list = []
    for village in coordinators:
        contact_list.append({
            'village': village.nama_desa,
            'coordinator': village.kordinator_adat,
            'phone': village.no_hp_kader,
            'role': 'Guru Adat/Koordinator Imunisasi'
        })
    
    return contact_list

def generate_adat_integration_report():
    """Generate report on traditional leader integration effectiveness"""
    from models import Village, Baby
    
    # Count babies registered from villages with active coordinators
    villages_with_coordinators = Village.query.filter(
        Village.kordinator_adat.isnot(None)
    ).all()
    
    village_names = [v.nama_desa for v in villages_with_coordinators]
    
    babies_with_coordinator_support = Baby.query.filter(
        Baby.desa.in_(village_names)
    ).count()
    
    total_babies = Baby.query.count()
    
    coordinator_impact = {
        'villages_with_coordinators': len(villages_with_coordinators),
        'babies_with_coordinator_support': babies_with_coordinator_support,
        'total_babies': total_babies,
        'coordinator_coverage_percentage': round((babies_with_coordinator_support / total_babies * 100), 2) if total_babies > 0 else 0
    }
    
    return coordinator_impact
from datetime import datetime, date, timedelta
from app import db
from models import Baby, Village
import logging

def get_village_coordinator_contacts():
    """Get village coordinator contact information"""
    try:
        coordinators = Village.query.filter(
            Village.kordinator_adat.isnot(None)
        ).all()
        
        return [{
            'village': coord.nama_desa,
            'coordinator': coord.kordinator_adat,
            'phone': coord.no_hp_kader,
            'code': coord.kode_desa
        } for coord in coordinators]
    except Exception as e:
        logging.error(f"Error getting coordinator contacts: {str(e)}")
        return []

def create_cultural_content_calendar():
    """Create culturally appropriate content calendar"""
    try:
        today = date.today()
        calendar_items = []
        
        # Generate weekly educational content
        for week in range(4):  # Next 4 weeks
            week_date = today + timedelta(weeks=week)
            
            # Rotate cultural themes
            themes = [
                "Belek Imunisasi te Anak Kite (Lengkapi Imunisasi Anak Kita)",
                "Anak Sehat, Desa Kuat - Tradisi Sasak",
                "Menangi Le, Bekelah Jadwal (Jangan Lupa, Tepati Jadwal)",
                "Gotong Royong untuk Kesehatan Anak"
            ]
            
            calendar_items.append({
                'date': week_date,
                'theme': themes[week % len(themes)],
                'content_type': 'educational_sms',
                'target': 'all_parents'
            })
        
        return calendar_items
    except Exception as e:
        logging.error(f"Error creating content calendar: {str(e)}")
        return []

def generate_adat_integration_report():
    """Generate report on traditional integration"""
    try:
        # Count babies by village with traditional coordinators
        villages_with_coordinators = Village.query.filter(
            Village.kordinator_adat.isnot(None)
        ).count()
        
        total_villages = Village.query.count()
        
        # Calculate coverage in villages with traditional support
        village_coverage = db.session.query(
            Baby.desa,
            db.func.count(Baby.id_bayi).label('baby_count')
        ).group_by(Baby.desa).all()
        
        return {
            'traditional_coverage': {
                'villages_with_coordinators': villages_with_coordinators,
                'total_villages': total_villages,
                'coverage_percentage': round(villages_with_coordinators / total_villages * 100, 2) if total_villages > 0 else 0
            },
            'village_engagement': [{
                'village': item.desa,
                'registered_babies': item.baby_count
            } for item in village_coverage]
        }
    except Exception as e:
        logging.error(f"Error generating adat integration report: {str(e)}")
        return {}

def generate_community_engagement_plan(village_name):
    """Generate community engagement plan for specific village"""
    try:
        # Get village data
        village = Village.query.filter_by(nama_desa=village_name).first()
        babies_in_village = Baby.query.filter_by(desa=village_name).count()
        
        # Basic engagement plan
        plan = {
            'village': village_name,
            'coordinator': village.kordinator_adat if village else None,
            'registered_babies': babies_in_village,
            'strategies': [
                {
                    'activity': 'Posyandu Bulanan dengan Nilai Adat',
                    'description': 'Integrasikan pemeriksaan kesehatan dengan ritual adat lokal',
                    'frequency': 'monthly'
                },
                {
                    'activity': 'Edukasi Melalui Tokoh Adat',
                    'description': 'Libatkan tokoh adat untuk menyampaikan pentingnya imunisasi',
                    'frequency': 'weekly'
                },
                {
                    'activity': 'SMS dengan Bahasa Sasak',
                    'description': 'Kirim reminder dalam bahasa Sasak dan Indonesia',
                    'frequency': 'as_needed'
                }
            ],
            'cultural_elements': [
                'Penggunaan pepatah Sasak dalam komunikasi',
                'Melibatkan ritual adat dalam kegiatan kesehatan',
                'Gotong royong untuk mobilisasi masyarakat'
            ]
        }
        
        return plan
    except Exception as e:
        logging.error(f"Error generating engagement plan: {str(e)}")
        return {}
