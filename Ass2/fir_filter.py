import numpy as np


class FIRfilter:
    def __init__(self, _coefficients):
        self.h = np.array(_coefficients, dtype=float)
        self.M = len(self.h)
        self.buf = np.zeros(self.M)  # ring buffer for the delay line
        self.offset = 0  #next sample space

    def store(self, v): # write v over the oldest sample and move the offset on
        n = self.offset
        self.buf[n] = v
        self.offset = (n + 1) % self.M
        return n

    def halves(self, n): # makes sure buffer keeps order
        return (self.h[:n + 1], self.buf[n::-1]), (self.h[n + 1:], self.buf[:n:-1])

    def dofilter(self, v):
        (h1, x1), (h2, x2) = self.halves(self.store(v))
        return np.dot(h1, x1) + np.dot(h2, x2)

    def doFilterAdaptive(self, signal, noise, learningRate):
        (h1, x1), (h2, x2) = self.halves(self.store(noise))
        e = signal - (np.dot(h1, x1) + np.dot(h2, x2))  # error for LMS
        h1 += learningRate * e * x1
        h2 += learningRate * e * x2
        return e
