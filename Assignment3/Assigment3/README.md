# DSP Assignment 3: real-time IIR filtering

An Arduino Uno samples an analogue signal and streams it to Python with
[pyFirmata2](https://github.com/berndporr/pyFirmata2), where it is filtered in real time.

## 1. Arduino firmware

The Arduino must run **StandardFirmata**. Use either:

- **Arduino IDE:** File → Examples → Firmata → StandardFirmata, then Upload.
- **PlatformIO:** `pio run -t upload` (builds `src/firmata/`).

`pio run -e selftest -t upload` flashes an optional board self-test instead.
Read its results with `pio device monitor -e selftest`, then reflash StandardFirmata.

## 2. Python setup

Tested with Python 3.14.

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt          # macOS / Linux
.venv\Scripts\pip install -r requirements.txt      # Windows
```

## 3. Run

```
.venv/bin/python realtime_scope.py           # port auto-detected
.venv/bin/python realtime_scope.py COM4      # or name the port explicitly
```

Run it from a terminal, not from inside an IDE, because IDEs can leave the serial port locked.
`realtime_scope.py` plots analogue input A0 sampled at 100 Hz.
