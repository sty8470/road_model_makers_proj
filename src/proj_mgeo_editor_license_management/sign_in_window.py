import sys

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import Qt

from define import *
#from proj_mgeo_editor_license_management.setting_file_manager import SettingFileManager
from proj_mgeo_editor_license_management.rest_api_manager import *
from proj_mgeo_editor_license_management.setting_file_manager import SettingFileManager
from proj_mgeo_editor_license_management.sign_up_window import SignUpWindow
from proj_mgeo_editor_license_management.launcher_window import *
from proj_mgeo_editor_license_management.uic.sign_in import Ui_sign_in
from proj_mgeo_editor_license_management.util import Util

# form_class = uic.loadUiType(Define.sign_in_window_path)[0]

#class SignInWindow(QMainWindow, form_class):
class SignInWindow(QMainWindow):
    def __init__(self, parent=None) :
        super().__init__()
        self.ui = Ui_sign_in()
        self.ui.setupUi(self)
        
        self.restManager = RestApiManager().instance()        
        self.signupWindow = SignUpWindow(self)

        # control binding
        self.ui.lineEdit_id.textChanged.connect(self.id_lineEdit_TextChanged)
        self.ui.lineEdit_pw.textChanged.connect(self.pw_lineEdit_TextChanged)
        self.ui.lineEdit_pw.setEchoMode(QLineEdit.Password)
        self.ui.pushButton_signin.clicked.connect(
            lambda checked: self.signin_button_clicked(self.mainWindow)
        )

        self.ui.pushButton_signup.clicked.connect(
            lambda checked: self.sign_up_button_clicked(self.signupWindow)
        )

        self.ui.checkBox_remember.stateChanged.connect(self.remember_account_checkbox_stateChanged)
        # self.pushButton_close.clicked.connect(self.close_button_clicked)

        self.mainWindow = LauncherWindow(self)
        RestApi.url = Define.server_url

        self.setting = SettingFileManager().instance()

        if self.setting.data.isRememberAccount == "True":
            self.ui.lineEdit_id.setText(self.setting.data.id)
            self.ui.lineEdit_pw.setText(self.setting.data.pw)
            self.ui.checkBox_remember.setChecked(bool(self.setting.data.isRememberAccount))

    def reset(self):
        self.lineEdit_id.setText("")
        self.lineEdit_pw.setText("")
        self.checkBox_remember.setChecked(False)

    # key event
    def keyPressEvent(self, event):
        try:
            if event.key() == 16777220:
                self.signin_button_clicked(self.mainWindow)
                print("enter")
            if event.key() == Qt.Key_Escape:
                print("escape")
        except:
            print("input error")       

    # control event
    def id_lineEdit_TextChanged(self):
        # self.id = self.lineEdit_id.text()
        self.setting.data.id = self.ui.lineEdit_id.text()

    def pw_lineEdit_TextChanged(self):
        # self.pw = self.lineEdit_pw.text()
        self.setting.data.pw = self.ui.lineEdit_pw.text()

    def remember_account_checkbox_stateChanged(self):
        self.setting.data.isRememberAccount = self.ui.checkBox_remember.isChecked()
        print(self.setting.data.isRememberAccount)

    def signin_button_clicked(self, window):
        self.statusBar().showMessage("")
        try:            
            errRes = ErrorCheck().sign_in_parameter_check(self.setting.data.id, self.setting.data.pw)
            if  errRes[0] == False:
                self.statusBar().showMessage(errRes[1])
                return
            
            #print("hwjung : 111")
            userinfo = self.restManager.sing_in(self.setting.data.id, self.setting.data.pw)            
            if userinfo.success:
                #print("hwjung : 222")
                res = self.restManager.check_program_name_and_version(userinfo.program_name, userinfo.program_version)                
                if res[0] == False:
                    self.statusBar().showMessage(res[1])
                    return

                print("customer id : ", userinfo.customer_id)
                print("customer name : ", userinfo.customer_name)
                print("organization : ", userinfo.organization)

                # start session check
                #print("hwjung : 333")
                self.restManager.start_session_check(userinfo.customer_id, userinfo.session_key)
                #print("hwjung : 444")

                if window.isVisible():
                    window.hide()
                else:
                    window.show()                    
                    self.hide()
            else:
                print(userinfo.error)
                self.statusBar().showMessage(userinfo.error)
        except:
            self.statusBar().showMessage("error")

        #self.settingFileManager.save()
        #self.setting.save()
        SettingFileManager().instance().save()
        #Define.setting.save()
    
    def sign_up_button_clicked(self, window):
        Util.open_popup_window("Evaluation Version Notification", "Not supported in the evaluation version. Please sign-in using the account pre-provided.")
        return

        self.statusBar().showMessage("")
        if window.isVisible():
            window.hide()
        else:
            window.show()
            self.hide()

    def closeEvent(self, a0: QtGui.QCloseEvent):
        #self.settingFileManager.save()      
        #Define.setting.save()  
        SettingFileManager().instance().save()
        self.restManager.thread_stop()
        return super().closeEvent(a0)

    def session_error_check(self):        
        print(datetime.datetime.now(), " : session count : ", self.restManager.session_error_count)

if __name__ == "__main__":            

    app = QApplication(sys.argv)    

    myWindow = SignInWindow()

    myWindow.setWindowIcon(QtGui.QIcon(Define.map_icon))

    myWindow.show()

    app.exec_()