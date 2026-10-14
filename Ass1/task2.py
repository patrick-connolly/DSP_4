import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

filenames = ["Zabi_1m.wav", "Zabi_5cm.wav"]

for filename in filenames:
    fs, x = wavfile.read(filename)
    x = x[:, 0]  # stereo file, both channels are the same
    x = x / np.max(np.abs(x))  # normalise to +-1
    N = len(x)

    #fft
    X = np.fft.fft(x)

    # frequency of each bin, the second half is a mirror of the first half
    # so fold it back so both halves get changed the same
    f = np.arange(N) * fs / N
    f = np.minimum(f, fs - f)

    Y = X.copy()

    # remove everything below 80 Hz (rumble, and pops for the 5cm one)
    Y[f < 80] = 0

    # boost bass for 1m only because bass is lost with distance
    # 5cm already has loads of bass (proximity effect)
    if filename == "Zabi_1m.wav":
        Y[(f >= 100) & (f < 300)] *= 2  # x2 is about +6 dB

    # boost 2-5 kHz to make the voice clearer
    Y[(f >= 2000) & (f < 5000)] *= 1.6  # x1.6 is about +4 dB

    #ifft back to time domain
    y = np.real(np.fft.ifft(Y))  # imaginary part is basically 0
    y = y / np.max(np.abs(y))  # normalise again so it doesnt clip

    wavfile.write(filename.replace(".wav", "_enhanced.wav"), fs, y.astype(np.float32))

    #plot before and after
    half = N // 2
    mag_before = np.abs(X[1:half])
    mag_after = np.abs(Y[1:half])
    ref = np.max(mag_before)  # same reference for both so the plot shows the real change
    dB_before = 20 * np.log10(mag_before / ref + 1e-12)
    dB_after = 20 * np.log10(mag_after / ref + 1e-12)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(f[1:half], dB_before, label="Original", alpha=0.7)
    ax.plot(f[1:half], dB_after, label="Enhanced", alpha=0.7)

    # shade the bands that were changed, grey = removed, green = boosted
    ax.axvspan(f[1], 80, color="grey", alpha=0.15)
    if filename == "Zabi_1m.wav":
        ax.axvspan(100, 300, color="green", alpha=0.15)
    ax.axvspan(2000, 5000, color="green", alpha=0.15)

    ax.set_xscale("log")
    ax.set_ylim(-120, 5)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude (dB) relative to peak")
    ax.set_title(filename + ": removed (grey), boosted (green)")
    ax.legend(loc="lower left")
    fig.tight_layout()
    #fig.savefig(filename.replace(".wav", "_task2.pdf"))

plt.show()
