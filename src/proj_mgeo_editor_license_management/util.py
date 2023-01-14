import json
import sys
from urllib.request import urlopen
from urllib import request
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from proj_mgeo_editor_license_management.define import Define
from lib.common.aes_cipher import AESCipher
import os

class Util:
    @staticmethod
    def get_my_country_code():
        try:
            request = "https://geolocation-db.com/json/%"
            with urlopen(request) as url:
                data = json.loads(url.read().decode())
                c_code = data['country_code']
                if c_code == None:
                    return 'KR'
                return c_code
        except:
            return 'KR'

    @staticmethod
    def get_external_ip():
        return request.urlopen('https://ident.me').read().decode('utf8')

    @staticmethod
    def open_popup_window(title, message):
        msg = QMessageBox()
        msg.setWindowIcon(QtGui.QIcon(Define.warning_icon))
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

    @staticmethod
    def get_program_name_and_version_from_user_info():
        aes_cipher = AESCipher()        
        if not os.path.exists(Define.user_file_path):
            aes_cipher.encrypt_file(Define.default_user_file, Define.user_file_path)

        user_info = aes_cipher.decrypt_file_to_json(Define.user_file_path)        
        program_name = user_info['program_key']
        arr = user_info['program_name'].split('(')
        version = arr[1][:-1]
        version = version.replace('v', "")
        return program_name, version
        


# ==================================================================

# util test
class MyWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ut = Util
        ut.open_popup_window("111", "aaa")

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MyWindow()
    window.show()

    app.exec_()

    