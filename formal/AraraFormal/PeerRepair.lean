import Lean

/-! Exact integer-scaled consequences of the peer audit and repair models. -/
namespace AraraFormal.PeerRepair

/-- Loss multiplied by ten, with integer masses on a common scale. -/
def repairLoss10 (skyCost skyMass faultMass : Int) : Int :=
  10 * skyCost * skyMass + faultMass

def deferLoss10 (faultMass : Int) : Int := 10 * faultMass

theorem repair_improves_iff (skyCost skyMass faultMass : Int) :
    repairLoss10 skyCost skyMass faultMass < deferLoss10 faultMass ↔
      10 * skyCost * skyMass < 9 * faultMass := by
  unfold repairLoss10 deferLoss10
  omega

/-- SWARM002 audit losses with common denominator 16000; k is tag-error percent. -/
def provenanceAuditLoss (k : Int) : Int := 3100 + 24 * k
def bitAuditLoss : Int := 3700

theorem audit_lower_iff (k : Int) :
    provenanceAuditLoss k < bitAuditLoss ↔ k < 25 := by
  unfold provenanceAuditLoss bitAuditLoss
  omega

theorem audit_equal_iff (k : Int) :
    provenanceAuditLoss k = bitAuditLoss ↔ k = 25 := by
  unfold provenanceAuditLoss bitAuditLoss
  omega

/-- The provenance rule defers on an additional joint mass of sky and fault
cases. The masses have denominator 8000 and the resulting delta has 80000. -/
def repairDelta (skyCost k : Int) : Int :=
  deferLoss10 (150 + 12 * k) - repairLoss10 skyCost 150 (150 + 12 * k)

theorem default_cost_provenance_improves_iff (k : Int) :
    repairDelta 1 k < 0 ↔ k ≤ 1 := by
  unfold repairDelta deferLoss10 repairLoss10
  omega

theorem high_cost_provenance_improves_iff (k : Int) :
    repairDelta 4 k < 0 ↔ k ≤ 43 := by
  unfold repairDelta deferLoss10 repairLoss10
  omega

theorem no_grid_tie (k : Int) : repairDelta 1 k ≠ 0 ∧ repairDelta 4 k ≠ 0 := by
  unfold repairDelta deferLoss10 repairLoss10
  omega

theorem nominal_and_inverted_witness :
    repairDelta 1 10 = 930 ∧ repairDelta 1 100 = 10650 ∧
    repairDelta 4 10 = -3570 ∧ repairDelta 4 100 = 6150 := by decide

end AraraFormal.PeerRepair
