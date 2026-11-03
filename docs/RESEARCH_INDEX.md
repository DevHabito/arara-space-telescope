# ARARA research index

I keep this page as the starting point for the current research record. The project has a large historical archive; the pages here distinguish archived statements, fresh audit evidence and future proposals.

## Start here

- [Scientific status](SCIENTIFIC_STATUS.md) — what the archive can and cannot establish about astronomy.
- [Research notebook — 3 November 2026](RESEARCH_NOTEBOOK_2026-11-03.md) — first-person account of the P0.1/P0.2 audit, source trace, numbers checked in GitHub Actions and decisions.
- [Failure and limitation register](FAILURE_AND_LIMITATIONS_REGISTER.md) — negative findings, failed attempts, corrected engineering mistakes and unresolved scientific blockers.
- [Literature and originality](LITERATURE_AND_ORIGINALITY.md) — authors, publication years, stable sources, prior methods and limits of relevance.
- [Research glossary](RESEARCH_GLOSSARY.md) — terms and definitions without implying validity from terminology.

## Scientific experiment boundary

- [M38B-R prospective design](../experiments/M38B-R/README.md) and [draft protocol](../experiments/M38B-R/PROTOCOL_DRAFT.json) — **not authorized for calibration**.
- [Independent onset audit](../experiments/M38B-R/INDEPENDENT_ONSET_AUDIT.md).
- [Independent projection audit](../experiments/M38B-R/INDEPENDENT_PROJECTION_AUDIT.md).
- [Observation-only source and data provenance](../experiments/M38B-R/OBSERVED_DATA_PROVENANCE_AUDIT.md).
- [P0.2 protocol dataflow](../experiments/M38B-R/PROTOCOL_DATAFLOW_AUDIT.md).
- [Open draft PR #9](https://github.com/DevHabito/arara-space-telescope/pull/9), [source-oracle issue #4](https://github.com/DevHabito/arara-space-telescope/issues/4), and [independent-scorer issue #7](https://github.com/DevHabito/arara-space-telescope/issues/7).

## Archives, code verification and old context

- [Historical checkpoint — 21 October 2026](RESEARCH_CHECKPOINT_2026-10-21.md).
- [Historical computational report](../TEST_REPORT.md).
- [GitHub Actions research audit, 3 November](https://github.com/DevHabito/arara-space-telescope/actions/runs/41712840089) and [historical test run](https://github.com/DevHabito/arara-space-telescope/actions/runs/41712840362).
- [Lean formal verification boundary](../formal/README.md).

## How I will write further entries

For each stage I will record its date, exact branch and commit, the question being tested, relevant prior literature, the pre-outcome method, data provenance, tested fixtures, numerical comparisons, failures, CI job links and unresolved limitations. I will distinguish “a source file contains X,” “a test actually executed,” “Lean checked this theorem,” and “an astronomical observation establishes Y.” I will never turn one category into another without new evidence.

**As of 3 November 2026:** historical M38B has no operational verdict; prospective M38B-R remains design-only and is not approved for calibration.
