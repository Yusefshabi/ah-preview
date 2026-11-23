"""One-off: pick up to MAX photos per project from the studio's media library, save web-sized copies
into assets/g/<project-id>/ and write gallery.json for build.py.  Resumable.  Run from the site folder."""
import concurrent.futures as cf, io, json, os, re, urllib.request
from PIL import Image

MAX = 10
S3 = 'https://s3.ap-south-1.amazonaws.com/attractive.home.ae/'
C = {'a': 'architectural', 'i': 'interior', 'f': 'fit'}
rows = re.findall(r"\('(\d+)','([aif])',", open('build.py', encoding='utf8').read())
out = json.load(open('gallery.json', encoding='utf8')) if os.path.exists('gallery.json') else {}

def get(url):
    for attempt in range(3):
        try:
            return urllib.request.urlopen(url, timeout=90).read()
        except Exception as ex:
            err = ex
    raise err

def pick(meta):
    media = [m['src'] for m in meta.get('media', []) if m.get('type') == 'image']
    if not media: return []
    key = lambda s: s.split('/')[-1].rsplit('.', 1)[0]
    groups, used = [], set()
    for s in meta.get('sections') or []:
        keys = set(s.get('keys') or [])
        items = [m for m in media if key(m) in keys]
        used.update(items)
        if items: groups.append(((s.get('names') or {}).get('en', ''), items))
    rest = [m for m in media if m not in used]
    if groups:
        if rest: groups.append(('', rest))
        picks, i = [], 0
        while len(picks) < MAX and any(len(g[1]) > i for g in groups):   # round-robin across rooms
            for name, items in groups:
                if len(items) > i and len(picks) < MAX: picks.append((items[i], name))
            i += 1
        cover = media[0]
        picks.sort(key=lambda p: p[0] != cover)                          # cover photo first
        return picks
    k = min(MAX, len(media))
    idx = sorted({round(j * (len(media) - 1) / max(1, k - 1)) for j in range(k)})
    return [(media[j], '') for j in idx]

def one(args):
    pid, n, src, room = args
    d = f'assets/g/{pid}'; os.makedirs(d, exist_ok=True)
    big, small = f'{d}/{n}.webp', f'{d}/{n}-s.webp'
    if not (os.path.exists(big) and os.path.exists(small)):
        im = Image.open(io.BytesIO(get(S3 + src))).convert('RGB')
        for path, w, q in ((big, 1600, 72), (small, 640, 70)):
            t = im.copy(); t.thumbnail((w, w * 2), Image.LANCZOS); t.save(path, quality=q, method=5)
    w, h = Image.open(big).size
    return {'n': n, 'w': w, 'h': h, 'room': room}

for pid, c in rows:
    if pid in out: continue
    meta = json.loads(get(f'{S3}projects/{C[c]}/project-{pid}/metadata.json'))
    picks = pick(meta)
    with cf.ThreadPoolExecutor(6) as ex:
        out[pid] = list(ex.map(one, [(pid, n + 1, src, room) for n, (src, room) in enumerate(picks)]))
    json.dump(out, open('gallery.json', 'w', encoding='utf8'), indent=0)
    print(pid, len(out[pid]), flush=True)

tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk('assets/g') for f in fs)
print('projects', len(out), 'photos', sum(len(v) for v in out.values()), 'MB', round(tot / 1e6, 1))
