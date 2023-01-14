from os import kill
# from tkinter.constants import TRUE
import requests
import threading
import datetime

from proj_mgeo_editor_license_management.rest_api import RestApi
from proj_mgeo_editor_license_management.setting_file_manager import SettingFileManager
from proj_mgeo_editor_license_management.singleton import SingletonInstane
from proj_mgeo_editor_license_management.structure import *
from proj_mgeo_editor_license_management.enumeration import RequestEnum
from proj_mgeo_editor_license_management.util import Util

class RestApiManager(SingletonInstane):
    def __init__(self):
        self.session_error_count = 0
        self.thread = None
        self.user_info = None
        # self.testCount = 0
            
    def sign_up(self, id, pw, retyping_pw, nation, organization):
        param = SignUpParam(id, pw, retyping_pw, nation, organization)
        response = requests.post(RestApi().get_api(RequestEnum.SIGN_UP), param.to_dic())
        return SignUpResult(response.text)

    def sing_in(self, id, pw):
        param = LoginParam(id, pw)
        response = requests.post(RestApi().get_api(RequestEnum.LOG_IN), param.to_dic())
        self.user_info = LoginResult(response.text)
        return self.user_info

    def check_program_name_and_version(self, name, version):
        res = Util.get_program_name_and_version_from_user_info()
        if name == "master":
            return True, ""

        # 임시 코드
        if name == "" or version == "":
            return True, ""

        if name != res[0]:
            return False, "Invalid account."
            
        if version != res[1]:
            return False, "Your account does not support this version."
        return True, ""

    def sign_in_with_program_name(self, id, pw, expected_program_name):                
        # program type & version check
        self.user_info = self.sing_in(id, pw)

        if self.user_info.success == False:
            return self.user_info

        if self.user_info.program_name != expected_program_name:        
            self.user_info.success = False
            self.user_info.error = "Invalid Account"

        return self.user_info

    """
    def sign_in_ex02(self, id, pw, expected_program_name):        
        #expected_program_name 을 인자로 받도록 한다        
        param = LoginParam(id, pw)
        response = requests.post(RestApi().get_api(RequestEnum.LOG_IN), param.to_dic())
        
        # program type & version check
        self.user_info = LoginResult(response.text)

        if self.user_info.success == False:
            return self.user_info

        if self.user_info.program_name != "":
            if self.user_info.program_name != 'master':
                if self.user_info.program_name != expected_program_name:
                    self.user_info.success = False
                    self.user_info.error = "Invalid account."

        return self.user_info
    """

    def modify_userinfo(self, id, nation, organization, admin_key, pw, retyping_pw):
        param = ModifyParam(id, nation, organization, admin_key, pw, retyping_pw)
        response = requests.post(RestApi().get_api(RequestEnum.MODIFY_USER_INFO), param.to_dic())                
        print(response.text)
        return ModifyResult(response.text)    

    def session_wait_to_running(self, id, session_key):
        param = SessionParam(id, session_key)
        response = requests.post(RestApi().get_api(RequestEnum.SESSION_WAIT_TO_RUNNING), param.to_dic())        
        return OnlyResult(response.text)

    def session_refresh(self, id, session_key):        
        print(datetime.datetime.now() , " call refresh")
        param = SessionParam(id, session_key)
        response = requests.post(RestApi().get_api(RequestEnum.SESSION_REFRESH), param.to_dic())
        result = OnlyResult(response.text)
        
        if result.success:                        
            # print("session error count", self.session_error_count)
            self.session_error_count = 0            
        else:            
            print("session error count", self.session_error_count)
            self.session_error_count += 1

        return result

    def session_retry(self, id, session_key):
        param = SessionParam(id, session_key)
        response = requests.post(RestApi().get_api(RequestEnum.SESSION_RETRY), param.to_dic())
        return OnlyResult(response.text)
    
    def start_session_check(self, id, key):
        self.session_error_count = 0
        self.id = id
        self.key = key
        self.recursive_refresh()

    def recursive_refresh(self):
        # Thread timer start
        #self.session_refresh(self.user_info.customer_id, self.user_info.session_key)
        self.session_refresh(self.id, self.key)
        refresh_time = SettingFileManager().instance().data.sessionRefreshTime
        self.thread = threading.Timer(int(refresh_time), self.recursive_refresh)        
        self.thread.start()

    def thread_stop(self):
        if self.thread != None: 
            if self.thread.isAlive:        
                self.thread.cancel()
                print("thread timer cancel")
        

#instance = RestApiManager()
#res = instance.sing_in("demo_odr_support", "demo_odr_support")
#print(res)