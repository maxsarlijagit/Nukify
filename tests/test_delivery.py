import sys,tempfile,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from delivery import collect,resolve_media,completed,commit_frame
from model import blank,new_node,connect,evaluation_order

class DeliveryTests(unittest.TestCase):
    def test_relocatable_sequence_and_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);media=root/'original';media.mkdir()
            for i in (1,2):(media/f'plate_{i:04d}.png').write_bytes(bytes([i]))
            g=blank();n=new_node(g,'Read');n['params']['path']=str(media/'plate_####.png')
            file=collect(g,root/'bundle');doc=json.loads(file.read_text())
            self.assertFalse(Path(doc['nodes'][0]['params']['path']).is_absolute())
            moved=root/'moved';file.parent.rename(moved)
            resolved=resolve_media(doc,moved);evaluation_order(resolved,n['id'],2)
            with self.assertRaises(ValueError):collect(g,moved)
    def test_receipts_reject_corruption_and_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            for ext in ('exr','png'):(out/('comp_0001.exr' if ext=='exr' else 'preview_0001.png')).write_bytes(b'valid')
            commit_frame(out,1,'signature');self.assertTrue(completed(out,1,'signature'))
            self.assertFalse(completed(out,1,'different'))
            (out/'comp_0001.exr').write_bytes(b'partial');self.assertFalse(completed(out,1,'signature'))
    def test_typed_scene(self):
        g=blank();cam=new_node(g,'Camera');geo=new_node(g,'Geometry');scene=new_node(g,'Scene');render=new_node(g,'RenderLayers')
        with self.assertRaises(ValueError):connect(g,cam['id'],scene['id'],'Object')
        connect(g,geo['id'],scene['id'],'Object');connect(g,scene['id'],render['id'],'Scene');connect(g,cam['id'],render['id'],'Camera')
        self.assertEqual(len(evaluation_order(g,render['id'])),4)

