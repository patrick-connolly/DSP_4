import os
import numpy as np
import matplotlib.pyplot as plt
from ecg import MINE, BASELINE, MAINS, load_ecg, spectrum
from fir import design_fir, FIRfilter

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the data wherever the script is run from

fs, x = load_ecg(MINE)

# the LMS only gets a mains reference so baseline wander still needs the FIR highpass.
# both FIRs have the same number of taps (set by the baseline band) so their delays match
highpass = FIRfilter(design_fir(fs, [BASELINE]))
bandstop = FIRfilter(design_fir(fs, [BASELINE] + MAINS))
M = len(highpass.h)

# noise reference: a sine at the measured mains frequency.
# one mains cycle of taps is enough to set the gain and phase of the mains sine
mains = 50.13  # measured mains peak in the task 1 spectrum, not exactly 50 Hz
harmonics = np.array([mains])  # no harmonics in the task 1 spectrum, so only the fundamental
taps = fs // 50
lms = FIRfilter(np.zeros(taps))

# learning rate * taps * reference power ~ 0.1: fast enough to follow the mains drifting off
# exactly 50 Hz, slow enough to leave the ECG alone (it goes unstable around 2)
learning_rate = 0.1 / (taps * len(harmonics) / 2)

y_fir = np.zeros(len(x))
y_lms = np.zeros(len(x))
for n, v in enumerate(x):
    ref = np.sum(np.sin(2 * np.pi * harmonics * n / fs))
    y_fir[n] = bandstop.dofilter(v)
    y_lms[n] = lms.doFilterAdaptive(highpass.dofilter(v), ref, learning_rate)

t = np.arange(len(x)) / fs
r = M + fs + np.argmax(np.abs(y_fir[M + fs:M + 4 * fs]))  # an R peak to zoom in on
beat = slice(r - int(0.4 * fs), r + int(0.6 * fs))

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 9))
ax1.plot(t[M:], y_fir[M:], label="FIR bandstop")
ax1.plot(t[M:], y_lms[M:], label="LMS", alpha=0.7)
ax1.set_title("Whole recording")
ax2.plot(t[beat], y_fir[beat], label="FIR bandstop")
ax2.plot(t[beat], y_lms[beat], label="LMS", alpha=0.7)
ax2.set_title("One heartbeat")
for ax in (ax1, ax2):
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("ECG (V)")
for s, label in ((y_fir[M:], "FIR bandstop"), (y_lms[M:], "LMS")):
    ax3.plot(*spectrum(s, fs), label=label, alpha=0.7)
ax3.set_xlim(0, fs / 2)
ax3.set_xlabel("Frequency (Hz)")
ax3.set_ylabel("Magnitude (dB)")
ax3.set_title("Spectrum")
for ax in (ax1, ax2, ax3):
    ax.legend(loc="upper right")
fig.tight_layout()
fig.savefig("task4.pdf")

plt.show()
