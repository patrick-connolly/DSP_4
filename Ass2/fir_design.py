import numpy as np


def design_fir(fs, stop_bands):
    # stop_bands is a list of (low, high) in Hz to remove. A band starting at 0 removes DC (highpass)
    # the IFFT samples the response every fs/M Hz, so fs/M has to be no wider than the narrowest
    # band. That is only the theoretical best: the window smears each band edge over a few bins,
    # so we use twice as many taps to keep the heart rate fundamental (~1 Hz) out of the transition
    df = min(hi - lo for lo, hi in stop_bands)
    # odd M with a symmetric h is a type 1 linear phase filter: the only type with no forced
    # zero at Nyquist, which the highpass needs, and the delay (M-1)/2 is a whole number of samples
    M = int(np.ceil(2 * fs / df)) | 1

    k = np.arange(M)
    f = np.minimum(k, M - k) * fs / M  # frequency of each bin, the top half mirrors the bottom
    H = np.ones(M)
    for lo, hi in stop_bands:
        H[(f >= lo) & (f <= hi)] = 0

    h = np.real(np.fft.ifft(H))
    h = np.roll(h, M // 2)  # swap the halves: negative time goes before positive time, so it is causal
    return h * np.hamming(M)  # smooth the truncation to cut the ripple
