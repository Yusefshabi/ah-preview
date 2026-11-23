/* Attractive Home — portfolio filter, project gallery motion and lightbox */
(function () {
  'use strict';
  var d = document;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); };
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
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

  /* ---------- project gallery ---------- */
  var gal = $('#gallery');
  if (!gal) return;
  var shots = $$('.shot', gal);
  var list = (gal.dataset.cover ? [gal.dataset.cover] : []).concat(shots.map(function (a) { return a.getAttribute('href'); }));
  var offset = gal.dataset.cover ? 1 : 0;

  /* lightbox */
  var lb, lbImg, lbCount, idx = 0;
  function buildLB() {
    lb = d.createElement('div'); lb.className = 'lb'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-label', 'Photo viewer');
    lb.innerHTML = '<img alt=""><button class="lb__x" aria-label="Close">✕</button><button class="lb__p" aria-label="Previous photo">←</button><button class="lb__n" aria-label="Next photo">→</button><div class="lb__c"></div>';
    d.body.appendChild(lb);
    lbImg = $('img', lb); lbCount = $('.lb__c', lb);
    lbImg.addEventListener('load', function () { lbImg.classList.add('on'); });
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
  function show() {
    lbImg.classList.remove('on'); lbImg.src = list[idx];
    if (lbImg.complete) lbImg.classList.add('on');
    lbCount.textContent = (idx + 1) + ' / ' + list.length;
    var nx = new Image(); nx.src = list[(idx + 1) % list.length];   // warm the next photo
  }
  function open(i) {
    if (!lb) buildLB(); idx = i; show(); lb.classList.add('open');
    d.body.style.overflow = 'hidden'; if (window.AH && AH.lenis) AH.lenis.stop();
  }
  function close() { lb.classList.remove('open'); d.body.style.overflow = ''; if (window.AH && AH.lenis) AH.lenis.start(); }
  function go(n) { idx = (idx + n + list.length) % list.length; show(); }

  shots.forEach(function (a, i) { a.addEventListener('click', function (e) { e.preventDefault(); open(i + offset); }); });
  $$('[data-open-gallery]').forEach(function (b) { b.addEventListener('click', function () { open(0); }); });

  /* gentle parallax inside each frame */
  if (!reduce && shots.length) {
    var imgs = shots.map(function (a) { return $('img', a); }), ticking = false;
    var update = function () {
      ticking = false;
      var vh = innerHeight;
      for (var i = 0; i < shots.length; i++) {
        var r = shots[i].getBoundingClientRect();
        if (r.bottom < -80 || r.top > vh + 80) continue;
        var c = (r.top + r.height / 2) / vh - .5;            // -0.5 .. 0.5 across the viewport
        imgs[i].style.setProperty('--py', (-c * r.height * .09).toFixed(1) + 'px');
      }
    };
    addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    addEventListener('resize', update);
    update();
  }
})();
