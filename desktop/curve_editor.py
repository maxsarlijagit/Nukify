# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
import copy,json,math
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QPainterPath,QPen,QColor
from PySide6.QtWidgets import QGraphicsView,QGraphicsScene,QPushButton,QHBoxLayout,QApplication,QInputDialog,QTableWidgetItem
from animation import value_at

def validate_curve(curve):
    if not isinstance(curve,dict) or curve.get('interpolation') not in ('linear','constant','smooth','bezier'):raise ValueError('Curva invalida')
    keys=curve.get('keys')
    if not isinstance(keys,list) or len(keys)>10000:raise ValueError('Cantidad de claves invalida')
    normalized=[]
    for key in keys:
        if not isinstance(key,list) or not 2<=len(key)<=4 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e9 for x in key):raise ValueError('Clave invalida')
        if key[0]!=round(key[0]):raise ValueError('Los frames deben ser enteros')
        normalized.append((key+[0.,0.])[:4])
    if len({k[0] for k in normalized})!=len(normalized):raise ValueError('Frames duplicados')
    return dict(interpolation=curve['interpolation'],keys=sorted(normalized))

def retime(curve,scale,offset,pivot=0):
    result=copy.deepcopy(validate_curve(curve))
    if not math.isfinite(scale) or scale<=0:raise ValueError('Escala de tiempo debe ser positiva')
    for key in result['keys']:
        key[0]=round(pivot+(key[0]-pivot)*scale+offset);key[2]/=scale;key[3]/=scale
    return validate_curve(result)

class CurveView(QGraphicsView):
    def __init__(self,table,combo,read):
        super().__init__();self.setScene(QGraphicsScene());self.table=table;self.combo=combo;self.read=read;self.drag=None;self.handles=[];self.axis=None;self.setMinimumHeight(220)
    def plot(self):
        try:curve=validate_curve(self.read())
        except (ValueError,AttributeError):return
        self.scene().clear();self.handles=[]
        if not curve['keys']:return
        keys=curve['keys'];first,last=keys[0][0],keys[-1][0]
        values=[value_at(curve,first+(last-first)*i/200) for i in range(201)]
        if self.drag is None:
            span=max(1,last-first);low,high=min(values),max(values);height=max(.1,high-low)
            self.axis=(first-span*.15,last+span*.15,low-height*.3,high+height*.3)
        path=QPainterPath()
        for i,y in enumerate(values):
            pos=self.map_value(first+(last-first)*i/200,y)
            if i==0:path.moveTo(pos)
            else:path.lineTo(pos)
        self.scene().addPath(path,QPen(QColor('#e9b56a'),2))
        selected={i.row() for i in self.table.selectedIndexes()}
        for row,key in enumerate(keys):
            pos=self.map_value(key[0],key[1]);self.handle(pos,row,0,'#f2cb84' if row in selected else '#aaaaaa')
            if curve['interpolation']=='bezier':
                dt=max(.25,(self.axis[1]-self.axis[0])*.08)
                for column,direction in ((2,-1),(3,1)):
                    endpoint=self.map_value(key[0]+dt*direction,key[1]+dt*direction*key[column])
                    self.scene().addLine(pos.x(),pos.y(),endpoint.x(),endpoint.y(),QPen(QColor('#7499b4')))
                    self.handle(endpoint,row,column,'#74b8cf')
        self.scene().setSceneRect(0,0,600,200);self.fitInView(self.sceneRect(),Qt.IgnoreAspectRatio)
    def handle(self,pos,row,column,color):
        self.scene().addEllipse(pos.x()-4,pos.y()-4,8,8,QPen(QColor(color)),QColor(color));self.handles.append((pos,row,column))
    def map_value(self,x,y):
        a,b,c,d=self.axis;return QPointF(20+560*(x-a)/(b-a),180-160*(y-c)/(d-c))
    def unmap_value(self,pos):
        a,b,c,d=self.axis;return a+(pos.x()-20)*(b-a)/560,c+(180-pos.y())*(d-c)/160
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton and self.handles:
            candidates=[((self.mapFromScene(p)-event.position().toPoint()).manhattanLength(),r,c) for p,r,c in self.handles]
            distance,row,column=min(candidates)
            if distance<=12:
                curve=validate_curve(self.read());self.drag=(row,column,curve)
                self.rows={i.row() for i in self.table.selectedIndexes()} if row in {i.row() for i in self.table.selectedIndexes()} else {row}
                event.accept();return
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self.drag:
            row,column,original=self.drag;curve=copy.deepcopy(original);x,y=self.unmap_value(self.mapToScene(event.position().toPoint()));key=curve['keys'][row]
            if column==0:
                dx=round(x)-key[0];dy=y-key[1]
                for r in self.rows:curve['keys'][r][0]+=dx;curve['keys'][r][1]+=dy
            elif abs(x-key[0])>1e-6:key[column]=(y-key[1])/(x-key[0])
            try:validate_curve(curve)
            except ValueError:return
            # Keep row order stable during a drag; normalize on release.
            self.table.blockSignals(True)
            for r,k in enumerate(curve['keys']):
                for c,v in enumerate(k):self.table.setItem(r,c,QTableWidgetItem(str(v)))
            self.table.blockSignals(False);self.plot();event.accept();return
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if self.drag:self.drag=None;set_table(self.table,self.read());self.plot();event.accept();return
        super().mouseReleaseEvent(event)
    def keyPressEvent(self,event):
        if event.key()==Qt.Key_Escape and self.drag:
            curve=self.drag[2];self.drag=None;set_table(self.table,curve);self.plot();return
        super().keyPressEvent(event)

def set_table(table,curve):
    curve=validate_curve(curve);table.blockSignals(True);table.setRowCount(len(curve['keys']))
    for row,key in enumerate(curve['keys']):
        for col,value in enumerate(key):table.setItem(row,col,QTableWidgetItem(str(value)))
    table.blockSignals(False)

def add_curve_tools(owner,layout,table,combo,read,plot):
    row=QHBoxLayout();layout.addLayout(row)
    def copy_keys():
        try:
            curve=validate_curve(read());selected=sorted({i.row() for i in table.selectedIndexes()})
            if selected:curve['keys']=[curve['keys'][i] for i in selected]
            QApplication.clipboard().setText(json.dumps({'nukify_curve':curve}))
        except (ValueError,AttributeError) as exc:owner.error(str(exc))
    def paste_keys():
        try:
            curve=validate_curve(json.loads(QApplication.clipboard().text())['nukify_curve']);current=validate_curve(read())
            merged={k[0]:k for k in current['keys']};merged.update({k[0]:k for k in curve['keys']});curve['keys']=list(merged.values())
            set_table(table,curve);combo.setCurrentText(curve['interpolation']);plot()
        except (ValueError,KeyError,TypeError,AttributeError) as exc:owner.error(str(exc))
    def change_time():
        scale,ok=QInputDialog.getDouble(owner,tr('Retime'),tr('Escala de tiempo'),1,.001,1000,3)
        if not ok:return
        offset,ok=QInputDialog.getInt(owner,tr('Retime'),tr('Desplazamiento en frames'),0,-100000,100000)
        if not ok:return
        try:set_table(table,retime(read(),scale,offset,owner.project['frame']));plot()
        except (ValueError,AttributeError) as exc:owner.error(str(exc))
    for title,callback in [('Copiar claves',copy_keys),('Pegar claves',paste_keys),('Retime',change_time)]:
        button=QPushButton(tr(title));button.clicked.connect(callback);row.addWidget(button)
