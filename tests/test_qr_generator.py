from io import BytesIO

from PIL import Image

from qr_generator import create_qr, qr_to_png_image, qr_to_svg_text


def test_create_qr_returns_high_error_qr():
    qr = create_qr("https://example.com")
    assert qr.error == "H"


def test_qr_to_png_image_returns_requested_size_rgb_image():
    qr = create_qr("https://example.com")
    image = qr_to_png_image(
        qr, size_px=512, foreground="#111111", background="#eeeeee"
    )
    assert image.size == (512, 512)
    assert image.mode == "RGB"

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    assert buffer.getvalue().startswith(b"\x89PNG")


def test_qr_to_svg_text_returns_svg_document():
    qr = create_qr("https://example.com")
    svg = qr_to_svg_text(qr, foreground="#000000", background="#ffffff")
    assert svg.lstrip().startswith("<?xml") or svg.lstrip().startswith("<svg")
    assert "<svg" in svg
