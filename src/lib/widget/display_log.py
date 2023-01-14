import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger
from lib.common.log_type import LogType

from os.path import join, getsize, isfile, isdir, splitext
import time

import inspect
import textwrap
from collections import OrderedDict, UserString
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *


class LogExpander(QWidget):
    """QToolButton을 이용하여 확장 가능하도록 Log Widget을 구성한다"""
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.log_msg = None
        self.checked = True
        self.splitter = None

        self.toggleButton = QToolButton()
        self.toggleButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(QtCore.Qt.RightArrow)
        self.toggleButton.setText(self.log_msg)
        self.toggleButton.setStyleSheet("border: 0px")
        self.toggleButton.setCheckable(True)
        self.toggleButton.setChecked(False)
        self.toggleButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toggleButton.clicked.connect(self.clickLog)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.contentArea = QWidget()
        horizontalSpacer = QSpacerItem(1, 1, QSizePolicy.Expanding)

        
        self.text_area = QTextEdit()
        self.text_area.setMinimumHeight(25)
        self.text_area.setTextInteractionFlags(Qt.TextSelectableByMouse)


        # 버튼 레이아웃
        self.btnLayout = QHBoxLayout()
        self.clearBtn = QPushButton("Clear")

        self.combobox = QComboBox()
        for i in LogType:
            self.combobox.addItem(i.name)
        self.combobox.setCurrentIndex(2)

        self.btnLayout.addWidget(self.toggleButton)
        self.btnLayout.addSpacerItem(horizontalSpacer)
        self.btnLayout.addWidget(self.combobox)
        self.btnLayout.addWidget(self.clearBtn)
        self.combobox.setVisible(False)
        self.clearBtn.setVisible(False)

        self.mainLayout.addLayout(self.btnLayout)
        self.mainLayout.addWidget(self.contentArea)
        super().setLayout(self.mainLayout)

    def setLayout(self, contentLayout):
        self.contentArea.setLayout(contentLayout)
        
    def setText(self, last_msg):
        if len(last_msg) > 180:
            self.log_msg = last_msg[0:180]
        else:
            self.log_msg = last_msg
        self.toggleButton.setText(self.log_msg)
        QApplication.processEvents()

    def clickLog(self, event):
        arrow_type = QtCore.Qt.DownArrow if event else QtCore.Qt.RightArrow
        self.toggleButton.setArrowType(arrow_type)

        self.combobox.setVisible(True) if event else self.combobox.setVisible(False)
        self.clearBtn.setVisible(True) if event else self.clearBtn.setVisible(False)
        self.text_area.setVisible(True) if event else self.text_area.setVisible(False)
        self.splitter.setSizes([100, 1]) if event else self.splitter.setSizes([10000, 1])

    def lockSplitter(self):
        if self.toggleButton.arrowType() == QtCore.Qt.RightArrow:
            self.splitter.setSizes([10000, 1])

class LogWidget(QWidget):
    """확장 가능한 Log Widget을 구성한다"""
    def __init__(self):
        super().__init__()
        self.collapsible = None
        self.text_area = None
        self.initUI()

    def initUI(self):
        self.collapsible = LogExpander(self)
        self.text_area = self.collapsible.text_area
        self.scrollbar = self.text_area.verticalScrollBar()
        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(0, 0, 0, 0)
        contents_vbox = QVBoxLayout()
        contents_vbox.setContentsMargins(0, 0, 0, 0)
        contents_vbox.addWidget(self.text_area)
        self.text_area.setVisible(False) 
        self.collapsible.setLayout(contents_vbox)
        self.vbox.addWidget(self.collapsible)
        self.vbox.setAlignment(Qt.AlignTop)
        self.setLayout(self.vbox)

        
    