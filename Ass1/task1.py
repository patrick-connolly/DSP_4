import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# Regions chosen by eye from the spectra (Hz)
marks = {
    "Zabi_5cm.wav": {"vowels": [95.3, 102, 108, 122], "consonants": (2000, 20000), "noise": [(20, 80), (20500, 22050)]},
    "Zabi_1m.wav":  {"vowels": [90, 98, 106.3, 114],  "consonants": (2000, 20000), "noise": [(20, 80), (20500, 22050)]},
}

for filename, m in marks.items():
    fs, x = wavfile.read(filename)
    x = x[:, 0]  # stereo file, both channels are the same
    x = x / np.max(np.abs(x))  # normalise to +-1
    N = len(x)
    t = np.arange(N) / fs

    # spectrum up to Nyquist, skipping the DC bin so the log axis works
    X = np.abs(np.fft.fft(x)[1:N // 2])
    f = np.arange(1, N // 2) * fs / N
    XdB = 20 * np.log10(X / np.max(X))

    # noise floor: spectrum of the first 0.1 s, before speaking starts
    # zero-padded to N so the bins match, scaled so the noise level matches the full recording
    s = x[:int(0.1 * fs)]
    S = np.abs(np.fft.fft(s, N)[1:N // 2]) * np.sqrt(N / len(s))
    SdB = 20 * np.log10(S / np.max(X))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    fig.suptitle(f"{filename} (fs = {fs} Hz)")
    ax1.plot(t, x)
    ax1.axvspan(0, 0.1, color="orange", alpha=0.3)  # section used for the noise floor
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Normalised amplitude")

    ax2.plot(f, XdB)
    ax2.plot(f, SdB, color="orange", alpha=0.8, label="Noise floor (first 0.1 s)")
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
