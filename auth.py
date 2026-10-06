"""Accounts + per-user sent history. Register with: app.register_blueprint(auth_bp)"""
import os, json, re, threading, time
from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)
BASE = os.path.dirname(os.path.abspath(__file__))
USERS, DATA = os.path.join(BASE, "users.json"), os.path.join(BASE, "data.json")
_lock = threading.Lock()
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _users():
    try:
        with open(USERS) as f:
            return json.load(f)
    except Exception:
        return {}


def current_user():
    return session.get("user")


def _public(u):
    return {"name": u["name"], "email": u["email"], "business": u["business"], "joined": u["joined"]}


@auth_bp.post("/api/signup")
def signup():
    d = request.get_json(force=True)
    name, biz = d.get("name", "").strip(), d.get("business", "").strip()
    email, pw = d.get("email", "").strip().lower(), d.get("password", "")
    if not name or not biz:
        return jsonify(error="Enter your name and business name."), 400
    if not EMAIL_RE.match(email):
        return jsonify(error="Enter a valid email address."), 400
    if len(pw) < 8:
        return jsonify(error="Password must be at least 8 characters."), 400
    with _lock:
        users = _users()
        if email in users:
            return jsonify(error="An account with this email already exists."), 409
        users[email] = {"name": name, "email": email, "business": biz,
                        "pw": generate_password_hash(pw), "joined": int(time.time())}
        with open(USERS, "w") as f:
            json.dump(users, f)
    session["user"] = email
    session.permanent = True
    return jsonify(user=_public(users[email]))


@auth_bp.post("/api/login")
def login():
    d = request.get_json(force=True)
    email = d.get("email", "").strip().lower()
    u = _users().get(email)
    if not u or not check_password_hash(u["pw"], d.get("password", "")):
        return jsonify(error="Email or password is incorrect."), 401
    session["user"] = email
    session.permanent = bool(d.get("remember"))
    return jsonify(user=_public(u))


@auth_bp.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@auth_bp.get("/api/me")
def me():
    u = _users().get(current_user() or "")
    return (jsonify(user=_public(u)), 200) if u else (jsonify(error="Not signed in."), 401)


@auth_bp.post("/api/profile")
def profile():
    email = current_user()
    if not email:
        return jsonify(error="Not signed in."), 401
    d = request.get_json(force=True)
    with _lock:
        users = _users()
        users[email]["name"] = d.get("name", users[email]["name"]).strip() or users[email]["name"]
        users[email]["business"] = d.get("business", users[email]["business"]).strip() or users[email]["business"]
        with open(USERS, "w") as f:
            json.dump(users, f)
    return jsonify(user=_public(users[email]))


@auth_bp.get("/api/sends")
def sends():
    email = current_user()
    if not email:
        return jsonify(error="Not signed in."), 401
    try:
        with open(DATA) as f:
            rows = json.load(f).get("sends", [])
    except Exception:
        rows = []
    mine = [r for r in rows if r.get("user") == email]
    return jsonify(sends=mine[::-1])