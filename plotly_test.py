import numpy as np
import plotly.graph_objs as go


class Plot:
    def __init__(self, origin, scale, image_scale, frame_window):
        self._origin = np.array(origin)
        self._scale = np.array(scale)
        self._image = np.array(image_scale)
        self._window = frame_window


class FrameWindow:
    def __init__(self, f_start, f_stop, t_start, t_stop):
        self._t0 = t_start
        self._tn = t_stop
        self._tt = t_stop - t_start
        self._f0 = f_start
        self._fn = f_stop
        self._ft = f_stop - f_start
        self._a = self._ft / self._tt

    def iterate_keyframes(self, keyframes):
        yield from zip(map(self.get_frame, keyframes._time), keyframes._signal)

    def get_total_frames(self):
        return math.floor((self._tn - self._t0) * self._fps)

    def get_frame(self, t):
        return int(self._f0 + (t - self._t0) * self._a)


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


def plot_frames(plot, points, times):
    frames = animate_frames(plot, points, times)
    go.Figure(
        data=frames[0].data,
        frames=frames[1:],
        layout=go.Layout(
            title="Sliding plot #0",
            xaxis=frames[0].layout.xaxis,
            updatemenus=[dict(
                type="buttons",
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[None, {"fromcurrent": True}]
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[[None], {
                            "mode": "immediate",
                        }]
                    ),
                ])]
        ),
    ).show()


def animate_frames(plot, points, times):
    ox = plot._origin[0]
    sx = plot._scale[0]
    ft = plot._window._ft
    a = plot._window._a
    wf = sx * 2 * a
    st = plot._image[0]
    oy = plot._origin[1]
    sy = plot._scale[1]
    f0 = plot._window._f0
    t0 = plot._window._t0
    print(a)
    def f(t): return int(round((t - t0) * a) + f0)
    fx1 = np.array([f(t - st) for t in times])
    fx2 = np.array([f(t + st) for t in times])
    fy1 = [0] + fx1[:-1]
    fy2 = fx1.copy()
    fy3 = fx2.copy()
    fy4 = fx2[1:] + [0]
    print("xtr1:", fx1)
    print("xtr2:", fx2)
    print("ytr1:", fy1)
    print("ytr2:", fy2)
    print("ytr3:", fy3)
    print("ytr4:", fy4)
    init_pre = np.nonzero(fx1 > f0)[0]
    init_post = np.nonzero(fx1 + wf < f0)[0]
    init_post_pre = np.nonzero(fx1 > f0)[0]
    init_in = np.nonzero(fx1 > f0)[0]
    init_pre_post = np.nonzero(fx1 + wf < f0)[0]
    print("initial pre-ytr1", init_pre)
    print("initial post-ytr4", init_post)
    exit()
    def fy(y): return 0
    f = go.Frame(
        data=[
            go.Scatter(x=[ox, ox, ox + sx], y=[oy + sy, oy, oy], name="frame"),
            go.Scatter(x=[ox + sx / 2] * 2, y=[oy, oy + sy], name="t"),
            go.Scatter(x=[fx(x) for x in times], y=[fy(y) for y in points], name="curves"),
        ],
        layout=go.Layout(
            xaxis=dict(
                tickmode = "array",
                tickvals = [ox, ox + sx / 2, ox + sx],
                ticktext = [round(t - st, 5), round(t, 5), round(tmm, 5)],
            ),
            title=f"Sliding plot #{frame} ({round(t, 4)})",
        )
    )
    return f

# origin, scale, image_scale, frame_window
plot = Plot([0, 0, 0], [100, 100, 0], [1, 100], FrameWindow(0, 100, 0, 1))
plot_frames(plot, [0, 10], [1.1, 1.12, 1.18, 1.2])
