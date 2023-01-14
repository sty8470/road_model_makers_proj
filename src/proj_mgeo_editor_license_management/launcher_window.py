import webbrowser

from PyQt5.uic.properties import QtWidgets
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import *
from requests.sessions import Request, session

from proj_mgeo_editor_license_management.edit_userinfo import EditUserInfo
from proj_mgeo_editor_license_management.uic.launcher import Ui_launcher
from proj_mgeo_editor_license_management.userinfo_window import UserInfoWindow
from proj_mgeo_editor_license_management.rest_api_manager import *
from proj_mgeo_editor_morai_opengl.main_opengl_editor import PyQTWindow

from define import *
# form_class = uic.loadUiType(Define.launcher_window_path)[0]

class LauncherWindow(QMainWindow):    
    def __init__(self, SignInWindow) :
        super().__init__()
        self.ui = Ui_launcher()
        self.ui.setupUi(self)                
        
        self.setWindowIcon(QtGui.QIcon(Define.map_icon))
        self.th = None

        self.signinWindow = SignInWindow
        self.userinfo_window = UserInfoWindow()
        self.edit_userinfo_window = EditUserInfo()
        self.mgeo_editor = PyQTWindow()        
        self.ui.pushButton_Launch.clicked.connect(self.launch_mgeo_editor)
        self.ui.action_userinfo.triggered.connect(self.open_userinfo)
        self.ui.action_edit_userinfo.triggered.connect(self.open_edit_userinfo)
        self.ui.actionGo_to_User_Manual.triggered.connect(self.open_user_manual)
        self.ui.actionMorai.triggered.connect(self.open_morai)
        self.ui.actionLogout.triggered.connect(self.logout)

        #self.ui.action_userinfo.setIconVisibleInMenu(False)
        #self.ui.action_edit_userinfo.setIconVisibleInMenu(False)
        #self.ui.actionLogout.setIconVisibleInMenu(False)

        self.ui.action_userinfo.setIcon(QtGui.QIcon(Define.userinfo_icon))
        self.ui.action_edit_userinfo.setIcon(QtGui.QIcon(Define.edit_user_icon))
        self.ui.actionLogout.setIcon(QtGui.QIcon(Define.logout_icon))
        
        # self.pushButton_edit_userinfo.clicked.connect(self.open_edit_userinfo)
        # self.ui.show()

    def init(self, left, top, width, height):
        self.move(left, top)
        self.size(width, height)

    def open_userinfo(self):        
        # print(self.restManager.user_info)
        self.userinfo_window.show()
        # self.userinfo_window.set(self.restManager.user_info)

    def open_edit_userinfo(self):
        self.edit_userinfo_window.show()        

    def open_user_manual(self):
        webbrowser.open('https://help-morai-sim.atlassian.net/wiki/external/1605818/ZWRhMzUxZWIxYjNkNGEwMTliMjNkMzI1ODliYWZlNGE?atlOrigin=eyJpIjoiMzk4OTdkZTJiY2ZjNDg4M2JjMTU0OGY3MDE5ZGM1NzIiLCJwIjoiYyJ9')
        print("open user manual")

    def open_morai(self):
        webbrowser.open('https://www.morai.ai/')

    def launch_mgeo_editor(self):
        print("start mgeo")        
        self.mgeo_editor.launcher_ex.show_editor()
        self.start_session_check()
        self.mgeo_editor.launcher_ex.set_menu_disable(False)
        self.mgeo_editor.launcher_ex.hide_launcher(self)
    
    def start_session_check(self):
        self.th = workThread(parent=self.mgeo_editor)
        self.th.is_session_changed.connect(self.mgeo_editor.launcher_ex.session_error)        
        self.th.start()

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.mgeo_editor.launcher_ex.set_menu_disable(True)
        RestApiManager().instance().thread_stop()        
        if self.th != None:
            self.th.working = False
        self.signinWindow.show()
        return super().closeEvent(a0)

    def logout(self):        
        self.mgeo_editor.launcher_ex.set_menu_disable(True)
        self.close()        

class workThread(QThread):
    is_session_changed = pyqtSignal(bool)

    def __init__(self, is_session_ok=True , parent=None):
        super(workThread, self).__init__(parent)
        self.main = parent
        self.working = True
        self.is_session_ok = is_session_ok

    def run(self):
        while self.working:
            if RestApiManager().instance().session_error_count > 4:
                self.is_session_changed.emit(False)
                # self.working = False

            #if RestApiManager().instance().testCount > 10:
                #self.is_session_changed.emit(False)
            self.sleep(1)