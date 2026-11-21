from __future__ import annotations

from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
import os

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from stegnova.core import (
    StegoError, encode_image, decode_image, encode_audio, decode_audio,
    encode_text, decode_text, build_payload, open_payload, image_capacity,
    audio_capacity,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024  # 80 MB upload limit
app.config["SECRET_KEY"] = os.environ.get("STEGNOVA_SECRET", "local-development-only")
ALLOWED_IMAGE = {".png", ".bmp"}
ALLOWED_AUDIO = {".wav"}
activity_log: list[dict] = []


def record(action: str, mode: str, detail: str) -> None:
    activity_log.insert(0, {
        "action": action, "mode": mode, "detail": detail,
        "time": datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
    })
    del activity_log[20:]


def get_payload() -> bytes:
    uploaded = request.files.get("payload_file")
    text = request.form.get("payload_text", "")
    if uploaded and uploaded.filename:
        data = uploaded.read()
        if not data:
            raise StegoError("The selected payload file is empty.")
        return data
    if text:
        return text.encode("utf-8")
    raise StegoError("Enter a secret message or select a payload file.")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/activity")
def activity():
    return jsonify({"items": activity_log})


@app.post("/api/encode")
def encode():
    mode = request.form.get("mode", "").lower()
    password = request.form.get("password", "")
    try:
        raw_payload = get_payload()
        envelope = build_payload(raw_payload, password)
        if mode == "image":
            carrier = request.files.get("carrier")
            if not carrier or not carrier.filename:
                raise StegoError("Choose a PNG or BMP carrier image.")
            ext = Path(secure_filename(carrier.filename)).suffix.lower()
            if ext not in ALLOWED_IMAGE:
                raise StegoError("Image mode supports PNG and BMP carriers only.")
            result = encode_image(carrier.read(), envelope)
            mimetype, filename = "image/png", "stegnova_encoded.png"
        elif mode == "audio":
            carrier = request.files.get("carrier")
            if not carrier or not carrier.filename:
                raise StegoError("Choose a WAV carrier audio file.")
            ext = Path(secure_filename(carrier.filename)).suffix.lower()
            if ext not in ALLOWED_AUDIO:
                raise StegoError("Audio mode supports WAV carriers only.")
            result = encode_audio(carrier.read(), envelope)
            mimetype, filename = "audio/wav", "stegnova_encoded.wav"
        elif mode == "text":
            cover = request.form.get("cover_text", "")
            if not cover.strip():
                raise StegoError("Enter some ordinary cover text.")
            result = encode_text(cover, envelope).encode("utf-8")
            mimetype, filename = "text/plain; charset=utf-8", "stegnova_encoded.txt"
        else:
            raise StegoError("Choose image, audio or text mode.")
        record("Encode", mode, f"{len(raw_payload):,} payload bytes")
        return send_file(BytesIO(result), mimetype=mimetype, as_attachment=True, download_name=filename)
    except StegoError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Encoding failed")
        return jsonify({"error": "Encoding failed. Check the carrier and payload files, then try again."}), 500


@app.post("/api/decode")
def decode():
    mode = request.form.get("mode", "").lower()
    password = request.form.get("password", "")
    carrier = request.files.get("carrier")
    try:
        if not carrier or not carrier.filename:
            raise StegoError("Choose the encoded file to inspect.")
        data = carrier.read()
        if mode == "image":
            envelope = decode_image(data)
        elif mode == "audio":
            envelope = decode_audio(data)
        elif mode == "text":
            envelope = decode_text(data.decode("utf-8"))
        else:
            raise StegoError("Choose image, audio or text mode.")
        payload = open_payload(envelope, password)
        record("Decode", mode, f"{len(payload):,} recovered bytes")
        is_text = False
        try:
            preview = payload.decode("utf-8")
            is_text = all(ch.isprintable() or ch in "\r\n\t" for ch in preview)
        except UnicodeDecodeError:
            preview = ""
        if is_text:
            return jsonify({"kind": "text", "text": preview, "bytes": len(payload)})
        return send_file(BytesIO(payload), mimetype="application/octet-stream",
                         as_attachment=True, download_name="stegnova_recovered_payload.bin")
    except StegoError as exc:
        return jsonify({"error": str(exc)}), 400
    except (UnicodeDecodeError, ValueError):
        return jsonify({"error": "The selected file is not valid UTF-8 text for text mode."}), 400
    except Exception:
        app.logger.exception("Decoding failed")
        return jsonify({"error": "Decoding failed. The file may be damaged or use a different format."}), 500


@app.post("/api/capacity")
def capacity():
    mode = request.form.get("mode", "").lower()
    carrier = request.files.get("carrier")
    try:
        if not carrier:
            raise StegoError("Choose a carrier file first.")
        data = carrier.read()
        if mode == "image":
            cap = image_capacity(data)
        elif mode == "audio":
            cap = audio_capacity(data)
        else:
            raise StegoError("Capacity is available for image and WAV audio carriers.")
        return jsonify({"capacity_bytes": cap, "capacity_kb": round(cap / 1024, 2)})
    except StegoError as exc:
        return jsonify({"error": str(exc)}), 400


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Upload exceeds the 80 MB limit."}), 413


if __name__ == "__main__":
    # Localhost only: this app is intended for local learning and testing.
    app.run(host="127.0.0.1", port=5000, debug=False)
