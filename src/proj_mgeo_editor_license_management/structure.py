import json
from lib.common.aes_cipher import AESCipher
from requests.models import requote_uri
from proj_mgeo_editor_license_management.error_check import ErrorCheck

# ==============================================================================
# param
class JsonSerializable:
    def to_dic(self):        
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))

    def to_test(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class SignUpParam(JsonSerializable):
    def __init__(self, user_name, pw, retyping_pw, nation, organization):
        self.user_name = user_name
        self.pw = pw
        self.nation = nation
        self.retyping_pw = retyping_pw
        self.organization = organization

class LoginParam(JsonSerializable):
    def __init__(self, user_name, pw):
        self.user_name = user_name
        self.pw = pw

class ModifyParam(JsonSerializable):
    def __init__(self, customer_id, nation, organization, admin_key, pw, retyping_pw):
        self.customer_id =customer_id
        self.nation = nation
        self.organization = organization
        self.admin_key = admin_key
        self.pw = pw
        self.retyping_pw = retyping_pw

class SessionParam(JsonSerializable):
    def __init__(self, customer_id, session_key):
        self.customer_id = customer_id
        self.session_key = session_key

# =====================================================================================
# result
class BaseResult:
    data = {}
    success = False
    isOnlyResult = False
    def __init__(self, result):
        dic = json.loads(result)
        self.value = dic['result']        

        if self.value == 1:
            if self.isOnlyResult == False:
                self.data = dic['data']
            self.success = True
        else:
            self.error = ErrorCheck().get_error_message(self.value)
            print(self.error)

class OnlyResult(BaseResult):
    def __init__(self, result):
        self.isOnlyResult = True
        super().__init__(result)                

class SignUpResult(BaseResult):
    def __init__(self, result): 
        super().__init__(result)
        # parsing
        if self.success:
            self.user_id = self.data['user_id']

class LoginResult(BaseResult):
    def __init__(self, result):
        super().__init__(result)
        if (self.success):                
            self.nation = self.data['nation']
            self.organization = self.data['organization']
            self.user_mail = self.data['user_mail']
            self.customer_id = self.data['customer_id']
            self.customer_name = self.data['customer_name']
            self.connection_check_time = self.data['connection_check_time']
            self.buffer_time = self.data['buffer_time']
            self.session_state = self.data['session_state']
            self.session_key = self.data['session_key']
            self.conccurent_max_count = self.data['conccurent_max_count']
            self.buy_time = self.data['buy_time']
            self.expire_time = self.data['expire_time']
            self.is_admin_account = self.data['is_admin_account']

            aes = AESCipher(encode = False)
            self.program_name = ""
            self.program_version = ""
            if 'program_type' in self.data:
                ptype = self.data['program_type']
                self.program_name = aes.decrypt(ptype)
                #print(self.program_name)
            
            if 'program_version' in self.data:
                pversion = self.data['program_version']
                self.program_version = aes.decrypt(pversion)
                #print(self.program_version)


class ModifyResult(BaseResult):
    def __init__(self, result):
        super().__init__(result)

        if (self.success):
            self.nation = self.data['nation']
            self.organization = self.data['organization']
            self.user_mail = self.data['user_mail']

"""
class PayLoad(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)

class TestData(object):
    def __init__(self, result):
        self.name = result['name']
        self.id = result['id']
"""