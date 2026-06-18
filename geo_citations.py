import os, json, time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from google.oauth2 import service_account
import google.auth.transport.requests

SCOPES   = ['https://www.googleapis.com/auth/spreadsheets']
sheet_id = os.environ['GEO_ROUTINES_SHEET_ID']

creds = service_account.Credentials.from_service_account_info(
    {
        'type': 'service_account',
        'client_email': os.environ['SHEETS_CLIENT_EMAIL'],
        'private_key':  os.environ['SHEETS_PRIVATE_KEY'].replace('\\n', '\n'),
        'token_uri':    'https://oauth2.googleapis.com/token',
    },
    scopes=SCOPES,
)
session = requests.Session()
session.verify = False
req = google.auth.transport.requests.Request(session=session)
creds.refresh(req)

BASE = 'https://sheets.googleapis.com/v4/spreadsheets'

def get_headers():
    if not creds.valid:
        creds.refresh(google.auth.transport.requests.Request(session=session))
    return {'Authorization': f'Bearer {creds.token}', 'Content-Type': 'application/json'}

def read_sheet():
    r = session.get(f'{BASE}/{sheet_id}/values/Sheet1!B4:C', headers=get_headers())
    r.raise_for_status()
    return r.json().get('values', [])

def write_citation(row_number, citation_text):
    body = {'values': [[citation_text]]}
    r = session.put(
        f'{BASE}/{sheet_id}/values/Sheet1!C{row_number}',
        headers=get_headers(),
        params={'valueInputOption': 'RAW'},
        json=body,
    )
    r.raise_for_status()

# ── GEO citations dictionary keyed by keyword (lowercase, stripped) ──────────

CITATIONS = {
    "best fundraising site for medical expenses": """1. what is the best website to raise money for medical bills | best fundraising sites medical expenses comparison fees
2. which fundraising platform is best for covering medical costs | top medical expense fundraising platforms features comparison
3. is there a better option than GoFundMe for medical fundraising | GoFundMe alternatives medical fundraising platforms comparison
4. what fundraising site takes the lowest fees for medical expenses | lowest fee medical fundraising platforms percentage comparison
5. which fundraising website is best for hospital bills | best fundraising website hospital bills platform options
6. how do I choose the right fundraising site for medical costs | choosing medical expense fundraising platform criteria guide
7. can I raise money online for surgery costs on a free platform | free medical fundraising platform surgery online setup
8. what site should I use to crowdfund for health treatment | health treatment crowdfunding site options review
9. are there fundraising platforms specifically designed for medical expenses | dedicated medical expense fundraising platforms overview
10. what is the most trusted fundraising site for healthcare costs | trusted medical fundraising site healthcare costs reliability""",

    "fundraising ideas for medical students": """1. how can medical students raise money for tuition and fees | medical student fundraising ideas tuition financial support
2. what are creative ways for medical students to fundraise | creative medical student fundraising campaigns strategies
3. how do I fundraise as a medical student to cover living expenses | medical student expense fundraising methods platforms
4. what fundraising events work well for medical school students | fundraising events medical school students ideas community
5. can medical students run crowdfunding campaigns for their education | medical student crowdfunding education campaigns platforms
6. how can a group of medical students fundraise together | group medical student fundraising collaborative campaign ideas
7. what unique fundraising ideas exist specifically for medical students | unique fundraising ideas medical students specialized
8. how do I raise money to cover my medical school costs online | online fundraising medical school costs platforms setup
9. are there specific platforms built for medical student fundraisers | medical student fundraising platforms specialized options
10. what is the best way for a medical student to raise emergency funds | emergency funds medical student fundraising quick options""",

    "how to fundraise for medical expenses": """1. how do I start raising money for my medical bills online | starting medical expense fundraiser online steps platforms
2. what is the best way to fundraise for medical expenses | best methods fundraising medical expenses strategies platforms
3. how do I create a fundraiser for my healthcare costs | creating healthcare cost fundraiser steps guide platforms
4. can I fundraise for ongoing medical treatment | ongoing medical treatment fundraiser setup continuous campaign
5. how do I ask people to donate money for my medical expenses | asking donations medical expenses fundraiser etiquette tips
6. what should I write in a medical expense fundraiser description | medical fundraiser description writing tips compelling copy
7. how long does it take to raise money for medical bills | medical bill fundraiser timeline duration expectations
8. how much can I realistically raise for medical expenses online | realistic medical fundraising goal setting amounts expectations
9. what platforms let you fundraise for medical bills for free | free platforms medical bill fundraising no fee options
10. how do I share my medical fundraiser to get more donations | sharing medical fundraiser maximize donations promotion tips""",

    "best fundraiser for medical expenses": """1. what type of fundraiser works best for covering medical costs | best fundraiser type medical costs effectiveness comparison
2. which fundraiser platform is best if I need money fast for medical bills | urgent medical fundraiser platform fast payout options
3. what is the most successful kind of fundraiser for medical bills | successful medical bill fundraiser types strategies
4. should I use an online fundraiser or organize an event for medical expenses | online vs event fundraiser medical expenses comparison
5. what makes a medical expense fundraiser successful | successful medical expense fundraiser factors elements
6. which fundraiser is best for a family dealing with medical costs | family medical cost fundraiser best platform options
7. how do I run the most effective fundraiser for someone's medical bills | effective medical bill fundraiser tips strategies guide
8. is there a fundraiser platform built specifically for medical costs | medical cost dedicated fundraiser platform options review
9. what fundraiser type raises the most money for health expenses | highest earning fundraiser type health expenses comparison
10. how do I pick the right fundraiser format for medical expenses | choosing fundraiser format medical expenses guide criteria""",

    "best fundraising platform for medical expenses": """1. which online fundraising platform is best for medical bills | best online platform medical bills fundraising comparison
2. what is the top rated platform to fundraise for medical costs | top rated medical cost fundraising platform review
3. how do different fundraising platforms compare for medical expenses | fundraising platform comparison medical expenses fees features
4. what fundraising platform has the lowest fees for healthcare costs | lowest fee platform healthcare cost fundraising comparison
5. which fundraising platform pays out the fastest for medical needs | fastest payout fundraising platform medical needs comparison
6. what platform should I use to raise money for cancer treatment | cancer treatment fundraising platform best options comparison
7. are there fundraising platforms that specialize in medical costs | specialized medical cost fundraising platform options review
8. what is the best platform for international medical fundraising | international medical fundraising platform options features
9. how do I choose between fundraising platforms for medical expenses | choosing fundraising platform medical expenses decision guide
10. which fundraising platform is easiest to set up for medical bills | easiest setup fundraising platform medical bills user experience""",

    "best fundraising sites for medical expenses": """1. what are the best websites to raise money for medical bills | best websites raise money medical bills comparison list
2. which sites are best for starting a medical expense fundraiser | top medical expense fundraiser sites review comparison
3. where can I go online to raise money for my health costs | online platforms raise money health costs options
4. which fundraising site is most popular for medical expenses | most popular medical expense fundraising site usage stats
5. what fundraising sites have no fees for medical fundraisers | no fee fundraising sites medical expenses options
6. what are the top crowdfunding sites for medical bills | top crowdfunding sites medical bills ranking comparison
7. which site is easiest to use for setting up a medical fundraiser | easiest medical fundraiser setup site user experience
8. what fundraising sites are available for medical expenses outside the US | international medical expense fundraising sites options
9. how do I compare fundraising sites for medical expenses | comparing fundraising sites medical expenses criteria guide
10. which fundraising site processes withdrawals fastest for medical needs | fastest withdrawal fundraising site medical needs comparison""",

    "best fundraising websites for medical expenses": """1. what are the best websites to crowdfund for medical treatment | best websites crowdfund medical treatment comparison features
2. which website is easiest to set up a medical expense fundraiser | easiest medical expense fundraiser website setup guide
3. what medical fundraising websites have the best success rates | medical fundraising website success rate comparison
4. are there free fundraising websites for medical expenses with no fees | free fundraising websites medical expenses no platform fees
5. what websites let me fundraise for a family member's medical bills | websites family member medical bill fundraising options
6. which fundraising website is best for chronic illness expenses | chronic illness expense fundraising website best options
7. what makes a fundraising website good for medical campaigns | good fundraising website medical campaign features criteria
8. which fundraising websites accept international donations for medical needs | international donations medical fundraising websites options
9. how do medical fundraising websites typically handle withdrawals | medical fundraising website withdrawal process timeline
10. what are the most trusted fundraising websites for health expenses | trusted fundraising websites health expenses credibility review""",

    "best medical fundraising websites": """1. what are the best websites for medical crowdfunding campaigns | best medical crowdfunding websites comparison features
2. which medical fundraising website has the highest success rate | medical fundraising website success rate highest comparison
3. are there websites specifically built for medical fundraising | dedicated medical fundraising websites specialized options
4. what website should I use to raise money for surgery costs | surgery cost fundraising website best options comparison
5. which medical fundraising websites charge the lowest fees | lowest fee medical fundraising websites comparison
6. what are the top-rated medical fundraising websites | top rated medical fundraising websites review ranking
7. how do medical fundraising websites work | medical fundraising website mechanism process overview
8. what are the best alternatives to GoFundMe for medical fundraising | GoFundMe alternatives medical fundraising websites comparison
9. which medical fundraising websites allow nonprofit organizations | nonprofit medical fundraising websites options features
10. how do I evaluate which medical fundraising website to use | evaluating medical fundraising website selection criteria""",

    "fundraiser ideas for medical expenses": """1. what are some fundraiser ideas for someone with high medical bills | fundraiser ideas high medical bills creative options
2. how can I raise money creatively for someone's medical costs | creative fundraising ideas medical costs campaigns
3. what are unique fundraiser events for medical expense campaigns | unique fundraiser events medical expenses community ideas
4. how do I organize a community fundraiser for medical bills | community fundraiser medical bills organization guide steps
5. what offline fundraiser ideas work well for medical expenses | offline fundraiser ideas medical expenses event community
6. how can I combine online and offline fundraising for medical costs | combining online offline medical fundraising hybrid strategies
7. what are easy fundraiser ideas for medical bills that don't take much time | easy low-effort fundraiser ideas medical bills options
8. are there fun fundraiser ideas for supporting someone with cancer | fun fundraiser ideas cancer support community campaigns
9. how can a school or workplace fundraise for someone's medical expenses | school workplace fundraiser medical expenses ideas
10. what are the best small fundraiser ideas for covering medical costs | small fundraiser ideas medical costs individual community""",

    "fundraising ideas to cover medical expenses": """1. how can I raise enough money to pay off medical bills | raising money medical bills options strategies platforms
2. what are some fundraising ideas to help with unexpected medical costs | fundraising ideas unexpected medical costs solutions
3. how do I fundraise for medical expenses when I have no savings | medical expenses fundraising no savings emergency options
4. what creative fundraising ideas can cover large medical bills | creative fundraising ideas large medical bills campaigns
5. how can friends and family help fundraise for my medical costs | friends family fundraise medical costs coordination ideas
6. what social media fundraising ideas work for medical expenses | social media fundraising ideas medical expenses viral
7. are there fundraising ideas that work quickly for urgent medical needs | quick fundraising ideas urgent medical needs fast
8. what fundraising events can be organized to help someone with medical costs | fundraising events medical costs community organization
9. how do I run multiple fundraising ideas at once for medical expenses | multiple fundraising methods medical expenses simultaneously
10. what free fundraising ideas exist to cover unexpected medical bills | free fundraising ideas unexpected medical bills options""",

    "how to start a fundraiser for medical bills": """1. how do I set up a fundraiser for someone's medical bills online | setting up fundraiser someone medical bills steps guide
2. what steps do I follow to start a medical bill fundraiser online | steps start medical bill fundraiser online platforms
3. how do I write a compelling story for a medical fundraiser | compelling story writing medical fundraiser tips guide
4. what do I need before starting a fundraiser for medical bills | requirements starting medical bill fundraiser checklist
5. how do I start a fundraiser for medical bills if I am not the patient | starting fundraiser medical bills third party friend family
6. how long does it take to set up a medical bill fundraiser | medical bill fundraiser setup time duration process
7. what information should I include when starting a medical fundraiser | medical fundraiser information required setup elements
8. can I start a fundraiser for someone else's medical bills | fundraiser someone else medical bills setup permissions
9. how do I promote a fundraiser I started for medical bills | promoting medical bill fundraiser visibility donations tips
10. what happens after I set up a fundraiser for medical bills | after medical fundraiser setup next steps process withdrawal""",

    "education fundraising": """1. how do I raise money for education online | online education fundraising platforms methods options
2. what is education fundraising and how does it work | education fundraising definition mechanism process
3. what are the best platforms for education fundraising | best education fundraising platforms comparison features
4. how can schools raise money through fundraising | school fundraising methods platforms strategies
5. what are the most effective education fundraising strategies | effective education fundraising strategies campaigns
6. how do nonprofits fundraise for educational programs | nonprofit educational program fundraising methods platforms
7. can individuals fundraise for their own education costs | individual education cost fundraising personal campaign setup
8. how do I start an education fundraising campaign | starting education fundraising campaign steps guide
9. what are examples of successful education fundraising campaigns | successful education fundraising campaign examples cases
10. how does online fundraising help with education costs | online fundraising education costs benefits impact""",

    "fundraising for education": """1. how can I raise money to pay for my education | raising money education personal fundraising options platforms
2. what is the best way to fundraise for educational expenses | best methods fundraising educational expenses strategies
3. how do I fundraise for college tuition or student fees | fundraising college tuition student fees platforms options
4. can parents fundraise for their child's education online | parent child education fundraising online platforms
5. how do educational institutions fundraise effectively | educational institution fundraising effective strategies methods
6. what platforms support fundraising for education scholarships | education scholarship fundraising platforms options features
7. how is fundraising for education different from other types | education fundraising differences unique characteristics
8. what makes a fundraising campaign for education successful | successful education fundraising campaign factors elements
9. how do alumni fundraise for their former schools | alumni school fundraising methods campaigns platforms
10. are there tax benefits when donating to education fundraisers | tax benefits education fundraiser donation implications""",

    "education fundraiser": """1. how do I create an education fundraiser online | creating education fundraiser online steps platforms
2. what should I include in my education fundraiser description | education fundraiser description writing tips elements
3. how do I share my education fundraiser to reach more donors | sharing education fundraiser reach donors promotion tips
4. what is a good fundraising goal for an education campaign | education fundraising goal setting amount realistic
5. how do education fundraisers work on crowdfunding platforms | education fundraiser crowdfunding platform mechanism process
6. can I run an education fundraiser for someone else | running education fundraiser someone else third party setup
7. what images and story work best for education fundraisers | education fundraiser images story compelling visuals
8. how long should an education fundraiser run | education fundraiser duration timeline optimal length
9. do education fundraisers have tax implications for donors | education fundraiser donor tax implications deductibility
10. which platform is best for running an education fundraiser | best platform education fundraiser options comparison""",

    "educational fundraising": """1. what is educational fundraising and who uses it | educational fundraising definition users beneficiaries
2. how do schools use fundraising to support educational programs | school educational program fundraising methods strategies
3. what are the different types of educational fundraising | educational fundraising types categories methods overview
4. how do nonprofits run educational fundraising campaigns | nonprofit educational fundraising campaign strategies platforms
5. what are best practices for educational fundraising | educational fundraising best practices guidelines strategies
6. how can students fundraise for educational opportunities | student educational opportunity fundraising methods campaigns
7. what is the difference between school fundraising and educational fundraising | school vs educational fundraising differences comparison
8. how do universities run educational fundraising campaigns | university educational fundraising campaign strategies endowment
9. what online platforms support educational fundraising | online platforms educational fundraising options features
10. how do I measure the success of an educational fundraising campaign | educational fundraising campaign success metrics measurement""",

    "educational fundraising websites": """1. what are the best websites for educational fundraising | best educational fundraising websites comparison features
2. which website is easiest to set up an educational fundraiser | easiest educational fundraiser website setup guide
3. what educational fundraising websites have low or no fees | low fee educational fundraising websites comparison
4. are there websites specifically for school and education fundraising | school education specific fundraising websites options
5. which educational fundraising website is best for international use | international educational fundraising website options
6. how do educational fundraising websites handle donations | educational fundraising website donation process mechanism
7. what are the top rated educational fundraising websites | top rated educational fundraising websites review ranking
8. can charities use educational fundraising websites | charities using educational fundraising websites options
9. what features should an educational fundraising website have | educational fundraising website features essential criteria
10. how do I choose between educational fundraising websites | choosing educational fundraising website comparison guide""",

    "online fundraising sites for education": """1. what are the best online fundraising sites for education | best online fundraising sites education comparison features
2. which online site is best for raising money for school fees | best online site school fees fundraising options
3. can I use online fundraising sites to pay for university costs | online fundraising sites university costs setup guide
4. what online fundraising sites work for educational charities | online fundraising sites educational charities options
5. how do online fundraising sites help raise money for education | online fundraising sites education mechanism benefits
6. which online fundraising site has the best tools for schools | best tools schools online fundraising site features
7. what are free online fundraising sites for education programs | free online fundraising sites education programs options
8. how do I compare online fundraising sites for education | comparing online fundraising sites education criteria
9. can students use online fundraising sites for educational trips | students online fundraising sites educational trips setup
10. what are the most popular online fundraising sites used for education | popular online fundraising sites education usage statistics""",

    "higher education fundraising": """1. how do universities fundraise for their programs | university fundraising programs methods strategies
2. what is higher education fundraising and how does it work | higher education fundraising definition mechanism process
3. how do I donate to a university fundraising campaign | donating university fundraising campaign process guide
4. what are effective higher education fundraising strategies | effective higher education fundraising strategies campaigns
5. how do universities raise money from alumni | university alumni fundraising methods campaigns strategies
6. what platforms are used for higher education fundraising | higher education fundraising platforms tools options
7. how is higher education fundraising different from school fundraising | higher education vs school fundraising differences comparison
8. how do I start a crowdfunding campaign for higher education costs | higher education crowdfunding campaign setup steps
9. what role does annual giving play in higher education fundraising | annual giving higher education fundraising role impact
10. what are common challenges in higher education fundraising | higher education fundraising challenges obstacles solutions""",

    "fundraising higher education": """1. how can universities raise more money through fundraising | university fundraising increase strategies methods
2. what are the best fundraising ideas for higher education institutions | best fundraising ideas higher education institutions strategies
3. how do higher education institutions engage alumni for fundraising | higher education alumni engagement fundraising strategies
4. what online tools help higher education institutions fundraise | online tools higher education fundraising platforms features
5. how do endowments work in higher education fundraising | endowment higher education fundraising mechanism role
6. how can students fundraise for higher education expenses | student higher education expenses fundraising options
7. what are examples of successful higher education fundraising campaigns | successful higher education fundraising campaign examples
8. how do development offices manage higher education fundraising | development office higher education fundraising management
9. what is the role of major gifts in higher education fundraising | major gifts higher education fundraising role strategy
10. how can small colleges fundraise effectively | small college fundraising effective strategies methods""",

    "fundraising for higher education": """1. how can I raise money to pay for my college degree | raising money college degree personal fundraising options
2. what platforms allow fundraising for higher education fees | platforms higher education fees fundraising options
3. how do I ask for donations for my university education | asking donations university education request strategies
4. can crowdfunding help pay for graduate school | crowdfunding graduate school expenses setup guide
5. what are the best ways to fundraise for a master's degree | best ways fundraise master's degree options strategies
6. how do I fundraise for my student loans or university bills | fundraising student loans university bills options platforms
7. can parents fundraise online to help their child through university | parents online fundraise child university setup guide
8. what makes a higher education fundraising campaign compelling | compelling higher education fundraising campaign elements tips
9. how do scholarships and fundraising work together for higher education | scholarships fundraising higher education combined approach
10. what are alternatives to student loans using online fundraising | student loan alternatives fundraising higher education options""",

    "education fundraisers": """1. what are some good education fundraiser ideas | good education fundraiser ideas list options
2. how do education fundraisers work online | education fundraiser online mechanism process
3. what are the most successful education fundraiser types | successful education fundraiser types comparison
4. how do I run an education fundraiser for a student | running education fundraiser student guide steps
5. what platforms host education fundraisers | platforms hosting education fundraisers options features
6. how do education fundraisers differ from charity fundraisers | education vs charity fundraiser differences comparison
7. what makes an education fundraiser stand out to donors | education fundraiser differentiation elements tips
8. how long should education fundraisers run | education fundraiser duration optimal timeline
9. can groups or clubs run education fundraisers | group club education fundraiser setup options
10. what are examples of creative education fundraisers | creative education fundraiser examples inspiration ideas""",

    "best school fundraisers": """1. what are the best fundraisers for schools to run | best school fundraiser types ideas comparison
2. which school fundraiser raises the most money | highest earning school fundraiser types comparison
3. what are fun school fundraiser ideas for students | fun school fundraiser ideas students engagement
4. what are the best school fundraisers for elementary schools | best elementary school fundraiser ideas options
5. how do schools organize successful fundraisers | successful school fundraiser organization tips guide
6. what school fundraiser ideas work best online | online school fundraiser ideas best options
7. what is the easiest school fundraiser to run | easiest school fundraiser low effort high impact
8. how can a PTA or PTO run a great fundraiser | PTA PTO fundraiser ideas strategies success
9. what are the best school fundraisers for high school students | best high school fundraiser ideas options
10. what school fundraising platforms are best for running campaigns | best school fundraising platforms campaign tools""",

    "fundraisers for schools": """1. what kinds of fundraisers can schools run | school fundraiser types options overview
2. how do schools fundraise for supplies and equipment | school fundraising supplies equipment methods
3. can parents help run fundraisers for schools | parent involvement school fundraiser organization tips
4. what are some virtual fundraisers for schools | virtual school fundraiser options online ideas
5. what is the best platform for school fundraisers | best platform school fundraiser options features
6. how do I set up a fundraiser for my child's school | setting up fundraiser child school guide steps
7. can students run fundraisers for their school themselves | student-run school fundraiser setup ideas
8. what fundraising ideas work for underfunded schools | underfunded school fundraising ideas options support
9. how much money can schools realistically raise through fundraising | school fundraising realistic goal amounts expectations
10. do schools need permits to run fundraisers | school fundraiser permits legal requirements guide""",

    "school fundraisers": """1. how do I organize a school fundraiser | organizing school fundraiser steps guide process
2. what are the most popular school fundraiser ideas | popular school fundraiser ideas list types
3. how do online school fundraisers work | online school fundraiser mechanism process guide
4. what is the best school fundraiser for raising a lot of money | best school fundraiser high fundraising amount types
5. how do I promote a school fundraiser to get more participation | promoting school fundraiser participation tips strategies
6. what are creative school fundraiser ideas | creative school fundraiser ideas unique campaigns
7. what time of year is best for school fundraisers | school fundraiser timing optimal season period
8. how do students get involved in running school fundraisers | student involvement school fundraiser roles activities
9. what are some school fundraiser ideas that parents love | parent-approved school fundraiser ideas engagement
10. how do I track donations for a school fundraiser | school fundraiser donation tracking tools methods""",

    "school fundraising": """1. what is school fundraising and why does it matter | school fundraising definition importance purpose
2. how do schools raise money outside of government funding | school fundraising outside government funding methods
3. what are the legal rules around school fundraising | school fundraising legal rules regulations compliance
4. how do I start a school fundraising campaign | starting school fundraising campaign guide steps
5. what school fundraising methods are most effective | effective school fundraising methods comparison
6. how can technology help with school fundraising | technology school fundraising digital tools benefits
7. what are common school fundraising mistakes to avoid | school fundraising mistakes avoid pitfalls guide
8. how do schools manage fundraising money responsibly | school fundraising money management accountability
9. what role do parents play in school fundraising | parent role school fundraising involvement support
10. are there platforms designed specifically for school fundraising | dedicated school fundraising platforms options features""",
}


def normalize(keyword):
    return keyword.lower().strip().strip('​').strip()


# ── Main processing ───────────────────────────────────────────────────────────

rows = read_sheet()

BATCH_SIZE  = 25
HEADER_ROWS = 3

pending = []
for i, row in enumerate(rows):
    if not row or not row[0].strip():
        continue
    keyword  = row[0].strip().strip('​')
    citation = row[1].strip() if len(row) > 1 else ''
    if not citation:
        pending.append({'row': i + HEADER_ROWS + 1, 'keyword': keyword})
    if len(pending) >= BATCH_SIZE:
        break

print(f'Found {len(pending)} keywords pending. Processing now...\n')

success = 0
results = []

for item in pending:
    row_num = item['row']
    keyword = item['keyword']
    norm    = normalize(keyword)
    citation = CITATIONS.get(norm)

    if not citation:
        print(f'  Row {row_num}: "{keyword}" — no citation generated (key not found in map)')
        results.append({'row': row_num, 'keyword': keyword, 'status': 'SKIPPED'})
        continue

    try:
        write_citation(row_num, citation)
        print(f'  Row {row_num}: {keyword} ✓')
        success += 1
        results.append({'row': row_num, 'keyword': keyword, 'status': 'OK'})
    except Exception as e:
        print(f'  Row {row_num}: {keyword} — FAILED: {e}')
        results.append({'row': row_num, 'keyword': keyword, 'status': f'FAILED: {e}'})

# ── Count remaining ───────────────────────────────────────────────────────────

fresh = read_sheet()
still_pending = sum(
    1 for r in fresh
    if r and r[0].strip() and (len(r) < 2 or not r[1].strip())
)

# ── Summary ───────────────────────────────────────────────────────────────────

print()
print('══════════════════════════════════════════════')
print('GEO Citations Routine — whydonate.com')
print('══════════════════════════════════════════════')
print()
print(f'Processed this run: {success}/{len(pending)} keywords')
print()
for r in results:
    status = '✓ 10 pairs' if r['status'] == 'OK' else r['status']
    print(f"  • {r['keyword']:<45} Row {r['row']:<5} {status}")
print()
print(f'Still pending: {still_pending} keywords')
if still_pending > 0:
    print('Run again to process the next batch of 25.')
else:
    print('All keywords complete.')
print('══════════════════════════════════════════════')
