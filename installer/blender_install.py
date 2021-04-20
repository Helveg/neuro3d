import bpy, os

print("Hello there", os.getcwd(), os.path.exists("neuro3d.zip"))
bpy.ops.preferences.addon_install(filepath='neuro3d.zip', overwrite=True)
# bpy.ops.preferences.addon_enable(module='neuro3d')
# bpy.ops.wm.save_userpref()
