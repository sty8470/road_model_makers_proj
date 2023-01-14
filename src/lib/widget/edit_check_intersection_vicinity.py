import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from lib.mgeo.class_defs import *

class EditCheckIntersectionVicinity(QDialog):
    def __init__(self, mgeo_map_dict):
        super().__init__()
        self.type = None
        self.value= None
        self.mgeo_map_dict = mgeo_map_dict
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Check Intersection Vicinity')

        notice_board = QLabel('Type the threshold of distance: ')
        notice_info = QLabel('The rule of thumb is 80')
        
        noticeEditLayout = QVBoxLayout()
        noticeEditLayout.addSpacing(10)
        noticeEditLayout.addWidget(notice_board)
        noticeEditLayout.addSpacing(5)
        noticeEditLayout.addWidget(notice_info)
        
        lbValue = QLabel('Value :')
        self.txtValue = QLineEdit()
        btn_OK = QPushButton('OK')

        textEditLayout = QHBoxLayout()
        textEditLayout.addWidget(lbValue)
        textEditLayout.addWidget(self.txtValue)

        widgetLayout = QVBoxLayout()
        widgetLayout.addSpacing(10)
        widgetLayout.addLayout(noticeEditLayout)
        widgetLayout.addSpacing(10)
        widgetLayout.addLayout(textEditLayout)
        widgetLayout.addSpacing(10)
        widgetLayout.addWidget(btn_OK)

        self.setLayout(widgetLayout)
        btn_OK.clicked.connect(self.accept)
    
    def accept(self):
        self.value = self.txtValue.text()
        self.done(1)
    
    def close(self):
        self.done(0)
    
    def showDialog(self):
        return super().exec_()
    