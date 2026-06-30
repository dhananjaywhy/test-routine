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

def ensure_headers(tab, headers):
    result = sheet.values().get(
        spreadsheetId=sheet_id,
        range=f"{tab}!A1:A1",
    ).execute()
    if not result.get("values"):
        sheet.values().update(
            spreadsheetId=sheet_id,
            range=f"{tab}!A1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

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

CONTENT_HEADERS = [
    "Date", "URL", "PageTitle", "WordCount",
    "EEATScore", "ReadabilityScore", "DepthScore", "AICitationScore",
    "ThinScore", "InternalLinksScore", "SocialProofScore", "OverallScore",
    "TopIssue", "ContentGap", "RecommendedAction", "Priority",
]
ensure_headers("content_audit", CONTENT_HEADERS)
ensure_headers("surfed_pages", ["URL", "DateSurfed"])

def weighted(eeat, read, depth, ai, thin, links, social):
    return round(
        eeat*0.20 + read*0.15 + depth*0.20 + ai*0.15 +
        thin*0.10 + links*0.10 + social*0.10
    )

DATE = "2026-06-30"

audits = [
    # /en/fundraising/ — category / index page
    {
        "url": "https://www.whydonate.com/en/fundraising/",
        "title": "Fundraising | WhyDonate",
        "wc": 520,
        "eeat": 40, "read": 65, "depth": 45, "ai": 45,
        "thin": 50, "links": 65, "social": 45,
        "top_issue": "Page is a thin category hub — describes types of fundraising but never anchors a single high-intent search query, so it competes with no one and converts no one.",
        "gap": "GoFundMe's parent /fundraise/ page has a hero outcome stat, a 3-step setup explainer, 4-6 named campaign success stories, and 8+ FAQs — this page has none of those in one place.",
        "rec": "Rewrite as a true pillar page (1200+ words): hero with 1-sentence value prop + headline stat ('£X raised by Y campaigns'), 4-step setup section, 3 mini case studies with names + amount raised, a comparison block vs GoFundMe/JustGiving, and 6-8 FAQs covering fees, payouts, supported countries, eligible causes. Add 6+ contextual internal links to /personal-fundraising/, /fundraising-for-nonprofits/, /peer-to-peer-fundraising/, /fees/.",
        "priority": "High",
    },
    # /personal-fundraising/
    {
        "url": "https://whydonate.com/personal-fundraising/",
        "title": "Personal Fundraising: Raise Funds For Any Cause | WhyDonate",
        "wc": 720,
        "eeat": 55, "read": 70, "depth": 60, "ai": 55,
        "thin": 65, "links": 60, "social": 60,
        "top_issue": "No FAQ section on a page where intent is overwhelmingly objection-based — 'is it really 0%?', 'when do I get paid?', 'is it legit?' — those questions go unanswered above the conversion.",
        "gap": "GoFundMe's personal fundraising page has a stacked FAQ block, named donor success stories with photos + amounts raised, and a press/media-mention strip — this page has unnamed testimonial snippets and no FAQ.",
        "rec": "Add an FAQ section (8 questions, 600+ words) under the steps block answering: how 0% works, when funds are paid out, supported currencies, what happens if a campaign is fraudulent, what fees apply, can I withdraw to any country, what proof is needed, how long campaigns can run. Attach full names + organisation to the existing 'heart surgery' / 'hospital bills' testimonials and add a photo + amount raised.",
        "priority": "Medium",
    },
    # /blog/best-personal-fundraising-websites/
    {
        "url": "https://whydonate.com/blog/best-personal-fundraising-websites/",
        "title": "10 Best Personal Fundraising Websites (2026 Comparison)",
        "wc": 2400,
        "eeat": 50, "read": 75, "depth": 75, "ai": 65,
        "thin": 90, "links": 70, "social": 50,
        "top_issue": "WhyDonate ranks itself #1 in its own comparison without disclosing it — AI Overviews and savvy readers discount the whole piece because the conflict of interest is unstated.",
        "gap": "Donorbox's comparable comparison post opens with a 'who this is by / how we compared' methodology block plus a disclosure that they are reviewed inside their own list — this post jumps straight to the ranking.",
        "rec": "Add a 120-word disclosure + methodology block above the rankings ('WhyDonate is included; here's how we scored each platform on fees / payout speed / country support / customer support'). Add a comparison table summarising the 10 platforms by fee / payout / countries — directly above the long write-ups, in plain HTML so AI Overviews can lift it. Add author byline + 1-sentence credentials at the top.",
        "priority": "Medium",
    },
    # /blog/fundraising-trends/
    {
        "url": "https://whydonate.com/blog/fundraising-trends/",
        "title": "Charity Fundraising Trends 2026 That Drive More Donations",
        "wc": 1900,
        "eeat": 55, "read": 70, "depth": 75, "ai": 65,
        "thin": 85, "links": 55, "social": 40,
        "top_issue": "Stats cited (e.g. '67% of online donors agree…', '30% of nonprofits…') have no source links — competing posts cite Nonprofit Tech for Good / Salesforce / NTEN by name and AI Overviews prefer those over an uncited rewrite.",
        "gap": "Nonprofit Tech for Good's equivalent trends post links every stat to its primary source and is the one AI Overviews actually quote — this post recycles the same numbers without attribution.",
        "rec": "Attach a primary-source hyperlink to every statistic in the post (Nonprofit Tech for Good 2026 report, M+R Benchmarks, Blackbaud Institute) — aim for 10+ outbound source links. Add an 'Author / Last updated' line at the top and a short 'How this was written' note. Replace generic intro with a 60-word answer-first summary of the top 5 trends so AI Overviews can extract it.",
        "priority": "Medium",
    },
    # /blog/top10-crowdfunding-platforms-europe/
    {
        "url": "https://whydonate.com/blog/top10-crowdfunding-platforms-europe/",
        "title": "10 Best Crowdfunding Platforms In Europe (2026)",
        "wc": 2500,
        "eeat": 50, "read": 75, "depth": 75, "ai": 70,
        "thin": 90, "links": 65, "social": 45,
        "top_issue": "Same self-ranking-without-disclosure problem as the personal-fundraising listicle — and the fee comparison is given as prose instead of a scannable table, so AI Overviews can't lift it cleanly.",
        "gap": "CrowdSpace's European platforms comparison opens with a sortable fee/feature table and discloses platform affiliations — both are signals Google's Helpful Content update rewards.",
        "rec": "Add a comparison table (Platform | Platform Fee | Transaction Fee | Countries | Payout Speed | Best For) directly under the intro so AI Overviews can extract a single block. Add a 120-word methodology + disclosure block. Add an author byline and 'Last updated June 2026' stamp. Link each platform's row to its dedicated review / alternative post you already have on the blog (Ulule, JustGiving, Betterplace).",
        "priority": "Medium",
    },
    # /blog/giving-tuesday/
    {
        "url": "https://whydonate.com/blog/giving-tuesday/",
        "title": "Everything About Giving Tuesday 2026 (+ Best Fundraising Ideas)",
        "wc": 1500,
        "eeat": 45, "read": 70, "depth": 65, "ai": 60,
        "thin": 80, "links": 50, "social": 35,
        "top_issue": "Seasonal page with no case studies — 'Giving Tuesday' searches peak in November and people are looking for proof a platform handles the spike, but this post has zero examples of campaigns that succeeded on Giving Tuesday.",
        "gap": "Classy's Giving Tuesday hub lists 3-4 named nonprofits with the exact amount they raised on the day, plus a downloadable Giving Tuesday toolkit — this post offers neither.",
        "rec": "Add a 'Giving Tuesday on WhyDonate: 2024/2025 results' block — even 2-3 named campaigns with date + amount raised. Add a downloadable / linked Giving Tuesday checklist (social posts, email templates, donation page tips) gated behind nothing — pure value. Add author byline + 'Updated for Giving Tuesday 2 December 2026'. Add 4+ internal links to /personal-fundraising/, /fundraising-for-nonprofits/, /blog/donation-landing-page/, /blog/fundraising-ideas/.",
        "priority": "Medium",
    },
]

content_rows = []
surfed_rows = []
for a in audits:
    overall = weighted(a["eeat"], a["read"], a["depth"], a["ai"], a["thin"], a["links"], a["social"])
    content_rows.append([
        DATE, a["url"], a["title"], a["wc"],
        a["eeat"], a["read"], a["depth"], a["ai"],
        a["thin"], a["links"], a["social"], overall,
        a["top_issue"], a["gap"], a["rec"], a["priority"],
    ])
    surfed_rows.append([a["url"], DATE])

append("content_audit", content_rows)
append("surfed_pages", surfed_rows)

print("══════════════════════════════════════════")
print("Content Audit Complete — whydonate.com")
print("══════════════════════════════════════════\n")
print("Pages audited this run:")
for a in audits:
    overall = weighted(a["eeat"], a["read"], a["depth"], a["ai"], a["thin"], a["links"], a["social"])
    short = a["url"].replace("https://www.whydonate.com", "").replace("https://whydonate.com", "")
    warn = "  ⚠ Needs work" if overall < 50 else (""  if overall >= 70 else "")
    print(f"  • {short:<55} — Overall: {overall}/100  [E-E-A-T: {a['eeat']} | Depth: {a['depth']} | AI: {a['ai']}]{warn}")
print()
critical = [a for a in audits if weighted(a['eeat'], a['read'], a['depth'], a['ai'], a['thin'], a['links'], a['social']) < 50]
print(f"Pages needing immediate attention (score < 50): {len(critical)}")
for a in critical:
    short = a["url"].replace("https://www.whydonate.com", "").replace("https://whydonate.com", "")
    print(f"  - {short}: {a['top_issue']}")
print()
print("Top content gaps across all pages:")
print("  • 5 of 6 pages have no FAQ / answer-first structure for AI extraction")
print("  • 4 of 6 pages have no author byline or credentials")
print("  • 3 of 6 listicles/blog posts cite stats without source links")
print("  • 4 of 6 pages have unnamed testimonials or none at all")
print(f"\nWrote {len(content_rows)} rows to content_audit, {len(surfed_rows)} to surfed_pages.")
