import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the wav files wherever the script is run from

# Regions chosen by eye
# same speaker and sentence, so the consonants sit in the same range at both distances
marks = {
    "Zabi_5cm.wav": {"vowels": [88.2, 95.3, 100.6, 104.7, 108, 122.5], "consonants": (3000, 20000), "noise": [(20, 80), (20500, 22050)]},
    "Zabi_1m.wav":  {"vowels": [89.2, 98, 107.7, 114],  "consonants": (4200, 20000), "noise": [(20, 80), (20500, 22050)]},
}

# Main Loop
for filename, m in marks.items():
    fs, x = wavfile.read(filename)
    x = x[:, 0]  # stereo file, both channels are the same
    x = x / np.max(np.abs(x))  # normalise to +-1
    x = np.trim_zeros(x, "b")  # trim trailing zeros added by garageband  ## "b" given in numpy doc just to cut trailing

    N = len(x)
    t = np.arange(N) / fs #for time axis

    # spectrum up to Nyquist, skipping the DC bin so the log axis works
    X = np.abs(np.fft.fft(x)[1:N // 2])
    f = np.arange(1, N // 2) * fs / N
    XdB = 20 * np.log10(X / np.max(X)) #dB relative to peak

    # plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    fig.suptitle(f"{filename} (fs = {fs} Hz)")
    ax1.plot(t, x)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Normalised amplitude")

    ax2.plot(f, XdB)
    ax2.set_xscale("log")
    ax2.set_xlim(20, fs / 2)  # audible range up to Nyquist
    ax2.set_ylim(-120, 5)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Amplitude (dB) relative to peak")
    ax2.vlines(m["vowels"], -120, 5, colors="r", linestyles="--", label="Vowel fundamentals")
    ax2.axvspan(*m["consonants"], color="g", alpha=0.2, label="Consonants")
    low, high = m["noise"]
    ax2.axvspan(*low, color="grey", alpha=0.4, label="Noise")
    ax2.axvspan(*high, color="grey", alpha=0.4)
    ax2.legend(loc="lower left")
    fig.tight_layout()
    #fig.savefig(filename.replace(".wav", ".pdf"))  

plt.show()
