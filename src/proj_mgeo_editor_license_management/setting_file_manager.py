import json
import os

from proj_mgeo_editor_license_management.define import *
from proj_mgeo_editor_license_management.singleton import SingletonInstane
from proj_mgeo_editor_license_management.structure import JsonSerializable
from proj_mgeo_editor_license_management.util import *

# ============================================================================
# setting file

class SettingData(JsonSerializable):
    def __init__(self, isRememberAccount, id, pw, lastLogin, sessionRefreshTime, isDebug, service_url, debug_url, editor_type):
        self.isRememberAccount = isRememberAccount
        self.id = id
        self.pw = pw
        self.lastLogin = lastLogin
        self.sessionRefreshTime = sessionRefreshTime
        self.isDebug = isDebug
        self.serviceUrl = service_url
        self.debugUrl = debug_url
        self.editor_type = editor_type

class SettingFileManager(SingletonInstane):
    def __init__(self):
        # default data
        self.data = SettingData("False", "", "", "", "60", "False", "http://ec2-54-180-34-141.ap-northeast-2.compute.amazonaws.com", "http://ec2-52-78-167-130.ap-northeast-2.compute.amazonaws.com", "None")
        
    def save(self):        
        dic = self.data.to_dic()        
        print(Define.setting_file_path)
        try:           
            with open(Define.setting_file_path, 'w', encoding="utf-8") as setting_file:
                json.dump(dic, setting_file, ensure_ascii=False, indent="\t")
        except:
            Util.open_popup_window("Error", "setting file Path : " + Define.setting_file_path)

    def load(self):
        if os.path.isfile(Define.setting_file_path) == False:
            return

        print(Define.setting_file_path)

        with open(Define.setting_file_path) as json_file:
            temp = json.load(json_file)
            self.data.isRememberAccount = str(temp['isRememberAccount'])
            self.data.id = temp['id']
            self.data.pw = temp['pw']
            self.data.lastLogin = temp['lastLogin']
            self.data.sessionRefreshTime = temp['sessionRefreshTime']
            self.data.isDebug = str(temp['isDebug'])
            self.data.serviceUrl = temp['serviceUrl']
            self.data.debugUrl = temp['debugUrl']
            self.data.editor_type = temp['editor_type']
