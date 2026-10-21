import AraraFormal.OracleBoundary

/-!
# Observation-only measured-window boundary

This theorem verifies the proposed discrete boundary policy only. It does not
verify a Python implementation, floating-point projected scores, calibration,
or astronomical performance. The true onset does not occur in the policy.
-/

namespace AraraFormal

def measuredWindowValid (endpoint horizon : Nat) : Bool :=
  decide (8 ≤ endpoint ∧ endpoint < horizon)

/-- The proposed boundary policy is independent of any supplied true onset. -/
def proposedWindowMask (_trueOnset endpoint horizon : Nat) : Bool :=
  measuredWindowValid endpoint horizon

theorem proposedMaskIgnoresTrueOnset
    (firstTruth secondTruth endpoint horizon : Nat) :
    proposedWindowMask firstTruth endpoint horizon =
      proposedWindowMask secondTruth endpoint horizon := by
  rfl

theorem earliestFrozenEndpointIsInBounds :
    measuredWindowValid 81 180 = true := by
  decide

theorem latestFrozenEndpointIsInBounds :
    measuredWindowValid 179 180 = true := by
  decide

theorem beyondObservationIsRejected :
    measuredWindowValid 180 180 = false := by
  decide

end AraraFormal
