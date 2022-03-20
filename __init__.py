# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "KubaNotes",
    "author": "Mateusz Grzeliński",
    "description": "",
    "blender": (3, 0, 0),
    "version": (0, 0, 2),
    "location": "Object -> Properties -> Object Data Properties",
    "warning": "",
    "category": "user",
}


import bpy
from bpy.types import Operator, Object, Panel
import os


class AddArrowOperator(bpy.types.Operator):
    bl_idname = "object.addarrow"
    bl_label = "Add parametric arrow to selected"

    ASSETS_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "assets", "arrow.blend"
    )
    ARROW_OBJECT_NAME = "Arrow"
    ARROW_NODE_TREE = "Complex arrow for curve"

    def execute(self, context):
        if len(context.selected_objects) < 1:
            self.report({"ERROR"}, "Select 2 or more object")
            return {"CANCELLED"}
        target_object = context.active_object
        selected = context.selected_objects.copy()
        selected.remove(target_object)
        source_object = selected[0]  # todo loop

        with bpy.data.libraries.load(self.ASSETS_PATH, link=False) as (
            data_from,
            data_to,
        ):
            data_from: bpy.data
            data_to: bpy.data
            # data_to.objects = [name for name in data_from.objects if name == self.ARROW_OBJECT_NAME]
            data_to.node_groups = [
                name for name in data_from.node_groups if name == self.ARROW_NODE_TREE
            ]

        # the simple way:
        # for obj in data_to.objects:
        #     #bpy.context.scene.objects.link(obj) # Blender 2.7x
        #     bpy.context.collection.objects.link(obj) # Blender 2.8x

        # not needed?:
        # for node_tree in data_to.node_groups:
        #     if node_tree.name not in bpy.data.node_groups.keys():
        #         bpy.data.node_groups.append(node_tree)

        # the manual way:
        curve_data = bpy.data.curves.new("Arrow", "CURVE")
        curve_data.dimensions = "3D"
        spline = curve_data.splines.new("BEZIER")  # 'POLY' ?
        spline.bezier_points.add(1)

        p_source = spline.bezier_points[1]
        p_target = spline.bezier_points[0]

        curveOB = bpy.data.objects.new("Arrow", curve_data)

        hook_source_mod = curveOB.modifiers.new(name="Hook source", type="HOOK")
        p_source.co = source_object.location
        hook_source_mod.center = source_object.location
        i = 1
        hook_source_mod.vertex_indices_set([i * 3, i * 3 + 1, i * 3 + 2])
        context.evaluated_depsgraph_get()
        hook_source_mod.object = source_object

        hook_target_mod = curveOB.modifiers.new(name="Hook target", type="HOOK")
        p_target.co = target_object.location
        hook_target_mod.center = target_object.location
        i = 0
        hook_target_mod.vertex_indices_set([i * 3, i * 3 + 1, i * 3 + 2])
        context.evaluated_depsgraph_get()
        hook_target_mod.object = target_object

        for point in spline.bezier_points:
            point.handle_left = point.co
            point.handle_right = point.co

        geom_nodes_mod = curveOB.modifiers.new("Arrow geom nodes", "NODES")
        context.collection.objects.link(curveOB)
        arrow_node_group = data_to.node_groups[0]
        geom_nodes_mod.node_group = arrow_node_group

        # gues initial offset values
        geom_nodes_mod['Input_9'] = source_object.dimensions[0]/2
        geom_nodes_mod['Input_10'] = target_object.dimensions[0]/2

        # Source offset
        # bpy.data.objects["Arrow"].modifiers["GeometryNodes"]["Input_9"]
        # modifiers["GeometryNodes"]["Input_10"] # target offset

        return {"FINISHED"}


class KUBA_NOTES_PT_notes(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "Kuba notes"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob

    def draw(self, context):
        layout = self.layout
        ob = context.object

        row = layout.row(align=True)
        row.prop(ob, "www", text="")
        row.operator(
            "wm.url_open",
            text="",
            icon="URL",
        ).url = ob.www


class KUBA_NOTES_PT_arrow(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_label = "Add Arrow"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob

    def draw(self, context):
        layout = self.layout
        layout.operator("object.addarrow")


classes = (
    KUBA_NOTES_PT_notes,
    KUBA_NOTES_PT_arrow,
    AddArrowOperator,
)


def register():
    from bpy.utils import register_class

    Object.www = bpy.props.StringProperty(
        name="link", description="www link for the purpose of documentation"
    )
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    del Object.www
    for cls in reversed(classes):
        unregister_class(cls)
