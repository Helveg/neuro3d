__version__ = "0.0.4"

import warnings
import numpy as np
from .backend import establish_backends, get_backend, RequiresSupport
from .exceptions import *

print("Checking backends")
establish_backends()
print("Back from backends")

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


_startup_backend = get_backend()
controller = _startup_backend.get_controller()

from . import animation
from .render import render
from .backend import set_backend
from .animation import encoders
from .animation.frames import FrameWindow, time, rtime

class HasBackendObject:
    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if k != "_backend_obj"}

class Branch(RequiresSupport, requires=[]):
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


class Cell(RequiresSupport, HasBackendObject, requires=["create_cell", "get_location", "set_location", "get_rotation", "set_rotation"]):
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

    def __getstate__(self):
        return dict()

    def register(self):
        """
        Register the cell with the controller to create its Blender object and manage its
        state. Only available inside Blender.
        """
        controller.create_cell(self)

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
