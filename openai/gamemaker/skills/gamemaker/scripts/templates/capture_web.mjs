#!/usr/bin/env node
// Scripted headless session for a web game — the gamemaker SESSION capture.
//
// Copy into the project as tools/capture.mjs, then adapt the three marked
// sections (URL, INPUT SCHEDULE, required metrics). Everything else can stay.
//
// Emits into --out:
//   frames/NNN.png   frames at a fixed interval
//   filmstrip.png    the frames tiled into one image (what the blind A/B reads)
//   metrics.json     harness-measured fps + whatever the game put in window.__metrics
//
// Exits non-zero when the session did not complete — that is what lets this
// command double as a free gate.
//
// Conventions the game must honour (references/harness.md):
//   - reads ?seed=<n> and routes ALL gameplay randomness through it
//   - maintains window.__metrics = { completed, events: [...], ... }
//   - (optional) ?replay=<name> plays a canned input script instead of live input
//
// Usage:
//   node tools/capture.mjs --url http://localhost:8080 --out .gamemaker/<slug>/rounds/07 \
//        [--seed 7] [--duration 30] [--interval 2000] [--serve "npx serve -l 8080 dist"]

import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

// ---------------------------------------------------------------- arguments
const arg = (name, dflt) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : dflt;
};
const URL_BASE = arg('url', 'http://localhost:8080');       // ADAPT
const OUT      = arg('out', 'capture-out');
const SEED     = arg('seed', '7');
const DURATION = Number(arg('duration', '30')) * 1000;      // session length, ms
const INTERVAL = Number(arg('interval', '2000'));           // frame every N ms
const SERVE    = arg('serve', '');                          // optional server cmd
const VIEWPORT = { width: 1280, height: 720 };              // fixed — never change between rounds

// ------------------------------------------------- ADAPT: the input schedule
// The same moves every round, or improvement is indistinguishable from luck.
// t is ms from session start. Types: key (down+up), keydown, keyup, click.
const SCHEDULE = [
  { t: 1000,  type: 'key',     key: 'Enter' },      // dismiss menu
  { t: 2000,  type: 'keydown', key: 'ArrowUp' },    // hold accelerate…
  { t: 6000,  type: 'key',     key: 'ArrowLeft' },
  { t: 9000,  type: 'key',     key: 'ArrowRight' },
  { t: 12000, type: 'key',     key: 'Space' },
  { t: 20000, type: 'keyup',   key: 'ArrowUp' },
];

// -------------------------------------- ADAPT: what metrics.json must contain
const REQUIRED = ['completed', 'events'];

// --------------------------------------------------------------------- main
const framesDir = path.join(OUT, 'frames');
fs.mkdirSync(framesDir, { recursive: true });

let server = null;
if (SERVE) {
  server = spawn(SERVE, { shell: true, stdio: 'ignore', detached: true });
  await new Promise(r => setTimeout(r, 1500));
}

const stopServer = () => {
  if (server) { try { process.kill(-server.pid); } catch {} server = null; }
};
const fail = async (why) => {
  console.error(`CAPTURE FAILED: ${why}`);
  stopServer();
  process.exit(1);
};

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: VIEWPORT, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error(`page error: ${e.message}`));

// Harness-side fps meter: counts rAF per second so fps needs nothing from the game.
await page.addInitScript(() => {
  window.__fps = [];
  let frames = 0;
  const tick = () => { frames++; requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  setInterval(() => { window.__fps.push(frames); frames = 0; }, 1000);
});

const url = `${URL_BASE}${URL_BASE.includes('?') ? '&' : '?'}capture=1&seed=${SEED}`;
try {
  await page.goto(url, { waitUntil: 'load', timeout: 15000 });
} catch (e) {
  await fail(`could not load ${url} — ${e.message}`);
}

// Run the schedule and the frame grabs on one clock.
const started = Date.now();
let frameN = 0, due = [...SCHEDULE];
while (Date.now() - started < DURATION) {
  const t = Date.now() - started;
  while (due.length && due[0].t <= t) {
    const ev = due.shift();
    if (ev.type === 'key')          await page.keyboard.press(ev.key);
    else if (ev.type === 'keydown') await page.keyboard.down(ev.key);
    else if (ev.type === 'keyup')   await page.keyboard.up(ev.key);
    else if (ev.type === 'click')   await page.mouse.click(ev.x, ev.y);
  }
  if (t >= frameN * INTERVAL) {
    await page.screenshot({ path: path.join(framesDir, `${String(frameN).padStart(3, '0')}.png`) });
    frameN++;
  }
  await new Promise(r => setTimeout(r, 50));
}

// ------------------------------------------------------------------ metrics
const gameMetrics = await page.evaluate(() => window.__metrics ?? null);
const fpsSamples = (await page.evaluate(() => window.__fps)).slice(1); // drop warm-up second
const metrics = {
  seed: Number(SEED),
  duration: DURATION / 1000,
  fps_mean: fpsSamples.length ? +(fpsSamples.reduce((a, b) => a + b) / fpsSamples.length).toFixed(1) : 0,
  fps_min: fpsSamples.length ? Math.min(...fpsSamples) : 0,
  ...gameMetrics,
};

// ---------------------------------------------------- filmstrip via canvas
const files = fs.readdirSync(framesDir).filter(f => f.endsWith('.png')).sort();
const cols = Math.min(files.length, 8);
const tile = 320; // px per frame width in the strip — small on purpose (token cost)
await page.setContent('<canvas id=c></canvas>');
const strip = await page.evaluate(async ({ srcs, cols, tile }) => {
  const imgs = await Promise.all(srcs.map(s => new Promise(res => {
    const i = new Image(); i.onload = () => res(i); i.src = s;
  })));
  const th = Math.round(tile * imgs[0].height / imgs[0].width);
  const rows = Math.ceil(imgs.length / cols);
  const c = document.getElementById('c');
  c.width = cols * tile; c.height = rows * th;
  const ctx = c.getContext('2d');
  imgs.forEach((im, i) => ctx.drawImage(im, (i % cols) * tile, Math.floor(i / cols) * th, tile, th));
  return c.toDataURL('image/png');
}, {
  srcs: files.map(f => `data:image/png;base64,${fs.readFileSync(path.join(framesDir, f)).toString('base64')}`),
  cols, tile,
});
fs.writeFileSync(path.join(OUT, 'filmstrip.png'), Buffer.from(strip.split(',')[1], 'base64'));
fs.writeFileSync(path.join(OUT, 'metrics.json'), JSON.stringify(metrics, null, 2) + '\n');

await browser.close();
stopServer();

// ------------------------------------------------------------------- verdict
if (!gameMetrics) await fail('window.__metrics was never set — the game is not instrumented');
for (const k of REQUIRED) if (!(k in metrics)) await fail(`metrics.json is missing "${k}"`);
if (metrics.completed !== true) await fail('session did not complete (metrics.completed !== true)');

console.log(`ok: ${files.length} frames, filmstrip.png, metrics.json → ${OUT}`);
console.log(JSON.stringify(metrics));
