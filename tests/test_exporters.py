from io import BytesIO

from PIL import Image

from exporters import (
    embed_logo_in_svg,
    export_jpg,
    export_pdf,
    export_png,
    export_svg,
    export_webp,
)


def make_image():
    return Image.new("RGBA", (256, 256), "#ffffff")


def make_logo_bytes():
    logo = Image.new("RGBA", (32, 32), "#ff0000")
    buffer = BytesIO()
    logo.save(buffer, format="PNG")
    return buffer.getvalue()


def make_jpeg_logo_bytes():
    logo = Image.new("RGB", (32, 32), "#ff0000")
    buffer = BytesIO()
    logo.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def test_export_png_returns_png_bytes():
    assert export_png(make_image()).startswith(b"\x89PNG")


def test_export_jpg_returns_jpeg_bytes():
    assert export_jpg(make_image(), "#ffffff").startswith(b"\xff\xd8")


def test_export_webp_returns_webp_bytes():
    data = export_webp(make_image())
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WEBP"


def test_export_pdf_returns_pdf_bytes():
    assert export_pdf(make_image()).startswith(b"%PDF")


def test_export_svg_without_logo_returns_original_svg_bytes():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    assert export_svg(svg, None, 20, 8, "square", "#ffffff") == svg.encode("utf-8")


def test_embed_logo_in_svg_adds_base64_image_and_backing():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = embed_logo_in_svg(svg, make_logo_bytes(), 20, 4, "rounded", "#ffffff")
    assert "data:image/png;base64," in result
    assert "<image" in result
    assert "<rect" in result


def test_embed_logo_in_svg_uses_jpeg_mime_for_jpeg_bytes():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = embed_logo_in_svg(svg, make_jpeg_logo_bytes(), 20, 4, "rounded", "#ffffff")
    assert "data:image/jpeg;base64," in result


def test_export_svg_embeds_logo_via_public_api():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = export_svg(svg, make_jpeg_logo_bytes(), 20, 4, "rounded", "#ffffff")
    text = result.decode("utf-8")
    assert "<image" in text
    assert "data:image/jpeg;base64," in text
