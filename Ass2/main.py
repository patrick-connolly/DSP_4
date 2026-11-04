"""DSP Assignment 2: FIR filtering and R-peak detection of our lab ECGs.

Run with: python3 main.py
Every figure is saved as a PDF next to this file and then shown.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from firdesign import design_fir
from firfilter import FIRfilter

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the data wherever the script is run from

MINE = "patrickecg1.tsv"
PARTNER = "zabiecg1.tsv"  # the other lab partner, gives the matched filter template
ECG_COLUMN = 8  # counting from 0, as told on moodle

# noise picked out of the task 1 spectra, these ranges go into the FIR design in task 2.
# no 100 Hz band: at fs = 250 Hz all mains harmonics alias onto 0, 50 or 100 Hz and there is no peak at 100 Hz
BASELINE = (0, 0.5)
MAINS = (48, 52)
MAINS_HZ = 50.13  # measured mains peak, the LMS noise reference in task 4


def load_ecg(filename):
    data = np.loadtxt(filename)
    fs = round(1 / (data[1, 0] - data[0, 0]))  # sampling rate from the time column (250 Hz)
    return fs, data[:, ECG_COLUMN] * 1000  # V -> mV


def spectrum(x, fs):
    # one sided amplitude spectrum, frequency axis built by hand since fftfreq isn't allowed
    N = len(x)
    X = 2 * np.abs(np.fft.fft(x)[:N // 2]) / N
    X[0] /= 2  # DC has no negative frequency twin
    return np.arange(N // 2) * fs / N, X


def db(X):
    return 20 * np.log10(X + 1e-12)


def realtime(fir, x):
    # feed the signal in one sample at a time, like a realtime system would
    return np.array([fir.dofilter(v) for v in x])


def task1():
    for filename in (PARTNER, MINE):
        fs, x = load_ecg(filename)
        t = np.arange(len(x)) / fs
        f, X = spectrum(x, fs)
        X = X * 1000  # mV -> uV, DC kept because it is part of the noise

        # heart rate fundamental = strongest peak between 40 and 120 bpm
        hr = f[np.argmax(X * ((f > 0.67) & (f < 2)))]

        # one heartbeat: R peak between 5 and 6 s, then 0.35 s before to 0.55 s after it
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

        # full spectrum, scaled to the biggest peak above the wander band so DC and wander go off scale
        ax3.plot(f, X, lw=0.5)
        ax3.set_xlim(0, fs / 2)
        ax3.set_ylim(0, 1.2 * X[f > BASELINE[1]].max())
        ax3.axvspan(0.5, 40, color="g", alpha=0.15, label="ECG")
        ax3.axvspan(*BASELINE, color="r", alpha=0.3, label="Noise to remove")
        ax3.axvspan(*MAINS, color="r", alpha=0.3)
        ax3.axvline(100, color="k", ls=":")
        ax3.text(101, 0.95 * ax3.get_ylim()[1], "no 100 Hz\nharmonic", va="top")
        ax3.set_title("Spectrum")
        ax3.legend(loc="center", bbox_to_anchor=(0.6, 0.6))  # empty gap between 50 and 100 Hz

        # zoom on the low end to show where the wander stops and the heartbeat starts
        ax4.plot(f, X)
        ax4.set_xlim(0, 5)
        ax4.set_ylim(0, 1.3 * X[(f > BASELINE[1]) & (f < 5)].max())
        ax4.axvspan(*BASELINE, color="r", alpha=0.3, label="Noise: DC + baseline wander")
        ax4.vlines(hr * np.arange(1, 5), *ax4.get_ylim(), colors="k", linestyles="--",
                   label=f"Heart rate {hr * 60:.0f} bpm + harmonics")
        ax4.set_title("Spectrum 0-5 Hz")
        ax4.legend(loc="upper right")
        for ax in (ax3, ax4):
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Amplitude (µV)")

        for ax in (ax1, ax2, ax3, ax4):
            ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(filename.replace(".tsv", "_task1.pdf"))


def task2(fs):
    h = design_fir(fs, [BASELINE, MAINS])
    M = len(h)
    print(f"Task 2: fs = {fs} Hz, {M} taps, delay {(M - 1) / 2 / fs:.2f} s")

    # impulse response and frequency response (zero padded FFT of h)
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
    fig.savefig("task2_filter.pdf")
    return h


def task3(fs, x, h):
    y = realtime(FIRfilter(h), x)
    M = len(h)
    delay = (M - 1) // 2
    t = np.arange(len(x)) / fs

    # whole recording before and after, skipping the first M samples while the delay line fills
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
        ax.set_ylabel("ECG (mV)")
    fig.tight_layout()
    fig.savefig("task3_beat.pdf")
    return y


def task4(fs, x, y_fir):
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

    y_lms = np.zeros(len(x))
    for n, v in enumerate(x):
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
    fig.savefig("task4.pdf")


def task5(fs, y, h):
    M = len(h)
    fs_p, xp = load_ecg(PARTNER)
    assert fs == fs_p, "template and ECG need the same sampling rate"

    # template: one PQRST from the partner's filtered ECG
    yp = realtime(FIRfilter(h), xp)
    r = M + fs + np.argmax(np.abs(yp[M + fs:M + 4 * fs]))
    template = yp[r - int(0.3 * fs):r + int(0.4 * fs)]
    template = template - np.mean(template)

    # matched filter = FIR whose coefficients are the time reversed template, run on our filtered ECG.
    # squaring makes the peaks stand out more and doesn't care about the sign
    m = realtime(FIRfilter(template[::-1]), y) ** 2

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


task1()
fs, x = load_ecg(MINE)
h = task2(fs)
y = task3(fs, x, h)
task4(fs, x, y)
task5(fs, y, h)
plt.show()
