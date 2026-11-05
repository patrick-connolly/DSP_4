"""Task 4: remove the mains with an adaptive LMS filter instead of the FIR bandstop, and compare.

Run with: python3 lms_filter.py
"""
import numpy as np
import matplotlib.pyplot as plt
from ecg_plot import MINE, BASELINE, MAINS, MAINS_HZ, load_ecg, save, spectrum, db
from fir_design import design_fir
from fir_filter import FIRfilter

fs, x = load_ecg(MINE)

# the fixed FIR from task 3, to compare against
bandstop = FIRfilter(design_fir(fs, [BASELINE, MAINS]))

# the LMS only gets a mains reference so baseline wander still needs the FIR highpass.
# it has the same number of taps as the bandstop (set by the baseline band) so the delays match
highpass = FIRfilter(design_fir(fs, [BASELINE]))
M = highpass.M

# noise reference: a sine at the measured mains frequency.
# one mains cycle of taps is enough to set the gain and phase of the mains sine
taps = fs // 50
lms = FIRfilter(np.zeros(taps))
# learning rate * taps * reference power (1/2) ~ 0.1: fast enough to follow the mains
# drifting, slow enough to leave the ECG alone (it goes unstable around 2)
learning_rate = 0.1 / (taps / 2)

# one sample at a time, like a realtime system would
y_fir = np.zeros(len(x))
y_lms = np.zeros(len(x))
for n, v in enumerate(x):
    y_fir[n] = bandstop.dofilter(v)
    ref = np.sin(2 * np.pi * MAINS_HZ * n / fs)
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
    ax.set_ylabel("ECG (mV)")
for s, label in ((y_fir[M:], "FIR bandstop"), (y_lms[M:], "LMS")):
    f, X = spectrum(s, fs)
    ax3.plot(f, db(X), label=label, alpha=0.7)
ax3.set_xlim(0, fs / 2)
ax3.set_xlabel("Frequency (Hz)")
ax3.set_ylabel("Amplitude (dB re 1 mV)")
ax3.set_title("Spectrum")
for ax in (ax1, ax2, ax3):
    ax.legend(loc="upper right")
fig.tight_layout()
save(fig, "lms_filter.pdf")
plt.show()
