import os,sys,copy,json,tempfile,unittest
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from PySide6.QtWidgets import QApplication,QCheckBox,QDoubleSpinBox
from model import blank,new_node,migrate,evaluation_order
from animation import set_key
from live_engine import fingerprint
from shortcuts import validate_shortcuts,DEFAULTS
from app import Window

class FingerprintTests(unittest.TestCase):
    def test_future_key_preserves_unchanged_frame(self):
        g=blank();c=new_node(g,'Constant');set_key(c,'r',1,0);set_key(c,'r',10,1)
        before={f:fingerprint(g,c['id'],f,1) for f in (1,5,10)}
        set_key(c,'r',10,2)
        self.assertEqual(before[1],fingerprint(g,c['id'],1,1))
        self.assertNotEqual(before[5],fingerprint(g,c['id'],5,1))
        self.assertNotEqual(before[10],fingerprint(g,c['id'],10,1))
    def test_other_branch_and_layout_keep_cache(self):
        g=blank();a=new_node(g,'Constant');b=new_node(g,'Constant')
        before=fingerprint(g,a['id'],1,1);b['params']['r']=7;a['x']=100
        self.assertEqual(before,fingerprint(g,a['id'],1,1))
    def test_linked_parameter_invalidates(self):
        g=blank();source=new_node(g,'Tracker2D');target=new_node(g,'Roto');target['animation_link']=source['id']
        before=fingerprint(g,target['id'],1,1);source['params']['x']=5
        self.assertNotEqual(before,fingerprint(g,target['id'],1,1))

class WorkflowUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.w=Window();self.w.live_toggle.setChecked(False);self.w.live_timer.stop();self.w.cache_scan.stop()
    def tearDown(self):
        self.w.dirty=False;self.w.close();self.w.deleteLater()
    def test_shortcut_validation_and_roundtrip(self):
        m=validate_shortcuts(DEFAULTS);self.assertEqual(m,validate_shortcuts(json.loads(json.dumps(m))))
        for update in ({'Viewer A':'2'},{'Viewer A':'Ctrl+Shift+S'},{'Viewer A':'Escape'},{'Viewer A':'Ctrl+A, Ctrl+B'},{'Viewer A':'foobar'},{'Viewer A':'Ctrl+'}):
            with self.assertRaises(ValueError):validate_shortcuts(dict(m,**update))
    def test_reset_animated_parameter_undo_keeps_pin(self):
        node=next(n for n in self.w.project['nodes'] if n['id']=='Color1');set_key(node,'exposure',1,3)
        self.w.pinned_properties=node['id'];self.w.properties(node);self.w.reset_parameter(node,'exposure')
        self.assertNotIn('exposure',node['animation']);self.w.undo()
        restored=next(n for n in self.w.project['nodes'] if n['id']=='Color1')
        self.assertEqual(restored['animation']['exposure']['keys'][0][1],3)
        self.assertEqual(self.w.pinned_properties,'Color1')
        self.w.reset_parameter(restored,'exposure');self.assertNotIn('exposure',restored['animation'])
    def test_50_nodes_save_reopen_undo(self):
        g=blank();g['blender']=self.w.project['blender'];previous=new_node(g,'Constant')
        for i in range(49):
            node=new_node(g,'Grade',i*10,i*80);node['inputs']['Image']=previous['id'];previous=node
        g['viewer']=previous['id'];self.w.project=g;self.w.sync()
        self.w.parameter(previous,'gain',2);self.w.undo()
        self.assertEqual(self.w.project['nodes'][-1]['params']['gain'],1)
        self.w.redo();self.assertEqual(self.w.project['nodes'][-1]['params']['gain'],2)
        with tempfile.TemporaryDirectory() as tmp:
            self.w.filename=str(Path(tmp)/'test.nukify');self.assertTrue(self.w.save_project())
            restored=migrate(json.loads(Path(self.w.filename).read_text()))
            self.assertEqual(len(evaluation_order(restored,restored['viewer'])),50)
            self.assertEqual(restored['nodes'],self.w.project['nodes'])
    def test_swap_is_undoable(self):
        self.w.project['viewer_b']='Read1';before=copy.deepcopy(self.w.project)
        self.w.swap_viewers();self.assertEqual(self.w.project['viewer'],'Read1');self.w.undo()
        self.assertEqual(self.w.project['viewer'],before['viewer'])
    def test_pinned_animation_follows_scrub(self):
        node=next(n for n in self.w.project['nodes'] if n['id']=='Color1')
        set_key(node,'exposure',1,1);set_key(node,'exposure',2,2)
        self.w.pinned_properties=node['id'];self.w.selected='Read1';self.w.properties(node)
        self.w.frame_changed(2)
        self.assertEqual(self.w.scroll.widget().findChild(QDoubleSpinBox).value(),2)
