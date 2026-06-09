"""
SEO Task Generator — whydonate.com
Surf site + content audit + competitor gaps → tasks written to Google Sheets.

Required env vars:
  SHEETS_CLIENT_EMAIL   — service account email
  SHEETS_PRIVATE_KEY    — service account private key (\\n-escaped)
  SEO_ROUTINES_SHEET_ID — Google Sheets ID

Dependencies:
  pip install google-auth google-api-python-client requests
"""

import os, sys, json, datetime
import requests
import urllib3
urllib3.disable_warnings()

from google.oauth2 import service_account
import google.auth.transport.requests

# ── Auth ──────────────────────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

class NoVerifySession(requests.Session):
    def request(self, *args, **kwargs):
        kwargs["verify"] = False
        return super().request(*args, **kwargs)


def get_sheets_client():
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
    sess = NoVerifySession()
    creds.refresh(google.auth.transport.requests.Request(session=sess))
    return sess, creds.token, sheet_id


# ── Sheets helpers ────────────────────────────────────────────────────────────

def get_sheet_names(sess, token, sheet_id):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}?fields=sheets.properties"
    r = sess.get(url, headers={"Authorization": f"Bearer {token}"})
    return {s["properties"]["title"]: s["properties"]["sheetId"]
            for s in r.json().get("sheets", [])}


def add_sheet(sess, token, sheet_id, title):
    body = {"requests": [{"addSheet": {"properties": {"title": title}}}]}
    r = sess.post(
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}:batchUpdate",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
    )
    return r.json()["replies"][0]["addSheet"]["properties"]["sheetId"]


def write_range(sess, token, sheet_id, tab, range_, values):
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/"
        f"{requests.utils.quote(tab)}!{range_}?valueInputOption=RAW"
    )
    r = sess.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"range": f"{tab}!{range_}", "majorDimension": "ROWS", "values": values},
    )
    return r.json()


def read_range(sess, token, sheet_id, tab, range_):
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/"
        f"{requests.utils.quote(tab)}!{range_}"
    )
    r = sess.get(url, headers={"Authorization": f"Bearer {token}"})
    return r.json().get("values", [])


def append_rows(sess, token, sheet_id, tab, rows):
    if not rows:
        return {}
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/"
        f"{requests.utils.quote(tab)}!A1:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS"
    )
    r = sess.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"values": rows},
    )
    return r.json()


# ── Tab definitions ───────────────────────────────────────────────────────────

REQUIRED_TABS = {
    "task_list":          ["Date","ID","Category","Title","Description","HowTo","Status","Impact","CompletionDate","Flagged"],
    "surfed_pages":       ["URL","DateSurfed","IssuesFound"],
    "content_audit":      ["Date","URL","PageTitle","EEATScore","ReadabilityScore","DepthScore","AICitationScore","ThinScore","OverallScore","TopIssue"],
    "competitor_history": ["Competitor","URL","LastAnalysed"],
    "competitor_gaps":    ["Date","Competitor","Gap","WhyDonateURL","Opportunity","Priority"],
}


def ensure_tabs(sess, token, sheet_id):
    existing = get_sheet_names(sess, token, sheet_id)
    for tab, headers_row in REQUIRED_TABS.items():
        if tab not in existing:
            print(f"  Creating tab: {tab}")
            add_sheet(sess, token, sheet_id, tab)
            write_range(sess, token, sheet_id, tab, "A1", [headers_row])
        else:
            rows = read_range(sess, token, sheet_id, tab, "A1:A1")
            if not rows:
                write_range(sess, token, sheet_id, tab, "A1", [headers_row])


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Connecting to Google Sheets...")
    sess, token, sheet_id = get_sheets_client()

    print("Ensuring tabs exist...")
    ensure_tabs(sess, token, sheet_id)

    today = datetime.date.today().isoformat()

    # Read existing tasks for deduplication check (print only — manual review)
    existing_tasks = read_range(sess, token, sheet_id, "task_list", "D:D")
    print(f"\nExisting tasks in task_list: {len(existing_tasks)}")

    # Read surfed pages (skip pages surfed in last 30 days)
    surfed = read_range(sess, token, sheet_id, "surfed_pages", "A:B")
    print(f"Previously surfed pages: {len(surfed)}")

    # Read competitor history
    comp_history = read_range(sess, token, sheet_id, "competitor_history", "A:C")
    print(f"Competitor checks logged: {len(comp_history)}")

    print("\nNote: Web research (page surfing + competitor analysis) should be")
    print("performed by Claude Code with WebSearch tools before calling this script.")
    print("Update the data sections below with findings from each run.")
    print("\nTo run a full automated cycle, invoke this via Claude Code with the")
    print("SEO Task Generator prompt which handles research + data writing in one pass.")


if __name__ == "__main__":
    main()
