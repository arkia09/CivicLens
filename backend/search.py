"""Finds an official reporting page for a complaint using SerpApi.
SerpApi calls only happen from /api/find-channel, which the frontend calls only when the
user taps the button. Results are cached in memory, and a daily cap protects the quota.
"""
import logging
import os
import threading
import time
from datetime import date
from urllib.parse import urlparse

import httpx

from models import FindChannelResponse
from utils import BONUS_CHANNEL_FOUND

log = logging.getLogger("civic-lens.search")

SERPAPI_URL = "https://serpapi.com/search.json"
# httpx applies each number per phase, so a single 30 s value could stack to ~60 s.
# Fail fast per phase and cap the whole lookup with a deadline.
HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=12.0, write=5.0, pool=5.0)
TOTAL_BUDGET_SECONDS = 20  # no second query is started after this much time has passed
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")
KEYWORDS = ("grievance", "complaint", "report", "portal", "redressal", "helpline")
CACHE_MAX_ENTRIES = 500


class SearchUnavailable(Exception):
    """No key, quota used up, timeout, or SerpApi error. Never cached."""


# ---------- cache and quota (in memory, reset on restart) ----------
_lock = threading.Lock()
_cache: dict[tuple[str, str], tuple[float, FindChannelResponse]] = {}
_usage = {"day": date.today(), "calls": 0}


def _cache_key(location: str, authority: str) -> tuple[str, str]:
    return " ".join(location.lower().split()), " ".join(authority.lower().split())


def _cache_get(key: tuple[str, str]) -> FindChannelResponse | None:
    with _lock:
        entry = _cache.get(key)
        if entry and entry[0] > time.time():
            return entry[1]
        _cache.pop(key, None)
        return None


def _cache_set(key: tuple[str, str], value: FindChannelResponse) -> None:
    ttl = int(os.getenv("SEARCH_CACHE_HOURS", "24")) * 3600
    now = time.time()
    with _lock:
        if len(_cache) >= CACHE_MAX_ENTRIES:
            for k in [k for k, (exp, _) in _cache.items() if exp <= now]:
                del _cache[k]
        if len(_cache) >= CACHE_MAX_ENTRIES:
            del _cache[next(iter(_cache))]  # oldest entry
        _cache[key] = (now + ttl, value)


def _spend_call() -> None:
    """Count one SerpApi call against the daily cap."""
    limit = int(os.getenv("SEARCH_DAILY_LIMIT", "50"))
    with _lock:
        today = date.today()
        if _usage["day"] != today:
            _usage["day"], _usage["calls"] = today, 0
        if _usage["calls"] >= limit:
            raise SearchUnavailable("daily search limit reached")
        _usage["calls"] += 1


# ---------- SerpApi ----------
def _query(q: str, api_key: str) -> list[dict]:
    """One SerpApi call. Returns organic results ([] when Google has nothing)."""
    _spend_call()
    params = {"engine": "google_light", "q": q, "gl": "in", "hl": "en", "api_key": api_key}
    started = time.monotonic()
    try:
        resp = httpx.get(SERPAPI_URL, params=params, timeout=HTTP_TIMEOUT)
    except httpx.HTTPError as e:
        # Log only the class: httpx messages can contain the URL, which contains the key.
        log.warning("SerpApi request failed after %.1fs: %s", time.monotonic() - started, type(e).__name__)
        raise SearchUnavailable("request failed") from e
    log.info("SerpApi call took %.1fs (HTTP %s) for query: %.80s", time.monotonic() - started, resp.status_code, q)

    if resp.status_code != 200:
        log.warning("SerpApi returned HTTP %s", resp.status_code)
        raise SearchUnavailable(f"HTTP {resp.status_code}")
    try:
        data = resp.json()
    except ValueError as e:
        raise SearchUnavailable("unreadable response") from e

    error = str(data.get("error") or "")
    if error:
        if "any results" in error.lower():  # "Google hasn't returned any results for this query."
            return []
        log.warning("SerpApi error: %.120s", error)
        raise SearchUnavailable("SerpApi error")
    return data.get("organic_results") or []


def is_official(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and host.endswith(OFFICIAL_SUFFIXES)


def _keyword_hits(text: str) -> int:
    text = text.lower()
    return sum(1 for k in KEYWORDS if k in text)


def pick_best(results: list[dict]) -> dict | None:
    """Best official result that looks like a reporting page, or None. Not just result #1."""
    best, best_rank = None, None
    for pos, r in enumerate(results):
        url = r.get("link") or ""
        if not is_official(url):
            continue
        title_hits = _keyword_hits(r.get("title") or "")
        other_hits = _keyword_hits(f"{r.get('snippet') or ''} {url}")
        if title_hits + other_hits == 0:
            continue  # official site, but nothing says "report here"
        rank = (2 * title_hits + other_hits, -pos)  # more keywords first, then earlier position
        if best_rank is None or rank > best_rank:
            best, best_rank = r, rank
    return best


def build_queries(location: str, issue_type: str, authority: str) -> list[str]:
    issue = issue_type.replace("_", " ")
    detailed = f"{location} {authority} {issue} complaint grievance portal"
    simple = f"{location} {authority} grievance portal"
    return [detailed, simple]


def find_channel(location: str, issue_type: str, authority: str) -> FindChannelResponse:
    key = _cache_key(location, authority)
    cached = _cache_get(key)
    if cached:
        return cached

    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        log.error("SERPAPI_KEY is not set: reporting-page search is disabled")
        raise SearchUnavailable("SERPAPI_KEY is not set")

    hit = None
    started = time.monotonic()
    for i, q in enumerate(build_queries(location, issue_type, authority)):
        if i > 0 and time.monotonic() - started > TOTAL_BUDGET_SECONDS:
            log.warning("Skipping retry query: lookup already took over %ss", TOTAL_BUDGET_SECONDS)
            break
        hit = pick_best(_query(q, api_key))
        if hit:
            break
    log.info("find_channel finished in %.1fs, found=%s", time.monotonic() - started, bool(hit))

    if hit:
        url = hit["link"]
        result = FindChannelResponse(
            found=True,
            title=(hit.get("title") or "Official reporting page")[:150],
            url=url,
            source=urlparse(url).hostname,
            bonus=BONUS_CHANNEL_FOUND,
        )
    else:
        result = FindChannelResponse(found=False, bonus=0)

    _cache_set(key, result)
    return result
