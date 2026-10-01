import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile


class AudioSignal:
    #file input
    def __init__(self, filename):
        fs, x = wavfile.read(filename)
        if x.ndim > 1:
            x = x[:, 0]  # Use only the first channel if stereo
        peak = np.max(np.abs(x))
        if peak > 0:
            x = x / peak  # Normalize the signal
        self.filename = filename
        self.fs = fs
        self.x = x
        self.N = len(x)

    def duration(self):
        return self.N / self.fs

    #time domain
    def time_axis(self):
        return np.arange(self.N) / self.fs

    #frequency domain
    def fft(self):
        X = np.fft.fft(self.x)
        half = self.N // 2
        f = np.arange(1, half) * self.fs / self.N       # skip DC bin for log axis
        mag = np.abs(X[1:half])
        XdB = 20 * np.log10(mag / np.max(mag) + 1e-12)  # offset to avoid log(0)
        return f, XdB

    #plotting
    def plot(self, zoom=None):
        t = self.time_axis()
        f, XdB = self.fft()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
        ax1.plot(t, self.x)
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Normalised amplitude")
        if zoom is not None:
            ax1.set_xlim(0, zoom)
        ax2.plot(f, XdB)
        ax2.set_xscale("log")
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Amplitude (dB)")
        ax2.set_ylim(-120, 5)
        fig.tight_layout()
        return fig

    def __repr__(self):
        return f"AudioSignal(fs={self.fs} Hz, N={self.N}, duration={self.duration():.2f} s)"


if __name__ == "__main__":
    filename = "Testingtestingtesting.wav"
    sig = AudioSignal(filename)
    print(sig)
    fig = sig.plot(zoom=0.005)  # zoom to 5 ms so the sine is visible; remove for real recordings
    #fig.savefig("tone_1khz.pdf")
    plt.show()
