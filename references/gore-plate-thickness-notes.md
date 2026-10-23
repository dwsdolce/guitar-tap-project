# Gore's plate-thickness method — notes

> **Provenance.** Written by Claude (Anthropic): first in claude.ai chats in February 2026, which drew on
> published descriptions of the method found by web search, then rewritten in October 2026 against the
> apps' code. Not checked against the book. The method and its equations are Trevor Gore's:
>
> Gore, T. & Gilet, G. (2011; 2nd ed. 2016). *Contemporary Acoustic Guitar Design and Build*, Vols. 1–2.
> Trevor Gore Guitars, Australia. <https://goreguitars.com.au/the-book/>
>
> Where these notes and the apps differ, the apps' code is what the project implements:
> `MaterialProperties.swift` (Swift, canonical) and `material_properties.py` (Python).

## The idea

Measure the elastic properties of the actual piece of wood from its tap tones, then calculate the thickness
that gives the finished plate a chosen stiffness. Two pieces that differ in stiffness and density are
thicknessed differently, so the finished plates behave alike.

## 1. Tap the test plate

A rectangular test plate (length *L* along the grain, width *W* across it, thickness *t*, density *ρ*) is
held at a node and tapped; the spectrum's fundamental gives each frequency:

| Frequency | Mode | How (the apps' instructions) |
|---|---|---|
| *f*<sub>L</sub> | bending along the grain | held at its nodal points, 22% from each end along its length |
| *f*<sub>C</sub> | bending across the grain | turned 90° and held at its nodal points along its width |
| *f*<sub>LC</sub> | twisting (optional) | held at the midpoint of one long edge, tapped near the opposite corner (~22% from both the end and the side) |

These are dynamic measurements. A static three-point bend test on a strip gives Young's modulus as an
alternative route to *E*<sub>L</sub> or *E*<sub>C</sub>, and agrees closely with the tap method, but it
cannot give the shear modulus *G*<sub>LC</sub>, which needs the twisting tap.

## 2. The plate's moduli

With *ν*<sub>LC</sub>·*ν*<sub>CL</sub> = 0.02 (Gore's average for softwoods):

- Coef₁ = 12 (1 − *ν*<sub>LC</sub>*ν*<sub>CL</sub>) / ((π/2)² (3/2)⁴)
- *E*<sub>L</sub> = Coef₁ · *ρ* · *L*⁴ · *f*<sub>L</sub>² / *t*²
- *E*<sub>C</sub> = Coef₁ · *ρ* · *W*⁴ · *f*<sub>C</sub>² / *t*²
- *G*<sub>LC</sub> = (12 / π²) · *ρ* · *L*² · *W*² · *f*<sub>LC</sub>² / *t*²

SI units throughout (m, kg/m³, Hz → Pa).

## 3. Target thickness (Gore Eq. 4.5-7)

For a guitar body of length *a* (neck joint to tail) and lower-bout width *b*, in metres, and a chosen
vibrational stiffness *f*<sub>vs</sub>:

*t* = Coef₂ · *f*<sub>vs</sub> · *a*² · √*ρ* / √( *E*<sub>L</sub> + (*a*/*b*)⁴ *E*<sub>C</sub> + (*a*/*b*)² (Coef₃ *E*<sub>L</sub> + Coef₄ *G*<sub>LC</sub>) )

- Coef₂ = π √(12 (1 − *ν*<sub>LC</sub>*ν*<sub>CL</sub>) / 126) ≈ 0.9598
- Coef₃ = 4 *ν*<sub>CL</sub> / 7, with *ν*<sub>CL</sub> = 0.05
- Coef₄ = 4 · 12 (1 − *ν*<sub>LC</sub>*ν*<sub>CL</sub>) / 42

*a* and *b* are the finished body's dimensions, not the test plate's. Without the twisting tap *G*<sub>LC</sub>
is taken as 0, which overestimates the thickness by roughly 5–7%.

The apps' presets for *f*<sub>vs</sub>:

| Plate | *f*<sub>vs</sub> |
|---|---|
| Steel-string top | 75 |
| Steel-string back | 55 |
| Classical top | 60 |
| Classical back | 50 |

## Poisson's ratio

Poisson's ratio enters through the coefficients above, as fixed averages for softwoods rather than
per-piece measurements. Measuring it needs strain gauges, which is impractical for a luthier, and it
varies far less between pieces than stiffness or density does. Typical published values of
*ν*<sub>LR</sub>:

| Wood | *ν*<sub>LR</sub> |
|---|---|
| Sitka spruce | 0.37 |
| Engelmann spruce | 0.42 |
| Western red cedar | 0.38 |
| Indian rosewood | 0.30 |
| Mahogany | 0.30 |
| Maple | 0.40 |

The thickness is barely sensitive to it. Poisson's ratio appears as (1 − *ν*<sub>LC</sub>*ν*<sub>CL</sub>),
about 0.98; even a 50% error in the product moves that by about 1%, and the thickness — which goes as
its square root — by about 0.5%, a few hundredths of a millimetre. The thickness is most sensitive to *E*<sub>L</sub> and *ρ*, then to *E*<sub>C</sub> (amplified by
(*a*/*b*)⁴ on wider bodies), and least to *G*<sub>LC</sub>. An error of a hertz or so in reading
*f*<sub>L</sub> or *f*<sub>C</sub> from the spectrum outweighs any error in Poisson's ratio.

## Braces

A brace's bending stiffness is *E* · *I*, with *I* = *b* *d*³ / 12 for a rectangular section of width *b*
and depth *d*: depth dominates. Gore designs the bracing so that the top and braces together are stiff
enough to keep the bridge's rotation under string tension small, while keeping the mass low. The brace
stock's Young's modulus can be measured by a tap test or a three-point bend test.
