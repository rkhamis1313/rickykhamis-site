#!/usr/bin/env python3
"""Build the downloadable contact card and its QR code from content/author.json.

Generated rather than hand-written so the phone number, title and NMLS live in
exactly one place. Change author.json and the card, the QR and every post's
About block all move together. A contact card that disagrees with the site is
worse than no contact card.

Outputs:
    site/assets/ricky-khamis.vcf                  vCard 3.0, widest support
    site/assets/images/contact-qr.png             QR pointing at the .vcf
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTHOR = ROOT / "content" / "author.json"
VCF = ROOT / "site" / "assets" / "ricky-khamis.vcf"
QR = ROOT / "site" / "assets" / "images" / "contact-qr.png"
PHOTO = ROOT / "site" / "assets" / "images" / "ricky-closeup.jpg"
SITE = "https://rickykhamis.com"
VCF_URL = f"{SITE}/assets/ricky-khamis.vcf"


def esc(v: str) -> str:
    """vCard escaping. Commas and semicolons are field separators."""
    return v.replace("\\", "\\\\").replace(";", "\;").replace(",", "\\,")


def build_vcard(a: dict, blinq_url: str | None = None) -> str:
    # "7975 N. Hayden Road, Suite A-101, Scottsdale, AZ 85258"
    # Last chunk is "STATE ZIP", the one before it is the city, and everything
    # ahead of those is street plus suite.
    chunks = [c.strip() for c in a["office"].split(",")]
    state, postal = chunks[-1].split()
    city = chunks[-2]
    street = ", ".join(chunks[:-2])

    digits = "".join(c for c in a["phone"] if c.isdigit())
    tel = f"+1{digits}"

    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        "N:Khamis;Ricky;;;",
        "FN:Ricky Khamis",
        "ORG:EPiQ Lending",
        f"TITLE:{esc(a['jobTitle'])}",
        f"TEL;TYPE=WORK,VOICE:{tel}",
        "EMAIL;TYPE=WORK,INTERNET:ricky.khamis@epiqlending.com",
        f"ADR;TYPE=WORK:;;{esc(street)};{esc(city)};{state};{postal};USA",
        f"URL:{SITE}",
        f"URL;TYPE=Profile:{a['proofLinks']['profile']}",
    ]
    if blinq_url:
        lines.append(f"URL;TYPE=Card:{blinq_url}")

    # Everything that makes him findable and checkable, in the card itself.
    note = (
        f"NMLS #{a['nmls']}. EPiQ Lending NMLS #{a['companyNmls']}. "
        f"Lending in Arizona since {a['lendingSince']}. "
        f"Licensed in {', '.join(a['licensedIn'])}. "
        + (f"{a['awards'][0]}. " if a.get("awards") else "")
        + " ".join(a.get("credentials", []))
        + " Verify at nmlsconsumeraccess.org."
    )
    lines.append(f"NOTE:{esc(note)}")

    if PHOTO.exists():
        # Downscale before embedding. A full resolution headshot produces a
        # six figure byte count, and some phone contact apps quietly reject or
        # truncate an oversized vCard rather than telling anyone.
        import io

        from PIL import Image

        im = Image.open(PHOTO).convert("RGB")
        im.thumbnail((400, 400))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        lines.append(f"PHOTO;ENCODING=b;TYPE=JPEG:{b64}")

    lines.append("END:VCARD")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


def fold(line: str, limit: int = 74) -> str:
    """Fold long lines per RFC 2426. Continuations start with a single space.

    Not cosmetic: some contact importers truncate or reject a vCard with
    overlong physical lines, and it fails silently on the phone rather than
    at build time.
    """
    if len(line) <= limit or line.startswith(" "):
        return line
    out, rest = [line[:limit]], line[limit:]
    while rest:
        out.append(" " + rest[:limit - 1])
        rest = rest[limit - 1:]
    return "\r\n".join(out)


def build_qr(target: str) -> None:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M

    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M,
                       box_size=10, border=2)
    qr.add_data(target)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1b1e24", back_color="white")
    QR.parent.mkdir(parents=True, exist_ok=True)
    img.save(QR)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blinq", help="Blinq card URL, added to the vCard and QR")
    ap.add_argument("--qr-target", default=VCF_URL,
                    help="what the QR encodes; defaults to the vCard URL")
    a = ap.parse_args()

    author = json.loads(AUTHOR.read_text(encoding="utf-8"))
    VCF.parent.mkdir(parents=True, exist_ok=True)
    VCF.write_text(build_vcard(author, a.blinq), encoding="utf-8")
    print(f"  + {VCF.relative_to(ROOT)}  ({VCF.stat().st_size / 1024:.0f} KB)")

    build_qr(a.qr_target)
    print(f"  + {QR.relative_to(ROOT)}  ({QR.stat().st_size / 1024:.0f} KB)")
    print(f"    QR encodes: {a.qr_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
