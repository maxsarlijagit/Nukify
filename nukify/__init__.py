# SPDX-License-Identifier: GPL-3.0-or-later
"""Nukify: compositor-first tools for Blender 4.5 LTS."""
bl_info = {
    "name": "Nukify", "author": "Nukify contributors", "version": (0, 1, 0),
    "blender": (4, 5, 0), "location": "Compositor > Sidebar > Nukify",
    "description": "Compositor-first workspace and familiar node workflows",
    "category": "Compositing",
}

import bpy
from bpy.props import EnumProperty

# These are workflow labels, not promises of mathematical Nuke equivalence.
NODES = {
    "READ": ("Read", "CompositorNodeImage"),
    "MERGE": ("Merge (Over)", "CompositorNodeAlphaOver"),
    "COLOR": ("Color Balance", "CompositorNodeColorBalance"),
    "BLUR": ("Blur", "CompositorNodeBlur"),
    "TRANSFORM": ("Transform", "CompositorNodeTransform"),
    "KEYER": ("Keyer", "CompositorNodeKeying"),
    "MASK": ("Mask", "CompositorNodeMask"),
    "RENDER": ("3D Render Layers", "CompositorNodeRLayers"),
    "WRITE": ("Write", "CompositorNodeOutputFile"),
}


def tree_for(scene):
    scene.use_nodes = True
    return scene.node_tree


def add_node(tree, kind, location=(0, 0)):
    label, node_type = NODES[kind]
    node = tree.nodes.new(node_type)
    node.label = label
    node.location = location
    node.width = 180
    if kind == "BLUR":
        node.filter_type = 'GAUSS'
        node.size_x = node.size_y = 8
    if kind == "WRITE":
        node.base_path = "//renders/"
        node.format.file_format = 'OPEN_EXR'
        node.format.color_depth = '32'
    for other in tree.nodes:
        other.select = other == node
    tree.nodes.active = node
    return node


def view_node(tree, node):
    output = next((s for s in node.outputs if s.type == 'RGBA' and s.enabled), None)
    if output is None:
        raise ValueError("Seleccioná un nodo con salida de imagen RGBA")
    viewer = next((n for n in tree.nodes if n.bl_idname == 'CompositorNodeViewer'), None)
    if viewer is None:
        viewer = tree.nodes.new('CompositorNodeViewer')
    viewer.location = (node.location.x + 240, node.location.y - 180)
    tree.links.new(output, viewer.inputs[0])
    return viewer


class NUKIFY_OT_workspace(bpy.types.Operator):
    bl_idname = 'nukify.workspace'
    bl_label = 'Abrir espacio Nukify'
    bl_description = 'Duplica el espacio actual y configura un editor de composición'

    def execute(self, context):
        existing = bpy.data.workspaces.get('Nukify')
        if existing:
            context.window.workspace = existing
            return {'FINISHED'}
        bpy.ops.workspace.duplicate()
        context.window.workspace.name = 'Nukify'
        tree_for(context.scene)
        areas = sorted(context.screen.areas, key=lambda a: a.width * a.height, reverse=True)
        editor = areas[0]
        editor.type = 'NODE_EDITOR'
        editor.ui_type = 'CompositorNodeTree'
        editor.spaces.active.show_region_ui = True
        editor.spaces.active.show_backdrop = True
        # Reuse a secondary pane; preserve Timeline and Properties when possible.
        for area in areas[1:]:
            if area.type == 'OUTLINER':
                area.type = 'IMAGE_EDITOR'
                image = bpy.data.images.get('Viewer Node')
                if image:
                    area.spaces.active.image = image
                break
        return {'FINISHED'}


class NUKIFY_OT_add(bpy.types.Operator):
    bl_idname = 'nukify.add_node'
    bl_label = 'Agregar nodo Nukify'
    bl_options = {'REGISTER', 'UNDO'}
    kind: EnumProperty(items=[(key, value[0], '') for key, value in NODES.items()])

    def execute(self, context):
        tree = tree_for(context.scene)
        active = tree.nodes.active
        location = (active.location.x, active.location.y - 220) if active else (0, 0)
        add_node(tree, self.kind, location)
        return {'FINISHED'}


class NUKIFY_OT_view(bpy.types.Operator):
    bl_idname = 'nukify.view_selected'
    bl_label = 'Ver nodo seleccionado'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tree = tree_for(context.scene)
        if not tree.nodes.active:
            self.report({'WARNING'}, 'Seleccioná un nodo')
            return {'CANCELLED'}
        try:
            view_node(tree, tree.nodes.active)
        except ValueError as exc:
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class NUKIFY_OT_starter(bpy.types.Operator):
    bl_idname = 'nukify.starter'
    bl_label = 'Crear composición inicial'
    bl_description = 'Agrega Read > Color Balance > Viewer; no borra nodos existentes'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tree = tree_for(context.scene)
        x = max((n.location.x + n.width for n in tree.nodes), default=-400) + 400
        read = add_node(tree, 'READ', (x, 200))
        color = add_node(tree, 'COLOR', (x, -80))
        tree.links.new(read.outputs['Image'], color.inputs['Image'])
        view_node(tree, color)
        self.report({'INFO'}, 'Elegí una imagen en Read. Write se agrega por separado.')
        return {'FINISHED'}


class NUKIFY_MT_nodes(bpy.types.Menu):
    bl_label = 'Nukify Nodes'
    bl_idname = 'NUKIFY_MT_nodes'

    def draw(self, context):
        for kind, (label, _) in NODES.items():
            self.layout.operator('nukify.add_node', text=label).kind = kind


class NUKIFY_PT_tools(bpy.types.Panel):
    bl_label = 'Nukify · Compositing'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Nukify'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'CompositorNodeTree'

    def draw(self, context):
        layout = self.layout
        layout.operator('nukify.workspace')
        layout.operator('nukify.starter')
        layout.menu('NUKIFY_MT_nodes', text='Agregar nodo · Shift+A')
        layout.operator('nukify.view_selected', text='Ver seleccionado · 1')
        layout.separator()
        layout.label(text='Motor: Blender Compositor')
        layout.label(text='Read/Write: configurar rutas en el nodo')


CLASSES = (NUKIFY_OT_workspace, NUKIFY_OT_add, NUKIFY_OT_view,
           NUKIFY_OT_starter, NUKIFY_MT_nodes, NUKIFY_PT_tools)
KEYMAPS = []


def node_menu(self, context):
    if context.space_data.tree_type == 'CompositorNodeTree':
        self.layout.menu('NUKIFY_MT_nodes')


class NUKIFY_OT_view_key(NUKIFY_OT_view):
    bl_idname = 'nukify.view_key'

    @classmethod
    def poll(cls, context):
        return (context.area and context.area.type == 'NODE_EDITOR'
                and context.space_data.tree_type == 'CompositorNodeTree')


def register():
    for cls in (*CLASSES, NUKIFY_OT_view_key):
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_add.append(node_menu)
    config = bpy.context.window_manager.keyconfigs.addon
    if config:
        km = config.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        item = km.keymap_items.new('nukify.view_key', 'ONE', 'PRESS')
        KEYMAPS.append((km, item))


def unregister():
    for km, item in KEYMAPS:
        km.keymap_items.remove(item)
    KEYMAPS.clear()
    bpy.types.NODE_MT_add.remove(node_menu)
    for cls in reversed((*CLASSES, NUKIFY_OT_view_key)):
        bpy.utils.unregister_class(cls)
