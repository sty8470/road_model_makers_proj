import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import numpy as np

from lib.mgeo.class_defs import *

import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

import csv
import json
import ast
import shutil

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.deepmap.deepmap_converter import *

"""
Editor 없이 출력하는 정보(횡단보도, 표지판, 신호등)
미국 데이터 모델 정보가 없어서 모델링팀에서 제작하면 수정해야함
"""

def export_other(input_path):

    output_path = os.path.join(input_path, 'output') 
    relative_loc = True
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    except OSError:
        print('Error: Creating directory. ' +  output_path)

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__)) 

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get File List
    map_info, map_data = read_json_files(input_path)

    features = map_info['UCDavis_Features']['features']

    origin = map_info['UCDavis_CenterLines']['features'][0]['geometry']['coordinates'][0]
    origin = np.array(origin)
    print('[INFO] Origin Set as: ', origin)
    
    # Feature Data 이용해서 신호등, 표지판, 노면표시 만들기
    export_feature(map_info['UCDavis_Features']['features'], origin, input_path, output_path)
    # Feature Data 이용해서 횡단보도 mesh 만들기
    create_crosswalk_obj(map_info['UCDavis_Features']['features'], origin, input_path, output_path)


def create_crosswalk_obj(feature_data, origin, freinput_path, output_path):

    print('START -- Create Crosswalk mesh(Obj)')
    """포인트 내부를 수정"""
    point_interval = 0.1

    cw_set = CrossWalkSet()
    
    for item in feature_data:
        if item['geometry']['type'] == "Polygon":
            if item['properties']['featureType'] == "Crosswalk":
                points = item['geometry']['coordinates']
                points = np.array(points)
                points -= origin
                cw_id = '{}'.format(item['properties']['featureId'])
                item_type = item['properties']['featureType']
                cw = CrossWalk(points=points, idx=cw_id)
                cw_set.append_data(cw)

    """이제 cw_set에서 mesh를 만든다"""

    # 여기에, filename 을 idx로 접근하면, 다음의 데이터가 존재한다
    # 한가지 idx = speedbump를 예를 들면, 
    # 'vertex': 모든 speedbump를 구성하는 꼭지점의 리스트
    # 'faces': speedbump의 각 면을 구성하는 꼭지점 idx의 집합
    # 'cnt': 현재까지 등록된 speedbump 수
    vertex_face_sets = dict()

    for obj in cw_set.data.values():
        obj.fill_in_points_evenly(step_len=point_interval)

    vertex_face_sets = dict()

    """ Crosswalk 데이터에 대한 작업 """
    for idx, obj in cw_set.data.items():
        file_name = 'crosswalk'

        # vertex, faces를 계산
        vertices, faces = obj.create_mesh_gen_points()

        # 해당 파일 이름으로 구성된 vertex_face_set에 추가한다
        # NOTE: 위쪽 일반 Surface Marking에 대한 작업도 동일
        if file_name in vertex_face_sets.keys():
            vertex_face = vertex_face_sets[file_name]

            exiting_num_vertices = len(vertex_face['vertex'])

            # 그 다음, face는 index 번호를 변경해주어야 한다
            faces = np.array(faces) # 상수를 쉽게 더하기 위해서 np array로 변경한다
            faces += exiting_num_vertices # vertex 리스트의 index가, 기존 vertex의 개수만큼 밀리게 되므로 이렇게 더해준다
            
            # 둘 다 리스트이므로, +로 붙여주면 된다.
            vertex_face['vertex'] += vertices # 그냥 리스트이므로 이렇게 붙여준다
            vertex_face['face'] += faces.tolist()
            vertex_face['cnt'] += 1

        else:
            vertex_face_sets[file_name] = {'vertex': vertices, 'face': faces, 'cnt':1}

    for file_name, vertex_face in vertex_face_sets.items():
        print('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
        file_name = os.path.normpath(os.path.join(output_path, file_name))  

        mesh_gen_vertices = vertex_face['vertex']
        mesh_gen_vertex_subsets_for_each_face = vertex_face['face']

        poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face)
        write_obj(poly_obj, file_name)

    print('END -- Create Crosswalk mesh(Obj)')




def export_feature(features, origin, freinput_path, output_path):

    # "featureType": "Stopline", ---------------------
    # "featureType": "TrafficSign",
    # "featureType": "TrafficSignal",

    # ----------------------------------surface_mark
    # "featureType": "Paint ↰↱",
    # "featureType": "Paint ↰↑↱",
    # "featureType": "Paint ↰↑",
    # "featureType": "Paint ↰",
    # "featureType": "Paint ↱",
    # "featureType": "Paint ↑↱",
    # "featureType": "Paint ↑",

    # "featureType": "BikePaint", 자전거
    # "featureType": "YieldLine", ▼▼▼▼▼▼▼▼▼▼▼ 
    # --------------------------------
    
   # "featureType": "ParkingSpace", 「 」4개
    # "featureType": "Intersection", 교차로에 있음
    # "featureType": "Crosswalk", line으로 □로 그려진것도 있고 ■ ■ ■ 로 되어있는데 obj

    # "featureType": "ImplicitYieldLine",
    # 횡단보도/주변 확인 필요한 도로에 앞으로 있는 라인, 한번 멈추려고 있는 것 같음
    # "featureType": "ImplicitStopline", 
    # ImplicitYieldLine이랑 비슷한데, 교차로에 있음
    

    print('START -- TrafficSign, TrafficSignal, Surfacemark (csv)')

    ts_asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'
    ts_to_csv_list = []

    tl_asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'
    tl_to_csv_list = []

    sm_asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'
    sm_to_csv_list = []
    
    for feature in features:

        # 표지판 정보
        if feature['properties']['featureType'] == 'TrafficSign':
            idx = feature['properties']['featureId']
            points = np.array(feature['geometry']['coordinates'][0])
            points -= origin

            point = points[0]
            signType = feature['properties']['signType']
            # "signType": "yield sign",
            # "signType": "wrong way",
            # "signType": "two lanes advanced",
            # "signType": "three lanes optional",
            # "signType": "stop sign",
            # "signType": "speed limit",
            # "signType": "signal ahead",
            # "signType": "right lane must turn right",
            # "signType": "pedestrian crossing",
            # "signType": "one way right arrow",
            # "signType": "one way left arrow",
            # "signType": "no u turn",
            # "signType": "no right turn",
            # "signType": "no parking anytime",
            # "signType": "no left turn",
            # "signType": "no left or u turn",
            # "signType": "no bike",
            # "signType": "merge ahead",
            # "signType": "left turn only",
            # "signType": "left and u turn only",
            # "signType": "keep right",
            # "signType": "general sign",
            # "signType": "do not enter",
            # "signType": "bike lane",
            # "signType": "bike crossing",
            # "signType": "advisory speed",
            prop_type = signType.replace(' ', '_')
            file_path = 'traffic_sign'
            file_name = '{}.fbx'.format(prop_type)

            # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
            file_path = ts_asset_path_root + file_path

            # INFO #2
            pos = point
            pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
            position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

            # INFO #3
            orientation_string = '0.0/0.0/0.0'

            # csv 파일 출력을 위한 리스트로 추가
            ts_to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

        # 신호등 정보
        elif feature['properties']['featureType'] == 'TrafficSignal':
            idx = feature['properties']['featureId']
            points = np.array(feature['geometry']['coordinates'][0])
            points -= origin

            point = points[0]
            # "signalType": "V:RYG:OOO" >> #TL_Ver_R_Y_SG(?)
            signType = feature['properties']['signalType']

            prop_type = signType.replace(':', '_')
            file_path = 'traffic_light'
            file_name = '{}.fbx'.format(prop_type)
            
            # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
            file_path = tl_asset_path_root + file_path

            # INFO #2
            pos = point
            pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
            position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

            # INFO #3
            orientation_string = '0.0/0.0/0.0'

            # csv 파일 출력을 위한 리스트로 추가
            tl_to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

        
        # surface marking 노면표지 KR_SurfaceMarking이 아니라
        # US_SurfaceMarking 따로 만드는거 아닌가
        elif 'Paint' in feature['properties']['featureType']:
            # "featureType": "Paint ↰↱",
            # "featureType": "Paint ↰↑↱",
            # "featureType": "Paint ↰↑",
            # "featureType": "Paint ↰",
            # "featureType": "Paint ↱",
            # "featureType": "Paint ↑↱",
            # "featureType": "Paint ↑",
            idx = feature['properties']['featureId']
            points = np.array(feature['geometry']['coordinates'][0])
            points -= origin

            point = points[0]
            featureType = feature['properties']['featureType']
            if featureType == "Paint ↰↱": # 좌우회전 5374(SHP2 type code)
                prop_type = 'RightLeftturnSign'
            elif featureType == "Paint ↰↑↱": # 전방향 5379
                prop_type = 'StraightRightLeftturnSign'
            elif featureType == "Paint ↰↑": # 직진 및 좌회전 5381
                prop_type = 'StraightLeftturnSign'
            elif featureType == "Paint ↰": # 좌회전 5372
                prop_type = 'TurnLeftSign'
            elif featureType == "Paint ↱": # 우회전 5373
                prop_type = 'TurnRightSign'
            elif featureType == "Paint ↑↱": # 직진 및 우회전 5382
                prop_type = 'StraightRightturnSign'
            elif featureType == "Paint ↑": # 직진 5371
                prop_type = 'StraightSign'
            elif featureType == "BikePaint": # BikePaint
                prop_type = 'BikePaint'

            file_path = 'surface_mark'
            file_name = '{}.fbx'.format(prop_type)

            # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
            file_path = sm_asset_path_root + file_path

            # INFO #2
            pos = point
            pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
            position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

            # INFO #3
            orientation_string = '0.0/0.0/0.0'

            # csv 파일 출력을 위한 리스트로 추가
            sm_to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

            
        output_file_name = os.path.join(output_path, 'traffic_sign.csv')
        with open(output_file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(ts_to_csv_list)

        output_file_name = os.path.join(output_path, 'traffic_light.csv')
        with open(output_file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(tl_to_csv_list)

        output_file_name = os.path.join(output_path, 'surface_mark.csv')
        with open(output_file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(sm_to_csv_list)

    print('END -- TrafficSign, TrafficSignal, Surfacemark (csv)')

def local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])


if __name__ == u'__main__':
    iuput_folder_path = 'D:/road_model_maker/rsc/map_data/deepmap_json_UCDavis'
    export_other(iuput_folder_path)