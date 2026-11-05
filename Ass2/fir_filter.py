import numpy as np


class FIRfilter:
    def __init__(self, _coefficients):
        self.h = np.array(_coefficients, dtype=float)
        self.M = len(self.h)
        self.buf = np.zeros(self.M)  # ring buffer for the delay line, samples never move once stored
        self.offset = 0  # where the next sample goes

    def store(self, v):
        # write v over the oldest sample and move the offset on, instead of shifting the buffer
        n = self.offset
        self.buf[n] = v
        self.offset = (n + 1) % self.M
        return n

    def halves(self, n):
        # the delay line newest first is buf[n], buf[n-1], ..., buf[0], then it wraps round to
        # buf[M-1], ..., buf[n+1]. h[0] lines up with the newest sample, so split h the same way
        return (self.h[:n + 1], self.buf[n::-1]), (self.h[n + 1:], self.buf[:n:-1])

    def dofilter(self, v):
        (h1, x1), (h2, x2) = self.halves(self.store(v))
        return np.dot(h1, x1) + np.dot(h2, x2)

    def doFilterAdaptive(self, signal, noise, learningRate):
        (h1, x1), (h2, x2) = self.halves(self.store(noise))
        e = signal - (np.dot(h1, x1) + np.dot(h2, x2))  # whatever the noise reference can't explain is the ECG
        # LMS: move each weight by its delay line sample times the error. h1, h2 are views, so this updates self.h
        h1 += learningRate * e * x1
        h2 += learningRate * e * x2
        return e
