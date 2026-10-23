# References

Third-party and background reference material that informed Guitar Tap's DSP, material
model, and UI across all three editions — kept here as shared project reference rather
than in any one edition's repo. Each entry says who wrote it: published papers and downloaded
material are their authors'; notes written by Claude (Anthropic) in discussions with the owner
say so.

## Pitch detection & spectrum display
- **`2002_JASA_YIN.pdf`** — published paper: de Cheveigné & Kawahara, *YIN, a fundamental frequency estimator for speech and music* (JASA, 2002).
- **`Comparing Pitch Detection Algorithms vs Neural Network.pdf`** — published survey comparing conventional pitch-detection algorithms with a neural-network approach.
- **[Fast and Efficient Pitch Detection](https://www.cycfi.com/2017/10/fast-and-efficient-pitch-detection/)** — Joel de Guzman's Cycfi Research article (2017), online.
- **`Spectra.png`** — a downloaded FFT-spectra comparison (two annotated tap-tone captures); a spectrum-display / annotation-style reference.

## Material properties & tonewood
- **`tonewood-references.md`** — curated index of the acoustic-property values, quality thresholds, and equations behind `MaterialProperties.swift` / `material_properties.py` (Blevins free-free beam formula, Gore, etc.). Written by Claude (Anthropic).
- **`gore-plate-thickness-notes.md`** — Gore's plate-thicknessing method: the tap modes, the moduli, the target-thickness equation (Eq. 4.5-7) with the apps' constants and presets, and Poisson's ratio. Written by Claude (Anthropic) from published descriptions of Gore & Gilet's method; not checked against the book.
- **`brace-youngs-modulus-derivation.md`** — where the 22.37 in the Young's-modulus formula comes from: (β₁L)² for a free-free beam. Written by Claude (Anthropic).
- **`guitar-modes.md`** — the guitar body modes the apps name, their T(m,n) equivalents, the apps' bands by guitar type, and what each mode tells a luthier. Written by Claude (Anthropic).
- **`tap-test-metrics.md`** — what a tap test yields: Young's modulus, speed of sound, specific modulus, radiation ratio. Written by Claude (Anthropic).

Assembled during the post-standup cleanup (2026-08-03), from `guitar_tap/docs/` and `GuitarTap/`.
