"""Arabic strings for the site.
en_core.txt / ar_core.txt hold the main copy as parallel lines (line N of one translates line N of the other).
EXTRA adds short UI strings, ROOMS the room names used in project galleries, PATTERNS the generated text."""
import os, re

_here = os.path.dirname(os.path.abspath(__file__))
_rd = lambda f: [x for x in open(os.path.join(_here, f), encoding='utf8').read().split('\n') if x != '']
_en, _ar = _rd('en_core.txt'), _rd('ar_core.txt')
assert len(_en) == len(_ar), 'en_core.txt and ar_core.txt must have the same number of lines'
STRINGS = dict(zip(_en, _ar))

BRAND = 'Attractive Home'
CAT = {'architectural design': 'تصميم معماري', 'interior design': 'تصميم داخلي', 'fit-out interiors': 'تنفيذ وتشطيبات داخلية'}

EXTRA = {
    'Our': 'مشاريعنا في',
    'architectural design projects.': 'التصميم المعماري.',
    'interior design projects.': 'التصميم الداخلي.',
    'fit-out interiors projects.': 'التنفيذ والتشطيبات الداخلية.',
    'Scope': 'نطاق العمل', 'Spaces': 'المساحات', 'Gallery': 'معرض الصور',
    'More projects': 'مشاريع أخرى', 'Previous project': 'المشروع السابق', 'Next project': 'المشروع التالي',
    'Want something': 'هل تريد شيئاً', 'like this?': 'مثل هذا؟',
    'Mr. Ibrahim El Hashmi\'s Villa': 'فيلا السيد إبراهيم الهاشمي',
    'WhatsApp': 'واتساب', 'English': 'English',
    'Architectural Design Projects': 'مشاريع التصميم المعماري',
}
STRINGS.update(EXTRA)

ROOMS = {
    'Lobby': 'اللوبي', 'Ground Hall': 'صالة الطابق الأرضي', 'Majlis': 'المجلس', 'Dining': 'غرفة الطعام', 'Office': 'المكتب',
    'Kitchen': 'المطبخ', 'Dirty Kitchen': 'المطبخ التحضيري', 'Livingroom': 'غرفة المعيشة', 'Gym': 'النادي الرياضي',
    'Prayer Room': 'المصلى', 'Bedroom 1': 'غرفة النوم 1', 'Bedroom 2': 'غرفة النوم 2', 'Bedroom 3': 'غرفة النوم 3',
    'Bedroom 4': 'غرفة النوم 4', 'Guest Bedroom': 'غرفة نوم الضيوف', 'Hall': 'الصالة', 'Living': 'المعيشة',
    'Landscape': 'تنسيق الحدائق', 'Master Bedroom': 'غرفة النوم الرئيسية', 'Entrance': 'المدخل', 'Guest Room': 'غرفة الضيوف',
    'Familly sitting': 'جلسة العائلة', 'Pantry': 'غرفة التحضير', 'Salon': 'الصالون', 'Bedroom': 'غرفة النوم',
    "Mira's Bedroom": 'غرفة نوم ميرا', 'Eissa Bedroom': 'غرفة نوم عيسى', 'Hall & Kitchen': 'الصالة والمطبخ',
    'Girl Bedroom': 'غرفة نوم البنت', 'Laundry': 'غرفة الغسيل', 'Master Bathroom': 'الحمام الرئيسي', 'Bathroom 1': 'الحمام 1',
    'Bathroom 2': 'الحمام 2', 'Guest Bathroom': 'حمام الضيوف', 'Play': 'غرفة الألعاب', 'Z-First': 'الطابق الأول',
    'Entrance & Living': 'المدخل والمعيشة', 'Bathroom': 'الحمام', 'Boy Bedroom 1': 'غرفة نوم الولد 1',
    'Boy Bedroom 2': 'غرفة نوم الولد 2', 'Hall Roof': 'صالة السطح', 'Laundry Room': 'غرفة الغسيل', 'Men Majlis': 'مجلس الرجال',
    'Omer Bedroom': 'غرفة نوم عمر', 'Boy Bedroom': 'غرفة نوم الولد', 'Ground': 'الطابق الأرضي', 'First Floor': 'الطابق الأول',
    'Ground Floor': 'الطابق الأرضي',
}
_rooms_l = {k.lower(): v for k, v in ROOMS.items()}

def _room(m, tr): return ROOMS.get(m.group(0))
def _rooms(m, tr):
    parts = m.group(0).split(', ')
    return '، '.join(ROOMS[p] for p in parts) if len(parts) > 1 and all(p in ROOMS for p in parts) else None
def _name(n, tr): return STRINGS.get(n)
def _alt(m, tr):
    name, room, cat = _name(m.group(1), tr), m.group(2), CAT.get(m.group(3))
    if not name or not cat: return None
    if room:
        r = _rooms_l.get(room[2:])
        if not r: return None
        return f'{name}، {r}، {cat} من {BRAND}'
    return f'{name}، مشروع {cat} من {BRAND}'
def _title(m, tr):
    name, cat = _name(m.group(1), tr), CAT.get(m.group(2).lower())
    return f'{name} | مشروع {cat} من {BRAND}' if name and cat else None
def _desc(m, tr):
    name, cat = _name(m.group(1), tr), CAT.get(m.group(2))
    return (f'{name}: مشروع {cat} من {BRAND}، استوديو التصميم الداخلي ومقاول التشطيبات في دبي. شاهد صور المشروع.') if name and cat else None
def _photos(m, tr):
    n = int(m.group(1)); return f'{n} صور' if 3 <= n <= 10 else f'{n} صورة'

_C = '(architectural design|interior design|fit-out interiors)'
PATTERNS = [
    (re.compile(r'^(\d+) photos$'), _photos),
    (re.compile(r'^(.+?)(, [^,]+)?, ' + _C + r'(?: project in the UAE)? by Attractive Home$'), _alt),
    (re.compile(r'^(.+) \| (Architectural Design|Interior Design|Fit-Out Interiors) Project by Attractive Home$'), _title),
    (re.compile(r'^(.+): a ' + _C + r' project by Attractive Home, the Dubai interior design studio and fit-out contractor\. View the project photos\.$'), _desc),
    (re.compile(r'^.+$'), _room),
    (re.compile(r'^.+, .+$'), _rooms),
]

# Arabic text for the pre-filled WhatsApp messages
WA = {
    "Hello%20Attractive%20Home%2C%20I%27d%20like%20to%20book%20a%20free%20design%20consultation.": 'مرحباً Attractive Home، أرغب في حجز استشارة تصميم مجانية.',
    "Hello%20Attractive%20Home%2C%20I%20have%20a%20question%20about%20my%20project.": 'مرحباً Attractive Home، لدي سؤال عن مشروعي.',
}
