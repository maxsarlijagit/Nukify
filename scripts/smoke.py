"""Run with Blender --background --factory-startup --python scripts/smoke.py."""
import sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nukify

nukify.register()
tree = nukify.tree_for(bpy.context.scene)
original = set(n.name for n in tree.nodes)
assert bpy.ops.nukify.starter() == {'FINISHED'}
assert original.issubset(set(n.name for n in tree.nodes))
for kind in nukify.NODES:
    node = nukify.add_node(tree, kind)
    assert node.bl_idname == nukify.NODES[kind][1]
read = nukify.add_node(tree, 'READ')
viewer = nukify.view_node(tree, read)
assert viewer.inputs[0].links[0].from_node == read
write = nukify.add_node(tree, 'WRITE')
assert write.format.file_format == 'OPEN_EXR'
assert write.format.color_depth == '32'
nukify.unregister()
print('NUKIFY_SMOKE_OK: register, node creation, preservation, viewer routing, EXR, unregister')
