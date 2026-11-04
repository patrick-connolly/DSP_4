import numpy as np


class FIRfilter:
    def __init__(self, _coefficients):
        self.h = np.array(_coefficients[::-1], dtype=float)  # reversed so it lines up with the delay line
        self.M = len(self.h)
        # ring buffer stored twice so the last M samples are always one contiguous slice, nothing shifts
        self.buf = np.zeros(2 * self.M)
        self.n = 0

    def push(self, v):
        # write v into the ring buffer, return the last M samples oldest first
        self.buf[self.n] = self.buf[self.n + self.M] = v
        self.n = (self.n + 1) % self.M
        return self.buf[self.n:self.n + self.M]

    def dofilter(self, v):
        return np.dot(self.h, self.push(v))

    def doFilterAdaptive(self, signal, noise, learningRate):
        x = self.push(noise)
        e = signal - np.dot(self.h, x)  # whatever the noise reference can't explain is the ECG
        self.h += learningRate * e * x  # LMS: move the weights to make the error smaller
        return e
