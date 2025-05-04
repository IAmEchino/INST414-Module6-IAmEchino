import requests
import re
import time
import random
import csv
import os
from itertools import product

BASE_URL = "https://www.techpowerup.com"
LIST_URL = f"{BASE_URL}/gpu-specs/"

GPU_LINK_REGEX = r'(?:<tr>\s*<td\s.*\s*<a href=\")(/gpu-specs/.*?)(?:\">)'
NAME_REGEX = r'(?:h1 class=\"gpudb-name\">)(.*?)(?:</h1>)'
RELEASE_REGEX = r'<dt>Release Date</dt>\s*<dd>(.+?)</dd>'
TRANSISTOR_REGEX = r'<dt>Transistors</dt>\s*<dd>(.+?)</dd>'

CSV_FILE = "gpu_data_all.csv"

BRANDS = ["NVIDIA"] #, "AMD", "Intel", "ATI", "Apple"]
YEARS = list(range(2002, 2025))
IGP_OPTIONS = ["Yes", "No"]
RETRY_DELAY_MULTIPLIER = 2 # Multiplier for exponential backoff, applied to all errors

def fetch(url):
    """
    Fetches the content of a URL with retry logic and exponential backoff.
    Retries indefinitely until successful.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The content of the URL, or an empty string on unrecoverable failure.
    """
    retries = 0
    while True: # Retry indefinitely
        try:
            HEADERS = {
    "User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.61 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.2478.51",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.2478.51",
    ])
}
            resp = requests.get(url, HEADERS, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.HTTPError as e:
            retries += 1
            delay = (RETRY_DELAY_MULTIPLIER ** retries) + random.uniform(15, 45)
            print(f"[!] HTTP error {resp.status_code} for {url}: {e}. Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
        except requests.exceptions.RequestException as e:
            retries += 1
            delay = (RETRY_DELAY_MULTIPLIER ** retries) + random.uniform(15, 45)
            print(f"[!] Request failed: {e}. Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
        except Exception as e:
            # Catch any other unexpected exceptions.  Consider logging this.
            print(f"[!] An unexpected error occurred: {e}.  Check the code.  Retrying in 60 seconds.")
            time.sleep(60) # A longer delay for unexpected errors.
            retries += 1 # Still increment retries to avoid infinite loop in extreme cases.

def extract_links(html):
    """Extracts GPU links from the HTML content.

    Args:
        html (str): The HTML content to parse.

    Returns:
        list: A list of GPU links.
    """
    return re.findall(GPU_LINK_REGEX, html)

def parse_gpu_page(html):
    """Parses the GPU details page.

    Args:
        html (str): The HTML content of the GPU details page.

    Returns:
        tuple: A tuple containing the GPU name, transistor count, and release date.
               Returns ("N/A", "N/A", "N/A") if parsing fails.
    """
    try:
        name_match = re.search(NAME_REGEX, html)
        release_match = re.search(RELEASE_REGEX, html)
        transistors_match = re.search(TRANSISTOR_REGEX, html)

        name = name_match.group(1).strip() if name_match else "N/A"
        transistors = transistors_match.group(1).strip() if transistors_match else "N/A"
        release = release_match.group(1).strip() if release_match else "N/A"

        return name, transistors, release
    except Exception as e:
        print(f"[!] Error parsing GPU page: {e}")
        return "N/A", "N/A", "N/A"

def main():
    """Main function to orchestrate the web scraping process."""
    seen = set()
    total = 0
    combos = list(product(BRANDS, YEARS, IGP_OPTIONS))

    # Check if the CSV file exists; create it with headers if it doesn't.
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
                print("  [!] Failed to fetch index page.  Moving to next brand/year/igp combination.")
                break

            links = extract_links(html)
            if not links:
                print("  [!] No results found.")
                break

            new_links = [l for l in links if l not in seen]
            if not new_links:
                print("  [!] All links already processed.")
                break

            for path in new_links:
                seen.add(path)
                full_url = BASE_URL + path
                print(f"  - Scraping: {full_url}")
                gpu_html = fetch(full_url)
                if not gpu_html:
                    print("  [!] Failed to fetch GPU details page. Skipping this GPU.")
                    continue

                name, transistors, release = parse_gpu_page(gpu_html)

                try:
                    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([name, transistors, release])
                    total += 1
                    print(f"    ✅ {name} | {transistors} | {release}")
                except Exception as e:
                    print(f"    [!] Failed to write to CSV: {e}")

                sleep_time = random.uniform(15, 45)
                print(f"    Sleeping {sleep_time:.1f}s...")
                time.sleep(sleep_time)

            index_sleep = random.uniform(20, 60)
            print(f"[~] Sleeping {index_sleep:.1f}s before next page...\n")
            time.sleep(index_sleep)
            page += 1

    print(f"\n✅ Done! {total} entries written to {CSV_FILE}")

if __name__ == "__main__":
    main()