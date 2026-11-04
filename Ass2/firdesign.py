import numpy as np


def design_fir(fs, stop_bands):
    # stop_bands is a list of (low, high) in Hz to remove. A band starting at 0 removes DC (highpass)
    # the IFFT samples the response every fs/M Hz, so fs/M has to be no wider than the
    # narrowest band, otherwise that band can fall between two bins and nothing gets removed
    df = min(hi - lo for lo, hi in stop_bands)
    M = int(np.ceil(fs / df)) | 1  # odd so the delay (M-1)/2 is a whole number of samples

    k = np.arange(M)
    f = np.minimum(k, M - k) * fs / M  # frequency of each bin, the top half mirrors the bottom
    H = np.ones(M)
    for lo, hi in stop_bands:
        H[(f >= lo) & (f <= hi)] = 0

    h = np.real(np.fft.ifft(H))
    h = np.roll(h, M // 2)  # the peak is at index 0, move it to the middle to make it causal
    h = h * np.hamming(M)  # smooth the truncation to cut the ripple

    # windowing lets a little DC leak back in, which matters because the ECG offset is huge
    if min(lo for lo, hi in stop_bands) <= 0:
        h = h - np.mean(h)  # DC gain is sum(h), force it to exactly 0
    return h
