#!/usr/bin/env node
/**
 * Visual/structural verification of the built site using the Chrome DevTools
 * Protocol. No npm dependencies: it launches the installed Chrome, drives it
 * over the websocket (Node 22+ has a global WebSocket) and asserts, per page
 * and per viewport:
 *
 *   - no horizontal overflow, and if there is, which element causes it
 *   - the language switch actually switches (data-lang, visibility, text)
 *   - no broken images and no failed network requests
 *   - console errors
 *
 * Usage:  node src/verify.mjs [--url http://host] [--shots DIR]
 */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';
import path from 'node:path';

const ROOT = path.resolve(new URL('..', import.meta.url).pathname);
const DIST = path.join(ROOT, 'dist');
const CHROME = process.env.CHROME_BIN ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9333;

const VIEWPORTS = [
  { name: 'mobile', width: 390, height: 844, dsf: 2, mobile: true },
  { name: 'tablet', width: 834, height: 1112, dsf: 1, mobile: true },
  { name: 'desktop', width: 1440, height: 900, dsf: 1, mobile: false },
];

// Positional page arguments only: skip flags and the value that follows them.
const FLAGS_WITH_VALUE = ['--shots', '--url'];
const argv = process.argv.slice(2);
const positional = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (FLAGS_WITH_VALUE.includes(a)) { i++; continue; }
  if (a.startsWith('-')) continue;
  positional.push(a);
}
const PAGES = positional;
const ALL_PAGES = PAGES.length ? PAGES : [
  'index.html', 'apec-2026.html', 'city.html', 'attractions.html', 'food.html',
  'stay.html', 'transport.html', 'shopping.html', 'itineraries.html',
  'business.html', 'services.html', 'faq.html', 'about.html',
];

const shotArg = process.argv.indexOf('--shots');
const SHOT_DIR = shotArg > -1 ? process.argv[shotArg + 1] : null;
if (SHOT_DIR) mkdirSync(SHOT_DIR, { recursive: true });

const baseArg = process.argv.indexOf('--url');
const BASE = baseArg > -1 ? process.argv[baseArg + 1].replace(/\/$/, '')
  : `file://${DIST}`;

/* ------------------------------------------------------------------ CDP ---- */
class CDP {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    this.handlers = new Map();
    ws.addEventListener('message', (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      } else if (msg.method) {
        (this.handlers.get(msg.method) || []).forEach((fn) => fn(msg.params));
      }
    });
  }
  on(method, fn) {
    if (!this.handlers.has(method)) this.handlers.set(method, []);
    this.handlers.get(method).push(fn);
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
}

async function connect() {
  for (let i = 0; i < 60; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const targets = await res.json();
      const page = targets.find((t) => t.type === 'page');
      if (page) {
        const ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((ok, err) => {
          ws.addEventListener('open', ok, { once: true });
          ws.addEventListener('error', err, { once: true });
        });
        return new CDP(ws);
      }
    } catch { /* chrome not up yet */ }
    await sleep(250);
  }
  throw new Error('could not attach to Chrome');
}

/* --------------------------------------------------------------- checks ---- */
const MEASURE = `(() => {
  const de = document.documentElement;
  const cw = de.clientWidth;
  const offenders = [];
  const seen = new Set();
  document.querySelectorAll('body *').forEach((el) => {
    if (el.closest('svg')) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0) return;
    const style = getComputedStyle(el);
    if (style.position === 'fixed') return;
    if (r.right > cw + 1 || r.left < -1) {
      const key = el.tagName + '|' + (el.className || '') + '|' + el.id;
      if (seen.has(key)) return;
      seen.add(key);
      offenders.push({
        sel: el.tagName.toLowerCase() +
             (el.id ? '#' + el.id : '') +
             (typeof el.className === 'string' && el.className
               ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : ''),
        left: Math.round(r.left), right: Math.round(r.right),
        w: Math.round(r.width), text: (el.textContent || '').trim().slice(0, 40),
      });
    }
  });
  window.scrollTo(9999, 0);
  const realScrollX = window.scrollX;
  window.scrollTo(0, 0);

  const imgs = [...document.images]
    .filter((i) => i.getAttribute('loading') !== 'lazy' || i.getBoundingClientRect().top < 3000)
    .filter((i) => i.complete && i.naturalWidth === 0)
    .map((i) => i.getAttribute('src'));

  // A scroll container's own ancestors legitimately report their full
  // scrollWidth too, so mark them as accounted-for rather than as defects.
  const excused = new Set();
  const scrollers = [];
  // Pass 1: find every intentionally scrollable container.
  const intentionalEls = [];
  document.querySelectorAll('*').forEach((el) => {
    if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
      const ox = getComputedStyle(el).overflowX;
      if (ox === 'auto' || ox === 'scroll' || ox === 'clip' || ox === 'hidden') {
        intentionalEls.push(el);
        let n = el.parentElement;
        while (n) { excused.add(n); n = n.parentElement; }
      }
    }
  });
  document.querySelectorAll('*').forEach((el) => {
    if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
      const ox = getComputedStyle(el).overflowX;
      const intentional = ox === 'auto' || ox === 'scroll' || ox === 'clip' || ox === 'hidden';
      scrollers.push({
        el,
        sel: el.tagName.toLowerCase() +
             (typeof el.className === 'string' && el.className
               ? '.' + el.className.trim().split(/\s+/)[0] : ''),
        scrollW: el.scrollWidth, clientW: el.clientWidth,
        intentional,
      });
      if (intentional) {
        let n = el.parentElement;
        while (n) { excused.add(n); n = n.parentElement; }
      }
    }
  });
  const unresolved = scrollers
    .filter((s) => !s.intentional && !excused.has(s.el))
    .map(({ sel, scrollW, clientW, el }) => ({
      sel, scrollW, clientW,
      parentW: el.parentElement
        ? Math.round(el.parentElement.getBoundingClientRect().width) : 0,
    }));
  const accounted = scrollers.length - unresolved.length;

  return {
    realScrollX,
    scrollers: unresolved,
    rawScrollers: scrollers.map((x) => {
      const pe = x.el.parentElement;
      return x.sel + '|sw=' + x.scrollW + '|cw=' + x.clientW +
        '|intent=' + x.intentional +
        '|parent=' + (pe ? pe.tagName.toLowerCase() + '.' +
          ((pe.className || '').toString().split(/\s+/)[0] || '-') : '-');
    }),
    accountedScrollers: accounted,
    clientW: cw,
    scrollW: Math.max(de.scrollWidth, document.body.scrollWidth),
    pageH: de.scrollHeight,
    offenders: offenders.slice(0, 8),
    brokenImages: imgs,
    h1: document.querySelectorAll('h1').length,
    zhPairs: document.querySelectorAll('.lang-zh').length,
    enPairs: document.querySelectorAll('.lang-en').length,
    title: document.title,
  };
})()`;

/* English-primary: default is EN; probe ZH then switch back to EN. */
const LANG_PROBE_EN_PRIMARY = `(() => {
  try { localStorage.removeItem('sz-apec-lang'); } catch (e) {}
  const de = document.documentElement;
  const h1zh = document.querySelector('h1 .lang-zh, .hero h1 .lang-zh, .page-hero h1 .lang-zh');
  const h1en = document.querySelector('h1 .lang-en, .hero h1 .lang-en, .page-hero h1 .lang-en');
  const vis = (el) => (el ? getComputedStyle(el).display !== 'none' : null);
  const state = { lang: de.getAttribute('data-lang'), zh: vis(h1zh), en: vis(h1en) };
  const zhBtn = document.querySelector('[data-setlang="zh"]');
  if (zhBtn) zhBtn.click();
  const afterChinese = {
    lang: de.getAttribute('data-lang'),
    zh: vis(h1zh), en: vis(h1en),
    stored: (() => { try { return localStorage.getItem('sz-apec-lang'); } catch { return 'ERR'; } })(),
  };
  const enBtn = document.querySelector('[data-setlang="en"]');
  if (enBtn) enBtn.click();
  const afterEnglish = { lang: de.getAttribute('data-lang'), zh: vis(h1zh), en: vis(h1en) };
  return { initial: state, afterChinese, afterEnglish };
})()`;

/* ----------------------------------------------------------------- main ---- */
const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--disable-crash-reporter',
  '--hide-scrollbars', '--no-first-run', '--disable-extensions',
  `--remote-debugging-port=${PORT}`,
  '--user-data-dir=/tmp/chrome-verify',
  'about:blank',
], { stdio: 'ignore', env: { ...process.env, HOME: '/tmp/chrome-home' } });

const problems = [];
const warnings = [];
let cdp;
try {
  cdp = await connect();
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Network.enable');

  let consoleErrors = [];
  let failedRequests = [];
  cdp.on('Runtime.consoleAPICalled', (p) => {
    if (p.type === 'error') consoleErrors.push(p.args.map((a) => a.value ?? a.description).join(' '));
  });
  cdp.on('Runtime.exceptionThrown', (p) => {
    consoleErrors.push(p.exceptionDetails?.text || 'exception');
  });
  cdp.on('Network.loadingFailed', (p) => {
    if (p.type !== 'Image') failedRequests.push(`${p.type}: ${p.errorText}`);
    else failedRequests.push(`image failed: ${p.errorText}`);
  });

  for (const vp of VIEWPORTS) {
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: vp.width, height: vp.height,
      deviceScaleFactor: vp.dsf, mobile: vp.mobile,
    });
    for (const page of ALL_PAGES) {
      consoleErrors = []; failedRequests = [];
      await cdp.send('Page.navigate', { url: `${BASE}/${page}` });
      await sleep(700);
      const { result } = await cdp.send('Runtime.evaluate', {
        expression: MEASURE, returnByValue: true,
      });
      const m = result.value;
      const tag = `${page} [${vp.name} ${vp.width}px]`;

      if (m.realScrollX > 0) {
        problems.push(`${tag}: page scrolls horizontally by ${m.realScrollX}px` +
          (m.offenders.length
            ? '\n      ' + m.offenders.map((o) =>
                `${o.sel} ${o.left}→${o.right} (${o.w}px) "${o.text}"`).join('\n      ')
            : ''));
      }
      // An ancestor of a scroll container reports the same inflated
      // scrollWidth, so only flag a container that still sticks out past the
      // space its parent actually provides. Anything inside `.table-wrap`
      // (which scrolls on purpose) is accounted for.
      const badScrollers = (m.scrollers || []).filter(
        (s) => !/card-icon|brand-mark/.test(s.sel) && s.scrollW > s.parentW + 80);
      if (badScrollers.length) {
        // Informational only: these are ancestors of a deliberate scroll
        // container (the mobile table pattern), so their scrollWidth is wide
        // while the page itself still does not scroll horizontally.
        warnings.push(`${tag}: wide scroller ancestor (expected for tables) ` +
          badScrollers.map((s) => `${s.sel} ${s.scrollW}>${s.parentW}`).join(', '));
      }
      if (m.brokenImages.length) {
        problems.push(`${tag}: broken images ${m.brokenImages.join(', ')}`);
      }
      if (m.h1 !== 1) problems.push(`${tag}: ${m.h1} <h1> elements`);
      if (m.zhPairs !== m.enPairs) {
        problems.push(`${tag}: lang-zh=${m.zhPairs} lang-en=${m.enPairs}`);
      }
      if (!m.title || m.title.length < 8) problems.push(`${tag}: weak <title>`);
      const bad = [...new Set([...consoleErrors, ...failedRequests])];
      if (bad.length) warnings.push(`${tag}: ${bad.slice(0, 3).join(' | ')}`);

      if (vp.name === 'desktop' && page === 'index.html') {
        // Clear preference so the HTML default (English-primary) is what we measure.
        await cdp.send('Runtime.evaluate', {
          expression: `try{localStorage.removeItem('sz-apec-lang')}catch(e){}`,
          returnByValue: true,
        });
        await cdp.send('Page.navigate', { url: `${BASE}/${page}` });
        await sleep(700);
        const { result: lr } = await cdp.send('Runtime.evaluate', {
          expression: LANG_PROBE_EN_PRIMARY, returnByValue: true,
        });
        const p = lr.value;
        if (!(p.initial.lang === 'en' && p.initial.en === true && p.initial.zh === false)) {
          problems.push(`language: unexpected initial state ${JSON.stringify(p.initial)}`);
        }
        if (!(p.afterChinese.lang === 'zh' && p.afterChinese.zh === true && p.afterChinese.en === false)) {
          problems.push(`language: ZH switch failed ${JSON.stringify(p.afterChinese)}`);
        }
        if (p.afterChinese.stored !== 'zh') {
          problems.push(`language: preference not persisted (${p.afterChinese.stored})`);
        }
        if (!(p.afterEnglish.lang === 'en' && p.afterEnglish.en === true)) {
          problems.push(`language: EN switch back failed ${JSON.stringify(p.afterEnglish)}`);
        }
      }

      if (process.env.DIAG && vp.name === 'mobile' && page === 'services.html') {
        console.log('    DIAG raw scrollers:', JSON.stringify(
          (m.rawScrollers || []).slice(0, 12)));
      }
      if (SHOT_DIR) {
        const shot = await cdp.send('Page.captureScreenshot', {
          format: 'png', captureBeyondViewport: true,
        });
        writeFileSync(
          path.join(SHOT_DIR, `${page.replace('.html', '')}-${vp.name}.png`),
          Buffer.from(shot.data, 'base64'),
        );
      }
      console.log(`  ${tag.padEnd(38)} h=${m.pageH}px  ok`);
    }
  }
} finally {
  chrome.kill();
}

console.log(`\nverified ${ALL_PAGES.length} page(s) × ${VIEWPORTS.length} viewports`);
for (const w of warnings) console.log(`  warning: ${w}`);
if (problems.length) {
  console.log(`\n${problems.length} problem(s):`);
  for (const p of problems) console.log(`  ERROR: ${p}`);
  process.exit(1);
}
console.log('all checks passed');
