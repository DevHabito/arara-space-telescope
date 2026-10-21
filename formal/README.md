# Lean 4 formal verification boundary

The Lean library is pinned by lean-toolchain and built by lakefile.toml. Run lake build to check it. The GitHub Actions research-audit workflow runs this in a clean cloud environment. Do not call a theorem verified until the action actually succeeds.

Protocol.lean states fixed hypothesis counts, a control-veto predicate, raw-score bank monotonicity for an abstract maximum, and a threshold-recalibration counterexample. These are discrete logical statements, not proofs of the simulator, floating-point numerical stability, detection power, or real-sky validity.

No sorry or new axioms are introduced in this file. Future formalization should start from explicit specifications and prove invariants of the projection and score implementation, distinguishing real arithmetic from IEEE floating-point behavior.
