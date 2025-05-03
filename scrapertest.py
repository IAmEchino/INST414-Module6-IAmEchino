import requests
import re
import time
import random
import csv
import os
from itertools import product

BASE_URL = "https://www.techpowerup.com"
LIST_URL = f"{BASE_URL}/gpu-specs/"
HEADERS = {
    "User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ])
}

GPU_LINK_REGEX = r'(?:<tr>\s*<td\s.*\s*<a href=\")(/gpu-specs/.*?)(?:\">)'
NAME_REGEX = r'(?:h1 class=\"gpudb-name\">)(.*?)(?:</h1>)'
RELEASE_REGEX = r'<dt>Release Date</dt>\s*<dd>(.+?)</dd>'
TRANSISTOR_REGEX = r'<dt>Transistors</dt>\s*<dd>(.+?)</dd>'

CSV_FILE = "gpu_data_all.csv"

BRANDS = ["NVIDIA", "AMD", "Intel", "ATI", "Apple"]
YEARS = list(range(1986, 2026))
IGP_OPTIONS = ["Yes", "No"]

def fetch(url):
    while True:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                print(f"[!] Received 429 Too Many Requests. Waiting for captcha to be solved. Retrying in 30 seconds...")
                time.sleep(30)
                continue
            else:
                print(f"[!] Status {resp.status_code} for {url}")
                return ""
        except Exception as e:
            print(f"[!] Request failed: {e}")
            return ""

def extract_links(html):
    return re.findall(GPU_LINK_REGEX, html)

def parse_gpu_page(html):
    name = re.search(NAME_REGEX, html)
    release = re.search(RELEASE_REGEX, html)
    transistors = re.search(TRANSISTOR_REGEX, html)
    return (
        name.group(1).strip() if name else "N/A",
        transistors.group(1).strip() if transistors else "N/A",
        release.group(1).strip() if release else "N/A"
    )

def main():
    seen = set()
    total = 0
    combos = list(product(BRANDS, YEARS, IGP_OPTIONS))

    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["GPU Name", "Transistor Count", "Release Date"])

    for brand, year, igp in combos:
        page = 1
        print(f"\n=== {brand} | {year} | IGP: {igp} ===")

        while True:
            url = f"{LIST_URL}?mfgr={brand}&released={year}&igp={igp}&page={page}"
            print(f"[+] Fetching index: {url}")
            html = fetch(url)

            if not html:
                break

            links = extract_links(html)
            if not links:
                no_results_sleep_time = random.uniform(10, 30)
                print(f"    No results found. Sleeping for {no_results_sleep_time} seconds.")
                time.sleep(no_results_sleep_time)
                break

            new_links = [l for l in links if l not in seen]
            if not new_links:
                print("    All links already processed.")
                break

            for path in new_links:
                seen.add(path)
                full_url = BASE_URL + path
                print(f"  - Scraping: {full_url}")
                gpu_html = fetch(full_url)
                if not gpu_html:
                    continue

                try:
                    name, transistors, release = parse_gpu_page(gpu_html)

                    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([name, transistors, release])

                    total += 1
                    print(f"    ✅ {name} | {transistors} | {release}")

                except Exception as e:
                    print(f"    [!] Failed to parse or write: {e}")

                sleep_time = random.uniform(10, 30)
                print(f"    Sleeping {sleep_time:.1f}s...")
                time.sleep(sleep_time)

            index_sleep = random.uniform(10, 30)
            print(f"[~] Sleeping {index_sleep:.1f}s before next page...\n")
            time.sleep(index_sleep)

            page += 1

    print(f"\n✅ Done! {total} entries written to {CSV_FILE}")

if __name__ == "__main__":
    main()