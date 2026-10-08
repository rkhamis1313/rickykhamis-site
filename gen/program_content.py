#!/usr/bin/env python3
"""Content for the five core program pages. Read by build_programs.py.

Separated from the builder because this is writing, not code, and it is the
part that will be edited.

Sourcing rule for this file: every agency figure names the agency and the date
it was published. Where a figure moves annually and could not be confirmed
against the issuing agency, the text explains the mechanism and sends the
reader to the agency instead of printing a number that will be wrong in a year.
The FHA county limit is the live example. Sources disagreed on Maricopa
County's 2026 figure, so no figure appears here.
"""

# Reused across pages. The one number on this site that decides which rulebook
# a file falls under, so it is written once.
CONFORMING = (
    'For 2026 the baseline conforming loan limit for a one-unit property is '
    '<strong>$832,750</strong>, announced by the Federal Housing Finance Agency on 25 November '
    '2025. Maricopa County is not a designated high-cost area, so that baseline is the number '
    'that applies in Phoenix, Scottsdale and across the East Valley. The multi-unit baselines '
    'are $1,066,250 for two units, $1,288,800 for three and $1,601,750 for four.'
)

PROGRAMS = [

# ---------------------------------------------------------------------- FHA
 dict(
  path='loan-programs/fha-loans',
  title='FHA Loans in Arizona: The 3.5% Down Program, and the Mortgage Insurance Rule Nobody Explains',
  h1='FHA loans',
  lede=('Government-insured financing that reaches credit profiles conventional guidelines turn '
        'away. The down payment is the part everyone knows. The mortgage insurance is the part '
        'that decides what it actually costs you.'),
  description=('How FHA loans work in Maricopa County: the 3.5% and 10% down tiers, why the '
               'annual mortgage insurance premium runs 11 years on some files and the full term '
               'on others, what the FHA appraisal flags in older East Valley housing, and when '
               'conventional is the cheaper answer.'),
  form='purchase',
  hook=('Your score came back in the low 600s, or there is a collection on the report you '
        'forgot about, and the last person you spoke to stopped returning calls.'),
  sections=[
   ('What FHA is actually for', [
     'FHA is not a first-time buyer program, and nothing about it requires you to be one. It is '
     'mortgage insurance sold by the federal government to the lender, which lets the lender '
     'accept a credit profile and a down payment that conventional guidelines will not. That is '
     'the whole mechanism. Everything else follows from it.',
     'The practical result is that FHA reaches three borrowers conventional financing frequently '
     'will not: the borrower with a thin or bruised credit file, the borrower with very little '
     'saved, and the borrower whose debt-to-income ratio needs more room than conventional '
     'underwriting allows. If none of those describe you, FHA is probably the wrong answer, and '
     'the section below on when conventional wins is the one to read.',
   ]),
   ('The down payment tiers, and what sits behind them', [
     'With a credit score of 580 or above, the minimum down payment is <strong>3.5%</strong>. '
     'Between 500 and 579 it is <strong>10%</strong>. Below 500 there is no FHA loan.',
     'The entire down payment may come from a gift, which is the quietest advantage in the '
     'program and the one that most often turns a renter into an owner. A documented gift from a '
     'family member can fund all of it. Conventional programs allow gifts too, but FHA pairs the '
     'gift allowance with the credit flexibility, and that combination is why the program exists.',
     'Arizona is a community property state. On an FHA file that matters: the debts of a spouse '
     'who is not on the loan can still be counted in your ratio even though their income and '
     'credit are not. If you are married and buying alone, that is a conversation to have before '
     'you shop, not after.',
   ]),
   ('The mortgage insurance rule that decides everything', [
     'FHA charges two premiums. An upfront premium, normally financed into the loan, and an '
     'annual premium collected monthly. The upfront one is a cost. The annual one is a decision, '
     'and almost nobody explains it before closing.',
     'Under HUD Mortgagee Letter 2013-04, the rule that still governs current files, the annual '
     'premium runs for <strong>11 years</strong> when the loan-to-value at origination is 90% or '
     'below, and for the <strong>full mortgage term</strong> when it is above 90%. The '
     'loan-to-value for this test is the base loan amount before the upfront premium is financed, '
     'divided by the lesser of the purchase price or the appraised value.',
     'Read that against the down payment tiers and the trap is obvious. Put 3.5% down and you are '
     'at 96.5% loan-to-value, above 90%, and the monthly mortgage insurance never comes off. Put '
     '10% down and you are at 90%, and it ends after 11 years. Same program, same borrower, and '
     'the only way off the premium in the first case is to refinance out of FHA entirely.',
     'So the real FHA question is not whether you can get approved. It is what the exit looks '
     'like. For most buyers the honest plan is to use FHA to get into the house, build to 20% '
     'equity through payments and appreciation, and refinance into a conventional loan where the '
     'insurance terminates by law. That plan should be on the table at application, not '
     'discovered in year four.',
     'One more wrinkle worth knowing if you already own: loans with case numbers assigned before '
     '3 June 2013 followed older rules under which the premium could cancel. If you have an '
     'existing FHA loan, the case number date changes whether refinancing out is worth doing.',
   ]),
   ('County loan limits, and why no number appears here', [
     'FHA limits are set county by county, adjusted annually, and calculated from area median '
     'home prices within a statutory floor and ceiling. The floor is 65% of the conforming '
     'baseline, which puts it at $541,287 for 2026. Maricopa County sits above the floor.',
     'Published sources disagreed on the exact Maricopa figure for 2026 when this page was '
     'written, so none is printed here. Use HUD\'s own county lookup, or ask us and we will '
     'confirm it against the agency before you write an offer. A page that prints the wrong '
     'number confidently is worse than one that tells you where the right number lives.',
   ]),
   ('The appraisal is a condition review, not just a value opinion', [
     'This is where FHA files die in the East Valley, and it has nothing to do with the borrower. '
     'An FHA appraiser is checking that the property meets minimum property standards: safety, '
     'security and soundness. The valuation is only half the assignment.',
     'In practice, on homes built before the mid 1980s, that means peeling exterior paint, missing '
     'or loose stair and balcony handrails, a water heater without a proper temperature and '
     'pressure relief discharge line, exposed or spliced wiring, roof covering with no remaining '
     'service life, inoperable windows, and unpermitted enclosures. Pool fencing and barrier '
     'requirements come up constantly here. Any of these can become a condition that must be '
     'repaired before closing, and on a seller who will not repair, the deal is over.',
     'None of that is a reason to avoid FHA. It is a reason to know, before you write, whether '
     'the house you picked is an FHA house. That is a fifteen minute conversation and it saves '
     'contracts.',
   ]),
   ('When conventional is the cheaper answer', [
     'If your score is 680 or better and you can reach 5% down, run both. Conventional private '
     'mortgage insurance is priced off your score and your loan-to-value, it is frequently '
     'cheaper than FHA\'s annual premium at that credit tier, and by law it terminates. FHA\'s '
     'does not, above 90% loan-to-value.',
     'Compare them over the number of years you will actually own the house, not over the first '
     'month. A payment that is slightly lower today and carries insurance for thirty years is not '
     'the cheaper loan. That comparison is the work, and it is the reason to price a file with '
     'someone who has access to both rather than someone selling one.',
   ]),
  ],
  geo_heading='Where FHA fits across the East Valley',
  geo_intro=('The program is federal. What it runs into is local: the age of the housing, the '
             'price point against the county limit, and whether the property is attached.'),
  cities={
   'Mesa': 'The oldest and largest housing stock in the East Valley, so Mesa files turn on the '
           'appraisal condition review rather than the credit file. Paint, handrails, water '
           'heater discharge lines and unpermitted Arizona rooms are the recurring findings. '
           'Price points sit comfortably inside the county limit, so the limit is rarely what '
           'binds here.',
   'Gilbert': 'Mostly built after the mid 1990s, so condition findings are uncommon. The live '
              'question is builder incentives, which are usually structured around a conventional '
              'loan with the builder\'s own lender. Price both before you accept the credit.',
   'Chandler': 'Credit profiles along the Price corridor tend to run higher, which means FHA '
               'frequently loses to conventional at 3% down once the mortgage insurance is '
               'compared across the years you will own the home rather than the first payment.',
   'Tempe': 'Attached housing is the Tempe market, and FHA requires the condominium project to be '
            'FHA approved or the individual unit to qualify under single-unit approval. That one '
            'check ends more Tempe FHA contracts than any borrower issue does. Verify it before '
            'you write.',
   'Scottsdale': 'FHA works in south Scottsdale and around Old Town, where price points stay under '
                 'the county limit. North of the 101 the limit is usually the binding constraint '
                 'rather than anything about the borrower.',
   'Phoenix': 'The widest price range of the eight cities. FHA reaches most of Phoenix '
              'comfortably. In Arcadia, the Biltmore corridor and the central historic districts '
              'the county limit is what runs out first.',
   'Queen Creek': 'New construction and larger parcels, well inside the county limit. The '
                  'appraisal here also picks up septic systems and shared wells that simply do not '
                  'exist in the tract subdivisions further west.',
   'Paradise Valley': 'Effectively outside the program. The county limit does not reach the entry '
                      'price of this market, so a Paradise Valley purchase is a conventional, '
                      'jumbo or portfolio conversation instead.',
  },
  faq=[
   ('Do I have to be a first-time buyer to use an FHA loan?',
    'No. There is no first-time buyer requirement. FHA is a credit and down payment program, not '
    'a status program.'),
   ('Does FHA mortgage insurance ever go away?',
    'It depends on the loan-to-value at origination. At 90% or below the annual premium runs 11 '
    'years. Above 90%, which includes every 3.5% down file, it runs for the full mortgage term '
    '(HUD Mortgagee Letter 2013-04). The only exit above 90% is refinancing out of FHA.'),
   ('Can my down payment be a gift?',
    'Yes. A properly documented gift from an eligible source can fund the entire down payment, '
    'which is one of the most useful features of the program.'),
   ('What credit score do I need?',
    '580 reaches the 3.5% minimum down payment. 500 to 579 requires 10% down. Lenders may apply '
    'their own higher minimums on top of FHA\'s, which is one reason to work with a broker rather '
    'than a single lender.'),
   ('Will the house I want pass an FHA appraisal?',
    'Usually, but the appraiser reviews safety, security and soundness, not only value. On homes '
    'built before the mid 1980s the common findings are paint, handrails, roof life, wiring and '
    'pool barriers. Ask before you write the offer, not after.'),
   ('I already have an FHA loan. Should I refinance out of it?',
    'Frequently yes, if you are above 90% original loan-to-value and have built equity, because '
    'that premium does not terminate on its own. Check the case number date first: loans with '
    'case numbers assigned before 3 June 2013 followed different cancellation rules.'),
  ],
  related=[
   ('/loan-programs/conventional-loans/', 'Conventional loans',
    'The program FHA borrowers usually refinance into, and the one where mortgage insurance '
    'terminates by law.'),
   ('/loan-programs/down-payment-assistance/', 'Down payment assistance',
    'Assistance toward the down payment and closing costs, which pairs with FHA on many files.'),
   ('/loan-programs/fha-203k-loan/', 'FHA 203k renovation loan',
    'Buy and repair with one loan, which is the answer when the appraisal condition findings are '
    'the obstacle.'),
  ],
 ),

# ----------------------------------------------------------------------- VA
 dict(
  path='loan-programs/va-loans',
  title='VA Loans in Arizona: Full Entitlement, the Funding Fee Exemption, and the Refund Most Veterans Never Claim',
  h1='VA loans',
  lede=('Zero down, no monthly mortgage insurance, and since 2020 no county loan limit at all if '
        'your entitlement is intact. The benefit is larger than most people are told.'),
  description=('How VA loans work in Arizona: why full entitlement removes the county loan limit, '
               'who is exempt from the funding fee, the refund available when a disability claim '
               'is still pending at closing, and how used entitlement changes the math.'),
  form='zero-down',
  hook=('You earned this benefit, and then someone told you a VA offer would get you beaten out '
        'or that your price range was capped. Both are usually wrong.'),
  sections=[
   ('Full entitlement removed the loan limit, and most people still do not know', [
     'Effective for loans closed on or after 1 January 2020, under the Blue Water Navy Vietnam '
     'Veterans Act of 2019, <strong>there are no county loan limits for a veteran with full '
     'entitlement</strong>. The VA says so plainly on its own site. The old county cap that '
     'everyone remembers does not apply to you if your entitlement has not been used, or has been '
     'used and restored.',
     'That changes which houses are on the table. It means a veteran with full entitlement can buy '
     'in north Scottsdale or Paradise Valley on a VA loan, which most agents and a surprising '
     'number of loan officers assume is impossible.',
     'Full entitlement does not mean unlimited. The lender still underwrites your credit, income, '
     'debts and assets, and the VA caps the loan at the appraised value or the purchase price, '
     'whichever is lower. What it removes is the arbitrary county ceiling.',
   ]),
   ('If you have used your entitlement before, the limit comes back', [
     'This is the part that gets missed. County loan limits still apply to a veteran who has '
     'previously used entitlement and not restored it, on a loan above $144,000. In that case '
     'your remaining entitlement is 25% of the county loan limit, reduced by the entitlement you '
     'used and have not restored.',
     'Practically: if you still own a home financed with a VA loan, or sold one without restoring '
     'entitlement, your second use is a different calculation than your first. It is still a '
     'strong loan, frequently still zero down, but the arithmetic has to be done before you shop '
     'rather than after you are in contract.',
     'Your Certificate of Eligibility shows both your exemption status and the entitlement '
     'already charged. Pull the COE first. Every other decision depends on what it says.',
   ]),
   ('The funding fee, and who does not pay it', [
     'There is no monthly mortgage insurance on a VA loan. Instead there is a one-time funding '
     'fee, which varies with your down payment and whether this is a first or subsequent use, and '
     'is normally financed into the loan.',
     'A large share of veterans are <strong>exempt from it entirely</strong>. Per the VA, the '
     'exemption covers veterans receiving VA compensation for a service-connected disability; '
     'veterans who would be entitled to that compensation but receive retirement or active duty '
     'pay instead; surviving spouses receiving Dependency and Indemnity Compensation; active duty '
     'service members with a proposed or memorandum rating issued before closing (VA Circular '
     '26-23-19); and active duty Purple Heart recipients.',
     'On a mid-six-figure purchase the exemption is worth thousands of dollars at the closing '
     'table. It is not automatic in the sense that nobody has to look it up: the lender has to '
     'confirm the exemption status before closing. If your file is being handled by someone who '
     'never asked about a disability rating, ask.',
   ]),
   ('The pending claim refund, which almost nobody is told about', [
     'If a disability claim is still pending when you close, the funding fee <strong>must</strong> '
     'be collected as though you were not exempt. That is the rule, and it feels wrong at the '
     'time.',
     'But if the claim is later awarded with an effective date retroactive to a date before your '
     'loan closed, you can seek a refund of the fee. Veterans lose real money here simply because '
     'nobody told them to go back and ask after the award came through.',
     'If you have a claim in process and you are buying now, write the date down. Close the loan, '
     'and when the award arrives, check the effective date against your closing date.',
   ]),
   ('Beating the "VA offers are weak" problem', [
     'The belief that a VA offer is a liability in a competitive market is stale, and it costs '
     'veterans houses. The appraisal has minimum property requirements, which is the legitimate '
     'root of the concern, and those requirements look a great deal like FHA\'s: safety, '
     'soundness, functioning systems, roof life, no exposed wiring, pool barriers.',
     'The fix is not to abandon the benefit. The fix is to pick properties that clear those '
     'requirements, and to have the listing agent shown the strength of the file up front: a '
     'full underwritten approval rather than a pre-qualification, a COE in hand, and a loan '
     'officer whose phone number is on the letter and who answers it. Sellers are not refusing VA, '
     'they are refusing uncertainty.',
   ]),
  ],
  geo_heading='Where the VA benefit goes furthest across the East Valley',
  geo_intro=('Zero down is federal. What changes by city is the supply of homes that clear the '
             'property requirements and whether the price point needs full entitlement.'),
  cities={
   'Mesa': 'A large veteran population and the deepest supply of homes in a comfortable VA price '
           'range. The minimum property requirements hit the older Mesa stock the same way FHA\'s '
           'do, so the property choice matters more here than the loan does.',
   'Gilbert': 'New construction. Get the COE and a complete file in hand before signing a builder '
              'contract, because the builder\'s completion date and the appraisal timing are the '
              'two clocks that collide on these files.',
   'Chandler': 'Competitive, frequently against cash. A VA offer holds up here when the listing '
               'agent has been shown an underwritten approval rather than a pre-qualification '
               'printout.',
   'Tempe': 'Attached housing has to be on the VA approved condominium project list. There is no '
            'single-unit workaround on the VA side the way FHA has one, so check the list before '
            'you write an offer on a Tempe condo.',
   'Scottsdale': 'This is where full entitlement matters most. With no county limit in play, VA '
                 'financing reaches Scottsdale price points that most agents assume are off the '
                 'table for a veteran.',
   'Phoenix': 'Central Phoenix puts you near the Phoenix VA Medical Center. If you are reporting '
              'to Luke Air Force Base, that is a west valley commute and worth driving on a '
              'weekday morning before you choose a neighborhood.',
   'Queen Creek': 'New build and acreage, popular with veterans leaving base housing. Zero down '
                  'works, and the closing costs still need a plan, which is where seller '
                  'concessions earn their keep.',
   'Paradise Valley': 'Reachable on full entitlement, which surprises people. The binding '
                      'constraints become the appraisal and the lender\'s own overlays rather than '
                      'anything the VA imposes.',
  },
  faq=[
   ('Is there a VA loan limit in Maricopa County?',
    'Not if you have full entitlement. For loans closed on or after 1 January 2020 there are no '
    'county loan limits for veterans with full entitlement. If you have used entitlement and not '
    'restored it, county limits apply to the remaining calculation.'),
   ('Do I pay the VA funding fee?',
    'Not if you are exempt. Exemptions include veterans receiving service-connected disability '
    'compensation, those entitled to it who take retirement or active duty pay instead, surviving '
    'spouses receiving DIC, active duty members with a proposed or memorandum rating before '
    'closing, and active duty Purple Heart recipients.'),
   ('My disability claim is still pending. What happens at closing?',
    'The fee must be collected as if you were not exempt. If the claim is later awarded with an '
    'effective date before your closing date, you can seek a refund. Keep the closing date and '
    'check it against the award.'),
   ('Can I use a VA loan more than once?',
    'Yes. Entitlement can be restored, and many veterans use the benefit several times. The '
    'calculation on a second use differs from the first, so it needs to be run before you shop.'),
   ('Is there monthly mortgage insurance on a VA loan?',
    'No. That is one of the structural advantages of the program compared with FHA and with '
    'conventional financing above 80% loan-to-value.'),
   ('Will sellers reject my VA offer?',
    'Some are wary because of the property requirements. The answer is property selection plus a '
    'fully underwritten approval the listing agent can verify, not giving up the benefit.'),
  ],
  related=[
   ('/loans-for-heroes/', 'Loans for heroes',
    'What we do for service members, veterans, first responders, teachers and medical '
    'professionals.'),
   ('/loan-programs/jumbo-loans/', 'Jumbo loans',
    'Where full entitlement reaches past the conforming limit, and what the alternatives look '
    'like.'),
   ('/analyze/', 'Send me an address',
    'One address in, a full written analysis back within 24 hours at no charge.'),
  ],
 ),

# ------------------------------------------------------------- CONVENTIONAL
 dict(
  path='loan-programs/conventional-loans',
  title='Conventional Loans in Arizona: The 2026 Limits, and Exactly When Your PMI Comes Off',
  h1='Conventional loans',
  lede=('The default rulebook for a well-qualified file, and the one program where the mortgage '
        'insurance is required by law to end. Knowing the two dates is worth more than shopping '
        'the rate.'),
  description=('Conventional financing in Maricopa County: the 2026 conforming loan limits, how '
               'private mortgage insurance cancels at 80% and terminates automatically at 78% '
               'under the Homeowners Protection Act, and when FHA still wins.'),
  form='purchase',
  hook=('You put five percent down, and the mortgage insurance line on the disclosure made the '
        'payment meaningfully higher than the number you had been planning around.'),
  sections=[
   ('The limit that decides which rulebook you are in', [
     CONFORMING,
     'One dollar over that limit and you are in a different program with different reserve '
     'requirements, different ratio ceilings and different pricing. Because Maricopa sits at the '
     'baseline rather than in a high-cost tier, there is no intermediate high-balance step here. '
     'The cliff is sharp, which means structuring around it is frequently worth real money. More '
     'on that on the <a href="/loan-programs/jumbo-loans/">jumbo page</a>.',
   ]),
   ('Private mortgage insurance ends. Here are the two dates', [
     'This is the single most valuable thing to understand about conventional financing, and it is '
     'federal law rather than a lender courtesy. Under the Homeowners Protection Act, as the '
     'Consumer Financial Protection Bureau describes it, there are two triggers and they work '
     'differently.',
     '<strong>Borrower-requested cancellation at 80%.</strong> You send the servicer a written '
     'request. The eligible date is either the date the balance is <em>scheduled</em> to reach 80% '
     'of the original value, or the earlier date it reaches 80% based on the payments you actually '
     'made. Approval also requires a good payment history, being current, certifying there are no '
     'junior liens, and evidence that the value has not fallen below the original value.',
     '<strong>Automatic termination at 78%.</strong> You do not have to ask. The servicer must '
     'terminate on the date the balance is scheduled to reach 78% of original value, provided you '
     'are current. Current property value is not a factor, so the servicer may not require you to '
     'pay for an appraisal as a condition of automatic termination. And it cannot be accelerated: '
     'extra payments do not move this date.',
     'That asymmetry is the whole strategy. Paying extra principal moves the <em>80% request</em> '
     'date closer. It does nothing to the <em>78% automatic</em> date. So if you intend to pay '
     'down aggressively, the written request is how you capture the benefit, and almost nobody '
     'sends it.',
     'If neither trigger fires, coverage still cannot be imposed past the first day of the month '
     'after the midpoint of the amortization period, which on a 30-year loan is after 15 years. '
     'Unearned premiums must be returned within 45 days of cancellation or termination. High-risk '
     'loans are carved out of the 80% and 78% rules and fall under the midpoint rule instead.',
   ]),
   ('Why that makes conventional the usual exit from FHA', [
     'Put the two programs side by side. Above 90% loan-to-value at origination, FHA\'s annual '
     'mortgage insurance premium runs for the full mortgage term and the only way out is to '
     'refinance (HUD Mortgagee Letter 2013-04). Conventional private mortgage insurance '
     'terminates by statute, on a schedule you can calculate the day you close.',
     'That is why the standard plan for an FHA buyer is not to keep the FHA loan. It is to use FHA '
     'to get in, build to 20% equity, and move to a conventional loan where the insurance has an '
     'end date. If nobody has walked you through that timeline, you are holding half the plan.',
   ]),
   ('Low down payment conventional, and the appraisal waiver', [
     'Conventional financing reaches as low as 3% down on qualifying files, which surprises people '
     'who assume FHA is the only low down payment route. At a 680 or better score the private '
     'mortgage insurance at that leverage is frequently cheaper than FHA\'s annual premium, and it '
     'ends. Run both. The comparison is the deliverable.',
     'The automated underwriting may also offer an appraisal waiver, which removes days and a fee '
     'from the transaction. Waivers show up most often on homes in large tract subdivisions with '
     'deep comparable sales data, and effectively never on unique or custom properties. That is '
     'worth knowing when you are choosing between a Gilbert production home and a custom build in '
     'Paradise Valley on the same timeline.',
   ]),
   ('When FHA still wins', [
     'If your score sits below the mid 600s, or there is recent credit damage, or your ratio needs '
     'more room than conventional underwriting allows, FHA will frequently approve a file that '
     'conventional declines, and an approval beats a cheaper loan you cannot have.',
     'The honest version is that these two programs are not rivals. They are two tools, and which '
     'one is right depends on your credit tier, your leverage and how long you will own the '
     'house. Anyone who recommends one before looking at all three is guessing.',
   ]),
  ],
  geo_heading='What changes by city across the East Valley',
  geo_intro=('The agency rulebook is national. The appraisal, the price point against the '
             'conforming limit, and the property type are local.'),
  cities={
   'Mesa': 'Older stock means a full appraisal is more likely than a waiver, so build the contract '
           'timeline around an appraisal rather than hoping for one to be waived.',
   'Gilbert': 'Large tract subdivisions with deep comparable data, which is exactly where '
              'appraisal waivers actually happen. When one is offered it shortens the timeline and '
              'removes a fee.',
   'Chandler': 'The dual-income Price corridor file. How base salary, bonus and equity '
               'compensation are documented moves the qualifying number far more than the rate '
               'does, and the rules for each of the three differ.',
   'Tempe': 'Warrantability. A conventional loan on an attached unit turns on the project review: '
            'investor concentration, single-entity ownership, commercial space and whether the '
            'budget funds reserves. Check it before the offer.',
   'Scottsdale': 'Price points cross from conforming into jumbo within a few miles, so the 2026 '
                 'limit is the line that decides which rulebook applies to your file.',
   'Phoenix': 'Historic districts and unique properties are where appraisal waivers disappear and '
              'a deliberate appraisal strategy earns its keep.',
   'Queen Creek': 'New construction with long completion windows, which makes a lock strategy, '
                  'not a rate quote, the thing you actually need.',
   'Paradise Valley': 'Almost always above the conforming limit, which puts these purchases under '
                      'the jumbo rulebook instead.',
  },
  faq=[
   ('What is the conforming loan limit in Maricopa County for 2026?',
    '$832,750 for a one-unit property. Maricopa is not a high-cost area, so the national baseline '
    'applies (Federal Housing Finance Agency, announced 25 November 2025).'),
   ('When does PMI come off a conventional loan?',
    'Two triggers. You may request cancellation when the balance reaches 80% of original value, '
    'and the servicer must terminate automatically at 78% scheduled, if you are current. Coverage '
    'also cannot continue past the amortization midpoint.'),
   ('Does paying extra principal get rid of PMI sooner?',
    'It can move the 80% borrower-request date up, because that date may be based on actual '
    'payments. It does not move the 78% automatic termination date, which is based on the '
    'scheduled balance.'),
   ('Can the servicer make me pay for an appraisal to remove PMI?',
    'Not for automatic termination at 78%, where current value is not a factor. For a borrower '
    'request at 80% the servicer may require evidence that the value has not declined below the '
    'original value.'),
   ('How little can I put down on a conventional loan?',
    'As little as 3% on qualifying files. At a 680 or better score the mortgage insurance at that '
    'leverage is frequently cheaper than FHA\'s, and unlike FHA above 90% loan-to-value, it ends.'),
   ('Conventional or FHA?',
    'Credit tier, leverage and how long you will own the home decide it. Above the mid 600s with '
    '5% down, conventional usually costs less over the hold. Below that, or with recent credit '
    'damage, FHA frequently approves what conventional will not.'),
  ],
  related=[
   ('/loan-programs/fha-loans/', 'FHA loans',
    'The program with the wider credit box, and the mortgage insurance rule that makes this page '
    'matter.'),
   ('/loan-programs/jumbo-loans/', 'Jumbo loans',
    'What happens one dollar above the conforming limit, and how to structure around the cliff.'),
   ('/buydown-calculator/', 'Rate buydown calculator',
    'Compares temporary and permanent buydowns funded with the same seller concession.'),
  ],
 ),

# -------------------------------------------------------------------- JUMBO
 dict(
  path='loan-programs/jumbo-loans',
  title='Jumbo Loans in Scottsdale and Paradise Valley: The $832,750 Cliff and How to Structure Around It',
  h1='Jumbo loans',
  lede=('Financing above the conforming limit. In Maricopa County there is no high-balance step '
        'in between, so the rules change all at once, at one number.'),
  description=('Jumbo financing in Maricopa County for 2026: where the conforming limit sits, why '
               'there is no high-balance tier here, what changes in reserves and documentation '
               'above the line, and the alternatives for a self-employed or asset-rich borrower.'),
  form='purchase',
  hook=('You are buying at a price that works comfortably on paper, and the lender has come back '
        'asking for a year of reserves and two appraisals on a file you were told was strong.'),
  sections=[
   ('Where the line is, and why it is a cliff here', [
     CONFORMING,
     'Many metros have a high-cost designation that creates a middle tier between conforming and '
     'jumbo, with agency pricing and agency rules at a higher limit. <strong>Maricopa County does '
     'not.</strong> Arizona median values stay below the threshold that triggers the high-cost '
     'exception, so Phoenix, Scottsdale, Paradise Valley and the whole East Valley sit at the '
     'baseline.',
     'The consequence is specific and expensive: there is no gentle step. At $832,750 you are an '
     'agency loan. At $832,751 you are a jumbo loan, underwritten to an investor\'s own rulebook, '
     'with different reserves, different ratio ceilings, different appraisal requirements and '
     'different pricing. Nowhere else does a single dollar change so much about a mortgage.',
   ]),
   ('What actually changes above the line', [
     'Reserves are the first thing. Agency guidelines frequently require little or none on a '
     'primary residence. Jumbo investors routinely want months of full housing payment held in '
     'verified accounts after closing, and the requirement scales with loan size and leverage.',
     'Documentation gets heavier. Expect a complete asset trail, sourcing on every large deposit, '
     'and more scrutiny of income that is not a simple salary. Debt-to-income ceilings tighten, '
     'and the compensating factors that would rescue an agency file carry less weight.',
     'Appraisal requirements change. At higher loan amounts and on unique properties, a second '
     'appraisal or a desk review is common, which costs both money and days. In Paradise Valley '
     'and the custom pockets of north Scottsdale, where comparable sales are thin and every house '
     'is different, that is the normal case rather than the exception.',
   ]),
   ('Structuring around the cliff', [
     'There are three usual moves, and they are worth pricing before you accept a jumbo quote.',
     'Bring the first lien under the limit. A larger down payment, or a seller credit applied to '
     'reduce the loan amount, can land the first mortgage at or below $832,750 and put the entire '
     'file back under agency rules. On a purchase sitting a few thousand dollars over the line, '
     'this is frequently the cheapest decision available.',
     'Split the financing. An agency first at the limit plus a second lien for the balance keeps '
     'the large loan under the friendlier rulebook. Whether it wins depends on the blended cost '
     'against a single jumbo, which is arithmetic, not opinion.',
     'Or go deliberately jumbo. On a larger purchase, or where the down payment is better deployed '
     'elsewhere, a single jumbo loan is the right structure. The point is not that jumbo is bad. '
     'The point is that nobody should land in it by accident because a number crept over a line.',
   ]),
   ('If your income is not a salary', [
     'Jumbo underwriting is least forgiving to exactly the borrowers who buy at these price '
     'points: business owners, physicians in their first year, people whose wealth is in a '
     'portfolio rather than a paycheck. A tax return that is written to minimize taxable income '
     'does not describe the money available to pay a mortgage, and an agency rulebook has no field '
     'for the difference.',
     'That is what the alternatives are for. <a href="/self-employed-home-loans/">Bank statement '
     'and P&amp;L documentation</a> qualifies a business owner on deposits or a third-party '
     'prepared profit and loss statement rather than returns. <a href="/asset-based-home-loans/">'
     'Asset depletion and asset qualifier programs</a> convert a portfolio into qualifying income '
     'or test a residual balance. <a href="/physician-home-loans/">Physician programs</a> reach '
     'to $2,000,000 with no mortgage insurance at any loan-to-value and will use a signed '
     'employment contract instead of pay history.',
     'A file declined as a jumbo is frequently approvable under one of those three. That is the '
     'argument for a broker with multiple investors rather than a bank with one shelf.',
   ]),
  ],
  geo_heading='Where jumbo actually applies across the East Valley',
  geo_intro=('Against a single countywide limit, the map is simple: a few places are mostly jumbo, '
             'most places are mostly not, and a few sit right on the line.'),
  cities={
   'Paradise Valley': 'The core jumbo market in the metro. Entry prices sit above the conforming '
                      'limit, so nearly every purchase is a jumbo or portfolio file, and thin '
                      'comparable sales make the appraisal the long pole.',
   'Scottsdale': 'North of the 101, and in Silverleaf, DC Ranch and Troon, the jumbo rulebook '
                 'applies. South Scottsdale and much of central Scottsdale stay conforming, so the '
                 'program can change between two houses you tour the same afternoon.',
   'Phoenix': 'Arcadia, the Biltmore corridor and parts of north central are jumbo. Most of the '
              'rest of the city is comfortably under the limit.',
   'Chandler': 'The top of the Ocotillo and south Chandler new-construction range crosses the '
               'limit, frequently by a small margin, which is precisely the situation where '
               'structuring the first lien under the line pays.',
   'Gilbert': 'The upper tiers in Agritopia, Seville and the custom pockets reach jumbo. Lot '
              'premiums and builder options are usually what push a conforming contract over, and '
              'those are negotiable.',
   'Mesa': 'Jumbo is the exception here, concentrated in Las Sendas and the northeast against the '
           'Tonto National Forest boundary.',
   'Tempe': 'Rarely jumbo. When it is, it is usually a multi-unit property or a custom home rather '
            'than standard single-family stock.',
   'Queen Creek': 'Acreage and custom builds reach jumbo; the tract product does not. On larger '
                  'parcels the appraisal and the land value are what complicate the file.',
  },
  faq=[
   ('What makes a loan jumbo in Maricopa County?',
    'A first mortgage above $832,750 on a one-unit property for 2026. Maricopa is at the national '
    'baseline because it is not a designated high-cost area (Federal Housing Finance Agency, '
    'announced 25 November 2025).'),
   ('Is there a high-balance tier in Phoenix or Scottsdale?',
    'No. Arizona median values stay below the high-cost threshold, so there is no intermediate '
    'step between conforming and jumbo here. The rules change all at once.'),
   ('How much in reserves will a jumbo loan require?',
    'More than an agency loan, scaling with loan size and leverage, and held in verified accounts '
    'after closing. The requirement is set by the investor, not by an agency, so it varies and is '
    'worth shopping.'),
   ('My purchase is just over the limit. What are my options?',
    'Three: increase the down payment or apply a seller credit to bring the first lien under the '
    'limit, split into an agency first plus a second lien, or price a single jumbo and compare. On '
    'a file a few thousand dollars over the line, the first option is often the cheapest.'),
   ('I am self-employed and was declined for a jumbo. Now what?',
    'Bank statement, third-party P&L, asset depletion and asset qualifier programs all exist for '
    'that exact file and underwrite it differently. A jumbo decline on tax returns is not the end '
    'of the question.'),
   ('Will I need two appraisals?',
    'Sometimes, at higher loan amounts or on unique properties. In Paradise Valley and the custom '
    'areas of north Scottsdale it is common enough to plan for in the timeline.'),
  ],
  related=[
   ('/self-employed-home-loans/', 'Self-employed home loans',
    'Bank statement, P&L and written verification routes for a business owner whose returns '
    'understate the income.'),
   ('/asset-based-home-loans/', 'Asset based home loans',
    'Asset depletion and asset qualifier programs for a borrower whose wealth is a portfolio '
    'rather than a paycheck.'),
   ('/physician-home-loans/', 'Physician home loans',
    'To $2,000,000 with no mortgage insurance at any loan-to-value, on a signed employment '
    'contract.'),
  ],
 ),

# ------------------------------------------------------------- CASH OUT / REFI
 dict(
  path='loan-programs/mortgage-refinance',
  title='Refinance and Cash-Out in Arizona: The Blended Rate, the 80% Ceiling, and What You Are Actually Trading',
  h1='Mortgage refinance and cash-out',
  lede=('Lower the rate, shorten the term, or turn equity into cash. Three different decisions '
        'with three different tests, and the honest one is rarely the one being advertised.'),
  description=('Refinancing and cash-out in Maricopa County: why the blended rate is the number '
               'that matters, the loan-to-value ceilings on conventional, FHA and VA cash-out, '
               'what consolidating unsecured debt actually costs you, and when a second lien beats '
               'a refinance.'),
  form='refinance',
  hook=('You are carrying consumer debt at a rate that is genuinely punishing, and a first '
        'mortgage at a rate you would be sorry to lose.'),
  sections=[
   ('The number almost nobody runs: your blended rate', [
     'People shop a refinance against their mortgage rate. That is the wrong comparison when there '
     'is other debt in the picture.',
     'The right number is the balance-weighted blended rate across everything secured by the home '
     'plus everything you are thinking of paying off. A first mortgage at a comfortable rate, a '
     'second lien, a card balance at a punitive rate and a vehicle loan do not average to the '
     'first mortgage rate. They average to something considerably higher, and that blended number '
     'is what a new loan has to beat.',
     'Run it before you decide anything. Our '
     '<a href="/cash-out-refinance-calculator/">cash-out refinance calculator</a> takes every loan '
     'and every debt with its balance, rate and payment, and returns the blended rate you carry '
     'today, the new loan amount and loan-to-value, and a payment priced off the most recent '
     'Freddie Mac survey average, refreshed daily and shown dated.',
   ]),
   ('The ceilings, by program', [
     'Cash-out is capped by loan-to-value, and the cap depends on which program you are in.',
     'Conventional cash-out on a primary residence is generally limited to <strong>80%</strong> of '
     'value. FHA cash-out is also limited to 80%. VA cash-out can reach higher for an eligible '
     'veteran, which is one of the least-used advantages of that benefit. Investment property '
     'cash-out is tighter than all of them, and on a <a href="/dscr-investor-loans/">DSCR '
     'file</a> the rent against the new payment has to still clear the coverage ratio at the '
     'higher balance.',
     'Those ceilings are set by the program and move with guideline updates, so confirm the '
     'current figure on your own file. The structural point does not move: the equity you can '
     'reach is a fraction of the equity you have, and the fraction depends on the rulebook.',
   ]),
   ('What consolidating unsecured debt actually trades', [
     'This is the part that gets left out of the advertisement, and it matters.',
     'Credit card and personal loan balances are unsecured. Nobody can take your house over them. '
     'Roll them into a mortgage and they become secured against your home. The monthly number goes '
     'down, frequently by a lot, and the nature of the risk changes completely. That can still be '
     'the right decision. It should be a decision you made on purpose.',
     'The second trade is time. Paying off a card balance over thirty years at a mortgage rate can '
     'cost more total interest than paying it off over four years at a card rate, even though the '
     'monthly payment is a fraction of the size. The way to capture the benefit without paying for '
     'it twice is to keep paying the old combined total after closing and let the difference hit '
     'principal. That single habit is what separates a consolidation that works from one you '
     'repeat in three years.',
     'The third trade is the amortization clock. A new 30-year loan restarts it. If you are eleven '
     'years into a mortgage, compare the new loan against a shorter term before you assume thirty '
     'years is the answer.',
   ]),
   ('When a second lien beats a refinance', [
     'If the rate on your first mortgage is materially better than what is available today, '
     'refinancing the whole balance to access equity means repricing debt you are happy with in '
     'order to reach debt you are not.',
     'In that situation a second lien, a home equity line or a fixed second, frequently wins. You '
     'keep the first mortgage untouched and borrow only the amount you actually need, at a higher '
     'rate on a much smaller balance. The blended result is usually better than a full refinance, '
     'and the arithmetic is straightforward once someone bothers to do it.',
     'There is a third structure worth knowing about: the '
     '<a href="/all-in-one-loan/">All In One Loan</a>, a first-lien line of credit where your '
     'deposits sit against the balance every day and reduce the interest accruing. It is not for '
     'everyone, and it rewards a borrower with real cash flow moving through the account. There is '
     'a simulator on that page.',
   ]),
   ('If your current loan is FHA, check the case number first', [
     'An existing FHA loan carries a mortgage insurance premium, and whether that premium can ever '
     'cancel on its own depends on when the case number was assigned.',
     'Loans with case numbers assigned on or after 3 June 2013 follow the current rule: the annual '
     'premium runs 11 years at 90% original loan-to-value or below, and for the full mortgage term '
     'above 90% (HUD Mortgagee Letter 2013-04). Older case numbers followed different cancellation '
     'rules.',
     'That single date changes the whole analysis. If you are above 90% original loan-to-value on '
     'a post-2013 FHA loan and you now have 20% equity, refinancing into a conventional loan ends '
     'an insurance premium that would otherwise run for the life of the loan. That saving is '
     'frequently larger than the rate difference people are shopping, and it is routinely missed.',
   ]),
  ],
  geo_heading='Equity positions across the East Valley',
  geo_intro=('A cash-out is decided by how much seasoned equity sits in the property, and that is '
             'mostly a function of when the neighborhood was built and when you bought.'),
  cities={
   'Mesa': 'The deepest seasoned equity in the East Valley, because the housing stock is the '
           'oldest. Also the most likely to carry an FHA loan with a pre-2013 case number, which '
           'changes the analysis entirely.',
   'Gilbert': 'Largely purchased during the growth of the 2010s, so owners hold meaningful equity '
              'and a first mortgage rate worth protecting. That combination usually argues for a '
              'second lien rather than a full refinance.',
   'Chandler': 'The same shape as Gilbert. Strong equity, a first lien many owners should not '
               'touch, and a consumer debt balance that is the actual problem to solve.',
   'Tempe': 'Long-held rentals and owner-occupied homes near the university, frequently owned free '
            'and clear or close to it, which opens options that a leveraged property does not have.',
   'Scottsdale': 'High balances, which means the 2026 conforming limit decides whether your '
                 'cash-out is an agency loan or a jumbo one, with the tighter ceilings and reserve '
                 'requirements that come with it.',
   'Phoenix': 'The widest spread of equity positions of the eight cities, from historic district '
              'homes held for decades to recent purchases with very little equity yet.',
   'Queen Creek': 'The newest stock and the least seasoned equity, so a cash-out frequently does '
                  'not clear the loan-to-value ceiling yet. Worth checking rather than assuming, '
                  'because appreciation has been uneven.',
   'Paradise Valley': 'Nearly always a jumbo cash-out, with tighter loan-to-value ceilings and '
                      'heavier reserve requirements than the agency rules above.',
  },
  faq=[
   ('How much equity can I take out?',
    'Conventional and FHA cash-out on a primary residence are generally limited to 80% of value. '
    'VA cash-out can reach higher for an eligible veteran. Investment property is tighter. '
    'Confirm the current figure on your own file, because these move with guideline updates.'),
   ('Should I consolidate credit cards into my mortgage?',
    'Sometimes, and it is a real trade. The payment drops and the debt becomes secured against '
    'your home. The way to make it work is to keep paying the old combined total afterward so the '
    'difference goes to principal.'),
   ('My first mortgage rate is good. Can I still access equity?',
    'Yes, usually with a second lien rather than a refinance. You keep the first mortgage and '
    'borrow only what you need. The blended cost is frequently better than repricing the whole '
    'balance.'),
   ('I have an FHA loan. Is refinancing worth it just to drop the insurance?',
    'Frequently yes, if the case number was assigned on or after 3 June 2013, the original '
    'loan-to-value was above 90% and you now have 20% equity. That premium runs for the full term '
    'and refinancing is the only exit.'),
   ('Does a refinance restart my 30 years?',
    'A new 30-year loan does. Compare a shorter term before assuming thirty, especially if you are '
    'already years into the current loan.'),
   ('What does the calculator need from me?',
    'Every loan secured by the home and every debt you are thinking of paying off, each with its '
    'balance, rate and payment. That is what produces the blended rate, which is the number the '
    'decision actually turns on.'),
  ],
  related=[
   ('/cash-out-refinance-calculator/', 'Cash-out refinance calculator',
    'Blended rate, new loan-to-value and a payment priced off the latest Freddie Mac survey '
    'average, refreshed daily.'),
   ('/all-in-one-loan/', 'All In One Loan',
    'A first-lien line of credit where daily deposits reduce the interest accruing. Includes a '
    'simulator.'),
   ('/loan-programs/conventional-loans/', 'Conventional loans',
    'Where mortgage insurance terminates by law, which is frequently the reason to refinance out '
    'of FHA.'),
  ],
 ),
]
