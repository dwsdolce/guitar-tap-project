# What a tap test measures

> **Provenance.** Written by Claude (Anthropic): first in a claude.ai chat in early 2026, then rewritten in
> October 2026 against the apps' code (`MaterialProperties.swift`, `material_properties.py`), which is what the
> project implements. Typical values are from published tonewood data; see `tonewood-references.md`.

From a plate's or brace's dimensions, mass and tap frequencies along and across the grain, the apps derive:

**1. Young's modulus** — stiffness, along the grain (*E*<sub>L</sub>) and across it (*E*<sub>C</sub>), from the
first bending frequency of a free-free beam:
E = 48 π² ρ f² L⁴ / (22.37 t)² (see `brace-youngs-modulus-derivation.md`).

**2. Speed of sound** — c = √(E / ρ). Typical for guitar-top spruce: 4 800–5 800 m/s along the grain,
900–1 800 m/s across it. (A tap excites bending, not the compressional wave, so *c* comes from *E*; the
formula c = 2 L f applies only to a bar's compressional mode.)

**3. Specific modulus** — E / ρ = c², stiffness for weight, in GPa/(g/cm³). The most telling single figure for
a soundboard: stiff but light. The apps grade wood quality on it, at least:

| Grade | Spruce, along | Spruce, across | Cedar, along | Cedar, across |
|---|---|---|---|---|
| Excellent | 25 | 1.5 | 22 | 1.3 |
| Very good | 22 | 1.2 | 19 | 1.0 |
| Good | 19 | 0.9 | 16 | 0.7 |
| Fair | 16 | 0.6 | 13 | 0.5 |

Below Fair is Poor.

**4. Radiation ratio** — R = c / ρ = √(E / ρ³): how efficiently the wood turns vibration into sound.

**5. Cross-grain to long-grain ratio** — E<sub>C</sub> / E<sub>L</sub>, typically 0.04–0.08 for spruce; it
affects how the top responds across its different modes.
