import AraraFormal.Protocol

/-!
# A source-level boundary-mask counterexample

This is a discrete counterexample to a prerequisite of operational onset
independence, not a proof of observed detector score changes or prevalence.
The archived implementation adds true onset when checking template bounds.
-/

namespace AraraFormal

def sourceInBounds (endpoint estimatedOnset trueOnset horizon : Nat) : Bool :=
  decide (endpoint - estimatedOnset + trueOnset < horizon)

/-- With identical endpoint, estimated onset and curve length, replacing
    the hidden true onset can change the archived template boundary mask. -/
theorem trueOnsetCanChangeBoundary :
    sourceInBounds 179 80 80 180 = true ∧
    sourceInBounds 179 80 110 180 = false := by
  decide

end AraraFormal
