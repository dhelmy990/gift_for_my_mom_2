from io import BytesIO

from PIL import Image, ImageDraw, UnidentifiedImageError


def load_uploaded_image(data: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Uploaded file is not a valid image.") from exc
    return image.convert("RGBA")


def embed_center_image(
    qr_image: Image.Image,
    logo_image: Image.Image | None,
    logo_percent: int,
    padding_px: int,
    backing_shape: str,
    background: str,
) -> Image.Image:
    result = qr_image.convert("RGBA").copy()
    if logo_image is None:
        return result

    qr_width, qr_height = result.size
    logo_size = max(1, int(qr_width * (logo_percent / 100)))
    resampling = getattr(Image.Resampling, "LANCZOS", Image.LANCZOS)
    logo = logo_image.convert("RGBA").resize((logo_size, logo_size), resampling)

    backing_size = logo_size + (padding_px * 2)
    backing = Image.new("RGBA", (backing_size, backing_size), (0, 0, 0, 0))
    mask = Image.new("L", (backing_size, backing_size), 0)
    draw = ImageDraw.Draw(mask)
    if backing_shape == "rounded":
        radius = max(4, backing_size // 8)
        draw.rounded_rectangle((0, 0, backing_size, backing_size), radius=radius, fill=255)
    else:
        draw.rectangle((0, 0, backing_size, backing_size), fill=255)

    fill = Image.new("RGBA", (backing_size, backing_size), background)
    backing.paste(fill, (0, 0), mask)
    backing.alpha_composite(logo, (padding_px, padding_px))

    x = (qr_width - backing_size) // 2
    y = (qr_height - backing_size) // 2
    result.alpha_composite(backing, (x, y))
    return result
