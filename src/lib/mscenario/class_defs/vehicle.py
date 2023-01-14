import os, sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from enum import Enum

from init_position import InitPosition
from collections import OrderedDict

class Vehicle:
    def __init__(self, id=0):
        self.id = id
        self.unique_id = 0
        self.is_ego = False
        self.data_id = 0        
        self.gear = 0
        self.is_random_creation = False
        self.model_index_list = []
        self.init_position = InitPosition()
        self.path_generation_method = PathGenerationMethod.FullRandom
        self.path = []
        self.respawn_distance = 0
        self.current_velocity = 0
        self.desired_velocitiy_mode = DesiredVelocitiyMode.Static

        # DesiredVelocitiyMode가 Dynamic 인 경우 '30:50' 이런 식으로 속도가 구간으로 표현되어야 함
        # Simulator 에서는 구간 중에 하나의 속도가 desired_velocity로 Random 선택되어야 함
        self.desired_velocity = 0
        self.traking_path_name = 'PathManager#1'

        # TODO : 네트워크 관련 필드는 어떻게 처리할 지 논의 필요

    @staticmethod
    def object_to_dict(eog_vehicle):
        result = {
            'DataID': eog_vehicle.data_id,
            'UNIQUEID': eog_vehicle.unique_id,
            'm_eobstacleObjType': 1,     
            'initPosition': eog_vehicle.init_position.to_dict(),
            'currentVelocity' : eog_vehicle.current_velocity,
            'gear': eog_vehicle.gear
        }

        return result

    @staticmethod
    def list_to_dict(origin_list):
        dict_list = list()
        for item in origin_list:
            dict_item = {
                'DataID': item.data_id,
                'UNIQUEID': item.unique_id,
                'm_eobstacleObjType': 1,     
                "isRandomCreation": item.is_random_creation,
                "modelIndexList": item.model_index_list,
                'initPosition': item.init_position.to_dict(),
                "pathGenerationMethod": item.path_generation_method,
                "path": item.path,
                "isEgo": item.is_ego,
                "respawnDistance": item.respawn_distance,
                "desiredVelocitiyMode": item.desired_velocitiy_mode,
                "desiredVelocity": item.desired_velocity,
                "currentVelocity": item.current_velocity,
                "trakingPathName": item.traking_path_name
            }
            dict_list.append(dict_item)

        return dict_list

    def item_prop(self, ego=False):
        if ego:
            prop_data = OrderedDict()
            prop_data['index'] = {'type' : 'int', 'value' : self.index}
            prop_data['initPositionMode'] = {'type' : 'string', 'value' : self.init_position['initPositionMode']}
            prop_data['pos'] = {'type' : 'dict', 'value' : self.init_position['pos']}
            prop_data['rot'] = {'type' : 'dict', 'value' : self.init_position['rot']}
            prop_data['currentVelocity'] = {'type' : 'int', 'value' : self.current_velocity}
            prop_data['gear'] = {'type' : 'int', 'value' : self.gear}
        else:
            prop_data = OrderedDict()
            prop_data['index'] = {'type' : 'int', 'value' : self.index}
            prop_data['isRandomCreation'] = {'type' : 'boolean', 'value' : self.is_random_creation}
            prop_data['modelIndexList'] = {'type' : 'list<int>', 'value' : self.model_index_list}
            prop_data['initPositionMode'] = {'type' : 'string', 'value' : self.init_position['initPositionMode']}
            prop_data['pos'] = {'type' : 'dict', 'value' : self.init_position['pos']}
            prop_data['rot'] = {'type' : 'dict', 'value' : self.init_position['rot']}
            prop_data['pathGenerationMethod'] = {'type' : 'string', 'value' : self.path_generation_method}
            prop_data['path'] = {'type' : 'list<string>', 'value' : self.path}
            prop_data['respawnDistance'] = {'type' : 'int', 'value' : self.respawn_distance}
            prop_data['desiredVelocitiyMode'] = {'type' : 'string', 'value' : self.desired_velocitiy_mode}
            prop_data['desiredVelocity'] = {'type' : 'int', 'value' : self.desired_velocity}
            prop_data['currentVelocity'] = {'type' : 'int', 'value' : self.current_velocity}
        return prop_data


class PathGenerationMethod(Enum):
    FullRandom = 0
    LinkPath = 1
    EndNode = 2


class DesiredVelocitiyMode(Enum):
    Static = 0

    # Dynamic 모드인 경우 desiredVelocity 값을 배열을 통한 범위([60, 80])로 전달
    # 값이 [60, 80]인 경우 시뮬레이터는 해당 링크의 Max Speed에서 60% ~ 80% 사이의 값을 랜덤으로 계산해서 desiredVelocity로 설정
    Dynamic = 1