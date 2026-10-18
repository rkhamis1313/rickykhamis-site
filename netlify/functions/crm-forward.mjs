// Forwards a Netlify Forms submission into the CRM.
//
// WHY A FUNCTION AND NOT A DIRECT POST FROM THE PAGE
// rickykhamis.com is a static mirror with no server, so the obvious shortcut
// is to have the browser POST straight to the CRM. That would put the CRM API
// key in client-side JavaScript on a public site, where anyone can read it and
// write to the CRM as Ricky. The key lives here instead, in a Netlify
// environment variable, and never reaches the browser.
//
// WHY IT HANGS OFF NETLIFY FORMS RATHER THAN REPLACING THEM
// The forms already post to Netlify with spam filtering and a stored record.
// Keeping that and adding this as an outgoing notification means a lead is
// captured even when the CRM call fails. A lost lead is real money, so the
// durable record stays and the CRM push is the thing allowed to fail.
//
// SETUP, ONE TIME
//  1. Netlify dashboard, Site configuration, Environment variables:
//       CRM_WEBHOOK_URL   the endpoint the CRM gave you
//       CRM_API_KEY       the key, if it needs one
//       CRM_AUTH_STYLE    optional: "bearer" (default), "x-api-key", or "query"
//  2. Forms, Form notifications, Add notification, Outgoing webhook:
//       URL      https://rickykhamis.com/.netlify/functions/crm-forward
//       Form     all forms, or pick them individually
//
// Netlify posts a JSON envelope; the submitted fields are under `data`.

// Keys taken from a rendered form on the live site, not guessed. The real
// fields use underscores and carry mortgage-specific values an earlier,
// generic map would have silently dropped. Each entry lists aliases so a
// future form variant still maps.
const FIELD_MAP = {
  firstName: ['first_name', 'first-name', 'firstname'],
  lastName: ['last_name', 'last-name', 'lastname'],
  name: ['name', 'full_name', 'full-name', 'fullname'],
  email: ['email', 'e-mail'],
  phone: ['phone', 'tel', 'telephone', 'mobile'],
  loanPurpose: ['purchase', 'purpose', 'loan_purpose', 'loan-purpose', 'intent'],
  buyerStage: ['stage'],
  priceRange: ['price'],
  downPayment: ['down'],
  creditBand: ['credit'],
  message: ['message', 'comments', 'notes', 'question'],
  propertyCity: ['city', 'property_city', 'property-city'],
  smsConsent: ['sms_consent', 'sms-consent', 'sms_optin', 'sms'],
};

function pick(data, keys) {
  for (const k of keys) {
    const v = data?.[k];
    if (typeof v === 'string' && v.trim()) return v.trim();
  }
  return '';
}

export default async (request) => {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  const url = process.env.CRM_WEBHOOK_URL;
  if (!url) {
    // Loud but non-fatal: the lead is already stored in Netlify Forms, so a
    // missing configuration must not look like a successful delivery.
    console.error('crm-forward: CRM_WEBHOOK_URL is not set; nothing forwarded');
    return new Response('CRM not configured', { status: 503 });
  }

  let envelope;
  try {
    envelope = await request.json();
  } catch {
    return new Response('Bad request', { status: 400 });
  }

  const data = envelope?.payload?.data ?? envelope?.data ?? envelope ?? {};
  const formName = envelope?.payload?.form_name ?? envelope?.form_name ?? 'unknown';

  // A honeypot value means a bot filled the hidden field. Drop it silently
  // rather than polluting the CRM.
  if ((data['company-website'] ?? '').trim()) {
    console.log('crm-forward: honeypot tripped, dropped');
    return new Response('OK', { status: 200 });
  }

  const lead = {};
  for (const [out, keys] of Object.entries(FIELD_MAP)) {
    const v = pick(data, keys);
    if (v) lead[out] = v;
  }
  if (!lead.name && (lead.firstName || lead.lastName)) {
    lead.name = [lead.firstName, lead.lastName].filter(Boolean).join(' ');
  }
  if (!lead.email && !lead.phone) {
    console.error('crm-forward: no email or phone in submission; not forwarded');
    return new Response('Nothing to forward', { status: 422 });
  }

  lead.source = 'rickykhamis.com';
  lead.sourceForm = formName;
  lead.submittedAt = new Date().toISOString();
  if (data['page-url']) lead.pageUrl = data['page-url'];

  const style = (process.env.CRM_AUTH_STYLE || 'bearer').toLowerCase();
  const key = process.env.CRM_API_KEY || '';
  const headers = { 'content-type': 'application/json' };
  let target = url;
  if (key) {
    if (style === 'x-api-key') headers['x-api-key'] = key;
    else if (style === 'query') {
      const u = new URL(url);
      u.searchParams.set('api_key', key);
      target = u.toString();
    } else headers.authorization = `Bearer ${key}`;
  }

  // One retry on a transient failure, then give up. Netlify still holds the
  // submission, so giving up loses the automation and not the lead.
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      const res = await fetch(target, {
        method: 'POST',
        headers,
        body: JSON.stringify(lead),
        signal: AbortSignal.timeout(10_000),
      });
      if (res.ok) {
        console.log(`crm-forward: delivered ${formName} (${res.status})`);
        return new Response('OK', { status: 200 });
      }
      // 4xx is our problem and will not fix itself on a retry.
      const body = (await res.text()).slice(0, 400);
      console.error(`crm-forward: CRM returned ${res.status}: ${body}`);
      if (res.status < 500) return new Response('CRM rejected', { status: 502 });
    } catch (err) {
      console.error(`crm-forward: attempt ${attempt} failed: ${err?.message}`);
    }
    if (attempt === 1) await new Promise((r) => setTimeout(r, 1200));
  }
  return new Response('CRM unreachable', { status: 502 });
};
