import os,sys,copy,unittest,tempfile
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
from model import blank,new_node,migrate,evaluation_order
from animation import set_key,parameters,value_at
from live_engine import fingerprint
from registry import NODES
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from app import Window


class AnimationTests(unittest.TestCase):
    def test_planar_inverse_and_live_link(self):
        from geometry import planar_output
        unit=[[0,0],[1,0],[1,1],[0,1]];moved=[[x+.1,y-.2] for x,y in unit]
        inverse=planar_output(moved,unit,'stabilize')
        self.assertAlmostEqual(inverse[0][0],-.1);self.assertAlmostEqual(inverse[0][1],.2)
        g=blank();tracker=new_node(g,'Tracker2D');target=new_node(g,'Roto')
        target['animation_link']=tracker['id'];set_key(tracker,'x',1,2.);set_key(tracker,'x',3,6.)
        self.assertEqual(parameters(target,2,g)['x'],4.)
        set_key(tracker,'x',2,8.);self.assertEqual(parameters(target,2,g)['x'],8.)
    def test_time_branches_and_fingerprint(self):
        g=blank();g['blender']='test';source=new_node(g,'Constant');hold=new_node(g,'FrameHold');hold['inputs']['Image']=source['id']
        hold['params']['frame']=3;set_key(source,'r',1,0.);set_key(source,'r',5,1.)
        self.assertEqual(evaluation_order(g,hold['id'],10)[0][1],3)
        self.assertEqual(parameters(source,3)['r'],.5)
        before=fingerprint(g,hold['id'],10,1);set_key(source,'r',3,.8)
        self.assertNotEqual(before,fingerprint(g,hold['id'],10,1))

    def test_bezier_tangents_and_constant(self):
        c={'interpolation':'bezier','keys':[[0,0,0,2],[1,1,0,0]]}
        self.assertAlmostEqual(value_at(c,.5),.75)
        c['interpolation']='constant';self.assertEqual(value_at(c,.99),0);self.assertEqual(value_at(c,1),1)

    def test_v1_migration_is_nonmutating(self):
        g={'version':1,'nodes':[dict(id='Transform1',kind='Transform',params=dict(x=2,y=3,scale=1),inputs={})]}
        result=migrate(g);self.assertEqual(result['nodes'][0]['params']['rotation'],0);self.assertNotIn('rotation',g['nodes'][0]['params'])


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.w=Window();self.w.live_toggle.setChecked(False);self.w.engine.stop();self.w.live_timer.stop()
        self.w.error=lambda message: (_ for _ in ()).throw(AssertionError(message))
    def tearDown(self):
        self.w.dirty=False;self.w.close();self.w.deleteLater()

    def test_all_property_panels(self):
        for kind in NODES:
            n=new_node(self.w.project,kind);self.w.properties(n)
        self.w.graph.rebuild()

    def test_copy_paste_and_bypass_undo(self):
        graph=self.w.graph;graph.items_by_id['Read2'].setSelected(True);graph.items_by_id['Color1'].setSelected(True)
        count=len(self.w.project['nodes']);graph.copy_nodes();graph.paste_nodes()
        self.assertEqual(len(self.w.project['nodes']),count+2)
        pasted=graph.selected_nodes();ids={n.data['id'] for n in pasted}
        color=next(n.data for n in pasted if n.data['kind']=='Color');self.assertIn(color['inputs']['Image'],ids)
        graph.bypass();self.assertTrue(color['disabled']);self.w.undo()
        current=next(n for n in self.w.project['nodes'] if n['id']==color['id']);self.assertFalse(current.get('disabled',False))

    def test_save_no_engine_and_autosave(self):
        with tempfile.TemporaryDirectory() as d:
            import json
            self.w.filename=str(Path(d)/'saved.nukify');self.assertTrue(self.w.save_project())
            saved=json.loads(Path(self.w.filename).read_text());self.assertNotIn('blender',saved)
            self.w.recovery_path=Path(d)/'recovery.nukify';self.w.dirty=True;self.w.autosave();self.assertTrue(self.w.recovery_path.is_file())

    def test_shortcut_focus_does_not_delete_nodes(self):
        self.w.graph.items_by_id['Color1'].setSelected(True)
        self.w.out.setText('something');self.w.out.setFocus();self.w.out.selectAll()
        QTest.keyClick(self.w.out,Qt.Key_Delete)
        self.assertTrue(any(n['id']=='Color1' for n in self.w.project['nodes']))

    def test_drag_connection_and_undo(self):
        self.w.show();self.app.processEvents();g=self.w.graph;g.fit()
        src=g.items_by_id['Read1'].output;dest=g.items_by_id['Color1'].inputs['Image']
        start=g.mapFromScene(src.scenePos());end=g.mapFromScene(dest.scenePos())
        QTest.mousePress(g.viewport(),Qt.LeftButton,pos=start)
        QTest.mouseMove(g.viewport(),end)
        QTest.mouseRelease(g.viewport(),Qt.LeftButton,pos=end)
        node=next(n for n in self.w.project['nodes'] if n['id']=='Color1')
        self.assertEqual(node['inputs']['Image'],'Read1')
        self.w.undo();node=next(n for n in self.w.project['nodes'] if n['id']=='Color1')
        self.assertEqual(node['inputs']['Image'],'Read2')

    def test_drop_node_on_wire_inserts_atomically(self):
        self.w.add('Dot');self.w.show();self.app.processEvents();g=self.w.graph;g.fit()
        node=g.items_by_id['Dot1']
        edge=next(e for e in g.edges if e.connection==('Color1','Image'))
        start=g.mapFromScene(node.sceneBoundingRect().center());end=g.mapFromScene(edge.path().pointAtPercent(.5))
        QTest.mousePress(g.viewport(),Qt.LeftButton,pos=start)
        QTest.mouseMove(g.viewport(),end);QTest.mouseRelease(g.viewport(),Qt.LeftButton,pos=end)
        nodes={n['id']:n for n in self.w.project['nodes']}
        self.assertEqual(nodes['Dot1']['inputs'].get('Image'),'Read2')
        self.assertEqual(nodes['Color1']['inputs']['Image'],'Dot1')
        self.w.undo();nodes={n['id']:n for n in self.w.project['nodes']}
        self.assertEqual(nodes['Color1']['inputs']['Image'],'Read2')
        self.assertEqual(nodes['Dot1']['inputs'],{})

if __name__=='__main__':unittest.main()
