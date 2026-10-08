#!/usr/bin/env python3
"""The in-post lead form.

Why this exists: a post that ranks for "physician home loan" and then offers
nothing but a phone number converts the small share of readers willing to call
a stranger. The rest leave. This puts a short, product-specific form inside the
article, where the reader already is, at the moment they have just read the
answer to their question.

Deliberately short. Every field past the fourth costs conversions, so each form
asks only what actually changes the answer for that product: a physician's
designation and contract status, a self-employed borrower's business type, an
investor's property and rent. Everything else is a conversation.

Posts opt in from front matter:

    form: physician

and the renderer drops the matching block in before the closing section. A post
with no `form` key renders exactly as it did before.

Submissions go to Netlify Forms the same way every other form on the site does:
a POST to /thank-you/, a hidden form-name, a .hp honeypot, and the
data-netlify attributes that make Netlify register the form at deploy. That
attribute is easy to lose, because Netlify strips it from served HTML and the
mirror captures what is served. If leads stop arriving, check that first.
"""

from __future__ import annotations

# Netlify needs a stable form name per form. Keep these unchanged once live, or
# submissions land under a new name in the dashboard and the old one looks dead.
FORMS: dict[str, dict] = {
    "physician": {
        "name": "physician-loan",
        "heading": "Find out what you qualify for before you start looking",
        "blurb": (
            "Tell me where you are in training or practice and I will tell you which structure "
            "fits your file, what it needs, and what it does not. No credit pull to have the "
            "conversation."
        ),
        "cta": "Check my eligibility",
        "fields": [
            ("designation", "Your designation", "select",
             ["MD", "DO", "DDS or DMD", "PharmD", "DVM or VMD", "DPM", "CRNA", "NP", "Other"]),
            ("stage", "Where you are", "select",
             ["Resident", "Fellow", "Attending, first year", "Attending, established", "Still in school"]),
            ("contract", "Employment contract", "select",
             ["Signed and executed", "Offer received, not signed", "Still interviewing", "Already employed"]),
            ("timeline", "When you want to buy", "select",
             ["Under contract now", "Next 90 days", "3 to 6 months", "6 to 12 months", "Just researching"]),
        ],
    },
    "self-employed": {
        "name": "self-employed-loan",
        "heading": "Find out which documentation option qualifies you for the most",
        "blurb": (
            "Bank statements, a third-party P&L and full documentation routinely produce very "
            "different qualifying income from the same business. Tell me the shape of yours and "
            "I will run all three."
        ),
        "cta": "Run my numbers",
        "fields": [
            ("business_type", "Your business", "select",
             ["Service business", "Product or goods business", "Both", "Not sure"]),
            ("employees", "Employees", "select", ["None, just me", "1 to 5", "More than 5"]),
            ("ownership", "Your ownership", "select",
             ["100%", "50% or more", "25% to 49%", "Under 25%"]),
            ("timeline", "When you want to buy", "select",
             ["Under contract now", "Next 90 days", "3 to 6 months", "6 to 12 months", "Just researching"]),
        ],
    },
    "investor": {
        "name": "investor-dscr",
        "heading": "Run the coverage ratio before you write the offer",
        "blurb": (
            "DSCR files are decided by the rent against the payment. Send the address and the "
            "rent and I will tell you where the ratio lands before you are committed."
        ),
        "cta": "Check the ratio",
        "fields": [
            ("property", "Property address or area", "text", None),
            ("rent_type", "Rental type", "select",
             ["Long-term lease", "Short-term rental", "Currently vacant", "Not purchased yet"]),
            ("monthly_rent", "Monthly rent, actual or expected", "text", None),
            ("timeline", "When you want to close", "select",
             ["Under contract now", "Next 90 days", "3 to 6 months", "Just researching"]),
        ],
    },
    "zero-down": {
        "name": "zero-down",
        "heading": "Find out whether you can buy without a down payment",
        "blurb": (
            "Zero down works when the closing costs have a plan too. Tell me what you have "
            "saved and what you earn, and I will tell you whether this structure beats waiting."
        ),
        "cta": "See if I qualify",
        "fields": [
            ("veteran", "Military service", "select",
             ["Not a veteran", "Veteran", "Active duty", "Surviving spouse"]),
            ("saved", "Saved for the purchase", "select",
             ["Nothing yet", "Under $5,000", "$5,000 to $15,000", "More than $15,000"]),
            ("credit", "Credit, roughly", "select",
             ["720 or better", "660 to 719", "600 to 659", "Under 600", "Not sure"]),
            ("timeline", "When you want to buy", "select",
             ["Next 90 days", "3 to 6 months", "6 to 12 months", "Just researching"]),
        ],
    },
    # These two reuse Netlify form names that already exist on the site
    # (registered 3 September), so the program pages do not create new forms
    # the owner has to configure notifications for all over again. The field
    # names are drawn from those forms' existing field sets for the same
    # reason: submissions land in the columns the dashboard already knows.
    "purchase": {
        "name": "purchase",
        "heading": "Find out which program actually costs you less",
        "blurb": (
            "FHA, conventional and jumbo price the same borrower very differently once the "
            "mortgage insurance is compared across the years you will own the home. Tell me the "
            "shape of your file and I will run them side by side."
        ),
        "cta": "Compare my options",
        "fields": [
            ("stage", "Where you are", "select",
             ["Under contract now", "Making offers", "Starting to look", "Just getting organized"]),
            ("price", "Price range", "select",
             ["Under $400,000", "$400,000 to $600,000", "$600,000 to $832,750",
              "$832,750 to $1,200,000", "Over $1,200,000"]),
            ("down", "Down payment you have in mind", "select",
             ["Nothing yet", "3% to 3.5%", "5% to 9%", "10% to 19%", "20% or more"]),
            ("credit", "Credit, roughly", "select",
             ["760 or better", "700 to 759", "640 to 699", "580 to 639", "Under 580", "Not sure"]),
        ],
    },
    "refinance": {
        "name": "refinance",
        "heading": "Find out what your blended rate actually is",
        "blurb": (
            "A refinance is shopped against the mortgage rate and decided by the blended rate "
            "across everything you owe. Tell me what is on the house and what you want gone, and "
            "I will run both."
        ),
        "cta": "Run my blended rate",
        "fields": [
            ("goal", "What you want", "select",
             ["Cash out for debt or a project", "A lower rate", "A shorter term",
              "Remove mortgage insurance", "Not sure yet"]),
            ("balance", "Balance on the first mortgage", "select",
             ["Under $250,000", "$250,000 to $450,000", "$450,000 to $832,750",
              "Over $832,750", "Owned free and clear"]),
            ("value", "What the home is worth, roughly", "select",
             ["Under $400,000", "$400,000 to $600,000", "$600,000 to $1,000,000",
              "Over $1,000,000", "Not sure"]),
            ("credit", "Credit, roughly", "select",
             ["760 or better", "700 to 759", "640 to 699", "Under 640", "Not sure"]),
        ],
    },
    "aio": {
        "name": "qualify",
        "heading": "Find out whether your cash flow is big enough to make this work",
        "blurb": (
            "The All In One wins or loses on how much cash sits in the account and how long it "
            "sits there, not on the rate. Tell me the shape of your month and I will run it "
            "against a fixed loan with the difference paid as extra principal."
        ),
        "cta": "Test it on my numbers",
        "fields": [
            ("loan_type", "Purchase or refinance", "select",
             ["Refinance my current mortgage", "Buying a home", "Either, show me both"]),
            ("loan_amount", "Mortgage amount, roughly", "select",
             ["Under $300,000", "$300,000 to $500,000", "$500,000 to $832,750",
              "Over $832,750"]),
            ("monthly_float", "Cash that typically sits in your checking account", "select",
             ["Under $5,000", "$5,000 to $20,000", "$20,000 to $50,000", "More than $50,000",
              "It swings a lot"]),
            ("credit", "Credit, roughly", "select",
             ["760 or better", "700 to 759", "640 to 699", "Under 640", "Not sure"]),
        ],
    },
}


def _field(form_name: str, key: str, label: str, kind: str, options) -> str:
    fid = f"{form_name}-{key}"
    if kind == "select":
        opts = "".join(f'<option value="{o}">{o}</option>' for o in options)
        control = f'<select id="{fid}" name="{key}" required><option value="">Select…</option>{opts}</select>'
    else:
        control = f'<input id="{fid}" type="text" name="{key}" required placeholder="">'
    return f'<div><label for="{fid}">{label}</label>{control}</div>'


def render(kind: str) -> str:
    """Return the form block for a front matter `form:` value, or '' if unknown."""
    spec = FORMS.get((kind or "").strip().lower())
    if not spec:
        return ""
    n = spec["name"]
    fields = "".join(_field(n, *f) for f in spec["fields"])
    return (
        f'<section class="leadform" id="apply">'
        f'<div class="form">'
        f'<h3>{spec["heading"]}</h3>'
        f'<p class="sub">{spec["blurb"]}</p>'
        f"<form action=\"/thank-you/\" class=\"form-inner\" method=\"POST\" name=\"{n}\" "
        f'data-netlify="true" data-netlify-honeypot="company-website">'
        f'<input type="hidden" name="form-name" value="{n}">'
        f'<p class="hp"><label>Leave this empty: <input name="company-website"></label></p>'
        f'<div class="fg">{fields}'
        f'<div><label for="{n}-first_name">First name</label>'
        f'<input id="{n}-first_name" type="text" name="first_name" required placeholder=""></div>'
        f'<div><label for="{n}-last_name">Last name</label>'
        f'<input id="{n}-last_name" type="text" name="last_name" required placeholder=""></div>'
        f'<div><label for="{n}-email">Email</label>'
        f'<input id="{n}-email" type="email" name="email" required placeholder=""></div>'
        f'<div><label for="{n}-phone">Phone</label>'
        f'<input id="{n}-phone" type="tel" name="phone" required placeholder=""></div>'
        f'</div>'
        f'<div class="actions"><button class="btn btn-primary" type="submit">{spec["cta"]}</button>'
        f'<p class="fine">By submitting, you agree to be contacted by phone, email, or text about '
        f'your request. No spam, no obligation. This is not a loan application and no credit is '
        f'pulled. Equal Housing Opportunity.</p></div>'
        f'</form></div></section>'
    )
