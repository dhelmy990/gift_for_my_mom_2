# Streamlit QR Code Generator Design

Date: 2026-06-29

## Goal

Build a public Streamlit application that creates QR codes from URLs and lets users embed an uploaded image in the center. The app is for personal use but should be accessible to anyone through a simple Streamlit Community Cloud URL.

## Scope

The app is a single-page QR generation tool. Users can enter a URL, optionally upload a center image, adjust basic styling, preview the generated QR code, and download the result in multiple formats.

Included features:

- URL input with validation and normalization.
- Optional center image upload.
- Adjustable logo size and padding.
- Foreground and background color controls.
- QR output size control.
- Live preview.
- Download buttons for PNG, SVG, PDF, JPG, and WebP.
- Scan reliability warnings when center image settings become risky.

Out of scope for the first version:

- User accounts.
- Server-side storage.
- QR scan analytics.
- Saved projects or history.
- Advanced visual styling such as gradients, custom finder-eye shapes, or rounded QR modules.
- Batch QR generation.

## User Experience

The app will present a single Streamlit page with the generator controls and preview. The primary workflow is:

1. Enter a URL.
2. Upload an optional center image.
3. Adjust basic styling controls.
4. Review the live preview.
5. Download the QR code in the desired format.

Controls:

- URL input.
- Image uploader for PNG, JPG, JPEG, and WebP files.
- Foreground color picker.
- Background color picker.
- QR output size control.
- Logo size percentage control.
- Logo padding control.
- Center-image backing shape selector, with square and rounded options.

The app should feel like a compact utility rather than a landing page. It should prioritize the generator and preview as the first screen.

## Architecture

The app will be split into a small Streamlit entry point and focused helper modules:

- `app.py`: Streamlit layout, form controls, preview rendering, warnings, and download buttons.
- `qr_generator.py`: Base QR generation from a normalized URL using high error correction. Produces QR data for raster and SVG exports.
- `image_embedder.py`: Uploaded image normalization, resizing, padding, backing shape application, and raster compositing.
- `exporters.py`: Conversion to PNG, JPG, WebP, PDF, and SVG bytes for Streamlit downloads.
- `validation.py`: URL normalization, URL validation, image size checks, and scan-risk thresholds.

The app will avoid writing uploaded images or generated QR codes to disk. Generated assets will be kept in memory with `BytesIO`, which fits Streamlit Community Cloud and avoids cleanup concerns.

## Dependencies

Recommended dependencies:

- `streamlit` for the app shell.
- `segno` for standards-compliant QR generation and SVG output.
- `Pillow` for image processing and raster exports.
- `reportlab` for PDF export.

The implementation should keep dependencies minimal for faster Streamlit Community Cloud setup and fewer deployment failures.

## Generation Behavior

QR codes will use high error correction, preferably level `H`, because embedding an image in the center covers part of the QR code. Defaults should favor scan reliability:

- Default center image size: around 20% of QR width.
- Warning threshold: above 25% of QR width.
- Strong warning threshold: above 30% of QR width.

The app should allow users to choose riskier settings, but it should warn them that scan reliability may suffer.

If the user enters a domain without a scheme, such as `example.com`, the app will normalize it to `https://example.com`. Invalid or unsupported URLs should prevent generation until corrected.

## Export Behavior

Raster exports:

- PNG: lossless default.
- JPG: flattened onto the selected background color.
- WebP: high-quality or lossless output.
- PDF: high-resolution QR image placed on a single PDF page.

SVG export:

- Without a center image, export a true vector SVG from the QR generator.
- With a center image, export an SVG containing vector QR data plus the uploaded image embedded as base64, centered with the same size and padding settings.

Each export should be generated in memory and passed directly to `st.download_button`.

## Error Handling

The app should handle invalid or risky inputs in the UI without crashing:

- Empty URL: disable generation and show a validation message.
- URL missing scheme: normalize to `https://`.
- Invalid colors: prevented through Streamlit color pickers.
- Unsupported or corrupt image upload: show an error and continue without the image.
- Oversized uploaded image: reject files above 5 MB and show a clear error. Accepted images may still be resized in memory for compositing.
- Logo too large: show scan reliability warnings above the defined thresholds.
- Export failure: show an error for the failed format while keeping other downloads available.

## Testing Strategy

The implementation should include focused tests for non-Streamlit helper modules:

- URL normalization and validation.
- QR byte generation.
- Raster image compositing with and without a center image.
- Export byte generation for PNG, JPG, WebP, PDF, and SVG.
- Edge cases, including no uploaded image, oversized image, and risky logo size thresholds.

Manual verification should include running the Streamlit app locally, generating a QR code, downloading each format, and scanning at least one generated QR code from the preview or exported image.

## Deployment

The app will target Streamlit Community Cloud:

- Keep app state local to the current browser session.
- Do not depend on a database or persistent filesystem.
- Provide a simple `requirements.txt`.
- Ensure `app.py` is the Streamlit entry point.

## Approved Approach

Use a Python-native Streamlit app with `segno` for QR generation and SVG support, Pillow for image processing and raster outputs, and reportlab for PDF export. This approach keeps the app idiomatic, deployment-friendly, and reliable for the required output formats.
