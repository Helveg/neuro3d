__version__ = "0.0.4"

import warnings
import numpy as np
from .backend import establish_backends, get_backend, BackendObject, RequiresSupport
from .exceptions import *

try:
    import bpy
except:
    inside_blender = False
else:
    inside_blender = True

# `bl_info` is read without evaluating the module. The Neuro3D installer will
# replace the `blender` and `location` key with what is appropriate for the detected
# Blender version so that our addon is compatible across Blender versions.
# `bl_info` needs to be defined at the module-level of the file aswell.
bl_info = {
    "name": "Neuro3D",
    "description": "Visualization of neurons and simulation data",
    "author": "Robin De Schepper",
    "version": (0, 0, 3),
    "blender": (2, 91, 0),
    "location": "View3D > Properties > Neuro3D",
    "wiki_url": "https://neuro3d.readthedocs.io/",
    "tracker_url": "https://github.com/Helveg/Neuro3D/issues",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

if inside_blender:
    from ._blender import make_blender_addon

    addon = make_blender_addon()

    def register():
        addon.register()

    def unregister():
        addon.unregister()

establish_backends()
_startup_backend = get_backend()
controller = _startup_backend.get_controller()

from . import animation
from .render import render
from .backend import set_backend
from .animation import encoders
from .animation.frames import FrameWindow, time, rtime


class Branch(BackendObject, requires=[]):
    """
    A branch is a piece of uninterrupted unbranching cable used to construct
    :class:`cells <.Cell>`.
    """

    def __init__(self, coords, radii, children=None, ref=None):
        """
        Create a branch.

        :param coords: A matrix or list of 3d points describing the branch in space.
        :type coords: np.ndarray (or list of lists-like outside Blender)
        :param children: A collection of branches that are the continuation of this branch
        :type children: list
        :param ref: A reference hash to associate to this object. Can be used to map this
            object to its data source.
        """
        if children is None:
            children = []
        self._children = children
        self._coords = coords
        self._radii = radii
        self._material = None
        self._spline = None
        self._cell = None
        self._ref = ref

    @property
    def children(self):
        """
        The child branches of this branch.
        """
        return self._children

    @property
    def coords(self):
        """
        A list of 3d coordinates that describe this piece of cell morphology
        """
        if self._cell:
            raise NotImplementedError("Reading Blender state not supported yet.")
        else:
            return self._coords

    @coords.setter
    def coords(self):
        if self._cell:
            raise NotImplementedError(
                "Manipulating the Blender object state not supported yet."
            )
        else:
            self._coords = coords

    @property
    def radii(self):
        """
        A list of radii at the 3d points on this branch
        """
        if self._cell:
            raise NotImplementedError("Reading Blender state not supported yet.")
        else:
            return self._radii

    def to_dict(self):
        d = dict(coords=self.coords)
        if self._ref is not None:
            d["ref"] = self.ref
        return d


class Cell(BackendObject, requires=["create_cell", "get_location", "set_location", "get_rotation", "set_rotation"]):
    """
    A cell is the 3D representation of a collection of root :class:`Branches <.Branch>`,
    branching out into child Branches.
    """

    def __init__(self, roots, location=None, rotation=None):
        if location is None:
            location = np.array([0, 0, 0])
        if rotation is None:
            rotation = np.array([0, 0, 0])
        self._roots = roots
        self._location = location
        self._rotation = rotation

    def __register__(self):
        controller.create_cell(self)

    def __getstate__(self):
        return dict()

    @property
    def roots(self):
        """
        A list of 3d coordinates that describe this piece of cell morphology
        """
        return self._roots

    @roots.setter
    def roots(self):
        raise NotImplementedError(
            "Manipulating the Blender object state not supported yet."
        )

    @property
    def branches(self):
        """
        List of :class:`branches <.Branch>` associated with this cell.
        """
        return self.curve_container._branches.copy()

    @branches.setter
    def branches(self):
        raise NotImplementedError(
            "Manipulating the Blender object state not supported yet."
        )

    @property
    def location(self):
        if hasattr(self, "curve_container"):
            return controller.get_location(self.curve_container)
        return self._location

    @location.setter
    def location(self, value):
        if hasattr(self, "curve_container"):
            return controller.set_location(self.curve_container, value)
        self._location = value

    @property
    def rotation(self):
        if hasattr(self, "curve_container"):
            return controller.get_rotation(self.curve_container)
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        if hasattr(self, "curve_container"):
            return controller.set_rotation(self.curve_container, value)
        self._rotation = value


class Plot(BackendObject, requires=["create_plot"]):
    def __init__(self, origin, scale, image_scale, frame_window):
        self._origin = np.array(origin)
        self._scale = np.array(scale)
        self._image = np.array(image_scale)
        self._window = frame_window
        self._traces = []

    def __register__(self):
        controller.create_plot(self)

    def add_trace(self, signal, time):
        self._traces.append(Scatter(self, signal, time))


class Scatter(RequiresSupport, requires=["create_scatter"]):
    def __init__(self, plot, signal, time):
        self._plot = plot
        self._curve = controller.create_scatter(self, signal, time)

def create_branch(*args, **kwargs):
    """
    Create a new :class:`.Branch`.
    """
    return Branch(*args, **kwargs)


def create_cell(roots):
    """
    Create a new :class:`.Cell` from the given roots.

    :param roots: Collection of :class:`Branches <.Branch>` without parents that start a
        branch of the cell morphology.
    :type roots: iterable
    """
    cell = Cell(roots)
    return cell

def require(id):
    def fetch(f):
        try:
            obj = controller.find(id)
        except IdError:
            obj = None
        if obj is None:
            _factorize(f, id)
        return obj

    return fetch


def _factorize(factory, id):
    # `factorize` runs a factory method and will require exactly 1 instance of
    # a child of `BackendObject` to be created during the factory call. Inside
    # the `__new__` call the product will be registered with the controller and
    # if the instance has a registration hook, that will be called as well.
    backend = get_backend()
    controller._factory_id = id
    controller._factory_product = None
    obj = factory(id)
    if controller._factory_product is None:
        warnings.warn("Factory call did not produce a backend object.")
    controller._factory_id = None
    controller._factory_product = None
