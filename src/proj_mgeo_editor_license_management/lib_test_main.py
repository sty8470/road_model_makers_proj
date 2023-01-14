# opendrive rest api test
import requests

from define import Define
from proj_mgeo_editor_license_management.structure import *
from proj_mgeo_editor_license_management.rest_api import *
from proj_mgeo_editor_license_management.enumeration import RequestEnum

# ===================================================================================
# SIGN_UP up test
print("--> request SIGN_UP")
param = SignUpParam("test04", "1234", "1234", "KR", "core_dev")
response = requests.post(RestApi.get_api(RequestEnum.SIGN_UP), param.to_dic())
print("<-- response : " + response.text)

# result parsing
result = SignUpResult(response.text)
if result.success:
    print(result.user_id)

print("press any key......")
input()

# ===================================================================================
# LOG_IN test
print("--> request LOG_IN")
param = LoginParam('test04', '1234')
response = requests.post(RestApi.get_api(RequestEnum.LOG_IN), param.to_dic())
print("<-- response : " + response.text)

# result parsing
result = LoginResult(response.text)
if result.success:
    print("customer id : ", result.customer_id)
    print("customer name : ", result.customer_name)

session_key = result.session_key
customer_id = result.customer_id

print("press any key......")
input()

# ===================================================================================
# MODIFY_USER_INFO test
print("--> request MODIFY_USER_INFO")
param = ModifyParam(customer_id, "KR", "core_dev_2", "", "1234", "1234")
response = requests.post(RestApi.get_api(RequestEnum.MODIFY_USER_INFO), param.to_dic())
print("<-- response : " + response.text)
result = ModifyResult(response.text)

if result.success:
    print(result.nation)
    print(result.organization)
    print(result.user_mail)

print("press any key......")
input()

# ===================================================================================
# SESSION_WAIT_TO_RUNNING test
print("--> request SESSION_WAIT_TO_RUNNING")
param = SessionParam(customer_id, session_key)
response = requests.post(RestApi.get_api(RequestEnum.SESSION_WAIT_TO_RUNNING), param.to_dic())
print("<-- response : " + response.text)
result = OnlyResult(response.text)
if result.success:
    print("session wait to running ok")

print("press any key......")
input()

# ===================================================================================
# SESSION_REFRESH test
print("--> request SESSION_REFRESH")
param = SessionParam(customer_id, session_key)
response = requests.post(RestApi.get_api(RequestEnum.SESSION_REFRESH), param.to_dic())
print("<-- response : " + response.text)
result = OnlyResult(response.text)
if result.success:
    print("session refresh ok")

print("press any key......")
input()

# ===================================================================================
# SESSION_REFRESH test
print("--> request SESSION_RETRY")
param = SessionParam(customer_id, session_key)
response = requests.post(RestApi.get_api(RequestEnum.SESSION_RETRY), param.to_dic())
print("<-- response : " + response.text)
result = OnlyResult(response.text)
if result.success:
    print("session retry ok")

print("Exit the program. press any key...")
input()