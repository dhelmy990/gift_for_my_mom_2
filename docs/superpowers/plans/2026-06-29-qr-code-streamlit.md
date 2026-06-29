# QR Code Streamlit App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public Streamlit app that generates styled URL QR codes with optional centered image embedding and downloads in PNG, SVG, PDF, JPG, and WebP.

**Architecture:** Keep `app.py` as a thin Streamlit entry point and place all testable behavior in focused helper modules. Generate QR data with `segno`, composite raster images with Pillow, export PDFs with reportlab, and keep every generated asset in memory.

**Tech Stack:** Python 3.11+, Streamlit, segno, Pillow, reportlab, pytest.

## Global Constraints

- The app targets Streamlit Community Cloud.
- `app.py` is the Streamlit entry point.
- Do not use user accounts, server-side storage, a database, saved projects, analytics, or batch generation.
- Keep uploaded images and generated QR codes in memory with `BytesIO`; do not write them to disk.
- Use high QR error correction, preferably level `H`.
- Default center image size is 20% of QR width.
- Show a warning above 25% logo size and a stronger warning above 30%.
- Reject uploaded images above 5 MB.
- Normalize URLs without a scheme to `https://`.
- Support downloads for PNG, SVG, PDF, JPG, and WebP.
- SVG export without a center image must be true vector QR data.
- SVG export with a center image must embed the uploaded image as base64 in the SVG.
- Keep dependencies minimal for Streamlit Community Cloud.

---

## File Structure

- `requirements.txt`: Runtime and test dependencies.
- `pytest.ini`: Pytest configuration with the project root on `pythonpath`.
- `validation.py`: URL normalization, image upload size validation, and logo risk classification.
- `qr_generator.py`: Base QR generation for raster and SVG paths.
- `image_embedder.py`: Uploaded image loading, resizing, backing creation, and center compositing.
- `exporters.py`: PNG, JPG, WebP, PDF, and SVG byte exporters.
- `app.py`: Streamlit UI, preview, warnings, and download buttons.
- `README.md`: Local run and Streamlit Community Cloud deployment notes.
- `tests/test_validation.py`: Validation unit tests.
- `tests/test_qr_generator.py`: QR generator unit tests.
- `tests/test_image_embedder.py`: Image embedder unit tests.
- `tests/test_exporters.py`: Exporter unit tests.

---

### Task 1: Project Setup And Validation

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `validation.py`
- Create: `tests/test_validation.py`

**Interfaces:**
- Produces: `MAX_UPLOAD_BYTES: int`
- Produces: `normalize_url(raw_url: str) -> str`
- Produces: `is_valid_url(url: str) -> bool`
- Produces: `validate_upload_size(size_bytes: int) -> None`
- Produces: `logo_risk_level(logo_percent: int) -> str`

- [ ] **Step 1: Write the failing validation tests**

Create `tests/test_validation.py`:

```python
import pytest

from validation import (
    MAX_UPLOAD_BYTES,
    is_valid_url,
    logo_risk_level,
    normalize_url,
    validate_upload_size,
)


def test_normalize_url_adds_https_to_bare_domain():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_preserves_existing_scheme_and_strips_spaces():
    assert normalize_url("  http://example.com/path  ") == "http://example.com/path"


def test_normalize_url_empty_string_returns_empty_string():
    assert normalize_url("   ") == ""


@pytest.mark.parametrize(
    "url",
    ["https://example.com", "http://example.com/path?x=1", "https://sub.example.co.uk"],
)
def test_is_valid_url_accepts_http_urls(url):
    assert is_valid_url(url)


@pytest.mark.parametrize("url", ["", "not a url", "ftp://example.com", "https://"])
def test_is_valid_url_rejects_invalid_or_unsupported_urls(url):
    assert not is_valid_url(url)


def test_validate_upload_size_accepts_5_mb_limit():
    validate_upload_size(MAX_UPLOAD_BYTES)


def test_validate_upload_size_rejects_above_5_mb_limit():
    with pytest.raises(ValueError, match="5 MB"):
        validate_upload_size(MAX_UPLOAD_BYTES + 1)


@pytest.mark.parametrize(
    ("logo_percent", "expected"),
    [(20, "ok"), (25, "ok"), (26, "warning"), (30, "warning"), (31, "strong_warning")],
)
def test_logo_risk_level(logo_percent, expected):
    assert logo_risk_level(logo_percent) == expected
```

- [ ] **Step 2: Add project dependency and pytest config files**

Create `requirements.txt`:

```txt
streamlit>=1.36,<2
segno>=1.6,<2
Pillow>=10.4,<11
reportlab>=4.2,<5
pytest>=8.2,<9
```

Create `pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 3: Run validation tests to verify they fail because the module is missing**

Run:

```bash
pytest tests/test_validation.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'validation'`.

- [ ] **Step 4: Implement validation helpers**

Create `validation.py`:

```python
from urllib.parse import urlparse

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def normalize_url(raw_url: str) -> str:
    stripped = raw_url.strip()
    if not stripped:
        return ""
    parsed = urlparse(stripped)
    if parsed.scheme:
        return stripped
    return f"https://{stripped}"


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_upload_size(size_bytes: int) -> None:
    if size_bytes > MAX_UPLOAD_BYTES:
        raise ValueError("Uploaded image must be 5 MB or smaller.")


def logo_risk_level(logo_percent: int) -> str:
    if logo_percent > 30:
        return "strong_warning"
    if logo_percent > 25:
        return "warning"
    return "ok"
```

- [ ] **Step 5: Run validation tests to verify they pass**

Run:

```bash
pytest tests/test_validation.py -v
```

Expected: PASS for all tests in `tests/test_validation.py`.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt pytest.ini validation.py tests/test_validation.py
git commit -m "feat: add validation helpers"
```

---

### Task 2: QR Generation

**Files:**
- Create: `qr_generator.py`
- Create: `tests/test_qr_generator.py`

**Interfaces:**
- Consumes: normalized valid URL strings from `validation.normalize_url`.
- Produces: `create_qr(url: str, foreground: str = "#000000", background: str = "#ffffff") -> segno.QRCode`
- Produces: `qr_to_png_image(qr: segno.QRCode, size_px: int, foreground: str, background: str) -> PIL.Image.Image`
- Produces: `qr_to_svg_text(qr: segno.QRCode, foreground: str, background: str) -> str`

- [ ] **Step 1: Write the failing QR generator tests**

Create `tests/test_qr_generator.py`:

```python
from io import BytesIO

from PIL import Image

from qr_generator import create_qr, qr_to_png_image, qr_to_svg_text


def test_create_qr_returns_high_error_qr():
    qr = create_qr("https://example.com")
    assert qr.error == "H"


def test_qr_to_png_image_returns_requested_size_rgb_image():
    qr = create_qr("https://example.com")
    image = qr_to_png_image(qr, size_px=512, foreground="#111111", background="#eeeeee")
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
```

- [ ] **Step 2: Run QR tests to verify they fail because the module is missing**

Run:

```bash
pytest tests/test_qr_generator.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'qr_generator'`.

- [ ] **Step 3: Implement QR generation helpers**

Create `qr_generator.py`:

```python
from io import BytesIO

import segno
from PIL import Image


def create_qr(url: str, foreground: str = "#000000", background: str = "#ffffff") -> segno.QRCode:
    return segno.make(url, error="h")


def qr_to_png_image(qr: segno.QRCode, size_px: int, foreground: str, background: str) -> Image.Image:
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
```

- [ ] **Step 4: Run QR tests to verify they pass**

Run:

```bash
pytest tests/test_qr_generator.py -v
```

Expected: PASS for all tests in `tests/test_qr_generator.py`.

- [ ] **Step 5: Run all tests**

Run:

```bash
pytest -v
```

Expected: PASS for validation and QR generator tests.

- [ ] **Step 6: Commit**

```bash
git add qr_generator.py tests/test_qr_generator.py
git commit -m "feat: add QR generation helpers"
```

---

### Task 3: Center Image Embedding

**Files:**
- Create: `image_embedder.py`
- Create: `tests/test_image_embedder.py`

**Interfaces:**
- Consumes: `PIL.Image.Image` QR images from `qr_generator.qr_to_png_image`.
- Produces: `load_uploaded_image(data: bytes) -> PIL.Image.Image`
- Produces: `embed_center_image(qr_image: PIL.Image.Image, logo_image: PIL.Image.Image | None, logo_percent: int, padding_px: int, backing_shape: str, background: str) -> PIL.Image.Image`

- [ ] **Step 1: Write the failing image embedding tests**

Create `tests/test_image_embedder.py`:

```python
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
```

- [ ] **Step 2: Run image embedding tests to verify they fail because the module is missing**

Run:

```bash
pytest tests/test_image_embedder.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'image_embedder'`.

- [ ] **Step 3: Implement image loading and compositing**

Create `image_embedder.py`:

```python
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
```

- [ ] **Step 4: Run image embedding tests to verify they pass**

Run:

```bash
pytest tests/test_image_embedder.py -v
```

Expected: PASS for all tests in `tests/test_image_embedder.py`.

- [ ] **Step 5: Run all tests**

Run:

```bash
pytest -v
```

Expected: PASS for validation, QR generator, and image embedding tests.

- [ ] **Step 6: Commit**

```bash
git add image_embedder.py tests/test_image_embedder.py
git commit -m "feat: add center image embedding"
```

---

### Task 4: Exporters

**Files:**
- Create: `exporters.py`
- Create: `tests/test_exporters.py`

**Interfaces:**
- Consumes: `PIL.Image.Image` from `image_embedder.embed_center_image`.
- Consumes: SVG text from `qr_generator.qr_to_svg_text`.
- Produces: `export_png(image: PIL.Image.Image) -> bytes`
- Produces: `export_jpg(image: PIL.Image.Image, background: str) -> bytes`
- Produces: `export_webp(image: PIL.Image.Image) -> bytes`
- Produces: `export_pdf(image: PIL.Image.Image) -> bytes`
- Produces: `embed_logo_in_svg(svg_text: str, logo_bytes: bytes | None, logo_percent: int, padding_px: int, backing_shape: str, background: str) -> str`
- Produces: `export_svg(svg_text: str, logo_bytes: bytes | None, logo_percent: int, padding_px: int, backing_shape: str, background: str) -> bytes`

- [ ] **Step 1: Write the failing exporter tests**

Create `tests/test_exporters.py`:

```python
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
    svg = "<svg viewBox=\"0 0 100 100\"><path d=\"M0 0h10v10z\" /></svg>"
    assert export_svg(svg, None, 20, 8, "square", "#ffffff") == svg.encode("utf-8")


def test_embed_logo_in_svg_adds_base64_image_and_backing():
    svg = "<svg viewBox=\"0 0 100 100\"><path d=\"M0 0h10v10z\" /></svg>"
    result = embed_logo_in_svg(svg, make_logo_bytes(), 20, 4, "rounded", "#ffffff")
    assert "data:image/png;base64," in result
    assert "<image" in result
    assert "<rect" in result
```

- [ ] **Step 2: Run exporter tests to verify they fail because the module is missing**

Run:

```bash
pytest tests/test_exporters.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'exporters'`.

- [ ] **Step 3: Implement raster and SVG exporters**

Create `exporters.py`:

```python
import base64
import re
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def export_png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def export_jpg(image: Image.Image, background: str) -> bytes:
    flattened = Image.new("RGB", image.size, background)
    flattened.paste(image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A"))
    buffer = BytesIO()
    flattened.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def export_webp(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="WEBP", lossless=True, quality=100)
    return buffer.getvalue()


def export_pdf(image: Image.Image) -> bytes:
    png_buffer = BytesIO(export_png(image))
    width, height = image.size
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=(width, height))
    pdf.drawImage(ImageReader(png_buffer), 0, 0, width=width, height=height)
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
    logo_size = view_width * (logo_percent / 100)
    backing_size = logo_size + (padding_px * 2)
    x = (view_width - backing_size) / 2
    y = (view_height - backing_size) / 2
    radius = backing_size / 8 if backing_shape == "rounded" else 0
    encoded = base64.b64encode(logo_bytes).decode("ascii")
    safe_background = escape(background)
    overlay = (
        f'<rect x="{x:.3f}" y="{y:.3f}" width="{backing_size:.3f}" '
        f'height="{backing_size:.3f}" rx="{radius:.3f}" ry="{radius:.3f}" '
        f'fill="{safe_background}" />'
        f'<image x="{x + padding_px:.3f}" y="{y + padding_px:.3f}" '
        f'width="{logo_size:.3f}" height="{logo_size:.3f}" '
        f'href="data:image/png;base64,{encoded}" />'
    )
    return svg_text.replace("</svg>", f"{overlay}</svg>")


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
```

- [ ] **Step 4: Run exporter tests to verify they pass**

Run:

```bash
pytest tests/test_exporters.py -v
```

Expected: PASS for all tests in `tests/test_exporters.py`.

- [ ] **Step 5: Run all tests**

Run:

```bash
pytest -v
```

Expected: PASS for validation, QR generation, image embedding, and exporter tests.

- [ ] **Step 6: Commit**

```bash
git add exporters.py tests/test_exporters.py
git commit -m "feat: add QR export formats"
```

---

### Task 5: Streamlit App And Deployment Notes

**Files:**
- Create: `app.py`
- Create: `README.md`

**Interfaces:**
- Consumes: `validation.normalize_url(raw_url: str) -> str`
- Consumes: `validation.is_valid_url(url: str) -> bool`
- Consumes: `validation.validate_upload_size(size_bytes: int) -> None`
- Consumes: `validation.logo_risk_level(logo_percent: int) -> str`
- Consumes: `qr_generator.create_qr(url: str, foreground: str, background: str) -> segno.QRCode`
- Consumes: `qr_generator.qr_to_png_image(qr, size_px: int, foreground: str, background: str) -> PIL.Image.Image`
- Consumes: `qr_generator.qr_to_svg_text(qr, foreground: str, background: str) -> str`
- Consumes: `image_embedder.load_uploaded_image(data: bytes) -> PIL.Image.Image`
- Consumes: `image_embedder.embed_center_image(...) -> PIL.Image.Image`
- Consumes: exporter functions from `exporters.py`.

- [ ] **Step 1: Create the Streamlit app**

Create `app.py`:

```python
import streamlit as st

from exporters import export_jpg, export_pdf, export_png, export_svg, export_webp
from image_embedder import embed_center_image, load_uploaded_image
from qr_generator import create_qr, qr_to_png_image, qr_to_svg_text
from validation import is_valid_url, logo_risk_level, normalize_url, validate_upload_size


def show_risk_message(logo_percent: int) -> None:
    risk = logo_risk_level(logo_percent)
    if risk == "warning":
        st.warning("Logo size is above 25%. Test the QR code before sharing.")
    elif risk == "strong_warning":
        st.error("Logo size is above 30%. This may make the QR code hard to scan.")


def main() -> None:
    st.set_page_config(page_title="QR Code Generator", page_icon="QR", layout="wide")
    st.title("QR Code Generator")

    controls, preview = st.columns([1, 1])

    with controls:
        raw_url = st.text_input("URL", placeholder="https://example.com")
        normalized_url = normalize_url(raw_url)
        foreground = st.color_picker("Foreground", "#000000")
        background = st.color_picker("Background", "#ffffff")
        size_px = st.slider("QR size", min_value=256, max_value=2048, value=1024, step=128)
        uploaded_file = st.file_uploader("Center image", type=["png", "jpg", "jpeg", "webp"])
        logo_percent = st.slider("Logo size", min_value=5, max_value=40, value=20, step=1)
        padding_px = st.slider("Logo padding", min_value=0, max_value=64, value=12, step=2)
        backing_shape = st.radio("Logo backing", ["square", "rounded"], horizontal=True)

    if raw_url and normalized_url != raw_url.strip():
        st.caption(f"Using normalized URL: `{normalized_url}`")

    if not normalized_url:
        st.info("Enter a URL to generate a QR code.")
        return

    if not is_valid_url(normalized_url):
        st.error("Enter a valid HTTP or HTTPS URL.")
        return

    show_risk_message(logo_percent)

    logo_image = None
    logo_bytes = None
    if uploaded_file is not None:
        logo_bytes = uploaded_file.getvalue()
        try:
            validate_upload_size(len(logo_bytes))
            logo_image = load_uploaded_image(logo_bytes)
        except ValueError as exc:
            st.error(str(exc))
            logo_image = None
            logo_bytes = None

    try:
        qr = create_qr(normalized_url, foreground=foreground, background=background)
        base_image = qr_to_png_image(qr, size_px=size_px, foreground=foreground, background=background)
        final_image = embed_center_image(
            base_image,
            logo_image,
            logo_percent=logo_percent,
            padding_px=padding_px,
            backing_shape=backing_shape,
            background=background,
        )
        svg_text = qr_to_svg_text(qr, foreground=foreground, background=background)
    except Exception as exc:
        st.error(f"Could not generate QR code: {exc}")
        return

    with preview:
        st.image(final_image, caption="Preview", use_container_width=True)

        exports = {
            "PNG": ("qr-code.png", "image/png", lambda: export_png(final_image)),
            "SVG": (
                "qr-code.svg",
                "image/svg+xml",
                lambda: export_svg(svg_text, logo_bytes, logo_percent, padding_px, backing_shape, background),
            ),
            "PDF": ("qr-code.pdf", "application/pdf", lambda: export_pdf(final_image)),
            "JPG": ("qr-code.jpg", "image/jpeg", lambda: export_jpg(final_image, background)),
            "WebP": ("qr-code.webp", "image/webp", lambda: export_webp(final_image)),
        }

        for label, (file_name, mime_type, build_bytes) in exports.items():
            try:
                st.download_button(
                    label=f"Download {label}",
                    data=build_bytes(),
                    file_name=file_name,
                    mime=mime_type,
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"{label} export failed: {exc}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add README with local and public deployment instructions**

Create `README.md`:

````markdown
# QR Code Generator

A Streamlit app for generating styled URL QR codes with an optional centered image.

## Features

- URL normalization and validation.
- Optional centered PNG, JPG, JPEG, or WebP image.
- Foreground and background color controls.
- QR size, logo size, logo padding, and backing shape controls.
- Downloads for PNG, SVG, PDF, JPG, and WebP.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest -v
```

## Streamlit Community Cloud

Deploy this repository on Streamlit Community Cloud with `app.py` as the entry point. The app does not require a database, secrets, or persistent file storage.
````

- [ ] **Step 3: Run unit tests**

Run:

```bash
pytest -v
```

Expected: PASS for all tests.

- [ ] **Step 4: Compile Python files**

Run:

```bash
python -m py_compile app.py validation.py qr_generator.py image_embedder.py exporters.py
```

Expected: command exits with status 0 and no output.

- [ ] **Step 5: Run the Streamlit app locally**

Run:

```bash
streamlit run app.py
```

Expected: Streamlit starts and prints a local URL such as `http://localhost:8501`.

- [ ] **Step 6: Manual verification**

In the running Streamlit app:

1. Enter `example.com` and confirm the UI displays the normalized URL `https://example.com`.
2. Generate a QR code without a center image.
3. Download PNG, SVG, PDF, JPG, and WebP files.
4. Upload a small PNG image.
5. Set logo size to 20%, padding to 12, backing to rounded.
6. Confirm the preview shows the image centered in the QR code.
7. Set logo size to 26% and confirm a warning appears.
8. Set logo size to 31% and confirm a stronger warning appears.
9. Download all five formats again.
10. Scan at least one generated QR code with a phone camera and confirm it opens `https://example.com`.

- [ ] **Step 7: Stop the Streamlit app**

Press `Ctrl+C` in the terminal running Streamlit.

Expected: the Streamlit process exits cleanly.

- [ ] **Step 8: Commit**

```bash
git add app.py README.md
git commit -m "feat: add Streamlit QR generator app"
```

---

## Final Verification

- [ ] Run all automated tests:

```bash
pytest -v
```

Expected: every test passes.

- [ ] Compile all Python files:

```bash
python -m py_compile app.py validation.py qr_generator.py image_embedder.py exporters.py
```

Expected: command exits with status 0 and no output.

- [ ] Check git state:

```bash
git status --short
```

Expected: no output.

---

## Self-Review Notes

- Spec coverage: The plan covers public Streamlit deployment, in-memory generation, URL normalization, image upload and embedding, basic styling controls, scan-risk warnings, all five export formats, and focused tests for non-Streamlit modules.
- Scope check: The plan is one implementation cycle because it builds one small stateless utility with no independent subsystems.
- Type consistency: Function signatures are defined before consumers use them, and the same names are used across tasks.
