from enum import Enum, IntEnum

class RequestEnum(Enum):
    SIGN_UP = 1                         # ok
    LOG_IN = 2                          # ok
    SESSION_WAIT_TO_RUNNING = 3         # ok
    SESSION_REFRESH = 4
    SESSION_RETRY = 5
    MODIFY_USER_INFO = 6                # ok

class ErrorCode(IntEnum):
    USER_NAME_ALREADY_EXIST = 1011          # 이미 존재하는 아이디면 에러
    USER_NAME_TOO_SHORT = 1012
    USER_NAME_TOO_LONG = 1013               # 유저아이디가 4자 미만이거나 20자 초과일때 에러
    USER_NAME_INVALID_CONDITION = 1014      # 유저아이디에 특수문자는 "-", "_" 이 두가지만 사용가능합니다. 다른거 사용하면 에러
    RETYPING_PW_NOT_MATCH = 1018            # pw, retyping_pw 값이 동일 하지 않으면 에러
    PW_IS_EMPTY = 1021                      # 패스워드 파라미터가 null 일경우 에러
    PW_NOT_ALLOW_EMPTY_SPACE = 1023         # 패스워드에 공백있을 경우 에러
    PW_LENGTH_IS_SHORT = 1024               # 패스워드가 4자 미만이면 에러 
    USER_NAME_NOT_EXIST = 1101              # 해당하는 유저명이 없음
    LOGIN_WRONG_PW = 1102                   # 패스워드 틀림
    SUBSCRIBE_EXPIRE = 1103                 # 구독 기간이 만료. 로그인시 받는 expire_time 값보다 시간이 지나면 발생
    LOGIN_MAX_COUNT_IS_ZERO = 1104          # 시뮬레이터 사용 가능 개수가 0개여서 로그인할수 없음
    SESSION_DISCONNECT_BY_OTHERS = 1202     # 다른 사용자가 접속해서 연결이 끊어진경우(프로그램 종료)
    SESSION_ALREADY_TERMINATED = 1203       # 1분마다 리프레시가 정상적으로 안오게 되서 일정시간 지나면 에러 발생 
                                            # 해당 에러는 네트워크 환경이나 클라 작업에 따라 발생하는 케이스가 종종 있었음 발생했을때 처리에 대한 논의 필요
    ADMIN_KEY_NOT_CORRECT = 1032            # admin key가 저장되어 있는 값과 다를 경우
    ORGANIZATION_IS_EMPTY = 1017            # organization 값이 없을경우
    NATION_CODE_INVALID = 1016              # 국가 코드 안맞을 경우(현재 KR, US)