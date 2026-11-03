import AraraFormal.OnsetEligibility

/-!
# Single-step AR(1) prefix causality

A fixed AR coefficient, current sample, and immediately preceding sample
determine a filtered value. Equal observational prefixes therefore produce
the same filter result at the endpoint. The coefficient is assumed equal.

This abstract exact-integer theorem does NOT prove that NumPy computes this
formula without rounding error, that an upstream fitted coefficient is
prefix-causal, or that the whole astronomical pipeline is causal.
-/

namespace AraraFormal

def ar1FilterAt (series : Nat → Int) (phi : Int) (at : Nat) : Int :=
  if at = 0 then series 0 else series at - phi * series (at - 1)

theorem ar1FilterAtUsesOnlyPrefix
    (left right : Nat → Int) (phi : Int) (at : Nat)
    (samePrefix : ∀ index, index ≤ at → left index = right index) :
    ar1FilterAt left phi at = ar1FilterAt right phi at := by
  by_cases h : at = 0
  · simp [ar1FilterAt, h, samePrefix 0 (by omega)]
  · simp [ar1FilterAt, h, samePrefix at (by omega),
      samePrefix (at - 1) (by omega)]

theorem ar1FilterAtZero (series : Nat → Int) (phi : Int) :
    ar1FilterAt series phi 0 = series 0 := by
  simp [ar1FilterAt]

end AraraFormal
