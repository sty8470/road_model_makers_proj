import sys
import json # import json module

from object import *
from pedestrian import *
from vehicle import *
from spawn_point import *
from traffic_light import *
from common import *


# 예전에 작성된 시나리오 파일을 최신 Morai SIM 버전에서 로드 되도록 변환하는 스크립트
# scenario_file_path = 'C:/Projects/ModelMaker/src/scripts/test_file/R_KR_PR_SeongnamCityHall/demo.json'
# result_file_path = 'C:/Projects/ModelMaker/src/scripts/test_file/result/R_KR_PR_SeongnamCityHall/convert_demo.json'
if len(sys.argv) != 3:
    print("failed to convert scenario file. - insufficient arguments.")
    sys.exit()

scenario_file_path = sys.argv[1]
result_file_path = sys.argv[2]

print('scenario file path : ' + scenario_file_path)
print('converted scenario file path : ' + result_file_path)

with open(scenario_file_path) as json_file:
    json_data = json.load(json_file)

    # Parse Ego Vehicle 
    ego = EgoVehicle()
    ego.parse(json_data['egoVehicle'])

    # Parse NPC Vehicle    
    npc_list = []
    for vehicle in json_data['vehicleList']:
        npc_vehicle = NPCVehicle()
        npc_vehicle.parse(vehicle)

        npc_list.append(npc_vehicle)

    # Parse Spawn Point
    spawn_point_list = []
    for spawn_point_item in json_data['spawnPointList']:
        spawn_point = SpawnPoint()
        spawn_point.parse(spawn_point_item)

        spawn_point_list.append(spawn_point)

    # Parse Object
    object_list = []
    for object_item in json_data['objectList']:
        object = Object()
        object.parse(object_item)

        object_list.append(object)

    # Parse Pedestrian
    pedestrian_list = []
    for pedestrian_item in json_data['pedestrianList']:
        pedestrian = Pedestrian()
        pedestrian.parse(pedestrian_item)

        pedestrian_list.append(pedestrian)

    # Parse TL
    tl_list = []
    for tl_item in json_data['tlList']:
        tl = TrafficLight()
        tl.parse(tl_item)

        tl_list.append(tl)

    # Parse Map Info
    map_info = MapInfo()
    map_info.parse(json_data['mapInfo'])

    # Parse V2IInfo
    v2i_info = V2IInfo()
    v2i_info.parse(json_data['v2IInfo'])

    # Write JSON
    new_json_data = {
        'version': 1.0,
        'egoVehicle': ego.to_dict(),
        'vehicleList': [],
        'pedestrianList': [],
        'objectList': [],
        'spawnPointList': [],
        'tlList': [],
        'pedspawnPointList': [],
        'aiPedstrianList': [],
        'shadedAreaList': [],
        'mapInfo': map_info.to_dict(),
        'v2IInfo': v2i_info.to_dict()
    }

    # vehicle to dict
    vehicle_list = []
    for npc in npc_list:
        vehicle_list.append(npc.to_dict())
    new_json_data['vehicleList'] = vehicle_list

    # pedestrian to dict
    pedestrian_dict = []
    for pedestrian in pedestrian_list:
        pedestrian_dict.append(pedestrian.to_dict())
    new_json_data['pedestrianList'] = pedestrian_dict

    # object to dict
    object_dict = []
    for object in object_list:
        object_dict.append(object.to_dict())
    new_json_data['objectList'] = object_dict

    # spawn point to dict
    spawn_point_dict = []
    for spawn_point in spawn_point_list:
        spawn_point_dict.append(spawn_point.to_dict())
    new_json_data['spawnPointList'] = spawn_point_dict

    # traffic light to dict
    traffic_light_dict = []
    for traffic_light in tl_list:
        traffic_light_dict.append(traffic_light.to_dict())
    new_json_data['tlList'] = traffic_light_dict

    with open(result_file_path, 'w') as outfile:
        json.dump(new_json_data, outfile)
        print('scenario conversion succeeded.')