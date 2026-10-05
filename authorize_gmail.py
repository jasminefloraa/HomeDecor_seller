from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",
    SCOPES
)

credentials = flow.run_local_server(
    host="127.0.0.1",
    bind_addr="127.0.0.1",
    port=8766,
    access_type="offline",
    prompt="consent"
)

print("\nAUTHORIZATION SUCCESSFUL")
print("Refresh token:")
print(credentials.refresh_token)
print("\nKeep this value secret.")