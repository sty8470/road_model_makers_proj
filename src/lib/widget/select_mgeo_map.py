import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class SelectMgeoMap(QDialog):
    
    def __init__(self, mgeo_map_dict):
        super(SelectMgeoMap, self).__init__()
        self.mgeo_map_dict = mgeo_map_dict
        self.initUI()
        
    def initUI(self):
        self.check_list = []
        if self.mgeo_map_dict != None:
            widgetLayout = QGridLayout()
        
            groupBox = QGroupBox('Select MGeo Map to Merge')
            self.vbox = QVBoxLayout()
    
            for key in self.mgeo_map_dict.keys():
                self.checkbox = QCheckBox(key, self)
                self.checkbox.setCheckState(Qt.Unchecked)
                
                self.vbox.addWidget(self.checkbox)
                groupBox.setLayout(self.vbox)
                widgetLayout.addWidget(groupBox, 0, 0)
            
            self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.buttonbox.accepted.connect(self.buttonClicked)
            self.buttonbox.rejected.connect(self.reject)
            widgetLayout.addWidget(self.buttonbox, 2, 0)
            
            self.setLayout(widgetLayout)
            self.setWindowTitle('Select MGeo Map to Merge')

        else:
            raise Exception('[Merge Failed]: There are not enough maps to merge')
        
    def showDialog(self):
        return super().exec_()
    
    def buttonClicked(self):
        for i in range(self.vbox.count()):
            chBox = self.vbox.itemAt(i).widget()
            
            if chBox.isChecked():
                self.check_list.append(chBox.text())
        self.done(1)
        
    def close(self):
        self.done(0)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SelectMgeoMap()
    ex.showDialog()
    sys.exit(app.exec_())