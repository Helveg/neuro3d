import sys


def patch_original(version, addon, controller):
    if version[0] == 2 and version[1] < 80:
        raise NotImplementedError("Blender versions before 2.8 are not supported")
