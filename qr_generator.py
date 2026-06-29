from io import BytesIO

import segno
from PIL import Image


def create_qr(
    url: str, foreground: str = "#000000", background: str = "#ffffff"
) -> segno.QRCode:
    return segno.make(url, error="h")


def qr_to_png_image(
    qr: segno.QRCode, size_px: int, foreground: str, background: str
) -> Image.Image:
    buffer = BytesIO()
    qr.save(
        buffer,
        kind="png",
        scale=10,
        border=4,
        dark=foreground,
        light=background,
    )
    buffer.seek(0)
    image = Image.open(buffer).convert("RGB")
    resampling = getattr(Image.Resampling, "NEAREST", Image.NEAREST)
    return image.resize((size_px, size_px), resampling)


def qr_to_svg_text(qr: segno.QRCode, foreground: str, background: str) -> str:
    buffer = BytesIO()
    qr.save(
        buffer,
        kind="svg",
        xmldecl=True,
        svgns=True,
        border=4,
        dark=foreground,
        light=background,
    )
    return buffer.getvalue().decode("utf-8")
