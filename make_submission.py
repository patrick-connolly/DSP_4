"""Build the Moodle zip for DSP Assignment 1 without touching the repo.

Set REPORT_PDF below, then run from anywhere:
    python3 make_submission.py

Copies the report, WAVs and code into submission/ with the Moodle names,
changes the file names inside the copied scripts to match, and zips the nine
required files as submission/2777107c_2893681a.zip. Nothing is re-run: the
enhanced and exciter WAVs are the ones already in Ass1/.
"""
import os
import shutil
import sys
import zipfile

REPORT_PDF = "DSP_4.pdf"  # report exported from Overleaf, relative to this folder

ZIP_NAME = "2777107c_2893681a.zip"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Ass1")
OUT = os.path.join(HERE, "submission")

# file in Ass1/ -> Moodle name
WAVS = {
    "Zabi_5cm.wav": "original_speech_5cm.wav",
    "Zabi_1m.wav": "original_speech_1m.wav",
    "Zabi_5cm_enhanced.wav": "enhanced_speech_5cm.wav",
    "Zabi_1m_enhanced.wav": "enhanced_speech_1m.wav",
    "Zabi_5cm_exciter_v2_final.wav": "exciter_speech.wav",
}

# repo script -> Moodle name, and the text swaps needed inside each copy
SCRIPTS = {
    "task1.py": ("audioplot.py", [
        ("Zabi_5cm.wav", "original_speech_5cm.wav"),
        ("Zabi_1m.wav", "original_speech_1m.wav"),
    ]),
    "task2.py": ("audioenhancer.py", [
        ('filename.replace(".wav", "_enhanced.wav")', 'filename.replace("original", "enhanced")'),
        ("Zabi_5cm.wav", "original_speech_5cm.wav"),
        ("Zabi_1m.wav", "original_speech_1m.wav"),
    ]),
    "task3.py": ("auralexciter.py", [
        ("Zabi_5cm_exciter_v1_initial.wav", "exciter_speech_v1_initial.wav"),
        ("Zabi_5cm_exciter_v2_final.wav", "exciter_speech_v2_final.wav"),
        ("Zabi_5cm.wav", "original_speech_5cm.wav"),
    ]),
}

report = os.path.join(HERE, REPORT_PDF)
if not os.path.isfile(report):
    sys.exit(f"can't find {REPORT_PDF} - check REPORT_PDF at the top of this script")

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
zip_path = os.path.join(OUT, ZIP_NAME)

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(report, "report.pdf")

    for old, new in WAVS.items():
        z.write(os.path.join(SRC, old), new)

    for old, (new, swaps) in SCRIPTS.items():
        with open(os.path.join(SRC, old)) as fh:
            code = fh.read()
        for a, b in swaps:
            if a not in code:
                sys.exit(f"{old}: expected to find {a!r} - has the code changed?")
            code = code.replace(a, b)
        z.writestr(new, code)

print("made", os.path.relpath(zip_path, HERE))
with zipfile.ZipFile(zip_path) as z:
    for name in z.namelist():
        print("  ", name)
