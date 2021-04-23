from ..render import BackendRender
from neuro3d.backend import Backend
import functools

class BlenderRender(BackendRender):
    def render_portion(self, rank, size):
        import os

        os.system(f"blender -b {self.file} -E BLENDER_EEVEE -s {rank + 1} -j {size} -o //render/animation_####.png -a")

class BlenderBackend(Backend):
    name = "blender"
    def __init__(self):
        try:
            import bpy
        except ImportError:
            self._inside = False
        else:
            self._inside = True

    def initialize(self):
        pass

    @property
    def available(self):
        return False

    @property
    def priority(self):
        return self._inside

    @functools.lru_cache()
    def get_controller(self):
        if self._inside:
            from .controller import BlenderController

            return BlenderController()
        else:
            raise NotImplementedError("Remote Blender controller not implemented yet.")

    def get_properties(self):
        from . import properties

        return properties
