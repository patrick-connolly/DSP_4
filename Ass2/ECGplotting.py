import os
import numpy as np
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the tsv files wherever the script is run from

filenames = ["zabiecg1.tsv", "patrickecg1.tsv"]

# noise picked out of the spectra below, these ranges go into the FIR design in task 2
# no 100 Hz band: at fs = 250 Hz all mains harmonics alias onto 0, 50 or 100 Hz and there is no peak at 100 Hz
noise = [(0, 0.5), (48, 52)]

for filename in filenames:
    data = np.loadtxt(filename)
    fs = round(1 / (data[1, 0] - data[0, 0]))  # sampling rate from the time column (250 Hz)
    x = data[:, 8] * 1000  # column 8 is the ECG, V -> mV
    N = len(x)
    t = np.arange(N) / fs

    # one sided amplitude spectrum in uV, DC kept because it is part of the noise
    X = 2 * np.abs(np.fft.fft(x)[:N // 2]) / N * 1000
    X[0] /= 2  # DC has no negative frequency twin
    f = np.arange(N // 2) * fs / N

    # heart rate fundamental = strongest peak between 40 and 120 bpm
    hr = f[np.argmax(X * ((f > 0.67) & (f < 2)))]

    # one heartbeat: R peak between 5 and 6 s, then 0.35 s before to 0.55 s after it
    r = 5 * fs + np.argmax(x[5 * fs:6 * fs])
    beat = slice(r - int(0.35 * fs), r + int(0.55 * fs))

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 7))
    fig.suptitle(f"{filename} (raw, fs = {fs} Hz)")

    ax1.plot(t, x, lw=0.5)
    ax1.set_title("Whole recording")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("ECG (mV)")

    ax2.plot(t[beat], x[beat])
    ax2.set_title("One heartbeat")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("ECG (mV)")

    # full spectrum, scaled to the biggest peak above the wander band so DC and wander go off scale
    ax3.plot(f, X, lw=0.5)
    ax3.set_xlim(0, fs / 2)
    ax3.set_ylim(0, 1.2 * X[f > noise[0][1]].max())
    ax3.axvspan(0.5, 40, color="g", alpha=0.15, label="ECG")
    ax3.axvspan(*noise[0], color="r", alpha=0.3, label="Noise to remove")
    ax3.axvspan(*noise[1], color="r", alpha=0.3)
    ax3.axvline(100, color="k", ls=":")
    ax3.text(101, 0.95 * ax3.get_ylim()[1], "no 100 Hz\nharmonic", va="top")
    ax3.set_title("Spectrum")
    ax3.set_xlabel("Frequency (Hz)")
    ax3.set_ylabel("Amplitude (µV)")
    ax3.legend(loc="center", bbox_to_anchor=(0.6, 0.6))  # empty gap between 50 and 100 Hz

    # zoom on the low end to show where the wander stops and the heartbeat starts
    ax4.plot(f, X)
    ax4.set_xlim(0, 5)
    ax4.set_ylim(0, 1.3 * X[(f > noise[0][1]) & (f < 5)].max())
    ax4.axvspan(*noise[0], color="r", alpha=0.3, label="Noise: DC + baseline wander")
    ax4.vlines(hr * np.arange(1, 5), *ax4.get_ylim(), colors="k", linestyles="--",
               label=f"Heart rate {hr * 60:.0f} bpm + harmonics")
    ax4.set_title("Spectrum 0-5 Hz")
    ax4.set_xlabel("Frequency (Hz)")
    ax4.set_ylabel("Amplitude (µV)")
    ax4.legend(loc="upper right")

    for ax in (ax1, ax2, ax3, ax4):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(filename.replace(".tsv", "_task1.pdf"))

plt.show()
