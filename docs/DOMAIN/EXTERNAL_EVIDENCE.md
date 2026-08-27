# External evidence record

**Review date:** 2026-08-27.

## Swiss Ephemeris

Astro.com’s official Swiss Ephemeris information page states that developers must choose between the GNU Affero General Public License and the Swiss Ephemeris Professional License before distributing software containing Swiss Ephemeris or activating a public service. It also states that the AGPL choice carries the obligation to place the whole software project under AGPL or a compatible license, while the professional path requires purchasing and signing the commercial license. The page requires preservation of copyright and license notices and distinguishes the free edition from the professional edition. [1]

OracleAI currently has `pyswisseph==2.10.3.2` in `requirements.txt` and uses Swiss Ephemeris through Kerykeion. This repository review did **not** find a project-specific commercial Swiss Ephemeris agreement or a completed legal decision to release the application under AGPL. Therefore the distribution/licensing gate remains **OPEN/BLOCKED for release**, even though the upstream terms are now documented.

## Kerykeion

The upstream Kerykeion GitHub repository identifies an AGPL-3.0 license in its repository navigation and its release history identifies the 5.12.x line used by OracleAI. [2] OracleAI pins `kerykeion==5.12.9`; this is compatible with documenting Kerykeion as an AGPL dependency, but dependency presence alone is not a legal determination for OracleAI’s deployment model.

## Numerical comparison scope

`scripts/domain_qa.py` and `docs/ASTRONOMY_REFERENCE_QA.md` compare the canonical Kerykeion adapter to direct `pyswisseph` calls. This is a useful independent implementation-path check, but both paths share the Swiss Ephemeris kernel. It is **not** an independent ephemeris-vendor comparison. Public web calculators discovered during review either expose an interactive form or also advertise Swiss Ephemeris; no stable, machine-readable, independently sourced numeric reference was captured in this run. No fabricated external values are added to the golden corpus. The external vendor/reference comparison gate remains open.

## References

[1] [Astrodienst, Swiss Ephemeris — for 8000 years and more](https://www.astro.com/swisseph/swephinfo_e.htm)

[2] [g-battaglia/kerykeion — upstream GitHub repository](https://github.com/g-battaglia/kerykeion)

## Captured JPL comparison

The saved artifact [`jpl_reference_2026-08-27.json`](jpl_reference_2026-08-27.json) was produced by `scripts/compare_jpl_reference.py`. It queried NASA/JPL Horizons for the same UTC instant as the representative Kazan case (`1990-06-21 14:30 Europe/Moscow` → `1990-06-21T10:30:00Z`), using Earth geocentric center `500@399`, Sun/planet targets, observer quantity 31 and a one-minute window. JPL documents quantity 31 as apparent observer-centered ecliptic-of-date longitude. [3]

All ten canonical planetary longitude comparisons were numerically close; the maximum recorded difference was **0.000282188°** for the Moon. This is evidence of agreement for this representative instant, not a universal accuracy guarantee. JPL quantity 31 does not supply the OracleAI Placidus house cusps/ASC/MC, true lunar-node convention, True Lilith convention or Kerykeion retrograde field in the captured artifact, so those fields remain open rather than being inferred.

## References

[3] [NASA/JPL Solar System Dynamics, Horizons Manual](https://ssd.jpl.nasa.gov/horizons/manual.html)
