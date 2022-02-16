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
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "Empty object (image) -> Properties -> Object Data Properties",
    "warning": "",
    "category": "user",
}


import bpy
from bpy.types import Operator, Object, Panel
from mathutils import Vector


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


classes = (KUBA_NOTES_PT_notes,)


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
