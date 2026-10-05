import os, ssl, json, time, threading, smtplib, requests
from email.message import EmailMessage
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from emailfinder import osm_leads, find_emails

load_dotenv()
app = Flask(__name__, static_folder="static", static_url_path="")

G = os.getenv("GOOGLE_PLACES_KEY", "").strip()
H = os.getenv("HUNTER_KEY", "").strip()
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_NAME = os.getenv("SENDER_NAME", "")
POSTAL = os.getenv("POSTAL_ADDRESS", "")


DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
_lock = threading.Lock()


def _load():
    try:
        with open(DB) as f:
            return json.load(f)
    except Exception:
        return {"searches": [], "sends": []}


def log(kind, row):
    with _lock:
        d = _load()
        row["t"] = int(time.time())
        d[kind].append(row)
        with open(DB, "w") as f:
            json.dump(d, f)


@app.post("/api/found")
def found():
    n = request.get_json(force=True).get("n", 0)
    with _lock:
        d = _load()
        if d["searches"]:
            d["searches"][-1]["with_email"] = n
            with open(DB, "w") as f:
                json.dump(d, f)
    return jsonify(ok=True)


@app.get("/api/stats")
def stats():
    d = _load(); s = d["sends"]; day = 86400; today = int(time.time()) // day
    daily = [sum(1 for x in s if x["ok"] and x["t"] // day == today - i) for i in range(6, -1, -1)]
    return jsonify(searches=len(d["searches"]), leads=sum(x["count"] for x in d["searches"]),
                   emails=sum(x.get("with_email", 0) for x in d["searches"]),
                   sent=sum(1 for x in s if x["ok"]), failed=sum(1 for x in s if not x["ok"]),
                   daily=daily, recent=s[-8:][::-1], recent_searches=d["searches"][-5:][::-1])


@app.get("/")
def home():
    return app.send_static_file("index.html")


@app.get("/api/status")
def status():
    return jsonify(places=bool(G), hunter=bool(H), mail=bool(SMTP_USER and SMTP_PASS),
                   sender=SMTP_USER)


def google_leads(types, city, state):
    out, seen = [], set()
    mask = ("places.id,places.displayName,places.formattedAddress,"
            "places.nationalPhoneNumber,places.websiteUri,places.rating")
    for t in types or ["home decor store"]:
        r = requests.post("https://places.googleapis.com/v1/places:searchText",
                          headers={"X-Goog-Api-Key": G, "X-Goog-FieldMask": mask},
                          json={"textQuery": f"{t} in {city}, {state}, USA", "pageSize": 20},
                          timeout=20)
        for p in r.json().get("places", []):
            if p["id"] in seen:
                continue
            seen.add(p["id"])
            out.append({"name": p["displayName"]["text"], "type": t,
                        "address": p.get("formattedAddress", ""),
                        "phone": p.get("nationalPhoneNumber"),
                        "website": p.get("websiteUri"), "rating": p.get("rating")})
    return out


@app.post("/api/search")
def search():
    d = request.get_json(force=True)
    city, state = d.get("city", "").strip(), d.get("state", "").strip()
    if not city or not state:
        return jsonify(error="Enter a city and a state."), 400
    try:
        if G:
            leads, source = google_leads(d.get("types"), city, state), "Google Places"
        else:
            leads, source = osm_leads(city, state), "OpenStreetMap"
    except Exception as e:
        return jsonify(error=f"Search failed: {e}"), 502
    for i, l in enumerate(leads):
        l["id"] = i
        l["city"] = city
    log("searches", {"city": city, "state": state, "count": len(leads), "source": source, "with_email": 0})
    return jsonify(leads=leads, source=source)


def hunter(domain):
    r = requests.get("https://api.hunter.io/v2/domain-search",
                     params={"domain": domain, "limit": 5, "api_key": H}, timeout=15).json()
    es = r.get("data", {}).get("emails", [])
    return es[0]["value"] if es else None


@app.post("/api/email")
def email_for():
    d = request.get_json(force=True)
    site, osm = d.get("website"), d.get("osm_email")
    if osm:
        return jsonify(email=osm, source="OpenStreetMap")
    found = find_emails(site) if site else []
    if found:
        return jsonify(email=found[0]["email"], source="Website")
    if H and site:
        try:
            host = site.replace("https://", "").replace("http://", "").split("/")[0]
            e = hunter(host)
            if e:
                return jsonify(email=e, source="Hunter")
        except Exception:
            pass
    return jsonify(email=None)


@app.post("/api/send")
def send():
    d = request.get_json(force=True)
    if not (SMTP_USER and SMTP_PASS):
        return jsonify(ok=False, error="Mail is not set up in .env"), 400
    name = d.get("from_name") or SENDER_NAME
    m = EmailMessage()
    m["From"] = f"{name} <{SMTP_USER}>"
    m["To"] = d["to"]
    m["Subject"] = d["subject"]
    m["Reply-To"] = d.get("reply_to") or SMTP_USER
    m["List-Unsubscribe"] = f"<mailto:{SMTP_USER}?subject=unsubscribe>"
    m.set_content(f"{d['body']}\n\n--\n{name}\n{POSTAL}\n"
                  f"Not interested? Reply \"unsubscribe\" and I won't write again.")
    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, 465, context=ssl.create_default_context(), timeout=25) as s:
                s.login(SMTP_USER, SMTP_PASS); s.send_message(m)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=25) as s:
                s.starttls(); s.login(SMTP_USER, SMTP_PASS); s.send_message(m)
        log("sends", {"to": d["to"], "business": d.get("business", ""), "ok": True})
        return jsonify(ok=True)
    except Exception as e:
        log("sends", {"to": d["to"], "business": d.get("business", ""), "ok": False, "error": str(e)[:120]})
        return jsonify(ok=False, error=str(e)), 502


if __name__ == "__main__":
    app.run(debug=True, port=5000)
