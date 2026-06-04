# allegro-share-automation

Generates Allegro referral share links by driving the Android app via ADB — no browser, no web scraping.

## Requirements

- Python 3.13+
- `adb` in PATH, device connected and authorized (`adb devices`)
- Tested on: Huawei Mate 10 Pro, Android 10

## Setup

```bash
uv sync
```

## Usage

**HTTP service**

```bash
python app.py
```

```bash
curl -X POST http://localhost:5000/share \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://allegro.pl/oferta/some-item-12345678901"}'
# {"link": "https://..."}
```

Returns `503` if another request is already in progress — retry after a few seconds.

**CLI**

```bash
python main.py https://allegro.pl/oferta/some-item-12345678901
```
