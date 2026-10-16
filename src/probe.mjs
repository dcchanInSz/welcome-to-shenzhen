#!/usr/bin/env node
/** Ad-hoc probe: node src/probe.mjs <page> [width] -- prints layout metrics. */
import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import path from 'node:path';

const ROOT = path.resolve(new URL('..', import.meta.url).pathname);
const DIST = path.join(ROOT, 'dist');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9345;
const page = process.argv[2] || 'services.html';
const width = Number(process.argv[3] || 390);

const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-sandbox',
  '--disable-crash-reporter', '--hide-scrollbars', '--no-first-run',
  `--remote-debugging-port=${PORT}`, '--user-data-dir=/tmp/chrome-probe',
  'about:blank'], { stdio: 'ignore', env: { ...process.env, HOME: '/tmp/chrome-home' } });

async function attach() {
  for (let i = 0; i < 60; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const t = list.find((x) => x.type === 'page');
      if (t) {
        const ws = new WebSocket(t.webSocketDebuggerUrl);
        await new Promise((ok) => ws.addEventListener('open', ok, { once: true }));
        return ws;
      }
    } catch {}
    await sleep(250);
  }
  throw new Error('no chrome');
}

const ws = await attach();
let id = 0;
const pending = new Map();
ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); }
});
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res);
  ws.send(JSON.stringify({ id: i, method, params }));
});

await send('Page.enable');
await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride',
  { width, height: 844, deviceScaleFactor: 2, mobile: true });
await send('Page.navigate', { url: `file://${DIST}/${page}` });
await sleep(1200);

const expr = `(() => {
  const de = document.documentElement;
  const out = { scrollW: de.scrollWidth, clientW: de.clientWidth,
                bodyScrollW: document.body.scrollWidth, rows: [] };
  const check = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return;
    const r = el.getBoundingClientRect();
    const p = el.parentElement ? el.parentElement.getBoundingClientRect() : null;
    out.rows.push({
      sel, left: Math.round(r.left), right: Math.round(r.right),
      w: Math.round(r.width), scrollW: el.scrollWidth,
      parent: el.parentElement ? el.parentElement.className : null,
      parentW: p ? Math.round(p.width) : null,
      parentRight: p ? Math.round(p.right) : null,
      overflowX: getComputedStyle(el).overflowX,
    });
  };
  ['table', 'table thead', 'table tr', 'table th', '.table-wrap',
   'main', 'main > section', 'main .wrap', '.page-hero', '.hero',
   'footer', '.site-footer', '.site-footer .wrap'].forEach(check);
  // widest element that is a direct-ish descendant of a .wrap
  let widest = null;
  document.querySelectorAll('*').forEach((el) => {
    if (el.closest('svg')) return;
    const r = el.getBoundingClientRect();
    if (getComputedStyle(el).position === 'fixed') return;
    if (!widest || r.right > widest.r.right) {
      widest = { r, el };
    }
  });
  if (widest) {
    out.widest = {
      sel: widest.el.tagName + '.' + (widest.el.className || '').toString().slice(0, 40),
      right: Math.round(widest.r.right), w: Math.round(widest.r.width),
      text: (widest.el.textContent || '').trim().slice(0, 50),
    };
  }
  return out;
})()`;

const probe3 = `(() => {
  window.scrollTo(9999, 0);
  const realScrollX = window.scrollX;
  const de0 = document.documentElement;
  const over = [];
  const cw0 = de0.clientWidth;
  document.querySelectorAll('*').forEach((el) => {
    if (el.closest('svg')) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || getComputedStyle(el).position === 'fixed') return;
    if (r.right > cw0 + 1) {
      over.push(el.tagName.toLowerCase() + '.' + (el.className || '').toString().slice(0,30) +
        '[' + Math.round(r.left) + '→' + Math.round(r.right) + '] "' +
        (el.textContent || '').trim().slice(0, 30) + '"');
    }
  });
  return { realScrollX, clientW: cw0, scrollW: de0.scrollWidth,
           over: over.slice(0, 12) };
})()`;
const resOver = await send('Runtime.evaluate', { expression: probe3, returnByValue: true });
console.log('OVERFLOW CHECK', JSON.stringify(resOver.result.value, null, 1));

const probe4 = `(() => {
  const de = document.documentElement;
  const cw = de.clientWidth;
  // find the deepest elements that stick out to the right of the viewport
  const out = [];
  document.querySelectorAll('*').forEach((el) => {
    if (el.closest('svg')) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || getComputedStyle(el).position === 'fixed') return;
    if (r.right > cw + 1) {
      const kids = [...el.children].filter((k) => {
        const kr = k.getBoundingClientRect();
        return kr.width > 0 && kr.right > cw + 1;
      });
      if (kids.length === 0) {
        const chain = [];
        let n = el;
        while (n && n !== document.body && chain.length < 6) {
          const nr = n.getBoundingClientRect();
          chain.push(n.tagName.toLowerCase() +
            (typeof n.className === 'string' && n.className ? '.' + n.className.trim().split(/\\s+/)[0] : '') +
            '[' + Math.round(nr.left) + '→' + Math.round(nr.right) + ']');
          n = n.parentElement;
        }
        out.push({ text: (el.textContent || '').trim().slice(0, 60), chain });
      }
    }
  });
  return { cw, count: out.length, sample: out.slice(0, 5) };
})()`;
const res3 = await send('Runtime.evaluate', { expression: probe4, returnByValue: true });
console.log(JSON.stringify(res3.result.value, null, 1));
chrome.kill();
