from __future__ import annotations

import base64
import re
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


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
    if not match:
        return (100.0, 100.0)
    parts = [float(part) for part in match.group(1).replace(",", " ").split()]
    if len(parts) != 4:
        return (100.0, 100.0)
    return (parts[2], parts[3])


def _logo_mime_type(logo_bytes: bytes) -> str:
    if logo_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if logo_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if logo_bytes.startswith(b"RIFF") and logo_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def embed_logo_in_svg(
    svg_text: str,
    logo_bytes: bytes | None,
    logo_percent: int,
    padding_px: int,
    backing_shape: str,
    background: str,
) -> str:
    if logo_bytes is None:
        return svg_text

    view_width, view_height = _svg_viewbox_size(svg_text)
    logo_size = min(view_width, view_height) * (logo_percent / 100)
    backing_size = logo_size + (padding_px * 2)
    x = (view_width - backing_size) / 2
    y = (view_height - backing_size) / 2
    radius = backing_size / 8 if backing_shape == "rounded" else 0
    encoded = base64.b64encode(logo_bytes).decode("ascii")
    mime_type = _logo_mime_type(logo_bytes)
    safe_background = escape(background)
    overlay = (
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{backing_size:.3f}" '
        f'height="{backing_size:.3f}" rx="{radius:.3f}" ry="{radius:.3f}" '
        f'fill="{safe_background}" />'
        f'<image x="{x + padding_px:.3f}" y="{y + padding_px:.3f}" '
        f'width="{logo_size:.3f}" height="{logo_size:.3f}" '
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
) -> bytes:
    return embed_logo_in_svg(
        svg_text,
        logo_bytes,
        logo_percent,
        padding_px,
        backing_shape,
        background,
    ).encode("utf-8")
