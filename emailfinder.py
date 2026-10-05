"""
emailfinder.py - free, no-API-key lead + email discovery.

1. osm_leads(city, state, queries)  -> businesses from OpenStreetMap (free)
2. find_emails(website)             -> public contact emails crawled from the
                                       business's own website (free, unlimited)
3. find_for_many(leads)             -> runs the crawler in parallel

Only reads publicly listed business contact addresses and respects robots.txt.
Install: pip install requests dnspython
"""
import re, html, socket, time
import concurrent.futures as cf
from urllib.parse import urljoin, urlparse
from urllib import robotparser
import requests

try:
    import dns.resolver  # optional, for MX validation
except ImportError:
    dns = None

UA = "Mozilla/5.0 (compatible; StockistBot/1.0)"
HEADERS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.[a-zA-Z]{2,}")
BAD_END = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".woff", ".woff2")
BAD_PARTS = ("sentry", "wixpress", "example.", "domain.com", "yourname", "email.com",
             "@2x", "godaddy", "yourdomain", "name@", "user@", "noreply", "no-reply")
PREFERRED = ("info", "hello", "contact", "sales", "orders", "shop", "store", "support", "wholesale")
CONTACT_HINTS = ("contact", "about", "reach", "connect", "team", "wholesale", "trade", "stockist", "customer")
COMMON_PATHS = ("/contact", "/contact-us", "/about", "/about-us", "/pages/contact", "/wholesale")

_robots_cache = {}


def _allowed(url):
    root = "{0.scheme}://{0.netloc}".format(urlparse(url))
    rp = _robots_cache.get(root)
    if rp is None:
        rp = robotparser.RobotFileParser()
        try:
            r = requests.get(root + "/robots.txt", headers=HEADERS, timeout=5)
            rp.parse(r.text.splitlines() if r.ok else [])
        except Exception:
            rp.parse([])
        _robots_cache[root] = rp
    return rp.can_fetch(UA, url)


def _get(url, timeout=8):
    if not _allowed(url):
        return ""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.ok and "text/html" in r.headers.get("content-type", "text/html"):
            return r.text[:600_000]
    except Exception:
        pass
    return ""


def _decode_cf(hexstr):
    """Decode Cloudflare's 'email protection' obfuscation."""
    try:
        key = int(hexstr[:2], 16)
        return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))
    except Exception:
        return ""


def _clean(e):
    e = e.strip().strip(".,;:()<>[]\"'").lower()
    if not EMAIL_RE.fullmatch(e) or e.endswith(BAD_END) or any(b in e for b in BAD_PARTS):
        return None
    return e


def extract_emails(page):
    found = set()
    for h in re.findall(r'data-cfemail="([0-9a-fA-F]+)"', page):
        found.add(_decode_cf(h))
    text = html.unescape(page)
    text = re.sub(r"\s*[\[\(]\s*at\s*[\]\)]\s*", "@", text, flags=re.I)
    text = re.sub(r"\s*[\[\(]\s*dot\s*[\]\)]\s*", ".", text, flags=re.I)
    found.update(re.findall(r"mailto:([^\"'?\s>]+)", text, flags=re.I))
    found.update(EMAIL_RE.findall(text))
    return {c for c in (_clean(e) for e in found) if c}


def _has_mx(domain):
    try:
        if dns:
            return bool(dns.resolver.resolve(domain, "MX", lifetime=4))
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False


def _site_domain(url):
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _score(email, site_domain):
    local, _, dom = email.partition("@")
    s = 0
    if dom == site_domain or site_domain.endswith("." + dom) or dom.endswith("." + site_domain):
        s += 3
    if local in PREFERRED:
        s += 2
    if dom in ("gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"):
        s += 1  # small shops often use these; keep but rank lower
    return s


def find_emails(website, max_pages=6):
    """Return ranked list of {'email','score','mx'} for one website."""
    if not website:
        return []
    if not website.startswith("http"):
        website = "https://" + website
    domain = _site_domain(website)
    seen, emails = set(), set()

    home = _get(website)
    if not home:
        return []
    seen.add(website.rstrip("/"))
    emails |= extract_emails(home)

    # candidate pages: links on the homepage that look like contact/about, then common paths
    cands = []
    for href in re.findall(r'href=["\']([^"\'#]+)', home, flags=re.I):
        if any(k in href.lower() for k in CONTACT_HINTS):
            cands.append(urljoin(website, href))
    cands += [urljoin(website, p) for p in COMMON_PATHS]

    pages = 1
    for url in cands:
        u = url.rstrip("/")
        if u in seen or urlparse(url).netloc.lower().lstrip("www.") != domain or pages >= max_pages:
            continue
        seen.add(u)
        emails |= extract_emails(_get(url))
        pages += 1
        if any(_score(e, domain) >= 5 for e in emails):
            break  # good enough, stop crawling

    out = []
    for e in emails:
        mx = _has_mx(e.split("@")[1])
        if mx:
            out.append({"email": e, "score": _score(e, domain), "mx": True})
    return sorted(out, key=lambda d: -d["score"])

SHOP_TAGS = "interior_decoration|furniture|houseware|gift|antiques|lighting|garden_centre|kitchen|bed|carpet|curtain"

def osm_leads(city, state, limit=40):
    """Find home-decor-type shops in a US city using free OpenStreetMap data."""

    # Find city coordinates using Nominatim
    try:
        g_response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{city}, {state}, USA",
                "format": "json",
                "limit": 1
            },
            headers={
                "User-Agent": "StockistApp/1.0"
            },
            timeout=15
        )

        g_response.raise_for_status()
        g = g_response.json()

    except requests.RequestException as e:
        raise RuntimeError(f"Location search failed: {e}")
    except ValueError:
        raise RuntimeError(
            "OpenStreetMap returned an invalid response."
        )

    if not g:
        return []

    lat = float(g[0]["lat"])
    lon = float(g[0]["lon"])

    # Smaller radius = much faster Overpass query
    q = (
        f'[out:json][timeout:20];'
        f'nwr(around:10000,{lat},{lon})'
        f'["shop"~"^({SHOP_TAGS})$"];'
        f'out center tags {limit};'
    )

    # Try multiple Overpass servers
    servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"
    ]

    data = None
    last_error = None

    for server in servers:
        try:
            print(f"Trying Overpass server: {server}")

            response = requests.post(
                server,
                data={"data": q},
                headers={
                    "User-Agent": "StockistApp/1.0",
                    "Accept": "application/json"
                },
                timeout=30
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "content-type", ""
            ).lower()

            if "json" not in content_type:
                raise RuntimeError(
                    f"Server returned {content_type or 'unknown content type'}"
                )

            data = response.json()

            print(
                f"Overpass search successful: "
                f"{len(data.get('elements', []))} results"
            )

            break

        except (requests.RequestException, ValueError, RuntimeError) as e:
            print(f"Overpass server failed: {e}")
            last_error = e
            continue

    if data is None:
        raise RuntimeError(
            f"OpenStreetMap search service is temporarily unavailable: "
            f"{last_error}"
        )

    # Convert OSM results into Stockist leads
    leads = []

    for el in data.get("elements", []):
        t = el.get("tags", {})

        if not t.get("name"):
            continue

        leads.append({
            "name": t["name"],
            "type": t.get("shop"),
            "website": (
                t.get("website")
                or t.get("contact:website")
            ),
            "phone": (
                t.get("phone")
                or t.get("contact:phone")
            ),
            "osm_email": (
                t.get("email")
                or t.get("contact:email")
            ),
            "address": " ".join(
                filter(
                    None,
                    [
                        t.get("addr:housenumber"),
                        t.get("addr:street"),
                        t.get("addr:city") or city,
                        t.get("addr:state") or state
                    ]
                )
            )
        })

    return leads
if __name__ == "__main__":
    leads = osm_leads("Austin", "TX")
    for l in find_for_many([x for x in leads if x["website"] or x["osm_email"]][:10]):
        print(l["name"], "->", l["email"])
