from __future__ import annotations

import base64
import re
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def _svg_length_value(svg_text: str, attribute: str) -> float | None:
    match = re.search(rf"""{attribute}=["']([^"']+)["']""", svg_text)
    if not match:
        return None
    number_match = re.match(r"""[-+]?(?:\d+(?:\.\d*)?|\.\d+)""", match.group(1).strip())
    if not number_match:
        return None
    return float(number_match.group(0))


def _flatten_to_rgb(image: Image.Image, background: str) -> Image.Image:
    base = Image.new("RGBA", image.size, background)
    base.alpha_composite(image.convert("RGBA"))
    return base.convert("RGB")


def export_png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def export_jpg(image: Image.Image, background: str) -> bytes:
    buffer = BytesIO()
    _flatten_to_rgb(image, background).save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def export_webp(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="WEBP", lossless=True, quality=100)
    return buffer.getvalue()


def export_pdf(image: Image.Image) -> bytes:
    pdf_buffer = BytesIO()
    rgb_image = _flatten_to_rgb(image, "#ffffff")
    pdf = canvas.Canvas(pdf_buffer, pagesize=rgb_image.size)
    pdf.drawImage(ImageReader(rgb_image), 0, 0, width=rgb_image.width, height=rgb_image.height)
    pdf.showPage()
    pdf.save()
    return pdf_buffer.getvalue()


def _svg_viewbox_size(svg_text: str) -> tuple[float, float]:
    match = re.search(r"""viewBox=["']([^"']+)["']""", svg_text)
    if match:
        parts = [float(part) for part in match.group(1).replace(",", " ").split()]
        if len(parts) == 4:
            return (parts[2], parts[3])

    width = _svg_length_value(svg_text, "width")
    height = _svg_length_value(svg_text, "height")
    if width is not None and height is not None:
        return (width, height)

    return (100.0, 100.0)


def _logo_mime_type(logo_bytes: bytes) -> str:
    if logo_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if logo_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if logo_bytes.startswith(b"RIFF") and logo_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _logo_aspect_ratio(logo_bytes: bytes) -> tuple[float, float]:
    with Image.open(BytesIO(logo_bytes)) as image:
        return (float(image.width), float(image.height))


def embed_logo_in_svg(
    svg_text: str,
    logo_bytes: bytes | None,
    logo_percent: int,
    padding_px: int,
    backing_shape: str,
    background: str,
    size_px: int,
) -> str:
    if logo_bytes is None:
        return svg_text

    view_width, view_height = _svg_viewbox_size(svg_text)
    logo_max_size = min(view_width, view_height) * (logo_percent / 100)
    source_width, source_height = _logo_aspect_ratio(logo_bytes)
    if source_width >= source_height:
        logo_width = logo_max_size
        logo_height = logo_max_size * (source_height / source_width)
    else:
        logo_height = logo_max_size
        logo_width = logo_max_size * (source_width / source_height)
    padding_units = min(view_width, view_height) * (padding_px / max(size_px, 1))
    backing_width = logo_width + (padding_units * 2)
    backing_height = logo_height + (padding_units * 2)
    x = (view_width - backing_width) / 2
    y = (view_height - backing_height) / 2
    radius = min(backing_width, backing_height) / 8 if backing_shape == "rounded" else 0
    encoded = base64.b64encode(logo_bytes).decode("ascii")
    mime_type = _logo_mime_type(logo_bytes)
    safe_background = escape(background)
    overlay = (
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{backing_width:.3f}" '
        f'height="{backing_height:.3f}" rx="{radius:.3f}" ry="{radius:.3f}" '
        f'fill="{safe_background}" />'
        f'<image x="{x + padding_units:.3f}" y="{y + padding_units:.3f}" '
        f'width="{logo_width:.3f}" height="{logo_height:.3f}" '
        f'href="data:{mime_type};base64,{encoded}" />'
    )
    if "</svg>" in svg_text:
        return svg_text.replace("</svg>", f"{overlay}</svg>", 1)
    return f"{svg_text}{overlay}"


def export_svg(
    svg_text: str,
    logo_bytes: bytes | None,
    logo_percent: int,
    padding_px: int,
    backing_shape: str,
    background: str,
    size_px: int,
) -> bytes:
    return embed_logo_in_svg(
        svg_text,
        logo_bytes,
        logo_percent,
        padding_px,
        backing_shape,
        background,
        size_px,
    ).encode("utf-8")
