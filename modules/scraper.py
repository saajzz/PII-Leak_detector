import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

GITHUB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Authorization": f"token {GITHUB_TOKEN}"
}

# ── PASTEBIN ────────────────────────────────────────────────────
def scrape_pastebin():
    results = []

    try:
        # get recent public pastes
        response = requests.get(
            "https://scrape.pastebin.com/api_scraping.php?limit=20",
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            print(f"[Pastebin] Failed: HTTP {response.status_code}")
            return results

        pastes = response.json()

        for paste in pastes:
            paste_key = paste.get("key")
            paste_url = f"https://pastebin.com/{paste_key}"

            # fetch raw content
            raw = requests.get(
                f"https://pastebin.com/raw/{paste_key}",
                headers=HEADERS,
                timeout=10
            )

            if raw.status_code == 200:
                results.append({
                    "url":         paste_url,
                    "source_type": "pastebin",
                    "content":     raw.text,
                    "fetched_at":  datetime.now(timezone.utc).isoformat()
                })
                print(f"[Pastebin] Fetched: {paste_url}")

    except Exception as e:
        print(f"[Pastebin] Error: {e}")

    return results


# ── GITHUB GIST ─────────────────────────────────────────────────
def scrape_github_gists():
    results = []

    # search terms likely to appear near Indian PII leaks
    search_queries = [
        "aadhaar leaked",
        "pan card dump",
        "india data breach",
        "aadhar number list",
    ]

    try:
        for query in search_queries:
            response = requests.get(
                "https://api.github.com/search/code",
                params={"q": query, "per_page": 5},
                headers=GITHUB_HEADERS,
                timeout=10
            )

            if response.status_code == 200:
                items = response.json().get("items", [])
                for item in items:
                    raw_url = item.get("html_url", "").replace(
                        "github.com", "raw.githubusercontent.com"
                    ).replace("/blob/", "/")

                    raw = requests.get(raw_url, headers=HEADERS, timeout=10)
                    if raw.status_code == 200:
                        results.append({
                            "url":         item.get("html_url"),
                            "source_type": "github_search",
                            "content":     raw.text,
                            "fetched_at":  datetime.now(timezone.utc).isoformat()
                        })
                        print(f"[GitHub Search] Fetched: {item.get('html_url')}")
            else:
                print(f"[GitHub Search] Failed for '{query}': {response.status_code}")

    except Exception as e:
        print(f"[GitHub Search] Error: {e}")

    return results
# ── COMBINED SCRAPE ──────────────────────────────────────────────
def run_scraper():
    print("\n── Starting Scrape ──")
    all_results = []
    all_results.extend(scrape_github_gists())
    all_results.extend(scrape_pastebin())
    print(f"── Done: {len(all_results)} sources fetched ──\n")
    return all_results


# ── TEST ────────────────────────────────────────────────────────
if __name__ == "__main__":
    results = run_scraper()
    print(f"\nTotal fetched: {len(results)}")
    for r in results[:3]:
        print(f"  [{r['source_type']}] {r['url']}")
        print(f"  Content preview: {r['content'][:100]}\n")