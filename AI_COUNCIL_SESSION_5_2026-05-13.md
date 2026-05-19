# CreditDoc AI Council — Session 5: Quizzes, Courses & Educational Content

**Follow-up from Sessions 1-4 (May 13, 2026)**

**The Founder's Questions:**
1. Quizzes weren't in the priority list — they need to be. How should the quiz framework be linked into the site?
2. Should CreditDoc create courses or educational content? The site already has financial wellness guides and Q&A content. What's the highest-value way to expand this?
3. What's the best way to integrate quizzes given the existing site architecture?

**Context:**
- Quiz template already exists: `/tools/borrowing-power-quiz/` (908 lines, LIVE)
- 10 quiz variants designed: credit repair, credit building, debt relief, personal loans, business loans, credit cards, auto loans, mortgage, student loans, banking
- Email capture built into quiz flow (after Q3)
- Site already has: 85 wellness guides, 39 blog posts, 26 answer pages, 215 comparisons
- Content pipelines running: blog 2/day, wellness 2/day, answers daily, comparisons 5/day

---

## JACK DORSEY — Quizzes & Education

### On the Quiz Framework

The quiz is actually your most important conversion asset. Here's why it matters more than most people think:

**The quiz is the bridge between content and commerce.** Right now your site has thousands of pages of information. A visitor reads about credit repair, learns something, and leaves. The quiz is what turns a reader into a lead. "Now that you know about credit repair — let's find the right option for you."

**How to link it into the site:**

1. **Homepage hero.** Not buried in `/tools/`. The quiz should be the first thing someone sees when they land on CreditDoc. Credit Karma's homepage IS the credit score check. CreditDoc's homepage should BE "What do you need help with?" → quiz flow. This doesn't replace your directory — it sits on top of it as the primary call-to-action.

2. **End of every content piece.** Every wellness guide, every blog post, every answer page should end with a contextual quiz CTA. Read an article about credit repair? The CTA is "Find out which credit repair approach is right for you" → credit repair quiz. Read about personal loans? → personal loan quiz. Match the quiz to the content pillar.

3. **Embedded in city guides.** "Looking for credit help in Denver? Take our 60-second assessment" → quiz pre-filled with Denver, CO. The city guide is the landing page, the quiz is the conversion action.

4. **Sidebar on lender review pages.** Someone reading about a specific lender is deep in the consideration phase. "Not sure if this lender is right for you? Compare your options" → quiz.

5. **Standalone `/qualify/` URLs.** Keep the 10 `/qualify/credit-repair/`, `/qualify/personal-loans/` etc. pages. These rank for "do I qualify for credit repair" type queries and are direct-intent landing pages.

**The linking hierarchy:**
```
Homepage hero quiz (general)
    ↓ routes to
Pillar-specific quiz (/qualify/credit-repair/)
    ↓ results page shows
Personalized lender recommendations from your database
    ↓ each recommendation links to
Lender review page (/review/[slug]/)
    ↓ future: embedded origination
Apply button (Phase 2: MoneyLion/Lendio widget)
```

**Start with ONE.** Don't build all 10 quizzes. Build the credit repair quiz (your strongest pillar by GSC data). Wire it to the homepage, to every credit repair wellness guide, and to every credit repair city guide. Measure completion rate, email capture rate, and click-through to lender pages. Then replicate to the next pillar.

### On Courses & Educational Content

This is where I think CreditDoc has an underexploited opportunity.

**The wellness guides and answer pages are good. But they're isolated articles. Courses turn isolated articles into a structured journey.**

Think about what Khan Academy did for education. They didn't just publish articles. They created structured learning paths: "Start here → then this → then this → now you understand algebra." The structure IS the product.

**CreditDoc should do the same for financial literacy:**

"The CreditDoc Credit Repair Course" — free, 7 modules:
1. Understanding Your Credit Report (what's on it, how to read it)
2. Your Rights Under Federal Law (FCRA, CFPB, state protections)
3. How to Dispute Errors (step-by-step with templates)
4. Choosing a Credit Repair Company (using CFPB data to evaluate)
5. Building Credit After Repair (secured cards, credit builder loans)
6. Avoiding Predatory Lenders (red flags, what the data shows)
7. Your 90-Day Action Plan (personalized via quiz)

**Why this matters for traffic AND conversion:**

1. **SEO:** A structured course with 7 interlinked modules creates a topic cluster that Google loves. Each module targets different keywords. The course hub page links to all modules. All modules link back. Internal linking is built into the structure.

2. **Email capture:** "Get Module 1 free. Enter your email to unlock the full course." This is the highest-converting lead magnet in online education. Way better than "download our PDF checklist."

3. **Time on site:** A course keeps people on your site for 20-30 minutes across multiple pages. Google sees engagement metrics. Longer sessions = higher quality signal.

4. **Trust building:** Someone who completes your credit repair course TRUSTS CreditDoc. When the quiz recommends a lender, they click. Trust = conversion rate.

5. **AI-proof content:** AI Overviews can answer "what is a credit score." AI cannot replace a structured 7-module course with progress tracking, quizzes at the end of each module, and personalized recommendations. This is experiential content, not informational content.

6. **Affiliate natural integration:** Module 4 ("Choosing a Credit Repair Company") naturally recommends companies from your database, ranked by CFPB resolution rate. Module 5 ("Building Credit After Repair") naturally recommends secured cards and credit builder loans. The affiliate links are PART of the education, not bolted on.

**Courses I'd build (in order):**

| Course | Modules | Target Audience | Monetization Hook |
|---|---|---|---|
| Credit Repair 101 | 7 | People with bad credit | Credit repair affiliates ($80-200/sale) |
| First-Time Borrower's Guide | 5 | Young adults, immigrants | Personal loan + credit builder affiliates |
| Small Business Funding Guide | 6 | Entrepreneurs | Business loan quiz → BrokerOS |
| Debt Freedom Roadmap | 6 | People in debt | Debt relief affiliates ($500-2K/enrollment) |
| Credit Building from Zero | 5 | Credit invisible (immigrants, young adults) | Secured cards + credit builder affiliates |

**Build the first course from existing content.** You already have 85 wellness guides and 26 answer pages. Many of these can be organized into a course structure with minimal new writing. The course is a CURATION of existing content with added structure, progress tracking, and quiz integration.

---

## ELON MUSK — Quizzes as the Product Layer

### On Quizzes

Dorsey's right about the placement, but let me add the engineering perspective.

**The quiz isn't a feature. It's the product.**

Everything else on CreditDoc — the 15,529 profiles, the CFPB data, the city guides, the wellness content — is infrastructure that FEEDS the quiz. The quiz is where intent converts to action.

**Technical architecture for the quiz framework:**

The quiz should be a single reusable component that accepts configuration:
```
Quiz Config:
- pillar: "credit-repair"
- questions: [array of 5 questions with branching logic]
- recommendations_source: "database query by pillar + location + score range"
- email_capture: after Q3
- result_page: personalized lender recommendations + CFPB trust data
- cta: pillar-specific ("/best/credit-repair-companies/" or "/qualify/credit-repair/")
```

One component, 10 configurations. Not 10 separate quiz pages. The template already exists — extend it to accept config, don't duplicate it.

**Pre-fill from context:** If someone arrives from a city guide, pre-fill the location. If they arrive from a credit repair article, pre-fill the intent. If they arrive from a lender review page, pre-fill the category. Reduce friction at every step.

**Data collection even without monetization:** Every quiz completion teaches you about your audience. What credit score ranges are visiting? What do they need most? What cities are they in? This data is gold for:
- Prioritizing which city guides to build next (build for where your quiz takers are)
- Prioritizing which lender profiles to enrich (enrich what people are asking about)
- Proving demand to future partners ("65% of our quiz takers need credit repair in the 500-600 score range")

**Wire the quiz to your database from day one.** Even if no affiliate or origination is connected, log every completion to Supabase. Schema: `quiz_completions(id, pillar, answers_jsonb, location, email, created_at, source_page)`. This is your first-party intent dataset.

### On Courses

I'll add one thing to what Dorsey said: **courses are AI-proof in a way that articles aren't.**

Google AI Overviews will answer "how to dispute a credit report error." They won't replicate a 7-module structured course with embedded quizzes, progress tracking, CFPB data lookups, and personalized lender recommendations at the end.

**The course is the moat within the moat.** Your data moat is the 9.8M complaints. Your content moat is the 30K pages. Your experience moat is the course — because it's the one thing that requires a VISIT to CreditDoc, not just a citation from an LLM.

Build courses. Make them genuinely excellent. Make them the reason someone bookmarks CreditDoc and comes back.

---

## CHAMATH PALIHAPITIYA — The Growth Angle on Quizzes & Courses

### Quizzes as Growth Hacks

Let me tell you why quizzes are one of the most underrated growth tools in 2026.

**Quizzes are inherently shareable.** "I just found out I qualify for a 4.9% personal loan — check yours at creditdoc.co" That's organic social distribution. Every quiz completion is a potential share. Every share is a potential new visitor.

**Make quiz results shareable:**
- Generate a unique results URL for each completion
- "Your CreditDoc Financial Profile: Score Range 580-620 | Best Options: 3 lenders in Houston | Resolution Rate: 87% average"
- Share button: X, LinkedIn, Facebook, WhatsApp
- The shared link brings new visitors to the quiz — viral loop

**Quizzes have the highest completion rates of any interactive content:**
- Blog post: 30-40% read to end
- Calculator: 50-60% complete
- Quiz: 60-80% complete all questions

Why? Because quizzes activate curiosity. "What do I qualify for?" is a question people NEED answered. They'll give you their email to get the answer.

**BuzzFeed built a $1.7B company significantly on quiz engagement.** Your quizzes are higher value because they're not "Which Friends character are you?" — they're "Which lenders will actually approve you?" That's real utility.

### On Courses — The Certification Play

Here's what nobody's mentioned: **certification.**

What if completing "CreditDoc Credit Repair 101" gave you a certificate? Not a legally binding credential — a completion badge that says "I completed CreditDoc's 7-module credit repair course."

**Why this matters:**

1. **For consumers:** A sense of accomplishment. Something to share on LinkedIn or social media. "I just completed CreditDoc's Credit Repair 101 course" → drives awareness.

2. **For CreditDoc's brand:** You become associated with financial education, not just financial information. That's a trust-level upgrade.

3. **For SEO:** Course pages with completion tracking have insanely high engagement metrics. Dwell time, return visits, page depth — all signals Google loves.

4. **For email:** The course IS the drip sequence. Module 1 today, Module 2 in 3 days, Module 3 in 3 days. 7 modules = 21-day email nurture that's actually WANTED by the recipient. Open rates for course emails: 40-60% vs 20% for marketing emails.

5. **For conversion:** Someone who completed your 7-module course and is now at Module 7 ("Your 90-Day Action Plan") is the most qualified lead you'll ever have. They understand their situation, they trust your recommendations, and they're ready to act. That's when you show them the quiz → personalized lender recommendations → affiliate/origination.

### Priority Order

I'd slot quizzes and courses into the execution plan like this:

**Week 1-2:** Credit repair quiz wired to homepage + city guides + wellness content. One quiz, one pillar. Capture completions to Supabase.

**Week 3-4:** Build "Credit Repair 101" course from existing wellness content. 7 modules. Email capture at module 1. Drip delivery.

**Week 5-6:** Measure quiz completion rate + course enrollment + email capture. If working, build personal loans quiz (pillar 2) and "First-Time Borrower's Guide" course.

**Week 7-8:** Make quiz results shareable (unique URL + share buttons). This is when the viral loop activates.

---

## NAVAL RAVIKANT — Education as Productized Knowledge

*"The best businesses productize the founder's knowledge so it runs while they sleep."*

### Quizzes = Productized Advice

Right now, if someone with a 550 credit score in Houston asks "what should I do?" — they'd need a 30-minute conversation with a financial advisor. The quiz answers that question in 60 seconds using your database. That's productized advice. That's leverage.

**The quiz + CFPB data combination is uniquely powerful:**

Traditional quiz: "Based on your answers, we recommend these lenders."
CreditDoc quiz: "Based on your answers AND federal consumer complaint data, here are the 3 lenders in Houston with the highest complaint resolution rates that serve your credit range."

Nobody else can do that second version. The quiz isn't generic recommendations — it's recommendations backed by 9.8M federal records. That's the trust differential.

### Courses = Productized Education

The founder can't personally teach 100 million people about credit. But a course CAN. And once built, it runs forever with zero marginal cost.

**The wealth creation insight:** Every course you build is an asset. An article depreciates (gets outdated, gets outranked). A well-structured course appreciates (gets shared, gets linked to, builds your email list, compounds trust).

### The "Learn → Assess → Act" Framework

This is how the quiz and course work together:

```
LEARN: Course modules (free, builds trust, captures email)
    ↓
ASSESS: Quiz (evaluates their specific situation)
    ↓
ACT: Personalized recommendations (from your database + CFPB data)
    ↓
CONVERT: Apply (affiliate link → future embedded origination)
```

Every page on CreditDoc should push toward this funnel:
- Wellness guides → "Want the full course? Start here"
- Answer pages → "Take our quiz to see your options"
- City guides → "Find your best options in [city]" → quiz
- Course completion → quiz → personalized recs → action

**The content you're already creating (wellness guides, answers) becomes MODULE CONTENT for courses.** You're not creating new content. You're organizing existing content into a higher-value structure.

---

## STEVE JOBS — One Thing Done Perfectly

I'll keep this short because everyone else is overcomplicating it.

**On the quiz:** Build ONE. The credit repair quiz. Make it beautiful. Make it fast. Make it work on mobile. Put it everywhere — homepage, city guides, wellness content, answer pages. Don't build 10 quizzes. Build one that's perfect.

**On courses:** Build ONE. "Credit Repair 101." 7 modules. Use your existing wellness guides as the raw material — reorganize, don't rewrite. Make it the best free credit repair course on the internet. Not hard — the competition is terrible. Most "free credit repair courses" are thinly disguised affiliate funnels. Yours uses federal data. That's the differentiator.

**On linking the quiz into the site:** The quiz is a COMPONENT, not a PAGE. It should appear as:
- Full-page experience on homepage and `/qualify/` URLs
- Embedded card in sidebar of content pages ("Check your options →")
- End-of-article CTA after every relevant piece of content
- Pop-up after 60 seconds on high-intent pages (lender reviews, money pages)

**One quiz. One course. Everywhere on the site. Done.**

---

## COUNCIL CONSENSUS — Session 5

### Quiz Integration Plan

**Build the credit repair quiz first.** Wire it to:
- Homepage hero (primary CTA)
- Every credit repair city guide
- Every credit repair wellness guide (end-of-article CTA)
- Every credit repair answer page
- Sidebar on credit repair lender review pages
- Standalone at `/qualify/credit-repair/`

**Log completions to Supabase** (`quiz_completions` table) from day one — even before any affiliate is wired. This data proves demand to future partners.

**Make results shareable** (unique URL + social share buttons) — turns every completion into a potential viral loop.

**Pre-fill from context** — if visitor arrives from Denver city guide, pre-fill location. Reduce friction.

**Then replicate:** personal loans quiz (pillar 2), then business loans (pillar 1 → BrokerOS).

### Course Strategy

**Build "Credit Repair 101" from existing content:**

| Module | Content Source | New Writing Needed |
|---|---|---|
| 1. Understanding Your Credit Report | Existing wellness guides | Minimal — reorganize |
| 2. Your Rights Under Federal Law | Existing regulatory data + state pages | Some — synthesize |
| 3. How to Dispute Errors | Existing answer pages | Minimal — reorganize |
| 4. Choosing a Credit Repair Company | CFPB data + /best/ page | New — use database |
| 5. Building Credit After Repair | Existing wellness guides | Minimal |
| 6. Avoiding Predatory Lenders | CFPB enforcement data | New — use database |
| 7. Your 90-Day Action Plan | Quiz results | New — dynamic |

**Delivery:** Email drip (module every 3 days = 21-day sequence). Captures email at Module 1. Course emails get 40-60% open rates vs 20% for marketing.

**Completion certificate:** Shareable badge for social media. Drives awareness.

### Updated Priority Stack (Sessions 4+5 Combined)

| Priority | Action | Impact | Effort |
|---|---|---|---|
| #1 | Accelerate city guides to 10-15/day | Highest traffic lever | Medium (increase cron) |
| #2 | Internal linking sprint | Accelerates indexing | Low |
| #3 | Credit repair quiz → homepage + content | Conversion infrastructure | Medium |
| #4 | Indexing pipeline priority reorder | More pages ranked | Low |
| #5 | "Credit Repair 101" course (from existing content) | Email capture + trust + SEO | Medium |
| #6 | Original research piece (positive CFPB) | Backlinks + domain authority | Medium |
| #7 | llms.txt + structured data | AI citation channel | Low |
| #8 | Light social media (2-3/week) | Non-SEO traffic + brand | Low |
| #9 | Shareable quiz results | Viral loop potential | Low |
| #10 | Apply to accessible affiliate programs | Revenue infrastructure | Low |

---

*Council Session 5 recorded May 13, 2026. Focused on quiz integration, educational content strategy, and course development.*
