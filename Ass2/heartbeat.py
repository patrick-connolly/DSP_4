"""Task 5: find the R peaks in our ECG with a matched filter and plot the momentary heart rate.

Run with: python3 heartbeat.py
"""
import numpy as np
import matplotlib.pyplot as plt
from ecg_plot import MINE, ZABI, BASELINE, MAINS, load_ecg, save
from fir_design import design_fir
from fir_filter import FIRfilter


def prefilter(x, h):
    # remove DC, baseline wander and mains first, one sample at a time
    fir = FIRfilter(h)
    return np.array([fir.dofilter(v) for v in x])


fs, x = load_ecg(MINE)
fs_zabi, x_zabi = load_ecg(ZABI)
assert fs == fs_zabi, "template and ECG need the same sampling rate"
h = design_fir(fs, [BASELINE, MAINS])
M = len(h)
y = prefilter(x, h)

# template: one PQRST from Zabi's filtered ECG
y_zabi = prefilter(x_zabi, h)
r = M + fs + np.argmax(np.abs(y_zabi[M + fs:M + 4 * fs]))
template = y_zabi[r - int(0.3 * fs):r + int(0.4 * fs)]
template = template - np.mean(template)

# matched filter = FIR whose coefficients are the time reversed template, run on our filtered ECG.
# squaring makes the peaks stand out more and doesn't care about the sign
matched = FIRfilter(template[::-1])
m = np.array([matched.dofilter(v) for v in y]) ** 2

skip = M + len(template)  # both delay lines filling up
threshold = 0.3 * np.max(m[skip:])
crossings = np.flatnonzero((m[1:] > threshold) & (m[:-1] <= threshold)) + 1  # upward crossings
crossings = crossings[crossings > skip]

# heuristic: the heart can't go above 200 bpm, so a crossing within 60/200 s of the last beat is
# noise. dropping the detection (not just the rate) keeps the interval to the next real beat right
beats = [crossings[0]]
for n in crossings[1:]:
    if n - beats[-1] > 60 / 200 * fs:
        beats.append(n)
beats = np.array(beats)
print(f"Task 5: {len(crossings)} detections, {len(crossings) - len(beats)} rejected")


def heart_rate(b):
    return b[1:] / fs, 60 / (np.diff(b) / fs)  # bpm at the time of each beat


t = np.arange(len(y)) / fs
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 9))
ax1.plot(np.arange(len(template)) / fs, template)
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("ECG (mV)")
ax1.set_title("Template (Zabi's heartbeat)")
show = slice(skip, skip + 10 * fs)
ax2.plot(t[show], m[show])
ax2.axhline(threshold, color="r", linestyle="--", label="Threshold")
b = beats[beats < skip + 10 * fs]
ax2.plot(t[b], m[b], "rx", label="Detected beat")
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Matched filter output$^2$")
ax2.set_title("R-peak detection")
ax2.legend(loc="upper right")
ax3.plot(*heart_rate(crossings), "x", color="grey", label="Before heuristic")
ax3.plot(*heart_rate(beats), label="After heuristic")
ax3.set_xlabel("Time (s)")
ax3.set_ylabel("Heart rate (bpm)")
ax3.set_title("Momentary heart rate")
ax3.legend(loc="upper right")
fig.tight_layout()
save(fig, "heartbeat.pdf")
plt.show()
