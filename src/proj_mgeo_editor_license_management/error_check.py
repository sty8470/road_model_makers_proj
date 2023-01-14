from proj_mgeo_editor_license_management.enumeration import ErrorCode

class ErrorCheck():
    @staticmethod
    def get_error_message(value):
        if (value == ErrorCode.USER_NAME_ALREADY_EXIST):                        
            return "USER_NAME_ALREADY_EXIST"
        elif (value == ErrorCode.USER_NAME_TOO_SHORT):
            return "USER_NAME_TOO_SHORT"
        elif (value == ErrorCode.USER_NAME_TOO_LONG):            
            return "USER_NAME_TOO_LONG"
        elif (value == ErrorCode.USER_NAME_INVALID_CONDITION):
            return "USER_NAME_INVALID_CONDITION"
        elif (value == ErrorCode.RETYPING_PW_NOT_MATCH):
            return "RETYPING_PW_NOT_MATCH"
        elif (value == ErrorCode.PW_IS_EMPTY):
            return "PW_IS_EMPTY"
        elif (value == ErrorCode.PW_NOT_ALLOW_EMPTY_SPACE):
            return "PW_NOT_ALLOW_EMPTY_SPACE"
        elif (value == ErrorCode.PW_LENGTH_IS_SHORT):
            return "PW_LENGTH_IS_SHORT"
        elif (value == ErrorCode.USER_NAME_NOT_EXIST):
            return "USER_NAME_NOT_EXIST"
        elif (value == ErrorCode.LOGIN_WRONG_PW):
            return "LOGIN_WRONG_PW"
        elif (value == ErrorCode.SUBSCRIBE_EXPIRE):
            return "SUBSCRIBE_EXPIRE"
        elif (value == ErrorCode.LOGIN_MAX_COUNT_IS_ZERO):
            return "LOGIN_MAX_COUNT_IS_ZERO"
        elif (value == ErrorCode.SESSION_DISCONNECT_BY_OTHERS):            
            return "SESSION_DISCONNECT_BY_OTHERS"
        elif (value == ErrorCode.SESSION_ALREADY_TERMINATED):
            return "SESSION_ALREADY_TERMINATED"
        elif (value == ErrorCode.ADMIN_KEY_NOT_CORRECT):            
            return "ADMIN_KEY_NOT_CORRECT"        
        elif (value == ErrorCode.ORGANIZATION_IS_EMPTY):
            return "ORGANIZATION_IS_EMPTY"
        elif (value == ErrorCode.NATION_CODE_INVALID):
            return "NATION_CODE_INVALID"
    
    @staticmethod
    def isNullorEmpty(str):
        if not str:
            return True

        if str == "":
            return True

        return False

    @staticmethod
    def sign_in_parameter_check(id, pw):
        if ErrorCheck.isNullorEmpty(id.strip()) == True:
            return False, "Please enter your ID"
        if ErrorCheck.isNullorEmpty(pw.strip()) == True:
            return False, "Please enter password"            
        return True, ""

    @staticmethod
    def password_retype_check(pw, retyping_pw):
        if ErrorCheck.isNullorEmpty(pw.strip()) == True:
            return False, "please enter password"
        if ErrorCheck.isNullorEmpty(retyping_pw.strip()) == True:
            return False, "please enter retype password"            
        if pw.strip() != retyping_pw.strip():
            return False, "The passwords are not the same"            
        return True, ""

    @staticmethod
    def edit_userinfo_check(id, pw, pw_retype, country, organization):
        # id check
        res = ErrorCheck.sign_in_parameter_check(id, pw)
        if res[0] == False:
            return res

        res = ErrorCheck.password_retype_check(pw, pw_retype)
        if res[0] == False:
            return res

        if ErrorCheck.isNullorEmpty(organization.strip()) == True:
            return False, "Please enter your name"

        if ErrorCheck.isNullorEmpty(country.strip()) == True:
            return False, "Please enter your location"
            
        return True, ""