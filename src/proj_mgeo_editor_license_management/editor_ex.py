import sys

from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import Qt, QMetaObject, QPoint, QSize, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QIcon

class LauncherBase():
    def __init__(self):
        print("super")

    def set_qtwindow(self, editor):
        self.editor = editor

    def show_editor(self):
        self.editor.show()
    
    def hide_editor(self):
        self.editor.hide()

    def hide_launcher(self, launcher):
        self.launcher = launcher
        self.launcher.hide()

    def show_launcher(self):
        self.launcher.show()

    def session_error(self):
        self.statusBar().showMessage("The session is expired. Save is only supported.")

    def set_menu_disable(self, isActive):        
        print("set_menu_disable")

class LauncherEx(LauncherBase):
    def __init__(self):
        super().__init__()

    def session_error(self):
        super().session_error()      
        self.set_menu_disable(True)
        
    def set_menu_disable(self, isActive):
        self.editor.set_menu_disable(isActive)

class LauncherEx_42dot(LauncherBase):
    def __init__(self):
        super().__init__()

    def session_error(self):        
        super().session_error()
        self.set_menu_disable(True)

    def set_menu_disable(self, isActive):
        print("set_menu_disable 42dot")
        self.editor.set_menu_disable(isActive)