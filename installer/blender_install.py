import bpy, os

bpy.ops.preferences.addon_install(
    filepath=os.path.abspath("neuro3d.zip"), overwrite=True
)
bpy.ops.preferences.addon_enable(module="neuro3d")
bpy.ops.wm.save_userpref()
