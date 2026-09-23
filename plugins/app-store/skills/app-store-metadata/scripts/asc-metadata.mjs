#!/usr/bin/env node
// asc-metadata.mjs: check, diff, push and verify App Store metadata kept as one
// JSON file per locale. No dependencies, Node 18+.
//
//   node asc-metadata.mjs check  [--dir ./appstore-metadata] [--locales en-US,fr-FR] [--rules rules.json]
//   node asc-metadata.mjs diff   --version 1.2.0 [--dir …] [--locales …] [--fields …]      (GET only)
//   node asc-metadata.mjs push   --version 1.2.0 [--dir …] [--locales …] [--fields …] --yes (WRITES)
//   node asc-metadata.mjs verify --version 1.2.0 [--dir …] [--locales …] [--fields …]      (GET only)
//
// Credentials come ONLY from the process environment, never from a .env file:
//   APP_STORE_ISSUER_ID, APP_STORE_KEY_ID, APP_STORE_APP_ID, APP_STORE_PRIVATE_KEY_PATH
// Reason: in many repos a .env also holds an unrelated APP_STORE_PRIVATE_KEY (StoreKit,
// server notifications). Auto-loading it would sign requests with the wrong key.
//
// Other options:
//   --rules <file>            JSON rules (forbidden patterns, required fields, competitor brands)
//   --forbid <regex>          extra forbidden pattern on every field (repeatable, case-insensitive)
//   --competitors a,b,c       brand names that must not appear in name, subtitle or keywords
//   --no-default-rules        drop the built-in forbidden patterns
//   --secondary-category ID   push only: also set the secondary category (e.g. PRODUCTIVITY)
//   --json                    diff only: machine-readable output
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { basename, resolve } from 'node:path';
import crypto from 'node:crypto';

const API = 'https://api.appstoreconnect.apple.com';

const LIMITS = {
  name: 30,
  subtitle: 30,
  keywords: 100,
  description: 4000,
  promotionalText: 170,
  whatsNew: 4000,
  privacyPolicyUrl: 255,
  marketingUrl: 255,
  supportUrl: 255,
};
const ALL_FIELDS = Object.keys(LIMITS);
// appInfoLocalizations are per app and only editable while an appInfo is in an editable state.
const APP_INFO_FIELDS = ['name', 'subtitle', 'privacyPolicyUrl'];
// appStoreVersionLocalizations are per version.
const VERSION_FIELDS = ['keywords', 'description', 'promotionalText', 'whatsNew', 'marketingUrl', 'supportUrl'];
const LONG_FIELDS = new Set(['description', 'whatsNew']);
const TEXT_FIELDS = ['name', 'subtitle', 'keywords', 'description', 'promotionalText', 'whatsNew'];

const EDITABLE_VERSION_STATES = new Set(['PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED', 'METADATA_REJECTED', 'INVALID_BINARY']);
const EDITABLE_INFO_STATES = ['PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED', 'METADATA_REJECTED'];
// Promotional text can be changed on a live version without a new submission.
const ALWAYS_EDITABLE = new Set(['promotionalText']);

// Built-in forbidden patterns. Disable with --no-default-rules or "useDefaults": false.
const DEFAULT_FORBIDDEN = [
  {
    pattern: '^\\s*(here is|here\'s|here are|sure[,!]|certainly[,!]|below is|voici|hier ist|hier sind|hier is|ecco|aquí (está|tienes)|aqui está|segue|oto)\\b',
    flags: 'iu',
    fields: ['description', 'whatsNew', 'promotionalText'],
    message: 'starts like an AI preamble ("Here is the optimized…")',
  },
  {
    pattern: '\\b(TODO|TBD|FIXME)\\b|lorem ipsum|\\{\\{|\\}\\}',
    flags: 'u',
    fields: '*',
    message: 'placeholder text',
  },
  {
    pattern: '^\\s*-{3,}\\s*$|\\*\\*|^#{1,6}\\s',
    flags: 'mu',
    fields: ['description', 'whatsNew', 'promotionalText'],
    message: 'markdown syntax (the App Store shows it as raw characters)',
    level: 'warn',
  },
];
const DEFAULT_REQUIRED = ['name', 'keywords', 'description'];

// ---------------------------------------------------------------- CLI

function parseArgs(argv) {
  const [command, ...rest] = argv;
  const opts = { command, dir: './appstore-metadata', forbid: [], useDefaults: true, yes: false, json: false };
  for (let i = 0; i < rest.length; i += 1) {
    const a = rest[i];
    const next = () => {
      const v = rest[++i];
      if (v === undefined) throw new Error(`${a} needs a value`);
      return v;
    };
    if (a === '--dir') opts.dir = next();
    else if (a === '--version') opts.version = next();
    else if (a === '--locales') opts.locales = next().split(',').map((s) => s.trim()).filter(Boolean);
    else if (a === '--fields') opts.fields = next().split(',').map((s) => s.trim()).filter(Boolean);
    else if (a === '--rules') opts.rules = next();
    else if (a === '--forbid') opts.forbid.push(next());
    else if (a === '--competitors') opts.competitors = next().split(',').map((s) => s.trim()).filter(Boolean);
    else if (a === '--no-default-rules') opts.useDefaults = false;
    else if (a === '--secondary-category') opts.secondaryCategory = next();
    else if (a === '--yes') opts.yes = true;
    else if (a === '--json') opts.json = true;
    else if (a === '--help' || a === '-h') opts.command = 'help';
    else throw new Error(`unknown argument: ${a}`);
  }
  if (!['check', 'diff', 'push', 'verify', 'help', undefined].includes(opts.command)) {
    throw new Error(`unknown command: ${opts.command} (check | diff | push | verify)`);
  }
  if (opts.fields) {
    const bad = opts.fields.filter((f) => !ALL_FIELDS.includes(f));
    if (bad.length) throw new Error(`unknown field(s): ${bad.join(', ')}. Known: ${ALL_FIELDS.join(', ')}`);
  }
  if (['diff', 'push', 'verify'].includes(opts.command) && !opts.version) {
    throw new Error(`${opts.command} needs --version <versionString> (the App Store version, e.g. 1.2.0)`);
  }
  return opts;
}

function usage() {
  console.log(`Usage:
  node asc-metadata.mjs check  [--dir DIR] [--locales L1,L2] [--rules FILE]
  node asc-metadata.mjs diff   --version X [--dir DIR] [--locales …] [--fields …] [--json]
  node asc-metadata.mjs push   --version X [--dir DIR] [--locales …] [--fields …] [--secondary-category ID] --yes
  node asc-metadata.mjs verify --version X [--dir DIR] [--locales …] [--fields …]

DIR defaults to ./appstore-metadata (one <locale>.json per App Store locale).
Env (process only, no .env loading): APP_STORE_ISSUER_ID, APP_STORE_KEY_ID,
APP_STORE_APP_ID, APP_STORE_PRIVATE_KEY_PATH.`);
}

// ---------------------------------------------------------------- Metadata

function loadMetadata(dir, filter) {
  const abs = resolve(dir);
  if (!existsSync(abs)) throw new Error(`metadata folder not found: ${abs} (use --dir)`);
  const files = readdirSync(abs).filter((f) => f.endsWith('.json'));
  if (!files.length) throw new Error(`no <locale>.json file in ${abs}`);
  const all = files.map((f) => {
    let m;
    try {
      m = JSON.parse(readFileSync(resolve(abs, f), 'utf8'));
    } catch (e) {
      throw new Error(`${f}: invalid JSON (${e.message})`);
    }
    if (!m.locale) m.locale = basename(f, '.json');
    m.__file = f;
    return m;
  });
  const selected = filter ? all.filter((m) => filter.includes(m.locale)) : all;
  if (filter) {
    const missing = filter.filter((l) => !selected.some((m) => m.locale === l));
    if (missing.length) throw new Error(`no metadata file for locale(s): ${missing.join(', ')}`);
  }
  return selected.sort((a, b) => a.locale.localeCompare(b.locale));
}

function loadRules(opts) {
  let file = {};
  if (opts.rules) {
    try {
      file = JSON.parse(readFileSync(resolve(opts.rules), 'utf8'));
    } catch (e) {
      throw new Error(`cannot read rules file ${opts.rules}: ${e.message}`);
    }
  }
  const useDefaults = opts.useDefaults && file.useDefaults !== false;
  const forbidden = [
    ...(useDefaults ? DEFAULT_FORBIDDEN : []),
    ...(file.forbidden ?? []),
    ...opts.forbid.map((p) => ({ pattern: p, flags: 'iu', fields: '*', message: `matches forbidden pattern /${p}/` })),
  ].map((r) => {
    try {
      return { ...r, re: new RegExp(r.pattern, r.flags ?? 'u') };
    } catch (e) {
      throw new Error(`invalid forbidden pattern ${r.pattern}: ${e.message}`);
    }
  });
  return {
    required: file.required ?? DEFAULT_REQUIRED,
    forbidden,
    competitors: [...(file.competitorBrands ?? []), ...(opts.competitors ?? [])].map((c) => c.toLowerCase()),
    keywordsMinLength: file.keywordsMinLength ?? 90,
  };
}

function words(text) {
  return new Set(
    (text ?? '')
      .toLowerCase()
      .split(/[^\p{L}\p{N}]+/u)
      .filter((w) => w.length > 2),
  );
}

const ENGLISH_MARKERS = /\b(the|and|your|with|you|for|this|that)\b/giu;

function checkMetadata(items, rules) {
  const errors = [];
  const warnings = [];
  for (const m of items) {
    const tag = `[${m.locale}]`;
    if (m.__file !== `${m.locale}.json`) warnings.push(`${tag} file is ${m.__file} but locale is ${m.locale}`);
    for (const field of Object.keys(m)) {
      if (!field.startsWith('__') && field !== 'locale' && !ALL_FIELDS.includes(field)) warnings.push(`${tag} unknown field "${field}" (ignored)`);
    }
    for (const [field, limit] of Object.entries(LIMITS)) {
      const v = m[field];
      if (v === undefined || v === null || v === '') {
        if (rules.required.includes(field)) errors.push(`${tag} ${field}: missing`);
        continue;
      }
      if (typeof v !== 'string') {
        errors.push(`${tag} ${field}: must be a string`);
        continue;
      }
      if (v.length > limit) errors.push(`${tag} ${field}: ${v.length} > ${limit} characters`);
      if (v !== v.trimEnd() && field !== 'description') warnings.push(`${tag} ${field}: trailing whitespace`);
    }
    for (const r of rules.forbidden) {
      const fields = r.fields === '*' || !r.fields ? TEXT_FIELDS.concat(['marketingUrl', 'supportUrl', 'privacyPolicyUrl']) : r.fields;
      for (const f of fields) {
        if (typeof m[f] === 'string' && r.re.test(m[f])) (r.level === 'warn' ? warnings : errors).push(`${tag} ${f}: ${r.message ?? `matches /${r.pattern}/`}`);
      }
    }
    if (typeof m.description === 'string' && /^\s/.test(m.description)) errors.push(`${tag} description starts with whitespace (wastes the lines shown before "more")`);

    if (typeof m.keywords === 'string' && m.keywords) {
      if (/,\s|\s,/.test(m.keywords)) errors.push(`${tag} keywords: space around a comma wastes characters`);
      const list = m.keywords.split(',').map((k) => k.trim().toLowerCase()).filter(Boolean);
      const seen = new Set();
      const dupSelf = list.filter((k) => (seen.has(k) ? true : (seen.add(k), false)));
      if (dupSelf.length) errors.push(`${tag} keywords repeated: ${[...new Set(dupSelf)].join(', ')}`);
      const indexed = new Set([...words(m.name), ...words(m.subtitle)]);
      const dupIndexed = list.filter((k) => {
        const w = [...words(k)];
        return w.length > 0 && w.every((x) => indexed.has(x));
      });
      if (dupIndexed.length) errors.push(`${tag} keywords already indexed via name/subtitle: ${dupIndexed.join(', ')}`);
      if (m.keywords.length < rules.keywordsMinLength) warnings.push(`${tag} keywords use ${m.keywords.length}/100 characters (aim for 94-100)`);
    }
    for (const brand of rules.competitors) {
      for (const f of ['name', 'subtitle', 'keywords']) {
        if (typeof m[f] === 'string' && m[f].toLowerCase().includes(brand)) errors.push(`${tag} ${f}: competitor brand "${brand}" (guideline 2.3.7)`);
      }
    }
    for (const f of ['marketingUrl', 'supportUrl', 'privacyPolicyUrl']) {
      const v = m[f];
      if (typeof v !== 'string' || !v) continue;
      if (!/^https:\/\//.test(v)) warnings.push(`${tag} ${f}: not an https URL`);
      else if (f === 'marketingUrl' && /^https:\/\/[^/]+\/[^?#]*[^/?#]$/.test(v) && !/\.[a-z0-9]{2,5}$/i.test(v)) {
        warnings.push(`${tag} marketingUrl has no trailing slash: open it once, some hosts 404 without it`);
      }
    }
    if (!/^en(-|$)/.test(m.locale) && typeof m.description === 'string') {
      const hits = (m.description.match(ENGLISH_MARKERS) ?? []).length;
      if (hits >= 4) warnings.push(`${tag} description: ${hits} common English words, check for untranslated sentences`);
    }
  }
  return { errors, warnings };
}

function printLengths(items) {
  for (const m of items) {
    const len = (f) => String((m[f] ?? '').length);
    console.log(
      `  ${m.locale.padEnd(6)} name ${len('name').padStart(2)}/30  subtitle ${len('subtitle').padStart(2)}/30  keywords ${len('keywords').padStart(3)}/100  promo ${len('promotionalText').padStart(3)}/170  description ${len('description').padStart(4)}/4000  whatsNew ${len('whatsNew').padStart(4)}/4000`,
    );
  }
}

function runCheck(items, rules) {
  console.log(`[check] ${items.length} locale(s): ${items.map((m) => m.locale).join(', ')}`);
  printLengths(items);
  const { errors, warnings } = checkMetadata(items, rules);
  for (const w of warnings) console.log(`  warn  ${w}`);
  if (errors.length) {
    console.error('[check] FAILED');
    for (const e of errors) console.error(`  error ${e}`);
    return false;
  }
  console.log(`[check] OK${warnings.length ? ` (${warnings.length} warning(s))` : ''}`);
  return true;
}

// ---------------------------------------------------------------- App Store Connect

function credentials() {
  const { APP_STORE_ISSUER_ID: iss, APP_STORE_KEY_ID: kid, APP_STORE_APP_ID: appId, APP_STORE_PRIVATE_KEY_PATH: keyPath } = process.env;
  const missing = [!iss && 'APP_STORE_ISSUER_ID', !kid && 'APP_STORE_KEY_ID', !appId && 'APP_STORE_APP_ID', !keyPath && 'APP_STORE_PRIVATE_KEY_PATH'].filter(Boolean);
  if (missing.length) throw new Error(`missing env: ${missing.join(', ')} (pass them on the command line; .env files are ignored on purpose)`);
  let key;
  try {
    key = readFileSync(keyPath, 'utf8');
  } catch (e) {
    throw new Error(`cannot read APP_STORE_PRIVATE_KEY_PATH (${e.code ?? e.message})`);
  }
  if (!key.includes('PRIVATE KEY')) throw new Error('APP_STORE_PRIVATE_KEY_PATH is not a PEM .p8 key');
  return { iss, kid, appId, key };
}

function jwt({ iss, kid, key }) {
  const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
  const now = Math.floor(Date.now() / 1000);
  const head = `${b64({ alg: 'ES256', kid, typ: 'JWT' })}.${b64({ iss, iat: now, exp: now + 900, aud: 'appstoreconnect-v1' })}`;
  const sig = crypto.sign('sha256', Buffer.from(head), { key, dsaEncoding: 'ieee-p1363' }).toString('base64url');
  return `${head}.${sig}`;
}

function client(creds, { readOnly }) {
  return async function api(method, path, body) {
    if (readOnly && method !== 'GET') throw new Error(`refusing ${method} in a read-only command`);
    const res = await fetch(API + path, {
      method,
      headers: { Authorization: `Bearer ${jwt(creds)}`, 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    const text = await res.text();
    if (!res.ok) throw new Error(`${method} ${path} -> HTTP ${res.status}: ${text.slice(0, 600)}`);
    return text ? JSON.parse(text) : {};
  };
}

async function resolveTargets(api, appId, version) {
  const infos = (await api('GET', `/v1/apps/${appId}/appInfos?fields[appInfos]=state&limit=20`)).data;
  const states = infos.map((i) => i.attributes.state ?? i.attributes.appStoreState);
  let editableInfo = null;
  for (const s of EDITABLE_INFO_STATES) {
    editableInfo = infos.find((i) => (i.attributes.state ?? i.attributes.appStoreState) === s);
    if (editableInfo) break;
  }
  // Read-only fallback: the appInfo in review, else the live one.
  const readInfo =
    editableInfo ??
    infos.find((i) => !['READY_FOR_DISTRIBUTION', 'READY_FOR_SALE', 'REPLACED_WITH_NEW_INFO'].includes(i.attributes.state ?? i.attributes.appStoreState)) ??
    infos[0];

  const vers = (
    await api(
      'GET',
      `/v1/apps/${appId}/appStoreVersions?filter[platform]=IOS&filter[versionString]=${encodeURIComponent(version)}&fields[appStoreVersions]=versionString,appVersionState,appStoreState`,
    )
  ).data;
  const ver = vers[0];
  if (!ver) throw new Error(`version ${version} not found on App Store Connect (create it there first)`);
  const verState = ver.attributes.appVersionState ?? ver.attributes.appStoreState;
  return { infos, states, editableInfo, readInfo, ver, verState };
}

async function listLocs(api, path) {
  if (!path) return new Map();
  const res = await api('GET', `${path}?limit=200`);
  return new Map(res.data.map((r) => [r.attributes.locale, r]));
}

function lineDiff(before, after) {
  const a = (before ?? '').split('\n');
  const b = (after ?? '').split('\n');
  const setA = new Set(a);
  const setB = new Set(b);
  return [...a.filter((l) => !setB.has(l)).map((l) => `      - ${l}`), ...b.filter((l) => !setA.has(l)).map((l) => `      + ${l}`)].join('\n');
}

function fieldsFor(opts, m) {
  const wanted = opts.fields ?? ALL_FIELDS;
  return wanted.filter((f) => typeof m[f] === 'string' && m[f] !== '');
}

function computeChanges(items, opts, infoLocs, verLocs) {
  const out = [];
  for (const m of items) {
    const ai = infoLocs.get(m.locale);
    const vl = verLocs.get(m.locale);
    const changes = [];
    for (const f of fieldsFor(opts, m)) {
      const src = APP_INFO_FIELDS.includes(f) ? ai : vl;
      const before = src?.attributes?.[f] ?? null;
      if (before !== m[f]) changes.push({ field: f, before, after: m[f] });
    }
    out.push({ locale: m.locale, infoMissing: !ai, versionMissing: !vl, changes });
  }
  return out;
}

function printChanges(report) {
  let n = 0;
  for (const r of report) {
    const lines = [];
    if (r.infoMissing) lines.push('    (app info localization missing on App Store Connect: it will be CREATED)');
    else if (r.versionMissing) lines.push('    (version localization missing: it will be CREATED)');
    for (const c of r.changes) {
      n += 1;
      if (LONG_FIELDS.has(c.field)) lines.push(`    ${c.field} (${(c.before ?? '').length} -> ${c.after.length} chars)\n${lineDiff(c.before, c.after)}`);
      else lines.push(`    ${c.field}\n      before: ${c.before ?? '(empty)'}\n      after:  ${c.after}`);
    }
    if (lines.length) console.log(`\n[${r.locale}]\n${lines.join('\n')}`);
  }
  return n;
}

function describeState(t) {
  console.log(`app info states: ${t.states.join(', ') || '(none)'}`);
  if (!t.editableInfo) console.log('  ! no editable app info: name, subtitle and privacy URL CANNOT be changed now (create a new version in App Store Connect)');
  console.log(`version ${t.ver.attributes.versionString}: ${t.verState}${EDITABLE_VERSION_STATES.has(t.verState) ? '' : ' (not editable: only promotionalText can change)'}`);
}

async function runDiff(items, opts) {
  const creds = credentials();
  const api = client(creds, { readOnly: true });
  const t = await resolveTargets(api, creds.appId, opts.version);
  const infoLocs = await listLocs(api, t.readInfo && `/v1/appInfos/${t.readInfo.id}/appInfoLocalizations`);
  const verLocs = await listLocs(api, `/v1/appStoreVersions/${t.ver.id}/appStoreVersionLocalizations`);
  const report = computeChanges(items, opts, infoLocs, verLocs);
  if (opts.json) {
    console.log(JSON.stringify({ appInfoStates: t.states, versionState: t.verState, report }, null, 2));
    return;
  }
  describeState(t);
  const n = printChanges(report);
  const remoteOnly = [...new Set([...infoLocs.keys(), ...verLocs.keys()])].filter((l) => !items.some((m) => m.locale === l));
  if (remoteOnly.length && !opts.locales) console.log(`\nlocales on App Store Connect without a local file (left untouched): ${remoteOnly.join(', ')}`);
  console.log(`\n${n} field(s) differ across ${items.length} locale(s). Nothing was written.`);
}

async function runVerify(items, opts) {
  const creds = credentials();
  const api = client(creds, { readOnly: true });
  const t = await resolveTargets(api, creds.appId, opts.version);
  describeState(t);
  const infoLocs = await listLocs(api, t.readInfo && `/v1/appInfos/${t.readInfo.id}/appInfoLocalizations`);
  const verLocs = await listLocs(api, `/v1/appStoreVersions/${t.ver.id}/appStoreVersionLocalizations`);
  const diffs = [];
  for (const r of computeChanges(items, opts, infoLocs, verLocs)) {
    if (r.infoMissing) diffs.push(`[${r.locale}] app info localization missing`);
    if (r.versionMissing) diffs.push(`[${r.locale}] version localization missing`);
    for (const c of r.changes) diffs.push(`[${r.locale}] ${c.field} differs`);
  }
  if (t.readInfo) {
    const cat = await api('GET', `/v1/appInfos/${t.readInfo.id}?include=primaryCategory,secondaryCategory`);
    const rel = cat.data.relationships ?? {};
    console.log(`categories: primary=${rel.primaryCategory?.data?.id ?? 'none'} secondary=${rel.secondaryCategory?.data?.id ?? 'none'}`);
  }
  if (diffs.length) {
    console.error('[verify] DIFFERENCES');
    for (const d of diffs) console.error(`  - ${d}`);
    return false;
  }
  console.log('[verify] App Store Connect matches local metadata');
  return true;
}

async function upsert(api, type, parent, existing, locale, attributes) {
  if (!Object.keys(attributes).length) return 'skipped';
  if (existing) {
    await api('PATCH', `/v1/${type}/${existing.id}`, { data: { type, id: existing.id, attributes } });
    return 'updated';
  }
  await api('POST', `/v1/${type}`, {
    data: {
      type,
      attributes: { locale, ...attributes },
      relationships: { [parent.rel]: { data: { type: parent.type, id: parent.id } } },
    },
  });
  return 'created';
}

async function runPush(items, opts) {
  const creds = credentials();
  const readApi = client(creds, { readOnly: true });
  const t = await resolveTargets(readApi, creds.appId, opts.version);
  describeState(t);

  const requested = new Set(items.flatMap((m) => fieldsFor(opts, m)));
  const wantsInfo = [...requested].some((f) => APP_INFO_FIELDS.includes(f));
  const wantsLocked = [...requested].some((f) => VERSION_FIELDS.includes(f) && !ALWAYS_EDITABLE.has(f));
  if (wantsInfo && !t.editableInfo) throw new Error('name/subtitle/privacyPolicyUrl requested but no app info is editable. Create a new version, or pass --fields without them.');
  if (wantsLocked && !EDITABLE_VERSION_STATES.has(t.verState)) {
    throw new Error(`version ${opts.version} is ${t.verState}: keywords, description, whatsNew and URLs are locked. Only --fields promotionalText can be pushed now.`);
  }

  const infoLocs = await listLocs(readApi, t.readInfo && `/v1/appInfos/${t.readInfo.id}/appInfoLocalizations`);
  const verLocs0 = await listLocs(readApi, `/v1/appStoreVersions/${t.ver.id}/appStoreVersionLocalizations`);
  const report = computeChanges(items, opts, infoLocs, verLocs0);
  if (!t.editableInfo) for (const r of report) r.infoMissing = false;
  const n = printChanges(report);

  if (!opts.yes) {
    console.log(`\n${n} field(s) would be written to the PUBLIC App Store listing of version ${opts.version}.`);
    console.log('Nothing was written. Show this diff to the owner, get an explicit OK, then re-run with --yes.');
    process.exitCode = 2;
    return;
  }

  console.log(`\n[push] WRITING to App Store Connect, version ${opts.version} (${t.verState})`);
  const api = client(creds, { readOnly: false });
  let verLocs = verLocs0;
  for (const m of items) {
    const r = report.find((x) => x.locale === m.locale);
    const fields = fieldsFor(opts, m);
    const infoAttrs = Object.fromEntries(fields.filter((f) => APP_INFO_FIELDS.includes(f)).map((f) => [f, m[f]]));
    const verAttrs = Object.fromEntries(fields.filter((f) => VERSION_FIELDS.includes(f)).map((f) => [f, m[f]]));
    if (!r.changes.length && !r.infoMissing && !r.versionMissing) {
      console.log(`[push] ${m.locale}: unchanged`);
      continue;
    }
    let a = 'skipped';
    if (t.editableInfo && (r.infoMissing || Object.keys(infoAttrs).length)) {
      a = await upsert(api, 'appInfoLocalizations', { rel: 'appInfo', type: 'appInfos', id: t.editableInfo.id }, infoLocs.get(m.locale), m.locale, infoAttrs);
      // Creating an app info localization also creates the version localization: re-read before writing.
      if (a === 'created') verLocs = await listLocs(readApi, `/v1/appStoreVersions/${t.ver.id}/appStoreVersionLocalizations`);
    }
    const b = await upsert(api, 'appStoreVersionLocalizations', { rel: 'appStoreVersion', type: 'appStoreVersions', id: t.ver.id }, verLocs.get(m.locale), m.locale, verAttrs);
    console.log(`[push] ${m.locale}: app info ${a}, version ${b}`);
  }
  if (opts.secondaryCategory) {
    if (!t.editableInfo) throw new Error('--secondary-category needs an editable app info');
    await api('PATCH', `/v1/appInfos/${t.editableInfo.id}`, {
      data: { type: 'appInfos', id: t.editableInfo.id, relationships: { secondaryCategory: { data: { type: 'appCategories', id: opts.secondaryCategory } } } },
    });
    console.log(`[push] secondary category set to ${opts.secondaryCategory}`);
  }
  console.log('[push] done, verifying…');
  if (!(await runVerify(items, opts))) process.exitCode = 1;
}

// ---------------------------------------------------------------- Main

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (!opts.command || opts.command === 'help') return usage();
  const items = loadMetadata(opts.dir, opts.locales);
  const rules = loadRules(opts);

  if (opts.command === 'check') {
    if (!runCheck(items, rules)) process.exitCode = 1;
    return;
  }
  if (opts.command === 'push') {
    console.log('WARNING: push modifies the App Store listing of this version. It must follow check + diff + an explicit OK from the owner.');
    if (!runCheck(items, rules)) {
      process.exitCode = 1;
      console.error('[push] aborted: fix the check errors first.');
      return;
    }
    return runPush(items, opts);
  }
  if (opts.command === 'diff') return runDiff(items, opts);
  if (opts.command === 'verify') {
    if (!(await runVerify(items, opts))) process.exitCode = 1;
  }
}

main().catch((e) => {
  console.error(`[asc-metadata] ERROR: ${e instanceof Error ? e.message : String(e)}`);
  process.exitCode = 1;
});
