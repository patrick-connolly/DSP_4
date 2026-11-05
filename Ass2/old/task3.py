import os
import numpy as np
import matplotlib.pyplot as plt
from ecg import MINE, BASELINE, MAINS, load_ecg, spectrum
from fir import design_fir, FIRfilter

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the data wherever the script is run from

fs, x = load_ecg(MINE)
h = design_fir(fs, [BASELINE] + MAINS)
M = len(h)
delay = (M - 1) // 2
print(f"fs = {fs} Hz, {M} taps, delay {delay / fs:.2f} s")

# simulate realtime, one sample in one sample out
fir = FIRfilter(h)
y = np.array([fir.dofilter(v) for v in x])
t = np.arange(len(x)) / fs

# filter design: impulse response and frequency response (zero padded FFT of h)
Nf = 16 * M
Hf = 20 * np.log10(np.abs(np.fft.fft(h, Nf)[:Nf // 2]) + 1e-12)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
ax1.plot(np.arange(M) / fs, h)
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("h(n)")
ax1.set_title(f"Impulse response ({M} taps)")
ax2.plot(np.arange(Nf // 2) * fs / Nf, Hf)
ax2.set_xlim(0, fs / 2)
ax2.set_ylim(-100, 10)
ax2.set_xlabel("Frequency (Hz)")
ax2.set_ylabel("Gain (dB)")
ax2.set_title("Frequency response")
fig.tight_layout()
fig.savefig("task3_filter.pdf")

# whole recording before and after, skipping the first M samples while the delay line fills
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 9))
ax1.plot(t, x)
ax1.set_title("Raw ECG")
ax2.plot(t[M:], y[M:])
ax2.set_title("FIR filtered ECG")
for ax in (ax1, ax2):
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("ECG (V)")
for s, label in ((x, "Raw"), (y[M:], "Filtered")):
    ax3.plot(*spectrum(s, fs), label=label)
ax3.set_xlim(0, fs / 2)
ax3.set_xlabel("Frequency (Hz)")
ax3.set_ylabel("Magnitude (dB)")
ax3.set_title("Spectrum")
ax3.legend()
fig.tight_layout()
fig.savefig("task3_ecg.pdf")

# one heartbeat, filtered output moved back by the filter delay so it lines up with the raw
r = M + fs + np.argmax(np.abs(y[M + fs:M + 4 * fs]))  # an R peak in the filtered signal
beat = np.arange(r - int(0.4 * fs), r + int(0.6 * fs))
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
ax1.plot(t[beat - delay], x[beat - delay])
ax1.set_title("Raw ECG, one heartbeat")
ax2.plot(t[beat - delay], y[beat])
ax2.set_title("FIR filtered ECG, one heartbeat (delay removed)")
ax2.set_xlabel("Time (s)")
for ax in (ax1, ax2):
    ax.set_ylabel("ECG (V)")
fig.tight_layout()
fig.savefig("task3_beat.pdf")

plt.show()
