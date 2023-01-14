from .define import *
from proj_mgeo_editor_license_management.enumeration import RequestEnum
from proj_mgeo_editor_license_management.setting_file_manager import *

class RestApi:
    url = Define.server_url
    def get_api(self, request):
        base_uri = self.url + ":" + Define.port
        if (request == RequestEnum.SIGN_UP):
            return base_uri + "/opendrive/auth/signup"
        elif (request == RequestEnum.LOG_IN):
            return base_uri + "/opendrive/auth/userlogin"
        elif (request == RequestEnum.SESSION_WAIT_TO_RUNNING):            
            return base_uri + "/opendrive/session/waittorunning"
        elif (request == RequestEnum.SESSION_REFRESH):
            return base_uri + "/opendrive/session/refresh"
        elif (request == RequestEnum.SESSION_RETRY):            
            return base_uri + "/opendrive/session/retry"
        elif (request == RequestEnum.MODIFY_USER_INFO):
            return base_uri + "/opendrive/auth/modify/userinfo"

        