import os
import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

    if not client_id or not client_secret or not refresh_token:
        raise RuntimeError("Gmail OAuth credentials are not configured.")

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    return build("gmail", "v1", credentials=credentials)


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

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": encoded_message}
        )
        .execute()
    )

    return result