import Init

/-!
# ARARA protocol invariants

Only discrete bookkeeping and a Boolean veto are formalized here.
This is not a proof of statistical calibration or astrophysical validity.
-/

namespace AraraFormal

def hypothesisCount (endpoints shapes durations latentValues : Nat) : Nat :=
  endpoints * shapes * durations * latentValues

theorem frozenControlCount : hypothesisCount 99 4 37 1 = 14652 := by
  decide

theorem frozenCandidateCount : hypothesisCount 99 4 37 5 = 73260 := by
  decide

theorem singleLatentCount (endpoints shapes durations : Nat) :
    hypothesisCount endpoints shapes durations 1 =
      endpoints * shapes * durations := by
  simp [hypothesisCount]

def approve (controlValid candidateValid : Bool) : Bool :=
  controlValid && candidateValid

theorem invalidControlVetoes (candidateValid : Bool) :
    approve false candidateValid = false := by
  cases candidateValid <;> rfl

theorem invalidCandidateVetoes (controlValid : Bool) :
    approve controlValid false = false := by
  cases controlValid <;> rfl

theorem candidatePassAloneIsInsufficient : approve false true = false := by
  rfl

def candidateMaximum (controlScore alternateScore : Nat) : Nat :=
  max controlScore alternateScore

theorem bankInclusionNeverLowersRawMaximum
    (controlScore alternateScore : Nat) :
    controlScore ≤ candidateMaximum controlScore alternateScore := by
  exact Nat.le_max_left _ _

def detected (score threshold : Nat) : Bool :=
  decide (threshold ≤ score)

/-- Counterexample: increasing the raw maximum need not increase detection
    when the candidate has a separately calibrated threshold. -/
theorem recalibrationCounterexample :
    (5 ≤ 6) ∧ detected 5 4 = true ∧ detected 6 7 = false := by
  decide

end AraraFormal
