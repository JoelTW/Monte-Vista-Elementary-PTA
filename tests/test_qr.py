import sys
from pathlib import Path

import cv2
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_qr  # noqa: E402

DONATE = "https://checkout.square.site/merchant/0MNPCQNT3X8SY/checkout/4CAB3DWDBRKVCWMJCWN2YBP5?src=webqr"


def decode(path):
    img = cv2.imread(str(path))
    text, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    return text


@pytest.mark.parametrize("name,url", make_qr.TARGETS.items())
def test_qr_decodes_with_logo(name, url):
    make_qr.make_all()
    assert decode(ROOT / "assets/qr" / f"{name}.png") == url


def test_donate_qr_has_webqr_tag():
    assert make_qr.TARGETS["donate"] == DONATE


def test_missing_logo_falls_back(tmp_path):
    make_qr.make_qr("https://example.com/x", tmp_path / "t", logo_path=None)
    assert decode(tmp_path / "t.png") == "https://example.com/x"
    assert (tmp_path / "t.svg").exists()


def _degraded(path, size=300, jpeg_quality=35):
    from PIL import Image
    import io
    img = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=jpeg_quality)
    return Image.open(io.BytesIO(buf.getvalue()))


@pytest.mark.parametrize("name,url", make_qr.TARGETS.items())
def test_qr_still_scans_small_and_compressed_with_a_second_reader(name, url):
    """A phone sees a small, compressed, imperfect picture. Use ZXing, a different decoder from OpenCV's."""
    zxingcpp = pytest.importorskip("zxingcpp")
    make_qr.make_all()
    got = zxingcpp.read_barcodes(_degraded(ROOT / "assets/qr" / f"{name}.png"))
    assert got and got[0].text == url


def test_logo_size_is_inside_the_measured_safe_range():
    assert 0.24 <= make_qr.LOGO_FRACTION <= 0.28     # 0.30 and above stopped scanning in testing


def test_join_code_points_at_the_plain_totem_page():
    assert make_qr.TARGETS["join"] == "https://jointotem.com/ca/vista/monte-vista-pta"


def test_volunteer_code_uses_the_new_site_address_not_the_old_weebly_one():
    assert make_qr.TARGETS["volunteer"] == "https://www.montevistapta.org/get-involved/#volunteer"
    assert ".html" not in make_qr.TARGETS["volunteer"]
