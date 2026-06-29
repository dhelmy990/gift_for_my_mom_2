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
