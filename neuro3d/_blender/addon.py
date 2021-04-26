import bpy

from bpy.props import (
    StringProperty,
    PointerProperty,
)
from bpy.types import (
    PropertyGroup,
)


@bpy.app.handlers.persistent
def save_state(_):
    from .. import controller

    controller.state._save()


class StatePickle(PropertyGroup):

    pickle: StringProperty(
        name="state",
        description="All the state Neuro3D needs to save in the Blend file",
        default=""
    )


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (StatePickle,)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    print("Added save handler")
    bpy.app.handlers.save_pre.append(save_state)
    bpy.types.Scene.neuro3d = PointerProperty(type=StatePickle)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    bpy.app.handlers.save_pre.remove(save_state)
    del bpy.types.Scene.neuro3d

#
#
# # ------------------------------------------------------------------------
# #    Operators
# # ------------------------------------------------------------------------
#
#
# class WM_OT_HelloWorld(Operator):
#     bl_label = "Print Values Operator"
#     bl_idname = "wm.hello_world"
#
#     def execute(self, context):
#         scene = context.scene
#         mytool = scene.my_tool
#
#         # print the values to the console
#         print("Hello World")
#         print("bool state:", mytool.my_bool)
#         print("int value:", mytool.my_int)
#         print("float value:", mytool.my_float)
#         print("string value:", mytool.my_string)
#         print("enum state:", mytool.my_enum)
#
#         return {"FINISHED"}
#
#
# # ------------------------------------------------------------------------
# #    Menus
# # ------------------------------------------------------------------------
#
#
# class OBJECT_MT_CustomMenu(bpy.types.Menu):
#     bl_label = "Select"
#     bl_idname = "OBJECT_MT_custom_menu"
#
#     def draw(self, context):
#         layout = self.layout
#
#         # Built-in operators
#         layout.operator(
#             "object.select_all", text="Select/Deselect All"
#         ).action = "TOGGLE"
#         layout.operator("object.select_all", text="Inverse").action = "INVERT"
#         layout.operator("object.select_random", text="Random")
#
#
# # ------------------------------------------------------------------------
# #    Panel in Object Mode
# # ------------------------------------------------------------------------
#
#
# class OBJECT_PT_CustomPanel(Panel):
#     bl_label = "My Panel"
#     bl_idname = "OBJECT_PT_custom_panel"
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "UI"
#     bl_category = "Neuro3D"
#
#     def draw(self, context):
#         layout = self.layout
#         scene = context.scene
#         mytool = scene.my_tool
#
#         layout.prop(mytool, "my_bool")
#         layout.prop(mytool, "my_enum", text="")
#         layout.prop(mytool, "my_int")
#         layout.prop(mytool, "my_float")
#         layout.prop(mytool, "my_float_vector", text="")
#         layout.prop(mytool, "my_string")
#         layout.prop(mytool, "my_path")
#         layout.operator("wm.hello_world")
#         layout.menu(OBJECT_MT_CustomMenu.bl_idname, text="Presets", icon="SCENE")
#         layout.separator()
