# SPDX-License-Identifier: GPL-3.0-or-later
import json
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QDialog,QVBoxLayout,QTableWidget,QTableWidgetItem,QDialogButtonBox,QKeySequenceEdit,QPushButton,QFileDialog
from pathlib import Path
from delivery import atomic_json

DEFAULTS={'Crear nodo':'Tab','Viewer A':'1','Viewer B':'2','Encuadrar':'F','Encuadrar todo':'Home','Seleccionar todo':'Ctrl+A',
          'Copiar':'Ctrl+C','Pegar':'Ctrl+V','Duplicar':'Ctrl+D','Bypass':'D','Eliminar':'Del','Maximizar panel':'Space'}

def validate_shortcuts(mapping):
    if not isinstance(mapping,dict) or set(mapping)-set(DEFAULTS):raise ValueError('Preset de shortcuts no compatible')
    merged=dict(DEFAULTS,**mapping);result={}
    reserved={'Ctrl+S','Ctrl+Shift+S','Ctrl+O','Ctrl+Z','Ctrl+Shift+Z','Esc'}
    for key,value in merged.items():
        if not isinstance(value,str):raise ValueError('Cada atajo debe ser texto')
        seq=QKeySequence(value);normalized=seq.toString()
        if value and (not normalized or seq.isEmpty() or seq.count()!=1 or seq[0].key()==0 or normalized in reserved):raise ValueError('Atajo invalido o reservado: '+value)
        result[key]=normalized
    used=[v for v in result.values() if v]
    if len(used)!=len(set(used)):raise ValueError('Hay atajos duplicados')
    return result


class ShortcutUI:
    def load_shortcuts(self):
        self.graph_shortcuts=dict(DEFAULTS)
        try:self.graph_shortcuts=validate_shortcuts(json.loads((self.app_data/'shortcuts.json').read_text()))
        except (ValueError,OSError):pass

    def shortcuts_dialog(self):
        dialog=QDialog(self);dialog.setWindowTitle('Shortcuts del Node Graph');layout=QVBoxLayout(dialog)
        table=QTableWidget(len(DEFAULTS),2);table.setHorizontalHeaderLabels(['Comando','Atajo']);editors={}
        for row,key in enumerate(DEFAULTS):
            item=QTableWidgetItem(key);table.setItem(row,0,item)
            editor=QKeySequenceEdit(QKeySequence(self.graph_shortcuts[key]));table.setCellWidget(row,1,editor);editors[key]=editor
        layout.addWidget(table);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel|QDialogButtonBox.RestoreDefaults);layout.addWidget(buttons)
        buttons.rejected.connect(dialog.reject)
        buttons.button(QDialogButtonBox.RestoreDefaults).clicked.connect(lambda:[e.setKeySequence(QKeySequence(DEFAULTS[k])) for k,e in editors.items()])
        def read_editors():return validate_shortcuts({k:e.keySequence().toString() for k,e in editors.items()})
        def import_preset():
            path,_=QFileDialog.getOpenFileName(self,'Importar shortcuts','','JSON (*.json)')
            if not path:return
            try:
                preset=json.loads(Path(path).read_text(encoding='utf-8'))
                if not isinstance(preset,dict):raise ValueError('Preset invalido')
                if preset.get('version')!=1:raise ValueError('Version de preset no compatible')
                mapping=validate_shortcuts(preset['shortcuts'])
                for key,value in mapping.items():editors[key].setKeySequence(QKeySequence(value))
            except (ValueError,KeyError,OSError,TypeError) as exc:self.error(str(exc))
        def export_preset():
            try:
                mapping=read_editors();path,_=QFileDialog.getSaveFileName(self,'Exportar shortcuts','nukify-shortcuts.json','JSON (*.json)')
                if path:atomic_json(path,{'version':1,'shortcuts':mapping})
            except (ValueError,OSError) as exc:self.error(str(exc))
        for title,callback in [('Importar preset',import_preset),('Exportar preset',export_preset)]:
            button=QPushButton(title);button.clicked.connect(callback);layout.addWidget(button)
        def save():
            try:
                mapping=read_editors();atomic_json(self.app_data/'shortcuts.json',mapping);self.graph_shortcuts=mapping;dialog.accept()
            except (ValueError,OSError) as exc:self.error(str(exc))
        buttons.accepted.connect(save);dialog.resize(540,560);dialog.exec()
