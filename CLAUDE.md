# allegro-share-automation

Automates generating Allegro referral share links by driving the Android Allegro app via ADB. Exposed as both a Flask HTTP service and a CLI.

## Architecture

- **`main.py`** — core ADB logic + CLI entry point
- **`app.py`** — Flask web service wrapping `main.py`

No other modules. Keep it flat.

## Key constraints

- Only one ADB session can run at a time. `app.py` enforces this with `threading.Lock` — do not add concurrency or async without replacing this mechanism.
- ADB operations depend on device UI state and use `time.sleep` deliberately. Do not remove sleeps.
- `generate_share_link()` in `main.py` is the single entry point for both CLI and HTTP.

## Package manager

Use `uv` exclusively. Never use `pip` directly.

```bash
uv add <package>
uv run python main.py <url>
```

## Running

```bash
# HTTP service
flask --app app run --host 0.0.0.0 --port 5000

# CLI
python main.py <allegro_offer_url>
```

## API

```
POST /share   {"url": "<allegro_url>"}  →  {"link": "<referral_url>"}  |  {"error": "..."}
GET  /health                            →  {"status": "ok"}
```

HTTP 503 = ADB busy (another request in progress). Caller should retry.

## ADB setup

Android device must be connected and authorized. Verify with `adb devices`.

## Tested on

Huawei Mate 10 Pro, Android 10. No other devices tested — UI element IDs, bounds, and timing may differ on other hardware/OS versions.
