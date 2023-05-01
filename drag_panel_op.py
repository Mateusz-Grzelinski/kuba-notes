import bpy

from bpy.types import Operator

from .bl_ui_widgets.bl_ui_label import *
from .bl_ui_widgets.bl_ui_button import *
from .bl_ui_widgets.bl_ui_checkbox import *
from .bl_ui_widgets.bl_ui_slider import *
from .bl_ui_widgets.bl_ui_up_down import *
from .bl_ui_widgets.bl_ui_drag_panel import *
from .bl_ui_widgets.bl_ui_draw_op import *

called = {}


class KUBA_OT_draw_operator(BL_UI_OT_draw_operator):
    bl_idname = "object.kuba_draw"
    bl_label = "bl ui widgets custom operator"
    bl_description = "Kuba notes button"
    bl_options = {"REGISTER"}

    object_name: bpy.props.StringProperty(name="object_name")

    _instances = dict()

    @classmethod
    def is_running(
        cls, context: bpy.types.Context, obj_name=""
    ) -> "KUBA_OT_draw_operator":
        area = context.area
        if area.type == "VIEW_3D":
            return cls._instances.get((hash(area), obj_name))
        else:
            print("Invalid area type!")
            return None

    def __init__(self):
        super().__init__()

        self.panel = BL_UI_Drag_Panel(x=100, y=50, width=300, height=50)
        self.panel.bg_color = (0.2, 0.2, 0.2, 0.7)

        # self.label = BL_UI_Label(20, 10, 100, 15)
        # self.label.text = "Go to:"
        # self.label.text_size = 14
        # self.label.text_color = (0.2, 0.9, 0.9, 1.0)

        self.button1 = BL_UI_Button(20, 10, 260, 30)
        self.button1.bg_color = (0.1, 0.6, 0.6, 0.8)
        self.hover_bg_color_backup = (0.1, 0.7, 0.7, 1.0)
        self.button1.text = "Go to url"
        # self.button1.set_image("//img/scale_24.png")
        # self.button1.set_image_size((24,24))
        self.button1.set_image_position((4, 2))
        self.button1.set_mouse_down(self.button1_press)

        # todo check if it is safe:
        self.ob = None

    def on_invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # Add new widgets here (TODO: perhaps a better, more automated solution?)
        if self.object_name:
            ob = bpy.data.objects[self.object_name]
        else:
            ob = context.active_object
        KUBA_OT_draw_operator._instances[(hash(context.area), ob.name)] = self
        self.ob = ob
        self.button1.hover_bg_color = (
            self.hover_bg_color_backup if not ob.www else self.button1.bg_color
        )
        appendix = "" if len(ob.www) < 10 else "..."
        self.button1.text = f"Go to: {ob.www[:10]}" + appendix

        widgets_panel = [self.button1]
        widgets = [self.panel, *widgets_panel]

        self.init_widgets(context, widgets)

        self.panel.add_widgets(widgets_panel)

        # Open the panel at the mouse location
        self.panel.set_location(event.mouse_x, context.area.height - event.mouse_y + 20)

    # Button press handlers
    def button1_press(self, widget):
        if self.ob.www:
            bpy.ops.wm.url_open("INVOKE_DEFAULT", url=self.www)
        print("Button '{0}' is pressed".format(widget.text))

    def on_finish(self, context):
        del KUBA_OT_draw_operator._instances[(hash(context.area), self.ob.name)]
        return super().on_finish(context)


def register():
    bpy.utils.register_class(KUBA_OT_draw_operator)


def unregister():
    bpy.utils.unregister_class(KUBA_OT_draw_operator)
