# AR-SWARM002-P01 — Peer confirmation with imperfect provenance

Registration date: 24 November 2026 (America/Sao_Paulo).
This is a prospective registration for exact enumeration of a two-node reporting network. The preceding [feasibility note](../research/AR-SWARM002-peer-audit-feasibility.md) used a marginal report model; it did not run the provenance policies or registered stress conditions below.

## Generative model

A emits a positive candidate. There is one directed audit link B → A. Condition on that candidate throughout. Ground truth Y is either sky or fault, each with probability 1/2. A hidden per-case variable D indicates whether the two processing paths share the failure route, with P(D=shared)=1/2 independent of Y. B has matching observational coverage with probability c, independent of Y and D; without it the audit receives no report or provenance tag.

With coverage, B's ideal bit is positive if Y=sky or D=shared. The report bit is flipped with probability e. The observable provenance tag Z encodes whether paths share the route, with symmetric error probability r. Coverage, report flip and tag flip are mutually independent and independent of Y and D. Decisions receive availability and the permitted observed bit/tag only. D and Y are reserved for generation and scoring. A false sky confirmation is deciding sky when Y=fault.

All parameters are hypothetical. The graph represents communication and one shared processing dependency, with no sector exchange, repairs or telescope hardware. There is no temporal forecast. Missing coverage means no basis for a peer check, independent of how a real mission would schedule observations.

## Frozen policies and score

Each policy has actions sky, fault, abstain. A wrong classification costs 1, a correct one costs 0, and abstention costs 1/4. Report exact total risk, per-label masses for all actions conditional on the label, decision coverage (fraction with a definitive classification), and conditional error among definitive decisions (null at zero coverage).

- A alone always abstains.
- Literal agreement uses sky for positive B, fault for negative B, and abstains when B is unavailable.
- Bit only uses the nominal Bayes rule with access to B availability and bit only.
- Bit and provenance uses the nominal Bayes rule with access to B availability, bit and tag.

Nominal is c=3/4, e=1/10, r=1/10. For each information set, generate nominal joint probability masses by enumeration. At each observable state, choose the action with smallest nominal conditional expected cost, breaking ties in order abstain, fault, sky. This is model-based calibration, not learning from held-out data. Freeze both derived mappings for every stress case. The analytical comparator is optimal given only availability and the bit under nominal parameters, so the provenance policy is compared against more than literal voting.

## Evaluation fixed before implementation

Run the following exact environments, keeping unspecified parameters nominal:

| Name | Inputs |
|---|---|
| nominal | c=3/4, e=1/10, r=1/10 |
| perfect_tag | r=0 |
| uninformative_tag | r=1/2 |
| inverted_tag | r=1 |
| no_coverage | c=0 |
| uninformative_report | e=1/2 |
| tag stress sweep | r=k/100, k=0 through 100 inclusive |

- H1: nominal bit-and-provenance risk is strictly lower than both nominal bit-only risk and nominal A-alone risk. Report both differences and the false-sky tradeoff even if H1 fails.
- H2: the frozen bit-and-provenance policy has strictly higher risk than bit only under inverted tags. The uninformative-tag and uninformative-report environments are controls; record their outcomes without assuming direction.
- Integrity: class and total mass conservation, equality of all policies in the no-coverage case, exact verification of nominal optimal rules by exhaustive enumeration of decision tables, deterministic outputs, and presence of all stress sweep points. Retain ties and adverse results. Record where the registered grid changes the direction of the risk comparison without interpolating between points.

Use Python standard library fractions; enumerate all primitive states and do not sample RNG seeds. Save exact fractions as strings in JSON. Run the previous feasibility checks as regression. No tuning of loss, policies, parameters or hypotheses after inspecting outputs. A remedy for an implementation error requires preserving the failure and recording the correction. This model can illustrate when provenance helps under explicit assumptions; it cannot estimate mission parameters or justify a repair action in a flight system.
