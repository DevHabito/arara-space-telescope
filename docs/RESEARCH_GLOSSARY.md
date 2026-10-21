# Research glossary and claim dictionary

Terms describe either standard methods or ARARA-specific choices. A definition is not evidence that a statistical assumption holds in nature.

| Term | Definition | Provenance |
|---|---|---|
| False-positive rate (FPR) | Fraction of negative cases producing an alert for a specified observational unit | Standard statistics; ARARA measures per synthetic curve, not per field-hour |
| Recall | Fraction of positive cases detected inside a specified window | Standard statistics; ARARA values are conditional on its simulated labels |
| Holdout | Cases withheld from parameter selection and threshold calibration | Standard methodology; fresh seeds do not establish external validity |
| Calibration | Threshold selection using negative cases | Standard detection methodology; the entire searched bank must be included |
| False discovery rate (FDR) | Expected false-discovery proportion among declared discoveries | Standard multiple testing; distinct from ARARA curve-level FPR |
| Familywise error rate (FWER) | Probability of at least one false rejection within a declared family | Standard multiple testing |
| Common-mode nuisance | Interference shared between target and reference observations | Standard signal processing; approximate rank-one artifacts in ARARA simulator |
| Reference-mode projection | Removing a shared reference component before scoring | Standard linear algebra, ARARA-specific implementation |
| Causal alignment anchor | Curve-dependent temporal alignment computed without future information | ARARA term; not a validated physical onset estimate |
| Shape/duration bank | Search over candidate templates and durations | Standard search idea; ARARA-specific candidate family |
| Latent parameter u | Continuous synthetic model parameter | ARARA-specific; no established astrophysical interpretation |
| Structural eligibility | Passing a prespecified non-outcome geometric retention criterion | ARARA protocol term; M38A is not operational detection validation |
| Recovery | Reconstitution of a partially lost experiment | ARARA provenance; changed seeds require a new identity |
| Formal verification | Kernel checking of a precisely stated mathematical proposition | Formal methods; does not independently verify physical assumptions |
| Injection-recovery | Inserting known synthetic signals into observational data and testing recovery | Established astronomical validation approach; not completed on real data for ARARA |

**Nominal hypothesis slots vs computed template evaluations:** A nominal Cartesian-product count may include values ignored by an invariant template family. In M38B the linear family is independent of u, so 73,260 nominal slots correspond to 58,608 computed candidate template scores per curve. These counts do not by themselves determine the effective multiple-testing penalty.
