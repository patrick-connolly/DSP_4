import os
import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))  #file finder
MINE = "ecg1.tsv"
ZABI = "ecg2.tsv"  # Zabi recording for matched filter template
ECG_COLUMN = 8  #ecg voltage 

# noise picked out forFIR
# no 100 Hz band: at fs = 250 Hz all mains harmonics alias onto 0, 50 or 100 Hz and there is no peak at 100 Hz
BASELINE = (0, 0.5)
MAINS = (48, 52)
MAINS_HZ = 50.13  # mains noise for the LMS noise reference


def load_ecg(filename):
    data = np.loadtxt(os.path.join(HERE, filename))
    fs = round(1 / (data[1, 0] - data[0, 0]))  # sampling rate from the time column (250 Hz)
    return fs, data[:, ECG_COLUMN] * 1000  #make mV


def save(fig, filename):
    fig.savefig(os.path.join(HERE, filename))


def spectrum(x, fs): # frequency axis
    N = len(x)
    X = 2 * np.abs(np.fft.fft(x)[:N // 2]) / N
    X[0] /= 2  # DC has no negative frequency twin
    return np.arange(N // 2) * fs / N, X


def db(X):
    return 20 * np.log10(X + 1e-12)


def plot_ecg(filename):
    fs, x = load_ecg(filename)
    t = np.arange(len(x)) / fs
    f, X = spectrum(x, fs)
    X = X * 1000  # makes uV

    # one heartbeat
    r = 5 * fs + np.argmax(x[5 * fs:6 * fs])
    beat = slice(r - int(0.35 * fs), r + int(0.55 * fs))

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 7))
    fig.suptitle(f"{filename} (raw, fs = {fs} Hz)")

    ax1.plot(t, x, lw=0.5)
    ax1.set_title("Whole recording")
    ax2.plot(t[beat], x[beat])
    ax2.set_title("One heartbeat")
    for ax in (ax1, ax2):
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("ECG (mV)")

    # full spectrum scaled to the biggest peak above the wander band
    ax3.plot(f, X, lw=0.5)
    ax3.set_xlim(0, fs / 2)
    ax3.set_ylim(0, 1.2 * X[f > BASELINE[1]].max())
    ax3.axvspan(0.5, 40, color="g", alpha=0.15, label="ECG")
    ax3.axvspan(*BASELINE, color="r", alpha=0.3, label="Noise to remove")
    ax3.axvspan(*MAINS, color="r", alpha=0.3)
    ax3.set_title("Spectrum")
    

    # zoom on the low shows wander stoping and the heartbeat starting
    ax4.plot(f, X)
    ax4.set_xlim(0, 5)
    ax4.set_ylim(0, 1.3 * X[(f > BASELINE[1]) & (f < 5)].max())
    ax4.axvspan(*BASELINE, color="r", alpha=0.3, label="Noise: DC + baseline wander")
    #heart rate wanders (58-75 bpm), so its peak is smeared over this range rather than one line
    ax4.axvspan(40 / 60, 120 / 60, color="g", alpha=0.15, label="Heart rate, 40-120 bpm")
    ax4.set_title("Spectrum 0-5 Hz")
    ax4.legend(loc="upper right")
    for ax in (ax3, ax4):
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Amplitude (µV)")

    for ax in (ax1, ax2, ax3, ax4):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    save(fig, filename.replace(".tsv", "_plot.pdf"))


if __name__ == "__main__":
    for filename in (ZABI, MINE):
        plot_ecg(filename)
    plt.show()
