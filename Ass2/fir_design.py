import numpy as np


def design_fir(fs, stop_bands): #list contaning freqs bins to remove
  
    df = min(hi - lo for lo, hi in stop_bands) # minimum width of the stop bands
    M = int(np.ceil(2 * fs / df)) | 1 #choice of M, choosen so two points land whithin each df ## '| 1' forces it odd

    k = np.arange(M)
    f = np.minimum(k, M - k) * fs / M  # frequency of each bin
    H = np.ones(M)
    for lo, hi in stop_bands:
        H[(f >= lo) & (f <= hi)] = 0

    h = np.real(np.fft.ifft(H))
    h = np.roll(h, M // 2)  # swap the halves to make it causal 
    return h * np.hamming(M)  # smooths the transition
