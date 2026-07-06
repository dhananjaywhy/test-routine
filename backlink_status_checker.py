"""
Backlink Status Checker — whydonate.com
Reads the "Lost & Found referring domain" tab, HTTP-checks Source URL /
Source Domain / Target URL for each row, classifies status, determines
recoverability, and writes back only the cells that changed.

Required env vars:
  SHEETS_CLIENT_EMAIL   — service account email
  SHEETS_PRIVATE_KEY    — service account private key (\\n-escaped)

Dependencies:
  pip install google-auth requests
"""

import os
import time
import concurrent.futures
from urllib.parse import urlparse

import requests
import urllib3
urllib3.disable_warnings()

from google.oauth2 import service_account
import google.auth.transport.requests

# ── Config ───────────────────────────────────────────────────────────────────

SPREADSHEET_ID = "1vFnZv6jzQltA2SM5hj24ERxj3Kri3rVxxle43-BFOzs"
TAB = "Lost & Found referring domain"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DATA_RANGE = "D2:L"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT = 10
MAX_REDIRECTS = 5
MAX_WORKERS = 25

# Column indices within a D2:L row (0-based, D=0 ... L=8)
COL_SOURCE_URL = 0
COL_SOURCE_TITLE = 1
COL_SOURCE_DOMAIN = 2
COL_TARGET_URL = 3
COL_SOURCE_URL_STATUS = 4
COL_SOURCE_DOMAIN_STATUS = 5
COL_TARGET_URL_STATUS = 6
COL_RECOVERABLE = 7
COL_REASON = 8


# ── Auth ─────────────────────────────────────────────────────────────────────

def get_sheets_client():
    client_email = os.environ["SHEETS_CLIENT_EMAIL"]
    private_key = os.environ["SHEETS_PRIVATE_KEY"].replace("\\n", "\n")

    creds = service_account.Credentials.from_service_account_info(
        {
            "type": "service_account",
            "client_email": client_email,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        scopes=SCOPES,
    )
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def read_range(token, tab, range_):
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/"
        f"{requests.utils.quote(tab)}!{range_}"
    )
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json().get("values", [])


def batch_update(token, data):
    if not data:
        return {}
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values:batchUpdate"
    body = {"valueInputOption": "RAW", "data": data}
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
    )
    r.raise_for_status()
    return r.json()


# ── HTTP checking ────────────────────────────────────────────────────────────

def normalize_url(value):
    value = (value or "").strip()
    if not value:
        return None
    if not (value.startswith("http://") or value.startswith("https://")):
        value = "https://" + value
    return value


def domain_root(value):
    url = normalize_url(value)
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}/"


def check_url(url):
    """Returns dict: {status: int|None, redirected: bool, error: str|None}"""
    session = requests.Session()
    session.max_redirects = MAX_REDIRECTS
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(2):
        try:
            resp = session.get(
                url, headers=headers, timeout=TIMEOUT, allow_redirects=True,
                verify=False, stream=True,
            )
            resp.close()
            return {"status": resp.status_code, "redirected": len(resp.history) > 0, "error": None}
        except requests.exceptions.TooManyRedirects:
            return {"status": None, "redirected": True, "error": "too_many_redirects"}
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt == 0:
                time.sleep(5)
                continue
            return {"status": None, "redirected": False, "error": "unreachable"}
        except requests.exceptions.RequestException as e:
            if attempt == 0:
                time.sleep(5)
                continue
            return {"status": None, "redirected": False, "error": str(e)}
    return {"status": None, "redirected": False, "error": "unreachable"}


def classify(check_result):
    """Returns (status_label, redirected_bool) or (None, False) if not checked."""
    if check_result is None:
        return None, False
    if check_result["error"]:
        return "NOT REACHABLE", check_result["redirected"]
    code = check_result["status"]
    redirected = check_result["redirected"]
    if 200 <= code < 300:
        return "LIVE", redirected
    if code in (404, 410):
        return "404", redirected
    return str(code), redirected


def bucket(status_label):
    """Collapse a status label into a decision-table bucket."""
    if status_label is None:
        return None
    if status_label == "LIVE":
        return "LIVE"
    if status_label == "404":
        return "404"
    if status_label == "NOT REACHABLE":
        return "NOT REACHABLE"
    try:
        code = int(status_label)
    except ValueError:
        return "OTHER"
    if code == 403 or 500 <= code < 600:
        return "403_5XX"
    return "OTHER"


# ── Recoverability + reason ──────────────────────────────────────────────────

def decide(src_status, domain_status, tgt_status):
    src, dom, tgt = bucket(src_status), bucket(domain_status), bucket(tgt_status)

    if dom == "NOT REACHABLE":
        return "NO", "Source domain not reachable — domain may be expired"
    if src == "NOT REACHABLE":
        return "NO", "Source URL not reachable — link cannot be verified"
    if src == "404" and dom == "404":
        return "NO", "Source page and domain both dead — not recoverable"
    if dom == "404":
        return "NO", "Source domain returns 404 — not recoverable"
    if dom == "OTHER" or dom == "403_5XX":
        return "NO", f"Source domain returns {domain_status} — not recoverable"

    # domain is LIVE from here on
    if tgt == "LIVE":
        if src == "LIVE":
            return "N/A", "All pages live — link may have been removed, manual check needed"
        if src == "404":
            return "YES", "Source page deleted, domain still live — outreach possible"
        if src in ("403_5XX", "OTHER"):
            return "YES", f"Source returns {src_status}, domain still live — outreach possible"
    elif tgt == "404":
        if src == "LIVE":
            return "YES", "Target URL returns 404 — fix or redirect on our end"
        if src == "404":
            return "NO", "Both source and target pages are dead — not recoverable"
        return "NO", f"Source returns {src_status} and target returns 404 — not recoverable"
    elif tgt == "NOT REACHABLE":
        if src == "404":
            return "NO", "Source page deleted and target not reachable — not recoverable"
        return "NO", "Target URL not reachable — not recoverable"
    else:  # tgt is 403_5XX or OTHER
        return "NO", f"Target URL returns {tgt_status} — not recoverable"

    return "NO", f"Source={src_status}, Domain={domain_status}, Target={tgt_status} — not recoverable based on best judgment"


def build_reason(base_reason, src_redirected, tgt_redirected):
    notes = []
    if src_redirected:
        notes.append("source URL redirected")
    if tgt_redirected:
        notes.append("target URL redirected")
    if notes:
        return f"{base_reason} ({', '.join(notes)})"
    return base_reason


# ── Row processing ───────────────────────────────────────────────────────────

def process_row(row):
    """row is a list from D2:L (may be shorter than 9 cols). Returns dict of new values or None to skip."""
    row = row + [""] * (9 - len(row))
    source_url = row[COL_SOURCE_URL].strip()
    source_domain = row[COL_SOURCE_DOMAIN].strip()
    target_url = row[COL_TARGET_URL].strip()

    if not source_url and not source_domain and not target_url:
        return None

    urls = {
        "source": normalize_url(source_url),
        "domain": domain_root(source_domain),
        "target": normalize_url(target_url),
    }

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(check_url, u): key for key, u in urls.items() if u}
        for fut in concurrent.futures.as_completed(futures):
            results[futures[fut]] = fut.result()

    src_status, src_redirected = classify(results.get("source"))
    dom_status, _ = classify(results.get("domain"))
    tgt_status, tgt_redirected = classify(results.get("target"))

    recoverable, base_reason = decide(src_status, dom_status, tgt_status)
    reason = build_reason(base_reason, src_redirected, tgt_redirected)

    return {
        COL_SOURCE_URL_STATUS: src_status or "",
        COL_SOURCE_DOMAIN_STATUS: dom_status or "",
        COL_TARGET_URL_STATUS: tgt_status or "",
        COL_RECOVERABLE: recoverable,
        COL_REASON: reason,
    }


# ── Main ─────────────────────────────────────────────────────────────────────

COL_LETTERS = {
    COL_SOURCE_URL_STATUS: "H",
    COL_SOURCE_DOMAIN_STATUS: "I",
    COL_TARGET_URL_STATUS: "J",
    COL_RECOVERABLE: "K",
    COL_REASON: "L",
}


def main():
    print("Authenticating with Google Sheets...")
    token = get_sheets_client()

    print(f"Reading '{TAB}'!{DATA_RANGE} ...")
    rows = read_range(token, TAB, DATA_RANGE)
    print(f"Read {len(rows)} data rows.")

    total_processed = 0
    total_skipped = []
    total_recoverable_yes = 0
    total_recoverable_no = 0
    total_recoverable_na = 0
    updates = []
    failed_rows = []

    def handle_row(idx_row):
        idx, row = idx_row
        try:
            new_values = process_row(row)
        except Exception as e:
            return idx, None, str(e)
        return idx, new_values, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(handle_row, (idx, row)) for idx, row in enumerate(rows)]
        for fut in concurrent.futures.as_completed(futures):
            idx, new_values, error = fut.result()
            sheet_row = idx + 2
            if error:
                failed_rows.append((sheet_row, error))
                continue
            if new_values is None:
                total_skipped.append((sheet_row, "D, F, G all empty"))
                continue

            total_processed += 1
            row = rows[idx] + [""] * (9 - len(rows[idx]))

            rec = new_values[COL_RECOVERABLE]
            if rec == "YES":
                total_recoverable_yes += 1
            elif rec == "NO":
                total_recoverable_no += 1
            elif rec == "N/A":
                total_recoverable_na += 1

            for col_idx, new_val in new_values.items():
                old_val = row[col_idx].strip() if col_idx < len(row) else ""
                if new_val != old_val:
                    letter = COL_LETTERS[col_idx]
                    updates.append({
                        "range": f"'{TAB}'!{letter}{sheet_row}",
                        "values": [[new_val]],
                    })

            if total_processed % 25 == 0:
                print(f"  ...processed {total_processed} rows")

    print(f"\nProcessed {total_processed} rows. {len(updates)} cells changed.")
    if updates:
        print("Writing changes via batchUpdate...")
        # batchUpdate accepts up to ~a few thousand ranges fine in one call, but
        # chunk defensively to keep request bodies reasonable.
        CHUNK = 500
        for i in range(0, len(updates), CHUNK):
            batch_update(token, updates[i:i + CHUNK])
        print("Done writing.")
    else:
        print("No changes to write.")

    print("\n=== Summary ===")
    print(f"Total rows processed: {total_processed}")
    print(f"Total cells updated: {len(updates)}")
    print(f"Recoverable = YES: {total_recoverable_yes}")
    print(f"Recoverable = NO: {total_recoverable_no}")
    print(f"Recoverable = N/A: {total_recoverable_na}")
    if total_skipped:
        print(f"Skipped rows ({len(total_skipped)}):")
        for sheet_row, reason in total_skipped:
            print(f"  Row {sheet_row}: {reason}")
    if failed_rows:
        print(f"Failed rows ({len(failed_rows)}):")
        for sheet_row, err in failed_rows:
            print(f"  Row {sheet_row}: {err}")
    if not total_skipped and not failed_rows:
        print("No rows failed or were skipped.")


if __name__ == "__main__":
    main()
