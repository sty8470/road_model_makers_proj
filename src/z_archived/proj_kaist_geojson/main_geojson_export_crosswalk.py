import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import json
import csv
import numpy as np

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.stryx.stryx_load_geojson_lane import *
from lib.stryx.stryx_geojson import *

def export_crosswalk_and_speedbump(input_path):

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

    map_info, filename_map = geojson_common.read_geojson_files(input_path)
    
    origin = map_info['A1_NODE']['features'][0]['geometry']['coordinates']
    print('[INFO] Origin Set as: ', origin)

    """데이터 읽기"""
    cw_set = create_cw_set(map_info['B4_CROSSWALK']['features'], origin)
    """포인트 내부를 수정"""
    point_interval = 0.1

    for obj in cw_set.data.values():
        obj.fill_in_points_evenly(step_len=point_interval)

    speedbump_set = CrossWalkSet()
    
    for i in map_info['C4_SPEEDBUMP']['features']:
        cw_id = i['id']
        points = np.array(i['geometry']['coordinates'][0])
        cw_type = i['properties']['Type']
        points -= origin
        cw = CrossWalk(points=points, idx=cw_id)
        cw.type_code_def = 'NGII_SHP2'
        cw.type = cw_type

        speedbump_set.append_data(cw)

    """이제 cw_set에서 mesh를 만든다"""

    # 여기에, filename 을 idx로 접근하면, 다음의 데이터가 존재한다
    # 한가지 idx = speedbump를 예를 들면, 
    # 'vertex': 모든 speedbump를 구성하는 꼭지점의 리스트
    # 'faces': speedbump의 각 면을 구성하는 꼭지점 idx의 집합
    # 'cnt': 현재까지 등록된 speedbump 수
    vertex_face_sets = dict()

    """ Crosswalk 데이터에 대한 작업 """
    for idx, obj in cw_set.data.items():
        if obj.type == '5321':
            file_name = 'crosswalk_pedestrian'
        elif obj.type == '534':
            file_name = 'crosswalk_bike'
        elif obj.type == '533':
            file_name = 'crosswalk_plateau_pedestrian'
        else:
            # 우선 과속방지턱이 아닌 대상은 우선 mesh 생성에서 제외한다.
            print('[WARNING] cw: {} skipped (currently not suppored type'.format(idx))
            continue

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


    """ SpeedBump 데이터에 대한 작업 """
    for idx, obj in speedbump_set.data.items():
        file_name = 'speedbump'
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

    print('END')


if __name__ == u'__main__':
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201203_KAIST_3rd'
    export_crosswalk_and_speedbump(input_path)
    