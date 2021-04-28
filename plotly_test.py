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
                        args=[None, {"frame": {"duration": 200}, "transtion": {"duration": 0}}]
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
    points = np.array(points)
    times = np.array(times)
    ox = plot._origin[0]
    sx = plot._scale[0]
    ft = plot._window._ft
    fn = plot._window._fn
    st = plot._image[0]
    a = plot._window._a
    wf = st * 2 * a
    print(wf)
    oy = plot._origin[1]
    sy = plot._scale[1]
    sv = plot._image[1]
    f0 = plot._window._f0
    t0 = plot._window._t0
    rbx = ox + sx
    f = np.vectorize(lambda t: int(round((t - t0) * a) + f0), otypes=[int])
    t = np.vectorize(lambda f: t0 + (f + f0) / a, otypes=[float])
    y = np.vectorize(lambda v: oy + v / sv * sy, otypes=[float])
    x = np.vectorize(lambda w: ox + sx / 2 + (w - t0) / (2 * st) * sx, otypes=[float])
    eb = np.fromiter((f(t - st) for t in times), dtype=int)
    # print("event base:", eb)
    # visibility = [[0, 'rgba(255, 0, 0, 1)'], [1.0, 'rgba(255, 0, 0, 0)']]
    def animate_frame(fn):
        frame_x = np.empty(eb.shape)
        frame_y = np.empty(eb.shape)
        fases = np.ones(eb.shape) * -1
        if4 = np.empty(eb.shape, dtype=bool)
        if0 = np.empty(eb.shape, dtype=bool)
        # Mask of points initially in fase 4 (located to the left of window)
        if4[:-1] = eb[1:] + wf < fn
        # Endpoint has no y4 transition, use previous point y4 transition
        if4[-1] = if4[-2]
        fases[if4] = 4
        if3 = ~if4 & (eb + wf < fn)
        fases[if3] = 3
        # print("fase 3 or 4", eb + wf <= fn)
        if0[1:] = eb[:-1] > fn
        # Startpoint has no y1 transition, use next point y1 transition
        if0[0] = if0[1]
        fases[if0] = 0
        if1 = ~if0 & (eb >= fn)
        fases[if1] = 1
        if2 = (eb < fn) & (eb + wf >= fn)
        fases[if2] = 2
        frame_x[fases < 2] = ox + sx
        frame_x[fases > 2] = ox
        frame_x[fases == 2] = x(times[fases == 2] - t(fn))
        # print("zero phase waiting points:", np.nonzero(fases == 0)[0] - 1, points, points.take(np.nonzero(fases == 0)[0] - 1, mode='clip'))
        frame_y[fases == 0] = y(points.take(np.nonzero(fases == 0)[0] - 1, mode='clip'))
        frame_y[fases == 1] = y(np.interp(t0 + st, times - t(fn), points))
        frame_y[fases == 2] = y(points[fases == 2])
        frame_y[fases == 3] = y(np.interp(t0 - st, times - t(fn), points))
        frame_y[fases == 4] = y(points.take(np.nonzero(fases == 4)[0] + 1, mode='clip'))
        # print(" ------ Frame report:", f0)
        # print("fases", fases)
        # print(frame_x)
        # print(frame_y)
        # print(points, y(points))
        # exit()
        return frame_x, frame_y

    def get_initial_phases(points, times):
        f0 = plot._window._f0
        st = plot._image[0]
        a = plot._window._a
        wf = st * 2 * a
        f = np.vectorize(lambda t: int(round((t - t0) * a) + f0), otypes=[int])

        eb = f(times - st)
        fases = np.ones(eb.shape) * -1
        if4 = np.empty(eb.shape, dtype=bool)
        if0 = np.empty(eb.shape, dtype=bool)

        if4[:-1] = eb[1:] + wf <= f0
        if4[-1] = if4[-2]
        fases[if4] = 4
        if3 = ~if4 & (eb + wf <= f0)
        fases[if3] = 3
        if2 = (eb <= f0) & (eb + wf > f0)
        fases[if2] = 2
        if0[1:] = eb[:-1] > f0
        if0[0] = if0[1]
        fases[if0] = 0
        if1 = ~if0 & (eb >= f0)
        fases[if1] = 1
        return fases

    print(get_initial_phases(points, times))
    frame_data = [animate_frame(f) for f in range(f0, fn + 1)]
    frames = [
        go.Frame(
            data=[
                go.Scatter(x=[ox, ox, ox + sx], y=[oy + sy, oy, oy], name="frame"),
                go.Scatter(x=[ox + sx / 2] * 2, y=[oy, oy + sy], name="t"),
                go.Scatter(x=frame_x, y=frame_y, name="frame_curve"),
                go.Scatter(x=x(times - t(fn)), y=y(points), name="full curve"),
            ],
            layout=go.Layout(
                # xaxis=dict(
                #     tickmode = "array",
                #     tickvals = [ox, ox + sx / 2, ox + sx],
                #     ticktext = [round(t(fn) - st, 5), round(t(f0 + fn), 5), round(t(fn) + st, 5)],
                # ),
                title=f"Sliding plot #{fn} ({round(float(t(fn)), 4)})",
            )
        )
        for fn, (frame_x, frame_y) in enumerate(frame_data)
    ]
    return frames

# origin, scale, image_scale, frame_window
plot = Plot([10, 0, 0], [100, 100, 0], [1, 50], FrameWindow(0, 100, 0, 2))
plot_frames(plot, [1, 10, 2, 5, 15, 3], [-2, -1.01, -0.0, 1.1, 1.18, 1.2])
