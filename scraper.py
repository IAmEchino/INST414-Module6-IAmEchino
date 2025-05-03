import requests
import re
import time
import random
import csv
import os

BASE_URL = "https://www.techpowerup.com"
LIST_URL = f"{BASE_URL}/gpu-specs/"
HEADERS = {
    "User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ])
}

# Your regex patterns
GPU_LINK_REGEX = r'(?:<tr>\s*<td\s.*\s*<a href=\")(/gpu-specs/.*?)(?:\">)'
NAME_REGEX = r'(?:h1 class=\"gpudb-name\">)(.*)(?:</h1>)'
RELEASE_REGEX = r'<dt>Release Date</dt>\s*<dd>(.+?)</dd>'
TRANSISTOR_REGEX = r'<dt>Transistors</dt>\s*<dd>(.+?)</dd>'

# Output file
CSV_FILE = "gpu_data.csv"

def fetch(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.text
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
    page = 1
    total_found = 0

    # Open CSV early and append rows as we go
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["GPU Name", "Transistor Count", "Release Date"])

        while True:
            list_url = f"{LIST_URL}?sort=name&page={page}"
            print(f"\n[+] Fetching index page {page}")
            html = fetch(list_url)
            if not html:
                break

            links = extract_links(html)
            if not links:
                print("[!] No links found, ending pagination.")
                break

            new_links = [l for l in links if l not in seen]
            if not new_links:
                print("[!] All links seen already.")
                break

            for path in new_links:
                full_url = BASE_URL + path
                seen.add(path)
                print(f"  - Scraping: {full_url}")
                gpu_html = fetch(full_url)
                if not gpu_html:
                    continue
                name, transistors, release = parse_gpu_page(gpu_html)
                writer.writerow([name, transistors, release])
                f.flush()
                total_found += 1

                sleep_time = random.uniform(10.0, 20.0)
                print(f"    Sleeping {sleep_time:.1f}s...")
                time.sleep(sleep_time)

            page += 1

    print(f"\n✅ Done! {total_found} entries written to {CSV_FILE}")

if __name__ == "__main__":
    main()
