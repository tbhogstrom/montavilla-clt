# Decision Log: Project Initialization

**Date:** 2026-04-13
**Participants:** Maven (Campaign Director), Statton (Founder)

---

## Context

The Montavilla CLT campaign website launched prior to the Montavilla Farmers Market event on April 12, 2026. The website includes petition signing, pledge collection, a public calculator/ledger, print flyer generator, and a published prospectus PDF. All digital infrastructure is deployed on Vercel with Neon PostgreSQL backend and Resend email service.

The property at 7700 SE Stark Street is actively listed at $4,999,000.

## Decisions Made

### 1. Project Board Initialized
- Created structured workspace with milestone-based tracking
- 5 milestones aligned with the website's published roadmap
- Dashboard tracks key campaign infrastructure status

### 2. Campaign Strategy Documented
- Identified 5 critical gaps: legal entity, seller engagement, capital stack, Proud Ground relationship, coalition breadth
- Defined 4 campaign phases with concrete targets
- Established "Days on Market" as the key leading indicator

### 3. Workspace Structure Established
```
workspace/
├── project-board.md          # Master tracking
├── decisions/                # Decision logs
├── milestones/
│   ├── 01-coalition/
│   ├── 02-legal/
│   ├── 03-fundraising/
│   ├── 04-grants/
│   └── 05-acquisition/
├── meeting-notes/
└── strategy/
    └── campaign-strategy.md
```

## Open Questions for Statton

1. **Market Day results** — How did April 12 go? How many flyers distributed? Any verbal commitments? What's the energy level?
2. **Database numbers** — Can we pull current petition signatures and pledge totals? That's our baseline.
3. **Proud Ground** — Have you spoken with anyone there? Do we have a contact name?
4. **Listing broker** — Do we know who the listing agent is for 7700 SE Stark?
5. **Fiscal sponsorship** — Any existing relationships with fiscal sponsors (Montavilla NA, any other 501(c)(3))?
6. **Budget** — Is there any seed capital for legal fees, filing costs, or campaign operations? Or is everything bootstrapped until we can fundraise?
7. **Steering committee** — Anyone already committed beyond you?

## Next Actions

| Action | Owner | Deadline |
|--------|-------|----------|
| Pull database metrics (signups + pledges) | Statton | Apr 14 |
| Segment signups by "how can you help" | Maven | Apr 14 |
| Draft Letter of Interest for seller | Maven | Apr 16 |
| Contact Proud Ground for intro call | Statton | Apr 16 |
| Research fiscal sponsors in Portland | Maven | Apr 16 |
| Identify listing broker for 7700 SE Stark | Statton | Apr 14 |
