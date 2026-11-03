# Literature, provenance, and originality boundaries

**Bibliographic review:** 3 November 2026. I checked the publication metadata, abstracts, and publisher, author, or institutional records linked below. This is **not** a claim that I read every full book or that I have reproduced each paper's analysis. Publication year is not the date a repository page was last updated.

## My distinction between prior work and ARARA

I am using established methods from statistics, numerical linear algebra, astronomy and reproducible research. The ARARA-specific contribution under study lies in its synthetic regimes, its particular causal-onset/shape-duration-latent bank, preprocessing choices, test protocols and engineering integration. A new arrangement of familiar techniques does not establish a new law of nature.

The existing literature gives me methods to compare against and standards for constructing defensible experiments. It does not validate ARARA by association. In particular, astrophysical transit light curves with planetary and stellar parameters are **not** automatically represented by the project's generic synthetic rising templates.

## Sources verified for this audit

### Numerical analysis and projection

1. **Gene H. Golub and Charles F. Van Loan (2013).** *Matrix Computations*, fourth edition. Johns Hopkins University Press, published 15 February 2013. [Publisher record](https://www.press.jhu.edu/books/title/10678/matrix-computations). [SIAM book record/DOI](https://doi.org/10.1137/1.9781421407944). **Relevance:** orthogonal projection, linear algebra and numerical algorithms are standard mathematical tools. **Boundary:** the book does not check ARARA's particular implementation or its numerical conditioning.

2. **Nicholas J. Higham (2002).** *Accuracy and Stability of Numerical Algorithms*, second edition. Society for Industrial and Applied Mathematics. [Author's book record](https://nhigham.com/accuracy-and-stability-of-numerical-algorithms/). [Publisher DOI](https://doi.org/10.1137/1.9780898718027). **Relevance:** floating-point error, conditioning and computational stability. **Boundary:** I have not derived a complete IEEE error bound for the ARARA scorer from this book.

### Astronomy: template searches and physical interpretation

3. **Géza Kovács, Shay Zucker and Tsevi Mazeh (2002).** “A box-fitting algorithm in the search for periodic transits.” *Astronomy & Astrophysics*, **391**, 369–377; published online 29 July 2002. DOI: [10.1051/0004-6361:20020802](https://doi.org/10.1051/0004-6361:20020802). [Journal record](https://www.aanda.org/articles/aa/abs/2002/31/aa2422/aa2422.html). **Relevance:** established searches over parameterized light-curve templates. **Boundary:** BLS concerns periodic transit-like dimming; ARARA's synthetic rising templates are different objects. This is a methodological comparison, not proof of superiority or physical correspondence.

4. **Kaisey Mandel and Eric Agol (2002).** “Analytic Light Curves for Planetary Transit Searches.” *The Astrophysical Journal Letters*, **580**, L171–L175; published 8 November 2002. DOI: [10.1086/345520](https://doi.org/10.1086/345520). [Caltech record](https://authors.library.caltech.edu/records/z46qg-me992). **Relevance:** explicit physical photometric models and limb darkening offer a standard against which a proposed astronomical interpretation should be assessed. **Boundary:** the paper does not confer an astrophysical meaning on ARARA's latent parameter `u`.

5. **Jessie L. Christiansen, Bruce D. Clarke, Christopher J. Burke, Jon M. Jenkins, Stephen T. Bryson, Jeffrey L. Coughlin, Susan E. Mullally, Joseph D. Twicken, Natalie M. Batalha, Joseph Catanzarite, AKM Kamal Uddin, Khadeejah Zamudio, Jeffrey C. Smith, Christopher E. Henze and Jennifer Campbell (2020).** “Measuring Transit Signal Recovery in the Kepler Pipeline. IV. Completeness of the DR25 Planet Candidate Catalog.” *The Astronomical Journal*, **160**, 159; published 10 September 2020. [Caltech institutional record and paper](https://authors.library.caltech.edu/records/qd364-hev76). [arXiv:2010.04796](https://arxiv.org/abs/2010.04796). **Relevance:** injection–recovery studies through the actual Kepler pipeline measure detection efficiency conditional on the instrument and target data. **Boundary:** ARARA has not performed a comparable real-observation completeness study.

### Statistics, integrity and protocol discipline

6. **Yoav Benjamini and Yosef Hochberg (1995).** “Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing.” *Journal of the Royal Statistical Society: Series B*, **57**(1), 289–300. DOI: [10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x). [Publisher record](https://academic.oup.com/jrsssb/article/57/1/289/7035855). **Relevance:** multiplicity and false discovery control are standard statistical subjects. **Boundary:** FDR is not the same as the per-synthetic-curve FPR that appears in the ARARA archive. The nominal 73,260 template slots cannot be treated as independent tests without evidence.

7. **Shachar Kaufman, Saharon Rosset, Claudia Perlich and Ori Stitelman (2012).** “Leakage in data mining: Formulation, detection, and avoidance.” *ACM Transactions on Knowledge Discovery from Data*, **6**(4), article 15; published 18 December 2012. DOI: [10.1145/2382577.2382579](https://doi.org/10.1145/2382577.2382579). [ACM record](https://dl.acm.org/doi/10.1145/2382577.2382579). **Relevance:** information that is not legitimately available at prediction time can invalidate an evaluation. **Boundary:** the paper is prior methodology. The actual ARARA leakage diagnosis rests on this repository's code and counterfactual tests, not on the citation.

8. **Brian A. Nosek, Charles R. Ebersole, Alexander C. DeHaven and David T. Mellor (2018).** “The preregistration revolution.” *Proceedings of the National Academy of Sciences*, **115**(11), 2600–2606; published online 12 March 2018. DOI: [10.1073/pnas.1708274114](https://doi.org/10.1073/pnas.1708274114). [Publisher record](https://www.pnas.org/doi/full/10.1073/pnas.1708274114). **Relevance:** separating hypothesis development from prospectively locked tests. **Boundary:** creating a draft protocol *after* earlier tests does not retroactively create an untouched holdout or valid prospective evidence.

9. **C. M. Croarkin (2003).** “NIST/SEMATECH Engineering Statistics Handbook, Chapter 2: Measurement Process Characterization.” National Institute of Standards and Technology; published 1 June 2003. [NIST record](https://www.nist.gov/publications/nistsematech-engineering-statistics-handbook-chapter-2-measurement-process). **Relevance:** measurement-process uncertainty, repeatability, reproducibility and stability are engineering questions distinct from algorithm unit tests. **Boundary:** no ARARA hardware or instrument-calibration result is implied.

### Tools and project references (not journal articles)

- **Lean 4 project:** [Lean 4 source](https://github.com/leanprover/lean4), and the [repository's formal boundary](../formal/README.md). Formal checking validates the proposition supplied to the checker, not unmodeled physical assumptions. The installed compiler is pinned by [`lean-toolchain`](../lean-toolchain). I do not invent authors or a paper DOI for the software project.
- **NASA HEASARC:** [TESS SPOC data pipeline](https://heasarc.gsfc.nasa.gov/docs/tess/data_pipeline.html). Institutional pipeline background; no ARARA performance result.
- **Lightkurve documentation:** [searching Kepler, K2 and TESS products](https://lightkurve.github.io/lightkurve/tutorials/1-getting-started/searching-for-data-products.html). Practical data-access guidance; not a peer-reviewed measurement of ARARA.

## Originality and citation rules for future results

| Claim type | Evidence required | What I must not claim |
| --- | --- | --- |
| Mathematical identity | Derivation, theorem statement, proof assumptions and checked formal artifact | Novel mathematical discovery from a textbook identity |
| Software reproducibility | Exact code commit, environment, fixtures, tests, logs and source hashes | Astronomical validity from a green CI badge |
| Synthetic detection performance | Prospectively frozen generator, calibration, sample counts, thresholds and untouched holdouts | General physical false-alarm rates from synthetic FPR |
| Physical astronomy | Independent observations, instrument response, uncertainties, physical model and blind comparisons | Space-telescope readiness from simulation alone |
| Independent method | A genuinely separate derivation and implementation with explicit comparison policy | Independence merely because a wrapper changed a function signature |

## Source-record discipline

Each future bibliography entry must include the authors as verified, original publication year/date, exact title, venue or publisher, stable DOI or institutional link, the claim for which I cite it, and an explicit limitation. If I have only checked a publisher abstract or metadata, I will say so. I will not invent a DOI, convert an institutional tutorial into a paper, or use a citation as evidence that a particular ARARA experiment passed.

The [research notebook](RESEARCH_NOTEBOOK_2026-11-03.md) records observed outcomes. The [failure register](FAILURE_AND_LIMITATIONS_REGISTER.md) records what is missing. This bibliography records **prior art**. They should not be merged into one undifferentiated list of achievements.
