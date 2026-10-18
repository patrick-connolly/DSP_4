# How the Assignment 1 code works

Study notes for `task1.py`, `task2.py` and `task3.py`. Read them alongside the code.

## Ideas used in every script

### Loading the audio
The same four lines appear in all three scripts:
```python
fs, x = wavfile.read(filename)   # fs = 44100 samples per second, x = int16 array of shape (N, 2)
x = x[:, 0]                      # both stereo channels are identical, so keep one
x = x / np.max(np.abs(x))        # normalise so the loudest sample is ±1
x = np.trim_zeros(x, "b")        # drop the zeros GarageBand padded on the end ("b" = back)
```
The files end with 0.54 s (5cm) and 0.38 s (1m) of digital silence. Without trimming, the time plot shows a flat line that was never part of the recording.

`os.chdir(os.path.dirname(os.path.abspath(__file__)))` moves into the script's own folder. That way `"Zabi_5cm.wav"` is found from whatever folder the marker runs the script in, without any absolute path in the code.

### FFT bins and frequencies
`np.fft.fft(x)` returns N complex numbers, one per bin. Bin k is the frequency k·fs/N. `fftfreq` is banned, so the frequency axis is built by hand:
```python
f = np.arange(N) * fs / N
```
Bins are fs/N ≈ 0.4 Hz apart. That is fine enough to separate vowel fundamentals only a few Hz apart.

For a real signal, the second half of the FFT mirrors the first: bin N−k is the complex conjugate of bin k, and represents the "negative frequency" −k·fs/N. Two consequences:
- **Plotting** needs only bins 1 to N/2. Bin 0 is DC (0 Hz), which can't go on a log axis.
- **Filtering** must give bin k and bin N−k the same gain. Otherwise the IFFT produces a complex signal.

Tasks 2 and 3 handle the second point with one line:
```python
f = np.minimum(f, fs - f)   # bin N-k now has the same frequency as bin k
```
After this, any gain defined as a function of `f` automatically treats each mirrored pair the same. The IFFT then comes back real: the imaginary part is only about 1e-16 of rounding error, which `np.real` drops.

### Decibels
`20 * np.log10(|X| / ref)` converts to dB. It's 20 because |X| is an amplitude (10 is for power). Dividing by `ref` makes the reference 0 dB. Useful values:
- +6 dB = ×2 amplitude
- +3 dB ≈ ×1.4
- −20 dB = ×0.1

Tasks 2 and 3 add `+ 1e-12` inside the log. Bins that a cut set to exactly 0 would otherwise give log10(0) = −∞.

### `ramp()`: the filter building block (tasks 2 and 3)
```python
def ramp(f0, f1):
    return np.clip((f - f0) / (f1 - f0), 0, 1)
```
The gain is 0 below f0, rises in a straight line to 1 at f1, and stays at 1 above. Every filter is built from it:
- **Highpass:** `ramp(60, 80)`
- **Lowpass:** `1 - ramp(20000, 20500)`
- **Bandpass:** `ramp(4000, 5000) * (1 - ramp(10000, 12000))`
- **Boost:** `1 + 0.3 * bandpass` gives ×1.3 inside the band and ×1 elsewhere

Filtering is then: multiply the FFT by the gain, and IFFT back.
```python
y = np.real(np.fft.ifft(np.fft.fft(x) * gain))
```
**Why a slope instead of a hard edge:**
- Multiplying the spectrum by a gain is the same as convolving the signal with the gain's IFFT, which is the filter's impulse response.
- A sudden step in the gain gives an impulse response that dies away very slowly, and you hear that as ringing.
- A slope makes it die away much faster. The ramped 2–5 kHz boost has about 35 dB less ringing beyond ±10 ms than the hard-edged one.
- That's why the original hard-edged boost rang and the current one doesn't.

## Task 1: plots and markers (`task1.py`)

1. `marks` holds everything chosen by eye, per file: vowel fundamentals, consonant range and noise regions. The brief bans automatic detection, so these values are typed in.
2. The script loops over both files. It loads each one and makes the time axis `t = np.arange(N) / fs`.
3. It computes the spectrum from the first half only, skipping DC:
   ```python
   X = np.abs(np.fft.fft(x)[1:N // 2])
   f = np.arange(1, N // 2) * fs / N
   ```
   `XdB` is relative to the strongest bin.
4. **Top plot:** normalised amplitude against time, on linear axes as the brief asks.
5. **Bottom plot:** dB against frequency, both axes log, from 20 Hz to fs/2 = 22.05 kHz. That top limit is the Nyquist frequency, the highest a 44.1 kHz recording can hold.
6. `vlines` draws the vowel markers. `axvspan` shades the consonant band (green) and noise bands (grey).

**Why these markers:**
- **Vowel fundamentals (88.7–122.5 Hz at 5cm, 89.2–114 Hz at 1m).** A male speaking voice's fundamental is around 85–155 Hz, and vowels are voiced, so each one shows up as a strong peak there. Each vowel is spoken at a slightly different pitch, which gives separate peaks. These are the first strong peaks above the noise region. The peaks at 2×, 3× and so on are their harmonics.
- **Consonants (3–20 kHz).** Sounds like s, sh, f and t are noisy bursts of air, with their energy high up where vowel energy has faded out.
  - The range is the same at both distances, because it's the same speaker saying the same sentence.
  - It runs up to 20 kHz because the hump at 17–20 kHz is far above the level in the silent parts of the recording, so it's speech.
- **Noise (20–80 Hz and 20.5–22.05 kHz).**
  - Below 80 Hz is under the lowest vowel fundamental, so it can't be voice: it's rumble, plus pops in the 5cm recording.
  - Above 20.5 kHz is past where the speech ends and beyond human hearing. The recorder's anti-aliasing filter rolls off there.

## Task 2: enhancement (`task2.py`)

For each file: FFT → build one gain curve `G` → `Y = X * G` → IFFT → normalise → save `_enhanced.wav`.

`G` is several factors multiplied together:

| Change | Code | Applied to | Why |
|---|---|---|---|
| Cut below 80 Hz | `ramp(60, 80)` | both | rumble, plus pops at 5cm |
| Cut above 20.5 kHz | `1 - ramp(20000, 20500)` | both | the noise region from task 1 |
| ×1.3 (+2.3 dB) at 2–5 kHz | `1 + 0.3 * ramp(1500, 2000) * (1 - ramp(5000, 6000))` | both | presence: where consonant detail sits and hearing is most sensitive |
| ×1.4 (+3 dB) below 120 Hz | `1 + 0.4 * (1 - ramp(120, 150))` | 1m only | puts back bass lost with distance |

**Why the two recordings are treated differently:**
- **5cm:**
  - Close up, a directional mic boosts the bass (the proximity effect), so there's no need to add more.
  - The risk at this distance is pops: p and b sounds blast air into the mic and cause low-frequency thumps.
  - Cutting below 80 Hz removes the pops without touching the voice, since the lowest fundamental is about 89 Hz.
- **1m:**
  - Bass falls off with distance.
  - Room noise is much louder relative to the voice: the silent parts are only about 11 dB below the speech, against about 27 dB at 5cm.
  - That noise is low-frequency rumble, mostly below 200 Hz, so it overlaps the voice and only the part below 80 Hz can be cut.
  - The bass boost stops at 120 Hz. Below that the vowel fundamentals (89–114 Hz) are strongest compared with the noise. Boosting 120–200 Hz would mostly boost noise.

**Details worth knowing:**
- Below 80 Hz the bass factor is ×1.4 too, but the cut has already made the gain about 0 there. So the boost only really acts on 80–150 Hz.
- `ramp` is defined above the loop but uses `f`, which is only set inside the loop. Python looks up `f` at the moment `ramp` is called, so it always uses the current file's frequency axis.
- The output is saved as a float32 WAV, so values stay within ±1 and are never rounded to integers.
- In the plot, both curves are divided by the original's peak (the same reference), so the gap between them is the real change. Grey means removed, green means boosted.

## Task 3: aural exciter (`task3.py`)

This follows the Aphex block diagram. The dry voice is summed with two side paths:
- **Sidechain:** highpass → harmonics generator → mix
- **Big bottom:** lowpass → dynamics → mix

### Steps
1. **Clean the input.** Load the 5cm file and apply the same pop and noise cuts as task 2. Task 2's clarity boost is left out, because that's the exciter's job here. From now on `x` is the cleaned voice.
2. **Big bottom** (computed once, because it doesn't depend on the version):
   ```python
   low = np.real(np.fft.ifft(X * (1 - ramp(150, 190))))   # lowpass
   low = low / np.max(np.abs(low))
   bass = np.real(np.fft.ifft(np.fft.fft(np.tanh(3 * low)) * ramp(60, 80)))
   ```
   - tanh is almost linear for small inputs and flattens towards ±1 for big ones (tanh(3) ≈ 0.995).
   - So loud bass is squashed more than quiet bass. Like a compressor, it evens the bass out.
   - tanh also creates new frequencies, some of them below 80 Hz, so the pop cut `ramp(60, 80)` is applied again afterwards.
3. **`exciter(hp, band, drive, mix, bass_mix)`** returns only the part to add to the voice:
   - `side` is the voice through the highpass `hp`, normalised to a peak of 1. This makes `drive` do the same thing whatever the recording level.
   - `tanh(drive * side)` is the nonlinearity. tanh is an odd function (tanh(−x) = −tanh(x)), so a single sine wave only gets odd harmonics (3f, 5f, …).
   - A real voice contains many frequencies at once, so tanh also creates intermodulation products: sums and differences such as 2f₁ − f₂. Those can land anywhere, including at very low frequencies.
   - Multiplying by `band` in the FFT keeps only the harmonics in the chosen band.
   - The result is normalised to a peak of 1 and multiplied by `mix`. So `mix` is the peak level of what gets added, relative to the voice (whose peak is about 1).
   - Finally `bass_mix * bass` is added on.
4. **Sum:** `y = x + added`, the dry voice plus the effect (the "SUM" block in the diagram). It's normalised only when saved, so the WAV doesn't clip.

### v1 → v2

| | v1: `exciter(ramp(600, 800), 1, 5, 0.3, 0)` | v2: `exciter(ramp(2000, 3000), band2, 5, 0.15, 0.1)` |
|---|---|---|
| Into the tanh | everything above 800 Hz | everything above 3 kHz |
| Kept after the tanh | everything | 4–12 kHz only |
| Mix | 0.3 | 0.15 |
| Bass | none | 0.1 |
| Result | +7.5 dB at 12–20 kHz (harsh); adds energy below 80 Hz | +2.8 dB at 4–10 kHz; 12–20 kHz unchanged; nothing below 60 Hz; level only +0.9 dB |

- **v1's problems:** everything above 800 Hz got louder. Nothing filtered the tanh output, so intermodulation products put energy back below 80 Hz, where the pops had been removed. Figure 2 shows both.
- **v2's fix:** v2 raises the highpass and keeps only 4–12 kHz, the region around 6 kHz where the ear is most sensitive. It halves the mix and adds a little big-bottom bass.

### What v2 really does
- `side` is normalised to its peak, but speech is quieter than its peak most of the time.
- So `5 * side` is usually below 1, where tanh is almost a straight line. Only about 1% of samples get bent in v2, and 3% in v1. (These were measured separately; the code doesn't compute them.)
- That means most of what v2 adds is the original 4–12 kHz voice turned up, with only a little real harmonic content.
- A version with a narrow 1.5–3 kHz sidechain and drive 20 made pure harmonics, but it sounded squawky, so v2 was kept.

### Figures
- **Figures 1 and 2:** what v1 and v2 each add (the `added` signal), drawn over the input in grey so you can see how loud it is. 0 dB is the input's peak.
  - `plot_added()` draws both, so they share a layout.
  - Each figure then gets its own arrows pointing at what matters: v1's harsh top end and low-end leak, and v2's bands.
- **Figure 3:** how much each version changes the voice's level, in dB, band by band.
  - The raw spectra are too spiky to compare, so `band_power()` averages the power over 40 bands. The bands are equally spaced on the log axis from 80 Hz to 20 kHz (`np.geomspace`).
  - The change in each band is `10·log10(output power / input power)`. It's 10 rather than 20 because these are powers.
  - The plot starts at 80 Hz because the input is cut below that, and a ratio against near-zero power means nothing.
  - The averaging only changes how the plot looks. The audio is untouched, so it isn't filtering.

## Likely interview questions

| Question | Short answer |
|---|---|
| How did you filter without `fftfreq` or scipy filters? | The frequency of bin k is k·fs/N, built by hand. Every filter is a gain multiplied onto the FFT bins, followed by an IFFT. |
| Why `np.minimum(f, fs - f)`? | Bins k and N−k are conjugate mirror images. Giving both the same gain keeps the IFFT output real. |
| Why `np.real` after the IFFT? | It removes about 1e-16 of rounding error in the imaginary part. |
| Why skip bin 0 in the plots? | It's 0 Hz (DC), which can't go on a log axis. |
| Why 20·log10 and not 10·log10? | FFT magnitudes are amplitudes; 10·log10 is for power. |
| Why ramps instead of hard cuts? | A hard edge in frequency rings for a long time in the time domain. A slope stops the ringing. |
| Why cut at 80 Hz and not higher? | The lowest vowel fundamental is about 89 Hz, so 80 Hz removes rumble and pops without touching the voice. |
| Why no bass boost on the 5cm recording? | The proximity effect already boosts bass that close to the mic. |
| Why does the 1m bass boost stop at 120 Hz? | The fundamentals are at 89–114 Hz. Above 120 Hz the room noise is worse compared with the voice. |
| The 2–5 kHz boost used to ring. Why is it fine now? | Its edges are ramped instead of hard. |
| Why normalise `side` before the tanh? | So `drive` means the same thing regardless of the recording level. |
| Why does tanh create harmonics, and why odd ones? | A nonlinearity changes a sine wave's shape, which adds harmonics. tanh is odd-symmetric, so a single tone only gets odd harmonics. A real voice also gets intermodulation products. |
| Where did v1's energy below 80 Hz come from? | Difference-frequency intermodulation from the tanh, with nothing filtering it afterwards. |
| What does `mix` control? | The peak level of the added signal relative to the voice. |
| Why does v2 add bass if task 2 says the 5cm has plenty? | The big bottom acts as a compressor: tanh squashes loud bass more than quiet bass, so it evens the bass out rather than simply boosting it. It came from trying the big-bottom side of the Aphex diagram. |
| Figure 3 is smoothed. Isn't that filtering? | No. It averages the plotted power in bands, like a spectrum analyser does. The audio itself is never changed by it. |
| Why trim the trailing zeros? | They're padding GarageBand added, not part of the recording. |
