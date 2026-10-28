# Tips & Technique: one set of advice, and a luthier's answers

**Issue:** [#48](https://github.com/dwsdolce/guitar-tap-project/issues/48)

Status: **✅ COMPLETE (2026-10-27)** — every item decided with the owner and made: GuitarTap `2f07e03` (the manual's ch02, ch03, ch10, and Help), guitar_tap `c3a96e1`, GuitarTapWeb `7d39eb0` (Help); reviewed by the owner. No release-note entry (owner: not a major change). The luthier's credit is added if he wants one.

## The request (owner, 2026-10-27)

1. **The Quick Start Guide's Tips & Technique and the User Manual's are inconsistent.** The Quick Start's is a Help
   section, the same in all three editions (Swift `HelpView.swift`, Python `help_view.py`, the web's
   `QuickStartGuide.tsx`); the manual's is ch10, *Tips, Technique, and Troubleshooting*.
2. **A luthier's answers, to add to the documentation** — some in the chapter where the subject is first presented,
   some in Tips & Technique; decided an item at a time. Written without attribution; a credit is added if he wants
   one.

### The original questions and answers

As received (the answers are the luthier's; his name is left out until he says whether he wants to be credited):

> Can the guitar tap be performed with or without strings and string tension? Yes, there is little difference with
> tension or not when collecting the frequencies. are there implications (e.g. mass of bridge pins)? Yes, mass makes a
> difference.
>
> Where is the best location to place the foam string dampers, do they need to be wedged against the fingerboard, is
> floating over the sound hole, etc. Do not place over the soundhole. This will alter the amount of air leaving the
> soundhole and thus alter the box frequency. I place them between the strings and fretboard.
>
> There is a statement about "tap the top, side, or back"; does tapping "anywhere" yield the same result, or is there a
> "best" tap location for exciting the air, top or back? I try to tap around the area of the monopole. If you tap
> directly on the centerline you could affect the dipole.
>
> In one of Gore's videos, he was tapping (seemingly randomly) all over the top around the lower bout and around the
> bridge. He uses Visual Analyzer and it averages 10 taps. That is why he uses various locations when tapping.
>
> In your demo, you were tapping the bridge, but I couldn't tell if you were tapping the wings or on the node
> centerline. I tap the bridge wings. Is there a difference between bass side or treble side due to bracing, back of
> bridge or on the saddle? Not usually.

## Terms

- **Monopole** — the top's main mode: the lower bout moving in and out as one. Guitar Tap labels it **Top**.
- **Dipole** — the two halves of the top moving in opposite directions, the centreline still (a node line). Guitar
  Tap labels it **Dipole**.
- **Foam string dampers** — foam wedged among the strings to stop them ringing while the body is tapped.

## Items

Each item: what it is, where it could go, and — once agreed — the decision and when it was done. **T** items are
where the Quick Start's Tips & Technique and the manual's ch10 already disagree; **L** items are the luthier's
answers.

| # | Item | Proposed place | Status |
|---|---|---|---|
| T1 | The tap's contact time: the Quick Start says a slow, pressing contact gives a **cleaner** fundamental; the manual (§10.1) says a long slow push **muddies** the spectrum | the Quick Start, to agree with §10.1 (short, crisp contact) | **decided** (owner, 2026-10-27): the manual is right; the Quick Start's tip now reads "The shorter the contact, the cleaner the spectrum: a slow, pressing contact excites fewer overtones and muddies it." — in all three editions, uncommitted |
| T2 | Where to tap a guitar: the Quick Start says "near the bridge area"; §10.1 lists the bridge centre, each wing, below the bridge, each side | with L3 and L5 | **decided** (owner, 2026-10-27): with L3–L5; see L3 |
| T3 | Topics in one only: the Quick Start's *Air Mode for Setup* (a palm clapped over the sound hole); the manual's §10.3 *Background Noise*, §10.4 *Decoupling the Top from the Air Mode*, §10.6 *Multi-Tap Averaging Strategy* | to decide: add to the other, or leave | **decided** (owner, 2026-10-27): the same list in both. *Air Mode for Setup* is dropped (it came with the first Quick Start, 2026-03, with no source; it does not fit a workflow that reads the air mode from a top tap). The Quick Start gains *Background Noise* (§10.3), *Reading the Top Without the Air Mode* (§10.4) and *How Many Taps* (§10.6), all three editions. Found on the way: §10.6 gave the diagonal (fLC) tap its own count, but Taps is one setting for every phase of a plate measurement — merged into the plate bullet. |
| L1 | Strings on or off, and string tension, change the frequencies little; mass does (bridge pins, anything attached) — so measure the same configuration each time | where the guitar is set up for a measurement (ch03, or ch02's *Your First Tap*), or ch10 | **decided** (owner, 2026-10-27): with L2: a *Preparing the guitar* paragraph in ch03 §3.2, and a Quick Start tip, *Preparing the Guitar* (all three editions). |
| L2 | Foam string dampers: between the strings and the fingerboard, never over the sound hole — it changes the air leaving the sound hole, and so the air (Helmholtz) frequency | with L1; and a cross-reference from §10.4, which blocks the sound hole on purpose | **decided** (owner, 2026-10-27): in ch03 §3.2 and the Quick Start tip with L1; §10.4 ends: blocking the sound hole is only for that reading — nothing may cover it in a normal measurement, foam string dampers included. |
| L3 | Where to tap: around the monopole area; right on the centreline affects the dipole (the centreline is its node line) | ch03's walkthrough and ch02's *Your First Tap*, and §10.1 | **decided** (owner, 2026-10-27): the main spot is the top near the bridge, just off the centreline; the bridge wings are two more; the centreline is the dipole's node line. In §10.1, ch03 §3.4 step 2, ch02 §2.8 step 4, and the Quick Start's Tap Technique (all three editions). The normal taps are on the top (a tap there excites the back's resonances too): the manual's "bouncy-ball strike on the back" is gone, and tapping the back is not covered. |
| L4 | Gore taps all over the lower bout and around the bridge because his analyzer averages 10 taps — with averaging, vary the location | §10.6 *Multi-Tap Averaging Strategy*, or ch03's multi-tap section | **decided** (owner, 2026-10-27): §10.6 recommends 3 taps for a guitar body — the top near the bridge, then each bridge wing — and says some luthiers take up to 10, the extra ones elsewhere on the top; ch03 §3.5 step 3 says the same. |
| L5 | The luthier taps the bridge wings; bass side or treble side, behind the bridge, or on the saddle usually make no difference | §10.1 (with L3) | **decided** (owner, 2026-10-27): in §10.1 with L3. |
