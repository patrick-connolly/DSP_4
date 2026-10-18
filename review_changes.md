# Assignment 1 – review changes (18 Oct)

All three scripts run headless with no errors or warnings, including when run from a different folder. Nothing is committed yet.

## What changed

### task1.py
- **1m consonant range now starts at 3 kHz, not 4.2 kHz.** Same speaker and sentence, so the consonants sit in the same range at both distances. The 5cm range was already 3 kHz.
- **5cm vowel marker 88.2 → 88.7 Hz.** 88.2 sat on the rising edge, 4 dB below the actual peak.
- Added `os.chdir(...)` so the WAVs are found wherever the script is run from (also in tasks 2 and 3).

### task2.py
- **All gain changes use `ramp()` from task 3** instead of hard steps. Hard edges were what made the voice ring. Ramped edges leave about 35 dB less ringing beyond ±10 ms (−59 dB vs −25 dB).
- **2–5 kHz clarity boost restored** (×1.3, about +2.3 dB, with ramped edges). Without it, the 5cm file got no enhancement beyond cuts.
- **1m bass boost changed from ×2 on 100–300 Hz to ×1.4 (+3 dB) below 120 Hz,** easing back to ×1 by 150 Hz.
  - The old boost missed two of the four vowel fundamentals (89.2 and 98 Hz).
  - It also amplified the room noise: the speech-to-silence ratio fell from 11.3 to 10.3 dB.
  - The noise is 31% at 80–120 Hz and 30% at 120–200 Hz, but the voice-to-noise ratio is 21 dB at 80–120 Hz versus only 15 dB at 120–200 Hz. Boosting just the fundamentals helps the voice without worsening the noise.
- The cuts below 80 Hz and above 20.5 kHz now use the same ramps as task 3: 60→80 Hz and 20→20.5 kHz.
- The plot shading now matches what the code does. Files are processed 5cm first, as in task 1.
- Removed the stale "x1.6 is about +4 dB" comment and the "#patrick review" note.

### task3.py
- **Pre-processing now matches task 2:** the same 60→80 Hz cut plus the 20.5 kHz noise cut. The 2–5 kHz boost is deliberately left out, because clarity is the exciter's job here.
- **v1 and v2 settings are unchanged.** I tried a band-limited redesign of v2 (only 1.5–3 kHz into the tanh, drive 20). It measured as pure harmonics, but by ear it had a squawking noise, so it was dropped and the original v2 kept.
- **The pop cut is re-applied after the bass tanh.** The tanh was putting energy back below 80 Hz, so v2 didn't actually fix what its own comment says it fixes. Now it adds nothing below 60 Hz, and the output is within −45 dB of the previous v2, so it sounds the same.
- The bass path is worked out once instead of on every `exciter()` call.
- **Figures simplified to three:**
  - one per version showing only what it adds, with arrows pointing out the key effects;
  - one comparing the dB change per frequency band for v1 and v2.
  - The cluttered "output spectra" figure is gone. The harmonics band is shaded 4–12 kHz to match `band2`.
- The v2 comment now says why the bass was added: "to try the big bottom side of the aphex diagram". That was my guess, so check it.
- Output file names are unchanged: `Zabi_5cm_exciter_v1_initial.wav` and `Zabi_5cm_exciter_v2_final.wav`.

### Deleted
- `Zabi_5cm.pdf` and `Zabi_1m.pdf`. They were out of date: they showed consonants from 2 kHz, the old title, and included the trailing zeros.

### Regenerated
- All `_enhanced` and `_exciter_` WAVs, from the new code.

## Numbers for the report

| | Speech-to-silence (original → enhanced) |
|---|---|
| 5cm, task 2 | 27.3 → 28.1 dB |
| 1m, task 2 | 11.3 → 11.4 dB (the old ×2 boost gave 10.3 dB) |

| Exciter | 4–10 kHz | 12–20 kHz | 80–190 Hz | Added below 60 Hz | RMS change | Share of added signal that is new harmonics |
|---|---|---|---|---|---|---|
| v1 | +6.7 dB | +7.5 dB | 0 | −41 dB | +2.1 dB | 11% (tanh bends 3% of samples) |
| v2 | +2.8 dB | 0 | +2.2 dB | none | +0.9 dB | 7% (tanh bends 1% of samples) |

How the story reads:
- **v1:** brightened everything above 800 Hz (+7.5 dB at 12–20 kHz) and put energy back below 80 Hz, where the pops had been removed.
- **v2:** moved the highpass up to 3 kHz and kept only 4–12 kHz. That cured the harsh top end and the low-end leak, and it added a little compressed bass.
- **The rejected redesign (optional extra step):** a band-limited sidechain made v2's added content pure harmonics, but it sounded squawky, so it was dropped. Rejecting a version by ear is exactly the kind of iteration the brief asks you to show.

## Still to do

- [ ] **Listen to the two `_enhanced` files.** I can only measure, not hear. Task 2 changed (ramped edges, 2–5 kHz boost back, new 1m bass boost).
- [ ] **Report: be honest about what v2's 4–12 kHz lift is.** At drive 5 the tanh barely bends the signal (1% of samples), so most of the lift (93%) is the original 4–12 kHz voice turned up, with only a little new harmonic content. Say so, and say why you kept it (it sounded better than the pure-harmonic version).
- [ ] **Report: justify the v2 bass against task 2.** Task 2 says the 5cm has loads of bass, yet v2 adds +2.2 dB at 80–190 Hz. Frame it as compression evening out the bass (tanh squashes the loud bits), or set `bass_mix` to 0 if you can't hear a benefit.
- [ ] **Report: explain 6 vowel markers for 5cm vs 4 for 1m.** For example, separate takes, or some fundamentals not resolvable at 1m.
- [ ] **Report: explain the 1m noise.** It is broadband low-frequency room noise, 80% of it below 200 Hz. It overlaps the voice fundamentals, so it can't simply be cut, and that is why the bass boost stops at 120 Hz.
  - Careful with the claim that bass is lost with distance. In these recordings the 1m low end (80–300 Hz) is actually 1.5 dB above its mids, against −1.7 dB at 5cm, because room noise fills it.
- [ ] **Regenerate the report figures.** Uncomment the `savefig` lines in all three scripts. They save as PDF, which is vector as the brief requires.
- [ ] **Add the GenAI acknowledgement** (tool name, version, publisher, how it was used, what you did yourselves). Both of you should be able to explain the code in an interview.
- [ ] **Check the file names against the Moodle naming conventions.** The zip should hold just `task1-3.py`, `requirements.txt` and the WAVs: no `.venv`, `__pycache__`, `.vscode` or this file.
- [ ] **Commit and push** (not done).

## Checked and already fine
- Both recordings are 44.1 kHz, with identical channels and no clipping (peak 98.9% of full scale).
- No `fftfreq`, `scipy.signal` or FIR/IIR anywhere. The frequency axis is built by hand.
- Folding the frequency axis keeps the spectrum symmetric, so the IFFT output is real (leftover imaginary part about 3e-16).
- Every vowel marker sits on a real spectral peak.
- The 17–20 kHz hump is speech, 25–40 dB above the silent sections, so "consonants up to 20 kHz" holds.
- Task 1's noise regions match the cuts in tasks 2 and 3.
- Axes, labels and limits match across all three tasks.
