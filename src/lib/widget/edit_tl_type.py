import sys
from PyQt5.QtCore    import *
from PyQt5.QtWidgets import *

class EditTLType(QDialog):
    def __init__(self, parent=None, signal=None):
        super(EditTLType, self).__init__(parent)
        self.item_type = ['car', 'bus', 'pedestrian', 'etc']
        self.item_ori = ['horizontal', 'vertical']
        self.item_sub_type = ['red', 'yellow', 'left', 'right', 'upperleft', 'upperright', 'lowerleft', 'lowerright', 'uturn', 'straight']
        layout = QVBoxLayout()

        self.combobox = QComboBox()
        for i, item in enumerate(self.item_type):
            self.combobox.addItem(item)
        if signal.type in self.item_type:
            self.combobox.setCurrentIndex(self.item_type.index(signal.type))
        layout.addWidget(self.combobox)

        self.oribox = QComboBox()
        for i, item in enumerate(self.item_ori):
            self.oribox.addItem(item)
        if signal.type == 'car' and signal.orientation in self.item_ori:
            self.oribox.setCurrentIndex(self.item_ori.index(signal.orientation))
        layout.addWidget(self.oribox)

        for i, item in enumerate(self.item_sub_type):
            self.item_sub_type[i] = QCheckBox(item)
            if signal.type == 'car' and item in signal.sub_type:
                self.item_sub_type[i].setChecked(True)
            layout.addWidget(self.item_sub_type[i])

        button = QPushButton('OK', self)
        button.clicked.connect(self.accept) 

        layout.addWidget(button)
        self.setLayout(layout)
        self.setWindowTitle('Edit TL Type')        

    def showDialog(self):
        return super().exec_()

    def accept(self):
        self.tl_type = self.combobox.currentText()
        self.tl_ori = self.oribox.currentText()
        self.tl_sub_type = []
        for i, item in enumerate(self.item_sub_type):
            if item.checkState():
                self.tl_sub_type.append(item.text())
        self.done(1)