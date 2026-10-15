// Analytics export — GET /api/export?from=YYYY-MM-DD&to=YYYY-MM-DD
// Returns the collector's records (api/hit.js) as NDJSON, one stored record
// per line, oldest day first. Read by scripts/analytics/ (the Colab notebook).
// CLAUDE.md → Analytics; plan.md → Phase 3 → "Analytics, self-built" (A3).
//
// Node built-ins + fetch only: no package.json, no npm, no build step.
//
// Access: only with the header  Authorization: Bearer <ANALYTICS_EXPORT_TOKEN>.
// Anything unauthorized — no or wrong token, any method but GET, the token
// missing on the server — gets an empty 404, so the endpoint looks absent. The
// token is compared in constant time (both sides hashed first, so the length
// doesn't leak either). No CORS headers are ever sent, so no other site's
// script can read a response. The token and the Authorization header are never
// logged.
//
// With a valid token:
//   400  bad dates: both required, real calendar dates, from <= to, at most
//        MAX_DAYS days. The notebook splits longer ranges into requests itself.
//   413  the body would pass MAX_BYTES (Vercel caps a function response at
//        4.5 MB); the notebook halves the range and retries.
//   502  Upstash failed;  503  Upstash isn't configured.
//   200  application/x-ndjson (an empty body when there is no data).
//
// Which records: the same prefix rule as api/hit.js. Production reads
// hits:<date>, preview deploys preview:hits:<date>, `vercel dev` dev:hits:<date>.
import crypto from "node:crypto";

const MAX_DAYS = 31;
const MAX_BYTES = 4_000_000;
const PAGE = 1000;          // LRANGE page size (records)
const PAGES_PER_CALL = 4;   // LRANGE pages per Upstash pipeline call

const env = process.env;
const STAGE = env.VERCEL_ENV === "production" ? "production" : env.VERCEL_ENV === "preview" ? "preview" : "development";
const PREFIX = STAGE === "production" ? "" : STAGE === "preview" ? "preview:" : "dev:";

const BASE_HEADERS = { "Cache-Control": "no-store", "X-Robots-Tag": "noindex", "X-Content-Type-Options": "nosniff" };

const notFound = () => new Response(null, { status: 404, headers: BASE_HEADERS });
const text = (status, msg) => new Response(msg + "\n", { status, headers: Object.assign({ "Content-Type": "text/plain; charset=utf-8" }, BASE_HEADERS) });

export default {
  async fetch(request) {
    if (request.method !== "GET") return notFound();
    if (!authorized(request.headers.get("authorization"))) return notFound();

    const url = new URL(request.url);
    const range = parseRange(url.searchParams.get("from"), url.searchParams.get("to"));
    if (typeof range === "string") return text(400, range);

    const redisUrl = env.UPSTASH_REDIS_REST_URL || env.KV_REST_API_URL;
    const redisToken = env.UPSTASH_REDIS_REST_TOKEN || env.KV_REST_API_TOKEN;
    if (!redisUrl || !redisToken) return text(503, "storage not configured");

    let body;
    try {
      body = await readRange(redisUrl, redisToken, range);
    } catch (e) {
      console.error("export: " + (e && e.message ? e.message : "error"));
      return text(502, "storage error");
    }
    if (body === null) return text(413, "range too large: use a shorter range");

    return new Response(body, {
      status: 200,
      headers: Object.assign({ "Content-Type": "application/x-ndjson; charset=utf-8" }, BASE_HEADERS),
    });
  },
};

// Constant-time: both sides are SHA-256 digests (always 32 bytes), so neither
// the content nor the length of the real token shows in the timing.
function authorized(header) {
  const expected = env.ANALYTICS_EXPORT_TOKEN || "";
  const m = /^Bearer\s+(\S+)\s*$/i.exec(header || "");
  const given = m ? m[1] : "";
  const a = crypto.createHash("sha256").update(given).digest();
  const b = crypto.createHash("sha256").update(expected).digest();
  const same = crypto.timingSafeEqual(a, b);
  return same && expected.length >= 32 && given.length >= 32;
}

// → array of "YYYY-MM-DD" days, or an error message.
function parseRange(from, to) {
  if (!from || !to) return "from and to are required (YYYY-MM-DD)";
  const a = day(from), b = day(to);
  if (a === null) return "from is not a valid date (YYYY-MM-DD)";
  if (b === null) return "to is not a valid date (YYYY-MM-DD)";
  if (a > b) return "from is after to";
  const n = Math.round((b - a) / 86400000) + 1;
  if (n > MAX_DAYS) return "range is " + n + " days; the maximum is " + MAX_DAYS;
  const days = [];
  for (let t = a; t <= b; t += 86400000) days.push(new Date(t).toISOString().slice(0, 10));
  return days;
}

// "YYYY-MM-DD" → UTC ms, or null unless it's a real calendar date.
function day(s) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  const t = Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
  return new Date(t).toISOString().slice(0, 10) === s ? t : null;
}

// NDJSON for the days, or null if it would pass MAX_BYTES.
async function readRange(url, token, days) {
  const keys = days.map((d) => PREFIX + "hits:" + d);
  const lengths = await redis(url, token, keys.map((k) => ["LLEN", k]));

  // One LRANGE per page of each day, in order.
  const pages = [];
  let total = 0;
  keys.forEach((k, i) => {
    const n = Number(lengths[i]) || 0;
    for (let start = 0; start < n; start += PAGE) pages.push(["LRANGE", k, String(start), String(Math.min(start + PAGE, n) - 1)]);
    total += n;
  });
  if (!total) return "";

  const chunks = [];
  let bytes = 0;
  for (let i = 0; i < pages.length; i += PAGES_PER_CALL) {
    const results = await redis(url, token, pages.slice(i, i + PAGES_PER_CALL));
    for (const records of results) {
      for (const r of records) {
        bytes += Buffer.byteLength(r) + 1;
        if (bytes > MAX_BYTES) return null;
        chunks.push(r);
      }
    }
  }
  return chunks.join("\n") + "\n";
}

// Upstash REST pipeline: one HTTP call, several commands, results in order.
// (Same helper as api/hit.js; each function is self-contained.)
async function redis(url, token, commands) {
  const res = await fetch(url.replace(/\/+$/, "") + "/pipeline", {
    method: "POST",
    headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
    body: JSON.stringify(commands),
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) throw new Error("upstash " + res.status);
  const out = await res.json();
  return out.map((r) => {
    if (r.error) throw new Error("upstash: " + r.error);
    return r.result;
  });
}
