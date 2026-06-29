from io import BytesIO

import pytest
from PIL import Image

from image_embedder import embed_center_image, load_uploaded_image


def make_png_bytes(color=(255, 0, 0, 255), size=(80, 80)):
    image = Image.new("RGBA", size, color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_load_uploaded_image_returns_rgba_image():
    image = load_uploaded_image(make_png_bytes())
    assert image.mode == "RGBA"
    assert image.size == (80, 80)


def test_load_uploaded_image_rejects_corrupt_bytes():
    with pytest.raises(ValueError, match="valid image"):
        load_uploaded_image(b"not-an-image")


def test_embed_center_image_returns_copy_when_logo_is_none():
    qr = Image.new("RGB", (400, 400), "#ffffff")
    result = embed_center_image(qr, None, 20, 8, "square", "#ffffff")
    assert result.size == qr.size
    assert result is not qr


def test_embed_center_image_places_logo_in_center():
    qr = Image.new("RGB", (400, 400), "#ffffff")
    logo = Image.new("RGBA", (100, 100), "#ff0000")
    result = embed_center_image(qr, logo, 20, 8, "square", "#ffffff")
    assert result.size == (400, 400)
    assert result.getpixel((200, 200))[:3] == (255, 0, 0)


def test_embed_center_image_supports_rounded_backing():
    qr = Image.new("RGB", (400, 400), "#ffffff")
    logo = Image.new("RGBA", (100, 100), "#0000ff")
    result = embed_center_image(qr, logo, 20, 8, "rounded", "#ffffff")
    assert result.size == (400, 400)
    assert result.mode == "RGBA"
