from common import *

class Object():
    def __init__(self):
        self.data_id = 0
        self.unique_id = -1
        self.obstacle_obj_type = 5

        self.pos = Position()
        self.rot = Rotation()
        self.scale = Scale()

    def parse(self, json_data):
        self.data_id = json_data['DataID']
        self.unique_id = json_data['UNIQUEID']
        self.obstacle_obj_type = json_data['m_eobstacleObjType']       
        self.pos = self.pos.parse(json_data['pos'])   
        self.rot = self.rot.parse(json_data['rot'])   
        self.scale = self.scale.parse(json_data['scale'])

    def to_dict(self):
        dict = {
            'DataID': self.data_id,
            'UNIQUEID': self.unique_id,
            'm_eobstacleObjType': self.obstacle_obj_type,
            'pos': self.pos.to_dict(),
            'rot': self.rot.to_dict(),
            'scale': self.scale.to_dict()
        }

        return dict
