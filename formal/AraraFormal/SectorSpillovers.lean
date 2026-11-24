import Lean

/-! Integer-scaled expected correctness for the registered four-node model. -/
namespace AraraFormal.SectorSpillovers

/-- Change in expected correctness in sector A, scaled by 1600. -/
def sectorA (k : Int) : Int := 600 - 4 * k
/-- Change in expected correctness in sector B, scaled by 1600. -/
def sectorB (k : Int) : Int := 200 - 12 * k

/-- Balanced network change for repair alone, scaled by 1600. -/
def repair (k : Int) : Int := 400 - 8 * k
/-- Balanced network change for repair and rerouting, scaled by 1600. -/
def reroute (k : Int) : Int := 400 - 7 * k

theorem balanced_accounting (k : Int) : 2 * repair k = sectorA k + sectorB k := by
  unfold repair sectorA sectorB
  omega

theorem hidden_sector_harm (k : Int) (hLo : 51 ≤ k) (hHi : k ≤ 100) :
    0 < sectorA k ∧ sectorB k < 0 ∧ repair k < 0 := by
  unfold sectorA sectorB repair
  constructor
  · omega
  · constructor <;> omega

theorem repair_positive_iff (k : Int) : 0 < repair k ↔ k < 50 := by
  unfold repair
  omega

theorem repair_tie_iff (k : Int) : repair k = 0 ↔ k = 50 := by
  unfold repair
  omega

theorem reroute_positive_iff (k : Int) : 0 < reroute k ↔ k ≤ 57 := by
  unfold reroute
  omega

theorem reroute_rescues_aggregate_iff (k : Int) :
    (repair k < 0 ∧ 0 < reroute k) ↔ (51 ≤ k ∧ k ≤ 57) := by
  unfold repair reroute
  omega

/-- Each source's cross-sector route probability is recorded in eighths.
The exchange over the four graph rows is therefore in thirty-seconds. -/
def exchangeNumerator (crossA crossB : Int) : Int := crossA + crossB

def sharedGraphCase (k : Int) : Int × Int := (exchangeNumerator 2 2, repair k)

theorem opposite_outcomes_same_exchange :
    (sharedGraphCase 0).1 = (sharedGraphCase 100).1 ∧
      0 < (sharedGraphCase 0).2 ∧ (sharedGraphCase 100).2 < 0 := by decide

end AraraFormal.SectorSpillovers
