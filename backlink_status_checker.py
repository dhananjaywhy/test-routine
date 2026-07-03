"""
Backlink Status Checker — Lost & Found referring domains
Reads rows from a Google Sheet, HTTP-checks Source URL / Source Domain /
Target URL, classifies statuses, determines recoverability, writes a reason,
and updates the sheet only where a value actually changed.

Required env vars:
  SHEETS_CLIENT_EMAIL — service account email
  SHEETS_PRIVATE_KEY  — service account private key (\\n-escaped PEM)

Dependencies:
  pip install google-auth google-api-python-client requests
"""

import os
import time
import socket
import requests
import urllib3
urllib3.disable_warnings()

from concurrent.futures import ThreadPoolExecutor, as_completed

from urllib.parse import urlparse
from google.oauth2 import service_account
import google.auth.transport.requests

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1vFnZv6jzQltA2SM5hj24ERxj3Kri3rVxxle43-BFOzs"
TAB = "Lost & Found referring domain"
READ_RANGE = f"'{TAB}'!D2:L"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

TIMEOUT = 10
RETRY_WAIT = 5
MAX_WORKERS = 20


class NoVerifySession(requests.Session):
    def request(self, *args, **kwargs):
        kwargs["verify"] = False
        return super().request(*args, **kwargs)


# ── Auth ──────────────────────────────────────────────────────────────────────

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
    sess = NoVerifySession()
    creds.refresh(google.auth.transport.requests.Request(session=sess))
    return sess, creds.token


# ── Sheets helpers ────────────────────────────────────────────────────────────

def read_range(sess, token, range_):
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/"
        f"{requests.utils.quote(range_)}"
    )
    r = sess.get(url, headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json().get("values", [])


def batch_update(sess, token, data):
    if not data:
        return {}
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values:batchUpdate"
    body = {"valueInputOption": "RAW", "data": data}
    r = sess.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
    )
    r.raise_for_status()
    return r.json()


# ── HTTP check ────────────────────────────────────────────────────────────────

def normalize_domain_url(domain):
    domain = domain.strip()
    if not domain:
        return None
    if not domain.startswith("http://") and not domain.startswith("https://"):
        domain = "https://" + domain
    parsed = urlparse(domain)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _do_request(url):
    return requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        allow_redirects=True,
        verify=False,
    )


def check_url(url):
    """Returns (status_str, redirected_bool)."""
    if not url:
        return "NOT REACHABLE", False

    for attempt in range(2):
        try:
            resp = _do_request(url)
            redirected = len(resp.history) > 0 and any(
                h.status_code in (301, 302) for h in resp.history
            )
            code = resp.status_code
            if 200 <= code <= 299:
                return "LIVE", redirected
            if code in (404, 410):
                return "404", False
            return str(code), redirected
        except (requests.exceptions.Timeout, socket.gaierror,
                requests.exceptions.ConnectionError):
            if attempt == 0:
                time.sleep(RETRY_WAIT)
                continue
            return "NOT REACHABLE", False
        except requests.exceptions.RequestException:
            if attempt == 0:
                time.sleep(RETRY_WAIT)
                continue
            return "NOT REACHABLE", False
    return "NOT REACHABLE", False


# ── Recoverability + reason ──────────────────────────────────────────────────

def is_live(s):
    return s == "LIVE"


def is_dead(s):
    return s in ("404", "NOT REACHABLE") or (s.isdigit() and s.startswith("5")) or s == "410"


def is_error_code(s):
    return s not in ("LIVE", "404", "NOT REACHABLE") and s.isdigit()


def determine_recoverability(src, dom, tgt):
    if src == "LIVE" and dom == "LIVE" and tgt == "LIVE":
        return "N/A"
    if src == "LIVE" and dom == "LIVE" and tgt == "404":
        return "YES"
    if src == "LIVE" and dom == "LIVE" and tgt == "NOT REACHABLE":
        return "NO"
    if src == "404" and dom == "LIVE" and tgt == "LIVE":
        return "YES"
    if src == "404" and dom == "LIVE" and tgt == "404":
        return "NO"
    if src == "404" and dom == "LIVE" and tgt == "NOT REACHABLE":
        return "NO"
    if src == "404" and dom == "404":
        return "NO"
    if src == "NOT REACHABLE":
        return "NO"
    if dom == "NOT REACHABLE":
        return "NO"
    if is_error_code(src) and dom == "LIVE" and tgt == "LIVE":
        return "YES"
    if src == "LIVE" and dom == "LIVE" and is_error_code(tgt):
        return "NO"
    # Best-judgment fallback
    if is_dead(src) and is_dead(dom):
        return "NO"
    if is_live(src) and is_live(dom) and is_dead(tgt):
        return "YES"
    return "NO"


def build_reason(src, dom, tgt, rec, src_redirected, tgt_redirected):
    if src == "LIVE" and dom == "LIVE" and tgt == "LIVE":
        reason = "All pages live — link may have been removed, manual check needed"
    elif src == "LIVE" and dom == "LIVE" and tgt == "404":
        reason = "Target URL returns 404 — fix or redirect on our end"
    elif src == "LIVE" and dom == "LIVE" and tgt == "NOT REACHABLE":
        reason = "Target domain not reachable — not recoverable"
    elif src == "404" and dom == "LIVE" and tgt == "LIVE":
        reason = "Source page deleted, domain still live — outreach possible"
    elif src == "404" and dom == "LIVE" and tgt == "404":
        reason = "Both source and target pages are dead — not recoverable"
    elif src == "404" and dom == "LIVE" and tgt == "NOT REACHABLE":
        reason = "Source page dead and target unreachable — not recoverable"
    elif src == "404" and dom == "404":
        reason = "Source page and domain both dead — not recoverable"
    elif src == "NOT REACHABLE":
        reason = "Source domain not reachable — domain may be expired"
    elif dom == "NOT REACHABLE":
        reason = "Source domain not reachable — domain may be expired"
    elif is_error_code(src) and dom == "LIVE" and tgt == "LIVE":
        reason = f"Source URL returned {src}, domain still live — outreach possible"
    elif src == "LIVE" and dom == "LIVE" and is_error_code(tgt):
        reason = f"Target URL returned {tgt} — fix or redirect on our end"
    elif rec == "N/A":
        reason = "Already live and working"
    else:
        reason = f"Source={src}, Domain={dom}, Target={tgt} — {rec.lower()} recoverable based on best judgment"

    tags = []
    if src_redirected:
        tags.append("source URL redirected")
    if tgt_redirected:
        tags.append("target URL redirected")
    if tags:
        reason += " (" + ", ".join(tags) + ")"
    return reason


# ── Main ──────────────────────────────────────────────────────────────────────

def col_letter_to_index(letter):
    return ord(letter) - ord("A")


def process_row(sheet_row, row):
    """Returns (sheet_row, updates_list, rec_or_None, error_or_None)."""
    row = row + [""] * (9 - len(row))  # pad to D..L (9 columns)
    source_url = row[0].strip()   # D
    source_domain = row[2].strip()  # F
    target_url = row[3].strip()  # G
    existing_h = row[4].strip()  # H
    existing_i = row[5].strip()  # I
    existing_j = row[6].strip()  # J
    existing_k = row[7].strip()  # K
    existing_l = row[8].strip()  # L

    try:
        src_status, src_redirected = check_url(source_url) if source_url else ("NOT REACHABLE", False)

        domain_check_url = normalize_domain_url(source_domain) if source_domain else None
        dom_status, _dom_redirected = check_url(domain_check_url) if domain_check_url else ("NOT REACHABLE", False)

        tgt_status, tgt_redirected = check_url(target_url) if target_url else ("NOT REACHABLE", False)

        src_display = src_status + (" (redirected)" if src_status == "LIVE" and src_redirected else "")
        tgt_display = tgt_status + (" (redirected)" if tgt_status == "LIVE" and tgt_redirected else "")
        dom_display = dom_status

        rec = determine_recoverability(src_status, dom_status, tgt_status)
        reason = build_reason(src_status, dom_status, tgt_status, rec,
                               src_redirected, tgt_redirected)

        new_values = {
            "H": src_display,
            "I": dom_display,
            "J": tgt_display,
            "K": rec,
            "L": reason,
        }
        existing_values = {
            "H": existing_h,
            "I": existing_i,
            "J": existing_j,
            "K": existing_k,
            "L": existing_l,
        }

        row_updates = [
            {"range": f"'{TAB}'!{col}{sheet_row}", "values": [[new_val]]}
            for col, new_val in new_values.items()
            if existing_values[col] != new_val
        ]
        return sheet_row, row_updates, rec, None
    except Exception as e:
        return sheet_row, [], None, str(e)


def main():
    sess, token = get_sheets_client()

    rows = read_range(sess, token, READ_RANGE)
    print(f"Read {len(rows)} data rows from '{TAB}'!D2:L")

    total_processed = 0
    total_updated_cells = 0
    count_yes = 0
    count_no = 0
    count_na = 0
    skipped = []
    failed = []

    updates = []  # list of {"range":..., "values": [[...]]}

    work_items = []
    for i, row in enumerate(rows):
        sheet_row = i + 2  # row 2 = first data row
        padded = row + [""] * (9 - len(row))
        if not padded[0].strip() and not padded[2].strip() and not padded[3].strip():
            skipped.append((sheet_row, "D, F, and G all empty"))
            continue
        work_items.append((sheet_row, row))

    total_processed = len(work_items)
    print(f"Checking {total_processed} rows with {MAX_WORKERS} concurrent workers...")

    done_count = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_row, sheet_row, row) for sheet_row, row in work_items]
        for future in as_completed(futures):
            sheet_row, row_updates, rec, error = future.result()
            done_count += 1
            if error:
                failed.append((sheet_row, error))
            else:
                updates.extend(row_updates)
                total_updated_cells += len(row_updates)
                if rec == "YES":
                    count_yes += 1
                elif rec == "NO":
                    count_no += 1
                else:
                    count_na += 1
            if done_count % 25 == 0 or done_count == total_processed:
                print(f"  progress: {done_count}/{total_processed} rows checked")

    if updates:
        # batchUpdate limits payload size; chunk to be safe
        CHUNK = 200
        for start in range(0, len(updates), CHUNK):
            batch_update(sess, token, updates[start:start + CHUNK])

    print("\n=== Summary ===")
    print(f"Total rows processed: {total_processed}")
    print(f"Total cells updated: {total_updated_cells}")
    print(f"Recoverable = YES: {count_yes}")
    print(f"Recoverable = NO: {count_no}")
    print(f"Recoverable = N/A: {count_na}")
    if skipped:
        print(f"Skipped rows: {skipped}")
    else:
        print("Skipped rows: none")
    if failed:
        print(f"Failed rows: {failed}")
    else:
        print("Failed rows: none")

    return {
        "total_processed": total_processed,
        "total_updated_cells": total_updated_cells,
        "count_yes": count_yes,
        "count_no": count_no,
        "count_na": count_na,
        "skipped": skipped,
        "failed": failed,
    }


if __name__ == "__main__":
    main()
