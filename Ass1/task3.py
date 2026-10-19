import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile


os.chdir(os.path.dirname(os.path.abspath(__file__)))  # find the wav files wherever the script is run from

fs, x = wavfile.read("Zabi_5cm.wav")
x = x[:, 0]  # stereo file, delete second channel
x = x / np.max(np.abs(x))  # normalise to +-1
x = np.trim_zeros(x, "b")  # trim trailing zeros added by garageband ## "b" given in numpy doc just to cut trailing
N = len(x)

# frequency of each bin the second half is a mirror of the first half
f = np.arange(N) * fs / N
f = np.minimum(f, fs - f)


# gain that goes from 0 at f0 up to 1 at f1, so 1- ramp is a lowpass
def ramp(f0, f1):
    return np.clip((f - f0) / (f1 - f0), 0, 1)


#fft
X = np.fft.fft(x)

# remove pops below 80 Hz and noise above 20.5 kHz first
X = X * ramp(60, 80) * (1 - ramp(20000, 20500))
x = np.real(np.fft.ifft(X))


# tanh puts a bit back below 80 Hz so the pop cut is done again afterwards
low = np.real(np.fft.ifft(X * (1 - ramp(150, 190))))
low = low / np.max(np.abs(low))
bass = np.real(np.fft.ifft(np.fft.fft(np.tanh(3 * low)) * ramp(60, 80)))


# hp = highpass gain, band = which harmonics to keep, drive = how hard tanh gets pushed
def exciter(hp, band, drive, mix, bass_mix):
    # highpass, then normalise so drive does the same thing every time
    side = np.real(np.fft.ifft(X * hp))
    side = side / np.max(np.abs(side))

    # tanh makes the odd harmonics 
    harm = np.tanh(drive * side)

    # only keep the harmonics inside the band
    harm = np.real(np.fft.ifft(np.fft.fft(harm) * band))
    harm = harm / np.max(np.abs(harm))

    return mix * harm + bass_mix * bass


# v1 highpass at 800 Hz and keep all the harmonics
added1 = exciter(ramp(600, 800), 1, 5, 0.3, 0)

# v2 highpass at 3 kHz and keep harmonics from 4-12 kHz
hp2 = ramp(2000, 3000)
band2 = ramp(4000, 5000) * (1 - ramp(10000, 12000))  # bandpass
added2 = exciter(hp2, band2, 5, 0.15, 0.1)

y1 = x + added1
y2 = x + added2


out1 = y1 / np.max(np.abs(y1))
out2 = y2 / np.max(np.abs(y2))
wavfile.write("Zabi_5cm_exciter_v1_initial.wav", fs, out1.astype(np.float32))
wavfile.write("Zabi_5cm_exciter_v2_final.wav", fs, out2.astype(np.float32))

#plotting
half = N // 2
fp = f[1:half]  # skip DC for the log axis
ref = np.max(np.abs(X[1:half])) 

def dB(s):
    mag = np.abs(np.fft.fft(s)[1:half])
    return 20 * np.log10(mag / ref + 1e-12)


x_dB = dB(x)

# plots each version 
def plot_added(added, version, colour):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(fp, x_dB, label="Input", color="lightgrey")
    ax.plot(fp, dB(added), label=f"Added by {version}", color=colour)
    ax.axvspan(20, 80, color="grey", alpha=0.2, label="Pops removed")
    ax.set_xscale("log")
    ax.set_xlim(20, fs / 2)
    ax.set_ylim(-120, 5)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude (dB) relative to input peak")
    ax.set_title(f"What {version} adds to the voice")
    return fig, ax


arrow = dict(arrowstyle="->")

fig1, ax1 = plot_added(added1, "v1", "C0")
ax1.annotate("almost as loud as the voice\nabove 800 Hz, sounds harsh", xy=(8000, -30), xytext=(1000, -95), arrowprops=arrow)
ax1.annotate("energy put back\nwhere the pops were", xy=(45, -50), xytext=(22, -100), arrowprops=arrow)
ax1.legend(loc="upper right", fontsize="small")

fig2, ax2 = plot_added(added2, "v2", "C1")
ax2.axvspan(80, 190, color="purple", alpha=0.15, label="Bass band")
ax2.axvspan(4000, 12000, color="green", alpha=0.15, label="Harmonics band")
ax2.annotate("only 4-12 kHz is kept", xy=(7000, -40), xytext=(1500, -8), arrowprops=arrow)
ax2.annotate("compressed bass", xy=(110, -25), xytext=(25, -60), arrowprops=arrow)
ax2.text(22, -110, "nothing added below 60 Hz")
ax2.legend(loc="lower right", fontsize="small")

# plots how much each version changes the level of the voice
edges = np.geomspace(80, 20000, 41)
centres = np.sqrt(edges[:-1] * edges[1:])  # middle of each band on a log axis


def band_power(s):
    P = np.abs(np.fft.fft(s)[1:half]) ** 2
    return np.array([P[(fp >= lo) & (fp < hi)].mean() for lo, hi in zip(edges[:-1], edges[1:])])


Px = band_power(x)
fig3, ax3 = plt.subplots(figsize=(8, 4))
ax3.plot(centres, 10 * np.log10(band_power(y1) / Px), "o-", label="v1")
ax3.plot(centres, 10 * np.log10(band_power(y2) / Px), "o-", label="v2")
ax3.axhline(0, color="k", linewidth=0.5)
ax3.annotate("v1 lifts everything above 800 Hz by 6-9 dB", xy=(1500, 6.1), xytext=(200, 7.5), arrowprops=arrow)
ax3.annotate("v2 only lifts 4-12 kHz, by about 3 dB", xy=(7000, 3.4), xytext=(1000, 4.2), arrowprops=arrow)
ax3.annotate("v2 bass, about +2 dB", xy=(130, 2.3), xytext=(200, 3.5), arrowprops=arrow)
ax3.set_xscale("log")
ax3.set_xlabel("Frequency (Hz)")
ax3.set_ylabel("Change in level (dB)")
ax3.set_title("How much each version changes the voice")
ax3.legend(loc="upper left")

for fig in [fig1, fig2, fig3]:
    fig.tight_layout()
fig1.savefig("task3_v1.pdf")
fig2.savefig("task3_v2.pdf")
fig3.savefig("task3_change.pdf")
plt.show()
