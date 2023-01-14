
import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

# import platform
# import datetime
# import ctypes
# if platform.system() == "Windows":
#     # 작업 표시줄에 아이콘을 표시하기 위해서 Process App User Model ID 등록
#     myappid = 'morai.mapeditor' # arbitrary string
#     ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# from lib.common.logger import Logger
# import numpy as np
# import json
# import shutil

from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import Qt, QMetaObject, QPoint, QSize, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QIcon

from GUI.ui_main import Ui_MainWindow


class PyQTWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    qtWindow = PyQTWindow()  
    qtWindow.show()
    sys.exit(app.exec_())
