# Website Audit & Proposed Rewrites

**Date:** 2026-04-29
**Author:** Maven, Campaign Director
**Status:** DELIVERABLE — ready for content team execution
**Scope:** All files in `src/components/` and `src/pages/` audited for (1) LLM-tell language that erodes credibility and (2) framing that contradicts the approved strategic reframe (community-first, outcome-open) or fails to reflect new context (MFM relationship status, seller intel, coalition progress).

---

## Executive Summary

### Counts

| Severity | Count |
|----------|-------|
| **Must-fix** | 14 |
| **Should-fix** | 16 |
| **Nice-to-have** | 8 |
| **Total issues** | 38 |

### Top 5 Issues

1. **`/today` page is frozen in April 12 — entire page uses "SAVE THIS LOT" and predetermined outcome framing.** This page is the single biggest credibility risk on the site. Anyone who finds it sees a campaign that contradicts its own stated strategy. (Must-fix)

2. **`/flyer` uses "SAVE THIS LOT!" headline and predetermined build-out language** — and this is a *print artifact* that may already be in circulation. New flyers must use community-decides framing. (Must-fix)

3. **Building.astro presents a specific build-out plan ("Year-Round Market Pavilion," "Mass Timber Community Hub") as decided** — the approved strategy says the community decides. This is the most visible contradiction on the homepage. (Must-fix)

4. **Situation.astro uses a fabricated MFM quote** — "We're grateful for the past 19 years..." attributed to "Montavilla Farmers Market." We have no permission to quote MFM. Lisa has not spoken to us. This could destroy the relationship before it starts. (Must-fix)

5. **UrgencyBar.astro uses crisis framing ("Act before a developer closes")** that contradicts our community-first posture and Lisa's public statement that nobody has asked them to move. (Must-fix)

### Top 5 Quick Wins (Biggest credibility gain per line changed)

1. **Delete the fabricated MFM quote in Situation.astro** — remove lines 24-27 entirely. Zero risk, immediate credibility improvement. (1 minute)

2. **Rewrite UrgencyBar.astro** — one line of text, massive framing improvement. (1 minute)

3. **Change Building.astro headline and lead paragraph** — swap predetermined language for outcome-open language. (5 minutes)

4. **Update `index.astro` meta description** — currently says "permanently protect the Montavilla Farmers Market," should say "give Montavilla a voice in the future of 7700 SE Stark." (1 minute)

5. **Add MFM independence disclaimer to About.astro** — the existing disclaimer is weak. Strengthen it per the MFM outreach plan. (2 minutes)

---

## File-by-File Audit

---

### `src/components/UrgencyBar.astro`

**1.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Line 4
- **Current text:** `"URGENT: 7700 SE Stark is listed for sale at $4,999,000. Act before a developer closes."`
- **Proposed replacement:** `"7700 SE Stark is listed at $4,999,000. The neighborhood deserves a voice in what happens next."`
- **Reason:** Crisis framing ("Act before a developer closes") contradicts the community-first reframe and Lisa's public position that nobody has been asked to move.

---

### `src/components/Hero.astro`

**2.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Line 8
- **Current text:** `"WHAT IS A CLT?"`
- **Proposed replacement:** `"OUR NEIGHBORHOOD,<br><em>OUR DECISION</em>"`
- **Reason:** The hero headline should lead with the mission, not an educational question. "What is a CLT?" belongs in the body or on `/what-is-a-clt`. The homepage should announce *why we're here*.

**3.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Lines 21-25 (the `.mclt-pitch` paragraph)
- **Current text:** `"Montavilla CLT would be one of the only CLTs in the country positioned at the intersection of commercial and agricultural -- protecting the farmers market lot, its vendors, and the community it feeds. That's the gold dot."`
- **Proposed replacement:** `"Montavilla CLT would give this neighborhood democratic control over 0.84 acres at the heart of the community. What happens on that land is up to the people who live here. That's the gold dot."`
- **Reason:** "Protecting the farmers market lot, its vendors" is predetermined-outcome language. The community decides.

**4.**
- **Severity:** Nice-to-have
- **Category:** LLM-tell
- **Location:** Line 11 (CLT definition paragraph)
- **Current text:** `"A Community Land Trust is a nonprofit that permanently removes land from the speculative market -- holding it in trust for the community, forever. Buildings on the land can be bought, sold, or leased. The land beneath them cannot be flipped."`
- **Proposed replacement:** `"A Community Land Trust is a nonprofit that takes land off the speculative market for good. The community owns the ground. Buildings on it can be bought, sold, or leased -- but the land itself can't be flipped."`
- **Reason:** The em-dash + "holding it in trust for the community, forever" is a classic LLM construction -- the trailing dramatic "forever" and the em-dash-parenthetical both read as machine-generated. The rewrite says the same thing in a more natural voice.

**5.**
- **Severity:** Nice-to-have
- **Category:** LLM-tell
- **Location:** Lines 15-19 (tricolon pattern)
- **Current text:** `"Most CLTs focus on affordable housing. A few protect farmland. A small handful anchor commercial corridors -- markets, small businesses, community institutions."`
- **Proposed replacement:** `"Most CLTs focus on affordable housing. Some protect farmland. A growing number anchor commercial corridors like markets and small business districts."`
- **Reason:** The tricolon structure (most / a few / a small handful) with escalating specificity is a recognizable LLM pattern. The content is fine; the rhythm needs roughing up.

---

### `src/components/Situation.astro`

**6.**
- **Severity:** Must-fix
- **Category:** Factual
- **Location:** Lines 24-27 (the callout/quote)
- **Current text:** `"We're grateful for the past 19 years in our location, and want to plan carefully for what comes next." -- Montavilla Farmers Market`
- **Proposed replacement:** Remove entirely. Do not replace with another quote.
- **Reason:** We do not have permission to quote MFM. Lisa has not spoken to us. We have not met her. Publishing a quote attributed to MFM that we did not obtain from MFM is fabrication and will permanently damage the relationship. This is the single most dangerous line on the website.

**7.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 13-16 (second paragraph)
- **Current text:** `"The property is now listed at $4,999,000. The market can continue operating until ownership transfers -- but the zoning allows up to four stories of commercial and residential development. If a developer closes, the market may be displaced permanently, along with Portland Guitar Repair, the lot's only remaining tenant."`
- **Proposed replacement:** `"The property is now listed at $4,999,000. The market continues to operate, and nobody has been asked to move. But the zoning allows up to four stories of development, and the listing is active. The question is whether the neighborhood wants a voice in what happens next."`
- **Reason:** "May be displaced permanently" is crisis framing. The rewrite states facts without alarmism and pivots to the community-decides frame. Also removes the guitar shop reference -- we don't yet have their permission to be named in our campaign materials.

**8.**
- **Severity:** Should-fix
- **Category:** LLM-tell
- **Location:** Lines 17-20 (third paragraph)
- **Current text:** `"There is no timeline guarantee. A sale could happen at any time. But there is also an opportunity -- one that communities in cities across the country have seized to protect beloved spaces through Community Land Trusts."`
- **Proposed replacement:** `"There's no timeline guarantee. But the lot has been listed for months and no sale is pending. That gives us time to organize -- and 308 CLTs in 48 states show the model works."`
- **Reason:** "An opportunity -- one that communities in cities across the country have seized to protect beloved spaces" is textbook LLM rhetoric: the em-dash reveal, the abstract-noun intensifier ("beloved spaces"), the grandiose framing. The rewrite grounds it in facts (listing duration, no pending sale, 308 CLTs).

**9.**
- **Severity:** Should-fix
- **Category:** New-context-missing
- **Location:** After the situation paragraphs
- **Current text:** (no mention of coalition progress)
- **Proposed replacement:** Add a brief progress note: `"As of April 2026, the coalition has gathered 40+ petition signatures, 20 founding members, and begun outreach to Proud Ground, the Northwest CLT Coalition, and neighborhood institutions."`
- **Reason:** The site reads like day-one with no traction. We have traction. Show it.

---

### `src/components/Building.astro`

**10.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Line 6 (headline)
- **Current text:** `"Not Just Saved.<br>Built to Last Generations."`
- **Proposed replacement:** `"What Could This Land Become?"`
- **Reason:** "Not Just Saved" uses the old "save" frame. "Built to Last Generations" presupposes a specific build-out. The reframe says: the community decides.

**11.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 7-10 (lead paragraph)
- **Current text:** `"A Community Land Trust permanently removes land from the speculative market. The community owns the ground. Development serves people -- not profit. Here's what we're building at 7700 SE Stark."`
- **Proposed replacement:** `"A Community Land Trust takes land off the speculative market. The community owns the ground. What gets built on it is up to the people who live here. Here are some of the possibilities the coalition is exploring."`
- **Reason:** "Here's what we're building" presents a predetermined plan. The reframe presents possibilities.

**12.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 12-33 (the four vision cards)
- **Current text:** Cards present CLT, Year-Round Market Pavilion, Mass Timber Community Hub, and Protected Green Space as *the* plan.
- **Proposed replacement:** Reframe cards as "possibilities the community could pursue." Add a 5th card: "Affordable Housing" or "Mixed-Use Development." Change card intros from declarative ("The land held in perpetuity") to exploratory ("The land could be held in perpetuity"). Add a note: "These are starting points, not final plans. The coalition will host listening sessions to hear what the neighborhood wants."
- **Reason:** The strategic reframe explicitly says we present multiple scenarios, not a predetermined plan.

**13.**
- **Severity:** Should-fix
- **Category:** LLM-tell
- **Location:** Line 29 (Green Space card)
- **Current text:** `"Thoughtful landscape design ensures the lot remains open, welcoming, and ecologically active -- green space for Montavilla permanently woven into the neighborhood."`
- **Proposed replacement:** `"Green space for Montavilla -- open, welcoming, and part of the neighborhood long-term."`
- **Reason:** "Ecologically active" and "permanently woven into the neighborhood" are vague intensifiers. "Thoughtful landscape design ensures" is classic LLM hedging.

**14.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Lines 34-37 (prospectus link)
- **Current text:** Links to the existing prospectus, which presents a predetermined plan.
- **Proposed replacement:** Either remove the link until the prospectus is revised, or add a note: "This prospectus describes one possible scenario. The coalition is exploring multiple options."
- **Reason:** The prospectus contradicts the community-decides framing.

---

### `src/components/Roadmap.astro`

**15.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Line 7 (headline)
- **Current text:** `"A Clear Path From<br>Here to Forever."`
- **Proposed replacement:** `"A Clear Path From<br>Here to Community Ownership."`
- **Reason:** "Forever" is LLM-dramatic. "Community Ownership" is what we're actually building toward.

**16.**
- **Severity:** Should-fix
- **Category:** LLM-tell
- **Location:** Line 14 (Step 01 description)
- **Current text:** `"Neighbors, vendors, and local businesses align around a shared vision. We're forming a steering committee, holding community meetings, and building the petition that demonstrates to funders and the city that Montavilla is organized and serious."`
- **Proposed replacement:** `"Neighbors, vendors, and local businesses come together to figure out what they want for this land. We're forming a steering committee, running community listening sessions, and gathering the petition signatures that show funders and the city this neighborhood is organized."`
- **Reason:** "Align around a shared vision" is abstract-noun-heavy LLM language. "Come together to figure out what they want" is more human. Also adds "listening sessions" per the reframe.

**17.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Lines 51-57 (Step 05 - Acquisition)
- **Current text:** `"...we break ground on the pavilion, mass timber hub, and landscape design that will define this space for a generation."`
- **Proposed replacement:** `"...we begin building whatever the community has determined is the right use for this land."`
- **Reason:** Predetermined build-out language.

---

### `src/components/Action.astro`

**18.**
- **Severity:** Should-fix
- **Category:** LLM-tell
- **Location:** Lines 8-9 (lead paragraph)
- **Current text:** `"You don't need to be a developer or a lawyer. You just need to show up. This is how communities win."`
- **Proposed replacement:** `"You don't need to be a developer or a lawyer. You just need to show up."`
- **Reason:** "This is how communities win" is a motivational-poster closer that reads as AI-generated. The first two sentences land fine on their own.

**19.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Line 14 (Donate card)
- **Current text:** `"Seed our acquisition fund. Every dollar signals to funders that this community is organized and serious about ownership."`
- **Proposed replacement:** `"Every dollar signals to funders that this community is organized. Pledges are non-binding and collected only when we're ready to act."`
- **Reason:** "Seed our acquisition fund" presupposes acquisition. We're in coalition-building mode.

**20.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Line 20 (Petition card)
- **Current text:** `"Hundreds of signatures show the city, the sellers, and our grant partners that Montavilla stands united behind this vision."`
- **Proposed replacement:** `"Every signature shows the city and our grant partners that Montavilla wants a voice in what happens at 7700 SE Stark."`
- **Reason:** "Stands united behind this vision" presupposes a predetermined outcome. Also "hundreds" is aspirational inflation -- we have ~40.

---

### `src/components/Petition.astro`

**21.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Line 7 (headline)
- **Current text:** `"Add Your Name.<br>Build the Movement."`
- **Proposed replacement:** `"Add Your Name.<br>Join the Coalition."`
- **Reason:** "Build the Movement" is vague and grandiose. "Join the Coalition" is concrete and matches the strategic reframe language.

**22.**
- **Severity:** Nice-to-have
- **Category:** LLM-tell
- **Location:** Line 9 (lead paragraph)
- **Current text:** `"Sign our community petition and join the MCLT founding member list. We'll keep you updated on meetings, milestones, and ways to plug in as we move fast."`
- **Proposed replacement:** `"Sign the community petition and join the MCLT founding member list. We'll keep you updated on meetings, milestones, and ways to get involved."`
- **Reason:** "Ways to plug in as we move fast" tries too hard. "Ways to get involved" is simpler.

---

### `src/components/About.astro`

**23.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 8-11
- **Current text:** `"The Montavilla Community Land Trust is a neighbor-led coalition organizing to permanently protect the land at 7700 SE Stark Street through community ownership. We are residents, market vendors, and local business people who believe that Montavilla's most important gathering place should belong to the people who built it."`
- **Proposed replacement:** `"The Montavilla Community Land Trust is a neighbor-led coalition working to give Montavilla a voice in the future of 7700 SE Stark Street. We are residents and local business people who believe this neighborhood should have a say in what happens to the land at its center."`
- **Reason:** "Permanently protect" and "most important gathering place should belong to the people who built it" are predetermined-outcome and savior framing. Also removes "market vendors" -- we have no vendor members yet and claiming them could anger MFM leadership.

**24.**
- **Severity:** Must-fix
- **Category:** New-context-missing
- **Location:** Lines 22-25 (existing disclaimer)
- **Current text:** `"This coalition operates independently from the Montavilla Farmers Market organization."`
- **Proposed replacement:** `"The Montavilla Community Land Trust is an independent organization. We are not affiliated with, endorsed by, or speaking on behalf of the Montavilla Farmers Market."`
- **Reason:** The current disclaimer is minimal. The MFM outreach plan requires a clear, explicit independence statement.

---

### `src/components/SignatureCount.astro`

**25.**
- **Severity:** Nice-to-have
- **Category:** Other
- **Location:** Line 15
- **Current text:** `"Montavilla neighbors like this idea"`
- **Proposed replacement:** `"Montavilla neighbors have joined the coalition"`
- **Reason:** "Like this idea" is casual and vague. "Joined the coalition" is concrete and matches the reframe.

---

### `src/components/Nav.astro`

**26.**
- **Severity:** Nice-to-have
- **Category:** Other
- **Location:** Line 10
- **Current text:** `"Our Vision"` (links to #building)
- **Proposed replacement:** `"Possibilities"` or `"What Could Be"`
- **Reason:** "Our Vision" implies a decided plan. "Possibilities" matches the outcome-open reframe.

---

### `src/components/Footer.astro`

No issues found. Clean and factual.

---

### `src/components/CommunityPost.astro` / `NewPostForm.astro`

No content issues. These are functional components (post display and form).

---

### `src/pages/index.astro`

**27.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Line 28 (meta description)
- **Current text:** `"We're building a Community Land Trust to permanently protect the Montavilla Farmers Market and 7700 SE Stark Street for our neighborhood -- forever."`
- **Proposed replacement:** `"A neighbor-led coalition exploring community ownership of 7700 SE Stark Street. The neighborhood decides what happens here."`
- **Reason:** The meta description is what Google shows. It currently uses the old predetermined framing. This is the single most visible SEO artifact.

---

### `src/pages/today.astro`

This entire page is the biggest single problem on the site. It is frozen in the April 12 market-day framing and contradicts the approved strategy in almost every section.

**28.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Line 11 (page title)
- **Current text:** `"Save This Lot -- Montavilla Community Land Trust"`
- **Proposed replacement:** `"Our Neighborhood, Our Decision -- Montavilla Community Land Trust"`
- **Reason:** "Save This Lot" is the explicitly deprecated headline.

**29.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 62-63 (CSS background text) and Line 305 (hero headline)
- **Current text:** `"SAVE THIS LOT"` as both a CSS pseudo-element and the h1
- **Proposed replacement:** Remove the CSS pseudo-element entirely. Change h1 to `"OUR<br><em>NEIGHBORHOOD,</em><br>OUR DECISION."` or similar.
- **Reason:** "Save This Lot" was deprecated on Apr 13.

**30.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 307-310 (hero subtitle)
- **Current text:** `"The land beneath the Montavilla Farmers Market is for sale. We're buying it -- and protecting it forever. Here's how you help."`
- **Proposed replacement:** `"The land at 7700 SE Stark is listed for sale. A coalition of neighbors is organizing to make sure Montavilla has a voice in what happens next."`
- **Reason:** "We're buying it -- and protecting it forever" is the old predetermined framing.

**31.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 317-329 (situation section on /today)
- **Current text:** `"The plan: a year-round market pavilion, a mass timber community hub with commissary kitchen and cold storage, and protected green space -- owned by this community, forever."`
- **Proposed replacement:** `"The goal: give this neighborhood a real voice in what happens to the land. Whether that means community green space, affordable housing, market infrastructure, or something else entirely -- the coalition decides."`
- **Reason:** Predetermined build-out language.

**32.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Line 304 (date stamp)
- **Current text:** `"Sunday, April 12, 2026 . Montavilla Farmers Market Day"`
- **Proposed replacement:** Either remove the date or update to reflect current status.
- **Reason:** The page is frozen in time. A visitor arriving today sees a page from 17 days ago that looks abandoned.

**33.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Lines 299 (urgency bar on /today)
- **Current text:** `"7700 SE Stark is listed for sale at $4,999,000. A developer could close at any time."`
- **Proposed replacement:** Same as UrgencyBar.astro rewrite (issue #1).
- **Reason:** Duplicate crisis framing.

---

### `src/pages/flyer.astro`

**34.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 146, 202 (flyer headline, duplicated)
- **Current text:** `"SAVE<br>THIS<br>LOT!"`
- **Proposed replacement:** `"OUR<br>NEIGHBORHOOD<br>OUR DECISION"`
- **Reason:** Same "Save This Lot" deprecation. This is a *print artifact* -- if people are still printing these, they're distributing contradicted messaging.

**35.**
- **Severity:** Must-fix
- **Category:** Outdated-framing
- **Location:** Lines 155-159, 211-215 (flyer body, duplicated)
- **Current text:** `"A group of neighbors is organizing the Montavilla Community Land Trust to purchase this land and protect it permanently. The plan: a year-round market pavilion, a mass timber community hub with commissary kitchen and cold storage, and protected green space -- owned by this community, in perpetuity."`
- **Proposed replacement:** `"A coalition of Montavilla neighbors is organizing to make sure the community has a voice in the future of this land. We're building a coalition, not making promises -- the neighborhood decides what happens here."`
- **Reason:** Predetermined build-out language.

---

### `src/pages/calculator.astro`

**36.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Line 9 (GOAL constant)
- **Current text:** `const GOAL = 4_999_000;`
- **Proposed replacement:** Either remove the goal bar entirely or change the framing to "community pledges" without implying acquisition at list price. The $5M goal bar showing 0.02% is demoralizing and implies we're trying to crowdfund $5M, which is not the plan.
- **Reason:** The strategic reframe moved away from "raise $5M." The pledge calculator should show community momentum, not a hopeless thermometer.

---

### `src/pages/what-is-a-clt.astro`

**37.**
- **Severity:** Should-fix
- **Category:** Outdated-framing
- **Location:** Lines 672-679 (CTA section)
- **Current text:** `"THIS IS HOW WE KEEP IT. The Montavilla Farmers Market has been here for 19 years. A CLT is how it stays for the next 100."`
- **Proposed replacement:** `"THIS IS HOW NEIGHBORHOODS DECIDE. 7700 SE Stark has been a community gathering place for 19 years. A CLT is how the neighborhood keeps a voice in what happens next."`
- **Reason:** "How we keep it" presupposes a specific outcome (keeping the market). The reframe is about community voice.

**38.**
- **Severity:** Nice-to-have
- **Category:** LLM-tell
- **Location:** Line 519 (CLT model description)
- **Current text:** `"That's the model MCLT aspires to over time."`
- **Proposed replacement:** `"That's the kind of hybrid model MCLT could grow into."`
- **Reason:** "Aspires to" is slightly grandiose for a coalition with $1,175 in pledges.

---

### `src/pages/research.astro`

No critical issues. This is a research document, not campaign copy. The factual claims are well-sourced and the tone is appropriate for an analytical piece.

---

### `src/pages/larping-for-land.astro`

**39 (informational -- no rewrite needed).**
- **Severity:** Nice-to-have
- **Category:** New-context-missing
- **Location:** Throughout
- **Current text:** References "permanently protect the land at 7700 SE Stark" and the specific build-out plan.
- **Proposed replacement:** If this page is still active/linked, align the framing with the community-decides reframe. But this is a creative/event page with a different audience, so lower priority.
- **Reason:** The LARP page has its own tone and audience. Update if there's bandwidth; deprioritize otherwise.

---

### `src/pages/clt-map.astro`

No issues. Data visualization page. Factual and well-executed.

---

### `src/pages/clt-inventory.astro`

No issues. Directory/data page. Clean.

---

### `src/pages/petition-packet.astro`

**40.**
- **Severity:** Nice-to-have
- **Category:** Outdated-framing
- **Location:** Lines 382-383 (cover headline)
- **Current text:** `"TRAGEDY OF THE COMMONS."` (with "TRAGEDY" struck through)
- **Proposed replacement:** This is clever enough to keep, but consider whether the visual gag lands with people who don't already understand the concept. Not urgent.
- **Reason:** Style note, not a framing problem.

---

### `src/pages/community/index.astro`

No content issues. Functional page (database-driven community board).

---

## Recommended Sequencing: First 5 Changes

These five changes produce the biggest credibility improvement for the smallest amount of work. Do them before anything else.

| Priority | File | Change | Time Est. |
|----------|------|--------|-----------|
| **1** | `Situation.astro` | Delete the fabricated MFM quote (lines 24-27). No replacement. | 1 min |
| **2** | `UrgencyBar.astro` | Rewrite one line: remove "Act before a developer closes," replace with community-voice framing. | 1 min |
| **3** | `index.astro` | Update the meta description to community-decides language. | 1 min |
| **4** | `About.astro` | Strengthen the MFM independence disclaimer to the explicit version from the outreach plan. | 2 min |
| **5** | `Building.astro` | Change headline to "What Could This Land Become?" and lead paragraph to outcome-open framing. Add a note that these are possibilities, not a decided plan. | 5 min |

After these five, the next batch should be:
- Rewrite `/today` page or take it offline (it is a time-capsule contradiction)
- Rewrite `/flyer` with new headline and body
- Update Roadmap step 5 language
- Update Action card copy
- Update Petition headline

---

*This audit does not cover the prospectus PDF, the color flyer PDF, social media (none exists), or email templates. Those are separate deliverables.*

*CRITICAL REMINDER: Do not name the trust representative or reference seller intel in any public-facing copy. Do not claim MFM endorsement or imply MFM is part of MCLT. All proposed rewrites in this document comply with these constraints.*

-- Maven
Campaign Director, Montavilla Community Land Trust
2026-04-29
