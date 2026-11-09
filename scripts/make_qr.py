"""Branded QR codes: Deep Blue modules on Warm Cream, the Bobcat logo in the centre. Run from the repo root:

    pip install -r scripts/requirements-images.txt
    python scripts/make_qr.py

Writes assets/qr/*.png and *.svg. If a link below changes, run this again and commit the new images.
The tests (tests/test_qr.py) decode every code back to its link with two different QR readers.
"""
import base64
import io
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_H

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "qr"
LOGO = ROOT / "assets" / "images" / "logo.png"
DEEP, CREAM, GOLD = "#102F63", "#FFF8E8", "#F4BD32"
LOGO_FRACTION = 0.25  # logo plate width as a share of the QR picture. Measured: scans reliably up to 0.28; fails from 0.30.

TARGETS = {
    "donate": "https://checkout.square.site/merchant/0MNPCQNT3X8SY/checkout/4CAB3DWDBRKVCWMJCWN2YBP5?src=webqr",
    "join": "https://jointotem.com/ca/vista/monte-vista-pta",   # plain link: Totem is not known to handle extra tracking text
    "volunteer": "https://www.montevistapta.org/get-involved/#volunteer",   # the NEW address: not live until the domain moves to the new site
    "spirit-wear": "https://spirithero.com/collections/monte-vista-swag-store-2025-26",
    "facebook": "https://www.facebook.com/MonteVistaElementary/",
    "instagram": "https://www.instagram.com/montevista_elem/",
}


def _logo_image(size, logo_path):
    """Return an RGBA square of `size` px: the real logo, or a gold 'MV' placeholder."""
    if logo_path and Path(logo_path).exists():
        return Image.open(logo_path).convert("RGBA").resize((size, size))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, size - 1, size - 1), fill=GOLD)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(size * 0.42))
    except OSError:
        font = ImageFont.load_default()
    d.text((size / 2, size / 2), "MV", fill=DEEP, font=font, anchor="mm")
    return img


def render(url, logo_path=LOGO, fraction=None, background=CREAM, module_px=20):
    """Draw the QR as a PIL image (module_px pixels per module). Returns (image, matrix).

    The logo sits on a rounded plate in the middle; `fraction` is the plate's width as a share of the whole picture.
    """
    fraction = LOGO_FRACTION if fraction is None else fraction
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, border=4, box_size=1)
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    n = len(matrix)
    size = n * module_px
    img = Image.new("RGB", (size, size), background)
    d = ImageDraw.Draw(img)
    for y, row in enumerate(matrix):
        for x, on in enumerate(row):
            if on:
                d.rectangle((x * module_px, y * module_px, (x + 1) * module_px - 1, (y + 1) * module_px - 1), fill=DEEP)
    plate = int(size * fraction)
    pad = int(plate * 0.12)
    pos = (size - plate) // 2
    d.rounded_rectangle((pos - pad, pos - pad, pos + plate + pad, pos + plate + pad), radius=pad * 2, fill=background)
    logo = _logo_image(plate, logo_path)
    img.paste(logo, (pos, pos), logo)
    return img, matrix


def make_qr(url, out_stem, logo_path=LOGO, fraction=None):
    out_stem = Path(out_stem)
    fraction = LOGO_FRACTION if fraction is None else fraction
    img, matrix = render(url, logo_path, fraction)
    img.save(out_stem.with_suffix(".png"))
    n = len(matrix)

    # SVG: vector modules; the centre plate carries the logo as an embedded PNG
    cells = "".join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for y, r in enumerate(matrix) for x, on in enumerate(r) if on)
    p, pp = n * fraction, n * fraction * 0.12
    c = (n - p) / 2
    buf = io.BytesIO()
    _logo_image(256, logo_path).save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    out_stem.with_suffix(".svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
        f'<rect width="{n}" height="{n}" fill="{CREAM}"/><g fill="{DEEP}">{cells}</g>'
        f'<rect x="{c - pp}" y="{c - pp}" width="{p + 2 * pp}" height="{p + 2 * pp}" rx="{pp * 2}" fill="{CREAM}"/>'
        f'<image x="{c}" y="{c}" width="{p}" height="{p}" href="data:image/png;base64,{b64}"/></svg>')


def make_all(logo_path=LOGO):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, url in TARGETS.items():
        make_qr(url, OUT / name, logo_path)


if __name__ == "__main__":
    make_all()
    print("wrote", ", ".join(TARGETS))
