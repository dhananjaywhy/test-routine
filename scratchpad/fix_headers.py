import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = service_account.Credentials.from_service_account_info(
    {
        "type": "service_account",
        "client_email": os.environ["SHEETS_CLIENT_EMAIL"],
        "private_key": os.environ["SHEETS_PRIVATE_KEY"].replace("\\n", "\n"),
        "token_uri": "https://oauth2.googleapis.com/token",
    },
    scopes=SCOPES,
)
sheet = build("sheets", "v4", credentials=creds).spreadsheets()
sheet_id = os.environ["SEO_ROUTINES_SHEET_ID"]

HEADERS = [
    "Date",                        # A
    "URL",                         # B
    "PageTitle",                   # C
    "WordCount",                   # D
    "EEATScore",                   # E — Expertise/Experience/Authority/Trust (0-100)
    "ReadabilityScore",            # F — scannability, paragraph & heading structure (0-100)
    "DepthScore",                  # G — topic coverage & objection handling (0-100)
    "AICitationScore",             # H — AI-Overview / LLM extractability (0-100)
    "ThinScore",                   # I — sufficiency of content for the page's purpose (0-100)
    "InternalLinksScore",          # J — contextual internal linking quality (0-100)
    "SocialProofScore",            # K — testimonials, case studies, stats, badges (0-100)
    "OverallScore",                # L — weighted average of the 7 dimensions
    "TopIssue",                    # M
    "ContentGap",                  # N
    "RecommendedAction",           # O
    "Priority",                    # P
]

sheet.values().update(
    spreadsheetId=sheet_id,
    range="content_audit!A1:P1",
    valueInputOption="RAW",
    body={"values": [HEADERS]},
).execute()

# Verify
r = sheet.values().get(spreadsheetId=sheet_id, range="content_audit!A1:P1").execute()
print("Row 1 now:")
for i, h in enumerate(r["values"][0]):
    col = chr(ord("A") + i)
    print(f"  {col}: {h}")
