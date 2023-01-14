import os, sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.normpath(os.path.join(current_path, './')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import json

from vehicle import Vehicle
from pedestrian import Pedestrian
from obstacle import Obstacle
from init_position import InitPosition, Position, Rotation, Scale

from glob import glob


class MScenario:
    def __init__(self):
        self.vehicle_id = 0
        self.pedestrian_id = 0
        self.obstacle_id = 0

        self.ego_vehicle = None
        self.vehicle_list = list()
        self.pedestrian_list = list()
        self.obstacle_list = list()


    def save(self, folder_path):
        # Vehicle 데이터 저장
        vehicle_data = {
            "egoVehicle": Vehicle.object_to_dict(self.ego_vehicle),
            "vehicleList": Vehicle.list_to_dict(self.vehicle_list)
        }
        filename = os.path.join(folder_path, 'vehicle.json')
        with open(filename, 'w') as f:
            json.dump(vehicle_data, f, indent=2)

        # Pedestrian 데이터 저장
        pedestrian_data = {
            "pedestrianList": Pedestrian.list_to_dict(self.pedestrian_list)
        }
        filename = os.path.join(folder_path, 'pedestrian.json')
        with open(filename, 'w') as f:
            json.dump(pedestrian_data, f, indent=2)

        # Obstacle 데이터 저장
        obstacle_data = {
            "obstacle_list": Obstacle.list_to_dict(self.obstacle_list)
        }
        filename = os.path.join(folder_path, 'obstacle.json')
        with open(filename, 'w') as f:
            json.dump(obstacle_data, f, indent=2)
    

    def load(self, folder_path):
        for file_name in glob(folder_path + '/**/*.json', recursive=True):
            with open(file_name) as f:
                head, tail = os.path.split(file_name)
                if "obstacle" in tail:
                    try:
                        data = json.load(f)
                        self.set_obstacle(data)
                    except Exception as e:
                        print("Failed to load obstacle file." + e)
                        
                elif "vehicle" in tail:
                    try:
                        data = json.load(f)
                        self.set_vehicle(data)
                    except Exception as e:
                        print("Failed to load vehicle file." + e)

                elif "pedestrian" in tail:
                    try:
                        data = json.load(f)
                        self.set_pedestrian(data)
                    except Exception as e:
                        print("Failed to load pedestrian file." + e)

        print("Success to load MScenario file.")
        return self

    def set_obstacle(self, data):
        if data['obstacle_list'] and len(data['obstacle_list']) > 0:
            for item in data['obstacle_list']:
                self.obstacle_id += 1
                obstacle = Obstacle(self.obstacle_id)
                obstacle.index = item['index']
                obstacle.unique_id = item['UNIQUEID']
                obstacle.obstacle_obj_type = item['m_eobstacleObjType']
                obstacle.init_transform.position = Position(item['initTransform']['pos']) 
                obstacle.init_transform.rotation = Rotation(item['initTransform']['rot'])
                obstacle.init_transform.scale = Scale(item['initTransform']['scale'])        

                self.obstacle_list.append(obstacle)

    def set_pedestrian(self, data):
        if data['pedestrianList'] and len(data['pedestrianList']) > 0:
            for item in data['pedestrianList']:
                self.pedestrian_id += 1
                pedestrian = Pedestrian(self.pedestrian_id)
                pedestrian.index = item['index']
                pedestrian.unique_id = item['UNIQUEID']
                pedestrian.obstacle_obj_type = item['m_eobstacleObjType']                
                pedestrian.init_position.position = Position(item['initPosition']['pos'])
                pedestrian.init_position.rotation = Rotation(item['initPosition']['rot'])
                pedestrian.active_distance = item['activeDistance']
                pedestrian.speed = item['speed']
                pedestrian.active = item['active']
                pedestrian.loop = item['loop']
                pedestrian.moving_distance = item['movingDistance']
                pedestrian.moving_distance_amount = item['movingDistanceAmount']
              
                self.pedestrian_list.append(pedestrian)
        
    def set_vehicle(self, data):
        if data['egoVehicle']:
            self.vehicle_id += 1
            self.ego_vehicle = Vehicle(self.vehicle_id)
            self.ego_vehicle.data_id = data['egoVehicle']['DataID']
            self.ego_vehicle.current_velocity = data['egoVehicle']['currentVelocity']
            self.ego_vehicle.init_position.init_position_mode = data['egoVehicle']['initPosition']['initPositionMode']
            self.ego_vehicle.init_position.position = Position(data['egoVehicle']['initPosition']['pos'])
            self.ego_vehicle.init_position.rotation = Rotation(data['egoVehicle']['initPosition']['rot'])
            self.ego_vehicle.init_position.initLinkRatio = data['egoVehicle']['initPosition']['initLinkRatio']
            self.ego_vehicle.init_position.initLink = data['egoVehicle']['initPosition']['initLink']
            self.ego_vehicle.init_position.gear = data['egoVehicle']['initPosition']['gear']

        if data['vehicleList'] and len(data['vehicleList']) > 0:
            for item in data['vehicleList']:
                self.vehicle_id += 1
                vehicle = Vehicle(self.vehicle_id)
                vehicle.is_ego = item['isEgo']
                vehicle.unique_id = item['UNIQUEID']
                vehicle.data_id = item['DataID']
                vehicle.is_random_creation = item['isRandomCreation'] if item['isRandomCreation'] else False
                vehicle.model_index_list = item['modelIndexList'] if item['modelIndexList'] else []                
                vehicle.init_position.init_position_mode = item['initPosition']['initPositionMode']
                vehicle.init_position.position = Position(item['initPosition']['pos'])
                vehicle.init_position.rotation = Rotation(item['initPosition']['rot'])
                vehicle.init_position.initLinkRatio = item['initPosition']['initLinkRatio']
                vehicle.init_position.initLink = item['initPosition']['initLink']
                vehicle.init_position.gear = item['initPosition']['gear']
                vehicle.path_generation_method = item['pathGenerationMethod']
                vehicle.path = item['path'] if item['path'] else []
                vehicle.respawn_distance = item['respawnDistance'] if item['respawnDistance'] else vehicle.respawn_distance
                vehicle.desired_velocitiy_mode = item['desiredVelocitiyMode'] if item['desiredVelocitiyMode'] else vehicle.desired_velocitiy_mode
                vehicle.desired_velocity = item['desiredVelocity']
                vehicle.current_velocity = item['currentVelocity']
                vehicle.traking_path_name = item['trakingPathName']

                self.vehicle_list.append(vehicle)


