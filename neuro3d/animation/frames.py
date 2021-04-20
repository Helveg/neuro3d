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
    def __init__(self, t_start, t_stop, dt=0.0001, fps=24, f_start=0):
        self._t0 = t_start
        self._tn = t_stop
        self._dt = dt
        self._fps = fps
        self._spf = 1 / fps
        self._ft = int((t_stop - t_start) * fps)
        self._f0 = f_start

    def iterate_keyframes(self, keyframes):
        yield from zip(map(self.get_frame, keyframes._time), keyframes._signal)

    def get_total_frames(self):
        return math.floor((self._tn - self._t0) * self._fps)

    def get_frame(self, t):
        return self._f0 + (t - self._t0) * self._fps


class TimeSignal:
    def __init__(self, signal):
        self.signal = signal

    def __iter__(self):
        return iter(self.signal)

    def np_arr(self):
        return self.signal.copy()


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

    def np_arr(self):
        return np.fromiter(self, dtype=float)


def time(signal):
    return TimeSignal(signal)


def rtime(start, stop, dt):
    return PeriodicTimeSignal(start, stop, dt)
