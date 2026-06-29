from io import BytesIO
import xml.etree.ElementTree as ET

import pytest
from PIL import Image

from exporters import (
    embed_logo_in_svg,
    export_jpg,
    export_pdf,
    export_png,
    export_svg,
    export_webp,
)
from qr_generator import create_qr, qr_to_svg_text


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


def make_webp_logo_bytes():
    logo = Image.new("RGBA", (32, 32), "#ff0000")
    buffer = BytesIO()
    logo.save(buffer, format="WEBP", lossless=True, quality=100)
    return buffer.getvalue()


def parse_overlay_geometry(svg_text):
    root = ET.fromstring(svg_text)
    rect = next(element for element in root.iter() if element.tag.endswith("rect"))
    image = next(element for element in root.iter() if element.tag.endswith("image"))
    return rect.attrib, image.attrib


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
    assert export_svg(svg, None, 20, 8, "square", "#ffffff", 1024) == svg.encode("utf-8")


def test_embed_logo_in_svg_adds_base64_image_and_backing():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = embed_logo_in_svg(svg, make_logo_bytes(), 20, 4, "rounded", "#ffffff", 1024)
    assert "data:image/png;base64," in result
    assert "<image" in result
    assert "<rect" in result


def test_embed_logo_in_svg_uses_jpeg_mime_for_jpeg_bytes():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = embed_logo_in_svg(svg, make_jpeg_logo_bytes(), 20, 4, "rounded", "#ffffff", 1024)
    assert "data:image/jpeg;base64," in result


def test_embed_logo_in_svg_uses_webp_mime_for_webp_bytes():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = embed_logo_in_svg(svg, make_webp_logo_bytes(), 20, 4, "rounded", "#ffffff", 1024)
    assert "data:image/webp;base64," in result


def test_embed_logo_in_svg_scales_padding_using_default_output_size_ratio():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = embed_logo_in_svg(svg, make_logo_bytes(), 20, 12, "rounded", "#ffffff", 1024)

    rect, image = parse_overlay_geometry(result)

    assert float(rect["x"]) == 38.828
    assert float(rect["y"]) == 38.828
    assert float(rect["width"]) == 22.344
    assert float(rect["height"]) == 22.344
    assert float(image["x"]) == 40.0
    assert float(image["y"]) == 40.0
    assert float(image["width"]) == 20.0
    assert float(image["height"]) == 20.0


def test_embed_logo_in_svg_scales_padding_using_non_default_output_size_ratio():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = embed_logo_in_svg(svg, make_logo_bytes(), 20, 12, "rounded", "#ffffff", 512)

    rect, image = parse_overlay_geometry(result)

    assert float(rect["x"]) == 37.656
    assert float(rect["y"]) == 37.656
    assert float(rect["width"]) == 24.688
    assert float(rect["height"]) == 24.688
    assert float(image["x"]) == 40.0
    assert float(image["y"]) == 40.0
    assert float(image["width"]) == 20.0
    assert float(image["height"]) == 20.0


def test_export_svg_embeds_logo_via_public_api():
    svg = '<svg viewBox="0 0 100 100"><path d="M0 0h10v10z" /></svg>'
    result = export_svg(svg, make_jpeg_logo_bytes(), 20, 4, "rounded", "#ffffff", 1024)
    text = result.decode("utf-8")
    assert "<image" in text
    assert "data:image/jpeg;base64," in text


def test_embed_logo_in_real_segno_svg_without_viewbox_uses_width_height_viewport():
    svg = qr_to_svg_text(create_qr("https://example.com"), "#000000", "#ffffff")
    result = embed_logo_in_svg(svg, make_logo_bytes(), 20, 12, "rounded", "#ffffff", 1024)

    root = ET.fromstring(result)
    rect, image = parse_overlay_geometry(result)
    viewport_width = float(root.attrib["width"])
    viewport_height = float(root.attrib["height"])

    rect_x = float(rect["x"])
    rect_y = float(rect["y"])
    rect_width = float(rect["width"])
    rect_height = float(rect["height"])
    image_x = float(image["x"])
    image_y = float(image["y"])
    image_width = float(image["width"])
    image_height = float(image["height"])

    assert rect_x >= 0
    assert rect_y >= 0
    assert rect_x + rect_width <= viewport_width
    assert rect_y + rect_height <= viewport_height
    assert image_x >= 0
    assert image_y >= 0
    assert image_x + image_width <= viewport_width
    assert image_y + image_height <= viewport_height
    assert rect_x + (rect_width / 2) == pytest.approx(viewport_width / 2, abs=0.001)
    assert rect_y + (rect_height / 2) == pytest.approx(viewport_height / 2, abs=0.001)
    assert image_x + (image_width / 2) == pytest.approx(viewport_width / 2, abs=0.001)
    assert image_y + (image_height / 2) == pytest.approx(viewport_height / 2, abs=0.001)
