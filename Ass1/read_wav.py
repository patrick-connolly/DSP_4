import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

filename = sys.argv[1] if len(sys.argv) > 1 else 'tone_1kHz.wav'
fs, x = wavfile.read(filename)

if x.ndim > 1:
    x = x[:, 0]  # Use only the first channel if stereo
x = x / np.max(np.abs(x))  # Normalize the signal
N = len(x)
print(f"fs = {fs} Hz, N = {N} samples, duration = {N/fs:.2f} s")

#time domain 
t = np.arange(N) / fs

#frequency domain
X = np.fft.fft(x)
half = N // 2
f = np.arange(1, half) * fs / N                 # skip DC bin for log axis
mag = np.abs(X[1:half])
XdB = 20 * np.log10(mag / np.max(mag) + 1e-12)  # offset to avoid log(0)

#plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
ax1.plot(t, x)
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Normalised amplitude")
ax1.set_xlim(0, 0.005)          #!!!mind remove for real recording # a zoom to 5 ms so the sine is visible
ax2.plot(f, XdB)
ax2.set_xscale("log")
ax2.set_xlabel("Frequency (Hz)")
ax2.set_ylabel("Amplitude (dB)")
ax2.set_ylim(-120, 5)
fig.tight_layout()
#fig.savefig("tone_1khz.pdf")
plt.show()