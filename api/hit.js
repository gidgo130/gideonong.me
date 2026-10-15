// Analytics collector — POST /api/hit, sent by js/analytics.js with
// navigator.sendBeacon. CLAUDE.md → Analytics; plan.md → Phase 3 →
// "Analytics, self-built" (A2).
//
// Node built-ins + fetch only: no package.json, no npm, no build step. Vercel
// compiles this file's `export` syntax to CommonJS on deploy.
//
// Every response is an empty 204, whether the event was stored or rejected,
// so a caller learns nothing. Rejected (nothing stored):
//   - any method other than POST
//   - an Origin that isn't the site (see allowedOrigin)
//   - a body over MAX_BODY bytes
//   - a bot User-Agent, or none
//   - bad JSON, an unknown type, a click without an event name
//   - more than RATE_LIMIT events in one minute from one visitor hash
//
// Privacy: the IP and the raw User-Agent are used only in memory, to compute
// the daily visitor hash and the coarse browser / OS / device. Neither is ever
// stored or logged.
//
// Storage (Upstash Redis, REST API): RPUSH <prefix>hits:<UTC date> with one
// JSON record per event. Production keys have no prefix and live ~13 months;
// preview deploys use "preview:", `vercel dev` uses "dev:", and both expire
// after 7 days, so test data never mixes with real data.
//
// Env vars: UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN (falling back to
// the Vercel Marketplace names KV_REST_API_URL / KV_REST_API_TOKEN) and
// ANALYTICS_SALT_SECRET. If any is missing the function stores nothing.
import crypto from "node:crypto";

const MAX_BODY = 2048;                 // bytes
const RATE_LIMIT = 60;                 // events per visitor hash per minute
const TTL_PROD = 397 * 24 * 3600;      // ~13 months, in seconds
const TTL_TEST = 7 * 24 * 3600;        // preview / dev keys
const SITE_ORIGINS = ["https://gideonong.me", "https://www.gideonong.me"];

// Link-preview fetchers are matched by their bot names only: the LinkedIn,
// Slack, etc. in-app browsers are real visitors (LinkedIn's says "LinkedInApp").
const BOT_UA = /bot\b|bot\/|crawl|spider|slurp|scrap|archiver|preview|headless|phantom|selenium|playwright|puppeteer|lighthouse|pagespeed|gtmetrix|uptime|pingdom|curl|wget|python|httpclient|http-client|axios|node-fetch|undici|go-http|java\/|okhttp|libwww|facebookexternalhit|facebookcatalog|embedly|whatsapp\/|vkshare|quora link|outbrain|bitlybot/i;

const VW_BUCKETS = ["<480", "480-767", "768-1023", "1024-1439", "1440+"];

const env = process.env;
const STAGE = env.VERCEL_ENV === "production" ? "production" : env.VERCEL_ENV === "preview" ? "preview" : "development";
const PREFIX = STAGE === "production" ? "" : STAGE === "preview" ? "preview:" : "dev:";

const NO_CONTENT = () => new Response(null, { status: 204 });

export default {
  async fetch(request) {
    try {
      await handle(request);
    } catch (e) {
      // Our own messages only; never the request's IP, UA or body.
      console.error("hit: " + (e && e.message ? e.message : "error"));
    }
    return NO_CONTENT();
  },
};

async function handle(request) {
  if (request.method !== "POST") return;
  if (!allowedOrigin(request.headers.get("origin"))) return;

  const declared = Number(request.headers.get("content-length"));
  if (declared > MAX_BODY) return;
  const text = await readCapped(request, MAX_BODY);
  if (text === null) return;

  const ua = request.headers.get("user-agent") || "";
  if (!ua || BOT_UA.test(ua)) return;

  let raw;
  try { raw = JSON.parse(text); } catch (e) { return; }
  const event = clean(raw);
  if (!event) return;

  const redisUrl = env.UPSTASH_REDIS_REST_URL || env.KV_REST_API_URL;
  const redisToken = env.UPSTASH_REDIS_REST_TOKEN || env.KV_REST_API_TOKEN;
  const secret = env.ANALYTICS_SALT_SECRET;
  if (!redisUrl || !redisToken || !secret) throw new Error("missing env vars");

  const now = new Date();
  const date = now.toISOString().slice(0, 10); // UTC
  const ip = clientIp(request.headers);
  const salt = crypto.createHmac("sha256", secret).update(date).digest("hex");
  const visitor = crypto.createHash("sha256").update(salt + ip + ua).digest("hex").slice(0, 16);

  // Rate limit: one counter per visitor per minute.
  const rlKey = PREFIX + "rl:" + visitor + ":" + Math.floor(now.getTime() / 60000);
  const rl = await redis(redisUrl, redisToken, [["INCR", rlKey], ["EXPIRE", rlKey, "60"]]);
  if (!(Number(rl[0]) <= RATE_LIMIT)) return;

  const h = request.headers;
  const record = Object.assign({ t: now.toISOString() }, event, {
    country: geo(h, "x-vercel-ip-country", 2),
    region: geo(h, "x-vercel-ip-country-region", 3),
    city: geo(h, "x-vercel-ip-city", 80),
  }, parseUa(ua), { visitor: visitor });

  const key = PREFIX + "hits:" + date;
  const ttl = String(STAGE === "production" ? TTL_PROD : TTL_TEST);
  await redis(redisUrl, redisToken, [["RPUSH", key, JSON.stringify(record)], ["EXPIRE", key, ttl]]);
}

// The site itself, this preview deploy's own hosts, or localhost under `vercel dev`.
function allowedOrigin(origin) {
  if (!origin) return false;
  if (STAGE === "development") return /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
  const ok = SITE_ORIGINS.slice();
  if (env.VERCEL_PROJECT_PRODUCTION_URL) ok.push("https://" + env.VERCEL_PROJECT_PRODUCTION_URL);
  if (STAGE === "preview") {
    if (env.VERCEL_URL) ok.push("https://" + env.VERCEL_URL);
    if (env.VERCEL_BRANCH_URL) ok.push("https://" + env.VERCEL_BRANCH_URL);
  }
  return ok.indexOf(origin) !== -1;
}

// Reads the body as text, giving up (null) as soon as it passes `max` bytes.
async function readCapped(request, max) {
  if (!request.body) return "";
  const reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > max) { try { await reader.cancel(); } catch (e) {} return null; }
    chunks.push(value);
  }
  return Buffer.concat(chunks.map((c) => Buffer.from(c))).toString("utf8");
}

// Keeps only the fields plan.md lists, each type-checked and length-capped.
function clean(o) {
  if (!o || typeof o !== "object" || Array.isArray(o)) return null;
  const type = o.type;
  if (type !== "pageview" && type !== "click" && type !== "leave") return null;

  const e = { type: type, path: pick(o.path, /^\/[\w\-./%~]{0,199}$/) || "/" };
  if (type === "click") {
    e.event = pick(o.event, /^[a-z0-9][a-z0-9.\-]{0,79}$/);
    if (!e.event) return null;
  }
  if (type === "leave") {
    e.ms = int(o.ms, 0, 24 * 3600 * 1000);
    e.scroll = int(o.scroll, 0, 100);
  }
  e.ref = pick(o.ref, /^[a-z0-9.\-]{1,100}(:\d{1,5})?$/i);
  e.lang = pick(o.lang, /^[a-z]{2}$/);
  e.nav = pick(o.nav, /^[A-Za-z0-9\-]{1,35}$/);
  e.vw = VW_BUCKETS.indexOf(o.vw) !== -1 ? o.vw : "";
  e.tz = pick(o.tz, /^[A-Za-z0-9_\/+\-]{1,64}$/);
  e.sid = pick(o.sid, /^[a-z0-9]{8,32}$/);
  e.utm = typeof o.utm === "string" ? o.utm.slice(0, 64) : "";
  return e;
}

function pick(v, re) { return typeof v === "string" && re.test(v) ? v : ""; }

function int(v, min, max) {
  const n = Math.round(Number(v));
  return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : 0;
}

function clientIp(h) {
  const xff = h.get("x-forwarded-for") || h.get("x-real-ip") || "";
  return xff.split(",")[0].trim();
}

function geo(h, name, max) {
  let v = h.get(name) || "";
  try { v = decodeURIComponent(v); } catch (e) { /* keep as sent */ }
  return v.slice(0, max);
}

// Coarse only: family names, never versions. Order matters: the in-app
// browsers first (they also say Chrome or Safari, or neither; Instagram's can
// carry Facebook's markers too), then Edge and Opera (which also say
// "Chrome"), then Chrome (which also says "Safari").
function parseUa(ua) {
  const browser =
    /LinkedInApp/.test(ua) ? "LinkedIn" :
    /Instagram/.test(ua) ? "Instagram" :
    /FBAN|FBAV|FB_IAB|FBIOS/.test(ua) ? "Facebook" :
    /Edg(e|A|iOS)?\//.test(ua) ? "Edge" :
    /OPR\/|Opera/.test(ua) ? "Opera" :
    /SamsungBrowser/.test(ua) ? "Samsung" :
    /Firefox\/|FxiOS/.test(ua) ? "Firefox" :
    /Chrome\/|CriOS/.test(ua) ? "Chrome" :
    /Safari\//.test(ua) ? "Safari" : "Other";
  const os =
    /iPhone|iPad|iPod/.test(ua) ? "iOS" :
    /Android/.test(ua) ? "Android" :
    /CrOS/.test(ua) ? "ChromeOS" :
    /Windows/.test(ua) ? "Windows" :
    /Mac OS X|Macintosh/.test(ua) ? "macOS" :
    /Linux/.test(ua) ? "Linux" : "Other";
  const device =
    /iPad|Tablet/.test(ua) || (/Android/.test(ua) && !/Mobile/.test(ua)) ? "tablet" :
    /Mobi|iPhone|iPod/.test(ua) ? "mobile" : "desktop";
  return { browser: browser, os: os, device: device };
}

// Upstash REST pipeline: one HTTP call, several commands, results in order.
async function redis(url, token, commands) {
  const res = await fetch(url.replace(/\/+$/, "") + "/pipeline", {
    method: "POST",
    headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
    body: JSON.stringify(commands),
    signal: AbortSignal.timeout(3000),
  });
  if (!res.ok) throw new Error("upstash " + res.status);
  const out = await res.json();
  return out.map((r) => {
    if (r.error) throw new Error("upstash: " + r.error);
    return r.result;
  });
}
