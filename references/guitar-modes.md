# Guitar body modes

> **Provenance.** Written by Claude (Anthropic): first in a claude.ai chat in early 2026, then rewritten in
> October 2026 against the apps' code (`GuitarMode.swift` and `GuitarType.swift` in Swift, canonical, and
> their Python and web equivalents), which is what the project implements.

The apps name a guitar's tap-tone peaks with a simplified, luthier-oriented set of modes. They do not map
one-to-one onto the T(m,n) plate-mode notation:

| App's mode | T(m,n) | Notes |
|---|---|---|
| Air (Helmholtz) | T(1,1)₁ | the body's air resonance, coupled to the top |
| Top | T(1,1)₂ | the top's monopole: the whole top moves in and out |
| Back | T(1,1)₃ | the back's monopole |
| Dipole | T(2,1) and/or T(1,2) | the two dipoles in one name |
| Ring Mode | T(2,2), the quadrupole | T(3,1) may also land here |
| Upper Modes | T(3,1) and above | everything higher |

## How the apps name peaks

Each guitar type has a frequency band per mode, in Hz:

| Mode | Classical | Flamenco | Acoustic | Generic |
|---|---|---|---|---|
| Air | 80–110 | 85–115 | 90–120 | 70–135 |
| Top | 170–230 | 180–220 | 150–210 | 140–260 |
| Back | 190–280 | 200–250 | 210–290 | 180–300 |
| Dipole | 330–430 | 350–450 | 360–460 | 310–460 |
| Ring Mode | 580–820 | 600–850 | 620–880 | 580–880 |
| Upper Modes | 820+ | 850+ | 880+ | 880+ |

Going through the modes in order of their bands, each takes the strongest peak in its band that no earlier
mode has taken; Back must also lie above the Top it found, since the back resonates above the top — which
matters where the Top and Back bands overlap. A peak outside every band is Unknown.

## What each mode tells a luthier

The three T(1,1) modes dominate a guitar's sound.

**Air** — sets the bass cutoff: too low sounds boomy, too high thin. Set mainly by the body's volume and the
soundhole's size.

**Top** — the single most important mode, with the largest effect on volume and bass character; the low
strings' fundamentals radiate most strongly near it. It sets "warm versus bright" more than any other mode.

**Back** — adds midrange presence and loudness through its coupling with the top. Typically some 30–50 Hz above
the top on a classical guitar.

**Dipole** — the two halves of the plate move in opposition and partly cancel, so it radiates less efficiently;
it makes notches in the upper bass and lower midrange. The two dipoles reflect stiffness across and along the
grain and sit at different frequencies, but the apps name whichever falls in the band.

**Ring Mode** — colours the upper midrange (a "nasal" quality). More important for violins than guitars;
luthiers watch it rather than tune for it.

**Upper Modes** — treble shimmer; not tuned individually.

## The relationships matter more than single frequencies

- **Top/Air ratio** — bass balance; the apps show it with an ideal of 1.9–2.1. Too close sounds muddy; too far
  apart gives an uneven response across registers.
- **Top/Back spacing** — too close and they interfere; a back below the top makes the guitar sound thin.
- **Q of Air and Top** — a sharp, high-Q peak resonates efficiently over a narrow band; a lower Q spreads the
  energy more broadly. The apps show Q for every peak.

In practice, in order: the Air frequency (body tuning), the Top frequency (character), the Top/Air ratio, the
Top's Q, the Back relative to the Top, and the decay time. The dipole and higher modes are worth seeing but are
rarely what a luthier changes the bracing for.
