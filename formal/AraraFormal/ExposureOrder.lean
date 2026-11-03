import AraraFormal.OnsetEligibility

/-!
# P0.7 exact integer witnesses for bounded exposure ordering

These theorems describe ordinary natural-number arithmetic. They are
NOT proofs about IEEE 754, UTC timestamps, physical instrument clocks,
probabilistic uncertainty or the Python exposure-provenance ledger.
-/

namespace AraraFormal

def boundedExposureBefore
    (firstEnd firstEndBound secondStart secondStartBound : Nat) : Prop :=
  firstEnd + firstEndBound + secondStartBound < secondStart

theorem boundedExposureBeforeImpliesNominalOrder
    (firstEnd firstEndBound secondStart secondStartBound : Nat)
    (h : boundedExposureBefore firstEnd firstEndBound secondStart secondStartBound) :
    firstEnd < secondStart := by
  unfold boundedExposureBefore at h
  omega

theorem separationWithBoundsWitness :
    boundedExposureBefore 100 1 105 1 := by
  decide

theorem overlapWithBoundsIsIneligible :
    ¬ boundedExposureBefore 100 2 103 2 := by
  decide

end AraraFormal
