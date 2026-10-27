# Tips & Technique: one set of advice, and a luthier's answers

**Issue:** [#48](https://github.com/dwsdolce/guitar-tap-project/issues/48)

Status: **OPEN — the material captured; each item's place to be decided with the owner, one at a time.**

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

Each item: what it is, where it could go, and — once agreed — the decision and when it was done.

| # | Item | Proposed place | Status |
|---|---|---|---|
| T1 | The tap's contact time: the Quick Start says a slow, pressing contact gives a **cleaner** fundamental; the manual (§10.1) says a long slow push **muddies** the spectrum | the Quick Start, to agree with §10.1 (short, crisp contact) | open |
| T2 | Where to tap a guitar: the Quick Start says "near the bridge area"; §10.1 lists the bridge centre, each wing, below the bridge, each side | with L3 and L5 | open |
| T3 | Topics in one only: the Quick Start's *Air Mode for Setup* (a palm clapped over the sound hole); the manual's §10.3 *Background Noise*, §10.4 *Decoupling the Top from the Air Mode*, §10.6 *Multi-Tap Averaging Strategy* | to decide: add to the other, or leave | open |
| L1 | Strings on or off, and string tension, change the frequencies little; mass does (bridge pins, anything attached) — so measure the same configuration each time | where the guitar is set up for a measurement (ch03, or ch02's *Your First Tap*), or ch10 | open |
| L2 | Foam string dampers: between the strings and the fingerboard, never over the sound hole — it changes the air leaving the sound hole, and so the air (Helmholtz) frequency | with L1; and a cross-reference from §10.4, which blocks the sound hole on purpose | open |
| L3 | Where to tap: around the monopole area; right on the centreline affects the dipole (the centreline is its node line) | ch03's walkthrough and ch02's *Your First Tap*, and §10.1 | open |
| L4 | Gore taps all over the lower bout and around the bridge because his analyzer averages 10 taps — with averaging, vary the location | §10.6 *Multi-Tap Averaging Strategy*, or ch03's multi-tap section | open |
| L5 | The luthier taps the bridge wings; bass side or treble side, behind the bridge, or on the saddle usually make no difference | §10.1 (with L3) | open |
