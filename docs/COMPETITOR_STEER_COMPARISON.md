# SteerCorp vs OracleAI: product and routing comparison

**Review date:** 2026-08-24  
**OracleAI branch:** `feat/agent-first-harness`  
**Routing benchmark:** 20 complex RU/EN/mixed queries, Urania and Lilith, top-3 expected-skill inclusion.

## Executive conclusion

OracleAI is not currently ahead of Steer in every Vedic-astrology feature. Steer has a clear advantage in **Vedic-specific product breadth and distribution claims**: Dasha/Vimshottari timelines, Panchang/Muhurta/Rahu Kaal, divisional charts, planetary strengths, alerts, multi-profile mobile usage and a public API-shaped chart example. Those capabilities are publicly advertised, but they were not independently tested in this review.[1] [2] [3] [4]

OracleAI is ahead in a different layer: **multi-specialist scope, evidence-first agent governance, explicit skill-first extensibility, safety boundaries, proof metadata, bilingual RU/EN routing, expanded Western natal points, Rahu/Ketu canonical output and full localized PDF reporting**. The routing benchmark reached 20/20 expected-skill inclusion after targeted fixes. This makes OracleAI stronger as a transparent, auditable specialist harness, while Steer currently presents the stronger single-domain Vedic astrology product surface.

> The honest product position is not “we beat Steer at everything”. It is: **Steer is the closer Vedic astrology competitor; OracleAI differentiates through four specialist agents, transparent evidence/tool provenance, safety and expandable skills.**

## Feature comparison

| Capability | SteerCorp public claim | OracleAI current evidence | Assessment |
|---|---|---|---|
| Core astrology tradition | Vedic/Jyotish, Kundli, sidereal/Lahiri | Western symbolic astrology, Tropical/Placidus/Apparent Geocentric natal contract | Different traditions; no direct parity claim |
| Natal chart | Full Kundli, planetary positions, houses, Ascendant, nakshatra | Full chart with exact conventions, planets, houses, aspects, angles, Rahu/Ketu and expanded points | OracleAI stronger in explicit contract transparency; Steer stronger in Vedic scope claim |
| Rahu/Ketu | Vedic product naturally implies nodes, but the reviewed public pages did not show a canonical Rahu/Ketu response contract | Explicit `lunar_nodes.rahu/ketu`, True Node mode, opposition checks and PDF/UI labels | OracleAI has stronger auditable public contract |
| Expanded points | Public pages emphasize divisional charts and planetary strengths, not Western Chiron/Juno/Ceres/Vesta/Pallas | Chiron, Juno, Ceres, Vesta, Pallas, Lilith in placements and full PDF reference block | OracleAI stronger for this Western expanded-point use case |
| Dasha/timeline | Vimsottari Dasha and life timeline are prominent public claims | Not evidenced as a parity feature in the audited current contract | Steer ahead; high-priority roadmap gap |
| Panchang/muhurta | Daily Panchang, tithi, nakshatra, yoga, karana, auspicious timing and Rahu Kaal are advertised | Current OracleAI audit did not verify a comparable Vedic Panchang engine | Steer ahead; do not market parity yet |
| Divisional charts | 20+ varga/divisional charts are advertised | Not evidenced as a comparable Vedic varga system | Steer ahead in Vedic depth |
| Transits | Real-time/daily transits and alerts are advertised | Transits and bounded timing reflection are present in Urania skill/eval surface | Near parity at concept level; Steer has stronger stated alert productization |
| Compatibility | Compatibility for partner/family/co-founder is advertised; Play listing names Guna Milan/Ashtakoot | Synastry, relationship boundaries and deterministic compatibility tooling are present | Different methods; Steer stronger Vedic matching claim, OracleAI stronger third-party/safety framing |
| Multi-agent scope | Public product is primarily an AI coach/astrologer | Four specialists: Urania astrology, Lilith reflection/Matrix, Lenormand Tarot, Mira palmistry | OracleAI clearly broader |
| Tarot | Public Steer pages reviewed did not establish a Tarot workflow | RWS Tarot draws, spreads, reversals, visual evidence and decision matrix skills | OracleAI ahead on verified scope |
| Palmistry/image analysis | Public Steer pages reviewed did not establish palm-image analysis | Mira photo quality gate, palm scanner/guide/history and confidence-based symbolic reading | OracleAI ahead on verified scope |
| Matrix/reflection | Self-discovery questions are advertised | Matrix tool, diary/memory/practice workflows and anti-Barnum evidence contract | OracleAI more structured and auditable |
| Agent extensibility | Public pages do not expose a file-backed skill authoring model | 122 file-backed skills, per-agent manifests, dependencies, tool requirements and authoring rules | OracleAI clearly ahead in developer extensibility |
| Tool provenance | Public pages state calculation precision, but no user-facing per-response tool trace was verified | User-safe proof envelope exposes mode, actual deterministic tools used and specialist scope | OracleAI ahead in transparency |
| Language | Public pages reviewed are English; multilingual product behavior was not verified | RU/EN content, localized PDF, skill aliases and 20-case mixed-language routing benchmark | OracleAI ahead in verified bilingual behavior |
| PDF/reporting | Public pages reviewed did not establish a full localized natal PDF | Seven-page dense RU/EN PDF with cover, wheel, Rahu/Ketu, points, houses, aspects and disclaimer | OracleAI ahead in verified report deliverable |
| Mobile/distribution | Android listing, ChatGPT app and iOS waitlist are publicly advertised | Telegram Mini App/web shell and local Mini App UI; native store distribution not verified | Steer ahead in distribution footprint |
| Privacy controls | Steer claims export/delete in-app; policy names AI-provider and cloud processing; support FAQ says email deletion may take up to 30 days | OracleAI has consent gates, memory-disabled behavior, bounded traces and safety protocol; public privacy parity requires further product documentation | Different strengths; Steer has more publicly documented account controls, OracleAI has stronger inspected runtime consent boundaries |
| Pricing | Steer advertises free ChatGPT questions and Play subscription premium features | OracleAI product has its own plans/limits; no direct pricing comparison was performed | Cannot declare winner without live commercial test |

## What we can honestly claim as “better”

OracleAI is better for users who want several symbolic modalities in one product, a clear specialist identity, a transparent distinction between calculated facts and interpretation, explicit Rahu/Ketu and expanded Western points, localized RU/EN reports, and visible evidence/tool provenance. The 20/20 routing benchmark also shows that a complex mixed-language request can be routed to the relevant skill in the top three for both Urania and Lilith.

Steer is better positioned for users who specifically want Vedic/Jyotish depth, Vimshottari Dasha, Panchang/Muhurta, varga charts, Rahu Kaal, Ashtakoot/Guna Milan, mobile-store distribution and a product marketed around an always-available astrology companion. These are public claims and should be re-tested in an authenticated product comparison before being converted into a hard competitive statement.

## Priority gaps to close

The largest product gap is not generic AI quality; it is **Vedic astrology parity**. If OracleAI wants to compete head-on with Steer, the next measurable modules should be a separate sidereal/Lahiri calculation profile, nakshatra/pada, Vimshottari Dasha, Panchang, divisional-chart support, Vedic compatibility/Guna Milan and event alerts. These should be separate skills and deterministic tools, not added as prose to the Western Urania profile.

The second gap is distribution and user proof. OracleAI should make the existing proof envelope visible in the deployed Mini App, add a public capabilities page, and add one-click export/delete and multi-profile explanations to the product documentation. Steer has stronger public positioning in these areas even where the technical claims still require independent verification.

## Multilingual routing evidence

The benchmark is stored in `scripts/benchmark_skill_routing.py`, is included in `pytest` and `check_agent_quality.py`, and therefore runs as part of the release gate. It covers 10 Urania and 10 Lilith prompts. It mixes Russian, English and code-switched language, including Rahu/Ketu, synastry, houses, date-only limits, expanded points, lunar journaling, Matrix, emotion naming, boundaries, memory, habit loops, values conflict, diary and conversation rehearsal.

Initial accuracy was **15/20 (75%)**. The failures exposed real lexical gaps rather than random instability: expanded-point vocabulary, date-only phrases such as `no birth time`, lunar journal/week vocabulary, post-conversation emotion naming, and stability-versus-project values conflict. After enriching the affected skills and adding one narrowly scoped date-only marker boost, the benchmark reached **20/20 (100%)** top-3 expected-skill inclusion. It is now a pytest regression and release invariant; it should still be expanded with adversarial paraphrases before any claim of broad production accuracy.

## Limitations of this comparison

This is a public-surface and repository-contract comparison, not a full black-box product benchmark. Steer’s authenticated app, actual chart calculations, response quality, retention, latency, subscription flows and live API were not tested. OracleAI’s live LLM provider was also not enabled during deterministic acceptance. Accordingly, the matrix distinguishes **verified in code/UI**, **publicly claimed by Steer**, and **not independently verified** rather than treating marketing copy as technical proof.

## References

[1]: https://steercorp.io/ "SteerCorp homepage and product claims"
[2]: https://steercorp.io/support.html "Steer support and FAQ"
[3]: https://steercorp.io/privacy.html "Steer privacy policy"
[4]: https://play.google.com/store/apps/details?id=coach.steer.app&hl=en_US "Steer: AI Coach & Astrologer on Google Play"
