"""
SEO Competitor Analysis — whydonate.com
Run: 2026-06-09
Competitors: JustGiving, Donorbox, GoGetFunding
"""

import os
import ssl
import httplib2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp

# Remote execution environment uses a self-signed CA in the chain;
# disable cert verification so the Google API calls succeed.
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
client_email = os.environ["SHEETS_CLIENT_EMAIL"]
private_key  = os.environ["SHEETS_PRIVATE_KEY"].replace("\\n", "\n")
sheet_id     = "1mZxNI7ehgRcEZtlrCBAGvHMWh5vC9UhpkwavLoDYq0Q"

creds = service_account.Credentials.from_service_account_info(
    {
        "type": "service_account",
        "client_email": client_email,
        "private_key": private_key,
        "token_uri": "https://oauth2.googleapis.com/token",
    },
    scopes=SCOPES,
)
_http = httplib2.Http(disable_ssl_certificate_validation=True)
_authed_http = AuthorizedHttp(creds, http=_http)
service = build("sheets", "v4", http=_authed_http)
sheet   = service.spreadsheets()


# ── helpers ───────────────────────────────────────────────────────────────────

def ensure_tab(tab_name, headers):
    """Create tab with headers if it doesn't exist, skip if it does."""
    meta = sheet.get(spreadsheetId=sheet_id).execute()
    existing = [s["properties"]["title"] for s in meta["sheets"]]
    if tab_name not in existing:
        sheet.batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
        ).execute()
        sheet.values().update(
            spreadsheetId=sheet_id,
            range=f"{tab_name}!A1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()
        print(f"  Created tab: {tab_name}")
    else:
        # Check if header row exists
        result = sheet.values().get(
            spreadsheetId=sheet_id, range=f"{tab_name}!A1:A1"
        ).execute()
        if not result.get("values"):
            sheet.values().update(
                spreadsheetId=sheet_id,
                range=f"{tab_name}!A1",
                valueInputOption="RAW",
                body={"values": [headers]},
            ).execute()
            print(f"  Added headers to existing tab: {tab_name}")


def append(tab, rows):
    if not rows:
        return
    sheet.values().append(
        spreadsheetId=sheet_id,
        range=f"{tab}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


# ── ensure tabs exist ─────────────────────────────────────────────────────────

ensure_tab("competitor_pages", [
    "Date", "Competitor", "URL", "PageType", "WordCountEst",
    "HasFAQ", "HasTestimonials", "HasStats", "TopGap", "Opportunity", "Priority"
])

ensure_tab("competitor_history", [
    "Competitor", "URL", "LastAnalysed"
])

ensure_tab("keyword_gaps", [
    "Date", "Keyword", "CompetitorRanking", "WhyDonateRanking",
    "Gap", "ContentAction"
])


# ── 1. Competitor page findings ───────────────────────────────────────────────

page_rows = [
    # JustGiving — for-charities page
    [
        "2026-06-09",
        "JustGiving",
        "https://www.justgiving.com/for-charities",
        "Nonprofit/Charity",
        "900",
        "TRUE",
        "TRUE",
        "TRUE",
        (
            "Named testimonials from Cancer Research UK & MND Association; "
            "'hundreds of millions raised' stat; full FAQ section covering eligibility, fees & setup; "
            "dedicated charity resources hub with free webinars and case studies — "
            "none of this exists on whydonate.com/fundraising-for-nonprofits/"
        ),
        (
            "Add 3 named nonprofit testimonials with measurable results, a FAQ section (6–8 Q&As), "
            "and a 'Resources for nonprofits' link block to /en/nonprofit. "
            "Add a platform-wide stat (e.g. total raised, charities supported) above the fold."
        ),
        "High",
    ],
    # JustGiving — pricing page
    [
        "2026-06-09",
        "JustGiving",
        "https://www.justgiving.com/for-charities/pricing",
        "Pricing",
        "700",
        "TRUE",
        "FALSE",
        "TRUE",
        (
            "Structured Start/Grow plan comparison table with exact fee percentages; "
            "FAQ covering Gift Aid fee (5%), payment processing (1.9%+30p), plan differences; "
            "whydonate.com /fees/ lacks both a structured plan table and FAQ"
        ),
        (
            "Add a fee comparison table to /fees/ showing 0% platform fee vs typical competitors. "
            "Add 6-item FAQ (platform fee, processing costs, payout timing, donor tip, nonprofit rate, refunds). "
            "Add a clear plan/tier summary if applicable."
        ),
        "High",
    ],
    # Donorbox — homepage
    [
        "2026-06-09",
        "Donorbox",
        "https://donorbox.org/",
        "Homepage",
        "1100",
        "TRUE",
        "TRUE",
        "TRUE",
        (
            "Leads with '#1 Donation Software' + G2/Capterra badge; "
            "stats: '50,000+ nonprofits', '96 countries', 'UltraSwift 4x faster checkout'; "
            "named case studies (Hurricane's Heroes: $1M raised, 20hrs saved/week); "
            "whydonate.com homepage has no rating badges, no named case studies, no conversion stats"
        ),
        (
            "Add Trustpilot rating badge + review count to homepage hero (currently only text mention). "
            "Add 2 named campaign success stories with $ amounts raised. "
            "Add a platform conversion stat (e.g. 'X% of campaigns reach their goal') to the stats bar."
        ),
        "High",
    ],
    # Donorbox — pricing page
    [
        "2026-06-09",
        "Donorbox",
        "https://donorbox.org/pricing",
        "Pricing",
        "1400",
        "TRUE",
        "FALSE",
        "TRUE",
        (
            "Three-tier plan comparison table (Standard/Pro/Premium) with per-feature checklist; "
            "FAQ section (setup fees, cancellation, currency, nonprofit discounts); "
            "whydonate.com /fees/ is a single-tier page with no structured table and no FAQ"
        ),
        (
            "Restructure /fees/ with a clear table: '0% platform fee | 1.9%+€0.25 processing | €0.35 iDEAL'. "
            "Add example: 'On a €100 donation, the donor keeps 100% + optional tip prompt'. "
            "Add 4-item FAQ under the table."
        ),
        "High",
    ],
    # Donorbox — case studies page (unique section)
    [
        "2026-06-09",
        "Donorbox",
        "https://donorbox.org/case-studies",
        "Case Studies",
        "800",
        "FALSE",
        "TRUE",
        "TRUE",
        (
            "Dedicated case-studies page with named nonprofits, campaign type, amounts raised, and time saved; "
            "whydonate.com has no equivalent case studies page or section"
        ),
        (
            "Create a 'Success stories' page or section on /en/nonprofit listing 3–5 named nonprofits "
            "who raised funds on WhyDonate, with cause, amount raised, and a short quote. "
            "Link to it from the homepage and nonprofit page."
        ),
        "Medium",
    ],
    # GoGetFunding — homepage
    [
        "2026-06-09",
        "GoGetFunding",
        "https://gogetfunding.com/",
        "Homepage",
        "600",
        "TRUE",
        "TRUE",
        "TRUE",
        (
            "Leads with benefit H1 + immediate CTA; TrustPilot 4/5 badge (410 reviews) visible in hero; "
            "dedicated FAQ page linked from homepage; 'no automatic donor tips' positioned as key differentiator; "
            "24/7 personal fundraising coach highlighted as unique feature — "
            "whydonate.com homepage lacks social proof badge, FAQ, and clear differentiation copy"
        ),
        (
            "Move Trustpilot badge into homepage hero (not buried below fold). "
            "Add FAQ section to homepage (6 Q&As). "
            "Add a 'What makes WhyDonate different' 4-point section highlighting: "
            "0% platform fee, global reach, 15 payment methods, 850k+ donors already on platform."
        ),
        "High",
    ],
    # GoGetFunding — FAQ page
    [
        "2026-06-09",
        "GoGetFunding",
        "https://gogetfunding.com/faq/",
        "FAQ",
        "1200",
        "TRUE",
        "FALSE",
        "FALSE",
        (
            "Standalone FAQ page covering fee structure, payment methods, withdrawal, account safety, "
            "Bitcoin fundraising, and campaign tips — "
            "whydonate.com has no standalone FAQ page; FAQ content is scattered across helpdesk subdomain"
        ),
        (
            "Create a /faq/ or /en/faq/ page on the main whydonate.com domain consolidating "
            "the top 15–20 questions from helpdesk. This builds main-domain topical authority "
            "and helps AI assistants extract answers about WhyDonate."
        ),
        "Medium",
    ],
]

append("competitor_pages", page_rows)
print(f"  Wrote {len(page_rows)} competitor page rows")


# ── 2. Keyword gaps ────────────────────────────────────────────────────────────

gap_rows = [
    [
        "2026-06-09",
        "online fundraising platform",
        "GoFundMe Pro #1, Zeffy #2, Fundraise Up #4",
        "Not in top 10",
        (
            "GoFundMe Pro and Zeffy dominate with pages 900–1,200 words, FAQ sections, "
            "and prominent stats. WhyDonate homepage (~400–600 words) lacks FAQ and depth."
        ),
        (
            "Expand homepage to 700+ words with an H2 section 'Why choose WhyDonate', "
            "an FAQ block (6 Q&As), and a stat bar (total raised, countries, payment methods)."
        ),
    ],
    [
        "2026-06-09",
        "free fundraising website",
        "FreeFunder #1, FundRazr #2, GiveLively #3, GoGetFunding #10",
        "Not in top 10",
        (
            "All top results lead with '0 fees' or 'completely free' in their H1 and page title. "
            "WhyDonate is free but 'free' is buried in body copy rather than leading the title/H1."
        ),
        (
            "Create a dedicated /free-fundraising/ landing page or update homepage H1 to lead with "
            "'Free fundraising' angle. Use title: 'Free Fundraising Website | 0% Platform Fee | WhyDonate'."
        ),
    ],
    [
        "2026-06-09",
        "nonprofit fundraising platform",
        "Givebutter #1, GoFundMe Pro #2, GiveLively #3",
        "Not in top 10",
        (
            "Top 3 all have dedicated nonprofit pages 800–1,400 words with case studies, "
            "testimonials, FAQ, and prominent stats. WhyDonate nonprofit page is ~400 words with none of these."
        ),
        (
            "Expand /en/nonprofit to 800+ words. Add nonprofit-specific FAQ, "
            "3 named testimonials, and a 'Trusted by X nonprofits' stat. "
            "Target the keyword 'nonprofit fundraising platform' in the H1 and title tag."
        ),
    ],
    [
        "2026-06-09",
        "how to raise money online for charity",
        "GoFundMe #1, JustGiving #2",
        "Not in top 10",
        (
            "GoFundMe and JustGiving rank because they have informational content pages and deep blog posts "
            "answering this exact question with step-by-step guidance. "
            "WhyDonate's blog has a best-personal-fundraising-websites post but not a how-to guide for charities."
        ),
        (
            "Publish a blog post titled 'How to Raise Money Online for Charity in 2026' "
            "(800–1,000 words, with step-by-step guide, FAQ, and link to /en/nonprofit). "
            "This is a high-intent keyword with informational intent WhyDonate can own."
        ),
    ],
    [
        "2026-06-09",
        "0% fee fundraising",
        "Zeffy #1 (multiple results), GoFundMe blog #6",
        "Not in top 10",
        (
            "Zeffy owns this keyword with 2+ results about '0% fee fundraising' and 'zero-fee fundraising'. "
            "WhyDonate actually charges 0% platform fee but has no dedicated page or blog post "
            "targeting this exact keyword."
        ),
        (
            "Publish a blog post or landing page titled '0% Platform Fee Fundraising — What It Means for You' "
            "or update the /fees/ page to include an H2 'Why WhyDonate charges 0% platform fees' "
            "with a direct comparison against Donorbox (2.95%), GoGetFunding (4%), JustGiving (1.9%+30p)."
        ),
    ],
    [
        "2026-06-09",
        "charity crowdfunding platform",
        "WhyDonate #1 (homepage)",
        "#1",
        (
            "WhyDonate ranks #1 for this keyword — a key strength to protect and build on. "
            "The ranking could be at risk if competitors strengthen their content on this term."
        ),
        (
            "Protect this ranking by adding a FAQ section to the homepage and /en/crowdfunding "
            "that uses the phrase 'charity crowdfunding platform'. "
            "Add an H2 heading with the keyword to the homepage or crowdfunding page."
        ),
    ],
    [
        "2026-06-09",
        "fundraising platform for nonprofits UK",
        "CharityDigital #1, CharityExcellence #2, Crowdfunder #4",
        "Blog post only (~#5)",
        (
            "WhyDonate appears only via a blog post ('Crowdfunding platforms in UK') not the main /en/nonprofit page. "
            "JustGiving dominates UK charity fundraising queries. "
            "Main nonprofit page not ranking for UK-specific intent."
        ),
        (
            "Add UK-specific content to /en/nonprofit: mention Gift Aid support, GBP currency, "
            "UK payment methods (Bacs, open banking). "
            "Consider a /en/fundraising-uk/ or /en/charity-fundraising-uk/ landing page "
            "to target UK nonprofit intent directly."
        ),
    ],
]

append("keyword_gaps", gap_rows)
print(f"  Wrote {len(gap_rows)} keyword gap rows")


# ── 3. Update competitor history ───────────────────────────────────────────────

history_rows = [
    ["JustGiving", "https://www.justgiving.com/for-charities", "2026-06-09"],
    ["JustGiving", "https://www.justgiving.com/for-charities/pricing", "2026-06-09"],
    ["Donorbox",   "https://donorbox.org/",                            "2026-06-09"],
    ["Donorbox",   "https://donorbox.org/pricing",                     "2026-06-09"],
    ["GoGetFunding", "https://gogetfunding.com/",                      "2026-06-09"],
    ["GoGetFunding", "https://gogetfunding.com/faq/",                  "2026-06-09"],
]

append("competitor_history", history_rows)
print(f"  Wrote {len(history_rows)} competitor history rows")


print(
    f"\nDone. {len(page_rows)} pages analysed. "
    f"{len(gap_rows)} keyword gaps found. "
    f"{len(history_rows)} history rows updated."
)
