# SteerCorp vs OracleAI: product and routing comparison

**Review date:** 2026-08-24  
**OracleAI branch:** `feat/agent-first-harness`  
**Routing benchmark:** 20 complex RU/EN/mixed queries, Urania and Lilith, top-3 expected-skill inclusion.

## Executive conclusion

OracleAI is not currently ahead of Steer in every Vedic-astrology feature. Steer has a clear advantage in **publicly claimed Vedic-specific product breadth and distribution**: Dasha/Vimshottari timelines, Panchang/Muhurta/Rahu Kaal, divisional charts, planetary strengths, alerts, multi-profile mobile usage and a public API-shaped chart example. OracleAI now implements a transparent first subset of these calculations, but Steer’s broader productization claims still require independent black-box verification. Those capabilities are publicly advertised, but they were not independently tested in this review.[1] [2] [3] [4]

OracleAI is ahead in a different layer: **multi-specialist scope, evidence-first agent governance, explicit skill-first extensibility, safety boundaries, proof metadata, bilingual RU/EN routing, expanded Western natal points, Rahu/Ketu canonical output and full localized PDF reporting**. The current harness has 139 file-backed skills and 29 registered tools after the Vedic, Mira and Lenormand expansions. The original Urania/Lilith routing benchmark, the Vedic/adversarial set and the new Mira/Lenormand set all reached full expected-skill inclusion in top-3.
This makes OracleAI stronger as a transparent, auditable specialist harness, while Steer currently presents the stronger single-domain Vedic astrology product surface.

> The honest product position is not “we beat Steer at everything”. It is: **Steer is the closer Vedic astrology competitor; OracleAI differentiates through four specialist agents, transparent evidence/tool provenance, safety and expandable skills.**

## Feature comparison

| Capability | SteerCorp public claim | OracleAI current evidence | Assessment |
|---|---|---|---|
| Core astrology tradition | Vedic/Jyotish, Kundli, sidereal/Lahiri | Western symbolic astrology, Tropical/Placidus/Apparent Geocentric natal contract | Different traditions; no direct parity claim |
| Natal chart | Full Kundli, planetary positions, houses, Ascendant, nakshatra | Full chart with exact conventions, planets, houses, aspects, angles, Rahu/Ketu and expanded points | OracleAI stronger in explicit contract transparency; Steer stronger in Vedic scope claim |
| Rahu/Ketu | Vedic product naturally implies nodes, but the reviewed public pages did not show a canonical Rahu/Ketu response contract | Explicit `lunar_nodes.rahu/ketu`, True Node mode, opposition checks and PDF/UI labels | OracleAI has stronger auditable public contract |
| Expanded points | Public pages emphasize divisional charts and planetary strengths, not Western Chiron/Juno/Ceres/Vesta/Pallas | Chiron, Juno, Ceres, Vesta, Pallas, Lilith in placements and full PDF reference block | OracleAI stronger for this Western expanded-point use case |
| Dasha/timeline | Vimsottari Dasha and life timeline are prominent public claims | Deterministic Vimshottari Mahadasha/Antardasha tool is now wired, with explicit precision limits | OracleAI now has a bounded implementation; independent cross-engine validation and richer interpretation remain |
| Panchang/muhurta | Daily Panchang, tithi, nakshatra, yoga, karana, auspicious timing and Rahu Kaal are advertised | Deterministic Panchang/Rahu Kaal/Muhurta tools are now wired with local coordinates/timezone and limitations | OracleAI has a first transparent subset; boundary-level cross-validation and richer Muhurta rules remain |
| Divisional charts | 20+ varga/divisional charts are advertised | Deterministic D1/D9/D10 subset is now wired with documented sign-division method | OracleAI still trails the advertised 20+ breadth; do not claim parity |
| Transits | Real-time/daily transits and alerts are advertised | Transits and bounded timing reflection are present in Urania skill/eval surface | Near parity at concept level; Steer has stronger stated alert productization |
| Compatibility | Compatibility for partner/family/co-founder is advertised; Play listing names Guna Milan/Ashtakoot | Synastry, relationship boundaries and deterministic compatibility tooling are present | Different methods; Steer stronger Vedic matching claim, OracleAI stronger third-party/safety framing |
| Multi-agent scope | Public product is primarily an AI coach/astrologer | Four specialists: Urania astrology, Lilith reflection/Matrix, Lenormand Tarot, Mira palmistry | OracleAI clearly broader |
| Tarot | Public Steer pages reviewed did not establish a Tarot workflow | RWS Tarot draws, spreads, reversals, visual evidence and decision matrix skills | OracleAI ahead on verified scope |
| Palmistry/image analysis | Public Steer pages reviewed did not establish palm-image analysis | Mira deterministic capture precheck, palm scanner/guide/history, visual evidence map, confidence rows and school/line topology skills | OracleAI ahead on verified scope; true line segmentation still requires a validated CV adapter |
| Matrix/reflection | Self-discovery questions are advertised | Matrix tool, diary/memory/practice workflows and anti-Barnum evidence contract | OracleAI more structured and auditable |
| Agent extensibility | Public pages do not expose a file-backed skill authoring model | 139 file-backed skills, per-agent manifests, dependencies, tool requirements and authoring rules | OracleAI clearly ahead in developer extensibility |
| Tool provenance | Public pages state calculation precision, but no user-facing per-response tool trace was verified | User-safe proof envelope, Mira visual precheck, Tarot ledger with deck/position/orientation/combination/checksum and actual deterministic tool trace | OracleAI ahead in transparency |
| Language | Public pages reviewed are English; multilingual product behavior was not verified | RU/EN content, localized PDF, skill aliases and 20-case mixed-language routing benchmark | OracleAI ahead in verified bilingual behavior |
| PDF/reporting | Public pages reviewed did not establish a full localized natal PDF | Seven-page dense RU/EN PDF with cover, wheel, Rahu/Ketu, points, houses, aspects and disclaimer | OracleAI ahead in verified report deliverable |
| Mobile/distribution | Android listing, ChatGPT app and iOS waitlist are publicly advertised | Telegram Mini App/web shell and local Mini App UI; native store distribution not verified | Steer ahead in distribution footprint |
| Privacy controls | Steer claims export/delete in-app; policy names AI-provider and cloud processing; support FAQ says email deletion may take up to 30 days | OracleAI has consent gates, memory-disabled behavior, bounded traces and safety protocol; public privacy parity requires further product documentation | Different strengths; Steer has more publicly documented account controls, OracleAI has stronger inspected runtime consent boundaries |
| Pricing | Steer advertises free ChatGPT questions and Play subscription premium features | OracleAI product has its own plans/limits; no direct pricing comparison was performed | Cannot declare winner without live commercial test |

## What we can honestly claim as “better”

OracleAI is better for users who want several symbolic modalities in one product, a clear specialist identity, a transparent distinction between calculated facts and interpretation, explicit Rahu/Ketu and expanded Western points, localized RU/EN reports, and visible evidence/tool provenance. The 20/20 routing benchmark also shows that a complex mixed-language request can be routed to the relevant skill in the top three for both Urania and Lilith.

Steer remains better positioned publicly for users who specifically want a broad Vedic/Jyotish product surface, mature-looking Vimshottari/Panchang/varga/Rahu Kaal/Guna Milan positioning, mobile-store distribution and a product marketed around an always-available astrology companion. OracleAI now has first deterministic implementations for the named Vedic subset, but should not claim equivalent breadth or maturity until cross-engine validation and product UX are complete. These are public claims and should be re-tested in an authenticated product comparison before being converted into a hard competitive statement.

## Priority gaps to close

The largest remaining product gap is not generic AI quality; it is **Vedic astrology breadth, formula validation and productization**. OracleAI now has a separate sidereal/Lahiri profile, nakshatra/pada, Vimshottari Dasha, Panchang/Rahu Kaal/Muhurta, D1/D9/D10, Guna Milan, sidereal transits and bounded dignity evidence. The next measurable work is cross-engine validation, richer school-specific formulas, the remaining vargas, alerts and a polished Vedic UX. These should be separate skills and deterministic tools, not added as prose to the Western Urania profile.

The second gap is distribution and user proof. OracleAI should make the existing proof envelope visible in the deployed Mini App, add a public capabilities page, and add one-click export/delete and multi-profile explanations to the product documentation. Steer has stronger public positioning in these areas even where the technical claims still require independent verification.

## Multilingual routing evidence

The original benchmark is stored in `scripts/benchmark_skill_routing.py`, while Vedic and Mira/Lenormand benchmarks have dedicated scripts. All three are included in `pytest` and `check_agent_quality.py`, and therefore run as release invariants. The original set covers 10 Urania and 10 Lilith prompts; the new Mira/Lenormand set covers 10 palm and 10 Tarot prompts.
It mixes Russian, English and code-switched language, including Rahu/Ketu, synastry, houses, date-only limits, expanded points, lunar journaling, Matrix, emotion naming, boundaries, memory, habit loops, values conflict, diary and conversation rehearsal.

Initial accuracy was **15/20 (75%)**. The failures exposed real lexical gaps rather than random instability: expanded-point vocabulary, date-only phrases such as `no birth time`, lunar journal/week vocabulary, post-conversation emotion naming, and stability-versus-project values conflict. After enriching the affected skills and adding narrowly scoped intent features, the original set reached **20/20 (100%)** top-3 expected-skill inclusion. The new Mira/Lenormand set also reaches **20/20 (100%)** top-3 inclusion and **14/20 top-1**. These are pytest regressions and release invariants; they should still be expanded with adversarial paraphrases before any claim of broad production accuracy.

## Limitations of this comparison

This is a public-surface and repository-contract comparison, not a full black-box product benchmark. Steer’s authenticated app, actual chart calculations, response quality, retention, latency, subscription flows and live API were not tested. OracleAI’s live LLM provider was also not enabled during deterministic acceptance. Accordingly, the matrix distinguishes **verified in code/UI**, **publicly claimed by Steer**, and **not independently verified** rather than treating marketing copy as technical proof.

## References

[1]: https://steercorp.io/ "SteerCorp homepage and product claims"
[2]: https://steercorp.io/support.html "Steer support and FAQ"
[3]: https://steercorp.io/privacy.html "Steer privacy policy"
[4]: https://play.google.com/store/apps/details?id=coach.steer.app&hl=en_US "Steer: AI Coach & Astrologer on Google Play"
