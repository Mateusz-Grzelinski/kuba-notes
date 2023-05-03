import functools
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


def get_targets(source_obj_name: str) -> bpy.types.Object:
    for ob in bpy.data.objects:
        ob: bpy.types.Object
        if "arrow" not in ob.name.lower():
            continue
        arrow_has_source_in_source_obj = any(
            mod
            for mod in ob.modifiers
            if mod.type == "HOOK" and mod.name == "Hook source" and mod.object.name == source_obj_name
        )
        if not arrow_has_source_in_source_obj:
            continue
        for mod in ob.modifiers:
            mod: bpy.types.Modifier
            if mod.type == "HOOK" and mod.name == "Hook target":
                yield mod.object
    return []
    # if mod.type != "HOOK" and mod.name == "Hook target":
    #     continue


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

    def _generate_link_buttons(self, source_ob: bpy.types.Object):
        # self.link_buttons.clear()
        for i, target_ob in enumerate(get_targets(source_ob.name)):
            but = BL_UI_Button(x=50, y=50 + i * 40, width=200, height=30)
            but.bg_color = (0.4, 0.4, 0.4, 0.8)
            but.hover_bg_color = (0.7, 0.7, 0.7, 1.0)
            but.text = target_ob.name
            but.set_mouse_down(
                functools.partial(
                    self.button_frame_selected, target_object=target_ob.name
                )
            )
            self.link_buttons.append(but)

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
        self.extract_and_set_button1_text()

        self.link_buttons = []
        self._generate_link_buttons(ob)

        widgets_panel = [self.button1, *self.link_buttons]
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
        self.panel.set_location(x=x - self.width / 2, y=context.area.height - y)

    def modal(self, context, event):
        # not ideal, but quick to implement:
        if event.type in {"TIMER"} and self.ob:
            region = context.region
            rv3d = context.region_data
            x, y = view3d_utils.location_3d_to_region_2d(region, rv3d, self.ob.location)
            self.panel.set_location(x=x - self.width / 2, y=context.area.height - y)
            self.extract_and_set_button1_text()
        return super().modal(context, event)

    def extract_and_set_button1_text(self):
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

    def button_frame_selected(self, widget: BL_UI_Widget, target_object: str):
        # todo ugly: overriding selected object does not want to work
        for ob in bpy.data.objects:
            ob.select_set(False)
        bpy.data.objects[target_object].select_set(True)
        # with bpy.context.temp_override(selected_objects=target_object):
        bpy.ops.view3d.view_selected()
        # bpy.ops.view3d.view_selected({"selected_objects": [target_object]})
        # print("Button '{0}' is pressed".format(widget.text))

    def on_finish(self, context):
        del KUBA_OT_draw_operator._instances[(hash(context.area), self.ob.name)]
        return super().on_finish(context)


def register():
    bpy.utils.register_class(KUBA_OT_draw_operator)


def unregister():
    bpy.utils.unregister_class(KUBA_OT_draw_operator)
