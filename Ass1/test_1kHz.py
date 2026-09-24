import numpy as np
from scipy.io import wavfile

fs = 48000  # Sample rate
f0 = 1000   # Tone Freq.
t = np.arange(fs) / fs  # 1 second time stamp
x = 0.5 * np.sin(2 * np.pi * f0 * t)  # Generate sine wave

wavfile.write('tone_1kHz.wav', fs, (x * 32767).astype(np.int16))  # Save as WAV file
print("Made test_1kHz")