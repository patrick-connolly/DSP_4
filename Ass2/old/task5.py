import os
import numpy as np
import matplotlib.pyplot as plt
from ecg import MINE, PARTNER, BASELINE, MAINS, load_ecg
from fir import design_fir, FIRfilter

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the data wherever the script is run from

fs, x = load_ecg(MINE)
fs_p, xp = load_ecg(PARTNER)
assert fs == fs_p, "template and ECG need the same sampling rate"
h = design_fir(fs, [BASELINE] + MAINS)
M = len(h)

# template: one PQRST from the partner's filtered ECG
fir = FIRfilter(h)
yp = np.array([fir.dofilter(v) for v in xp])
r = M + fs + np.argmax(np.abs(yp[M + fs:M + 4 * fs]))
template = yp[r - int(0.3 * fs):r + int(0.4 * fs)]
template = template - np.mean(template)

# matched filter = FIR whose coefficients are the time reversed template.
# squaring makes the peaks stand out more and doesn't care about the sign
fir = FIRfilter(h)
matched = FIRfilter(template[::-1])
m = np.array([matched.dofilter(fir.dofilter(v)) for v in x]) ** 2

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
print(f"{len(crossings)} detections, {len(crossings) - len(beats)} rejected")


def heart_rate(b):
    return b[1:] / fs, 60 / (np.diff(b) / fs)  # bpm at the time of each beat

t = np.arange(len(x)) / fs
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 9))
ax1.plot(np.arange(len(template)) / fs, template)
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("ECG (V)")
ax1.set_title("Template (partner's heartbeat)")
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
fig.savefig("task5.pdf")

plt.show()
