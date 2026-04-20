import os
import re
from datetime import datetime, timezone
from modules.telegram_scraper import scrape_telegram

import requests
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(ENV_PATH)

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT") or ""
GITHUB_HEADERS = dict(BASE_HEADERS)
if GITHUB_TOKEN:
    # Bearer is preferred for PATs; token also works for many setups.
    GITHUB_HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
DEBUG_PII = os.getenv("DEBUG_PII", "1") == "1"

PASTEBIN_KEYWORDS = [
    "aadhaar", "aadhar", "pan card", "pancard", "india leak",
    "upi", "ifsc", "mobile number india", "data breach india"
]

def scrape_pastebin():
    results = []

    pastebin_enabled = os.getenv("PASTEBIN_ENABLED", "false").lower() == "true"
    if not pastebin_enabled:
        print("[Pastebin] Disabled — set PASTEBIN_ENABLED=true in .env when Pro is active")
        return results

    try:
        response = requests.get(
            "https://scrape.pastebin.com/api_scraping.php?limit=250",
            headers=BASE_HEADERS,
            timeout=15
        )

        if response.status_code == 403:
            print("[Pastebin] 403 — IP not whitelisted yet. Whitelist at pastebin.com/doc_scraping_api")
            return results
        elif response.status_code != 200:
            print(f"[Pastebin] Failed: HTTP {response.status_code}")
            return results

        pastes = response.json()
        print(f"[Pastebin] Got {len(pastes)} pastes, filtering by keywords...")

        for paste in pastes:
            paste_key  = paste.get("key", "")
            paste_title = (paste.get("title") or "").lower()
            paste_url  = f"https://pastebin.com/{paste_key}"

            # keyword filter on title first (cheap)
            title_match = any(kw in paste_title for kw in PASTEBIN_KEYWORDS)

            # fetch raw content
            raw = requests.get(
                f"https://scrape.pastebin.com/api_scrape_item.php?i={paste_key}",
                headers=BASE_HEADERS,
                timeout=10
            )

            if raw.status_code != 200:
                continue

            content = raw.text

            # keyword filter on content too
            content_lower = content.lower()
            content_match = any(kw in content_lower for kw in PASTEBIN_KEYWORDS)

            if not title_match and not content_match:
                continue  # skip irrelevant pastes

            results.append({
                "url":         paste_url,
                "source_type": "pastebin",
                "content":     content,
                "fetched_at":  datetime.now(timezone.utc).isoformat()
            })
            print(f"[Pastebin] Matched: {paste_url} | title='{paste.get('title')}'")

    except Exception as e:
        print(f"[Pastebin] Error: {e}")

    return results


def scrape_github_gists():
    results = []

    search_queries = [
        "aadhaar in:file",
        "aadhar in:file",
        "pan card in:file",
        "upi id in:file",
        "ifsc code in:file",
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
                if DEBUG_PII:
                    print(f"[DEBUG][github_search] query='{query}' items={len(items)}")
                for item in items:
                    # Resolve true raw URL via contents API to avoid HTML fetches.
                    api_url = item.get("url", "")
                    raw_url = ""
                    if api_url:
                        file_meta = requests.get(api_url, headers=GITHUB_HEADERS, timeout=10)
                        if file_meta.status_code == 200:
                            raw_url = file_meta.json().get("download_url", "")
                    if not raw_url:
                        continue

                    raw = requests.get(raw_url, headers=BASE_HEADERS, timeout=10)
                    if raw.status_code == 200:
                        if DEBUG_PII:
                            preview = _safe_console(raw.text[:300].replace("\n", "\\n"))
                            is_html = "<html" in raw.text[:1000].lower() or "<!doctype html" in raw.text[:1000].lower()
                            print(f"[DEBUG][github_raw] {raw_url}")
                            print(f"[DEBUG][content_len] {len(raw.text)} html={is_html}")
                            print(f"[DEBUG][content_preview_300] {preview}")
                        results.append({
                            "url":         item.get("html_url"),
                            "source_type": "github_search",
                            "content":     raw.text,
                            "fetched_at":  datetime.now(timezone.utc).isoformat()
                        })
                        print(f"[GitHub Search] Fetched: {item.get('html_url')}")
            elif response.status_code in (401, 403):
                print("[GitHub Search] Unauthorized/rate-limited. Check GITHUB_TOKEN.")
                break
            else:
                print(f"[GitHub Search] Failed for '{query}': {response.status_code}")

    except Exception as e:
        print(f"[GitHub Search] Error: {e}")

    return results


def _extract_first_match(pattern, text):
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _safe_console(text):
    return text.encode("ascii", "replace").decode("ascii")


def scrape_controlc(limit=20):
    results = []

    try:
        resp = requests.get("https://controlc.com/", headers=BASE_HEADERS, timeout=12)
        if resp.status_code != 200:
            print(f"[controlc] Failed index fetch: HTTP {resp.status_code}")
            return results

        # Matches links like /a1b2c3d4 from homepage HTML.
        links = re.findall(r'href="/([a-zA-Z0-9]{8})"', resp.text)
        unique_ids = []
        for pid in links:
            if pid not in unique_ids:
                unique_ids.append(pid)
            if len(unique_ids) >= limit:
                break

        for pid in unique_ids:
            raw_url = f"https://controlc.com/{pid}/raw.php"
            raw_resp = requests.get(raw_url, headers=BASE_HEADERS, timeout=10)
            if raw_resp.status_code != 200 or not raw_resp.text.strip():
                continue
            results.append(
                {
                    "url": f"https://controlc.com/{pid}",
                    "source_type": "controlc",
                    "content": raw_resp.text,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            print(f"[controlc] Fetched: https://controlc.com/{pid}")
    except Exception as e:
        print(f"[controlc] Error: {e}")

    return results


def scrape_paste_fo(limit=20):
    results = []

    try:
        resp = requests.get("https://paste.fo/recent", headers=BASE_HEADERS, timeout=12)
        if resp.status_code != 200:
            print(f"[paste.fo] Failed index fetch: HTTP {resp.status_code}")
            return results

        # Common link format: /<id>, where id is hex-ish, length 6-16
        candidate_ids = re.findall(r'href="/([a-fA-F0-9]{6,16})"', resp.text)
        unique_ids = []
        for pid in candidate_ids:
            if pid not in unique_ids:
                unique_ids.append(pid)
            if len(unique_ids) >= limit:
                break

        for pid in unique_ids:
            page_url = f"https://paste.fo/{pid}"
            page_resp = requests.get(page_url, headers=BASE_HEADERS, timeout=10)
            if page_resp.status_code != 200:
                continue

            # Try known textarea/JS embeddings for raw paste content.
            content = _extract_first_match(
                r'<textarea[^>]*id="paste-content"[^>]*>(.*?)</textarea>',
                page_resp.text,
            )
            if content is None:
                content = _extract_first_match(
                    r'"rawText"\s*:\s*"(.*?)"\s*,',
                    page_resp.text,
                )
                if content:
                    content = content.encode("utf-8").decode("unicode_escape")

            if not content or not content.strip():
                continue

            results.append(
                {
                    "url": page_url,
                    "source_type": "paste_fo",
                    "content": content,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            print(f"[paste.fo] Fetched: {page_url}")
    except Exception as e:
        print(f"[paste.fo] Error: {e}")

    return results


def run_scraper():
    print("\n-- Starting Scrape --")
    all_results = []
    all_results.extend(scrape_github_gists())
    all_results.extend(scrape_pastebin())
    all_results.extend(scrape_controlc())
    all_results.extend(scrape_paste_fo())
    all_results.extend(scrape_telegram())
    print(f"-- Done: {len(all_results)} sources fetched --\n")
    return all_results


if __name__ == "__main__":
    results = run_scraper()
    print(f"\nTotal fetched: {len(results)}")
    for r in results[:3]:
        print(f"  [{r['source_type']}] {r['url']}")
        print(f"  Content preview: {r['content'][:100]}\n")