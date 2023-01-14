class MyException(Exception):
    def __init__(self, err_id, message):
        self.err_id = err_id
        self.message = message

    def throw_from_outside(self, error_id_prefix = ''):
        # except 구문로 오류를 받았는데, 이를 다시 던지고 싶다.
        # 그냥 이를 다시 던지면 호출측이 정확히 표시되지 않을 수 있다.
        # 그래서 다시 던질 때 호출한 측의 error_id_prefix를 붙여 던지고 싶은 경우가 생기는데
        # 이 때 사용하도록 한다
        if error_id_prefix == '':
            return self

        return MyException(error_id_prefix + ':' + self.err_id, self.message)