"""SerpApi layer tests. No network: _query or httpx.get is always faked."""
import httpx
import pytest
from fastapi.testclient import TestClient

import search
from main import app

client = TestClient(app)
LOC, ISSUE, AUTH = "Rohini, Delhi", "garbage_accumulation", "Sanitation department"
BODY = {"location": LOC, "issue_type": ISSUE, "authority": AUTH}


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("SERPAPI_KEY", "test-key")
    monkeypatch.setenv("SEARCH_DAILY_LIMIT", "1000")
    search._cache.clear()
    search._usage.update(calls=0)


def hit(link, title="Page", snippet=""):
    return {"link": link, "title": title, "snippet": snippet}


def fake_query(monkeypatch, *replies):
    """Make search._query return the given result lists in order (or raise Exceptions)."""
    seq, queries = list(replies), []

    def _q(q, api_key):
        queries.append(q)
        r = seq.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(search, "_query", _q)
    return queries


# ---------- ranking ----------
def test_official_domain_beats_higher_ranked_non_official(monkeypatch):
    fake_query(monkeypatch, [
        hit("https://www.somenews.com/grievance-portal", "Grievance portal guide"),
        hit("https://mcd.delhi.gov.in/complaint", "File a complaint"),
    ])
    r = search.find_channel(LOC, ISSUE, AUTH)
    assert r.found and r.url == "https://mcd.delhi.gov.in/complaint" and r.bonus == 2
    assert r.source == "mcd.delhi.gov.in"


def test_keywords_beat_result_one(monkeypatch):
    fake_query(monkeypatch, [
        hit("https://delhi.gov.in/about", "About the department", "Report issues here"),
        hit("https://mcd.delhi.gov.in/grievance", "Grievance redressal portal"),
    ])
    assert search.find_channel(LOC, ISSUE, AUTH).url == "https://mcd.delhi.gov.in/grievance"


def test_official_site_without_reporting_words_is_not_enough(monkeypatch):
    fake_query(monkeypatch, [hit("https://delhi.gov.in/history", "History of Delhi")], [])
    r = search.find_channel(LOC, ISSUE, AUTH)
    assert not r.found and r.bonus == 0 and r.url is None


def test_no_official_result_means_no_bonus(monkeypatch):
    fake_query(monkeypatch, [hit("https://blog.example.com/complaint-portal", "Complaint portal")],
               [hit("https://x.org/grievance", "Grievance")])
    r = search.find_channel(LOC, ISSUE, AUTH)
    assert r.found is False and r.bonus == 0 and r.url is None


@pytest.mark.parametrize("url", [
    "https://gov.in.evil.com/grievance",
    "https://notgov.in/grievance",
    "https://evil.com/?u=https://mcd.gov.in/grievance",
    "ftp://mcd.delhi.gov.in/grievance",
    "not a url",
])
def test_lookalike_domains_rejected(url):
    assert search.is_official(url) is False


@pytest.mark.parametrize("url", ["https://mcd.delhi.gov.in/x", "http://pgportal.nic.in/y"])
def test_real_official_domains_accepted(url):
    assert search.is_official(url) is True


# ---------- queries ----------
def test_falls_back_to_simpler_query_when_first_finds_nothing(monkeypatch):
    queries = fake_query(monkeypatch, [], [hit("https://mcd.delhi.gov.in/grievance", "Grievance")])
    assert search.find_channel(LOC, ISSUE, AUTH).found
    assert len(queries) == 2 and "garbage accumulation" in queries[0] and "garbage" not in queries[1]


def test_stops_after_first_query_when_it_works(monkeypatch):
    queries = fake_query(monkeypatch, [hit("https://mcd.delhi.gov.in/grievance", "Grievance")])
    search.find_channel(LOC, ISSUE, AUTH)
    assert len(queries) == 1


# ---------- cache ----------
def test_repeat_lookup_costs_nothing(monkeypatch):
    queries = fake_query(monkeypatch, [hit("https://mcd.delhi.gov.in/grievance", "Grievance")])
    first = search.find_channel(LOC, ISSUE, AUTH)
    again = search.find_channel("  rohini,  DELHI ", "other_issue", "sanitation DEPARTMENT")
    assert first == again and len(queries) == 1


def test_not_found_is_cached_too(monkeypatch):
    queries = fake_query(monkeypatch, [], [])
    search.find_channel(LOC, ISSUE, AUTH)
    search.find_channel(LOC, ISSUE, AUTH)
    assert len(queries) == 2  # both queries of the first lookup, nothing for the second


def test_different_authority_is_a_new_search(monkeypatch):
    queries = fake_query(monkeypatch, [hit("https://a.gov.in/grievance", "Grievance")],
                         [hit("https://b.gov.in/grievance", "Grievance")])
    search.find_channel(LOC, ISSUE, AUTH)
    search.find_channel(LOC, ISSUE, "Road authority")
    assert len(queries) == 2


def test_cache_expires(monkeypatch):
    queries = fake_query(monkeypatch, [hit("https://a.gov.in/grievance", "Grievance")],
                         [hit("https://a.gov.in/grievance", "Grievance")])
    search.find_channel(LOC, ISSUE, AUTH)
    key = search._cache_key(LOC, AUTH)
    expiry, value = search._cache[key]
    search._cache[key] = (0, value)
    search.find_channel(LOC, ISSUE, AUTH)
    assert len(queries) == 2


def test_cache_is_capped(monkeypatch):
    monkeypatch.setattr(search, "CACHE_MAX_ENTRIES", 3)
    for i in range(6):
        search._cache_set((f"loc{i}", "a"), search.FindChannelResponse(found=False))
    assert len(search._cache) == 3


# ---------- failures ----------
def test_failure_is_not_cached(monkeypatch):
    fake_query(monkeypatch, search.SearchUnavailable("boom"))
    with pytest.raises(search.SearchUnavailable):
        search.find_channel(LOC, ISSUE, AUTH)
    assert not search._cache


def test_missing_key(monkeypatch):
    monkeypatch.delenv("SERPAPI_KEY")
    with pytest.raises(search.SearchUnavailable):
        search.find_channel(LOC, ISSUE, AUTH)


def test_daily_limit(monkeypatch):
    monkeypatch.setenv("SEARCH_DAILY_LIMIT", "1")
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, json={"organic_results": []}))
    search._query("one", "k")
    with pytest.raises(search.SearchUnavailable):
        search._query("two", "k")


def test_timeout_becomes_unavailable(monkeypatch):
    def boom(*a, **k):
        raise httpx.ReadTimeout("slow https://serpapi.com/search.json?api_key=SECRET")

    monkeypatch.setattr(httpx, "get", boom)
    with pytest.raises(search.SearchUnavailable):
        search._query("q", "SECRET")


@pytest.mark.parametrize("status", [401, 429, 500])
def test_http_errors_become_unavailable(monkeypatch, status):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(status, json={"error": "x"}))
    with pytest.raises(search.SearchUnavailable):
        search._query("q", "k")


def test_google_no_results_is_empty_not_an_error(monkeypatch):
    body = {"error": "Google hasn't returned any results for this query."}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, json=body))
    assert search._query("q", "k") == []


def test_other_serpapi_error_is_unavailable(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, json={"error": "Invalid API key."}))
    with pytest.raises(search.SearchUnavailable):
        search._query("q", "k")


def test_non_json_response_is_unavailable(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, text="<html>"))
    with pytest.raises(search.SearchUnavailable):
        search._query("q", "k")


# ---------- endpoint ----------
def test_endpoint_found(monkeypatch):
    fake_query(monkeypatch, [hit("https://mcd.delhi.gov.in/grievance", "Grievance portal")])
    r = client.post("/api/find-channel", json=BODY)
    assert r.status_code == 200
    assert r.json() == {"found": True, "title": "Grievance portal",
                        "url": "https://mcd.delhi.gov.in/grievance",
                        "source": "mcd.delhi.gov.in", "bonus": 2}


def test_endpoint_not_found(monkeypatch):
    fake_query(monkeypatch, [], [])
    r = client.post("/api/find-channel", json=BODY)
    assert r.status_code == 200 and r.json()["found"] is False and r.json()["bonus"] == 0


def test_endpoint_503_when_search_is_down(monkeypatch):
    fake_query(monkeypatch, search.SearchUnavailable("down"))
    r = client.post("/api/find-channel", json=BODY)
    assert r.status_code == 503 and "unavailable" in r.json()["detail"].lower()


def test_endpoint_mock_mode_never_calls_search(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")
    fake_query(monkeypatch)  # any call would pop from an empty list and fail
    assert client.post("/api/find-channel", json=BODY).json()["bonus"] == 2
