#!/usr/bin/env python3

import os, sys, shutil, urllib.request, time

if "--local" in sys.argv:
    print("Installing local Neuro3D Blender addon.")
    shutil.make_archive("neuro3d", 'zip', ".", "neuro3d")
else:
    print("Downloading Neuro3D Blender addon.")
    archive = "https://github.com/Helveg/neuro3d/releases/latest/download/neuro3d.zip"
    with urllib.request.urlopen(archive) as w:
        with open("neuro3d.zip", 'wb') as f:
            f.write(w.read())
try:
    with open("_tmp_n3d_blenderinstall.py", "w") as f:
        f.write("""
import bpy, os

bpy.ops.preferences.addon_install(
    filepath=os.path.abspath("neuro3d.zip"), overwrite=True
)
bpy.ops.preferences.addon_enable(module="neuro3d")
bpy.ops.wm.save_userpref()
""")
    try:
        print("Launching Blender, installing zip.")
        os.system(f"blender --background --python _tmp_n3d_blenderinstall.py")
    finally:
        os.remove("_tmp_n3d_blenderinstall.py")
finally:
    os.remove("neuro3d.zip")
