/* Attractive Home — portfolio filter, project gallery and lightbox */
(function () {
  'use strict';
  var d = document;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); };
  var relayout = function () { if (window.AH && AH.lenis) setTimeout(function () { AH.lenis.resize(); }, 400); };

  /* ---------- portfolio filter (the links still work without JS) ---------- */
  var grid = $('#pgrid'), filters = $$('.filters a');
  // Category pages only contain their own projects, so there the links navigate normally.
  if (grid && filters.length && /\/portfolio\/?$/.test(location.pathname)) {
    var all = $$('.pcard', grid);
    filters.forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        var f = a.dataset.filter;
        filters.forEach(function (x) { x.classList.toggle('is-active', x === a); });
        all.forEach(function (c) { c.hidden = !!f && c.dataset.cat !== f; });
        relayout();
      });
    });
  }

  /* ---------- lightbox ---------- */
  var lb, lbImg, lbCount, list = [], idx = 0;
  function buildLB() {
    lb = d.createElement('div'); lb.className = 'lb'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-label', 'Photo viewer');
    lb.innerHTML = '<img alt=""><button class="lb__x" aria-label="Close">✕</button><button class="lb__p" aria-label="Previous photo">←</button><button class="lb__n" aria-label="Next photo">→</button><div class="lb__c"></div>';
    d.body.appendChild(lb);
    lbImg = $('img', lb); lbCount = $('.lb__c', lb);
    $('.lb__x', lb).onclick = close;
    $('.lb__p', lb).onclick = function () { go(-1); };
    $('.lb__n', lb).onclick = function () { go(1); };
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    d.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') close(); else if (e.key === 'ArrowLeft') go(-1); else if (e.key === 'ArrowRight') go(1);
    });
    var x0 = null;
    lb.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 50) go(dx < 0 ? 1 : -1); x0 = null;
    });
  }
  function show() { lbImg.src = list[idx]; lbCount.textContent = (idx + 1) + ' / ' + list.length; }
  function open(i) {
    if (!lb) buildLB(); idx = i; show(); lb.classList.add('open');
    d.body.style.overflow = 'hidden'; if (window.AH && AH.lenis) AH.lenis.stop();
  }
  function close() { lb.classList.remove('open'); d.body.style.overflow = ''; if (window.AH && AH.lenis) AH.lenis.start(); }
  function go(n) { idx = (idx + n + list.length) % list.length; show(); }

  /* ---------- project gallery, read live from the studio's media library ---------- */
  var gal = $('#gallery');
  if (!gal) return;
  var base = gal.dataset.base, title = gal.dataset.title, PAGE = 9; // full-size originals: keep batches small until gallery thumbnails exist

  function render(groups) {
    gal.innerHTML = ''; list = [];
    groups.forEach(function (g) {
      if (!g.items.length) return;
      if (g.name) {
        var h = d.createElement('div'); h.className = 'gallery__sec';
        var h2 = d.createElement('h2'); h2.textContent = g.name;
        var n = d.createElement('span'); n.textContent = g.items.length + ' photos';
        h.appendChild(h2); h.appendChild(n); gal.appendChild(h);
      }
      var wrap = d.createElement('div'); wrap.className = 'gallery__grid'; gal.appendChild(wrap);
      var shown = 0, more = null;
      function add(count) {
        g.items.slice(shown, shown + count).forEach(function (src) {
          list.push(src);
          var a = d.createElement('a'); a.href = src;
          var im = new Image(); im.loading = 'lazy'; im.decoding = 'async';
          im.alt = title + (g.name ? ', ' + g.name.toLowerCase() : '') + ' by Attractive Home'; im.src = src;
          a.appendChild(im);
          a.addEventListener('click', function (e) { e.preventDefault(); open(list.indexOf(src)); });
          wrap.appendChild(a);
        });
        shown += count;
        if (more && shown >= g.items.length) more.remove();
        relayout();
      }
      add(PAGE);
      if (shown < g.items.length) {
        more = d.createElement('div'); more.className = 'gallery__more';
        var b = d.createElement('button'); b.type = 'button'; b.className = 'btn'; b.textContent = 'Show more photos';
        b.addEventListener('click', function () { add(PAGE); });
        more.appendChild(b); gal.appendChild(more);
      }
    });
  }

  fetch(gal.dataset.src).then(function (r) { return r.json(); }).then(function (m) {
    var media = (m.media || []).filter(function (x) { return x.type === 'image'; }).map(function (x) { return base + x.src; });
    var key = function (src) { return src.split('/').pop().replace(/\.\w+$/, ''); };
    var groups = [], used = {};
    (m.sections || []).forEach(function (s) {
      var keys = s.keys || [];
      var items = media.filter(function (src) { return keys.indexOf(key(src)) > -1; });
      items.forEach(function (src) { used[src] = 1; });
      groups.push({ name: (s.names && s.names.en) || '', items: items });
    });
    var rest = media.filter(function (src) { return !used[src]; });
    if (groups.length && rest.length) groups.push({ name: 'More from this project', items: rest });
    else if (!groups.length) groups.push({ name: '', items: media });
    if (media.length) render(groups);
  }).catch(function () { /* keep the pre-rendered cover photo */ });
})();
