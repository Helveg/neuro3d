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
    print("Dumping", obj)
    return base64.b64encode(pickle.dumps(obj)).decode("utf8")


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
            print("Objs from pickle?")
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
        print("State being saved")
        self._scene.neuro3d.pickle = _dump(self)

    def __getstate__(self):
        state = {k: v for k, v in self.__dict__.items() if k not in ("_objects", "_scene")}
        obj_state = {}
        for k, o in self._objects.items():
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
        print("Obj stored:", state)
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
        return id

    def create_cell(self, id, cell):
        self.register_object(cell, id)
        cell._id = id
        cc = self._create_curve_container(cell)
        _init_pos, _init_rot = cell.location, cell.rotation
        cell._backend_obj = cc._backend_obj
        cell.curve_container = cc
        # Trigger cell properties now that the curve container is available.
        cell.location = _init_pos
        cell.rotation = _init_rot

    def create_plot(self, id, plot):
        self.register_object(plot, id)
        plot._id = id
        coll = self._create_collection(plot)
        self.scene.collection.children.link(coll)
        frame = self._plot_frame(plot)
        coll.objects.link(frame)

    def _create_collection(self, obj):
        obj._backend_obj = c = bpy.data.collections.new(self.get_name(obj))
        return c

    def _plot_frame(self, plot):
        curve = bpy.data.curves.new(self.get_name(plot) + "_frame", type="CURVE")
        mat = bpy.data.materials.new(self.get_name(plot) + "_frame")
        mat.diffuse_color = (1, 0, 0, 1)
        curve.materials.append(mat)
        curve.dimensions = '3D'
        curve.resolution_u = 2
        curve.bevel_depth = 0.01
        line = curve.splines.new('POLY')
        line.points.add(2)
        line.points.foreach_set("radius", [25] * 3)
        o = np.concatenate((plot._origin, [1]))
        line.points[0].co = o + [plot._scale[0], 0, 0, 0]
        line.points[1].co = o
        line.points[2].co = o + [0, plot._scale[1], 0, 0]
        obj = bpy.data.objects.new(self.get_name(plot) + "_frame", curve)
        return obj

    def get_rotation(self, obj):
        return obj._backend_obj.rotation_euler

    def set_rotation(self, obj, rotation):
        obj._backend_obj.rotation_euler = rotation

    def get_location(self, obj):
        return obj._backend_obj.location

    def set_location(self, obj, location):
        obj._backend_obj.location = location

    def _create_curve_container(self, cell):
        name = self.get_name(cell)
        return CurveContainer(
            cell, _get_curve_template(name), True, _get_default_color(name), 1.0
        )

    def get_name(self, obj):
        try:
            return "bn_obj_" + str(obj._id)
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
