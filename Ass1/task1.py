import matplotlib.pyplot as plt
from audio import AudioSignal

# Regions chosen
marks = {
    "Zabi_5cm.wav": {"vowels": [95.3, 102, 108, 122], "consonants": (2000, 20000), "noise": [(20, 80), (20500, 22050)]},
    "Zabi_1m.wav":  {"vowels": [90, 98, 106.3, 114],  "consonants": (2000, 20000), "noise": [(20, 80), (20500, 22050)]},
}

for filename, m in marks.items():
    sig = AudioSignal(filename)
    print(sig)
    fig = sig.plot()
    ax = fig.axes[1]  # frequency plot
    ax.set_xlim(20, sig.fs / 2)  # audible range up to Nyquist
    ax.vlines(m["vowels"], -120, 5, colors="r", linestyles="--", label="Vowel fundamentals")
    ax.axvspan(*m["consonants"], color="g", alpha=0.2, label="Consonants")
    for i, band in enumerate(m["noise"]):
        ax.axvspan(*band, color="grey", alpha=0.4, label="Noise" if i == 0 else None)
    ax.legend(loc="lower left")
    #fig.savefig(filename.replace(".wav", ".pdf"))  # vector format for the report

plt.show()
