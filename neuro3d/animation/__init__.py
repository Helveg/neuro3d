from . import encoders, frames, properties


class CalibrationNotSupportedError(Exception):
    pass


class Animator:
    def __init__(self, encoder, property):
        self._encoder = encoder
        self._property = property

    def animate(self, bn_obj, frame_window, signal, time):
        key_frames = frames.KeyFrames(*self._encoder.encode(signal, time))
        for frame, value in frame_window.iterate_keyframes(key_frames):
            self._property.keyframe_insert(bn_obj, frame, value)


def create_window(*args, **kwargs):
    return frames.FrameWindow(*args, **kwargs)


def create_animator(encoder=None, property=None, **kwargs):
    if encoder is None:
        encoder = encoders.NormEncoder()
    if property is None:
        property = properties.EmissionProperty()
    return Animator(encoder, property, **kwargs)
