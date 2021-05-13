import abc
import numpy as np
from . import frames

class Encoder(abc.ABC):
    def __init_subclass__(cls, operator=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if operator is not None:
            def op(*args, **kwargs):
                return cls(*args, **kwargs)

            op.__name__ = operator
            op.__qualname__ = operator
            op.__doc__ = cls.__doc__
            globals()[operator] = op

    @abc.abstractmethod
    def encode(self, signal, time):
        pass

    def pipe(self, *encoders):
        return PipeEncoder(self, *encoders)

    @classmethod
    def calibrate(cls, *args, **kwargs):
        raise NotImplementedError(f"{cls.__name__} does not support calibration.")


class PipeEncoder(Encoder, operator="pipe"):
    def __init__(self, *encoders):
        self._pipe = encoders

    def encode(self, signal, time):
        for encoder in self._pipe:
            signal, time = encoder.encode(signal, time)
        return signal, time


class NormEncoder(Encoder, operator="norm"):
    def __init__(self, min=0, max=1):
        self._min = min
        self._max = max

    def encode(self, signal, time):
        signal = np.array(signal, dtype=float)
        # Normalize to calibration or to signal if not calibrated
        signal -= min(signal) if self._cmin is None else self._cmin
        m = max(signal) if self._cmax is None else self._cmax
        if m != 0:
            signal /= m
        if self._min != 0:
            signal += self._min
        if self._max != 1:
            signal *= self._max
        return signal, time

    def calibrate(self, min, max):
        self._cmin = min
        self._cmax = max


class InspectEncoder(Encoder, operator="tap"):
    def __init__(self, f):
        self._f = f

    def encode(self, signal, time):
        f(signal, time)
        return signal, time


class StdDevEncoder(Encoder, operator="stdev"):
    def __init__(self, mean=1.0, scale=1.0):
        self._mean = mean
        self._scale = scale
        self._cmean = None
        self._cstd = None

    def encode(self, signal, time):
        stdev = np.std(signal) if self._cstd is None else self._cstd
        mean = np.mean(signal) if self._cmean is None else self._cmean
        signal = self._mean + (signal - mean) * self._scale / stdev
        return signal, time

    def calibrate(self, mean, stdev):
        self._cmean = mean
        self._cstd = stdev


class SumEncoder(Encoder, operator="plus"):
    def __init__(self, scalar):
        self._scalar = scalar

    def encode(self, signal, time):
        signal += self._scalar
        return signal, time


class MultEncoder(Encoder, operator="mult"):
    def __init__(self, scalar):
        self._scalar = scalar

    def encode(self, signal, time):
        signal *= self._scalar
        return signal, time


class SqrtEncoder(Encoder, operator="sqrt"):
    def __init__(self, min=None, max=None):
        self._min = min
        self._max = max

    def encode(self, signal, time):
        signal = np.sqrt(signal)
        return signal, time


class ClipEncoder(Encoder, operator="clip"):
    def __init__(self, min=None, max=None):
        self._min = min
        self._max = max

    def encode(self, signal, time):
        if self._min is not None:
            signal = np.where(signal < self._min, self._min, signal)
        if self._max is not None:
            signal = np.where(signal > self._max, self._max, signal)
        return signal, time


class RDPEncoder(Encoder, operator="rdp"):
    def __init__(self, epsilon=0.0):
        self._epsilon = epsilon

    def encode(self, signal, time):
        if len(signal) == 0:
            return np.zeros(0), np.zeros(0)

        # Make a matrix where times and values are columns
        formatted = np.column_stack((time.as_array(), signal))
        # Run simplification algorithm
        simplified = _rdp(formatted, self._epsilon).T
        # Split the result matrix back to individual times and values columns
        time, signal = simplified[0:2]
        return signal, frames.time(time)


class WindowDecimationEncoder(Encoder, operator="win_decimate"):
    """
    Decimate points that end up in the same frame of a window.

    All points grouped into the same frame of a :class:`.frames.FrameWindow` are
    decimated according to a survivor function, the default survivor function
    picks the ``int(n / 2)``-th element as survivor.
    """
    def __init__(self, window, survivor=None, epsilon=0.0):
        self._window = window
        self._epsilon = epsilon
        if survivor is not None:
            self._survivor = survivor

    def encode(self, signal, time):
        cache = dict()
        # Map the frames of `time` to their indices in `time`
        for s, f in enumerate(map(self._window.get_frame, time)):
            cache.setdefault(f, []).append(s)
        survivors = [self._survivor(s) for s in cache.values()]
        if len(survivors) == len(signal):
            # Prematurely optimized in case nothing gets decimated!
            return signal, time
        else:
            signal = signal[survivors]
            time = frames.time(time.as_array(copy=False)[survivors])
            return signal, time

    def _survivor(self, group):
        return group[int(len(group) / 2)]


# Line simplification algorithm using Numpy from:
# https://github.com/fhirschmann/rdp/issues/7


def _line_dists(points, start, end):
    if np.all(start == end):
        return np.linalg.norm(points - start, axis=1)

    vec = end - start
    cross = np.cross(vec, start - points)
    return np.divide(abs(cross), np.linalg.norm(vec))


def _rdp(M, epsilon=0):
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
