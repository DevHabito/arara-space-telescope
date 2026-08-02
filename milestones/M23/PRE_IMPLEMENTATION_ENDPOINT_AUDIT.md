# M23 pre-implementation endpoint audit

The inherited `PositivePanel.t100` field is a legacy variable name.

Inspection of the frozen M9 dependency shows that it is assigned by:

`time_at_fraction(shape_values, cfg.target_fraction)`.

With `target_fraction = 0.50`, its numerical content is therefore t50, not t100.

M22 positive scoring used this field. No endpoint mismatch was found.
