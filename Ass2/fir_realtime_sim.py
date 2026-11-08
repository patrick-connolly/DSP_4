import numpy as np
import matplotlib.pyplot as plt
from ecg_plot import MINE, BASELINE, MAINS, load_ecg, save, spectrum, db
from fir_design import design_fir
from fir_filter import FIRfilter


def plot_design(fs, h):
    M = len(h)
    print(f"Task 2: fs = {fs} Hz, {M} taps, delay {(M - 1) / 2 / fs:.2f} s")

    # impulse response and frequency response
    Nf = 16 * M
    H = np.abs(np.fft.fft(h, Nf)[:Nf // 2])
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    ax1.plot(np.arange(M) / fs, h)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("h(n)")
    ax1.set_title(f"Impulse response ({M} taps)")
    ax2.plot(np.arange(Nf // 2) * fs / Nf, db(H))
    ax2.set_xlim(0, fs / 2)
    ax2.set_ylim(-100, 10)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Gain (dB)")
    ax2.set_title("Frequency response")
    fig.tight_layout()
    save(fig, "fir_design.pdf")


def plot_filtered(fs, x, y, M):
    delay = (M - 1) // 2
    t = np.arange(len(x)) / fs

    # whole recording before and after #skipping the first M samples while the delay line fills
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 9))
    ax1.plot(t, x)
    ax1.set_title("Raw ECG")
    ax2.plot(t[M:], y[M:])
    ax2.set_title("FIR filtered ECG")
    for ax in (ax1, ax2):
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("ECG (mV)")
    for s, label in ((x - np.mean(x), "Raw"), (y[M:], "Filtered")):
        f, X = spectrum(s, fs)
        ax3.plot(f, db(X), label=label)
    ax3.set_xlim(0, fs / 2)
    ax3.set_xlabel("Frequency (Hz)")
    ax3.set_ylabel("Amplitude (dB re 1 mV)")
    ax3.set_title("Spectrum")
    ax3.legend()
    fig.tight_layout()
    save(fig, "fir_realtime_ecg.pdf")

    # one heartbeat
    r = M + fs + np.argmax(np.abs(y[M + fs:M + 4 * fs]))  # an R peak in the filtered signal
    beat = np.arange(r - int(0.4 * fs), r + int(0.6 * fs))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(t[beat - delay], x[beat - delay])
    ax1.set_title("Raw ECG, one heartbeat")
    ax2.plot(t[beat - delay], y[beat])
    ax2.set_title("FIR filtered ECG, one heartbeat (delay removed)")
    ax2.set_xlabel("Time (s)")
    for ax in (ax1, ax2):
        ax.set_ylabel("ECG (mV)")
    fig.tight_layout()
    save(fig, "fir_realtime_beat.pdf")


if __name__ == "__main__":
    fs, x = load_ecg(MINE)
    h = design_fir(fs, [BASELINE, MAINS])
    plot_design(fs, h)

    # ECG in one sampple at a time
    fir = FIRfilter(h)
    y = np.array([fir.dofilter(v) for v in x])
    plot_filtered(fs, x, y, len(h))
    plt.show()
