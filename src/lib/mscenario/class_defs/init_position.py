import os, sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from enum import Enum


class InitPosition:
    def __init__(self):
        self.init_position_mode = InitPositionMode.Absolute
        self.position = Position()
        self.rotation = Rotation()
        self.init_link = None
        self.init_link_ratio = 0
        self.gear = 0

    def to_dict(self):
        dict_obj = {
            "initPositionMode": self.init_position_mode,
            'pos': {
                'x': self.position.x,
                'y': self.position.y,
                'z': self.position.z
            },
            'rot': {
                'roll': self.rotation.roll,
                'pitch': self.rotation.pitch,
                'yaw': self.rotation.yaw
            },         
            'initLink': self.init_link,
            'initLinkRatio': self.init_link_ratio,
            'gear': self.gear
        }

        return dict_obj


class InitTransform:
    def __init__(self):
        self.position = Position()
        self.rotation = Rotation()
        self.scale = Scale()

    def to_dict(self):
        dict_obj = {
            'pos': {
                'x': self.position.x,
                'y': self.position.y,
                'z': self.position.z
            },
            'rot': {
                'roll': self.rotation.roll,
                'pitch': self.rotation.pitch,
                'yaw': self.rotation.yaw
            },         
           'scale': {
                'x': self.scale.x,
                'y': self.scale.y,
                'z': self.scale.z
            }
        }

        return dict_obj


class Position:
    def __init__(self, data=None):
        if data:
            self.x = data['x']
            self.y = data['y']      
            self.z = data['z']
        else:
            self.x = 0
            self.y = 0        
            self.z = 0


class Rotation:
    def __init__(self, data=None):
        if data:
            self.roll = data['roll']
            self.pitch = data['pitch']      
            self.yaw = data['yaw']
        else:
            self.roll = 0
            self.pitch = 0
            self.yaw = 0   
        

class Scale:
    def __init__(self, data=None):
        if data:
            self.x = data['x']
            self.y = data['y']      
            self.z = data['z']
        else:
            self.x = 1.0
            self.y = 1.0
            self.z = 1.0


class InitPositionMode(Enum):
    Absolute = 0
    Relative = 1