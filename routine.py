import os
import time
import anthropic
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
import json

# ── Credentials ───────────────────────────────────────────────────────────────
client_email = os.environ["SHEETS_CLIENT_EMAIL"]
private_key  = os.environ["SHEETS_PRIVATE_KEY"].replace("\\n", "\n")
sheet_id     = os.environ.get("GEO_ROUTINES_SHEET_ID", "1bYCLlrKyUU2h0ltkAMlfFhCHx2NqFxiWqIcaI9_qNlU")
BATCH_SIZE   = 25
HEADER_ROWS  = 3
SCOPES       = ["https://www.googleapis.com/auth/spreadsheets"]
CA_BUNDLE    = os.environ.get("REQUESTS_CA_BUNDLE", True)

creds = service_account.Credentials.from_service_account_info(
    {
        "type": "service_account",
        "client_email": client_email,
        "private_key": private_key,
        "token_uri": "https://oauth2.googleapis.com/token",
    },
    scopes=SCOPES,
)

authed = AuthorizedSession(creds)
authed.verify = CA_BUNDLE

SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

def sheets_get(range_: str) -> list:
    url = f"{SHEETS_BASE}/{sheet_id}/values/{range_}"
    resp = authed.get(url)
    resp.raise_for_status()
    return resp.json().get("values", [])

def sheets_put(range_: str, value: str):
    url = f"{SHEETS_BASE}/{sheet_id}/values/{range_}"
    params = {"valueInputOption": "RAW"}
    body = {"values": [[value]]}
    resp = authed.put(url, params=params, json=body)
    resp.raise_for_status()

# Use session ingress token if ANTHROPIC_API_KEY not set
_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not _api_key:
    _token_file = os.environ.get("CLAUDE_SESSION_INGRESS_TOKEN_FILE")
    if _token_file and os.path.exists(_token_file):
        with open(_token_file) as _f:
            _api_key = _f.read().strip()

ai = anthropic.Anthropic(api_key=_api_key) if _api_key else anthropic.Anthropic()

GEO_SYSTEM_PROMPT = """You are a Generative Engine Optimization (GEO) expert.

Given a keyword, generate exactly 10 question-query pairs showing:
- What a real person would ask an AI assistant (ChatGPT, Gemini, Claude, Perplexity) about this keyword
- What the AI would internally search to answer that question

Output format — exactly 10 numbered lines, nothing else:
1. [Human Question] | [AI Internal Query]
2. [Human Question] | [AI Internal Query]

Rules:
- Human Question: natural conversational language, exactly how someone types into ChatGPT
- AI Internal Query: compact, entity-rich, semantic — what hits the retrieval index
- Separate the two with space-pipe-space: ` | `
- Cover all angles: what/how/why/best/cost/compare/trust/examples/alternatives
- Sort by most likely to least likely
- No headers, no explanation, no markdown — just the 10 numbered lines"""

# ── Read sheet ────────────────────────────────────────────────────────────────
print("Reading sheet...")
rows = sheets_get("Sheet1!B4:C")

# Find pending rows (keyword in B, empty C)
pending = []
for i, row in enumerate(rows):
    if not row or not row[0].strip():
        continue
    keyword  = row[0].strip()
    citation = row[1].strip() if len(row) > 1 else ""
    if not citation:
        pending.append({"row": i + HEADER_ROWS + 1, "keyword": keyword})
    if len(pending) >= BATCH_SIZE:
        break

print(f"Found {len(pending)} keywords pending GEO citations\n")

if not pending:
    print("Nothing to process — all keywords already have GEO citations in Column C.")
    exit(0)

# ── Process batch ─────────────────────────────────────────────────────────────
success, errors = 0, 0
summary_lines = []

for item in pending:
    keyword = item["keyword"]
    row_num = item["row"]
    print(f"  Row {row_num}: {keyword}", end=" ... ", flush=True)

    try:
        msg = ai.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            temperature=0,
            system=GEO_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": keyword}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(l for l in raw.split("\n") if not l.startswith("```")).strip()

        sheets_put(f"Sheet1!C{row_num}", raw)

        n = len(raw.splitlines())
        print(f"{n} pairs written")
        summary_lines.append(f"  • {keyword:<40} — Row {row_num}  ✓ {n} pairs")
        success += 1

    except Exception as e:
        print(f"ERROR: {e}")
        summary_lines.append(f"  • {keyword:<40} — Row {row_num}  ✗ {e}")
        errors += 1

    time.sleep(0.4)

# ── Count remaining ───────────────────────────────────────────────────────────
fresh = sheets_get("Sheet1!B4:C")
still_pending = sum(
    1 for r in fresh
    if r and r[0].strip() and (len(r) < 2 or not r[1].strip())
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"""
══════════════════════════════════════════════
GEO Citations Routine — whydonate.com
══════════════════════════════════════════════

Batch processed: {success}/{len(pending)} keywords

Keywords written this run:
{chr(10).join(summary_lines)}

Column C format (10 pairs per keyword):
  1. [Human Question] | [AI Internal Query]
  2. ...
  10. ...

Still pending: {still_pending} keywords
{"Run again to process the next batch of 25." if still_pending > 0 else "All keywords complete."}
Errors this run: {errors}
══════════════════════════════════════════════
""")
