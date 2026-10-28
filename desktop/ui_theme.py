# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared desktop design tokens, vector icons and wrapping tool strips."""
from PySide6.QtCore import Qt,QRect,QSize
from PySide6.QtGui import QIcon,QIconEngine,QPainter,QPen,QColor,QPainterPath,QPixmap
from PySide6.QtWidgets import QLayout,QSizePolicy,QPushButton

COLORS=dict(bg='#242424',panel='#303030',field='#202020',border='#454545',text='#dddddd',muted='#a5a5a5',accent='#e6a34b',selected='#477eb4')
STYLE='''
QWidget { background:#303030; color:#dddddd; font-family:Segoe UI; font-size:12px; }
QMainWindow, QStatusBar { background:#242424; }
QPushButton, QToolButton { background:#393939; border:1px solid #494949; border-radius:4px; padding:4px 8px; min-height:20px; }
QPushButton:hover, QToolButton:hover { background:#494949; border-color:#686868; }
QPushButton:pressed, QToolButton:pressed { background:#252525; }
QPushButton:checked, QToolButton:checked { background:#365975; border-color:#6095bf; color:#ffffff; }
QPushButton:focus, QToolButton:focus, QLineEdit:focus, QComboBox:focus, QAbstractSpinBox:focus { border:1px solid #e6a34b; }
QPushButton:disabled, QToolButton:disabled { color:#777777; background:#2b2b2b; border-color:#383838; }
QPushButton[primary="true"] { background:#97602b; border-color:#c08a48; color:#ffffff; }
QPushButton[primary="true"]:hover { background:#ae7335; }
QLineEdit, QAbstractSpinBox, QComboBox { background:#202020; border:1px solid #454545; border-radius:3px; padding:3px 5px; min-height:20px; selection-background-color:#477eb4; }
QScrollArea, QGraphicsView { border:0; }
QTabWidget::pane { border:1px solid #414141; }
QTabBar::tab { background:#272727; padding:8px 14px; border-bottom:2px solid #272727; }
QTabBar::tab:selected { background:#303030; border-bottom-color:#e6a34b; }
QSplitter::handle { background:#202020; width:5px; height:5px; }
QSplitter::handle:hover { background:#63503a; }
QMenu { background:#292929; border:1px solid #555555; padding:4px; }
QMenu::item { padding:7px 24px; border-radius:3px; }
QMenu::item:selected { background:#477eb4; }
QPlainTextEdit, QTableWidget, QTreeWidget { background:#242424; border:1px solid #454545; alternate-background-color:#2c2c2c; selection-background-color:#365975; }
QHeaderView::section { background:#383838; padding:5px; border:0; }
QToolTip { background:#171717; color:#eeeeee; border:1px solid #666666; padding:5px; }
QScrollBar:vertical { background:#272727; width:10px; margin:0; }
QScrollBar:horizontal { background:#272727; height:10px; margin:0; }
QScrollBar::handle { background:#606060; border-radius:4px; min-height:24px; min-width:24px; }
QScrollBar::handle:hover { background:#808080; }
QScrollBar::add-line, QScrollBar::sub-line { width:0; height:0; }
QScrollBar::add-page, QScrollBar::sub-page { background:none; }
QStatusBar { color:#aaaaaa; }
'''

PATHS={
 'key':[(12,3,21,12,12,21,3,12,12,3)],
 'open':[(2,6,8,6,10,8,21,8,18,19,2,19,2,6),(2,6,2,4,9,4,11,6)],
 'save':[(4,3,18,3,21,6,21,21,3,21,3,3,4,3),(7,3,7,10,16,10,16,3),(7,21,7,14,17,14,17,21)],
 'export':[(4,14,4,21,20,21,20,14),(12,17,12,3),(7,8,12,3,17,8)],
 'viewer':[(2,4,22,4,22,18,2,18,2,4),(8,22,16,22),(12,18,12,22)],
 'nodes':[(2,2,9,2,9,8,2,8,2,2),(15,16,22,16,22,22,15,22,15,16),(5,8,5,13,18,13,18,16)],
 'fit':[(3,9,3,3,9,3),(15,3,21,3,21,9),(21,15,21,21,15,21),(9,21,3,21,3,15)],
 'plus':[(12,4,12,20),(4,12,20,12)],
 'reset':[(5,8,5,3),(5,8,10,8),(5,8,9,4,16,4,21,10,20,17,15,21,8,20,4,16)],
 'layers':[(2,8,12,2,22,8,12,14,2,8),(2,12,12,18,22,12),(2,16,12,22,22,16)],
 'swap':[(3,7,21,7,17,3),(21,17,3,17,7,21)],
 'play':[(7,3,21,12,7,21,7,3)], 'pause':[(7,4,7,20),(17,4,17,20)],
 'first':[(5,4,5,20),(19,4,9,12,19,20)], 'prev':[(16,4,6,12,16,20)],
 'next':[(8,4,18,12,8,20)], 'last':[(19,4,19,20),(5,4,15,12,5,20)],
 'loop':[(3,11,3,6,19,6,16,3),(21,13,21,18,5,18,8,21)],
 'image':[(3,3,21,3,21,21,3,21,3,3),(3,18,9,11,14,16,18,12,21,16)],
 'color':[(3,18,9,6,15,18,3,18),(12,3,21,3,21,12)],
 'filter':[(3,3,21,3,14,12,14,20,10,22,10,12,3,3)],
 'transform':[(3,8,3,3,8,3),(16,3,21,3,21,8),(21,16,21,21,16,21),(8,21,3,21,3,16),(7,7,17,7,17,17,7,17,7,7)],
 'draw':[(3,21,5,14,17,2,22,7,10,19,3,21),(5,14,10,19)],
 'cube':[(3,6,12,2,21,6,21,18,12,22,3,18,3,6,12,10,21,6),(12,10,12,22)],
 'tools':[(3,6,21,6),(3,12,21,12),(3,18,21,18),(8,3,8,9),(16,9,16,15),(10,15,10,21)],
}
class VectorIcon(QIconEngine):
    def __init__(self,name):super().__init__();self.name=name
    def clone(self):return VectorIcon(self.name)
    def pixmap(self,size,mode,state):
        result=QPixmap(size);result.fill(Qt.transparent);painter=QPainter(result);self.paint(painter,QRect(0,0,size.width(),size.height()),mode,state);painter.end();return result
    def paint(self,painter,rect,mode,state):
        painter.save();painter.setRenderHint(QPainter.Antialiasing);side=min(rect.width(),rect.height());painter.translate(rect.x()+(rect.width()-side)/2,rect.y()+(rect.height()-side)/2);painter.scale(side/24,side/24)
        painter.setPen(QPen(QColor('#777777' if mode==QIcon.Disabled else '#eeeeee'),1.7,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
        for coords in PATHS.get(self.name,PATHS['tools']):
            path=QPainterPath();path.moveTo(coords[0],coords[1])
            for i in range(2,len(coords),2):path.lineTo(coords[i],coords[i+1])
            painter.drawPath(path)
        painter.restore()
_icons={}
def icon(name):
    # Keep the Python virtual engine alive while Qt retains copies of its QIcon.
    if name not in _icons:
        engine=VectorIcon(name);_icons[name]=(engine,QIcon(engine))
    return _icons[name][1]
def decorate(button,name,tooltip=None,compact=False):
    from i18n import tr
    if tooltip: tooltip=tr(tooltip)
    text=button.text();button.setIcon(icon(name));button.setIconSize(QSize(16,16));button.setAccessibleName(tooltip or text);button.setToolTip(tooltip or button.toolTip() or text)
    button.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Fixed)
    if compact:button.setText('');button.setFixedWidth(30)
    return button

class FlowLayout(QLayout):
    """Tool rows wrap at the available width without hiding commands."""
    def __init__(self):super().__init__();self.items=[];self.setContentsMargins(0,0,0,0);self.setSpacing(4)
    def addItem(self,item):self.items.append(item)
    def addWidget(self,widget,*args):super().addWidget(widget)
    def addStretch(self,*args):pass
    def count(self):return len(self.items)
    def itemAt(self,index):return self.items[index] if 0<=index<len(self.items) else None
    def takeAt(self,index):return self.items.pop(index) if 0<=index<len(self.items) else None
    def expandingDirections(self):return Qt.Orientations(0)
    def hasHeightForWidth(self):return True
    def heightForWidth(self,width):return self.arrange(QRect(0,0,width,0),True)
    def setGeometry(self,rect):super().setGeometry(rect);self.arrange(rect,False)
    def sizeHint(self):return self.minimumSize()
    def minimumSize(self):
        size=QSize()
        for item in self.items:size=size.expandedTo(item.minimumSize())
        return size
    def arrange(self,rect,test):
        x,y=rect.x(),rect.y();height=0
        for item in self.items:
            if item.isEmpty():continue
            size=item.widget().sizeHint() if item.widget() else item.sizeHint();width=min(size.width(),max(1,rect.width()))
            if x>rect.x() and x+width>rect.right()+1:x=rect.x();y+=height+self.spacing();height=0
            if not test:item.setGeometry(QRect(x,y,width,size.height()))
            x+=width+self.spacing();height=max(height,size.height())
        return y+height-rect.y()
