import AraraFormal.OnsetEligibility

/-!
# Single-step AR(1) prefix causality

A fixed AR coefficient, current sample, and immediately preceding sample
determine a filtered value. Equal observational prefixes therefore produce
the same filter result endpoint the endpoint. The coefficient is assumed equal.

This abstract exact-integer theorem does NOT prove that NumPy computes this
formula without rounding error, that an upstream fitted coefficient is
prefix-causal, or that the whole astronomical pipeline is causal.
-/

namespace AraraFormal

def ar1FilterAt (series : Nat → Int) (phi : Int) (endpoint : Nat) : Int :=
  if endpoint = 0 then series 0 else series endpoint - phi * series (endpoint - 1)

theorem ar1FilterAtUsesOnlyPrefix
    (left right : Nat → Int) (phi : Int) (endpoint : Nat)
    (samePrefix : ∀ index, index ≤ endpoint → left index = right index) :
    ar1FilterAt left phi endpoint = ar1FilterAt right phi endpoint := by
  by_cases h : endpoint = 0
  · simp [ar1FilterAt, h, samePrefix 0 (by omega)]
  · simp [ar1FilterAt, h, samePrefix endpoint (by omega),
      samePrefix (endpoint - 1) (by omega)]

theorem ar1FilterAtZero (series : Nat → Int) (phi : Int) :
    ar1FilterAt series phi 0 = series 0 := by
  simp [ar1FilterAt]

end AraraFormal
