from io import BytesIO
import xml.etree.ElementTree as ET

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
