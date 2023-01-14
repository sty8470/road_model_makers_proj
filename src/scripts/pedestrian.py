from common import *

class Pedestrian():
    def __init__(self):
        self.data_id = 0
        self.unique_id = -1
        self.obstacle_obj_type = 5

        self.pos = Position()
        self.rot = Rotation()

        self.activeDistance = 10
        self.speed = 10
        self.active = True
        self.loop = False

        self.initPos = Position()
        self.initRot = Rotation()

        self.movingDistance = 5
        self.movingDistanceAmount = 0
        self.standardPos = Position()

        self.anim = anim()
        self.stateNameHash = 0
        self.stateNormalizedTime = 0
        self.pedestrianBehavior = 1
        self.pedestrianType = 1
        self.listObjIDForBehavior = []
        self.animSpeed = 0.0

    def parse(self, json_data):
        self.data_id = json_data['DataID']
        self.unique_id = json_data['UNIQUEID']
        self.obstacle_obj_type = json_data['m_eobstacleObjType']       
        self.pos = self.pos.parse(json_data['pos'])   
        self.rot = self.rot.parse(json_data['rot'])   

        self.activeDistance = json_data['activeDistance']
        self.speed = json_data['speed']
        self.active = json_data['active']
        self.loop = json_data['loop']

        self.initPos = self.initPos.parse(json_data['initPos'])
        self.initRot = self.initRot.parse(json_data['initRot'])

        self.movingDistance = json_data['movingDistance']      
        self.movingDistanceAmount = json_data['movingDistanceAmount']      
        self.standardPos = self.standardPos.parse(json_data['standardPos'])

        self.anim = self.anim.parse(json_data['anim'])
        self.stateNameHash = json_data['stateNameHash']
        self.stateNormalizedTime = json_data['stateNormalizedTime']
        self.pedestrianBehavior = json_data['pedestrianBehavior']
        self.pedestrianType = json_data['pedestrianType']
        
        if 'listObjIDForBehavior' in json_data:
            self.listObjIDForBehavior = json_data['listObjIDForBehavior']
        
        if 'animSpeed' in json_data:
            self.animSpeed = json_data['animSpeed']

    def to_dict(self):
        dict = {
            'DataID': self.data_id,
            'UNIQUEID': self.unique_id,
            'm_eobstacleObjType': self.obstacle_obj_type,
            'pos': self.pos.to_dict(),
            'rot': self.rot.to_dict(),
            'activeDistance': self.activeDistance,
            'speed': self.speed,
            'active': self.active,
            'loop': self.loop,
            'initPos': self.initPos.to_dict(),
            'initRot': self.initRot.to_dict(),
            'movingDistance': self.movingDistance,
            'movingDistanceAmount': self.movingDistanceAmount,
            'standardPos': self.standardPos.to_dict(),

            'anim': self.anim.to_dict(),
            'stateNameHash': self.stateNameHash,
            'stateNormalizedTime': self.stateNormalizedTime,
            'pedestrianBehavior': self.pedestrianBehavior,
            'pedestrianType': self.pedestrianType,
            'listObjIDForBehavior': self.listObjIDForBehavior,
            'animSpeed': self.animSpeed,
        }

        return dict

class anim():
    def __init__(self):
        self.m_FileID = 0
        self.m_PathID = 0

    def parse(self, json_data):
        self.m_FileID = json_data['m_FileID']
        self.m_PathID = json_data['m_PathID']

        return self

    def to_dict(self):
        dict = {
            'm_FileID': self.m_FileID,
            'm_PathID': self.m_PathID
        }

        return dict