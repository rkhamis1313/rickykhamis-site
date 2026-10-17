"""One-time A2P 10DLC compliance patch for rickykhamis.com.
Puts the full texting disclosure (brand, frequency, rates, STOP/HELP, links) on
every lead form consent line, and adds SMS sections to the Privacy Policy
and Terms of Use. Idempotent: safe to run twice. Run from the repo root."""
import re, sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SITE = ROOT / "site"

LINKS = ' <a href="/privacy-policy/#sms">Privacy Policy</a> &middot; <a href="/terms-of-use/#sms">SMS Terms</a>.'
SMS_DISCLOSURE = ('By submitting, you agree that EPiQ Lending (Ricky Khamis and team) may contact you by phone, '
                  'email, or text message about your request. Message frequency varies. Msg &amp; data rates may '
                  'apply. Reply STOP to opt out, HELP for help. Consent is not a condition of any purchase.')
MARK = 'terms-of-use/#sms'

FINE_RE = re.compile(r'By submitting, you agree to be contacted by phone, email, or text about your request\.')
FINE_NEW = SMS_DISCLOSURE
ANALYZE_OLD = ('By sending this, you agree that Ricky Khamis and EPiQ Lending may contact you by phone, '
               'text, or email about this request. Message and data rates may apply. Consent is not '
               'required to buy anything. Your information is never sold.')
ANALYZE_NEW = ('By sending this, you agree that EPiQ Lending (Ricky Khamis and team) may contact you by phone, '
               'email, or text message about this request. Message frequency varies. Msg &amp; data rates may apply. '
               'Reply STOP to opt out, HELP for help. Consent is not a condition of any purchase. Your information '
               'is never sold.' + LINKS)


def patch_forms(html: str) -> str:
    if "By submitting, you agree to be contacted" not in html and ANALYZE_OLD not in html:
        return html
    out, pos = [], 0
    for fm in re.finditer(r'<form\b.*?</form>', html, flags=re.S):
        out.append(html[pos:fm.start()])
        form = fm.group(0)
        if MARK not in form and (FINE_RE.search(form) or ANALYZE_OLD in form):
            if ANALYZE_OLD in form:
                form = form.replace(ANALYZE_OLD, ANALYZE_NEW, 1)
            else:
                m = FINE_RE.search(form)
                close = form.find('</p>', m.end())
                form = form[:close] + LINKS + form[close:]
                form = FINE_RE.sub(FINE_NEW, form, count=1)
        out.append(form)
        pos = fm.end()
    out.append(html[pos:])
    return "".join(out)


PRIVACY_SMS = (
    '<h2 id="sms">Text messaging (SMS)</h2>'
    '<p>If you opt in to text messages, we use your mobile number only to send you the messages you agreed to receive '
    'about your inquiry, application, appointments and loan status. <strong>Mobile numbers and SMS opt-in consent are never '
    'sold, rented, or shared with third parties or affiliates for their marketing or promotional purposes.</strong> Text '
    'messaging originator opt-in data and consent are excluded from all of the information sharing described above, '
    'except with service providers (such as our messaging platform and phone carriers) that deliver the messages for us.</p>'
    '<p>Message frequency varies. Msg &amp; data rates may apply. Reply STOP at any time to opt out, or HELP for help. '
    'See our <a href="/terms-of-use/#sms">SMS Terms</a>.</p>'
)

TERMS_SMS = (
    '<h2 id="sms">SMS Terms</h2>'
    '<p><strong>Program:</strong> EPiQ Lending text messaging. EVO Home Loans LLC dba EPiQ Lending (NMLS #1936984) and its '
    'loan officers, including Ricky Khamis (NMLS #173141), send conversational and informational text messages about your '
    'home loan inquiry, application, document requests, appointments and loan status to people who opt in, for example by '
    'checking the optional text box on our forms or by texting us first.</p>'
    '<ul>'
    '<li><strong>Frequency:</strong> message frequency varies based on your request and loan activity.</li>'
    '<li><strong>Cost:</strong> Msg &amp; data rates may apply.</li>'
    '<li><strong>Opt out:</strong> reply STOP (or UNSUBSCRIBE, END, QUIT, CANCEL) at any time. You will receive one '
    'message confirming you are unsubscribed, and no further texts. Reply START to opt back in.</li>'
    '<li><strong>Help:</strong> reply HELP, call (480) 999-9842, or email '
    '<a href="mailto:ricky.khamis@epiqlending.com">ricky.khamis@epiqlending.com</a>.</li>'
    '<li>Consent to receive text messages is not a condition of any purchase or loan.</li>'
    '<li>Carriers are not liable for delayed or undelivered messages.</li>'
    '<li><strong>Privacy:</strong> mobile numbers and SMS opt-in consent are never sold or shared with third parties for '
    'marketing. See our <a href="/privacy-policy/#sms">Privacy Policy</a>.</li>'
    '</ul>'
)


def add_section(path: Path, block: str) -> bool:
    s = path.read_text(encoding="utf-8")
    if 'id="sms"' in s:
        return False
    i = s.find("</main>")
    j = s.rfind("</div></section>", 0, i)
    s = s[:j] + block + s[j:]
    path.write_text(s, encoding="utf-8")
    return True


def patch_generator() -> bool:
    p = ROOT / "gen" / "lead_form.py"
    s = p.read_text(encoding="utf-8")
    if "terms-of-use/#sms" in s:
        return False
    old = ("        f'<p class=\"fine\">By submitting, you agree to be contacted by phone, email, or text about '\n"
           "        f'your request. No spam, no obligation. This is not a loan application and no credit is '\n"
           "        f'pulled. Equal Housing Opportunity.</p></div>'\n")
    if old not in s:
        print("WARN: lead_form.py pattern not found; generator not patched")
        return False
    new = ("        f'<p class=\"fine\">' + " + repr(SMS_DISCLOSURE) + " +\n"
           "        f' No spam, no obligation. This is not a loan application and no credit is '\n"
           "        f'pulled. Equal Housing Opportunity.' + " + repr(LINKS) + " + '</p></div>'\n")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    return True


changed = 0
for f in SITE.rglob("*.html"):
    s = f.read_text(encoding="utf-8")
    n = patch_forms(s)
    if n != s:
        f.write_text(n, encoding="utf-8")
        changed += 1
print("form pages patched:", changed)
print("privacy:", add_section(SITE / "privacy-policy" / "index.html", PRIVACY_SMS))
print("terms:", add_section(SITE / "terms-of-use" / "index.html", TERMS_SMS))
print("generator:", patch_generator())
left = [str(f) for f in SITE.rglob("*.html") if "or text about your request" in f.read_text(encoding="utf-8")
        or ANALYZE_OLD in f.read_text(encoding="utf-8")]
print("old consent remaining:", left)
