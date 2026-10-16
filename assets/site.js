/* Welcome to Shenzhen · APEC 2026 — site behaviour
   Vanilla JS, no dependencies. Safe on file:// as well as http(s)://        */
(function () {
  'use strict';

  var KEY = 'sz-apec-lang';

  /* ---------- language ---------- */
  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function remember(lang) {
    try { localStorage.setItem(KEY, lang); } catch (e) { /* ignore */ }
  }
  function applyLang(lang) {
    var root = document.documentElement;
    root.setAttribute('data-lang', lang);
    root.setAttribute('lang', lang === 'zh' ? 'zh-Hans' : 'en');
    var nodes = document.querySelectorAll('[data-setlang]');
    for (var i = 0; i < nodes.length; i++) {
      var on = nodes[i].getAttribute('data-setlang') === lang;
      nodes[i].setAttribute('aria-pressed', on ? 'true' : 'false');
      nodes[i].classList.toggle('is-on', on);
    }
  }
  /* English-primary: default EN; only a saved preference switches away. */
  applyLang(stored() || 'en');

  /* ---------- nav ---------- */
  document.addEventListener('click', function (ev) {
    var t = ev.target;

    var langBtn = t.closest ? t.closest('[data-setlang]') : null;
    if (langBtn) {
      ev.preventDefault();
      var lang = langBtn.getAttribute('data-setlang');
      applyLang(lang);
      remember(lang);
      return;
    }

    var toggle = t.closest ? t.closest('.nav-toggle') : null;
    if (toggle) {
      ev.preventDefault();
      var nav = document.getElementById('site-nav');
      if (nav) {
        var open = nav.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      }
      return;
    }

    var link = t.closest ? t.closest('#site-nav a') : null;
    if (link) {
      var nav2 = document.getElementById('site-nav');
      if (nav2) { nav2.classList.remove('is-open'); }
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    /* ---------- scroll reveal (+ timeline / steps progressive highlight) ---------- */
    var reveals = document.querySelectorAll('.reveal, .timeline > li, .steps > li');
    if (!('IntersectionObserver' in window)) {
      for (var i = 0; i < reveals.length; i++) { reveals[i].classList.add('is-in'); }
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add('is-in');
            io.unobserve(en.target);
          }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
      for (var j = 0; j < reveals.length; j++) { io.observe(reveals[j]); }
    }

    /* ---------- back to top ---------- */
    var btn = document.querySelector('.back-to-top');
    if (btn) {
      var onScroll = function () {
        btn.classList.toggle('is-visible', window.scrollY > 700);
      };
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
      btn.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    /* ---------- countdown ---------- */
    var cds = document.querySelectorAll('[data-countdown]');
    for (var c = 0; c < cds.length; c++) {
      (function (el) {
        var target = new Date(el.getAttribute('data-countdown'));
        if (isNaN(target.getTime())) { return; }
        var days = Math.ceil((target.getTime() - Date.now()) / 86400000);
        var zh = el.querySelector('.lang-zh');
        var en = el.querySelector('.lang-en');
        if (!zh || !en) { return; }
        if (days > 1) {
          zh.textContent = String(days) + ' 天后';
          en.textContent = String(days) + ' days';
        } else if (days === 1) {
          zh.textContent = '明天'; en.textContent = 'Tomorrow';
        } else if (days > -3) {
          zh.textContent = '正在进行'; en.textContent = 'Happening now';
        } else {
          zh.textContent = '已举办'; en.textContent = 'Concluded';
        }
      })(cds[c]);
    }

    /* ---------- table of contents highlighting ---------- */
    var tocLinks = document.querySelectorAll('.toc a[href^="#"]');
    if (tocLinks.length && 'IntersectionObserver' in window) {
      var map = {};
      var targets = [];
      for (var k = 0; k < tocLinks.length; k++) {
        var id = tocLinks[k].getAttribute('href').slice(1);
        var el = id && document.getElementById(id);
        if (el) { map[id] = tocLinks[k]; targets.push(el); }
      }
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting && map[en.target.id]) {
            for (var m = 0; m < tocLinks.length; m++) { tocLinks[m].classList.remove('is-active'); }
            map[en.target.id].classList.add('is-active');
          }
        });
      }, { rootMargin: '-88px 0px -70% 0px' });
      targets.forEach(function (el) { spy.observe(el); });
    }
  });
})();
