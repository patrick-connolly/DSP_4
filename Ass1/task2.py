import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the wav files wherever the script is run from

filenames = ["Zabi_5cm.wav", "Zabi_1m.wav"]


# gain that goes from 0 at f0 up to 1 at f1, so 1 - ramp is a lowpass (same as task 3)
# slopes instead of hard steps because hard steps in the gain made the voice ring
# f is the frequency axis of the file being processed, set in the loop below
def ramp(f0, f1):
    return np.clip((f - f0) / (f1 - f0), 0, 1)


for filename in filenames:
    fs, x = wavfile.read(filename)
    x = x[:, 0]  # stereo file, both channels are the same
    x = x / np.max(np.abs(x))  # normalise to +-1
    x = np.trim_zeros(x, "b")  # trim trailing zeros added by garageband  ## "b" given in numpy doc just to cut trailing
    N = len(x)

    #fft
    X = np.fft.fft(x)

    # frequency of each bin, the second half is a mirror of the first half
    # so fold it back so both halves get changed the same
    f = np.arange(N) * fs / N
    f = np.minimum(f, fs - f)

    # remove everything below 80 Hz (rumble, and pops for the 5cm one)
    # and the upper noise margin identified in task 1, above 20.5 kHz
    G = ramp(60, 80) * (1 - ramp(20000, 20500))

    # boost 2-5 kHz to make the voice clearer
    G *= 1 + 0.3 * ramp(1500, 2000) * (1 - ramp(5000, 6000))  # x1.3 is about +2.3 dB

    # boost bass for 1m only because bass is lost with distance
    # 5cm already has loads of bass (proximity effect)
    # only below 120 Hz where the vowel fundamentals are (89-114 Hz in task 1),
    # the room noise is worst compared to the voice at 120-200 Hz so that is left alone
    if filename == "Zabi_1m.wav":
        G *= 1 + 0.4 * (1 - ramp(120, 150))  # x1.4 is about +3 dB

    Y = X * G

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
    ax.axvspan(20, 80, color="grey", alpha=0.15)
    ax.axvspan(20500, fs / 2, color="grey", alpha=0.15)
    if filename == "Zabi_1m.wav":
        ax.axvspan(80, 120, color="green", alpha=0.15)
    ax.axvspan(2000, 5000, color="green", alpha=0.15)

    ax.set_xscale("log")
    ax.set_xlim(20, fs / 2)
    ax.set_ylim(-120, 5)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude (dB) relative to peak")
    ax.set_title(filename + ": removed (grey), boosted (green)")
    ax.legend(loc="lower left")
    fig.tight_layout()
    #fig.savefig(filename.replace(".wav", "_task2.pdf"))

plt.show()
