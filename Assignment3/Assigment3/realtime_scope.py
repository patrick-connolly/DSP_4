"""Real-time scope for one Arduino analogue input, using pyFirmata2.

The Arduino must be running StandardFirmata.
Usage: python realtime_scope.py [serial port]   (the port is auto-detected if omitted)
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pyfirmata2 import Arduino

FS = 100         # sampling rate (Hz); the sampling interval is 1000/FS ms, minimum 1 ms
CHANNEL = 0      # analogue input A0
WINDOW = 5 * FS  # number of samples on screen (5 s)


class ScrollingPlot:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.buffer = np.zeros(WINDOW)
        self.line, = self.ax.plot(np.arange(-WINDOW, 0) / FS, self.buffer)
        self.ax.set(xlabel="time (s)", ylabel=f"A{CHANNEL} (1 = 5 V)", ylim=(0, 1))
        self.new_samples = []
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=50, cache_frame_data=False)

    def add_sample(self, value):
        # Called by pyFirmata2's serial thread for every sample.
        self.new_samples.append(value)

    def update(self, _frame):
        # Swap in an empty list first so samples arriving meanwhile aren't lost.
        new, self.new_samples = self.new_samples, []
        self.buffer = np.append(self.buffer, new)[-WINDOW:]
        self.line.set_ydata(self.buffer)
        return self.line,


port = sys.argv[1] if len(sys.argv) > 1 else Arduino.AUTODETECT
plot = ScrollingPlot()
board = Arduino(port)
try:
    board.samplingOn(1000 / FS)
    board.analog[CHANNEL].register_callback(plot.add_sample)
    board.analog[CHANNEL].enable_reporting()
    plt.show()
finally:
    board.exit()  # always release the serial port
