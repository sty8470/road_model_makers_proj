import os, sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from enum import Enum

from init_position import InitPosition, InitTransform
from collections import OrderedDict

class Obstacle:
    def __init__(self, id=0):
        self.id = id
        self.index = 0        
        self.unique_id = 0
        self.obstacle_obj_type = 0
        self.init_transform = InitTransform()


    @staticmethod
    def object_to_dict(obstacle):
        result = {
            'index': obstacle.index,
            'UNIQUEID': obstacle.unique_id,
            'm_eobstacleObjType': obstacle.obstacle_obj_type,
            'initTransform': obstacle.init_transform.to_dict()
        }

        return result


    @staticmethod
    def list_to_dict(origin_list):
        dict_list = list()
        for item in origin_list:
            dict_item = {
                'index': item.index,
                'UNIQUEID': item.unique_id,
                'm_eobstacleObjType': item.obstacle_obj_type,
                'initTransform': item.init_transform.to_dict()
            }
            dict_list.append(dict_item)

        return dict_list


    def item_prop(self):

        prop_data = OrderedDict()
        prop_data['index'] = {'type' : 'int', 'value' : self.index}
        prop_data['UNIQUEID'] = {'type' : 'int', 'value' : self.unique_id}
        prop_data['m_eobstacleObjType'] = {'type' : 'int', 'value' : self.obstacle_obj_type}
        prop_data['pos'] = {'type' : 'dict', 'value' : self.init_transform['pos']}
        prop_data['rot'] = {'type' : 'dict', 'value' : self.init_transform['rot']}
        prop_data['scale'] = {'type' : 'dict', 'value' : self.init_transform['scale']}

        return prop_data