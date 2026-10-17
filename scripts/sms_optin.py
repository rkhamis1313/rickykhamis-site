"""A2P 10DLC fix for campaign rejection 30909 (CTA not verifiable).
1) Adds an optional, unchecked "Text me" checkbox to every lead form, with the
   full SMS disclosure on the checkbox, and narrows the submit line to phone/email.
2) Publishes /sms-consent/, a public page documenting every opt-in method,
   with a screenshot of the form, the verbal consent script, and opt-out/help.
Idempotent. Run from the repo root."""
import re, sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SITE = ROOT / "site"
MARK = 'name="sms_consent"'
LINKS = ' <a href="/privacy-policy/#sms">Privacy Policy</a> &middot; <a href="/terms-of-use/#sms">SMS Terms</a>.'
OLD_DISCLOSURE = ('By submitting, you agree that EPiQ Lending (Ricky Khamis and team) may contact you by phone, '
                  'email, or text message about your request. Message frequency varies. Msg &amp; data rates may '
                  'apply. Reply STOP to opt out, HELP for help. Consent is not a condition of any purchase.')
NEW_SUBMIT = 'By submitting, you agree to be contacted by phone or email about your request.'
OLD_ANALYZE = ('By sending this, you agree that EPiQ Lending (Ricky Khamis and team) may contact you by phone, '
               'email, or text message about this request. Message frequency varies. Msg &amp; data rates may apply. '
               'Reply STOP to opt out, HELP for help. Consent is not a condition of any purchase. Your information '
               'is never sold.')
NEW_ANALYZE = ('By sending this, you agree that EPiQ Lending (Ricky Khamis and team) may contact you by phone or '
               'email about this request. Your information is never sold.')

OPTIN = (
    '<label class="sms-optin" style="display:flex;gap:10px;align-items:flex-start;margin:14px 0 6px;'
    'font-size:.8rem;line-height:1.45;font-weight:400;text-transform:none;letter-spacing:0;'
    'color:inherit;cursor:pointer;text-align:left">'
    '<input type="checkbox" name="sms_consent" value="yes" '
    'style="width:auto;min-width:16px;height:16px;margin:2px 0 0;flex:0 0 auto;padding:0">'
    '<span><strong>Yes, text me (optional).</strong> I agree to receive text messages from EPiQ Lending '
    '(Ricky Khamis and team) about my inquiry, application, appointments and loan status. Message frequency '
    'varies. Msg &amp; data rates may apply. Reply STOP to opt out, HELP for help. Consent is not a condition '
    'of any purchase.' + LINKS + '</span></label>'
)


def patch_forms(html: str) -> str:
    if OLD_DISCLOSURE not in html and OLD_ANALYZE not in html:
        return html
    out, pos = [], 0
    for fm in re.finditer(r'<form\b.*?</form>', html, flags=re.S):
        out.append(html[pos:fm.start()])
        form = fm.group(0)
        if MARK not in form:
            if OLD_ANALYZE in form:
                form = form.replace('<p class="consent">' + OLD_ANALYZE + LINKS,
                                    OPTIN + '<p class="consent">' + NEW_ANALYZE, 1)
                form = form.replace(OLD_ANALYZE, NEW_ANALYZE)
            elif OLD_DISCLOSURE in form:
                cut = form.find(OLD_DISCLOSURE)
                act = form.rfind('<div class="actions">', 0, cut)
                if act == -1:
                    act = form.rfind('<p class="fine"', 0, cut)
                form = form[:act] + OPTIN + form[act:]
                form = form.replace(OLD_DISCLOSURE, NEW_SUBMIT)
        out.append(form)
        pos = fm.end()
    out.append(html[pos:])
    return "".join(out)


def patch_generator() -> bool:
    p = ROOT / "gen" / "lead_form.py"
    s = p.read_text(encoding="utf-8")
    if "sms_consent" in s:
        return False
    old_open = "        f'<div class=\"actions\"><button class=\"btn btn-primary\" type=\"submit\">{spec[\"cta\"]}</button>'\n"
    if old_open not in s or repr(OLD_DISCLOSURE) not in s:
        print("WARN: lead_form.py pattern not found; generator not patched")
        return False
    s = s.replace(old_open, "        + SMS_OPTIN +\n" + old_open, 1)
    s = s.replace(repr(OLD_DISCLOSURE), repr(NEW_SUBMIT), 1)
    s = s.replace("def render(kind: str) -> str:",
                  "# A2P 10DLC: optional, unchecked SMS opt-in. Never pre-check it or make it required.\n"
                  "SMS_OPTIN = " + repr(OPTIN) + "\n\n\ndef render(kind: str) -> str:", 1)
    p.write_text(s, encoding="utf-8")
    return True


CONSENT_BODY = (
    '<p>This page explains how people agree to receive text messages from EPiQ Lending (EVO Home Loans LLC dba '
    'EPiQ Lending, NMLS #1936984) and its loan officers, including Ricky Khamis (NMLS #173141). We text one-to-one '
    'with people about their home loan inquiry, application, documents, appointments and loan status. We never buy '
    'phone numbers or text anyone who has not agreed to it.</p>'
    '<h2>1. Website forms</h2>'
    '<p>Every lead form on rickykhamis.com has an <strong>optional, unchecked</strong> checkbox. Texts are sent only '
    'if the visitor checks it. Submitting the form without checking the box means we contact them by phone or email '
    'only. The checkbox reads:</p>'
    '<p><em>"Yes, text me (optional). I agree to receive text messages from EPiQ Lending (Ricky Khamis and team) '
    'about my inquiry, application, appointments and loan status. Message frequency varies. Msg &amp; data rates may '
    'apply. Reply STOP to opt out, HELP for help. Consent is not a condition of any purchase. Privacy Policy &middot; '
    'SMS Terms."</em></p>'
    '<p>Live example: the "How much do you qualify for?" form on our <a href="/">home page</a>. Screenshot:</p>'
    '<p><img src="/assets/images/sms-consent-form.png" alt="rickykhamis.com lead form showing the optional, unchecked '
    'text message consent checkbox and disclosure" style="max-width:100%;height:auto;border:1px solid #d7d9de;'
    'border-radius:10px"></p>'
    '<h2>2. Consumer texts us first</h2>'
    '<p>When someone texts a loan officer\'s number first, for example from our website, business card, email '
    'signature or a referral, we reply to that conversation. Our first reply includes our name and how to opt out.</p>'
    '<h2>3. Verbal consent on a call or in person</h2>'
    '<p>When a client or real estate agent partner gives a loan officer their mobile number on a call or in a meeting, '
    'the loan officer asks before texting, using this script:</p>'
    '<p><em>"Is it okay if I text you at this number about your loan? It\'s EPiQ Lending, message frequency varies, '
    'message and data rates may apply, and you can reply STOP anytime to opt out."</em></p>'
    '<p>We text only if they say yes, and the loan officer records the consent, its source and the date on the '
    'contact in our CRM.</p>'
    '<h2>Opting out and getting help</h2>'
    '<p>Reply <strong>STOP</strong> (or UNSUBSCRIBE, END, QUIT, CANCEL) at any time to stop all texts. Reply '
    '<strong>HELP</strong> for help, or call (480) 999-9842. Reply <strong>START</strong> to opt back in. Mobile '
    'numbers and opt-in consent are never sold or shared with third parties for marketing. See our '
    '<a href="/privacy-policy/#sms">Privacy Policy</a> and <a href="/terms-of-use/#sms">SMS Terms</a>.</p>'
)


def build_consent_page() -> bool:
    out = SITE / "sms-consent" / "index.html"
    tpl = (SITE / "terms-of-use" / "index.html").read_text(encoding="utf-8")
    s = tpl.replace("Terms of Use | Ricky Khamis, EPiQ Lending", "Text Message Consent | Ricky Khamis, EPiQ Lending")
    s = s.replace("Terms of use for rickykhamis.com, Ricky Khamis, EPiQ Lending.",
                  "How people agree to receive text messages from EPiQ Lending and Ricky Khamis, and how to opt out.")
    s = s.replace("https://rickykhamis.com/terms-of-use/", "https://rickykhamis.com/sms-consent/")
    s = s.replace("<a href=\"/\">Home</a> / Terms of Use</div><h1>Terms of Use</h1>",
                  "<a href=\"/\">Home</a> / Text Message Consent</div><h1>Text Message Consent</h1>")
    i = s.find('<div class="wrap prose">') + len('<div class="wrap prose">')
    j = s.find("</div></section>", i)
    if i < len('<div class="wrap prose">') or j == -1:
        print("WARN: consent page template not recognized")
        return False
    s = s[:i] + "\n" + CONSENT_BODY + "\n" + s[j:]
    out.parent.mkdir(parents=True, exist_ok=True)
    new = not out.exists() or out.read_text(encoding="utf-8") != s
    out.write_text(s, encoding="utf-8")
    sm = SITE / "sitemap.xml"
    t = sm.read_text(encoding="utf-8")
    if "/sms-consent/" not in t:
        t = t.replace("</urlset>", "<url><loc>https://rickykhamis.com/sms-consent/</loc><lastmod>2026-10-17</lastmod></url>\n</urlset>")
        sm.write_text(t, encoding="utf-8")
    return new


def link_from_terms() -> bool:
    p = SITE / "terms-of-use" / "index.html"
    s = p.read_text(encoding="utf-8")
    if "/sms-consent/" in s:
        return False
    old = 'checking the optional text box on our forms or by texting us first.</p>'
    if old not in s:
        print("WARN: terms anchor not found")
        return False
    s = s.replace(old, 'checking the optional text box on our forms, by texting us first, or by agreeing on a call. '
                       'See <a href="/sms-consent/">how we collect consent</a>.</p>', 1)
    p.write_text(s, encoding="utf-8")
    return True


changed = 0
for f in SITE.rglob("*.html"):
    s = f.read_text(encoding="utf-8")
    n = patch_forms(s)
    if n != s:
        f.write_text(n, encoding="utf-8")
        changed += 1
print("form pages patched:", changed)
print("generator:", patch_generator())
print("terms link:", link_from_terms())
print("consent page:", build_consent_page())
left = [str(f) for f in SITE.rglob("*.html") if OLD_DISCLOSURE in f.read_text(encoding="utf-8")
        or OLD_ANALYZE in f.read_text(encoding="utf-8")]
print("old disclosure remaining:", left)
