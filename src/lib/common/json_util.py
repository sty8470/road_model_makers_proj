import os
import json

class json_util:
    __instance = None

    @classmethod
    def __getInstance(cls):
        return cls.__instance
    
    @classmethod    
    def instnace(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instnace = cls.__getInstance
        return cls.__instance
    
    def getValue(self, file_path, attribute):
        with open(file_path, 'r') as f:
            json_file = json.load(f)
        
        if json_file == None:
            return
        
        return json_file[attribute]
    
    def setValue(self, file_path, attribute, value):
        with open(file_path, 'r') as f:
            json_file = json.load(f)

        if json_file == None:
            return
        
        json_file[attribute] = value

        with open(file_path, 'w') as f:
            json_file = json.dump(json_file, f, indent="\t")


    # if __name__ == "__main__":
    #     file_path = 'D:\\road_model_maker\\src\\proj_mgeo_editor_morai_opengl\\GUI\\Users\\User_MORAI.json'
    #     setValue(None, file_path, 'program_name', 'test')
    #     program_name = getValue(None, file_path, 'program_name')
    #     print(program_name)

