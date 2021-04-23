from ..render import BackendRender

class BlenderRender(BackendRender):
    def render_portion(self, rank, size):
        import os

        os.system(f"blender -b {self.file} -E BLENDER_EEVEE -s {rank + 1} -j {size} -o //render/animation_####.png -a")
