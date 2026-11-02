
import os, ssl, json, time, threading, smtplib, requests, secrets
from gmail_api import send_email, gmail_status, create_authorization_url, complete_authorization, GmailAuthError, GmailSendError
from email.message import EmailMessage
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from emailfinder import osm_leads, find_emails

load_dotenv()
app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or secrets.token_hex(32)

G = os.getenv("GOOGLE_PLACES_KEY", "").strip()
H = os.getenv("HUNTER_KEY", "").strip()
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", os.getenv("SMTP_POR", "465")))
SENDER_NAME = os.getenv("SENDER_NAME", "")
POSTAL = os.getenv("POSTAL_ADDRESS", "")


DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
_lock = threading.Lock()


def _load():
    try:
        with open(DB) as f:
            return json.load(f)
    except Exception:
        return {"searches": [], "sends": [], "users": []}


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
    gmail = gmail_status()
    return jsonify(places=bool(G), hunter=bool(H), mail=bool(SMTP_USER and SMTP_PASS),
                   sender=SMTP_USER, gmail_configured=gmail["configured"],
                   gmail_authorized=gmail["authorized"],
                   resend=bool(os.getenv("RESEND_API_KEY", "").strip()))


def gmail_redirect_uri():
    configured = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
    if configured:
        return configured.rstrip("/")
    base_url = os.getenv("APP_URL", "").strip().rstrip("/")
    if base_url:
        return base_url + "/api/gmail/callback"
    return "https://homedecor-seller-1.onrender.com/api/gmail/callback"


@app.get("/api/gmail/authorize")
def gmail_authorize():
    try:
        redirect_uri = gmail_redirect_uri()
        state = secrets.token_urlsafe(24)
        from flask import session
        session["gmail_oauth_state"] = state
        url, _ = create_authorization_url(redirect_uri, state)
        from flask import redirect
        return redirect(url)
    except GmailAuthError as e:
        return jsonify(ok=False, error=str(e)), 400


@app.get("/api/gmail/callback")
def gmail_callback():
    from flask import session, redirect
    expected = session.pop("gmail_oauth_state", None)
    if not expected or request.args.get("state") != expected:
        return jsonify(ok=False, error="OAuth state validation failed. Start authorization again."), 400
    try:
        callback_url = gmail_redirect_uri()
        if request.query_string:
            callback_url += "?" + request.query_string.decode("ascii")
        complete_authorization(callback_url, expected)
        return redirect("/#gmail=connected")
    except Exception as e:
        message = str(e)
        if "invalid_grant" in message.lower():
            message = "Google authorization expired or was revoked. Please reconnect again."
        return jsonify(ok=False, error=message), 400


@app.post("/api/gmail/test")
def gmail_test():
    d = request.get_json(force=True)
    to = (d.get("to") or os.getenv("GMAIL_SENDER_EMAIL", "")).strip()
    sender_email = (
        os.getenv("GMAIL_SENDER_EMAIL")
        or os.getenv("FROM_EMAIL")
        or ""
    ).strip()
    if not to:
        return jsonify(ok=False, error="Enter a recipient email address."), 400
    if not sender_email:
        return jsonify(ok=False, error="Gmail sender email is not configured."), 400
    try:
        result = send_email(
            to=to,
            subject="DecorReach Gmail authentication test",
            body="This test confirms that Gmail API sending is working.",
            sender_name=SENDER_NAME or "DecorReach",
            sender_email=sender_email,
            reply_to=sender_email,
        )
        if not result.get("id"):
            raise RuntimeError("Gmail API did not return a message ID.")
        return jsonify(ok=True, message_id=result["id"])
    except GmailAuthError as e:
        return jsonify(ok=False, error=str(e), reconnect=True), 401
    except GmailSendError as e:
        return jsonify(ok=False, error=str(e)), 502
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 502


def resend_send(to, subject, body, sender_name, sender_email, reply_to=None):
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Resend is not configured.")
    payload = {
        "from": f"{sender_name} <{sender_email}>",
        "to": [to],
        "subject": subject,
        "text": body,
        "reply_to": reply_to or sender_email,
    }
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response_data = response.json()
    if not response.ok or not response_data.get("id"):
        raise RuntimeError(f"Resend API request failed with HTTP {response.status_code}.")
    return {"id": response_data["id"], "provider": "resend"}


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

    sender_email = (
        os.getenv("GMAIL_SENDER_EMAIL")
        or os.getenv("FROM_EMAIL")
        or ""
    ).strip()
    sender_name = d.get("from_name") or SENDER_NAME

    if not sender_email:
        return jsonify(
            ok=False,
            error="Gmail sender email is not configured."
        ), 400

    try:
        with _lock:
            sent = [row for row in _load().get("sends", [])
                    if row.get("to") == d["to"] and row.get("ok")]
        if sent and not d.get("allow_duplicate"):
            return jsonify(ok=False, error="This recipient has already received an email.", duplicate=True), 409

        body = (
            f"{d['body']}\n\n"
            f"--\n"
            f"{sender_name}\n"
            f"Not interested? Reply \"unsubscribe\" and I won't write again."
        )

        result = send_email(
            to=d["to"],
            subject=d["subject"],
            body=body,
            sender_name=sender_name,
            sender_email=sender_email,
            reply_to=d.get("reply_to") or sender_email
        )

        log("sends", {
            "to": d["to"],
            "business": d.get("business", ""),
            "ok": True,
            "message_id": result.get("id")
        })

        return jsonify(
            ok=True,
            message_id=result.get("id")
        )

    except GmailAuthError as e:
        if os.getenv("RESEND_API_KEY", "").strip():
            try:
                resend_result = resend_send(
                    to=d["to"],
                    subject=d["subject"],
                    body=body,
                    sender_name=sender_name,
                    sender_email=sender_email,
                    reply_to=d.get("reply_to") or sender_email,
                )
                log("sends", {
                    "to": d["to"],
                    "business": d.get("business", ""),
                    "ok": True,
                    "message_id": resend_result["id"],
                    "provider": "resend",
                })
                return jsonify(ok=True, message_id=resend_result["id"], provider="resend")
            except Exception:
                pass
        log("sends", {
            "to": d["to"],
            "business": d.get("business", ""),
            "ok": False,
            "error": str(e)[:120],
            "auth_error": True
        })
        return jsonify(ok=False, error=str(e), reconnect=True), 401
    except Exception as e:
        log("sends", {
            "to": d["to"],
            "business": d.get("business", ""),
            "ok": False,
            "error": str(e)[:120]
        })

        return jsonify(
            ok=False,
            error=str(e)
        ), 502


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5050)
