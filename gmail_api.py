import os
import base64
import json
import stat
import threading
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gmail_token.json")
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
_lock = threading.Lock()


class GmailAuthError(RuntimeError):
    pass


class GmailSendError(RuntimeError):
    pass


def _oauth_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

    if client_id and client_secret:
        return {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }

    if os.path.isfile(CLIENT_SECRETS_FILE):
        with open(CLIENT_SECRETS_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        installed = config.get("installed", {})
        if installed.get("client_id") and installed.get("client_secret"):
            return config
    return {}


def _load_token():
    try:
        if os.path.isfile(TOKEN_FILE):
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass

    refresh_token = (
        os.getenv("GOOGLE_REFRESH_TOKEN")
        or os.getenv("GMAIL_REFRESH_TOKEN")
        or ""
    ).strip()
    return {"refresh_token": refresh_token} if refresh_token else {}


def _save_token(token):
    with _lock:
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        temporary = TOKEN_FILE + ".tmp"
        with open(temporary, "w", encoding="utf-8") as f:
            json.dump(token, f)
        os.replace(temporary, TOKEN_FILE)
        if os.name != "nt":
            os.chmod(TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)


def get_gmail_service():
    config = _oauth_config()
    token = _load_token()
    installed = config.get("installed")
    if not installed:
        raise GmailAuthError("Gmail OAuth client credentials are not configured. Reconnect Google.")
    if not token.get("refresh_token"):
        raise GmailAuthError("Gmail authorization is missing. Reconnect the Google account.")

    credentials = Credentials(
        token=token.get("token"),
        refresh_token=token["refresh_token"],
        token_uri=installed.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=installed["client_id"],
        client_secret=installed["client_secret"],
        scopes=token.get("scopes", SCOPES),
    )

    if credentials.expired or not credentials.valid:
        try:
            credentials.refresh(Request())
        except RefreshError as exc:
            raise GmailAuthError(
                "Google authorization was revoked or expired. Reconnect the Google account."
            ) from exc
        saved = dict(token)
        saved.update({
            "token": credentials.token,
            "refresh_token": credentials.refresh_token or token["refresh_token"],
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "scopes": list(credentials.scopes or SCOPES),
        })
        _save_token(saved)
    return build("gmail", "v1", credentials=credentials)


def gmail_status():
    token = _load_token()
    return {
        "configured": bool(_oauth_config().get("installed")),
        "authorized": bool(token.get("refresh_token")),
    }


def create_authorization_url(redirect_uri, state):
    config = _oauth_config()
    if not config.get("installed"):
        raise GmailAuthError("Gmail OAuth client credentials are not configured.")
    flow = Flow.from_client_config(config, scopes=SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    url, generated_state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return url, generated_state


def complete_authorization(callback_url, state):
    config = _oauth_config()
    flow = Flow.from_client_config(config, scopes=SCOPES, state=state)
    configured_redirect = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
    app_url = os.getenv("APP_URL", "").strip().rstrip("/")
    flow.redirect_uri = configured_redirect.rstrip("/") or (
        app_url + "/api/gmail/callback"
        if app_url
        else "https://homedecor-seller-1.onrender.com/api/gmail/callback"
    )
    flow.fetch_token(authorization_response=callback_url)
    credentials = flow.credentials
    if not credentials.refresh_token:
        raise GmailAuthError("Google did not return a refresh token. Revoke prior access and reconnect again.")
    _save_token({
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "scopes": list(credentials.scopes or SCOPES),
    })


def send_email(to, subject, body, sender_name, sender_email, reply_to=None):
    service = get_gmail_service()

    message = EmailMessage()
    message["To"] = to
    message["From"] = f"{sender_name} <{sender_email}>"
    message["Subject"] = subject
    message["Reply-To"] = reply_to or sender_email

    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    try:
        result = (
            service.users()
            .messages()
            .send(
                userId="me",
                body={"raw": encoded_message}
            )
            .execute()
        )
    except HttpError as exc:
        status = exc.resp.status
        if status == 401:
            raise GmailAuthError("Gmail authorization expired. Reconnect the Google account.") from exc
        if status == 403:
            raise GmailAuthError("Gmail denied sending permission. Reconnect with Gmail send access.") from exc
        raise GmailSendError(f"Gmail API request failed with HTTP {status}.") from exc

    return result