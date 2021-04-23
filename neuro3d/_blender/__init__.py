def get_blender_version():
    try:
        import bpy
    except:
        raise ImportError("`neuro3d._blender` can only be imported inside Blender.")
    try:
        return bpy.app.version_string.split(".")
    except:
        raise RuntimeError("Blender version could not be determined.")


def make_blender_addon():
    import sys
    from . import patches, addon

    version = get_blender_version()
    for name, patch in patches.__dict__.items():
        if name.startswith("patch_"):
            patch(version, addon)

    # Explicitly return the object put into `sys.modules` as if executing
    # `import addon`
    return sys.modules[addon.__name__]
