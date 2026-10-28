import os,sys,unittest,tempfile,copy
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
import numpy as np
from expressions import evaluate,remap_refs
from animation import parameters,render_parameters,set_key
from model import blank,new_node
from live_engine import fingerprint
from roto import render_mask,validate_groups
from curve_editor import retime,validate_curve,CurveView,set_table
from PySide6.QtWidgets import QApplication,QTableWidget,QComboBox
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from tracking import analyze,cv2

class AdvancedTests(unittest.TestCase):
    def test_expressions_and_rejections(self):
        self.assertEqual(evaluate('clamp(value + frame + ref("A","r"),0,10)',2,3,lambda a,b:4),9)
        for text in ['__import__("os")','value.real','[1][0]','2**100','1/0','sqrt(-1)']:
            with self.assertRaises(ValueError):evaluate(text,1,0,lambda a,b:0)
        self.assertIn("'B'",remap_refs('ref("A","r")',{'A':'B'}))
    def test_reference_cache_and_cycle(self):
        g=blank();a=new_node(g,'Constant');b=new_node(g,'Constant')
        b['expressions']={'r':f'ref("{a["id"]}","r") * 2'}
        old=fingerprint(g,b['id'],1,1);a['params']['r']=.25
        self.assertEqual(parameters(b,1,g)['r'],.5)
        self.assertNotEqual(old,fingerprint(g,b['id'],1,1))
        a['expressions']={'r':f'ref("{b["id"]}","r")'}
        with self.assertRaisesRegex(ValueError,'[Cc]iclo'):parameters(b,1,g)
    def test_retime_slopes_and_collisions(self):
        curve={'interpolation':'bezier','keys':[[1,0,2,4],[3,2,6,8]]}
        self.assertEqual(retime(curve,2,1,1)['keys'],[[2,0,1,2],[6,2,3,4]])
        with self.assertRaises(ValueError):retime(curve,.01,0)
    def test_curve_drag_cancel(self):
        app=QApplication.instance() or QApplication([])
        table=QTableWidget(0,4);combo=QComboBox();combo.addItem('bezier')
        original={'interpolation':'bezier','keys':[[1,0,0,0],[10,1,0,0]]};set_table(table,original)
        def read():return dict(interpolation=combo.currentText(),keys=[[float(table.item(r,c).text()) for c in range(4)] for r in range(table.rowCount())])
        view=CurveView(table,combo,read);view.resize(650,250);view.show();app.processEvents();view.plot()
        start=view.mapFromScene(view.handles[0][0]);QTest.mousePress(view.viewport(),Qt.LeftButton,pos=start)
        QTest.mouseMove(view.viewport(),start+QPoint(20,-20));self.assertNotEqual(read(),original)
        QTest.keyClick(view,Qt.Key_Escape);self.assertEqual(read(),original);view.close()
    def test_real_curve_dialog_save_and_failed_tracking_preserves_animation(self):
        from app import Window
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QDialog,QDialogButtonBox
        app=QApplication.instance() or QApplication([]);w=Window();w.live_toggle.setChecked(False);w.live_timer.stop();w.cache_scan.stop()
        errors=[]
        try:
            n=new_node(w.project,'Roto');set_key(n,'shape_x',1,0);set_key(n,'shape_x',10,10)
            def edit():
                d=w.findChild(QDialog)
                try:
                    view=d.findChild(CurveView);set_table(view.table,retime(view.read(),2,0));view.plot()
                    d.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).click()
                except Exception as exc:errors.append(exc);d.reject()
            QTimer.singleShot(0,edit);w.curve_dialog(n,'shape_x')
            self.assertEqual(errors,[]);self.assertEqual([k[0] for k in n['animation']['shape_x']['keys']],[2,20])
            tracker=new_node(w.project,'Tracker2D');tracker['params']['tracking_path']='fixture_####.png';set_key(tracker,'x',1,99)
            old=copy.deepcopy(tracker['animation']);callbacks=[];w.task_start=lambda job,callback:callbacks.append(callback)
            w.start_tracking(tracker)
            callbacks[0](dict(width=w.project['width'],height=w.project['height'],complete=False,failures=[{'frame':2,'error':'lost'}],records={},animation={}))
            self.assertEqual(tracker['animation'],old);self.assertIn('last_tracking_attempt',tracker)
        finally:w.dirty=False;w.close();w.deleteLater()
    def test_roto_group_and_shutter(self):
        g=blank();n=new_node(g,'Roto');p=n['params'];p.update(points=[[.4,.4],[.5,.4],[.5,.5],[.4,.5]],shape_group='child',groups=[{'id':'parent','x':10},{'id':'child','parent':'parent','x':10}])
        mask=render_mask(render_parameters(n,2,g),100,100,2)
        self.assertGreater(np.where(mask>.5)[1].mean(),60)
        p['groups'][0]['enabled']=False;self.assertEqual(render_mask(render_parameters(n,2,g),100,100,2).sum(),0)
        p.update(groups=[],shape_group='',motion_samples=8,shutter=1)
        set_key(n,'shape_x',1,-20);set_key(n,'shape_x',3,20)
        blurred=render_mask(render_parameters(n,2,g),100,100,2);p['motion_samples']=1
        sharp=render_mask(render_parameters(n,2,g),100,100,2)
        self.assertGreater(np.count_nonzero(blurred),np.count_nonzero(sharp))
        with self.assertRaises(ValueError):validate_groups([{'id':'a','parent':'b'},{'id':'b','parent':'a'}])
    def test_manual_tracking_recovery_and_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            rng=np.random.default_rng(45);base=cv2.GaussianBlur(rng.integers(0,256,(240,320),np.uint8),(3,3),.7)
            for f,dx in [(1,0),(2,50),(3,52)]:
                cv2.imencode('.png',cv2.warpAffine(base,np.float32([[1,0,dx],[0,1,0]]),(320,240)))[1].tofile(str(Path(tmp)/f'p_{f:04d}.png'))
            job=dict(kind='Tracker2D',path=str(Path(tmp)/'p_####.png'),reference=1,first=1,last=3,tracks=[[.4,.4]],max_step=5,allow_partial=True)
            failed=analyze(job);self.assertFalse(failed['complete']);self.assertEqual(failed['failures'][0]['frame'],2)
            job['manual_points']={'2':[[.4+50/320,.4]]};result=analyze(job)
            self.assertTrue(result['complete']);self.assertTrue(result['records'][2]['manual']);self.assertAlmostEqual(result['animation']['x']['keys'][-1][1],52,delta=.2)
            job.update(kind='PlanarTracker',corners=[[.2,.2],[.6,.2],[.6,.8],[.2,.8]],manual_points={'2':[[.2+50/320,.2],[.6+50/320,.2],[.6+50/320,.8],[.2+50/320,.8]]})
            self.assertTrue(analyze(job)['complete'])
            job['exclude_polygon']=[[0,0],[1,0],[1,1],[0,1]]
            with self.assertRaisesRegex(ValueError,'features'):analyze(job)

if __name__=='__main__':unittest.main()
