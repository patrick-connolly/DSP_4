import matplotlib.pyplot as plt
from audio import AudioSignal

# Regions chosen by eye from each spectrum (no automatic detection)
marks = {
    "Zabi_5cm.wav": {"vowels": [100, 108, 115, 123], "consonants": (2000, 11000), "noise": (12000, 22050)},
    "Zabi_1m.wav":  {"vowels": [97, 105, 115],        "consonants": (2000, 10000), "noise": (11000, 22050)},
}

for filename, m in marks.items():
    sig = AudioSignal(filename)
    print(sig)
    fig = sig.plot()
    ax = fig.axes[1]  # frequency plot
    ax.vlines(m["vowels"], -120, 5, colors="r", linestyles="--", label="Vowel fundamentals")
    ax.axvspan(*m["consonants"], color="g", alpha=0.2, label="Consonants")
    ax.axvspan(*m["noise"], color="grey", alpha=0.3, label="Noise")
    ax.legend(loc="lower left")
    #fig.savefig(filename.replace(".wav", ".pdf"))  # vector format for the report

plt.show()
