import os
import json
import time
import threading
import requests
import resend

from flask import Flask, jsonify, request
from dotenv import load_dotenv
from emailfinder import osm_leads, find_emails

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")

# =========================
# Environment Variables
# =========================

G = os.getenv("GOOGLE_PLACES_KEY", "").strip()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
FROM_EMAIL = os.getenv("FROM_EMAIL", "").strip()
SENDER_NAME = os.getenv("SENDER_NAME", "").strip()

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


# =========================
# Local Data Storage
# =========================

DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data.json"
)

_lock = threading.Lock()


def _load():
    try:
        with open(DB) as f:
            return json.load(f)
    except Exception:
        return {
            "searches": [],
            "sends": []
        }


def log(kind, row):
    with _lock:
        d = _load()

        row["t"] = int(time.time())
        d[kind].append(row)

        with open(DB, "w") as f:
            json.dump(d, f)


# =========================
# Email Discovery Count
# =========================

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


# =========================
# Dashboard Statistics
# =========================

@app.get("/api/stats")
def stats():
    d = _load()

    s = d["sends"]
    day = 86400
    today = int(time.time()) // day

    daily = [
        sum(
            1
            for x in s
            if x["ok"] and x["t"] // day == today - i
        )
        for i in range(6, -1, -1)
    ]

    return jsonify(
        searches=len(d["searches"]),
        leads=sum(x["count"] for x in d["searches"]),
        emails=sum(
            x.get("with_email", 0)
            for x in d["searches"]
        ),
        sent=sum(
            1 for x in s
            if x["ok"]
        ),
        failed=sum(
            1 for x in s
            if not x["ok"]
        ),
        daily=daily,
        recent=s[-8:][::-1],
        recent_searches=d["searches"][-5:][::-1]
    )


# =========================
# Homepage
# =========================

@app.get("/")
def home():
    return app.send_static_file("index.html")


# =========================
# Service Status
# =========================

@app.get("/api/status")
def status():
    return jsonify(
        places=bool(G),
        mail=bool(
            RESEND_API_KEY and FROM_EMAIL
        ),
        sender=FROM_EMAIL,
        provider="Resend"
    )


# =========================
# Google Places Discovery
# =========================

def google_leads(types, city, state):
    out = []
    seen = set()

    mask = (
        "places.id,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.nationalPhoneNumber,"
        "places.websiteUri,"
        "places.rating"
    )

    for t in types or ["home decor store"]:

        response = requests.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={
                "X-Goog-Api-Key": G,
                "X-Goog-FieldMask": mask
            },
            json={
                "textQuery": f"{t} in {city}, {state}, USA",
                "pageSize": 20
            },
            timeout=20
        )

        response.raise_for_status()

        for p in response.json().get("places", []):

            if p["id"] in seen:
                continue

            seen.add(p["id"])

            out.append({
                "name": p["displayName"]["text"],
                "type": t,
                "address": p.get(
                    "formattedAddress",
                    ""
                ),
                "phone": p.get(
                    "nationalPhoneNumber"
                ),
                "website": p.get(
                    "websiteUri"
                ),
                "rating": p.get(
                    "rating"
                )
            })

    return out


# =========================
# Business Search
# =========================

@app.post("/api/search")
def search():

    d = request.get_json(force=True)

    city = d.get("city", "").strip()
    state = d.get("state", "").strip()

    if not city or not state:
        return jsonify(
            error="Enter a city and a state."
        ), 400

    try:

        if G:
            leads = google_leads(
                d.get("types"),
                city,
                state
            )

            source = "Google Places"

        else:
            leads = osm_leads(
                city,
                state
            )

            source = "OpenStreetMap"

    except Exception as e:

        return jsonify(
            error=f"Search failed: {e}"
        ), 502

    for i, lead in enumerate(leads):

        lead["id"] = i
        lead["city"] = city

    log(
        "searches",
        {
            "city": city,
            "state": state,
            "count": len(leads),
            "source": source,
            "with_email": 0
        }
    )

    return jsonify(
        leads=leads,
        source=source
    )


# =========================
# Public Website Email Finder
# =========================

@app.post("/api/email")
def email_for():

    d = request.get_json(force=True)

    site = d.get("website")
    osm = d.get("osm_email")

    # OpenStreetMap email
    if osm:
        return jsonify(
            email=osm,
            source="OpenStreetMap"
        )

    # Website email discovery
    found = find_emails(site) if site else []

    if found:
        return jsonify(
            email=found[0]["email"],
            source="Website"
        )

    return jsonify(
        email=None
    )


# =========================
# Send Email Through Resend
# =========================

@app.post("/api/send")
def send():

    d = request.get_json(force=True)

    # Check Resend configuration
    if not RESEND_API_KEY:
        return jsonify(
            ok=False,
            error="Email service is not configured. Add RESEND_API_KEY in Render Environment Variables."
        ), 400

    if not FROM_EMAIL:
        return jsonify(
            ok=False,
            error="FROM_EMAIL is not configured."
        ), 400

    # Get email information
    to_email = (
        d.get("to") or ""
    ).strip()

    subject = (
        d.get("subject") or ""
    ).strip()

    body = d.get("body") or ""

    business = d.get(
        "business",
        ""
    )

    name = (
        d.get("from_name")
        or SENDER_NAME
        or "Stockist"
    )

    # Validate input
    if not to_email:
        return jsonify(
            ok=False,
            error="Recipient email is required."
        ), 400

    if not subject:
        return jsonify(
            ok=False,
            error="Email subject is required."
        ), 400

    if not body.strip():
        return jsonify(
            ok=False,
            error="Email body is required."
        ), 400

    # Plain text version
    text_body = (
        f"{body}\n\n"
        f"--\n"
        f"{name}\n\n"
        f'Not interested? Reply "unsubscribe" '
        f"and I won't write again."
    )

    # HTML version
    safe_body = (
        body
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )

    html_body = f"""
    <div style="
        font-family: Arial, sans-serif;
        line-height: 1.6;
        color: #222;
    ">
        <div>
            {safe_body}
        </div>

        <br>

        <div>
            --
            <br>
            {name}
        </div>

        <br>

        <div style="
            color: #777;
            font-size: 13px;
        ">
            Not interested?
            Reply "unsubscribe" and I won't write again.
        </div>
    </div>
    """

    try:

        params = {
            "from": f"{name} <{FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
            "text": text_body,
            "reply_to": (
                d.get("reply_to")
                or FROM_EMAIL
            )
        }

        # Send using Resend
        result = resend.Emails.send(
            params
        )

        email_id = getattr(
            result,
            "id",
            None
        )

        # Record successful send
        log(
            "sends",
            {
                "to": to_email,
                "business": business,
                "ok": True,
                "provider": "Resend",
                "email_id": email_id
            }
        )

        return jsonify(
            ok=True,
            provider="Resend",
            email_id=email_id
        )

    except Exception as e:

        error_message = str(e)[:300]

        # Record failed send
        log(
            "sends",
            {
                "to": to_email,
                "business": business,
                "ok": False,
                "provider": "Resend",
                "error": error_message
            }
        )

        return jsonify(
            ok=False,
            error=error_message
        ), 502


# =========================
# Run Application
# =========================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
