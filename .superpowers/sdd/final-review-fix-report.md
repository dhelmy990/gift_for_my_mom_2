# Final Review Fix Report

Date: 2026-06-29
Branch: `master`

## Commands Run

1. `git status --short`
   - Result: clean working tree before edits.
2. `rg --files /home/dhelmy990/Code/gift_for_my_mom_2`
   - Result: confirmed expected app, exporter, validation, and test files.
3. `sed -n '1,240p' app.py`
   - Result: confirmed upload size was checked after `uploaded_file.getvalue()` and SVG export did not receive `size_px`.
4. `sed -n '1,240p' validation.py`
   - Result: confirmed normalization used `urlparse()` directly and validation only checked scheme plus `netloc`.
5. `sed -n '1,280p' exporters.py`
   - Result: confirmed SVG padding used raw `padding_px` in viewBox coordinates.
6. `sed -n '1,260p' tests/test_validation.py`
   - Result: confirmed missing coverage for scheme-less URLs with ports and malformed hostnames containing whitespace.
7. `sed -n '1,320p' tests/test_exporters.py`
   - Result: confirmed missing coverage for SVG geometry scaling and WebP MIME embedding.
8. `sed -n '1,260p' qr_generator.py`
   - Result: confirmed raster preview is resized to caller-provided `size_px`, which defines the correct SVG padding ratio.
9. `sed -n '1,280p' image_embedder.py`
   - Result: confirmed raster logo padding is pixel-based, so SVG export needed conversion from pixels to viewBox units.
10. `sed -n '1,240p' README.md`
    - Result: reviewed deployment notes; no README update required for the requested fixes.
11. `.venv/bin/python -m pytest tests/test_validation.py tests/test_exporters.py`
    - Result: failed with 9 expected regressions, including URL normalization/validation failures and missing `size_px` support in SVG exporter APIs.
12. `.venv/bin/python -m pytest tests/test_validation.py tests/test_exporters.py`
    - Result: passed, `30 passed in 0.07s`.
13. `.venv/bin/python -m py_compile app.py validation.py qr_generator.py image_embedder.py exporters.py`
    - Result: passed with exit code 0.
14. `.venv/bin/python -m pytest`
    - Result: passed, `38 passed in 0.07s`.

## Fix Summary

- Added `size_px` plumbing to `embed_logo_in_svg()` and `export_svg()` and converted logo padding from raster pixels to SVG viewBox units.
- Tightened URL normalization and validation for scheme-less URLs with ports and malformed whitespace-containing URLs.
- Enforced the 5 MB upload limit before reading uploaded bytes when Streamlit exposes `uploaded_file.size`.
- Added `.streamlit/config.toml` with `maxUploadSize = 5`.
- Added regression tests for SVG geometry ratios and WebP MIME embedding.

## Final Re-review Fix

1. `git status --short`
   - Result: clean working tree before these edits.
2. `.venv/bin/python - <<'PY' ... PY`
   - Result: confirmed `qr_to_svg_text(create_qr(...))` emits Segno SVG with `width="37"` and `height="37"` but no `viewBox`.
3. `.venv/bin/python -m pytest tests/test_validation.py tests/test_exporters.py`
   - Result: failed as expected with 4 regressions:
     - `is_valid_url("https://[::1")` raised `ValueError: Invalid IPv6 URL`
     - `is_valid_url("https://example.com:bad")` incorrectly returned `True`
     - `is_valid_url("https://example.com:99999")` incorrectly returned `True`
     - Segno SVG logo overlay coordinates exceeded the real `37x37` viewport when `viewBox` was absent
4. `apply_patch` on `tests/test_exporters.py` and `tests/test_validation.py`
   - Result: added regression coverage for real Segno SVG width/height fallback behavior and malformed/out-of-range URL ports.
5. `apply_patch` on `exporters.py` and `validation.py`
   - Result: `_svg_viewbox_size()` now falls back to numeric `width`/`height` attributes when `viewBox` is absent; `is_valid_url()` now returns `False` on `urlparse()` / hostname / port `ValueError`s and forces `parsed.port` evaluation.
6. `.venv/bin/python -m pytest tests/test_validation.py tests/test_exporters.py`
   - Result: passed, `34 passed in 0.11s`.
7. `.venv/bin/python -m pytest`
   - Result: passed, `42 passed in 0.11s`.
8. `.venv/bin/python -m py_compile app.py validation.py qr_generator.py image_embedder.py exporters.py`
   - Result: passed with exit code 0.
