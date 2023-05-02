import bpy

from bpy.types import Operator
from bpy_extras import view3d_utils

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
    bl_label = "Kuba notes button"
    bl_options = {"REGISTER"}

    object_name: bpy.props.StringProperty(name="object_name")

    _instances = dict()
    width = 300

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

        self.panel = BL_UI_Drag_Panel(x=00, y=50, width=self.width, height=50)
        self.panel.bg_color = (0.2, 0.2, 0.2, 0.7)

        # self.label = BL_UI_Label(20, 10, 100, 15)
        # self.label.text = "Go to:"
        # self.label.text_size = 14
        # self.label.text_color = (0.2, 0.9, 0.9, 1.0)

        self.button1 = BL_UI_Button(20, 10, 260, 30)
        self.button1.bg_color = (0.6, 0.6, 0.6, 0.8)
        self.hover_bg_color_brighter = (0.7, 0.7, 0.7, 1.0)
        # self.button1.text = "Go to url"
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
            self.hover_bg_color_brighter if ob.www else self.button1.bg_color
        )
        self.extract_button_text()

        widgets_panel = [self.button1]
        widgets = [self.panel, *widgets_panel]

        self.init_widgets(context, widgets)

        self.panel.add_widgets(widgets_panel)

        # Open the panel at the mouse location
        # can be either on cursor location
        # self.panel.set_location(event.mouse_x, context.area.height - event.mouse_y + 20)
        # or pinned to 3d point
        
        region = context.region
        rv3d = context.region_data
        x, y = view3d_utils.location_3d_to_region_2d(region, rv3d, ob.location)
        self.panel.set_location(x=x-self.width/2, y=context.area.height - y)

    def modal(self, context, event):
        # not ideal, but quick to implement:
        if event.type in {"TIMER"} and self.ob:
            region = context.region
            rv3d = context.region_data
            x, y = view3d_utils.location_3d_to_region_2d(region, rv3d, self.ob.location)
            self.panel.set_location(x=x-self.width/2, y=context.area.height - y)
            self.extract_button_text()
        return super().modal(context, event)

    def extract_button_text(self):
        link_desc = self.ob.link_description
        if link_desc:
            appendix = "" if len(link_desc) < 15 else "..."
            self.button1.text = f"Go to: {link_desc[:15]}" + appendix
        else:
            appendix = "" if len(self.ob.www) < 15 else "..."
            self.button1.text = f"Go to: {self.ob.www[:15]}" + appendix

    # Button press handlers
    def button1_press(self, widget):
        if self.ob.www:
            bpy.ops.wm.url_open("INVOKE_DEFAULT", url=self.ob.www)
        # print("Button '{0}' is pressed".format(widget.text))

    def on_finish(self, context):
        del KUBA_OT_draw_operator._instances[(hash(context.area), self.ob.name)]
        return super().on_finish(context)


def register():
    bpy.utils.register_class(KUBA_OT_draw_operator)


def unregister():
    bpy.utils.unregister_class(KUBA_OT_draw_operator)
