from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import *
from PyQt5.uic.properties import QtWidgets
from iso3166 import Country, countries

from proj_mgeo_editor_license_management.uic.sign_up import Ui_sign_up

from .rest_api_manager import *
from .util import Util
from define import *

# form_class = uic.loadUiType(Define.sign_up_window_path)[0]

class SignUpWindow(QMainWindow):
    def __init__(self, SignInWindow):
        super().__init__()
        self.ui = Ui_sign_up()
        self.ui.setupUi(self)
        # self.setupUi(self)
        self.signinWindow = SignInWindow

        self.setWindowIcon(QtGui.QIcon(Define.map_icon))

        # ui
        self.ui.pushButton_signup.clicked.connect(self.sign_up_button_clicked)        
        self.ui.lineEdit_pw.setEchoMode(QLineEdit.Password)
        self.ui.lineEdit_pwConfirm.setEchoMode(QLineEdit.Password)

        for c in countries:
            self.ui.comboBox_country.addItem(c.name)

        c_code = Util.get_my_country_code()
        c_name = countries.get(c_code)
        self.ui.comboBox_country.setCurrentText(c_name.name)
        
    def sign_up_button_clicked(self):        
        id = self.ui.lineEdit_id.text()
        pw = self.ui.lineEdit_pw.text()
        pw_confirm = self.ui.lineEdit_pwConfirm.text()
        name = self.ui.lineEdit_name.text()
        #country = self.lineEdit_country.text()
        country_name = self.ui.comboBox_country.currentText()
        country_code = countries.get(country_name).alpha2

        errRes = ErrorCheck().edit_userinfo_check(id, pw, pw_confirm, country_code, name)
        if errRes[0] == False:
            self.statusBar().showMessage(errRes[1])
            return

        instance = RestApiManager().instance()
        result = instance.sign_up(id, pw, pw_confirm, country_code, name)    
        if result.success:
            msg = "Sign up success"
            self.statusBar().showMessage(msg)
            Util.open_popup_window("Congratulation!", msg)

            self.signinWindow.reset()
            self.signinWindow.show()            
            self.close()
        else:
            print(result.error)
            self.statusBar().showMessage(result.error)

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.signinWindow.show()        
        return super().closeEvent(a0)