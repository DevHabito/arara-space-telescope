import AraraFormal.ObservationOnly

/-!
# Finite exact-arithmetic reference-projection witnesses

The scaled orthogonal residual is norm²(reference) * template
minus dot(template, reference) * reference. Integer calculations avoid
floating-point rounding in these deliberately narrow test cases.

These theorems do not establish a general projection theorem or verify
NumPy, the detector, or the scientific calibration.
-/

namespace AraraFormal

def dot2 (left right : Int × Int) : Int :=
  left.1 * right.1 + left.2 * right.2

def scaledResidual2 (template reference : Int × Int) : Int × Int :=
  let energy := dot2 reference reference
  let coefficient := dot2 template reference
  (energy * template.1 - coefficient * reference.1,
   energy * template.2 - coefficient * reference.2)

theorem exactReferenceEnergyWitness :
    dot2 (3, 4) (3, 4) = 25 := by
  decide

theorem independentOrthogonalWitness :
    dot2 (scaledResidual2 (4, -3) (3, 4)) (3, 4) = 0 := by
  decide

theorem parallelTemplateCancelsExactly :
    scaledResidual2 (3, 4) (3, 4) = (0, 0) := by
  decide

theorem zeroReferenceKeepsScaledResidualZero :
    scaledResidual2 (3, 4) (0, 0) = (0, 0) := by
  decide

end AraraFormal
