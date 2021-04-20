import abc
import numpy as np


class Encoder(abc.ABC):
    @abc.abstractmethod
    def encode(self, signal, time=None):
        pass

    def pipe(self, *encoders):
        return PipeEncoder(self, *encoders)

    @classmethod
    def calibrate(cls, *args, **kwargs):
        raise NotImplementedError(f"{cls.__name__} does not support calibration.")


class PipeEncoder(Encoder):
    def __init__(self, *encoders):
        self._pipe = encoders

    def encode(self, signal, time):
        for encoder in self._pipe:
            signal, time = encoder.encode(signal, time)
        return signal, time


class NormEncoder(Encoder):
    def encode(self, signal, time):
        signal = np.array(signal, dtype=float)
        # Normalize to calibration or to signal if not calibrated
        signal -= min(signal) if self._cmin is None else self._cmin
        m = max(signal) if self._cmax is None else self._cmax
        if m != 0:
            signal /= m
        signal += self._min
        signal *= self._max
        return signal, time

    def calibrate(self, min, max):
        self._cmin = min
        self._cmax = max


class StdDevEncoder(Encoder):
    def __init__(self, mean=1.0, scale=1.0):
        self._mean = mean
        self._scale = scale
        self._cmean = None
        self._cstd = None

    def encode(self, signal, time):
        stdev = np.std(signal) if self._cstd is None else self._cstd
        mean = np.mean(signal) if self._cmean is None else self._cmean
        print("cal?", stdev, mean)
        signal = self._mean + (signal - mean) * self._scale / stdev
        print("std enc:", np.min(signal), np.max(signal))
        return signal, time

    def calibrate(self, mean, stdev):
        self._cmean = mean
        self._cstd = stdev


class ClipEncoder(Encoder):
    def __init__(self, min=None, max=None):
        self._min = min
        self._max = max

    def encode(self, signal, time):
        if self._min is not None:
            signal = np.where(signal < self._min, self._min, signal)
        if self._max is not None:
            signal = np.where(signal > self._max, self._max, signal)
        return signal, time


class RDPEncoder(Encoder):
    def __init__(self, epsilon=0.0):
        self._epsilon = epsilon

    def encode(self, signal, time):
        if len(signal) == 0:
            return np.zeros(0), np.zeros(0)
        # Make a matrix where times and values are columns
        formatted = np.column_stack((time, signal))
        # Run simplification algorithm
        simplified = _rdp(formatted, epsilon).T
        # Split the result matrix back to individual times and values columns
        time, signal = simplified[0:2]
        return signal, time


# Line simplification algorithm using Numpy from:
# https://github.com/fhirschmann/rdp/issues/7


def _line_dists(points, start, end):
    if np.all(start == end):
        return np.linalg.norm(points - start, axis=1)

    vec = end - start
    cross = np.cross(vec, start - points)
    return np.divide(abs(cross), np.linalg.norm(vec))


def _rdp(M, epsilon=0):
    M = np.array(M)
    start, end = M[0], M[-1]
    dists = _line_dists(M, start, end)

    index = np.argmax(dists)
    dmax = dists[index]

    if dmax > epsilon:
        result1 = _rdp(M[: index + 1], epsilon)
        result2 = _rdp(M[index:], epsilon)

        result = np.vstack((result1[:-1], result2))
    else:
        result = np.array([start, end])

    return result


# End line simplification
