import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
client_email = os.environ["SHEETS_CLIENT_EMAIL"]
private_key  = os.environ["SHEETS_PRIVATE_KEY"].replace("\\n", "\n")
sheet_id     = os.environ["SEO_ROUTINES_SHEET_ID"]

creds = service_account.Credentials.from_service_account_info(
    {
        "type": "service_account",
        "client_email": client_email,
        "private_key": private_key,
        "token_uri": "https://oauth2.googleapis.com/token",
    },
    scopes=SCOPES,
)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

# List tabs
meta = sheet.get(spreadsheetId=sheet_id).execute()
tabs = [s["properties"]["title"] for s in meta["sheets"]]
print("TABS:", tabs)

# Read content_audit if exists
if "content_audit" in tabs:
    r = sheet.values().get(spreadsheetId=sheet_id, range="content_audit!A:C").execute()
    print("content_audit rows:", len(r.get("values", [])))
    for row in r.get("values", [])[-30:]:
        print("  ", row)
else:
    print("content_audit tab missing")

if "surfed_pages" in tabs:
    r = sheet.values().get(spreadsheetId=sheet_id, range="surfed_pages!A:B").execute()
    print("surfed_pages rows:", len(r.get("values", [])))
    for row in r.get("values", [])[-30:]:
        print("  ", row)
else:
    print("surfed_pages tab missing")
