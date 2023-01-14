import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from lib.common.singleton import Singleton
import json

'''
@class StructureVariableManager
@brief 도로의 오브젝트(가드레일, 방음벽, 중앙분리대 등)의 크기와 모양을
       변경할 수 있도록 변수를 파일에서 읽어와 생성할 때, 가져다 사용하기 위한
       메니저 입니다. 일단 임시로 만들어서 사용되는 클래스입니다.
'''
class StructureVariableManager(Singleton) :
    def __init__(self):
        
        self.data = None
        self.use = False

        # 터널.
        self.tunnel_list = None


    def load_structure_config(self) :
        default_user_info_path = os.path.join(current_path, 'GUI/Structure_Config.json')
        self.load_config_file(default_user_info_path)

    def load_config_file(self, file_path) :
        if os.path.isfile(file_path) == False : 
            return
        
        with open(file_path) as file :
            json_data =  json.load(file)

            self.data = json_data

            if str("use") in json_data :
                self.use = bool(json_data["use"])

            if str("structure") not in json_data :
                return

            st_data = json_data["structure"]

            # 터널.
            self.tunnel_list = st_data["tunnel"]

    # def get_structure_value(self, structure_name) :
    #     select_index = self.data["select"][structure_name]
    #     return self.data["structure"][structure_name][select_index]

    def get_structure_value(self, structure_name, index) :
        return self.data["structure"][structure_name][index]