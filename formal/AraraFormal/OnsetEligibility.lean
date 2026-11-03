import AraraFormal.ProjectionWitness

/-!
# Frozen hinge candidate eligibility

M34 computes the selection end as endpoint - confirmation_length - guard_length,
with frozen lengths 8 and 1. Candidate eligibility requires at least three
post-onset samples in that selection interval.

This is exact natural-number arithmetic, not a proof of the floating-point
estimator, its tie behavior, or physical onset identifiability.
-/

namespace AraraFormal

def hingeEligible (endpoint candidate : Nat) : Prop :=
  3 ≤ endpoint - 9 - candidate + 1

theorem hingeEligibilityEquivalent (endpoint candidate : Nat) :
    hingeEligible endpoint candidate ↔ candidate + 11 ≤ endpoint := by
  simp only [hingeEligible]
  omega

theorem firstFrozenEndpointAllowsCandidate70 : hingeEligible 81 70 := by
  decide

theorem firstFrozenEndpointExcludesCandidate71 : ¬ hingeEligible 81 71 := by
  decide

end AraraFormal
