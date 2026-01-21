import os
import time
import uuid
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

from db import images_col

# =========================
# CONFIG
# =========================
RAW_DIR = Path("data/raw_images")
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

SEARCH_QUERIES = [
    "Vietnam traffic sign",
    "road sign Vietnam",
    "traffic warning sign Vietnam",
    "traffic prohibition sign Vietnam",
]

MAX_IMAGES_PER_QUERY = 20
REQUEST_DELAY = 1.5


# =========================
# UTILS
# =========================
def generate_filename(ext=".jpg"):
    return f"img_{int(time.time())}_{uuid.uuid4().hex[:6]}{ext}"


def save_image(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()

        if len(r.content) < 10_000:  # bỏ ảnh quá nhỏ
            return False

        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"

        filename = generate_filename(ext)
        save_path = RAW_DIR / filename

        with open(save_path, "wb") as f:
            f.write(r.content)

        images_col.insert_one({
            "filename": filename,
            "raw_path": str(save_path),
            "source_url": url,
            "source": "web_scraping",
            "stage": "raw",
            "created_at": datetime.utcnow()
        })

        print(f"✔ Saved {filename}")
        return True

    except Exception as e:
        print(f"✘ Failed {url}: {e}")
        return False


# =========================
# 1. COLLECT FROM LOCAL SEED
# =========================
def collect_from_local_seed():
    count = 0
    for f in RAW_DIR.iterdir():
        if f.suffix.lower() not in [".jpg", ".png", ".jpeg"]:
            continue

        if images_col.find_one({"filename": f.name}):
            continue

        images_col.insert_one({
            "filename": f.name,
            "raw_path": str(f),
            "source": "manual_seed",
            "stage": "raw",
            "created_at": datetime.utcnow()
        })
        count += 1

    if count > 0:
        print(f"✔ Indexed {count} local seed images")


# =========================
# 2. IMAGE SCRAPING (BING HTML)
# =========================
def scrape_images():
    for query in SEARCH_QUERIES:
        print(f"\n🔍 Searching: {query}")

        search_url = f"https://www.bing.com/images/search?q={query.replace(' ', '+')}"
        try:
            r = requests.get(search_url, headers=HEADERS, timeout=10)
            r.raise_for_status()
        except Exception as e:
            print(f"✘ Search failed [{query}]: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        img_tags = soup.find_all("img")

        saved = 0
        for img in img_tags:
            if saved >= MAX_IMAGES_PER_QUERY:
                break

            img_url = img.get("src") or img.get("data-src")
            if not img_url:
                continue
            if not img_url.startswith("http"):
                continue

            if save_image(img_url):
                saved += 1
                time.sleep(REQUEST_DELAY)

        print(f"✔ Collected {saved} images for [{query}]")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("🚀 START COLLECT DATA")

    collect_from_local_seed()
    scrape_images()

    print("\n🎉 Data collected (raw, unlabeled)")
