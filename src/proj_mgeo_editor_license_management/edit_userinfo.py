from PyQt5.uic.properties import QtWidgets
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import *
from proj_mgeo_editor_license_management.define import Define
from proj_mgeo_editor_license_management.enumeration import ErrorCode
from proj_mgeo_editor_license_management .rest_api_manager import *
from iso3166 import countries
from proj_mgeo_editor_license_management.uic.edit_userinfo import Ui_edit_user_info

from proj_mgeo_editor_license_management.util import Util

# form_class = uic.loadUiType(Define.edituser_window_path)[0]

class EditUserInfo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_edit_user_info()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(Define.map_icon))
        # ui
        self.ui.pushButton_ok.clicked.connect(self.ok_button_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.cancel_button_clicked)

        for c in countries:
            self.ui.comboBox_country.addItem(c.name)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        instance = RestApiManager().instance()
        self.set(instance.user_info)
        print("show edit window")
        #self.set()
        return super().showEvent(a0)   

    def set(self, userinfo):
        self.id = userinfo.customer_id
        # self.admin_key = userinfo.session_key
        self.ui.lineEdit_pw.setText("")
        self.ui.lineEdit_pw.setEchoMode(QLineEdit.Password)
        self.ui.lineEdit_pwConfirm.setText("")
        self.ui.lineEdit_pwConfirm.setEchoMode(QLineEdit.Password)
        self.ui.label_id.setText(userinfo.customer_name)
        self.ui.lineEdit_name.setText(userinfo.organization)

        c_info = countries.get(userinfo.nation)
        self.ui.comboBox_country.setCurrentText(c_info.name)
        #self.lineEdit_country.setText(userinfo.nation)

        if userinfo.is_admin_account == False:
            self.ui.lineEdit_admin_key.setVisible(False)
            self.ui.label_admin_key.setVisible(False)
        #self.lineEdit_admin_key.setText("")

        self.statusBar().showMessage("")
        
    def ok_button_clicked(self):
        pw = self.ui.lineEdit_pw.text()
        pw_confirm = self.ui.lineEdit_pwConfirm.text()
        name = self.ui.lineEdit_name.text()
        
        country_name = self.ui.comboBox_country.currentText()
        country_code = countries.get(country_name).alpha2
        input_key = self.ui.lineEdit_admin_key.text()

        errRes = ErrorCheck().password_retype_check(pw, pw_confirm)
        if errRes[0] == False:
            self.statusBar().showMessage(errRes[1])
            return        
        
        instance = RestApiManager().instance()
        res = instance.modify_userinfo(self.id, country_code, name, input_key, pw, pw_confirm)
        if res.success:
            instance.user_info.nation = res.nation
            instance.user_info.organization = res.organization
            self.statusBar().showMessage("Edit userinfo success")
        else:
            self.statusBar().showMessage(res.error)
            if res.value == ErrorCode.ADMIN_KEY_NOT_CORRECT:
                msg = "Incorrect admin key. Admin key is required for changing user information. Admin key is provided to the license manager in your organization."
                Util.open_popup_window("Warning", msg)
                self.statusBar().showMessage(msg)

    def cancel_button_clicked(self):
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent):        
        return super().closeEvent(a0)
