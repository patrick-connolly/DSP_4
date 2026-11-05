import numpy as np

# recordings from the lab: time (s) in column 0, ECG in ECG_COLUMN
MINE = "patrickecg1.tsv"
PARTNER = "zabiecg1.tsv"
ECG_COLUMN = 8  # Bernd: column 8 counting from 0

# noise picked out of the task1 spectrum: baseline wander and 50 Hz mains
BASELINE = (0, 0.5)
MAINS = [(48, 52)]  # only the 50 Hz fundamental: no 100 Hz peak in the task 1 spectrum


def load_ecg(filename):
    data = np.loadtxt(filename)
    t = data[:, 0]
    fs = round((len(t) - 1) / (t[-1] - t[0]))
    return fs, data[:, ECG_COLUMN]


def spectrum(x, fs):
    # single sided magnitude in dB, frequency axis built by hand since fftfreq isn't allowed
    N = len(x)
    X = np.abs(np.fft.fft(x)[:N // 2]) / N
    return np.arange(N // 2) * fs / N, 20 * np.log10(X + 1e-12)
