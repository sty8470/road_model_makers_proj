from PyQt5.uic.properties import QtWidgets
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from iso3166 import countries

from proj_mgeo_editor_license_management.rest_api_manager import *
from proj_mgeo_editor_license_management.uic.userinfo import Ui_user_info

from define import *

# form_class = uic.loadUiType(Define.userinfo_window_path)[0]

class UserInfoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_user_info()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(Define.map_icon))
        # ui        
        self.ui.pushButton_ok.clicked.connect(self.ok_button_click)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        instance = RestApiManager().instance()
        self.set(instance.user_info)
        return super().showEvent(a0)

    def closeEvent(self, a0: QtGui.QCloseEvent):
        return super().closeEvent(a0)

    def set(self, userinfo):
        try:
            self.ui.label_id.setText(userinfo.customer_name)
            self.ui.label_name.setText(userinfo.organization)

            c_info = countries.get(userinfo.nation)
            self.ui.label_country.setText(c_info.name)

            humanTime = datetime.datetime.utcfromtimestamp(userinfo.buy_time).strftime('%Y-%m-%d %H:%M:%S')
            self.ui.label_purchase_date.setText(humanTime)
            humanTime = datetime.datetime.utcfromtimestamp(userinfo.expire_time).strftime('%Y-%m-%d %H:%M:%S')
            self.ui.label_expiration_date.setText(humanTime)
            self.ui.labe_seats.setText(str(userinfo.conccurent_max_count))
        except Exception as e:
            print("Error : ", e)                    

    def ok_button_click(self):
        self.close()