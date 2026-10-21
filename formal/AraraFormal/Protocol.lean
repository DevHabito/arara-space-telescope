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

/-! The linear shape is independent of u in the source implementation.
The nonlinear power-law, exponential and logistic shapes use five u values.
This counts template score evaluations, not necessarily distinct statistics. -/
def candidateEvaluations (endpoints durations latentValues : Nat) : Nat :=
  endpoints * durations * (1 + 3 * latentValues)

theorem evaluatedCandidateCount : candidateEvaluations 99 37 5 = 58608 := by
  decide

theorem nominalSlotsExceedEvaluations :
    candidateEvaluations 99 37 5 < hypothesisCount 99 4 37 5 := by
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
