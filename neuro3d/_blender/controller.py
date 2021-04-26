try:
    import bpy
except ImportError:
    raise ImportError("`neuro3d._blender` can only be imported inside Blender.") from None

from .curve_container import CurveContainer, _get_curve_template, _get_default_color
from neuro3d.backend import Controller
import functools, pickle, base64


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
            self._objects = {k: BlenderController.get_n3d(self._scene.objects[v]) for k, v in self._objects.items()}
            self._next_object_id = max(self._objects.keys(), default=0) + 1
        else:
            self._objects = {}
            self._next_object_id = 0

    def _save(self):
        print("State being saved")
        self._scene.neuro3d.pickle = _dump(self)

    def __getstate__(self):
        state = {k: v for k, v in self.__dict__.items() if k not in ("_objects", "_scene")}
        obj_state = {}
        for k, o in self._objects.items():
            o._backend_obj["_n3d_pickle"] = _dump(o)
            obj_state[k] = o._backend_obj.name
        state["_objects"] = obj_state
        print("Obj stored:", state)
        return state


class BlenderController(Controller):
    @property
    @functools.lru_cache()
    def state(self):
        return SceneState(bpy.context.scene)

    def register_object(self, obj):
        id = self.state._next_object_id
        self.state._objects[id] = obj
        self.state._next_object_id += 1
        return id

    def create_cell(self, cell):
        id = self.register_object(cell)
        cell._id = id
        cc = self._create_curve_container(cell)
        _init_pos, _init_rot = cell.location, cell.rotation
        cell._backend_obj = cc._backend_obj
        cell.curve_container = cc
        # Trigger cell properties now that the curve container is available.
        cell.location = _init_pos
        cell.rotation = _init_rot

    def register_plot(self, plot):
        id = self.register_object(plot)
        plot._id = id
        cc = self._create_curve_container(cell)
        _init_pos, _init_rot = cell.location, cell.rotation
        cell.curve_container = cc
        # Trigger cell properties now that the curve container is available.
        cell.location = _init_pos
        cell.rotation = _init_rot

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
