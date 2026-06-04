import argparse
import subprocess
import time
import xml.etree.ElementTree as ET
import re
import sys
from urllib.parse import urlparse, parse_qs


ALLEGRO_PACKAGE = "pl.allegro"
DUMP_PATH_DEVICE = "/sdcard/ui.xml"
DUMP_PATH_LOCAL = "/tmp/ui.xml"


def adb(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["adb", "shell"] + args, capture_output=True, text=True, check=check
    )


def adb_host(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["adb"] + args, capture_output=True, text=True, check=True)


def dump_ui() -> ET.Element:
    adb(["uiautomator", "dump", DUMP_PATH_DEVICE])
    adb_host(["pull", DUMP_PATH_DEVICE, DUMP_PATH_LOCAL])
    return ET.parse(DUMP_PATH_LOCAL).getroot()


def find_node(
    root: ET.Element, content_desc: str | None = None, text: str | None = None
) -> ET.Element | None:
    for node in root.iter("node"):
        if content_desc and node.attrib.get("content-desc") == content_desc:
            return node
        if text and node.attrib.get("text") == text:
            return node
    return None


def tap_node(node: ET.Element) -> None:
    bounds = node.attrib["bounds"]
    # Parse "[x1,y1][x2,y2]"
    coords = list(map(int, re.findall(r"\d+", bounds)))
    x = (coords[0] + coords[2]) // 2
    y = (coords[1] + coords[3]) // 2
    adb(["input", "tap", str(x), str(y)])


def tap_bounds(bounds_str: str) -> None:
    coords = list(map(int, re.findall(r"\d+", bounds_str)))
    x = (coords[0] + coords[2]) // 2
    y = (coords[1] + coords[3]) // 2
    adb(["input", "tap", str(x), str(y)])


def get_clipboard() -> str:
    adb(["input", "keyevent", "KEYCODE_BACK"])
    time.sleep(1.5)

    adb(["input", "tap", "468", "156"])
    time.sleep(1.5)

    # Android-native paste keyevent (not Ctrl+V)
    adb(["input", "keyevent", "279"])  # KEYCODE_PASTE = 279
    time.sleep(0.5)

    root = dump_ui()
    for node in root.iter("node"):
        if node.attrib.get("resource-id") == "pl.allegro:id/searchBox":
            text = node.attrib.get("text", "")
            if "allegro.pl" in text:
                return text.rstrip("#")

    return ""


def ensure_allegro_closed() -> None:
    adb(["am", "force-stop", ALLEGRO_PACKAGE])
    time.sleep(1)


def extract_offer_id(url: str) -> str:
    # Handle /oferta/slug-ID and /produkt/slug-ID?offerId=ID formats
    path = urlparse(url).path

    # /oferta/some-slug-12345678901
    match = re.search(r"-(\d{10,})$", path)
    if match:
        return match.group(1)

    # /produkt/... with ?offerId=
    qs = parse_qs(urlparse(url).query)
    if "offerId" in qs:
        return qs["offerId"][0]

    raise ValueError(f"Cannot extract offer ID from URL: {url}")


def open_offer(url: str) -> None:
    offer_id = extract_offer_id(url)
    clean_url = f"https://allegro.pl/oferta/{offer_id}"
    adb(
        [
            "am",
            "start",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            clean_url,
            ALLEGRO_PACKAGE,
        ]
    )


def wait_for_element(
    content_desc: str = None, text: str = None, timeout: int = 15
) -> ET.Element | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(1.5)
        root = dump_ui()
        node = find_node(root, content_desc=content_desc, text=text)
        if node is not None:
            return node
    return None


def generate_share_link(offer_url: str) -> str:
    print(f"[1/5] Opening offer: {offer_url}")
    ensure_allegro_closed()
    open_offer(offer_url)

    print("[2/5] Waiting for offer page to load...")
    share_btn = wait_for_element(content_desc="Udostępnij", timeout=20)
    if share_btn is None:
        raise RuntimeError("Offer page did not load or 'Udostępnij' button not found")

    print("[3/5] Tapping 'Udostępnij'...")
    # Tap the clickable parent of the 'Udostępnij' icon
    tap_node(share_btn.find("..") or share_btn)
    time.sleep(2)

    print("[4/5] Waiting for Share bottom sheet...")
    root = dump_ui()
    copy_btn = find_node(root, text="Kopiuj link polecający")
    if copy_btn is None:
        raise RuntimeError(
            "Share bottom sheet did not appear or 'Kopiuj link polecający' not found"
        )

    print("[5/5] Tapping 'Kopiuj link polecający'...")
    tap_node(copy_btn)
    time.sleep(1.5)

    link = get_clipboard()
    if not link:
        raise RuntimeError("Clipboard is empty — link was not copied")

    ensure_allegro_closed()
    return link


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Allegro referral share link via ADB"
    )
    parser.add_argument("url", help="Allegro offer URL")
    args = parser.parse_args()

    try:
        link = generate_share_link(args.url)
        print(f"\nShare link: {link}")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
