class Singleton:
    __instance = None
    
    @classmethod
    def __get_created_instance(cls):
        return cls.__instance
        
    @classmethod
    def get_instance(cls, *args, **kargs):
        # 클래스 인스턴스를 하나 생성한다
        cls.__instance = cls(*args, **kargs)

        # 한번 get_instance method가 호출된 다음에는, 
        # 현재의 메소드가 이미 생성된 클래스 인스턴스를 가져오는 메소드로 변경된다.
        cls.get_instance = cls.__get_created_instance

        # 처음 호출될 때에는 클래스 인스턴스를 생성해서 전달하지만,
        # 그 다음부터는 __get_created_instance가 대신 호출된다.
        return cls.__instance