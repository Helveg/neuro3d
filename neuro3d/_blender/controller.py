try:
    import bpy
    import bpy.types
except ImportError:
    raise ImportError("`neuro3d._blender` can only be imported inside Blender.") from None

from .curve_container import CurveContainer, _get_curve_template, _get_default_color
from neuro3d.backend import Controller
from neuro3d.exceptions import *
import warnings, functools, pickle, base64, numpy as np


def _load(obj):
    return pickle.loads(base64.b64decode(obj))


def _dump(obj):
    return base64.b64encode(pickle.dumps(obj)).decode("utf8")


def _append_material(obj, color=None):
    mat = bpy.data.materials.new(obj.name)
    mat.diffuse_color = color or (1, 1, 1, 1)
    obj.materials.append(mat)


def _create_curve(name, splines=None, color=None, type="CURVE", spline_type=None, **spline_kwargs):
    curve = bpy.data.curves.new(name, type=type)
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = 0.01
    _append_material(curve, color)
    if spline_type is not None:
        spline_kwargs["type"] = spline_type
    for data in splines or ():
        _create_spline(curve, *data, **spline_kwargs)
    return curve


def _create_spline(curve, nurbs, radii, type="POLY"):
    line = curve.splines.new(type)
    line.points.add(len(nurbs) - 1)
    line.points.foreach_set("radius", radii)
    line.points.foreach_set("co", nurbs.ravel())

class SceneState:
    def __new__(cls, scene=None):
        if scene and scene.neuro3d.pickle:
            return _load(scene.neuro3d.pickle)
        else:
            return super().__new__(cls)

    def __init__(self, scene):
        self._scene = scene
        # If `_objects` is already set then we were loaded from a pickle
        if getattr(self, "_objects", False):
            self._objects = dict()
            for k,v in self._objects.items():
                try:
                    self._objects[k] = self._obj_from_pickle(v)
                except KeyError:
                    warnings.warn(f"Couldn't find obj {k} '{v}'.")
                    continue
            self._next_object_id = max(self._objects.keys(), default=0) + 1
        else:
            self._objects = {}
            self._next_object_id = 0

    def _obj_from_pickle(self, name):
        if name.startswith("::"):
            name = name[2:]
            parent = self._scene.collection.children
        else:
            parent = self._scene.collection.objects
        return BlenderController.get_n3d(parent[name])


    def _save(self):
        self._scene.neuro3d.pickle = _dump(self)

    def __getstate__(self):
        state = {k: v for k, v in self.__dict__.items() if k not in ("_objects", "_scene")}
        obj_state = {}
        for k, o in list(self._objects.items()):
            try:
                o._backend_obj["_n3d_pickle"] = _dump(o)
            except ReferenceError:
                # Object has been removed, don't store it.
                del self._objects[k]
                continue
            else:
                name = o._backend_obj.name
                if isinstance(o._backend_obj, bpy.types.Collection):
                    name = "::" + name
                obj_state[k] = name
        state["_objects"] = obj_state
        return state


class BlenderController(Controller):
    @property
    @functools.lru_cache()
    def state(self):
        return SceneState(self.scene)

    @property
    @functools.lru_cache()
    def scene(self):
        return bpy.context.scene

    def find(self, id):
        if id not in self.state._objects:
            raise IdMissingError("id %id% is not registered.", id)
        return self.state._objects[id]

    def register_object(self, obj, id=None):
        if id is None:
            id = self.state._next_object_id
            self.state._objects[id] = obj
            self.state._next_object_id += 1
        elif id in self.state._objects:
            obj = self.state._objects[id]
            raise IdTakenError("%id% is already taken by %obj%", id, obj)
        else:
            self.state._objects[id] = obj
            self.state._next_object_id = max(self.state._next_object_id, id + 1)
        obj._id = id
        return id

    def create_cell(self, cell):
        cc = self._create_curve_container(cell)
        _init_pos, _init_rot = cell.location, cell.rotation
        cell._backend_obj = cc._backend_obj
        cell.curve_container = cc
        # Trigger cell properties now that the curve container is available.
        cell.location = _init_pos
        cell.rotation = _init_rot

    def create_plot(self, plot):
        coll = self._create_collection(plot)
        self.scene.collection.children.link(coll)
        frame = self._create_plot_frame(plot)
        coll.objects.link(frame)

    def _create_collection(self, obj):
        obj._backend_obj = c = bpy.data.collections.new(self.get_blender_name(obj))
        return c

    def _create_plot_frame(self, plot):
        frame_nurbs = np.column_stack((np.tile(plot._origin, (3, 1)), np.ones(3)))
        frame_nurbs[0, 1] += plot._scale[1]
        frame_nurbs[2, 0] += plot._scale[0]
        name = self.get_blender_name(plot) + "_frame"
        curve = _create_curve(name, color=(1, 0, 0, 1), splines=((frame_nurbs, [25] * 3),))
        return bpy.data.objects.new(name, curve)

    def get_rotation(self, obj):
        return obj._backend_obj.rotation_euler

    def set_rotation(self, obj, rotation):
        obj._backend_obj.rotation_euler = rotation

    def get_location(self, obj):
        return obj._backend_obj.location

    def set_location(self, obj, location):
        obj._backend_obj.location = location

    def _create_curve_container(self, cell):
        name = self.get_blender_name(cell)
        return CurveContainer(
            cell, _get_curve_template(name), True, _get_default_color(name), 1.0
        )

    def get_blender_name(self, obj):
        try:
            return "n3d_obj_" + str(obj._id)
        except:
            raise ValueError(f"Could not determine blender object name of '{obj}'.")

    def camera_fit_cells(self, camera, cells):
        camera.data.clip_end = 1000000
        camera.rotation_euler = [0, 0, 0]

    @staticmethod
    def get_n3d(obj):
        n3d_object = _load(obj["_n3d_pickle"])
        n3d_object._backend_obj = obj
        return n3d_object

    def create_scatter(self, scatter, signal, time):
        name = self.get_blender_name(scatter._plot) + f"_trace_{len(scatter._plot._traces)}"
        # Get the coordinates of the scatter on the first frame
        phases = _sc_frame_phases(scatter, points, times, frame)
        coords = _sc_frame_to_coords(scatter, signal, time.as_array(copy=False), scatter._plot._window._f0, phases=phases)
        curve = _create_curve(
            name,
            splines=(
                (
                    np.column_stack((coords, np.ones(len(coords)))),
                    [40] * len(coords)
                ),
            )
        )
        obj = bpy.data.objects.new(name, curve)
        scatter._plot._backend_obj.objects.link(obj)


def _sc_frame_phases(scatter, points, times, fn):
    f0 = scatter._plot._window._f0
    t0 = scatter._plot._window._t0
    st = scatter._plot._image[0]
    a = scatter._plot._window._a
    wf = st * 2 * a
    f = np.vectorize(lambda t: int(round((t - t0) * a) + f0), otypes=[int])

    eb = f(times - st)
    fases = np.ones(eb.shape, dtype=int) * -1
    if4 = np.empty(eb.shape, dtype=bool)
    if0 = np.empty(eb.shape, dtype=bool)

    if4[:-1] = eb[1:] + wf <= fn
    if4[-1] = if4[-2]
    fases[if4] = 4
    if3 = ~if4 & (eb + wf <= fn)
    fases[if3] = 3
    if2 = (eb <= fn) & (eb + wf > fn)
    fases[if2] = 2
    if0[1:] = eb[:-1] > fn
    if0[0] = if0[1]
    fases[if0] = 0
    if1 = ~if0 & (eb >= fn)
    fases[if1] = 1
    return fases

def _sc_frame_to_coords(scatter, points, times, frame, phases=None):
    if phases is None:
        phases = _sc_frame_phases(scatter, points, times, frame)
    coords = np.empty((len(points), 3))
    coords[:, 2] = scatter._plot._origin[2]
    ox = scatter._plot._origin[0]
    sx = scatter._plot._scale[0]
    st = scatter._plot._image[0]
    a = scatter._plot._window._a
    oy = scatter._plot._origin[1]
    sy = scatter._plot._scale[1]
    sv = scatter._plot._image[1]
    f0 = scatter._plot._window._f0
    t0 = scatter._plot._window._t0
    f = np.vectorize(lambda t: int(round((t - t0) * a) + f0), otypes=[int])
    t = np.vectorize(lambda f: t0 + (f + f0) / a, otypes=[float])
    y = np.vectorize(lambda v: oy + v / sv * sy, otypes=[float])
    x = np.vectorize(lambda w: ox + sx / 2 + (w - t0) / (2 * st) * sx, otypes=[float])
    coords[phases < 2, 0] = ox + sx
    coords[phases > 2, 0] = ox
    coords[phases == 2, 0] = x(times[phases == 2] - t(frame))
    coords[phases == 0, 1] = y(points.take(np.nonzero(phases == 0)[0] - 1, mode='clip'))
    coords[phases == 1, 1] = y(np.interp(t0 + st, times - t(frame), points))
    coords[phases == 2, 1] = y(points[phases == 2])
    coords[phases == 3, 1] = y(np.interp(t0 - st, times - t(frame), points))
    coords[phases == 4, 1] = y(points.take(np.nonzero(phases == 4)[0] + 1, mode='clip'))
    return coords
