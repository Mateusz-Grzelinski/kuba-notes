import bpy
from bpy_extras import view3d_utils

from . import drag_panel_op


def main(context: bpy.types.Context, event: bpy.types.Event) -> bpy.types.Object:
    """Run this function on left mouse, execute the ray cast"""
    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

    ray_target = ray_origin + view_vector

    def visible_objects_and_duplis():
        """Loop over (object, matrix) pairs (mesh only)"""

        depsgraph = context.evaluated_depsgraph_get()
        for dup in depsgraph.object_instances:
            if dup.is_instance:  # Real dupli instance
                obj = dup.instance_object
                yield (obj, dup.matrix_world.copy())
            else:  # Usual object
                obj = dup.object
                yield (obj, obj.matrix_world.copy())

    def obj_ray_cast(obj, matrix):
        """Wrapper for ray casting that moves the ray into object space"""

        # get the ray relative to the object
        matrix_inv = matrix.inverted()
        ray_origin_obj = matrix_inv @ ray_origin
        ray_target_obj = matrix_inv @ ray_target
        ray_direction_obj = ray_target_obj - ray_origin_obj

        # cast the ray
        success, location, normal, face_index = obj.ray_cast(
            ray_origin_obj, ray_direction_obj
        )

        if success:
            return location, normal, face_index
        else:
            return None, None, None

    # cast rays and find the closest object
    best_length_squared = -1.0
    best_obj = None

    for obj, matrix in visible_objects_and_duplis():
        if obj.type == "MESH":
            hit, normal, face_index = obj_ray_cast(obj, matrix)
            if hit is not None:
                hit_world = matrix @ hit
                scene.cursor.location = hit_world
                length_squared = (hit_world - ray_origin).length_squared
                if best_obj is None or length_squared < best_length_squared:
                    best_length_squared = length_squared
                    best_obj = obj
    # print("object chosen!:" + str(best_obj))
    return best_obj


class ViewOperatorRayCast(bpy.types.Operator):
    """Modal object selection with a ray cast"""

    bl_idname = "kuba.raycast"
    bl_label = "Kuba RayCast"

    _instances = dict()
    _finish = False

    finish: bpy.props.BoolProperty(
        name="finish",
        description="false to start operator, true to stop operator",
        default=False,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.area.type == "VIEW_3D"

    @classmethod
    def is_running(cls, scene: bpy.types.Scene) -> "ViewOperatorRayCast":
        return cls._instances.get(scene.name)

    # @classmethod
    # def finish(cls, scene: bpy.types.Scene):
    #     op = ViewOperatorRayCast.is_running(scene)
    #     op._finish = True

    def invoke(self, context, event):
        running_op = ViewOperatorRayCast.is_running(context.scene)
        if running_op and self.finish:
            self._finish = True
            try:
                running_op._finish = True
            except ReferenceError:
                del ViewOperatorRayCast._instances[context.scene.name]
                pass
            return {"FINISHED"}
        self.last_object_name = None
        if context.space_data.type == "VIEW_3D":
            context.window_manager.modal_handler_add(self)
            ViewOperatorRayCast._instances[context.scene.name] = self
            return {"RUNNING_MODAL"}
        else:
            self.report({"WARNING"}, "Active space must be a View3d")
            return {"CANCELLED"}

    def modal(self, context, event):
        # context.area can be none if workspace is changed
        if self._finish or context.area is None:
            del ViewOperatorRayCast._instances[context.scene.name]
            if context.area:
                context.area.tag_redraw()
            return {"CANCELLED"}
        if event.type in {"MIDDLEMOUSE", "WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            # allow navigation
            return {"PASS_THROUGH"}
        # elif event.type == 'LEFTMOUSE':
        elif event.type == "MOUSEMOVE":
            try:
                obj: bpy.types.Object = main(context, event)
            except AttributeError:
                # can occur when changing workspace
                obj = None
            if (obj is not None and obj.name != self.last_object_name) or (
                obj is None and self.last_object_name is not None
            ):
                self._on_hover_object_change(context, event, obj)
            self.last_object_name = obj.name if obj else None
            # return {'RUNNING_MODAL'}

        return {"PASS_THROUGH"}

    def _on_hover_object_change(self, context, event, obj):
        # print(f"Last: {self.last_object_name}, now: {obj}")
        # close panel on hover ended
        if op := drag_panel_op.KUBA_OT_draw_operator.is_running(
            context=context, obj_name=self.last_object_name
        ):
            op.finish()

        if (
            obj
            and self.last_object_name != obj.name
            and (obj.www or obj.link_description)
        ):
            op: drag_panel_op.KUBA_OT_draw_operator
            if not (
                op := drag_panel_op.KUBA_OT_draw_operator.is_running(
                    context=context, obj_name=obj.name
                )
            ):
                bpy.ops.object.kuba_draw("INVOKE_DEFAULT", object_name=obj.name)
            # else:
            #     op.panel.set_location(
            #         event.mouse_x, context.area.height - event.mouse_y + 20
            #     )


def register():
    bpy.utils.register_class(ViewOperatorRayCast)


def unregister():
    bpy.utils.unregister_class(ViewOperatorRayCast)
