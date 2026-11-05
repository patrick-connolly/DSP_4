"""Task 5: find the R peaks in our ECG with a matched filter and plot the momentary heart rate.

Run with: python3 heartbeat.py
"""
import numpy as np
import matplotlib.pyplot as plt
from ecg_plot import MINE, ZABI, BASELINE, MAINS, load_ecg, save
from fir_design import design_fir
from fir_filter import FIRfilter


fs, x = load_ecg(MINE)
fs_zabi, x_zabi = load_ecg(ZABI)
assert fs == fs_zabi, "template and ECG need the same sampling rate"
h = design_fir(fs, [BASELINE, MAINS])
M = len(h)

# setup, done once before the realtime loop like designing the coefficients:
# the template is one PQRST from Zabi's filtered ECG
fir = FIRfilter(h)
y_zabi = np.array([fir.dofilter(v) for v in x_zabi])
r = M + fs + np.argmax(np.abs(y_zabi[M + fs:M + 4 * fs]))
template = y_zabi[r - int(0.3 * fs):r + int(0.4 * fs)]
template = template - np.mean(template)

# the threshold is fixed before any of our ECG arrives. When the template meets itself the matched
# filter gives sum(template^2), squared below. Our beats are a bit smaller than Zabi's and peak at
# about 0.45 of that, so 0.15 leaves a safe margin
threshold = 0.15 * np.sum(template ** 2) ** 2

# realtime: every sample goes through the bandstop, then the matched filter (time reversed template),
# then gets squared, which makes the peaks stand out and doesn't care about the sign.
# A beat is an upward crossing of the threshold. Nothing here looks ahead in the recording
fir = FIRfilter(h)
matched = FIRfilter(template[::-1])
skip = M + len(template)  # both delay lines filling up
min_gap = 60 / 200 * fs  # heuristic: the heart can't beat faster than 200 bpm
m = np.zeros(len(x))
beats, rejected = [], []
for n, v in enumerate(x):
    m[n] = matched.dofilter(fir.dofilter(v)) ** 2
    if n > skip and m[n] > threshold >= m[n - 1]:
        # a crossing too soon after the last beat is noise. dropping the detection (not just the
        # rate) keeps the interval to the next real beat right
        if beats and n - beats[-1] < min_gap:
            rejected.append(n)
        else:
            beats.append(n)
beats = np.array(beats)
detections = np.sort(beats.tolist() + rejected)
print(f"Task 5: {len(detections)} detections, {len(rejected)} rejected")


def heart_rate(b):
    return b[1:] / fs, 60 / (np.diff(b) / fs)  # bpm at the time of each beat


t = np.arange(len(x)) / fs
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
ax3.plot(*heart_rate(detections), "x", color="grey", label="Before heuristic")
ax3.plot(*heart_rate(beats), label="After heuristic")
ax3.set_xlabel("Time (s)")
ax3.set_ylabel("Heart rate (bpm)")
ax3.set_title("Momentary heart rate")
ax3.legend(loc="upper right")
fig.tight_layout()
save(fig, "heartbeat.pdf")
plt.show()
