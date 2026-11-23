/* Attractive Home — core interactions (no dependencies) */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var AH = window.AH = { process: { p: 0, a: 0, b: 0 }, scroll: 0, listeners: [] };

  /* ---------- word splitting ---------- */
  function split(el) {
    var i = 0;
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var frag = d.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.appendChild(d.createTextNode(' ')); return; }
            var w = d.createElement('span'); w.className = 'w';
            var inner = d.createElement('span'); inner.textContent = part; inner.style.setProperty('--i', i++);
            w.appendChild(inner); frag.appendChild(w);
          });
          node.replaceChild(frag, n);
        } else if (n.nodeType === 1) walk(n);
      });
    })(el);
  }
  $$('[data-split]').forEach(split);

  /* statement: word-by-word highlight */
  var statement = $('[data-words]'), sWords = [];
  if (statement) {
    var txt = statement.textContent.trim().split(/\s+/);
    statement.textContent = '';
    txt.forEach(function (w, i) {
      var s = d.createElement('span'); s.className = 'sw'; s.textContent = w;
      statement.appendChild(s); if (i < txt.length - 1) statement.appendChild(d.createTextNode(' '));
      sWords.push(s);
    });
  }

  /* ---------- reveal on view ---------- */
  var revealEls = $$('[data-reveal],[data-split]');
  var heroEls = $$('.hero [data-reveal],.hero [data-split]');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { if (heroEls.indexOf(el) < 0) io.observe(el); });
  } else revealEls.forEach(function (el) { el.classList.add('in'); });

  /* ---------- ready / loader ---------- */
  var readied = false;
  function ready() {
    if (readied) return; readied = true;
    root.classList.add('is-ready'); AH.readyAt = Math.round(performance.now());
    setTimeout(function () { heroEls.forEach(function (el) { el.classList.add('in'); }); }, 250);
  }
  var heroImg = $('.hero__img');
  if (heroImg && heroImg.complete) setTimeout(ready, 350);
  else if (heroImg) heroImg.addEventListener('load', function () { setTimeout(ready, 200); });
  setTimeout(ready, 1600);

  /* ---------- counters ---------- */
  $$('[data-count]').forEach(function (el) {
    var to = +el.dataset.count, plain = el.hasAttribute('data-plain');
    if (reduce || !('IntersectionObserver' in window)) return;
    var from = plain ? to - 13 : 0; el.textContent = from;
    var o = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting) return; o.disconnect();
      var t0 = performance.now(), dur = 1600;
      (function tick(t) {
        var k = clamp((t - t0) / dur, 0, 1); k = 1 - Math.pow(1 - k, 4);
        el.textContent = Math.round(from + (to - from) * k);
        if (k < 1) requestAnimationFrame(tick);
      })(t0);
    }, { threshold: 0.6 });
    o.observe(el);
  });

  /* ---------- nav ---------- */
  var nav = $('#nav'), burger = $('.nav__burger'), menu = $('#menu');
  function setMenu(open) {
    burger.setAttribute('aria-expanded', open);
    burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    if (open) { menu.hidden = false; d.body.style.overflow = 'hidden'; }
    else { menu.hidden = true; d.body.style.overflow = ''; }
  }
  burger.addEventListener('click', function () { setMenu(burger.getAttribute('aria-expanded') !== 'true'); });
  $$('a', menu).forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });

  /* ---------- marquee clone ---------- */
  $$('.marquee__row').forEach(function (row) {
    $$('li', row).forEach(function (li) { var c = li.cloneNode(true); c.setAttribute('aria-hidden', 'true'); row.appendChild(c); });
  });

  /* ---------- tilt ---------- */
  if (matchMedia('(hover:hover)').matches && !reduce) {
    $$('[data-tilt]').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
        card.style.setProperty('--ry', (x * 5).toFixed(2) + 'deg');
        card.style.setProperty('--rx', (-y * 5).toFixed(2) + 'deg');
      });
      card.addEventListener('pointerleave', function () { card.style.setProperty('--ry', '0deg'); card.style.setProperty('--rx', '0deg'); });
    });
  }

  /* ---------- FAQ accordion ---------- */
  var qas = $$('.qa');
  qas.forEach(function (qa) {
    var sum = $('summary', qa), body = $('.qa__a', qa);
    sum.addEventListener('click', function (e) {
      e.preventDefault();
      var opening = !qa.open;
      qas.forEach(function (o) { if (o !== qa && o.open) toggle(o, false); });
      toggle(qa, opening);
    });
    function toggle(el, open) {
      var b = $('.qa__a', el);
      if (reduce || !b.animate) { el.open = open; return; }
      if (open) {
        el.open = true;
        b.animate([{ height: '0px', opacity: 0 }, { height: b.scrollHeight + 'px', opacity: 1 }], { duration: 520, easing: 'cubic-bezier(.2,.7,.1,1)' });
      } else {
        var an = b.animate([{ height: b.scrollHeight + 'px', opacity: 1 }, { height: '0px', opacity: 0 }], { duration: 380, easing: 'cubic-bezier(.2,.7,.1,1)' });
        an.onfinish = function () { el.open = false; };
      }
    }
    void body;
  });

  /* ---------- lead form -> WhatsApp ---------- */
  var form = $('#lead');
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    var f = new FormData(form), name = (f.get('name') || '').trim();
    var nameEl = form.elements.name;
    if (!name) { nameEl.classList.add('err'); nameEl.focus(); return; }
    nameEl.classList.remove('err');
    var lines = ['Hello Attractive Home, I\'d like to book a free design consultation.', '', 'Name: ' + name];
    if ((f.get('phone') || '').trim()) lines.push('Phone: ' + f.get('phone').trim());
    lines.push('Project: ' + f.get('type'), 'Scope: ' + f.get('scope'));
    if ((f.get('msg') || '').trim()) lines.push('Details: ' + f.get('msg').trim());
    window.open('https://wa.me/971588840028?text=' + encodeURIComponent(lines.join('\n')), '_blank', 'noopener');
  });

  /* ---------- materials data + selection ---------- */
  var MATS = [
    ['Honed Travertine', 'Warm, porous and calm underfoot. Our go-to for floors, coffee tables and feature walls.'],
    ['Walnut Veneer', 'Book-matched and sealed in our joinery. Wardrobes, doors and full-height wall panelling.'],
    ['Calacatta Marble', 'Bright, softly veined stone for kitchen islands, vanities and statement bathrooms.'],
    ['Brushed Brass', 'A quiet line of warmth. Handles, inlays, trims and lighting details.'],
    ['Ivory Bouclé', 'Textured, tactile upholstery for sofas, headboards and majlis seating.'],
    ['Verde Marble', 'Deep green stone for the one surface that should stop people mid-sentence.']
  ];
  var mInfo = $('.materials__info'), swatches = $$('.swatch');
  AH.mat = { index: 0, count: MATS.length, on: [] };
  AH.setMaterial = function (i, silent) {
    i = ((i % MATS.length) + MATS.length) % MATS.length;
    if (i === AH.mat.index && !silent) return;
    AH.mat.index = i;
    if (mInfo) {
      $('.materials__idx', mInfo).textContent = ('0' + (i + 1)).slice(-2) + ' / 0' + MATS.length;
      $('.materials__name', mInfo).textContent = MATS[i][0];
      $('.materials__desc', mInfo).textContent = MATS[i][1];
      mInfo.classList.remove('swap'); void mInfo.offsetWidth; mInfo.classList.add('swap');
    }
    swatches.forEach(function (s, k) { s.classList.toggle('is-active', k === i); });
    AH.mat.on.forEach(function (fn) { fn(i); });
  };
  swatches.forEach(function (s) { s.addEventListener('click', function () { AH.setMaterial(+s.dataset.i); }); });
  $$('[data-mat]').forEach(function (b) { b.addEventListener('click', function () { AH.setMaterial(AH.mat.index + (b.dataset.mat === 'next' ? 1 : -1)); }); });

  /* ---------- scroll-driven pieces ---------- */
  var contactEl = $('#lead'), hero = $('.hero'), fab = $('.fab'), dock = $('.dock');
  var proc = $('.process'), steps = $$('.step'), rail = $('.rail'), railLabels = $$('.rail__labels span');
  var spaces = $('.spaces'), track = $('.spaces__track'), viewport = $('.spaces__viewport'), sProg = $('.spaces__progress');
  var spaceImgs = $$('.space__img img');
  var pinMQ = matchMedia('(min-width:900px) and (hover:hover)');
  var vh = innerHeight, lastY = 0, pinned = false, maxX = 0, stepIdx = -1;

  function layout() {
    vh = innerHeight;
    pinned = !!spaces && pinMQ.matches && !reduce;
    if (spaces) spaces.classList.toggle('is-pinned', pinned);
    if (pinned) {
      maxX = Math.max(0, track.scrollWidth - innerWidth);
      spaces.style.height = (maxX + vh) + 'px';
    } else if (spaces) { spaces.style.height = ''; track.style.transform = ''; }
    update();
  }

  function update() {
    var y = window.scrollY; AH.scroll = y;

    // nav
    nav.classList.toggle('is-solid', y > 40);
    if (burger.getAttribute('aria-expanded') !== 'true') {
      if (y > lastY + 6 && y > vh * .6) nav.classList.add('is-hidden');
      else if (y < lastY - 6) nav.classList.remove('is-hidden');
    }
    lastY = y;

    // floating CTAs
    var show = y > (hero ? Math.min(vh * .7, hero.offsetHeight * .7) : 300);
    var ct = contactEl ? contactEl.getBoundingClientRect().top : 1e9;
    fab.classList.toggle('show', show); dock.classList.toggle('show', show && ct > vh * .55);

    // statement
    if (statement && !reduce) {
      var r = statement.getBoundingClientRect();
      var k = clamp((vh * .86 - r.top) / (r.height + vh * .38), 0, 1);
      var n = Math.round(k * sWords.length);
      for (var i = 0; i < sWords.length; i++) sWords[i].classList.toggle('on', i < n);
    }

    // process
    if (proc) {
      var pr = proc.getBoundingClientRect();
      var p = clamp(-pr.top / (pr.height - vh), 0, 1);
      var a = clamp((p - .12) / .24, 0, 1), b = clamp((p - .56) / .26, 0, 1);
      AH.process.p = p; AH.process.a = a; AH.process.b = b;
      proc.style.setProperty('--a', a.toFixed(3)); proc.style.setProperty('--b', b.toFixed(3));
      rail.style.setProperty('--p', p.toFixed(3));
      var idx = p < .14 ? 0 : p < .40 ? 1 : p < .58 ? 2 : p < .86 ? 3 : 4;
      if (idx !== stepIdx) {
        stepIdx = idx;
        steps.forEach(function (s, i) { s.classList.toggle('is-active', i === idx); });
        railLabels[0].classList.toggle('is-on', true);
        railLabels[1].classList.toggle('is-on', idx >= 1);
        railLabels[2].classList.toggle('is-on', idx >= 3);
      }
    }

    // spaces
    var sp = 0;
    if (!spaces) { /* inner page */ } else if (pinned) {
      var sr = spaces.getBoundingClientRect();
      sp = clamp(-sr.top / (sr.height - vh), 0, 1);
      track.style.transform = 'translate3d(' + (-sp * maxX).toFixed(1) + 'px,0,0)';
    } else {
      var mx = viewport.scrollWidth - viewport.clientWidth;
      sp = mx > 0 ? viewport.scrollLeft / mx : 0;
    }
    if (sProg) sProg.style.setProperty('--p', clamp(.08 + sp * .92, 0, 1).toFixed(3));
    if (!reduce) {
      var w = innerWidth;
      for (var j = 0; j < spaceImgs.length; j++) {
        var ir = spaceImgs[j].parentNode.getBoundingClientRect();
        if (ir.right < -100 || ir.left > w + 100) continue;
        var c = (ir.left + ir.width / 2) / w - .5; // -0.5..0.5
        spaceImgs[j].style.setProperty('--px', (-7.5 - c * 12).toFixed(2) + '%');
      }
    }
    for (var l = 0; l < AH.listeners.length; l++) AH.listeners[l](y);
  }

  var ticking = false;
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(function () { ticking = false; update(); }); } }
  addEventListener('scroll', onScroll, { passive: true });
  if (viewport) viewport.addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', layout);
  addEventListener('load', layout);
  if (pinMQ.addEventListener) pinMQ.addEventListener('change', layout);
  layout();
  AH.update = update;
})();
