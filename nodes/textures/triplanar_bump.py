import bpy
from bpy.props import BoolProperty
from ..base import LuxCoreNodeTexture
from ... import utils
from ...utils import node as utils_node



class LuxCoreNodeTriplanarBump(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Triplanar Bump Mapping"
    bl_width_default = 180

    def update_individual_textures(self, context):
        if self.individual_textures:
            self.inputs["Value"].name = "Value X"
            self.inputs["Bump Height"].name = "Bump Height X"
        else:
            self.inputs["Value X"].name = "Value"
            self.inputs["Bump Height X"].name = "Bump Height"

        self.inputs["Value Y"].enabled = self.individual_textures
        self.inputs["Bump Height Y"].enabled = self.individual_textures
        self.inputs["Value Z"].enabled = self.individual_textures
        self.inputs["Bump Height Z"].enabled = self.individual_textures
        utils_node.force_viewport_update(self, context)

    individual_textures: BoolProperty(update=update_individual_textures, name="Individual Textures",
                                      default=False)

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height", 0.001)
        self.add_input("LuxCoreSocketFloatUnbounded", "Value Y", 0, enabled=False)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height Y", 0.001, enabled=False)
        self.add_input("LuxCoreSocketFloatUnbounded", "Value Z", 0, enabled=False)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height Z", 0.001, enabled=False)
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketBump", "Bump")

    def draw_buttons(self, context, layout):
        layout.prop(self, "individual_textures")

    def _create_bump_tex(self, suffix, value, height, props):
        tex_name = self.make_name() + suffix
        prefix = "scene.textures." + tex_name + "."
        defs = {
            "type": "scale",
            "texture1": value,
            "texture2": height,
        }
        props.Set(utils.create_props(prefix, defs))
        return tex_name

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        mapping_type, uvindex, transformation = self.inputs["3D Mapping"].export(exporter, depsgraph, props)

        if self.individual_textures:
            value1 = self.inputs["Value X"].export(exporter, depsgraph, props)
            height1 = self.inputs["Bump Height X"].export(exporter, depsgraph, props)
            tex1 = self._create_bump_tex("bumpX", value1, height1, props)

            value2 = self.inputs["Value Y"].export(exporter, depsgraph, props)
            height2 = self.inputs["Bump Height Y"].export(exporter, depsgraph, props)
            tex2 = self._create_bump_tex("bumpY", value2, height2, props)

            value3 = self.inputs["Value Z"].export(exporter, depsgraph, props)
            height3 = self.inputs["Bump Height Z"].export(exporter, depsgraph, props)
            tex3 = self._create_bump_tex("bumpZ", value3, height3, props)
        else:
            value = self.inputs["Value"].export(exporter, depsgraph, props)
            height = self.inputs["Bump Height"].export(exporter, depsgraph, props)
            tex1 = tex2 = tex3 = self._create_bump_tex("bump", value, height, props)

        definitions = {
            "type": "triplanar",
            "texture1": tex1,
            "texture2": tex2,
            "texture3": tex3,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }

        if not utils_node.get_link(self.inputs["3D Mapping"]):
            definitions["mapping.type"] = "localmapping3d"

        if mapping_type == "uvmapping3d":
            definitions["mapping.uvindex"] = uvindex

        return self.create_props(props, definitions, luxcore_name)
