import threading

from flask import Flask, jsonify, request
from waitress import serve

from main import generate_share_link

app = Flask(__name__)
_adb_lock = threading.Lock()


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/share")
def share():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid or missing JSON body"}), 400
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "missing url"}), 400
    if not _adb_lock.acquire(blocking=False):
        return jsonify({"error": "device busy"}), 503
    try:
        link = generate_share_link(url)
        return jsonify({"link": link})
    except (RuntimeError, ValueError) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        _adb_lock.release()


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
