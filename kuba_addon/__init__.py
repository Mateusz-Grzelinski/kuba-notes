bl_info = {
    "name": "KubaNotes",
    "author": "Mateusz Grzeliński",
    "description": "",
    "blender": (3, 0, 0),
    "version": (0, 4, 0),
    "location": "Object -> Properties -> Object Data Properties",
    "warning": "",
    "category": "user",
}


import os

try:
    import bpy
except ModuleNotFoundError as e:
    e.bl_info = bl_info
    raise e
from bpy.types import Operator, Object, Panel, Context
from . import bl_ui_widgets
from . import drag_panel_op
from . import raycast_op


def walk_backwards(node: bpy.types.Node) -> bpy.types.Node:
    for output in node.outputs:
        if not output:
            return node
        if output.type != "SHADER":
            return node
        for input in node.inputs:
            input: bpy.types.NodeSocket
            if input.links:
                for link in input.links:
                    link: bpy.types.NodeLink
                    if link.from_socket.type == "VECTOR":
                        continue
                    return walk_backwards(link.from_node)


def pick_colored_output(node: bpy.types.Node) -> str:
    colored_output = [out.name for out in node.outputs if out.type == "RGBA"]
    if colored_output:
        return colored_output[0]
    return node.outputs[0].name


class EmitMaterialOperator(Operator):
    bl_idname = "kuba_notes.emit_material"
    bl_label = "Make Shadowless"
    bl_description = "Convert to material that is not affected by shadow"

    reverse: bpy.props.BoolProperty(
        description="reverse the effect - bring back old material",
        default=False
    )

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob

    def execute(self, context):
        obj: bpy.types.Object = context.active_object

        if not obj.material_slots:
            self.report({"ERROR"}, "No material is present")
            return {"CANCELLED"}

        for material_slot in obj.material_slots:
            material_slot: bpy.types.MaterialSlot
            material = material_slot.material
            if not material.use_nodes:
                self.report({"ERROR"}, "Not supported: Material does not use nodes")
                return {"CANCELLED"}
            node_tree: bpy.types.ShaderNodeTree = material.node_tree
            links = node_tree.links
            output_nodes = [
                node
                for node in node_tree.nodes
                if node.type == "OUTPUT_MATERIAL" and node.inputs[0].links
            ]
            if len(output_nodes) != 1:
                self.report(
                    {"ERROR"},
                    "Not supported: can not find Output Material node or found multiple",
                )
                return {"CANCELLED"}
            output_node = output_nodes[0]

            if self.reverse:
                try:
                    emission: bpy.types.ShaderNodeEmission = node_tree.nodes[
                        "Added by addon Emission"
                    ]
                    # very hacky xd and the logic is not perfect
                    old_input: bpy.types.Node = node_tree.nodes[emission.label]
                except KeyError:
                    return {"CANCELLED"}
                else:
                    links.new(old_input.outputs[0], output_node.inputs[0])
                return {"FINISHED"}

            first_non_shader_node = walk_backwards(
                output_node.inputs[0].links[0].from_node
            )
            output_node_inputs = output_node.inputs[0].links
            if output_node_inputs:
                old_node: bpy.types.Node = output_node_inputs[0].from_node
            try:
                emission: bpy.types.ShaderNodeEmission = node_tree.nodes["Added by addon Emission"]
            except KeyError:
                emission: bpy.types.ShaderNodeEmission = node_tree.nodes.new("ShaderNodeEmission")
            emission.name = "Added by addon Emission"
            if not self.reverse:
                emission.label = old_node.name
            if first_non_shader_node:
                links.new(
                    first_non_shader_node.outputs[
                        pick_colored_output(first_non_shader_node)
                    ],
                    emission.inputs[0],
                )
            else:
                try:
                    shader_to_rgb: bpy.types.ShaderNodeShaderToRGB = node_tree.nodes["Added by addon Shader To RGB"]
                except KeyError:
                    shader_to_rgb: bpy.types.ShaderNodeShaderToRGB = node_tree.nodes.new("ShaderNodeShaderToRGB")
                shader_to_rgb.name = "Added by addon Shader To RGB"
                if old_node:
                    links.new(old_node.outputs[0], shader_to_rgb.inputs[0])
                links.new(shader_to_rgb.outputs[0], emission.inputs[0])
            links.new(emission.outputs[0], output_node.inputs[0])
        return {"FINISHED"}


class AddArrowOperator(Operator):
    bl_idname = "object.addarrow"
    bl_label = "Add parametric arrow to selected"

    ASSETS_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "assets", "arrow.blend"
    )
    ARROW_OBJECT_NAME = "Arrow"
    ARROW_NODE_TREE = "Complex arrow for curve"

    # @classmethod
    # def poll(cls, context: Context):
    #     if len(context.selected_objects) <= 1:
    #         return {"CANCELLED"}

    def execute(self, context):
        if len(context.selected_objects) <= 1:
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
        geom_nodes_mod["Input_9"] = source_object.dimensions[0] / 2
        geom_nodes_mod["Input_10"] = target_object.dimensions[0] / 2

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

        layout.label(text="Link description:")
        layout.prop(ob, "link_description", text="")
        layout.label(text="Links:")
        draw_kuba_note_menu(layout, ob)
        layout.label(text="Arrows:")
        layout.operator(AddArrowOperator.bl_idname)
        row = layout.row(align=True)
        op = row.operator(EmitMaterialOperator.bl_idname, icon="X", text="")
        op.reverse = True
        op = row.operator(EmitMaterialOperator.bl_idname)
        op.reverse = False
        from .raycast_op import ViewOperatorRayCast

        op = ViewOperatorRayCast.is_running(context.scene)
        if op:
            op = layout.operator(ViewOperatorRayCast.bl_idname, icon="PAUSE", text="")
            op.finish = True
        else:
            op = layout.operator(ViewOperatorRayCast.bl_idname, icon="PLAY")
            op.finish = False


def draw_kuba_note_menu(layout: bpy.types.UILayout, ob):
    row = layout.row(align=True)
    col = row.column(align=True)
    col.operator(
        "wm.url_open",
        text="",
        icon="URL",
    ).url = ob.www
    col.enabled = ob.www != ""
    col = row.column(align=True)
    col.prop(ob, "www", text="")


class KUBA_NOTES_PT_arrow(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_label = KUBA_NOTES_PT_notes.bl_label

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob

    draw = KUBA_NOTES_PT_notes.draw


classes = (
    KUBA_NOTES_PT_notes,
    KUBA_NOTES_PT_arrow,
    AddArrowOperator,
    EmitMaterialOperator,
)


def draw_note_button(self: bpy.types.VIEW3D_HT_header, context: bpy.types.Context):
    layout: bpy.types.UILayout = self.layout
    draw_kuba_note_menu(layout=layout, ob=context.active_object)


def register():
    from bpy.utils import register_class

    Object.link_description = bpy.props.StringProperty(
        name="link_description", description="Description of www link"
    )
    Object.www = bpy.props.StringProperty(
        name="link", description="www link for the purpose of documentation"
    )
    for cls in classes:
        register_class(cls)
    bpy.types.VIEW3D_HT_header.append(draw_func=draw_note_button)

    bl_ui_widgets.register()
    drag_panel_op.register()
    raycast_op.register()


def unregister():
    from bpy.utils import unregister_class

    bl_ui_widgets.unregister()

    del Object.www
    del Object.link_description

    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.VIEW3D_HT_header.remove(draw_func=draw_note_button)

    drag_panel_op.unregister()
    raycast_op.unregister()
