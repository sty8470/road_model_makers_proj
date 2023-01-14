from common import *

class EgoVehicle():
    def __init__(self):
        self.data_id = 20100005
        self.unique_id = -1
        self.obstacle_obj_type = 0
        self.initPosition = InitPosition()
        self.currentVelocity = 0
        self.v2vUDPSessionInfo = V2VUDPSessionInfo()
        self.beforeControlMode = 0

    def parse(self, json_data):
        self.data_id = json_data['DataID'] if json_data['DataID'] is not 0 else 20100005
        self.unique_id = json_data['UNIQUEID']
        self.obstacle_obj_type = json_data['m_eobstacleObjType']
        
        self.currentVelocity = json_data['currentVelocity']

        self.initPosition = self.initPosition.parse(json_data['initPosition'])
        self.v2vUDPSessionInfo = self.v2vUDPSessionInfo.parse(json_data['v2vUDPSessionInfo'])

        self.beforeControlMode = json_data['beforeControlMode']

        return self

    def to_dict(self):
        dict = {
            'DataID': self.data_id,
            'UNIQUEID': self.unique_id,
            'm_eobstacleObjType': self.obstacle_obj_type,
            'initPosition': self.initPosition.to_dict(),
            'currentVelocity': self.currentVelocity,
            'v2vUDPSessionInfo': self.v2vUDPSessionInfo.to_dict(),
            'beforeControlMode': self.beforeControlMode
        }

        return dict

class NPCVehicle():
    def __init__(self):
        self.data_id = 0
        self.unique_id = -1
        self.obstacle_obj_type = 0
        self.initPosition = InitPosition()
        self.velocityType = 1
        self.linkVelocity = 85
        self.constantVelocity = 60
        self.desiredVelocity = 60
        self.currentVelocity = 0

        self.isCloseLoop = False
        self.isEgo = False

        self.spawnPointUniqueID = -1
        self.destinationUniqueID = -1

        self.startPointLinkInfo = LinkInfo()
        self.endPointLinkInfo = LinkInfo()
        self.currentLinkInfo = LinkInfo()
        self.loopStartLinkInfo = LinkInfo()

        self.v2vUDPSessionInfo = V2VUDPSessionInfo()

        self.latBiasMode = 1
        self.bias = 0.0

    def parse(self, json_data):
        self.data_id = json_data['DataID']
        self.unique_id = json_data['UNIQUEID']
        self.obstacle_obj_type = json_data['m_eobstacleObjType']                

        self.initPosition = self.initPosition.parse(json_data['initPosition'])

        self.velocityType = json_data['velocityType']
        self.linkVelocity = json_data['linkVelocity']
        self.constantVelocity = json_data['constantVelocity']
        self.desiredVelocity = json_data['desiredVelocity']
        self.currentVelocity = json_data['currentVelocity']
        self.isCloseLoop = json_data['isCloseLoop']
        self.isEgo = json_data['isEgo']

        # self.spawnPointUniqueID = json_data['spawnPointUniqueID']
        # self.destinationUniqueID = json_data['destinationUniqueID']
        self.spawnPointUniqueID = -1
        self.destinationUniqueID = -1

        self.startPointLinkInfo = self.startPointLinkInfo.parse(json_data['startPointLinkInfo'])
        self.endPointLinkInfo = self.endPointLinkInfo.parse(json_data['endPointLinkInfo'])
        self.currentLinkInfo = self.currentLinkInfo.parse(json_data['currentLinkInfo'])
        self.loopStartLinkInfo = self.loopStartLinkInfo.parse(json_data['loopStartLinkInfo'])

        self.v2vUDPSessionInfo = self.v2vUDPSessionInfo.parse(json_data['v2vUDPSessionInfo'])

        self.latBiasMode = json_data['latBiasMode']
        self.bias = json_data['bias']

        return self

    def to_dict(self):
        dict = {
            'DataID': self.data_id,
            'UNIQUEID': self.unique_id,
            'm_eobstacleObjType': self.obstacle_obj_type,
            'initPosition': self.initPosition.to_dict(),

            'velocityType': self.velocityType,
            'linkVelocity': self.linkVelocity,
            'constantVelocity': self.constantVelocity,
            'desiredVelocity': self.desiredVelocity,
            'currentVelocity': self.currentVelocity,

            'isCloseLoop': self.isCloseLoop,
            'isEgo': self.isEgo,

            'spawnPointUniqueID': self.spawnPointUniqueID,
            'destinationUniqueID': self.destinationUniqueID,

            'startPointLinkInfo': self.startPointLinkInfo.to_dict(),
            'endPointLinkInfo': self.endPointLinkInfo.to_dict(),
            'currentLinkInfo': self.currentLinkInfo.to_dict(),
            'loopStartLinkInfo': self.loopStartLinkInfo.to_dict(),

            'v2vUDPSessionInfo': self.v2vUDPSessionInfo.to_dict(),
            'latBiasMode': self.latBiasMode,
            'bias': self.bias
        }

        return dict