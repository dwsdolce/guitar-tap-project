# Young's modulus from a tap — where 22.37 comes from

> **Provenance.** Written by Claude (Anthropic): first in a claude.ai chat in February 2026, then rewritten in
> October 2026 against the apps' code (`MaterialProperties.swift`, `material_properties.py`). The beam theory
> is standard: Blevins, *Formulas for Natural Frequency and Mode Shape* (1979), Table 8-1.

The apps calculate Young's modulus along the grain of a plate or brace from its first bending frequency:

E = 48 π² ρ f² L⁴ / (22.37 t)²

with *ρ* the density, *f* the measured frequency, *L* the length and *t* the thickness (SI units). Across the
grain, the width *W* takes the place of *L*. The constant 22.37 is not empirical: it is (β₁L)² for a beam with
free ends.

## Derivation

A strip held at its nodes and tapped vibrates as a free-free Euler–Bernoulli beam. Its bending frequencies are

f<sub>n</sub> = (β<sub>n</sub>L)² / (2π L²) · √(E I / (ρ A))

With both ends free (no bending moment and no shear force at either end), the β<sub>n</sub>L are the roots of

cos(βL) · cosh(βL) = 1

The first two solutions are rigid-body motions; the first bending mode is β₁L = 4.7300, so
(β₁L)² = 22.3733. Its nodes lie 22.4% of the length from each end — which is why the strip is held there.

For a rectangular section of thickness *t*, I / A = t² / 12, so

f = (β₁L)² / (2π L²) · t · √(E / (12 ρ))

Squaring and solving for *E*:

E = 48 π² ρ f² L⁴ / ((β₁L)² t)² = 48 π² ρ f² L⁴ / (22.37 t)²

## Other supports, for comparison

| Supports | β₁L | (β₁L)² |
|---|---|---|
| Free–free (the tap test) | 4.7300 | 22.37 |
| Clamped–free (cantilever) | 1.8751 | 3.516 |
| Simply supported | π = 3.1416 | 9.870 |
