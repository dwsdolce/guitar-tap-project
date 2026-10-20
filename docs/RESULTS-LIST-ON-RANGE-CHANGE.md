# Zoom and pan slow with many peaks — the results list rebuilt on every range change

**Issue:** [#35](https://github.com/dwsdolce/guitar-tap-project/issues/35)

Status: **OPEN — Python measured and its cause found; the web to measure; nothing changed.**

With a low Peak Min, so that many peaks are listed, zooming and panning the chart is unusable in Python and slow on
the web. Swift stays smooth (owner, 2026-10-20).

## Python — measured

A guitar measurement (`dws-2024-umik-1-3-tap-swift-mac-1785359425.guitartap`) open in the real window, the chart's
frequency range moved 20–30 times, each step repainted (Python `26d0939`, macOS):

| What was switched off | Time per pan step |
|---|---|
| nothing | 146–168 ms |
| the mode lines and their chips | no better |
| the spectrum curve | no better |
| the results panel's refresh | 34 ms |

| Peak Min | Peaks listed | Time per pan step |
|---|---|---|
| −60 dB | 8 | 47 ms |
| −80 dB | 46 | 146 ms |
| −100 dB | 46 in view | 181 ms |

**Cause.** Each change of the chart's range (`_on_canvas_freq_range_changed` → `_refresh_results_peaks` →
`peak_card_widget.update_data_with_modes`) discards and rebuilds every peak card in the list (`_rebuild_cards`), with
about 20 `setStyleSheet` calls per card — and it runs twice per change (38 rebuilds for 19 steps). The cost grows with
the number of peaks listed. The same holds at every commit back to 2026-10-08; a low Peak Min is what makes it
unusable. Swift lists the same peaks on every range change but redraws only what changed.

## Web — to measure

Slower with many peaks, less than Python (owner). Not yet measured.

## Items

| # | Item | Status |
|---|---|---|
| 1 | Python: the list refreshed once per range change, and its cards updated in place by peak id — those that came into view added, those that left removed, a card's style set only when its state changes. Target: a pan step near the chart's own cost (≈ 35 ms) at −100 dB, measured the same way; a test that a range change does not rebuild the cards | open |
| 2 | The web: measure the same way, find the cause, then the same treatment | open |
