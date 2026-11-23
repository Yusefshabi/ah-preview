"""Arabic generation: walks the built English HTML and swaps every text node / translatable attribute
using the dictionary in ar_strings.py.  Used by build.py; can also list anything still untranslated:
    python i18n.py            -> prints untranslated strings across all English pages"""
import glob, html, json, os, re, sys, urllib.parse

TAG = re.compile(r'(<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|<[^>]+>)', re.S)
ATTRS = ('alt', 'aria-label', 'placeholder', 'title', 'value')
META = ('description', 'og:title', 'og:description', 'og:image:alt', 'twitter:title', 'twitter:description')
LATIN = re.compile(r'[A-Za-z]')
KEEP = re.compile(r'^(Attractive Home|[\w.+-]+@[\w.-]+|[\d\s+/–—.,:%×x-]+|Instagram|TikTok|Facebook|LinkedIn|Pinterest|A1|EN|English)$')
LTR = re.compile(r'(\+971[\d ]+\d|79P6\+86|\d+\s?[–-]\s?\d+|\d+ / \d+)')
SKIP_HREF = re.compile(r'^/(assets|css|js|ar)/|^/site\.webmanifest|^/robots|^/sitemap')

def norm(s): return re.sub(r'\s+', ' ', html.unescape(s)).strip()

class Translator:
    def __init__(self, strings, patterns):
        self.s, self.p, self.missing = strings, patterns, {}
    def t(self, text, where=''):
        k = norm(text)
        if not k or not LATIN.search(k) or KEEP.match(k): return None
        if k in self.s: return self.s[k]
        for rx, fn in self.p:
            m = rx.match(k)
            if m:
                r = fn(m, self)
                if r is not None: return r
        self.missing.setdefault(k, where)
        return None
    def text(self, raw, where, plain=False):
        r = self.t(raw, where)
        if r is None:                                    # nothing to translate, but keep numbers left-to-right
            return raw if plain else LTR.sub(lambda m: f'<bdi dir="ltr">{m.group(1)}</bdi>', raw)
        out = html.escape(r, quote=False)
        if not plain: out = LTR.sub(lambda m: f'<bdi dir="ltr">{m.group(1)}</bdi>', out)
        lead, trail = raw[:len(raw) - len(raw.lstrip())], raw[len(raw.rstrip()):]
        return lead + out + trail
    def attr(self, v, where):
        r = self.t(v, where)
        return v if r is None else html.escape(r, quote=True)
    def ld(self, node):
        if isinstance(node, dict): return {k: (v if k in ('@type', '@id', '@context', 'url', 'logo', 'image', 'telephone', 'email', 'sameAs', 'item', 'priceRange', 'foundingDate', 'knowsLanguage', 'addressCountry') else self.ld(v)) for k, v in node.items()}
        if isinstance(node, list): return [self.ld(x) for x in node]
        if isinstance(node, str):
            if node == 'en': return 'ar'
            r = self.t(node, 'json-ld'); return node if r is None else r
        return node

def translate(src, path, tr, site, wa=None):
    """src: English HTML of the page at `path` (e.g. /about/). Returns Arabic HTML for /ar + path."""
    parts, out, where, plain = TAG.split(src), [], path, False
    for i, part in enumerate(parts):
        if i % 2 == 0:                                   # text node
            out.append(tr.text(part, where, plain) if part.strip() else part); plain = False; continue
        low = part[:40].lower()
        if low.startswith('<script'):
            if 'application/ld+json' in part[:80]:
                m = re.match(r'(<script[^>]*>)(.*)(</script>)', part, re.S)
                data = tr.ld(json.loads(m.group(2)))
                part = m.group(1) + json.dumps(data, ensure_ascii=False).replace(site + '/', site + '/ar/').replace(site + '/ar/assets', site + '/assets').replace(site + '/ar/#', site + '/#') + m.group(3)
            out.append(part); continue
        if low.startswith('<style') or low.startswith('<!--') or low.startswith('</'):
            out.append(part); continue
        if low.startswith('<title'): out.append(part); plain = True; continue
        if low.startswith('<meta'):
            m = re.search(r'(?:name|property)="([^"]+)"', part)
            if m and m.group(1) in META:
                part = re.sub(r'content="([^"]*)"', lambda c: 'content="' + tr.attr(c.group(1), where) + '"', part)
            elif m and m.group(1) == 'og:locale': part = part.replace('en_AE', 'ar_AE')
            elif m and m.group(1) == 'og:url': part = part.replace(site + '/', site + '/ar/')
            out.append(part); continue
        for a in ATTRS:                                  # translatable attributes
            if a + '="' in part:
                if a == 'value' and 'type="radio"' not in part: continue
                part = re.sub(r'(\s' + a + r')="([^"]*)"', lambda c: c.group(1) + '="' + tr.attr(c.group(2), where) + '"', part)
        if low.startswith('<html'): part = '<html lang="ar" dir="rtl">'
        if 'class="lang"' in part:                       # language switcher -> points back to English
            part = re.sub(r'href="[^"]*"', f'href="{path}"', part).replace('hreflang="ar"', 'hreflang="en"').replace('lang="ar"', 'lang="en"')
        elif low.startswith('<link') and ('rel="canonical"' in part): part = part.replace(site + '/', site + '/ar/')
        elif low.startswith('<link') and 'hreflang' in part: pass
        elif low.startswith('<a') or low.startswith('<form'):
            part = re.sub(r'href="(/[^"]*)"', lambda h: h.group(0) if SKIP_HREF.match(h.group(1)) else f'href="/ar{h.group(1)}"', part)
        out.append(part)
    res = ''.join(out)
    # <title> text is a text node already handled; switcher label; Arabic fonts + RTL stylesheet
    res = res.replace('>العربية</a>', '>English</a>')
    res = res.replace('family=Inter:wght@300..700&family=Instrument+Serif:ital@0;1', 'family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&family=Amiri:wght@400;700&family=Instrument+Serif&family=Inter:wght@600')
    for en_q, ar_text in (wa or {}).items(): res = res.replace(en_q, urllib.parse.quote(ar_text, safe=''))
    res = res.replace('</head>', '<link rel="stylesheet" href="/css/rtl.css">\n</head>', 1)
    return res

if __name__ == '__main__':
    import ar_strings
    tr = Translator(ar_strings.STRINGS, ar_strings.PATTERNS)
    pages = ['index.html'] + [p for p in glob.glob('**/index.html', recursive=True) if not p.replace('\\', '/').startswith('ar/') and p != 'index.html']
    for p in pages:
        path = '/' + p.replace('\\', '/').replace('index.html', '')
        translate(open(p, encoding='utf8').read(), path, tr, 'https://attractivehome.ae')
    for k, w in tr.missing.items(): print(f'{w}\t{k}')
    print(len(tr.missing), 'untranslated', file=sys.stderr)
