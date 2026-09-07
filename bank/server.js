// First Packet Bank & Trust - online banking (deliberately vulnerable).
//
//   POST /login                seeded p.ellis/ellis (customer), teller/teller
//   GET  /dashboard            own account; staff/admin see ALL + the wire token
//   GET  /api/accounts/:id     any account, no ownership check (IDOR)
//   POST /api/transfer         staff/admin only (reachable via a forged token)
//
// THE BUG: the JWT check honours  {"alg":"none"}  - take your customer token,
// swap the header to alg:none, set role:"admin", drop the signature, and the
// bank treats you as staff.
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const express = require('express');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

const SECRET = process.env.BANK_JWT_SECRET || 'first-packet-bank-dev';
const b64u = (b) => Buffer.from(b).toString('base64url');
const b64uJson = (o) => b64u(JSON.stringify(o));

function readFlag(tech) {
  try { return fs.readFileSync(`/run/secret/${tech}/flag.txt`, 'utf8').trim(); }
  catch { return `${tech}-flag-missing`; }
}
const FLAG_JWT = readFlag('bank_jwt_none');
const FLAG_IDOR = readFlag('bank_account_idor');

// --- in-memory ledger ----------------------------------------------------
const USERS = {
  'p.ellis': { pw: 'ellis', sub: 'p.ellis', role: 'customer', acct: 1001 },
  'teller':  { pw: 'teller', sub: 'teller', role: 'staff', acct: null },
};
const ACCOUNTS = {
  1001: { id: 1001, holder: 'P. Ellis', balance: 4210.55, memo: 'personal checking' },
  1002: { id: 1002, holder: 'R. Singh', balance: 88900.10, memo: 'contractor - large deposits expected' },
  1003: { id: 1003, holder: 'Town of Packet River', balance: 512300.00,
          memo: `municipal operating account - reconciliation token ${FLAG_IDOR}` },
  1004: { id: 1004, holder: 'Widget Factory Payroll', balance: 61044.00, memo: 'weekly payroll sweep' },
};
let BANK_TOTAL = () => Object.values(ACCOUNTS).reduce((s, a) => s + a.balance, 0);

// --- token handling (with the alg:none flaw) --------------------------
const TOKEN_TTL = parseInt(process.env.PKT_PORTAL_TTL || '180', 10) || 180;

function makeToken(u) {
  const header = b64uJson({ alg: 'HS256', typ: 'JWT' });
  const payload = b64uJson({ sub: u.sub, role: u.role, acct: u.acct,
                             exp: Math.floor(Date.now() / 1000) + TOKEN_TTL });
  const sig = crypto.createHmac('sha256', SECRET).update(`${header}.${payload}`).digest('base64url');
  return `${header}.${payload}.${sig}`;
}

function verify(token) {
  if (!token) return null;
  const [h, p, s] = token.split('.');
  if (!h || !p) return null;
  let header, payload;
  try {
    header = JSON.parse(Buffer.from(h, 'base64url').toString());
    payload = JSON.parse(Buffer.from(p, 'base64url').toString());
  } catch { return null; }
  if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
  // <-- the bug: alg:none accepted. The segmented build pins the algorithm.
  if (header.alg === 'none') {
    if (process.env.JWT_STRICT === '1') return null;
    return payload;
  }
  if (header.alg !== 'HS256') return null;
  const expect = crypto.createHmac('sha256', SECRET).update(`${h}.${p}`).digest('base64url');
  if (s !== expect) return null;
  return payload;
}

function cookies(req) {
  return Object.fromEntries((req.headers.cookie || '').split(';').map((c) => {
    const i = c.indexOf('='); return [c.slice(0, i).trim(), c.slice(i + 1).trim()];
  }));
}
const claims = (req) => verify(cookies(req).bank_jwt);

// --- routes ---------------------------------------------------------
const page = (body) => `<!doctype html><meta charset=utf-8>
<title>First Packet Bank &amp; Trust</title>
<style>body{margin:0;background:#f3ecdd;color:#3b3226;font:15px/1.5 ui-rounded,system-ui,sans-serif}
.bar{background:#fffdf7;border-bottom:2px solid #e4d8bf;padding:12px 20px;font-weight:800;letter-spacing:.06em}
main{max-width:620px;margin:26px auto;padding:0 20px}
.card{background:#fffdf7;border:1px solid #e4d8bf;border-radius:12px;padding:16px;margin-bottom:12px}
input{display:block;width:100%;margin:6px 0;padding:7px 10px;border:1px solid #e4d8bf;border-radius:8px;font:inherit}
button{padding:7px 16px;border:0;border-radius:8px;background:#2f8fbf;color:#fff;font:inherit;font-weight:600;cursor:pointer}
table{width:100%;border-collapse:collapse}td{padding:4px 8px;border-bottom:1px solid #efe6d0}code{word-break:break-all}</style>
<div class=bar>FIRST PACKET BANK &amp; TRUST</div><main>${body}</main>`;

app.get('/health', (_req, res) => res.send('ok'));

app.get('/', (req, res) => {
  if (claims(req)) return res.redirect('/dashboard');
  res.send(page(`<div class=card><h2>Online banking</h2>
    <form method=post action=/login>
      <input name=username placeholder=username autofocus>
      <input name=password type=password placeholder=password>
      <button>Sign in</button></form></div>`));
});

app.post('/login', (req, res) => {
  const u = USERS[String(req.body.username || '').toLowerCase()];
  if (!u || u.pw !== req.body.password) {
    return res.status(401).send(page('<div class=card><p>Sign-in failed. <a href=/>back</a></p></div>'));
  }
  res.setHeader('Set-Cookie', `bank_jwt=${makeToken(u)}; HttpOnly; Path=/; SameSite=Lax`);
  res.redirect('/dashboard');
});

app.get('/dashboard', (req, res) => {
  const c = claims(req);
  if (!c) return res.redirect('/');
  if (c.role === 'staff' || c.role === 'admin') {
    const rows = Object.values(ACCOUNTS).map((a) =>
      `<tr><td>${a.id}</td><td>${a.holder}</td><td>$${a.balance.toFixed(2)}</td></tr>`).join('');
    return res.send(page(`<div class=card><h2>All accounts (${c.role})</h2>
      <table>${rows}</table>
      <p>Bank total: $${BANK_TOTAL().toFixed(2)}</p>
      <p>Fed wire settlement token: <code>${FLAG_JWT}</code></p></div>
      <div class=card><form method=post action=/api/transfer>
        <input name=to placeholder="to account"><input name=amount placeholder=amount>
        <button>Transfer</button></form></div>`));
  }
  const a = ACCOUNTS[c.acct] || { balance: 0, holder: c.sub, memo: '' };
  res.send(page(`<div class=card><h2>Your account</h2>
    <p>${a.holder} &middot; #${c.acct}</p><p>Balance: $${a.balance.toFixed(2)}</p>
    <p><a href=/api/accounts/${c.acct}>account detail (JSON API)</a></p></div>`));
});

app.get('/api/accounts/:id', (req, res) => {
  if (!claims(req)) return res.status(401).json({ error: 'auth required' });
  const a = ACCOUNTS[Number(req.params.id)];        // no ownership check
  if (!a) return res.status(404).json({ error: 'no such account' });
  res.json(a);
});

app.post('/api/transfer', (req, res) => {
  const c = claims(req);
  if (!c || (c.role !== 'staff' && c.role !== 'admin')) {
    return res.status(403).json({ error: 'staff only' });
  }
  const to = ACCOUNTS[Number(req.body.to)];
  const amt = Number(req.body.amount) || 0;
  if (!to) return res.status(400).json({ error: 'bad destination' });
  for (const a of Object.values(ACCOUNTS)) { if (a.id !== to.id) { to.balance += a.balance; a.balance = 0; } }
  res.json({ ok: true, note: 'swept', bank_total: BANK_TOTAL() });
});

app.listen(8100, () => console.log('[bank] listening on 8100'));
