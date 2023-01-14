import os, sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from enum import Enum

from init_position import InitPosition
from collections import OrderedDict

class Pedestrian:
    def __init__(self, id=0):
        self.id = id
        self.index = 0        
        self.unique_id = 0
        self.obstacle_obj_type = 0
        self.init_position = InitPosition()
        self.active_distance = 0
        self.speed = 0
        self.active = True
        self.loop = False
        self.moving_distance = 0
        self.moving_distance_amount = 0

    @staticmethod
    def object_to_dict(pedestrian):
        result = {
            'index': pedestrian.index,
            'UNIQUEID': pedestrian.unique_id,
            'm_eobstacleObjType': pedestrian.obstacle_obj_type,
            'initPosition': {
                'pos': {
                    'x': pedestrian.init_position.position.x,
                    'y': pedestrian.init_position.position.y,
                    'z': pedestrian.init_position.position.z
                },
                'rot': {
                    'pitch': pedestrian.init_position.rotation.roll,
                    'yaw': pedestrian.init_position.rotation.pitch,
                    'roll': pedestrian.init_position.rotation.yaw
                }
            },
            'activeDistance' : pedestrian.active_distance,
            'speed' : pedestrian.speed,
            'active' : pedestrian.active,
            'loop' : pedestrian.loop,
            'movingDistance' : pedestrian.moving_distance,
            'movingDistanceAmount' : pedestrian.moving_distance_amount
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
                'initPosition': {
                    'pos': {
                        'x': item.init_position.position.x,
                        'y': item.init_position.position.y,
                        'z': item.init_position.position.z
                    },
                    'rot': {
                        'pitch': item.init_position.rotation.roll,
                        'yaw': item.init_position.rotation.pitch,
                        'roll': item.init_position.rotation.yaw
                    }
                },
                'activeDistance' : item.active_distance,
                'speed' : item.speed,
                'active' : item.active,
                'loop' : item.loop,
                'movingDistance' : item.moving_distance,
                'movingDistanceAmount' : item.moving_distance_amount
            }
            dict_list.append(dict_item)

        return dict_list

    def item_prop(self):

        prop_data = OrderedDict()
        prop_data['index'] = {'type' : 'int', 'value' : self.index}
        prop_data['UNIQUEID'] = {'type' : 'int', 'value' : self.unique_id}
        prop_data['m_eobstacleObjType'] = {'type' : 'int', 'value' : self.obstacle_obj_type}
        prop_data['pos'] = {'type' : 'dict', 'value' : self.init_position['pos']}
        prop_data['rot'] = {'type' : 'dict', 'value' : self.init_position['rot']}
        prop_data['activeDistance'] = {'type' : 'float', 'value' : self.active_distance}
        prop_data['speed'] = {'type' : 'float', 'value' : self.speed}
        prop_data['active'] = {'type' : 'boolean', 'value' : self.active}
        prop_data['loop'] = {'type' : 'boolean', 'value' : self.loop}
        prop_data['movingDistance'] = {'type' : 'float', 'value' : self.moving_distance}
        prop_data['movingDistanceAmount'] = {'type' : 'float', 'value' : self.moving_distance_amount}

        return prop_data