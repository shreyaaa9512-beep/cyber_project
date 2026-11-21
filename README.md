# StegNova – Local Steganography Multitool

A local-first educational steganography web app built with Python + Flask.

## Features
- Image steganography: RGB least-significant-bit (LSB), PNG/BMP input, PNG output.
- Audio steganography: PCM WAV sample LSB, WAV output.
- Text steganography: zero-width Unicode payload markers.
- Optional AES-256-GCM encryption with PBKDF2-HMAC-SHA256 key derivation.
- Capacity checks, validation, download responses, and in-session activity log.
- Runs on `127.0.0.1` only; no cloud service or API key.

## Requirements
- Windows 10/11, macOS, or Linux
- Python 3.11+ recommended
- VS Code (Python extension recommended)

## Windows setup (VS Code terminal)
1. Extract the ZIP.
2. Open the `stegnova_local` folder in VS Code (`File > Open Folder`).
3. Open `Terminal > New Terminal`.
4. Check Python: `py --version`
5. Create a virtual environment: `py -m venv .venv`
6. Activate it in PowerShell: `.\.venv\Scripts\Activate.ps1`
   - If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.
   - Command Prompt alternative: `.venv\Scripts\activate.bat`
7. Install packages: `py -m pip install --upgrade pip`
8. Then: `py -m pip install -r requirements.txt`
9. Start the website: `py app.py`
10. Open `http://127.0.0.1:5000` in your browser.
11. Stop the server with `Ctrl+C` in the VS Code terminal.

## macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.

## How to use
### Encode
1. Select Image, Audio, or Text.
2. Choose a secret message or payload file.
3. Choose a carrier (image/WAV) or enter cover text.
4. Optionally set a password. Keep it safe: a forgotten password cannot be recovered.
5. Click **Encode & Download** and save the generated carrier.

### Decode
1. Select the same carrier type used during encoding.
2. Upload the encoded carrier.
3. Enter the password if encryption was enabled.
4. Click **Extract Secret**. Text payloads are shown; binary payloads download.

## Important limitations
- Image: use PNG or BMP. Do not convert the encoded output to JPEG, resize it, or apply filters.
- Audio: use uncompressed PCM WAV. Do not convert, normalize, trim, or re-encode the output.
- Text: copy/paste may preserve zero-width characters inconsistently; use the downloaded TXT file.
- This is a learning/demo tool, not a substitute for a vetted secure communications product.
- The app has no user accounts and is intended for localhost. Do not expose it to the public internet.
- The in-memory activity list resets when the server restarts.
- Video-frame steganography is not included in this first stable local build.

## Troubleshooting
- `py is not recognized`: install Python from python.org and enable **Add Python to PATH**, then reopen VS Code.
- `No module named flask`: activate `.venv` and run `py -m pip install -r requirements.txt`.
- Port 5000 busy: close the other local server or change `port=5000` in `app.py`.
- Decryption error: use the exact same password used during encoding.
