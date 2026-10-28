# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
from PySide6.QtCore import Qt,Signal
from PySide6.QtGui import QPainter,QColor
from PySide6.QtWidgets import QWidget

class CacheStrip(QWidget):
    seek=Signal(int)
    def __init__(self):
        super().__init__();self.setFixedHeight(14);self.first=self.last=1;self.marks={};self.setMouseTracking(True)
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#14191f'));count=max(1,self.last-self.first+1)
        for frame,branches in self.marks.items():
            x=round((frame-self.first)*self.width()/count);w=max(1,round(self.width()/count))
            if 'A' in branches:p.fillRect(x,1,w,5,QColor('#dbac60'))
            if 'B' in branches:p.fillRect(x,8,w,5,QColor('#64b9d4'))
    def frame_at(self,x):return max(self.first,min(self.last,self.first+int(x/max(1,self.width())*(self.last-self.first+1))))
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:self.seek.emit(self.frame_at(event.position().x()))
    def mouseMoveEvent(self,event):
        frame=self.frame_at(event.position().x());branches=self.marks.get(frame,set())
        self.setToolTip(tr('Frame {0}: {1} | A dorado, B azul').format(frame, tr('{0} en cache').format(' / '.join(sorted(branches))) if branches else tr('sin cache')))
