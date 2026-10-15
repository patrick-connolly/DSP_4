import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# aural exciter based on the aphex block diagram in the brief
# exciter part: highpass -> tanh makes harmonics -> only keep some of them -> mix back in
# big bottom part: lowpass -> tanh squashes it like a compressor -> mix back in
# all the filtering is done by multiplying the fft and then doing the ifft (like task 2)

fs, x = wavfile.read("Zabi_5cm.wav")
x = x[:, 0]  # stereo file, both channels are the same
x = x / np.max(np.abs(x))  # normalise to +-1
x = np.trim_zeros(x, "b")  # trim trailing zeros added by garageband
N = len(x)

# frequency of each bin, folded like in task 2 so both halves get changed the same
f = np.arange(N) * fs / N
f = np.minimum(f, fs - f)


# gain that goes from 0 at f0 up to 1 at f1, so 1 - ramp is a lowpass
# used a slope instead of a hard cut because hard cuts can cause ringing
def ramp(f0, f1):
    return np.clip((f - f0) / (f1 - f0), 0, 1)


#fft
X = np.fft.fft(x)

# remove pops below 80 Hz first, same as task 2
# no cut at the top because task 1 shows the consonants go up to about 20 kHz
X = X * ramp(60, 80)
x = np.real(np.fft.ifft(X))


# hp = highpass gain, band = which harmonics to keep, drive = how hard tanh gets pushed,
# mix and bass_mix = how much of each part gets added back
# returns only the part that gets added to the voice
def exciter(hp, band, drive, mix, bass_mix):
    # highpass, then normalise so drive does the same thing every time
    side = np.real(np.fft.ifft(X * hp))
    side = side / np.max(np.abs(side))

    # tanh makes the harmonics, its symmetric so only odd ones (3rd, 5th...)
    harm = np.tanh(drive * side)

    # only keep the harmonics inside the band
    harm = np.real(np.fft.ifft(np.fft.fft(harm) * band))
    harm = harm / np.max(np.abs(harm))

    # big bottom, lowpass then tanh squashes the loud bits like a compressor
    low = np.real(np.fft.ifft(X * (1 - ramp(150, 190))))
    low = low / np.max(np.abs(low))
    bass = np.tanh(3 * low)

    return mix * harm + bass_mix * bass


# v1 first try: highpass at 800 Hz and keep all the harmonics (band = 1)
added1 = exciter(ramp(600, 800), 1, 5, 0.3, 0)

# v2: v1 boosts everything above 800 Hz (12-20 kHz goes up about 7 dB) and puts stuff back
# below 80 Hz where i'd removed the pops (see figure 2)
# so the highpass is moved up to 3 kHz, only harmonics from 4-10 kHz are kept, plus a bit of bass
hp2 = ramp(2000, 3000)
band2 = ramp(4000, 5000) * (1 - ramp(10000, 12000))  # highpass * lowpass = bandpass
added2 = exciter(hp2, band2, 5, 0.15, 0.1)

y1 = x + added1
y2 = x + added2

# save them so i can listen, normalised so they dont clip
out1 = y1 / np.max(np.abs(y1))
out2 = y2 / np.max(np.abs(y2))
wavfile.write("Zabi_5cm_exciter_v1_initial.wav", fs, out1.astype(np.float32))
wavfile.write("Zabi_5cm_exciter_v2_final.wav", fs, out2.astype(np.float32))

#plotting
half = N // 2
fp = f[1:half]  # skip DC for the log axis
ref = np.max(np.abs(X[1:half]))  # 0 dB = input peak so all the curves can be compared


def dB(s):
    mag = np.abs(np.fft.fft(s)[1:half])
    return 20 * np.log10(mag / ref + 1e-12)


x_dB = dB(x)

# figure 1: output of v1 and v2, input drawn last in black so it doesnt get hidden
fig1, ax1 = plt.subplots(figsize=(8, 4))
ax1.plot(fp, dB(y1), label="v1 output", alpha=0.7)
ax1.plot(fp, dB(y2), label="v2 output", alpha=0.7)
ax1.plot(fp, x_dB, label="Input", color="k", linewidth=0.5)
ax1.set_title("Exciter output spectra")

# figure 2: only the part v1 and v2 add to the voice
fig2, ax2 = plt.subplots(figsize=(8, 4))
ax2.plot(fp, x_dB, label="Input", color="lightgrey")
ax2.plot(fp, dB(added1), label="Added by v1", alpha=0.7)
ax2.plot(fp, dB(added2), label="Added by v2", alpha=0.7)
ax2.set_title("What v1 and v2 add to the voice")

# same shading and labels on both
for ax in [ax1, ax2]:
    ax.axvspan(20, 80, color="grey", alpha=0.2, label="Removed (pops)")
    ax.axvspan(80, 190, color="purple", alpha=0.15, label="v2 bass band")
    ax.axvspan(4000, 10000, color="green", alpha=0.15, label="v2 harmonics band")
    ax.set_xscale("log")
    ax.set_xlim(20, fs / 2)
    ax.set_ylim(-120, 5)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude (dB) relative to input peak")
    ax.legend(loc="lower left", fontsize="small")

fig1.tight_layout()
fig2.tight_layout()
#fig1.savefig("task3_spectra.pdf")
#fig2.savefig("task3_added.pdf")
plt.show()
