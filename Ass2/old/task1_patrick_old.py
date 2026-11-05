import os
import numpy as np
import matplotlib.pyplot as plt
from ecg import MINE, BASELINE, MAINS, load_ecg, spectrum

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the data wherever the script is run from

fs, x = load_ecg(MINE)
t = np.arange(len(x)) / fs
f, X = spectrum(x, fs)

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 9))
ax1.plot(t, x)
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("ECG (V)")
ax1.set_title("Raw ECG")

# full spectrum and a zoom on the low end where baseline wander and the heartbeat sit
for ax, top in ((ax2, fs / 2), (ax3, 5)):
    ax.plot(f, X)
    ax.set_xlim(0, top)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Magnitude (dB)")
    ax.axvspan(*BASELINE, color="grey", alpha=0.4, label="Baseline wander")
    for lo, hi in MAINS:
        ax.axvspan(lo, hi, color="r", alpha=0.3, label="50 Hz + harmonics" if lo < 50 else None)
ax2.set_title("Spectrum")
ax3.set_title("Spectrum 0-5 Hz")
ax2.legend(loc="upper right")
fig.tight_layout()
fig.savefig("task1.pdf")

plt.show()
