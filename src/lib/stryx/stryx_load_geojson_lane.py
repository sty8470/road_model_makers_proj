import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(current_path + '/../lib/common/')

import json
import csv
import numpy as np

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_lane_boundary, edit_line
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.stryx.stryx_geojson import *
from lib.stryx.stryx_hdmap_importer import StryxHDMapImporter


def load_stryx_lane(input_path):

    relative_loc = True
    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))

    # Get File List
    map_info, filename_map = geojson_common.read_geojson_files(input_path)

    # map_info['A1_NODE']
    # map_info['A2_LINK']
    # map_info['A5_PARKINGLOT']
    # map_info['B2_SURFACELINEMARK'] >> 차선 위치/교차로 유도선
    # map_info['B3_SURFACEMARK']
    # map_info['B4_CROSSWALK']
    # map_info['C3_VEHICLEPROTECTIONSAFETY'] >> 도로 경계
    # map_info['D3_SIDEWALK'] >> 인도

    origin = map_info['A1_NODE']['features'][0]['geometry']['coordinates']
    print('[INFO] Origin Set as: ', origin)

    importer = StryxHDMapImporter()
    node_link_mgeo = importer.import_geojson(input_path)

    node_set = node_link_mgeo.node_set
    link_set = node_link_mgeo.link_set

    lane_node_set = NodeSet()
    lane_boundary_set = LaneBoundarySet()

    surf_line_list = map_info['B2_SURFACELINEMARK']['features']

    for surf_line in surf_line_list:
        lane_marking_id = surf_line['properties']['id']
        points = np.array(surf_line['geometry']['coordinates'])
        points -= np.array(origin)
    
        start_node = Node(lane_marking_id+'S')
        start_node.point = points[0]
        lane_node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = points[-1]
        lane_node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)
        
        lane_boundary.lane_shape = surf_line['properties']['Style']
        lane_boundary.lane_color = [surf_line['properties']['Color']]
        lane_boundary.lane_type_def = 'NGII_SHP2'

        # 세부 속성 설정 차선 유형
        lane_type = surf_line['properties']['Kind']
        if lane_type == '501': # 중앙선
            lane_boundary.lane_type = [501]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3


        elif lane_type == '5011': # 가변차선
            lane_boundary.lane_type = [5011]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3

        elif lane_type == '502': # 유턴구역선
            lane_boundary.lane_type = [502]
            lane_boundary.lane_width = 0.35 # 너비가 0.3~0.45 로 규정되어있다.
            lane_boundary.dash_interval_L1 = 0.5
            lane_boundary.dash_interval_L2 = 0.5

        elif lane_type == '503': # 차선
            lane_boundary.lane_type = [503]
            lane_boundary.lane_width = 0.15
            
            # 도시 
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 5

            # # 지방도로
            # lane_boundary.dash_interval_L1 = 5
            # lane_boundary.dash_interval_L2 = 8

            # # 자동차전용도로, 고속도로
            # lane_boundary.dash_interval_L1 = 10
            # lane_boundary.dash_interval_L2 = 10

        elif lane_type == '504': # 버스전용차선
            lane_boundary.lane_type = [504]
            lane_boundary.lane_width = 0.15 
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3

        elif lane_type == '505': # 길가장자리구역선
            lane_boundary.lane_type = [505]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
        
        elif lane_type == '506':  # 진로변경제한선
            lane_boundary.lane_type = [506]
            lane_boundary.lane_width = 0.15 #점선일 때 너비가 0.1 ~ 0.5로, 넓을 수도 있다.
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3

        elif lane_type == '515': # 주정차금지선
            lane_boundary.lane_type = [515]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.

        elif lane_type == '525': # 유도선
            lane_boundary.lane_type = [525]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 0.75 # 0.5 ~ 1.0
            lane_boundary.dash_interval_L2 = 0.75 # 0.5 ~ 1.0

        elif lane_type == '530': # 정지선
            lane_boundary.lane_type = [530]
            lane_boundary.lane_width = 0.6 # 정지선은 0.3 ~ 0.6
            lane_boundary.dash_interval_L1 = 0 # 정지선에서는 의미가 없다
            lane_boundary.dash_interval_L2 = 0 # 정지선에서는 의미가 없다.

        elif lane_type == '531': # 안전지대
            lane_boundary.lane_type = [531]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
            # 531만 null값으로 있어서 넣음
            lane_boundary.lane_shape = [ "Solid" ]

        elif lane_type == '535': # 자전거도로
            lane_boundary.lane_type = [535]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.

        elif lane_type == '599': # 기타선
            lane_boundary.lane_type = [599]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.

        else:
            raise BaseException('Unexpected lane_type = {}'.format(surf_line['properties']['Kind']))

        lane_boundary.lane_type_offset = [0]
        lane_boundary_set.lanes[lane_boundary.idx] = lane_boundary

    mgeo_planner_map = MGeo(
        node_set=node_set, link_set=link_set, lane_node_set=lane_node_set, lane_boundary_set=lane_boundary_set)

    mgeo_planner_map.set_origin(origin)

    return mgeo_planner_map


def save_mesh(input_path):

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
    
    mgeo_planner_map = load_stryx_lane(input_path)
    lane_boundary_set = mgeo_planner_map.lane_marking_set
    
    vertex_face_sets = dict()
    

    for idx, lane in lane_boundary_set.lanes.items():
        edit_line.fill_in_points_evenly(lane, 0.1)
        # 파일 이름 생성
        if lane.lane_type == 530: # 정지선
            file_name = 'w_misc_stop_line'
        elif lane.lane_type == 525: # 교차로 내 유도선
            file_name = 'w_misc_intersection_guide_line'
        elif lane.lane_type == 502: # 유턴 구역선
            file_name = 'w_misc_u_turn_marking'
        else:
            if lane.get_lane_num() == 1:
                file_name = '{}_{}'.format(lane.lane_color[0], lane.lane_shape[0])
            else:
                file_name = '{}_{}_{}'.format(lane.lane_color[0], lane.lane_shape[0], lane.lane_shape[1])
    
        # 해당 lane의 vertex, faces를 계산
        
        vertices, faces = edit_lane_boundary.create_mesh_gen_points(lane)

        # 해당 파일 이름으로 구성된 vertex_face_set에 추가한다
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

    print('export_lane_mesh done OK')


if __name__ == u'__main__':
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201203_KAIST_3rd'
    save_mesh(input_path)
    