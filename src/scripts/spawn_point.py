from common import *

class SpawnPoint():
    def __init__(self):
        self.data_id = 0
        self.unique_id = -1
        self.obstacle_obj_type = 5

        self.pos = Position()
        self.rot = Rotation()
        self.scale = Scale()

        self.spawnVehicleTypeID = -1
        self.listVehicleLengthType = [0, 1, 2, 3]
        self.isCloseLoop = False
        self.isLaneChange = True
        self.ParameterType = 1

        self.maximumSpawnVehicle = 3

        self.minSpawnPeriod = 5.0
        self.maxSpawnPeriod = 10.0

        self.SpawnVelocityType = 1

        self.MinSpawnVelocity_Custom = 0.0
        self.MaxSpawnVelocity_Custom = 20.0

        self.MinSpawnVelocity_Link = 0.0
        self.MaxSpawnVelocity_Link = 10.0

        self.DesiredVelocityType = 1

        self.MinDesiredVelocity_Custom = 50.0
        self.MaxDesiredVelocity_Custom = 60.0

        self.MinDesiredVelocity_Link = 85.0
        self.MaxDesiredVelocity_Link = 100.0

        self.spawnedVehiclesCount = 0
        self.isSpawning = False
        self.waitSpawnTime = 0.0
        self.destinationObjUniqueID = -1

        self.startLinkInfo = LinkInfo()
        self.endLinkInfo = LinkInfo()
        
        self.latBiasMode = 1
        self.MinLatBias = -10
        self.MaxLatBias = 10
    
    def parse(self, json_data):
        self.data_id = json_data['DataID']
        self.unique_id = json_data['UNIQUEID']
        self.obstacle_obj_type = json_data['m_eobstacleObjType']       
        self.pos = self.pos.parse(json_data['pos'])   
        self.rot = self.rot.parse(json_data['rot'])   
        self.scale = self.scale.parse(json_data['scale'])

        self.spawnVehicleTypeID = json_data['spawnVehicleTypeID']        
        self.isCloseLoop = json_data['isCloseLoop']      

        if 'listVehicleLengthType' in json_data:
            self.listVehicleLengthType = json_data['listVehicleLengthType']  

        if 'isLaneChange' in json_data:
            self.isLaneChange = json_data['isLaneChange']    

        if 'ParameterType' in json_data:
            self.ParameterType = json_data['ParameterType']  

        if 'maximumSpawnVehicle' in json_data:
            self.maximumSpawnVehicle = json_data['maximumSpawnVehicle']  

        if 'minSpawnPeriod' in json_data:
            self.minSpawnPeriod = json_data['minSpawnPeriod']  
        if 'maxSpawnPeriod' in json_data:
            self.maxSpawnPeriod = json_data['maxSpawnPeriod']  

        if 'SpawnVelocityType' in json_data:
            self.SpawnVelocityType = json_data['SpawnVelocityType']  

        if 'MinSpawnVelocity_Custom' in json_data:
            self.MinSpawnVelocity_Custom = json_data['MinSpawnVelocity_Custom']  
        if 'MaxSpawnVelocity_Custom' in json_data:
            self.MaxSpawnVelocity_Custom = json_data['MaxSpawnVelocity_Custom']  

        if 'MinSpawnVelocity_Link' in json_data:
            self.MinSpawnVelocity_Link = json_data['MinSpawnVelocity_Link']  
        if 'MaxSpawnVelocity_Link' in json_data:
            self.MaxSpawnVelocity_Link = json_data['MaxSpawnVelocity_Link']  

        if 'DesiredVelocityType' in json_data:
            self.DesiredVelocityType = json_data['DesiredVelocityType']  

        if 'MinDesiredVelocity_Custom' in json_data:
            self.MinDesiredVelocity_Custom = json_data['MinDesiredVelocity_Custom'] 
        if 'MaxDesiredVelocity_Custom' in json_data:
            self.MaxDesiredVelocity_Custom = json_data['MaxDesiredVelocity_Custom']  

        if 'MinDesiredVelocity_Link' in json_data:
            self.MinDesiredVelocity_Link = json_data['MinDesiredVelocity_Link']  
        if 'MaxDesiredVelocity_Link' in json_data:
            self.MaxDesiredVelocity_Link = json_data['MaxDesiredVelocity_Link']  

        # spawnedVehiclesCount는 기본값인 0으로 설정
        # if 'spawnedVehiclesCount' in json_data:
        #     self.spawnedVehiclesCount = json_data['spawnedVehiclesCount']  

        if 'isSpawning' in json_data:
            self.isSpawning = json_data['isSpawning']  
        if 'waitSpawnTime' in json_data:
            self.waitSpawnTime = json_data['waitSpawnTime']  

        # destinationObjUniqueID 정보가 잘못되어서 오류나는 경우가 있음
        # if 'destinationObjUniqueID' in json_data:
        #     self.destinationObjUniqueID = json_data['destinationObjUniqueID']  

        if 'startLinkInfo' in json_data:
            self.startLinkInfo = self.startLinkInfo.parse(json_data['startLinkInfo'])

        # end link 정보가 잘못되어서 오류나는 경우가 있음
        # if 'endLinkInfo' in json_data:
        #     self.endLinkInfo = self.endLinkInfo.parse(json_data['endLinkInfo'])
        
        if 'latBiasMode' in json_data:
            self.latBiasMode = json_data['latBiasMode']  
        if 'MinLatBias' in json_data:
            self.MinLatBias = json_data['MinLatBias']  
        if 'MaxLatBias' in json_data:
            self.MaxLatBias = json_data['MaxLatBias']  

        return self

    def to_dict(self):
        dict = {
            'DataID': self.data_id,
            'UNIQUEID': self.unique_id,
            'm_eobstacleObjType': self.obstacle_obj_type,
            'pos': self.pos.to_dict(),
            'rot': self.rot.to_dict(),
            'scale': self.scale.to_dict(),

            'spawnVehicleTypeID': self.spawnVehicleTypeID,
            'listVehicleLengthType': self.listVehicleLengthType,
            'isCloseLoop': self.isCloseLoop,
            'isLaneChange': self.isLaneChange,
            'ParameterType': self.ParameterType,

            'maximumSpawnVehicle': self.maximumSpawnVehicle,
            'minSpawnPeriod': self.minSpawnPeriod,
            'maxSpawnPeriod': self.maxSpawnPeriod,

            'SpawnVelocityType': self.SpawnVelocityType,
            'MinSpawnVelocity_Custom': self.MinSpawnVelocity_Custom,
            'MaxSpawnVelocity_Custom': self.MaxSpawnVelocity_Custom,
            'MinSpawnVelocity_Link': self.MinSpawnVelocity_Link,
            'MaxSpawnVelocity_Link': self.MaxSpawnVelocity_Link,

            'DesiredVelocityType': self.DesiredVelocityType,
            'MinDesiredVelocity_Custom': self.MinDesiredVelocity_Custom,
            'MaxDesiredVelocity_Custom': self.MaxDesiredVelocity_Custom,
            'MinDesiredVelocity_Link': self.MinDesiredVelocity_Link,
            'MaxDesiredVelocity_Link': self.MaxDesiredVelocity_Link,

            'spawnedVehiclesCount': self.spawnedVehiclesCount,
            'isSpawning': self.isSpawning,
            'waitSpawnTime': self.waitSpawnTime,
            'destinationObjUniqueID': self.destinationObjUniqueID,

            'startLinkInfo': self.startLinkInfo.to_dict(),
            'endLinkInfo': self.endLinkInfo.to_dict(),

            'latBiasMode': self.latBiasMode,
            'MinLatBias': self.MinLatBias,
            'MaxLatBias': self.MaxLatBias
        }

        return dict