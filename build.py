"""Generates the inner pages (About, Services, Portfolio, project pages, Contact) from shared partials.
Run from the site folder:  python build.py
The homepage (index.html) is hand-written; this script only keeps its nav/footer in sync."""
import html, json, os, re

SITE = 'https://attractivehome.ae'
S3 = 'https://s3.ap-south-1.amazonaws.com/attractive.home.ae/'
WA = 'https://wa.me/971588840028?text=Hello%20Attractive%20Home%2C%20I%27d%20like%20to%20book%20a%20free%20design%20consultation.'
CATS = {'a': ('architectural', 'Architectural Design'), 'i': ('interior', 'Interior Design'), 'f': ('fit', 'Fit-Out Interiors')}
CAT_COPY = {
    'architectural': 'Architecture that pushes past the four walls. We use landscape, climate and terrain to shape villas that feel made for their plot.',
    'interior': 'Stylish, comfortable spaces that reflect our clients\' tastes and lifestyles. Visually striking, but also practical and welcoming.',
    'fit': 'Tailored, efficient fit-out delivery. Functionality and aesthetics built exactly as designed.',
}
# id, category, title, cover image (first photo of the project in the client's media library)
PROJECTS = [
 ('1784012461022','a',"Mr. Ahmed Baghoum's Villa",'media_mrkahghw_cplhj.webp'),
 ('1784015143789','a','Palm Jumeirah A3 Villa','media_mrkc4zv4_h2d63.webp'),
 ('1785226072508','a',"Mr. Khalid's Villa",'media_ms4czihw_2dld2.webp'),
 ('1785224307147','i',"Mr. Ibrahim El Hashmi's Villa",'media_ms4cgd6b_95iec.webp'),
 ('1785226307734','i',"Mr. El Hashmy's Villa",'media_ms4dnc1j_89n6s.webp'),
 ('1785226744769','i',"Mr. Mohamed El Maktom's Villa",'media_ms4dt2fy_d4uzk.webp'),
 ('1785227903874','i','El Sarh Office','media_ms4ekkl3_yk3q8.webp'),
 ('1785233442998','i',"Mr. Baloushi's Villa",'media_ms4htvkb_x1fpq.webp'),
 ('1782716582643','i',"Mr. El Zaroani's Villa",'media_5.webp'),
 ('1782717736180','i',"Mr. Rashid's Villa",'media_6.webp'),
 ('1782718563787','i',"Mrs. Soha's Villa",'media_1.webp'),
 ('1782109102785','i','Watch Fair','media_9.webp'),
 ('1783496200911','i',"Minister Rashed's Villa",'media_29.webp'),
 ('1783499059353','i',"Mr. El Tayeb's Villa",'media_3.webp'),
 ('1783499926338','i',"Mr. Salem's Villa",'media_31.webp'),
 ('1782113550818','i',"Mr. Wallid's Office",'media_12.webp'),
 ('1783504171550','i',"Mr. Srour's Villa",'media_40.webp'),
 ('1783502242563','i',"Mr. Mohamed Omar's Villa",'media_45.webp'),
 ('1783501164618','i',"Mr. Wahed's Villa",'media_9.webp'),
 ('1783513423844','i',"Mr. Nabras's Villa",'media_41.webp'),
 ('1783583324297','i',"Mr. Abdallah's Villa",'media_8.webp'),
 ('1783585404916','i',"Mr. Ali Al Shamsi's Villa",'media_79.webp'),
 ('1783588119212','i',"Mr. Mansour's Villa",'media_32.webp'),
 ('1783589807591','i',"Mr. Youssef's Villa",'media_61.webp'),
 ('1783846792086','i','A1 Villa','media_mrhkat5b_il0wo.webp'),
 ('1783848293647','i',"Mrs. Mithaa's Villa",'media_mrhl7awn_gmm2i.webp'),
 ('1783926600671','i',"Mr. Adib's Villa",'media_mrivj7bt_mfctq.webp'),
 ('1783932018284','i',"Mr. Ahmed El Haje's Villa",'media_mriwxmtc_0i3tk.webp'),
 ('1783933055521','i',"Mr. Ahmed Nasser's Villa",'media_mrizmdtb_8i201.webp'),
 ('1783933533344','i',"Mr. Hassan AbdAllah's Villa",'media_mrizvz7w_k7a5f.webp'),
 ('1783933776928','i',"Mr. Hussein Nasser's Villa",'media_mrj00ur4_oc18x.webp'),
 ('1783933871479','i',"Mr. Hussein's Villa",'media_mrj05tuy_de9pr.webp'),
 ('1783935072837','i',"Mr. Jaffar's Villa",'media_mrj0e9if_69439.webp'),
 ('1783937763553','i',"Mr. Samy's Villa",'media_mrj29dhd_wfuon.webp'),
 ('1783939723917','i',"Mr. Ziad El Haje's Villa",'media_mrj2lpfi_cc6vy.webp'),
 ('1783941260683','i',"Mrs. Hoda's Villa",'media_mrj4b3hx_tj97v.webp'),
 ('1783942475560','i',"Mrs. Suha's Villa",'media_mrj56eyw_ym54t.webp'),
 ('1783944357542','i',"Mr. Seif El Taresh's Villa",'media_mrj65i7n_m5p5c.webp'),
 ('1784712209838','i','Villa 112','media_mrvv6pj5_xwff0.webp'),
 ('1785149698110','i','Lighting Showroom','media_ms34170p_7pooa.webp'),
 ('1785157611196','i','Mzaree El Sham Restaurant','media_ms38qxs9_1ut7o.webp'),
 ('1785311507543','i',"Mr Waffi's Villa",'media_ms5rsj71_6zpga.webp'),
 ('1783590700136','f',"Mr. Dawoud's Villa",'media_4.webp'),
]
e = html.escape
CUR = ' aria-current="page"'
LOAD_EAGER = 'fetchpriority="high"'
LOAD_LAZY = 'loading="lazy"'
ACT = ' class="is-active" aria-current="page"'
def ppath(p): return f"/portfolio/{CATS[p[1]][0]}/project-{p[0]}/"
def pimg(p): return f"{S3}projects/{CATS[p[1]][0]}/project-{p[0]}/media/{p[3]}"
ALT_A = 'by Attractive Home'
ALT_B = 'project in the UAE by Attractive Home'
def pthumb(p, tail, eager=False):
    """Local 4:3 cover thumbnail (generated from the first project photo) with a small/large srcset."""
    return (f'<img src="/assets/pf/{p[0]}.webp" srcset="/assets/pf/{p[0]}-s.webp 480w, /assets/pf/{p[0]}.webp 960w" '
            f'sizes="(min-width:900px) 31vw, (min-width:561px) 46vw, 92vw" width="960" height="720" '
            f'{LOAD_EAGER if eager else LOAD_LAZY} decoding="async" alt="{e(p[2])}, {CATS[p[1]][1].lower()} {tail}">')

src = open('index.html', encoding='utf8').read()
SPRITE = re.search(r'<!-- SVG sprite -->.*?</svg>\n', src, re.S).group(0)
LOGO = '''<svg class="logo__mark" aria-hidden="true"><use href="#ah-mark"/></svg>
    <span class="logo__text"><span class="logo__name">Attractive Home</span><span class="logo__tag">Interior Design &amp; Fit-Out</span></span>'''
LINKS = [('About', '/about/'), ('Services', '/services/'), ('Portfolio', '/portfolio/'), ('Process', '/#process'), ('FAQ', '/#faq'), ('Contact', '/contacts/')]

def nav(active=''):
    li = '\n    '.join(f'<a href="{h}"{CUR if h == active else ""}>{t}</a>' for t, h in LINKS)
    return f'''<!-- ============ NAV ============ -->
<header class="nav" id="nav">
  <a class="logo" href="/" aria-label="Attractive Home, interior design and fit-out, home">
    {LOGO}
  </a>
  <nav class="nav__links" aria-label="Primary">
    {li}
  </nav>
  <a class="btn btn--cream btn--sm nav__cta" href="{WA}" target="_blank" rel="noopener">
    <svg aria-hidden="true"><use href="#i-wa"/></svg><span>Free consultation</span>
  </a>
  <button class="nav__burger" aria-label="Open menu" aria-expanded="false" aria-controls="menu"><span></span><span></span></button>
</header>

<div class="menu" id="menu" hidden>
  <nav aria-label="Mobile">
    {li}
  </nav>
  <div class="menu__foot">
    <a href="tel:+971588840028">+971 58 884 0028</a>
    <a href="mailto:info@attractivehome.ae">info@attractivehome.ae</a>
  </div>
</div>
'''

FOOTER = f'''<!-- ============ FOOTER ============ -->
<footer class="footer">
  <div class="wrap footer__grid">
    <div class="footer__brand">
      <a class="logo logo--lg" href="/" aria-label="Attractive Home, home">
        {LOGO}
      </a>
      <p>Dubai interior design studio and fit-out contractor. One team, from design to handover, since 2013.</p>
    </div>
    <nav aria-label="Services">
      <h4>Services</h4>
      <a href="/services/#architectural-design">Architectural Design</a>
      <a href="/services/#interior-design">Interior Design</a>
      <a href="/services/#fit-out">Fit-Out Interiors</a>
      <a href="/services/#joinery">Bespoke Joinery</a>
    </nav>
    <nav aria-label="Company">
      <h4>Studio</h4>
      <a href="/about/">About</a>
      <a href="/portfolio/">Portfolio</a>
      <a href="/#process">Process</a>
      <a href="/contacts/">Contact</a>
    </nav>
    <nav aria-label="Social">
      <h4>Follow</h4>
      <a href="https://www.instagram.com/attractive_home" target="_blank" rel="noopener">Instagram</a>
      <a href="https://www.tiktok.com/@attractivehome" target="_blank" rel="noopener">TikTok</a>
      <a href="https://www.facebook.com/attractive.home.interiors" target="_blank" rel="noopener">Facebook</a>
      <a href="https://www.linkedin.com/company/attractive-home-interior-studio/" target="_blank" rel="noopener">LinkedIn</a>
      <a href="https://pin.it/4dHNZjnCY" target="_blank" rel="noopener">Pinterest</a>
    </nav>
  </div>
  <div class="wrap footer__base">
    <span>© 2013–2026 Attractive Home. All rights reserved.</span>
    <span>{{note}}</span>
  </div>
</footer>

<!-- Floating actions -->
<a class="fab" href="{WA}" target="_blank" rel="noopener" aria-label="Chat with Attractive Home on WhatsApp">
  <svg aria-hidden="true"><use href="#i-wa"/></svg>
</a>
<div class="dock" aria-label="Quick contact">
  <a href="tel:+971588840028"><svg aria-hidden="true"><use href="#i-phone"/></svg>Call</a>
  <a class="dock__wa" href="{WA}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-wa"/></svg>WhatsApp us</a>
</div>
'''
NOTE_RENDER = 'Room images on this page are concept visualisations.'
NOTE_REAL = 'Project photography © Attractive Home.'

def cta(title='Tell us about <em>your space.</em>'):
    return f'''<section class="cta" aria-label="Book a consultation">
  <div class="wrap cta__in">
    <div>
      <p class="eyebrow eyebrow--light" data-reveal>Free design consultation</p>
      <h2 class="h2 h2--xl h2--light" data-split>{title}</h2>
    </div>
    <div class="cta__side" data-reveal>
      <p>We will come back with ideas, an indicative timeline and a clear price. No obligation.</p>
      <div class="hero__actions">
        <a class="btn btn--cream" href="{WA}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-wa"/></svg><span>Book on WhatsApp</span></a>
        <a class="btn btn--ghost" href="/contacts/"><span>Contact details</span><svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
      </div>
    </div>
  </div>
</section>'''

def hero(eyebrow, title, lead='', img=None, alt='', crumbs=()):
    media = ''
    if img:
        media = f'''<img class="hero__img" src="/assets/img/{img}.webp" width="1200" height="1500" alt="{e(alt)}" fetchpriority="high" decoding="async">
    <canvas class="hero__gl" id="hero-gl" aria-hidden="true"></canvas>
    <div class="hero__shade"></div>'''
    bc = ''
    if crumbs:
        items = ''.join(f'<li><a href="{h}">{e(t)}</a></li>' for t, h in crumbs[:-1]) + f'<li aria-current="page">{e(crumbs[-1][0])}</li>'
        bc = f'<nav class="crumbs" aria-label="Breadcrumb" data-reveal><ol>{items}</ol></nav>'
    return f'''<section class="hero hero--inner{'' if img else ' hero--plain'}" id="top">
  <div class="hero__media">
    {media}
  </div>
  <div class="hero__content wrap">
    {bc}
    <p class="eyebrow eyebrow--light" data-reveal>{eyebrow}</p>
    <h1 class="hero__title" data-split>{title}</h1>
    {f'<p class="hero__lead" data-reveal style="--d:.45s">{lead}</p>' if lead else ''}
  </div>
</section>'''

def page(path, title, desc, body, active='', crumbs=(), og='/assets/img/og.jpg', note=NOTE_RENDER, preload=None, extra_ld=None, scripts=''):
    url = SITE + path
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": t, "item": SITE + h} for i, (t, h) in enumerate(crumbs)]}] if crumbs else []
    if extra_ld: ld.append(extra_ld)
    ogurl = og if og.startswith('http') else SITE + og
    out = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#0f2434">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Attractive Home">
<meta property="og:locale" content="en_AE">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{ogurl}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{f'<link rel="preload" as="image" href="{preload}" fetchpriority="high">' if preload else ''}
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<link rel="stylesheet" href="/css/inner.css">
<script>document.documentElement.classList.add('js')</script>
{''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' + chr(10) for x in ld)}</head>
<body class="inner">

{SPRITE}
<a class="skip" href="#main">Skip to content</a>
<div class="loader" aria-hidden="true"><svg class="loader__mark"><use href="#ah-mark"/></svg></div>

{nav(active)}
<main id="main">
{body}
</main>

{FOOTER.replace('{note}', note)}
<script src="/js/app.js" defer></script>
{scripts}<script type="importmap">
{{ "imports": {{ "three": "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/" }} }}
</script>
<script type="module" src="/js/gl.js"></script>
</body>
</html>
'''
    d = path.strip('/')
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf8', newline='\n').write(out)
    return path

PAGES = []

# ------------------------------------------------------------------ ABOUT
about = hero('Who we are', 'A Dubai studio that designs it, <em>then builds it.</em>',
             'Since 2013, Attractive Home has been bringing creative architectural, interior and fit-out solutions that combine elegance, functionality and artistry.',
             'living', 'Living room designed and built by Attractive Home in Dubai', (('Home', '/'), ('About', '/about/'))) + f'''
<section class="section">
  <div class="wrap split">
    <div>
      <p class="eyebrow" data-reveal>Our approach</p>
      <h2 class="h2" data-split>One point of <em>accountability.</em></h2>
    </div>
    <div class="prose" data-reveal>
      <p class="prose__lead">We transform spaces into personalised expressions of style and comfort, for clients who want considered design and finishes that hold up over time.</p>
      <p>Attractive Home is a Dubai based interior design studio and fit-out contractor delivering complete residential and commercial interiors across the UAE. We have designed and built villas, apartments, offices and retail spaces since 2013.</p>
      <p>Our architects, interior designers, joinery specialists and site engineers handle concept design, 3D visualisation, technical drawings, authority approvals, procurement and full fit-out execution under one contract. You approve the design once, and the same team builds exactly what you approved.</p>
      <p>Whether you are furnishing a new handover in Dubai Hills Estate, renovating a family villa on Palm Jumeirah or fitting out a commercial space in Business Bay, we manage the project from the first sketch to the final handover.</p>
    </div>
  </div>
  <div class="wrap">
    <dl class="stats">
      <div class="stat" data-reveal><dt>Established</dt><dd><span data-count="2013" data-plain>2013</span></dd><p>More than a decade of interiors across Dubai and the wider Emirates.</p></div>
      <div class="stat" data-reveal style="--d:.08s"><dt>Projects</dt><dd><span data-count="100">100</span>+</dd><p>Villas, apartments, offices, showrooms and restaurants delivered.</p></div>
      <div class="stat" data-reveal style="--d:.16s"><dt>Contract</dt><dd><span data-count="1">1</span></dd><p>One team and one point of accountability from concept to handover.</p></div>
      <div class="stat" data-reveal style="--d:.24s"><dt>Languages</dt><dd><span data-count="4">4</span></dd><p>We work with clients in English, Arabic, French and Russian.</p></div>
    </dl>
  </div>
</section>

<section class="band">
  <div class="wrap">
    <header class="head">
      <p class="eyebrow eyebrow--light" data-reveal>The team behind your project</p>
      <h2 class="h2 h2--light" data-split>Four disciplines, <em>one studio.</em></h2>
    </header>
    <div class="roles">
      <article class="role" data-reveal><span>01</span><h3>Architects</h3><p>Space planning, concept layouts, elevations, full technical drawing sets and the documentation for municipality and developer approvals.</p></article>
      <article class="role" data-reveal style="--d:.08s"><span>02</span><h3>Interior designers</h3><p>Concept development, mood boards, material and finish selection, lighting design and photorealistic 3D visualisation.</p></article>
      <article class="role" data-reveal style="--d:.16s"><span>03</span><h3>Joinery specialists</h3><p>Bespoke wardrobes, kitchens, doors, wall panelling and feature units produced to your exact dimensions.</p></article>
      <article class="role" data-reveal style="--d:.24s"><span>04</span><h3>Site engineers</h3><p>Fit-out execution with scheduled progress updates and a named project manager from the first day on site to handover.</p></article>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <header class="head">
      <p class="eyebrow" data-reveal>Over 100 projects across Dubai</p>
      <h2 class="h2" data-split>Work you can <em>walk through.</em></h2>
      <p class="head__lead" data-reveal>From architectural and interior design to fit-out. A few recent projects from the portfolio.</p>
    </header>
    <ul class="pgrid pgrid--3">
      {''.join(f'<li class="pcard" data-reveal><a href="{ppath(p)}"><div class="pcard__img">{pthumb(p, ALT_A)}</div><p>{CATS[p[1]][1]}</p><h3>{e(p[2])}</h3></a></li>' for p in (PROJECTS[1], PROJECTS[5], PROJECTS[7]))}
    </ul>
    <a class="link" href="/portfolio/">View the full portfolio <svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
  </div>
</section>
''' + cta('Let\'s talk about <em>your project.</em>')
PAGES.append(page('/about/', 'About Attractive Home | Interior Design Studio in Dubai Since 2013',
     'Attractive Home is a Dubai interior design studio and fit-out contractor. Architects, designers, joinery specialists and site engineers under one contract since 2013.',
     about, '/about/', (('Home', '/'), ('About', '/about/')), preload='/assets/img/living.webp', note=NOTE_REAL + ' ' + NOTE_RENDER.replace('Room images', 'Header image').replace('are concept visualisations', 'is a concept visualisation')))

# ------------------------------------------------------------------ SERVICES
SERVICES = [
 ('architectural-design', 'Architectural Design', 'exterior', 'Contemporary villa architecture in Dubai',
  'Architectural design and space planning for new builds, extensions and structural reconfiguration. We prepare concept layouts, elevations, full technical drawing sets and the documentation required for municipality and developer approvals.',
  ['Concept layouts and space planning', 'Elevations and exterior design', 'Full technical drawing sets', 'Municipality and developer approvals']),
 ('interior-design', 'Interior Design', 'bedroom', 'Master bedroom interior design in a Dubai villa',
  'Concept development, mood boards, material and finish selection, lighting design, bespoke joinery drawings and photorealistic 3D visualisation. You see the finished space before a single wall is touched.',
  ['Concept development and mood boards', 'Material and finish selection', 'Lighting design', 'Photorealistic 3D visualisation']),
 ('fit-out', 'Fit-Out Interiors', 'fitout', 'Villa fit-out in progress in Dubai',
  'Turnkey fit-out execution covering civil works, MEP, ceilings, flooring, wall cladding, custom joinery, painting, furniture installation and final styling. One contract, one project manager, one handover date.',
  ['Civil works and MEP', 'Ceilings, flooring and wall cladding', 'Painting and furniture installation', 'One project manager, one handover date']),
 ('joinery', 'Furniture and Bespoke Joinery', 'joinery', 'Bespoke walnut joinery detail with brass handle',
  'Custom wardrobes, kitchens, doors, wall panelling and feature units produced to your dimensions.',
  ['Wardrobes and dressing rooms', 'Kitchens', 'Doors and wall panelling', 'Feature units']),
]
CAPS = [
 ('Construction Management', 'Expert management of construction projects ensuring quality and efficiency.'),
 ('Remodeling', 'Transform your spaces with our high-quality remodeling services.'),
 ('Flooring Installation', 'Professional installation of durable and stylish flooring options.'),
 ('Exterior Design', 'Transform outdoor spaces with stunning and functional exterior designs.'),
 ('Fit-Out', 'Customized fit-out solutions for commercial and residential spaces.'),
 ('Interior Design', 'Creative and functional interior design solutions tailored to your style and needs.'),
 ('Plumbing Fixture Installation', 'Efficient installation of plumbing fixtures for kitchens, bathrooms and more.'),
 ('Site Excavation', 'Accurate and efficient excavation services for all types of construction sites.'),
 ('Interior Structural Repairs', 'Expert repairs to maintain the integrity and safety of your building.'),
 ('Exterior Painting', 'High-quality exterior painting services to refresh and protect your building.'),
 ('MEP Solutions', 'Comprehensive mechanical, electrical and plumbing solutions for efficient systems.'),
 ('Shop Drawings', 'Accurate shop drawings for precise construction and manufacturing.'),
]
rows = ''
for i, (sid, name, img, alt, text, pts) in enumerate(SERVICES):
    rows += f'''
    <article class="row{' row--rev' if i % 2 else ''}" id="{sid}">
      <div class="row__media" data-reveal><img src="/assets/img/{img}.webp" loading="lazy" decoding="async" alt="{e(alt)}"></div>
      <div class="row__body">
        <span class="row__no" data-reveal>0{i+1}</span>
        <h2 class="h2" data-split>{e(name)}</h2>
        <p data-reveal>{e(text)}</p>
        <ul class="ticks" data-reveal>{''.join(f'<li>{e(x)}</li>' for x in pts)}</ul>
      </div>
    </article>'''
services = hero('What we do', 'Interior design and fit-out services, <em>under one contract.</em>',
                'Four connected services delivered by one team, so nothing is lost between the design you approved and the space you receive.',
                'joinery', 'Bespoke joinery detail by Attractive Home', (('Home', '/'), ('Services', '/services/'))) + f'''
<section class="section">
  <div class="wrap rows">{rows}
  </div>
</section>

<section class="band">
  <div class="wrap">
    <header class="head">
      <p class="eyebrow eyebrow--light" data-reveal>Also in scope</p>
      <h2 class="h2 h2--light" data-split>Everything a project needs, <em>handled in-house.</em></h2>
    </header>
    <ul class="caps">
      {''.join(f'<li data-reveal style="--d:{(i%4)*.06:.2f}s"><h3>{e(n)}</h3><p>{e(t)}</p></li>' for i, (n, t) in enumerate(CAPS))}
    </ul>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div>
      <p class="eyebrow" data-reveal>How it comes together</p>
      <h2 class="h2" data-split>Five steps from consultation <em>to handover.</em></h2>
      <a class="link" href="/#process" data-reveal>See the process in motion <svg aria-hidden="true"><use href="#i-arrow"/></svg></a>
    </div>
    <ol class="plist">
      <li data-reveal><span>01</span><div><h3>Free Consultation</h3><p>We meet at your space or on a call and agree the scope, timeline and budget range.</p></div></li>
      <li data-reveal><span>02</span><div><h3>Concept and 3D Design</h3><p>Layouts, material boards and photorealistic 3D renders, revised until the design is right.</p></div></li>
      <li data-reveal><span>03</span><div><h3>Drawings and Approvals</h3><p>The full technical drawing set, plus municipality and developer approvals on your behalf.</p></div></li>
      <li data-reveal><span>04</span><div><h3>Fit-Out Execution</h3><p>Our site team builds the approved design with a named project manager throughout.</p></div></li>
      <li data-reveal><span>05</span><div><h3>Handover</h3><p>Final snagging, deep clean and styling, on the date we committed to.</p></div></li>
    </ol>
  </div>
</section>
''' + cta()
svc_ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Interior design and fit-out services in Dubai",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Service", "name": s[1], "description": s[4], "url": f"{SITE}/services/#{s[0]}",
                               "provider": {"@id": SITE + "/#business"}, "areaServed": "Dubai, United Arab Emirates"}} for i, s in enumerate(SERVICES)]}
PAGES.append(page('/services/', 'Interior Design & Fit-Out Services in Dubai | Attractive Home',
     'Architectural design, interior design, turnkey fit-out and bespoke joinery in Dubai, delivered by one team under one contract. See what each service includes.',
     services, '/services/', (('Home', '/'), ('Services', '/services/')), preload='/assets/img/joinery.webp', extra_ld=svc_ld))

# ------------------------------------------------------------------ PORTFOLIO (+ category pages)
def cards(items):
    return '\n      '.join(
        f'<li class="pcard" data-cat="{CATS[p[1]][0]}"><a href="{ppath(p)}"><div class="pcard__img">{pthumb(p, ALT_B, i < 3)}</div><p>{CATS[p[1]][1]}</p><h3>{e(p[2])}</h3></a></li>'
        for i, p in enumerate(items))
def filters(active):
    n = {k: sum(1 for p in PROJECTS if CATS[p[1]][0] == k) for k in ('architectural', 'interior', 'fit')}
    opts = [('', 'All projects', len(PROJECTS), '/portfolio/'), ('architectural', 'Architectural', n['architectural'], '/portfolio/architectural/'),
            ('interior', 'Interior', n['interior'], '/portfolio/interior/'), ('fit', 'Fit-out', n['fit'], '/portfolio/fit/')]
    return '<nav class="filters" aria-label="Filter projects" data-reveal>' + ''.join(
        f'<a href="{h}" data-filter="{k}"{ACT if k == active else ""}>{t}<sup>{c}</sup></a>' for k, t, c, h in opts) + '</nav>'
def portfolio(cat=''):
    items = [p for p in PROJECTS if not cat or CATS[p[1]][0] == cat]
    name = next((v[1] for v in CATS.values() if v[0] == cat), '')
    crumbs = (('Home', '/'), ('Portfolio', '/portfolio/')) + (((name, f'/portfolio/{cat}/'),) if cat else ())
    ttl = f'{name} <em>projects.</em>' if cat else 'Homes, offices and showrooms <em>we have delivered.</em>'
    lead = CAT_COPY[cat] if cat else 'Over 100 projects across Dubai and the wider Emirates since 2013. Every photo on this page is from a real Attractive Home project.'
    body = hero('Portfolio', ttl, lead, None, '', crumbs) + f'''
<section class="section section--tight">
  <div class="wrap">
    {filters(cat)}
    <ul class="pgrid" id="pgrid">
      {cards(items)}
    </ul>
  </div>
</section>
''' + cta('Your project <em>could be next.</em>')
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": (name + ' projects' if cat else 'Portfolio') + ' | Attractive Home',
          "url": SITE + (f'/portfolio/{cat}/' if cat else '/portfolio/'),
          "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "url": SITE + ppath(p), "name": p[2]} for i, p in enumerate(items)]}}
    t = f'{name} Projects in Dubai | Attractive Home Portfolio' if cat else 'Interior Design & Fit-Out Portfolio Dubai | Attractive Home'
    dsc = (f'{name} projects by Attractive Home in Dubai and the UAE. ' + CAT_COPY[cat]) if cat else 'Browse villas, offices, showrooms and restaurants designed and built by Attractive Home across Dubai and the UAE. Real project photography.'
    return page(f'/portfolio/{cat}/' if cat else '/portfolio/', t, dsc[:158], body, '/portfolio/', crumbs, og=pimg(items[0]), note=NOTE_REAL,
                extra_ld=ld, scripts='<script src="/js/pages.js" defer></script>\n')
PAGES.append(portfolio())
for c in ('architectural', 'interior', 'fit'): PAGES.append(portfolio(c))

# ------------------------------------------------------------------ PROJECT PAGES
for i, p in enumerate(PROJECTS):
    cat, cname = CATS[p[1]]
    prev, nxt = PROJECTS[i - 1], PROJECTS[(i + 1) % len(PROJECTS)]
    crumbs = (('Home', '/'), ('Portfolio', '/portfolio/'), (cname, f'/portfolio/{cat}/'), (p[2], ppath(p)))
    body = hero(cname, e(p[2]), '', None, '', crumbs) + f'''
<section class="section section--tight">
  <div class="wrap">
    <div class="gallery" id="gallery" data-src="{S3}projects/{cat}/project-{p[0]}/metadata.json" data-base="{S3}" data-title="{e(p[2])}">
      <div class="gallery__grid"><a href="{pimg(p)}">{pthumb(p, ALT_A, True)}</a></div>
    </div>
    <nav class="pnav" aria-label="More projects">
      <a href="{ppath(prev)}"><small>Previous project</small><span>{e(prev[2])}</span></a>
      <a href="/portfolio/" class="pnav__all">All projects</a>
      <a href="{ppath(nxt)}"><small>Next project</small><span>{e(nxt[2])}</span></a>
    </nav>
  </div>
</section>
''' + cta('Want something <em>like this?</em>')
    ld = {"@context": "https://schema.org", "@type": "CreativeWork", "name": p[2], "genre": cname, "image": pimg(p), "url": SITE + ppath(p),
          "creator": {"@id": SITE + "/#business"}}
    PAGES.append(page(ppath(p), f'{p[2]} | {cname} Project by Attractive Home',
         f'{p[2]}: a {cname.lower()} project by Attractive Home, the Dubai interior design studio and fit-out contractor. View the full photo gallery.',
         body, '/portfolio/', crumbs, og=pimg(p), note=NOTE_REAL, extra_ld=ld, scripts='<script src="/js/pages.js" defer></script>\n'))

# ------------------------------------------------------------------ CONTACT
contact = hero('Contact', 'Tell us about <em>your space.</em>',
               'Discussing your project does not oblige you to anything. We will tell you about ourselves and the options for your ideas, and you decide.',
               None, '', (('Home', '/'), ('Contact', '/contacts/'))) + f'''
<section class="section section--tight">
  <div class="wrap contact2">
    <div>
      <address class="nap" data-reveal>
        <a href="{WA}" target="_blank" rel="noopener"><small>WhatsApp</small>+971 58 884 0028</a>
        <a href="tel:+971588840028"><small>Call</small>+971 58 884 0028</a>
        <a href="mailto:info@attractivehome.ae"><small>Email</small>info@attractivehome.ae</a>
        <a href="https://www.google.com/maps/search/?api=1&query=79P6%2B86+Dubai" target="_blank" rel="noopener"><small>Studio</small>79P6+86, Al Nahda 1, Al Qusais, Dubai, United Arab Emirates</a>
      </address>
      <p class="nap__note" data-reveal>Replies within business hours, seven days a week.</p>
      <div class="map" data-reveal>
        <iframe title="Attractive Home studio location on Google Maps" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://www.google.com/maps?q=79P6%2B86+Dubai&z=15&output=embed"></iframe>
      </div>
    </div>
    <form class="form form--page" id="lead" data-reveal novalidate>
      <h2>Start on WhatsApp</h2>
      <label class="field"><span>Your name</span><input name="name" type="text" autocomplete="name" required placeholder="Full name"></label>
      <label class="field"><span>Phone number</span><input name="phone" type="tel" autocomplete="tel" inputmode="tel" placeholder="+971"></label>
      <fieldset class="chips"><legend>Project type</legend>
        <label><input type="radio" name="type" value="Villa" checked><span>Villa</span></label>
        <label><input type="radio" name="type" value="Apartment"><span>Apartment</span></label>
        <label><input type="radio" name="type" value="Office"><span>Office</span></label>
        <label><input type="radio" name="type" value="Retail / F&amp;B"><span>Retail / F&amp;B</span></label>
      </fieldset>
      <fieldset class="chips"><legend>What do you need?</legend>
        <label><input type="radio" name="scope" value="Design and fit-out" checked><span>Design + fit-out</span></label>
        <label><input type="radio" name="scope" value="Design only"><span>Design only</span></label>
        <label><input type="radio" name="scope" value="Joinery"><span>Joinery</span></label>
      </fieldset>
      <label class="field"><span>Location and details <em>(optional)</em></span><textarea name="msg" rows="3" placeholder="e.g. 4-bedroom villa in Dubai Hills, handover in March"></textarea></label>
      <button class="btn btn--wa btn--block" type="submit"><svg aria-hidden="true"><use href="#i-wa"/></svg><span>Send on WhatsApp</span></button>
      <p class="form__note">Opens WhatsApp with your message ready to send. Nothing is stored on this site.</p>
    </form>
  </div>
</section>
'''
PAGES.append(page('/contacts/', 'Contact Attractive Home | Free Interior Design Consultation in Dubai',
     'Book a free design consultation with Attractive Home in Dubai. WhatsApp or call +971 58 884 0028, email info@attractivehome.ae, or visit the studio in Al Nahda 1.',
     contact, '/contacts/', (('Home', '/'), ('Contact', '/contacts/')), note='© Attractive Home'))

# ------------------------------------------------------------------ keep homepage nav / footer in sync
h = src
h = re.sub(r'<!-- ============ NAV ============ -->.*?</div>\n\n<main', nav('/').replace('\\', '\\\\') + '\n<main', h, flags=re.S)
h = re.sub(r'<!-- ============ FOOTER ============ -->.*?</div>\n\n<script src', (FOOTER.replace('{note}', 'Homepage images are concept visualisations.')).replace('\\', '\\\\') + '\n<script src', h, flags=re.S)
for a, b in [('href="css/', 'href="/css/'), ('src="js/', 'src="/js/'), ('src="assets/', 'src="/assets/'), ('href="assets/', 'href="/assets/'),
             ('srcset="assets/', 'srcset="/assets/'), (', assets/', ', /assets/'), ('url(assets/', 'url(/assets/'), ('href="site.webmanifest"', 'href="/site.webmanifest"'),
             ('href="https://attractivehome.ae/portfolio"', 'href="/portfolio/"')]:
    h = h.replace(a, b)
open('index.html', 'w', encoding='utf8', newline='\n').write(h)

# ------------------------------------------------------------------ sitemap
urls = ['/'] + PAGES
open('sitemap.xml', 'w', encoding='utf8', newline='\n').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>2026-11-24</lastmod></url>\n' for u in urls) + '</urlset>\n')
print(len(PAGES), 'pages written')
