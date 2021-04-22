import numpy as np, math, abc


class TimeInfoError(Exception):
    pass


class KeyFrames:
    def __init__(self, signal, time):
        self._signal = signal
        self._time = time

    @property
    def signal(self):
        return self._signal.copy()

    @signal.setter
    def signal(self, value):
        if len(value) != len(self._signal):
            raise ValueError(
                "Can only assign KeyFrame signals when number of frames is the same."
            )
        self._signal = np.array(value)

    @property
    def time(self):
        return self._time.copy()


class FrameWindow:
    def __init__(self, f_start, f_stop, t_start, t_stop):
        self._t0 = t_start
        self._tn = t_stop
        self._f0 = f_start
        self._fn = f_stop
        self._a = (self._fn - self._f0) / (self._tn - self._t0)

    def iterate_keyframes(self, keyframes):
        yield from zip(map(self.get_frame, keyframes._time), keyframes._signal)

    def get_total_frames(self):
        return math.floor((self._tn - self._t0) * self._fps)

    def get_frame(self, t):
        return int(self._f0 + (t - self._t0) * self._a)


class TimeSignal:
    """
    Class for optimized handling of time signals in time series. Represent many
    simulation signals with just 1 shared underlying array, or even replace the
    array by a simplified constant memory data structure like the
    :class:`.frames.PeriodicTimeSignal`
    """
    def __init__(self, signal, mask=None, copy=False):
        self.signal = signal.copy() if copy else signal
        self._mask = mask

    def __iter__(self):
        return iter(self.signal)

    def __getitem__(self, slice):
        if self._mask is None:
            return self.signal[slice]
        else:
            return self.signal[self._mask][slice]

    def as_array(self, copy=True):
        if self._mask is None:
            return self.signal.copy() if copy else self.signal
        else:
            return self.signal[self._mask]

    def window(self, start, stop, copy=False):
        mask = (self.signal >= start) & (self.signal <= stop)
        return TimeSignal(self.signal, mask, copy)

    def as_mask(self):
        if self._mask is not None:
            return self._mask
        else:
            return np.ones(self.signal.shape, dtype=bool)


class PeriodicTimeSignal(TimeSignal):
    def __init__(self, start, stop, dt):
        self.start = start
        self.stop = stop
        self.dt = dt

    def __iter__(self):
        r = self.start
        while r <= self.stop:
            r += self.dt
            yield r

    def as_array(self):
        return np.fromiter(self, dtype=float)

    def window(self, start, stop):
        self.start = start
        self.stop = stop
        return self


def time(signal):
    return TimeSignal(signal)


def rtime(start, stop, dt):
    return PeriodicTimeSignal(start, stop, dt)
