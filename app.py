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
