# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import PyOpenColorIO as ocio
import numpy as np
from PySide6.QtWidgets import QDialog,QFormLayout,QComboBox,QPushButton,QFileDialog,QDialogButtonBox,QLabel


def display_processor(path,display,view):
    config=ocio.Config.CreateFromFile(path)
    transform=ocio.DisplayViewTransform(src=ocio.ROLE_SCENE_LINEAR,display=display,view=view)
    return config.getProcessor(transform).getDefaultCPUProcessor()


class ColorUI:
    def color_settings(self):
        dialog=QDialog(self);dialog.setWindowTitle('Color Management');layout=QFormLayout(dialog)
        state={'path':self.project.get('ocio') or str(Path(self.project['blender']).parent/'4.5/datafiles/colormanagement/config.ocio')}
        label=QLabel(state['path']);label.setWordWrap(True);layout.addRow('Config',label)
        display=QComboBox();view=QComboBox()
        def load():
            config=ocio.Config.CreateFromFile(state['path']);config.validate();state['config']=config
            display.clear();display.addItems(list(config.getDisplays()))
        def views():
            view.clear()
            if display.currentText():view.addItems(list(state['config'].getViews(display.currentText())))
        display.currentTextChanged.connect(views)
        def choose():
            path,_=QFileDialog.getOpenFileName(self,'OCIO config','','OpenColorIO (*.ocio)')
            if path:
                previous=state['path'];state['path']=path
                try:load();label.setText(path)
                except Exception as exc:state['path']=previous;self.error(str(exc))
        b=QPushButton('Elegir config OCIO');b.clicked.connect(choose);layout.addRow(b)
        try:load()
        except Exception as exc:self.error(str(exc));return
        display.setCurrentText(self.project.get('display',state['config'].getDefaultDisplay()))
        view.setCurrentText(self.project.get('view','Standard'))
        layout.addRow('Display',display);layout.addRow('View',view)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);layout.addRow(buttons);buttons.rejected.connect(dialog.reject)
        def save():
            try:
                processor=display_processor(state['path'],display.currentText(),view.currentText())
                self.checkpoint();self.project.update(ocio=state['path'],display=display.currentText(),view=view.currentText())
                self.viewer.ocio_processor=processor
                self.viewer.display_cache.clear();self.viewer.transform.setCurrentText('OCIO');self.viewer.refresh()
                self.engine.stop();self.changed();dialog.accept()
            except Exception as exc:self.error(str(exc))
        buttons.accepted.connect(save);dialog.exec()

    def restore_color(self):
        if self.project.get('ocio'):
            self.viewer.ocio_processor=display_processor(self.project['ocio'],self.project['display'],self.project['view'])
            self.viewer.display_cache.clear();self.viewer.transform.setCurrentText('OCIO')
        else:
            self.viewer.ocio_processor=None;self.viewer.transform.setCurrentText('sRGB');self.viewer.display_cache.clear()
