#!/usr/bin/env python3

import os, sys, shutil, urllib.request, time, argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "-l",
    "--local",
    help="Install local checked out code.",
    action="store_true"
)
parser.add_argument(
    "-v",
    "--version",
    help="Install a specific version.",
    action="store"
)

cl_args = parser.parse_args()

if cl_args.local:
    print("Installing local Neuro3D Blender addon.")
    shutil.make_archive("neuro3d", 'zip', ".", "neuro3d")
else:
    print("Downloading Neuro3D Blender addon.")
    if cl_args.version is None:
        archive = f"https://github.com/Helveg/neuro3d/releases/latest/download/neuro3d.zip"
    else:
        archive = f"https://github.com/Helveg/neuro3d/releases/download/v{version}/neuro3d.zip"
    with urllib.request.urlopen(archive) as w:
        with open("neuro3d.zip", 'wb') as f:
            f.write(w.read())
try:
    with open("_tmp_n3d_blenderinstall.py", "w") as f:
        f.write("""
try:
    import bpy, os

    bpy.ops.preferences.addon_install(
        filepath=os.path.abspath("neuro3d.zip"), overwrite=True
    )
    bpy.ops.preferences.addon_enable(module="neuro3d")
    bpy.ops.wm.save_userpref()
except:
    import sys, traceback

    print(traceback.format_exc(), file=sys.stderr, flush=True)
    exit(1)
""")
    try:
        print("Launching Blender, installing zip.")
        os.system(f"blender --background --python _tmp_n3d_blenderinstall.py")
    finally:
        os.remove("_tmp_n3d_blenderinstall.py")
finally:
    os.remove("neuro3d.zip")
