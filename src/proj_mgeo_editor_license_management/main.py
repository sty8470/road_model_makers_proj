import sys
import hashlib

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from define import *
from proj_mgeo_editor_morai_opengl.main_opengl_editor import PyQTWindow
from proj_mgeo_editor_license_management.sign_in_window import SignInWindow

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Authentication key is not given. User authentication is necessary")
        app = QApplication(sys.argv)
        window = SignInWindow()
        window.setWindowIcon(QtGui.QIcon(Define.map_icon))
        window.show()
        app.exec_()
    else:
        key = hashlib.sha256(str(sys.argv[1]).encode()).hexdigest()

        if key not in Define.valid_key_dict.keys():
            print("Given authentication key is not valid")
        else:
            app = QApplication([sys.argv[0]])
            window = PyQTWindow()
            window.show()
            window.set_menu_disable(False)
            app.exec_()