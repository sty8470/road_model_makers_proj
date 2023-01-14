import copy
import os
import sys

from shapefile import NULL
from lib.mgeo.class_defs.lane_boundary_structure import make_tunnel_structure
from lib.opendrive.mesh_utils import vtkFlip_y, vtkSwap_yz

from proj_mgeo_editor_morai_opengl.StructureVariableManager import StructureVariableManager
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import numpy as np
from tkinter import filedialog
import json
import csv

# MGeo Module
from lib.mgeo.class_defs import *
from lib.mgeo.save_load import *
from lib.mgeo.mesh_gen import * 
from lib.mgeo.edit.funcs import edit_lane_boundary, edit_line, edit_singlecrosswalk, edit_surfacemarking
from lib.mgeo.utils import error_fix, file_io, lane_change_link_creation
from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_mgeo_planner_map
from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj


from lib.common.logger import Logger
from lib.common.polygon_util import *


# NGII Library
from lib_ngii_shp1 import ngii_shp1_to_mgeo
from lib_ngii_shp_ver2 import ngii_shp2_to_mgeo, morai_sim_build_data_exporter
from lib.fourtytwodot import hdmap_42dot_importer

from lib.common.coord_trans_srs import get_tranform_UTM52N_to_TMMid, get_tranform_UTMK_to_TMMid

from PyQt5.QtWidgets import *
from PyQt5.Qt import *


# lane_mark 정리
def simplify_lane_markings(map_data):
    simplify_candidate = list()

    node_set = map_data.lane_node_set
    lane_set = map_data.lane_boundary_set

    for idx, node in node_set.nodes.items():
        if len(node.get_to_links()) == 1 and len(node.get_from_links()) == 1:
                
            # 또한, attribute가 같아야 한다!
            to_link = node.get_to_links()[0]
            from_link = node.get_from_links()[0]
            if from_link.is_every_attribute_equal(to_link):
                simplify_candidate.append(node)

    Logger.log_info('{} nodes (out of total {}) will be deleted'.format(
        len(simplify_candidate),
        len(node_set.nodes.keys())))

    # 이미 삭제한 라인의 idx를 저장 >> 중복으로 삭제 요청하는 걸 막기 위함
    removed_line_idx = []
    for sc_node in simplify_candidate:
        # for each node, connect its from_link and to_link together
        # then, update each from_node and to_node
        # NOTE: (hjpark) 아직 여러 경우에 수에 대해 테스팅이 필요함
        #       특히 to_node, from_node를 여러 개 소유하는 node의 경우
        #       for문 대신 index[0]를 explicit하게 처리하여 (구현 편의 위해)
        #       충분히 예외가 발생할 여지가 있음 
        current_node_to_link = sc_node.get_to_links()[0]
        current_node_from_link = sc_node.get_from_links()[0]

        # 선 2개로 이뤄진 circular line 예외처리
        if current_node_from_link == current_node_to_link:
            continue

        # closed plane들은 최소 2개의 line으로 구성되도록 조치
        # 시험용으로 도입하였으나, 롤백하는걸로 결정
        # if current_node_to_link.get_to_node() == \
        #     current_node_from_link.get_from_node():
        #     continue

        # 새로운 라인/링크 생성
        new_line = LaneBoundary()

        # 포인트 생성 시, from_link의 마지막점과, to_link의 시작점이 겹치므로 from_link에서 마지막 점을 제외시킨다
        new_line.set_points(np.vstack((current_node_from_link.points[:-1], current_node_to_link.points)))

        to_node = sc_node.get_to_nodes()[0]
        from_node = sc_node.get_from_nodes()[0]
            
        to_node.remove_from_links(current_node_to_link)
        from_node.remove_to_links(current_node_from_link)

        new_line.set_to_node(to_node)
        new_line.set_from_node(from_node)

        new_line.get_attribute_from(current_node_from_link)

        lane_set.append_line(new_line, create_new_key=True)                       

            
        # 삭제되는 대상은 plot을 지우고, 새로운 대상은 plot을 그린다
        # current_node_to_link.erase_plot()
        # current_node_from_link.erase_plot()
        # sc_node.erase_plot()
        # new_line.draw_plot(ax)

        lane_set.remove_line(current_node_to_link)
        lane_set.remove_line(current_node_from_link)
        node_set.remove_node(sc_node)

    Logger.log_info('Starting to update plot ... ')
    Logger.log_info('Simplify operation done OK. Plot update finished.')

    
    map_data.lane_node_set = node_set
    map_data.lane_boundary_set = lane_set

    return map_data

# 차선 points 간격 바꾸기
def fill_points_in_lane_markings(map_data, step_len, points_keep=False):
    node_set = map_data.lane_node_set
    lane_set = map_data.lane_boundary_set
    # step_len = 0.1
    for idx, lane in lane_set.lanes.items():
        edit_line.fill_in_points_evenly(lane, step_len, points_keep)

    map_data.lane_node_set = node_set
    map_data.lane_boundary_set = lane_set

    return map_data

def fill_points_in_lane_markings_deep_copy_return(map_data, step_len):
    
    cp_laneboundary_set = copy.deepcopy(map_data.lane_boundary_set)

    for idx, lane in cp_laneboundary_set.lanes.items():
        if lane.lane_type == 999:
            continue
        edit_line.fill_in_points_evenly(lane, step_len)

    return cp_laneboundary_set


##### File >> Export >> CSV File 관련 함수 #####

def export_link_as_csv(map_data, output_path):
    lines = map_data.link_set.lines
    relative_loc = True

    for idx in lines:
        fileOpenMode = 'a'
        each_out = output_path
        line_points = lines[idx].points
       
        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            # coord_obj가
            # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
            # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
            is_single_line = _is_single_line_obj(line_points)
                
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = line_points
                _write_single_line(writer, line, relative_loc)

            else:
                print('[DEBUG] line type = {}, # of line = {}'.format(idx, len(line_points)))
                for line in line_points:
                    writer.writerow(line)


def export_lane_marking_as_csv(map_data, save_path):
    fill_points_in_lane_markings(map_data, 0.1)
    simplify_lane_markings(map_data)

    relative_loc = True
   
    lanes = map_data.lane_boundary_set.lanes


    for idx in lanes:
        fileOpenMode = 'a'
        each_out = save_path
        lane_points = lanes[idx].points
        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            # coord_obj가
            # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
            # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
            is_single_line = _is_single_line_obj(lane_points)
                
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = lane_points
                _write_single_line(writer, line, relative_loc)

            else:
                print('[DEBUG] line type = {}, # of line = {}'.format(idx, len(lane_points)))
                for line in lane_points:
                    writer.writerow(line)



##### 에디터 Export에 있는 기능 #####
""" road_mesh csv 파일 출력"""
def export_road_mesh(map_data, output_path, step_len=None):
    relative_loc = True
    output_file_name_prefix = ''
    output_file_name_suffix = '.csv'
    output_file_name_list = dict()
    type_name_list = list()

    output_path = os.path.join(output_path, '{}m'.format(step_len)) 
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    except OSError:
        print('Error: Creating directory. ' +  output_path)

    type_names = ['CenterLine', 
                    'NormalLane', 
                    'MiscLane', 
                    'RoadEdge',
                    'SafeArea',
                    'Barrier',
                    'StopLine',
                    'DrivePath',
                    'NoParking',
                    'BikeLane',
                    'GuardRail',
                    'ConcreteCurb',
                    'Greenbelt',
                    'Concrete',
                    'Parking',
                    'Greenbelt',
                    'TrafficIsland',
                    'BusStop',
                    'UnknownBarrier',
                    'Fence'
                    ]
    for type_name in type_names:
        type_name_list.append(type_name)
        output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
        output_file_name_list[type_name] = output_file_name

    for key in output_file_name_list.keys():
        output_file_name_list[key] = os.path.join(
            output_path, output_file_name_list[key])

    for key in output_file_name_list.keys():
        each_out = output_file_name_list[key]
        if os.path.exists(each_out):
            print('[WARNING] Removing an existing file... ({})'.format(each_out))
            os.remove(each_out)
        
        fileOpenMode = 'w'
        with open(each_out, fileOpenMode, newline='') as csvfile:
            continue
    for key in output_file_name_list.keys():
        each_out = output_file_name_list[key]
        print('[INFO] Created a new file: ({})'.format(each_out))

    lanes = map_data.lane_boundary_set.lanes

    for idx in lanes:

        lane_type = lanes[idx].lane_type[0]
        
        # 횡단보도
        if lane_type == 999:
            continue
        
        # 미국 tomtom 값
        if lane_type == 101:
            key = 'ConcreteCurb'
        elif lane_type == 103:
            key = 'NormalLane'
        elif lane_type == 100:
            key = 'Barrier'
        elif lane_type == 105:
            key = 'RoadEdge'
        elif lane_type == 1021:
            key = 'Guardrail'
        elif lane_type == 1022:
            key = 'UnknownBarrier'
        elif lane_type == 1023:
            key = 'Fence'

        # 한국 기준
        elif lane_type == 501:
            key = 'CenterLine'
        elif lane_type == 5011 or lane_type == 502  or lane_type == 503 or lane_type == 504 or lane_type == 506 or lane_type == 525:
            key = 'NormalLane'
        elif lane_type == 505 or lane_type == 1:
            key = 'RoadEdge'
        elif lane_type == 515:
            key = 'NoParking'
        elif lane_type == 531:
            key = 'SafeArea'
        elif lane_type == 535:
            key = 'BikeLane'
        elif lane_type == 530:
            key = 'StopLine'
        elif lane_type == 599 or lane_type == 99 or lane_type == 7:
            key = 'MiscLane'
        elif lane_type == 2 or lane_type == 6 or lane_type == 5:
            key = 'GuardRail'
        elif lane_type == 4:
            key = 'ConcreteCurb'
        elif lane_type == 3 or lane_type == 8:
            key = 'Concrete'
        elif lane_type == 900:
            key = 'Parking'
        elif lane_type == 1111:
            key = 'Greenbelt'
        elif lane_type == 500:
            key = 'TrafficIsland'
        elif lane_type == 400:
            key = 'BusStop'
        else:
            print('lane_type : ({}) is not exported.'.format(lane_type))
            continue

        fileOpenMode = 'a'
        each_out = output_file_name_list[key]
        # lane_points = lanes[idx].points
        # 출력할 때만 포인트 정리
        if step_len is None:
            lane_points = lanes[idx].points
        else:
            lane_points = edit_line.calculate_evenly_spaced_link_points(lanes[idx], step_len)

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            # coord_obj가
            # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
            # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
            is_single_line = _is_single_line_obj(lane_points)
                
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = lane_points
                _write_single_line(writer, line, relative_loc)

            else:
                print('[DEBUG] line type = {}, # of line = {}'.format(key, len(lane_points)))
                for line in lane_points:
                    csvwriter.writerow(line)

    # Drivepath로 출력되는 부분
    # lines = map_data.link_set.lines
    # for idx in lines:
    #     key = 'DrivePath'
    #     fileOpenMode = 'a'
    #     each_out = output_file_name_list[key]
    #     # lane_points = lines[idx].points
    #     lane_points = lines[idx].calculate_evenly_spaced_link_points(step_len)
    #     with open(each_out, fileOpenMode, newline='') as csvfile:
    #         writer = csv.writer(csvfile, delimiter = ',')
    #         # coord_obj가
    #         # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
    #         # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
    #         is_single_line = _is_single_line_obj(lane_points)
    #         if is_single_line:
    #             # print('[DEBUG] line type = {}, # of line = 1'.format(key))
    #             line = lane_points
    #             _write_single_line(writer, line, relative_loc)
    #         else:
    #             print('[DEBUG] line type = {}, # of line = {}'.format(key, len(lane_points)))
    #             for line in lane_points:
    #                 csvwriter.writerow(line)


""" lane_mark obj 파일 출력"""
def export_lane_mesh(map_data, save_path, mgeo_key, widget_result):
    # 차선정리, 0.1간격은 출력할때만 사용
    simplify_lane_markings(map_data)

    lane_height = float(widget_result['lane_height'])
    if widget_result['lane']:
        export_lane_boundary_mesh(map_data, save_path, lane_height)
    if widget_result['stopline']:
        export_lane_boundary_mesh(map_data, save_path, lane_height, only_stop=True)
    if widget_result['crosswalk']:
        export_crosswalk(map_data, save_path, lane_height)




def export_lane_boundary_mesh(map_data, save_path, lane_height, only_stop=False):
    
    node_set = map_data.lane_node_set
    lane_set = map_data.lane_boundary_set
    vertex_face_sets = dict()
    crosswalk_set = SingleCrosswalkSet()

    # TODO: 여기 구현해서 넣어야 함
    for idx, lane in lane_set.lanes.items():

        lane_shape_list = lane.lane_shape
        lane_color_list = lane.lane_color
        lane_type_list = lane.lane_type
        lane_type_offset = lane.lane_type_offset

        if len(lane_shape_list) != len(lane_type_offset):
            raise BaseException('ERROR lane_id : {} len(lane_shape) != len(lane_type_offset)'.format(lane.idx))

        # 출력할 때만 포인트 정리
        origin_lane_points = lane.points
        lane.points = edit_line.calculate_evenly_spaced_link_points(lane, 0.1)
        lane.points[:,2] += lane_height

        lane_length = lane.get_total_distance()
        lane_shape_count = len(lane_shape_list)

        start_point_idx = 0
        end_point_idx = 0

        for ind in range(lane_shape_count):
            export_lane = LaneBoundary()
            lane_shape = lane_shape_list[ind]

            export_lane.lane_shape = lane_shape.split(' ')
            export_lane.lane_color = lane_color_list[ind]
            export_lane.lane_type = lane_type_list[ind]

            start_lane_offset = lane_type_offset[ind]
            if ind+1 == lane_shape_count:
                end_lane_offset = 1
            else:
                end_lane_offset = lane_type_offset[ind+1]
            if start_lane_offset == 0:
                start_point_idx = 0
            else:
                start_point_idx = end_point_idx
                # start_point_idx = int(math.floor(start_lane_offset*lane_length))
            if end_lane_offset == 1:
                end_point_idx = len(lane.points)-1
            else:
                end_point_idx = int(math.floor(end_lane_offset*lane_length)*10)
            export_lane.points = lane.points[start_point_idx:end_point_idx]
            
            export_lane.lane_width = lane.lane_width
            export_lane.dash_interval_L1 = lane.dash_interval_L1
            export_lane.dash_interval_L2 = lane.dash_interval_L2
            export_lane.double_line_interval = lane.double_line_interval
            export_lane.idx = '{}_{}'.format(lane.idx, ind)

            if str("structure") in lane.idx :
                # structure laneboundary는 pass.
                continue
            if only_stop and export_lane.lane_type != 530:
                continue
                
            # 파일 이름 생성
            if export_lane.lane_type == 530: # 정지선
                file_name = 'w_misc_stop_line'
                export_lane.lane_width = 0.6 # 정지선은 0.3 ~ 0.6
                export_lane.dash_interval_L1 = 0 # 정지선에서는 의미가 없다
                export_lane.dash_interval_L2 = 0 # 정지선에서는 의미가 없다.

            elif export_lane.lane_type == 525: # 교차로 내 유도선
                file_name = 'w_misc_intersection_guide_line'
                export_lane.lane_width = 0.15
                export_lane.dash_interval_L1 = 0.75 # 0.5 ~ 1.0
                export_lane.dash_interval_L2 = 0.75 # 0.5 ~ 1.0

            elif export_lane.lane_type == 502: # 유턴 구역선
                file_name = 'w_misc_u_turn_marking'
                export_lane.lane_width = 0.35 # 너비가 0.3~0.45 로 규정되어있다.
                export_lane.dash_interval_L1 = 0.5
                export_lane.dash_interval_L2 = 0.5

            elif export_lane.lane_type in [3, 8]:# 콘크리트도 obj 형식으로 출력하기
                file_name = 'concrete_line'
            elif export_lane.lane_type in [2, 6, 5, 1021]:# 가드레일도 obj 형식으로 출력하기
                file_name = 'guardrail_line'
            else:
                if export_lane.get_lane_num() == 0:
                    raise BaseException('Lane shape does not exist.(lane_boundary id : {})'.format(lane.idx))
                if export_lane.get_lane_num() == 1:
                    file_name = '{}_{}'.format(export_lane.lane_color[0], export_lane.lane_shape[0])
                else:
                    file_name = '{}_{}_{}'.format(export_lane.lane_color[0], export_lane.lane_shape[0], export_lane.lane_shape[1])
            

            # 해당 lane의 vertex, faces를 계산
            vertices, faces, uvcoords = edit_lane_boundary.create_mesh_gen_points(export_lane)

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
                vertex_face['uv'] += uvcoords
                vertex_face['cnt'] += 1

            else:
                vertex_face_sets[file_name] = {'vertex': vertices, 'face': faces, 'uv': uvcoords, 'cnt':1 }
            # 차선 포인트 원래대로
        lane.points = origin_lane_points


    for file_name, vertex_face in vertex_face_sets.items():
        Logger.log_info('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
        file_name = os.path.normpath(os.path.join(save_path, file_name))
        
        mesh_gen_vertices = vertex_face['vertex']
        mesh_gen_vertex_subsets_for_each_face = vertex_face['face']
        mesh_gen_uv_coords = vertex_face['uv']

        poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face, mesh_gen_uv_coords)
        poly_obj = vtkFlip_y(poly_obj)
        poly_obj = vtkSwap_yz(poly_obj)
        write_obj(poly_obj, file_name)

    Logger.log_info('export_lane_mesh done OK')


def export_structure_mesh(map_data, save_path) :
    # 현재 출력할 데이터가 구조물 데이터인지 판단.
    # structure 구조물 params config file input.
    StructureVariableManager.get_instance().load_structure_config()
    
    # mat_config.json 만들기.
    material_dic = dict()

    # 구조물.
    structure_obj_name_dic = export_structure_obj_mesh(map_data, save_path)

    for st_k, st_v in structure_obj_name_dic.items() :
        if st_k not in material_dic :
            material_dic[st_k] = list()
        for st_v_list_value in st_v :
            material_dic[st_k].append(st_v_list_value)

    if len(StructureVariableManager.get_instance().tunnel_list) > 0 :
        # 터널 생성.
        tunnel_obj_name_dic = export_tunner_mesh(map_data, save_path)

        for tn_k, tn_v in tunnel_obj_name_dic.items() :
            if tn_k not in material_dic :
                material_dic[tn_k] = list()
            for tn_v_list_value in tn_v :
                material_dic[tn_k].append(tn_v_list_value)

    # create mat_config.json
    mat_file_name = os.path.normpath(os.path.join(save_path, "mat_config.json"))  
    with open(mat_file_name, 'w') as f:
        json.dump(material_dic, f, indent=2)


def export_structure_obj_mesh(map_data, save_path) :
    # laneboundary의 points 가 늘어나서 메쉬 출력 후 editor 느려지기에 copy해서 사용하도록 수정.
    cp_laneboundary_set = fill_points_in_lane_markings_deep_copy_return(map_data, 0.1)

    lane_set = cp_laneboundary_set
    file_count_dic = dict()
    vertex_face_sets = dict()
    divide_count = 0

    ret_file_names = dict()


    # structure laneboundary는 lane_type_def 가 아래 이름으로 되어 있어야 합니다.
    structure_laneboundary_list = list()
    structure_laneboundary_list.append(str("RoadRunner_Object"))
    structure_laneboundary_list.append(str("Autoever_Object"))
    structure_laneboundary_list.append(str("modify"))
    # Hyundai AutoEver 타입 추가, 하나의 lane_boundary에 여러개 타입 있어서 나눠서 출력
    structure_laneboundary_list.append(str("Hyundai AutoEver"))
    
    for idx, lane in lane_set.lanes.items():
        is_structure = False
        # structure 아닌 lane boundary 거르기.
        for structure_type_def in structure_laneboundary_list :
            if structure_type_def in lane.lane_type_def :
                is_structure = True
                break
        if is_structure == False : 
            continue
        
        lane_type_list = lane.lane_type
        lane_type_offset = lane.lane_type_offset
        
        if len(lane_type_list) != len(lane_type_offset):
                raise BaseException('ERROR lane_id : {} len(lane_type_list) != len(lane_type_offset)'.format(lane.idx)) 
        
        originpoints = lane.points
        lane.points = edit_line.calculate_evenly_spaced_link_points(lane, 0.1)
        lane_length = lane.get_total_distance()
        lane_type_count = len(lane_type_list)
        lane_sub_type = lane.lane_sub_type

        for ind in range(lane_type_count):
            if lane.lane_color[ind] in ['yellow', 'white', 'blue']:
                continue

            export_lane = LaneBoundary()
            lane_type = lane_type_list[ind]
            
            start_lane_offset = lane_type_offset[ind]
            if ind+1 == lane_type_count:
                end_lane_offset = 1
            else:
                end_lane_offset = lane_type_offset[ind+1]
            
            start_point_idx = int(math.floor(start_lane_offset*lane_length))
            if end_lane_offset == 1:
                end_point_idx = len(lane.points)-1
            else:
                end_point_idx = int(math.floor(end_lane_offset*lane_length)*10)
            export_lane.points = lane.points[start_point_idx:end_point_idx]

            if lane_type in [131, 605]: # 방음벽
                lane_type = 3
            elif lane_type in [129, 136]: # 가드레일
                lane_type = 2
            elif lane_type in [130, 128]: # 중앙분리대
                lane_type = 1
            else:
                lane_type = 0

            export_lane.lane_type = lane_type


            f_name = str("")
            prefix = str("")

            if lane_sub_type == 0 or lane_sub_type == None :
                if lane_type == 3 :
                    f_name = str("Sound_Proof")
                elif lane_type == 2 :
                    f_name = str("Guard_Rail")
                elif lane_type == 1 :
                    f_name = str("Center_Concrete")
            else :
                # AutoEver의 road edge 타입은 일단 명확해지기 전까지 보류. 2021.11.22 정택진.
                # f_name = str("roadEdge_") + str(lane.lane_sub_type)
                continue # 확실해지면 출력하도록 하자.

            if f_name in file_count_dic :
                f_cnt = file_count_dic[f_name]
                if f_cnt != 0 :
                    prefix = str("__") + str(f_cnt)
            else :
                file_count_dic[f_name] = 0

            file_name = f_name + prefix

            
            # mat_config.json 을 위한 준비.
            obj_file_name = file_name + str(".obj")
            if f_name not in ret_file_names :
                ret_file_names[f_name] = list()
            if obj_file_name not in ret_file_names[f_name] :
                ret_file_names[f_name].append(obj_file_name)
            
            if lane_type not in [1, 2, 3]:
                continue
            # 해당 lane의 vertex, faces를 계산
            vertices, faces, uvcoords = edit_lane_boundary.create_mesh_gen_points_structure(export_lane)

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
                vertex_face['uv'] += uvcoords
                vertex_face['cnt'] += 1
            else:
                vertex_face_sets[file_name] = {'vertex': vertices, 'face': faces, 'uv': uvcoords, 'cnt':1 }

            # 이름 변경.
            vertex_face = vertex_face_sets[file_name]
            exiting_num_vertices = len(vertex_face['vertex'])
            if divide_count != 0 and exiting_num_vertices > divide_count :
                file_count_dic[f_name] += 1


    for file_name, vertex_face in vertex_face_sets.items():
        Logger.log_info('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
        file_name = os.path.normpath(os.path.join(save_path, file_name))  

        mesh_gen_vertices = vertex_face['vertex']
        mesh_gen_vertex_subsets_for_each_face = vertex_face['face']
        mesh_gen_uv_coords = vertex_face['uv']

        poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face, mesh_gen_uv_coords)
        poly_obj = vtkFlip_y(poly_obj)
        poly_obj = vtkSwap_yz(poly_obj)
        write_obj(poly_obj, file_name)

    Logger.log_info('export structure obj mesh done OK')

    return ret_file_names


def export_tunner_mesh(map_data, save_path) :
    create_tunnel_mesh = make_tunnel_structure(map_data, save_path)
    vertex_face_sets, obj_name_dic = create_tunnel_mesh.create_tunnel_mesh()
                
    for file_name, vertex_face in vertex_face_sets.items():
        Logger.log_info('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
        file_name = os.path.normpath(os.path.join(save_path, file_name))

        mesh_gen_vertices = vertex_face['vertex']
        mesh_gen_vertex_subsets_for_each_face = vertex_face['face']
        mesh_gen_uv_coords = vertex_face['uv']

        poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face, mesh_gen_uv_coords)
        poly_obj = vtkFlip_y(poly_obj)
        poly_obj = vtkSwap_yz(poly_obj)
        write_obj(poly_obj, file_name)

    Logger.log_info('export tunnel mesh done OK')

    return obj_name_dic


""" 표지판 csv 파일 출력"""
def export_traffic_sign_csv(ts_set, output_path, ts_type_def=None):

    if ts_type_def is not None:
        __change_to_prefab_type(ts_set, ts_type_def)

    # traffic sign
    ts_csv_list = []
    ts_csv_list.append(['FolderPath','PrefabName','InitPos','InitRot','GameObjectName'])
    ts_asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'
    tss = ts_set.signals
    for ts in tss:
        idx = tss[ts].idx
        point = tss[ts].point
        file_name = tss[ts].type

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        result, file_path, file_name = get_traffic_sign_asset_path_and_name(tss[ts])
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        file_path = ts_asset_path_root + file_path

        # INFO #2
        pos = point
        pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        orientation_string = '0.0/0.0/0.0'
        orientation_string = '0.0/{:.6f}/0.0'.format(calculate_heading(tss[ts]))

        # csv 파일 출력을 위한 리스트로 추가
        ts_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

    # 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_sign.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(ts_csv_list)


""" 신호등 csv 파일 출력"""
def export_traffic_light_csv(mgeo_set, output_path, mgeo_key):
    
    int_set = mgeo_set.intersection_controller_set.intersection_controllers
    tl_set = mgeo_set.light_set
    tl_csv_list = []
    tl_csv_list.append(['FolderPath','PrefabName','InitPos','InitRot','GameObjectName', 'IntTL', 'SyncedTL'])
    tl_asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'
    tls = tl_set.signals

    if len(int_set) != 0:
        for int_id in int_set:
            int_item = int_set[int_id]
            for syn_index in range(len(int_item.TL)):
                sync_id = '{}'.format(syn_index)
                for tl in int_item.TL[syn_index]:
                    idx = tls[tl].idx
                    point = tls[tl].point
                    file_name = tls[tl].type

                    result, file_path, file_name = get_traffic_light_asset_path_and_name(tls[tl])
                    if not result:
                        # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
                        continue

                    # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
                    file_path = tl_asset_path_root + file_path
                    # INFO #2
                    pos = point
                    pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
                    position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

                    # INFO #3
                    orientation_string = '0.0/0.0/0.0'
                    orientation_string = '0.0/{:.6f}/0.0'.format(calculate_heading(tls[tl]))

                    # csv 파일 출력을 위한 리스트로 추가
                    tl_csv_list.append([file_path, file_name, position_string, orientation_string, idx, int_id, sync_id])
    else:
        for tl in tls:
            idx = tls[tl].idx
            point = tls[tl].point
            file_name = tls[tl].type

            result, file_path, file_name = get_traffic_light_asset_path_and_name(tls[tl])
            if not result:
                # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
                continue

            # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
            file_path = tl_asset_path_root + file_path
            # INFO #2
            pos = point
            pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
            position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

            # INFO #3
            orientation_string = '0.0/0.0/0.0'
            orientation_string = '0.0/{:.6f}/0.0'.format(calculate_heading(tls[tl]))

            # csv 파일 출력을 위한 리스트로 추가
            tl_csv_list.append([file_path, file_name, position_string, orientation_string, idx])


    # 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_light.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(tl_csv_list)


def export_crosswalk(map_data, save_path, lane_height):
    link_set = map_data.link_set.lines
    single_crosswalk_set = map_data.scw_set.data
    vertex_face_sets = dict()

    if len(single_crosswalk_set) > 0:
    
        for scw in single_crosswalk_set:
            current_item = single_crosswalk_set[scw]

            # ngii_model2 타입 말고 다른 타입 추가 되면 변경
            # if current_item.type_code_def == 'ngii_model2':
            if current_item.sign_type == '5321':
                file_name = 'crosswalk_pedestrian'
            elif current_item.sign_type == '534':
                file_name = 'crosswalk_bike'
            elif current_item.sign_type == '533':
                file_name = 'crosswalk_plateau_pedestrian'
            elif current_item.sign_type == 'speedbump':
                file_name = 'speedbump'
            elif current_item.sign_type == '97':
                file_name = 'parking_lot'
            elif current_item.sign_type == '98':
                file_name = 'speed_symbol'
            elif current_item.sign_type == '544':
                file_name = 'uphill_slope'
            elif current_item.sign_type == '524':
                file_name = 'no_parking'
            else:
                print('[WARNING] cw: {} skipped (currently not suppored type: {}'.format(current_item.idx, current_item.sub_type))
                continue
            
            current_item.points = np.array(current_item.points)
            current_item.points = minimum_bounding_rectangle(current_item.points)
            current_item.points = np.vstack((current_item.points, current_item.points[0]))
            current_item.points[:,2] += lane_height
            link_item = find_close_link(current_item, link_set)
            
            if 'crosswalk' not in file_name:
                vertices, faces = edit_surfacemarking.create_mesh_gen_points(current_item)

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
                    vertex_face_sets[file_name] = {'vertex': vertices, 'face': faces, 'cnt':1 }

            else:

                new_lane, min_width, max_width = print_crosswalk_to_lane_boudnary(current_item, link_item, single_crosswalk_set)
                new_lane.points = edit_line.calculate_evenly_spaced_link_points(new_lane, 0.1)
                if current_item.sign_type == '534':
                    vertices, faces, uvcoords = edit_singlecrosswalk.create_mesh_gen_points_bike_crosswalk(new_lane)
                else:
                    if int(np.ceil(min_width)) > 6:
                        vertices, faces, uvcoords = edit_singlecrosswalk.create_mesh_gen_points_crosswalk_double(new_lane, link_item)
                    else:
                        vertices, faces, uvcoords = edit_singlecrosswalk.create_mesh_gen_points_crosswalk(new_lane, link_item)

                # vertices, faces = current_item.create_mesh_gen_points()
                if file_name in vertex_face_sets.keys():
                    vertex_face = vertex_face_sets[file_name]

                    exiting_num_vertices = len(vertex_face['vertex'])

                    # 그 다음, face는 index 번호를 변경해주어야 한다
                    faces = np.array(faces) # 상수를 쉽게 더하기 위해서 np array로 변경한다
                    faces += exiting_num_vertices # vertex 리스트의 index가, 기존 vertex의 개수만큼 밀리게 되므로 이렇게 더해준다
                        
                    # 둘 다 리스트이므로, +로 붙여주면 된다.
                    vertex_face['vertex'] += vertices # 그냥 리스트이므로 이렇게 붙여준다
                    vertex_face['face'] += faces.tolist()
                    vertex_face['uv'] += uvcoords
                    vertex_face['cnt'] += 1

                else:
                    vertex_face_sets[file_name] = {'vertex': vertices, 'face': faces, 'uv': uvcoords, 'cnt':1 }


        for file_name, vertex_face in vertex_face_sets.items():
            print('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
            file_name = os.path.normpath(os.path.join(save_path, file_name))  
            
            mesh_gen_vertices = vertex_face['vertex']
            mesh_gen_vertex_subsets_for_each_face = vertex_face['face']
            
            mesh_gen_uv_coords = []
            if 'uv' in vertex_face:
                mesh_gen_uv_coords = vertex_face['uv']

            poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face, mesh_gen_uv_coords)
            poly_obj = vtkFlip_y(poly_obj)
            poly_obj = vtkSwap_yz(poly_obj)
            write_obj(poly_obj, file_name)
            

""" surface mark csv / speedbump obj 파일 출력"""
def export_surface_mark(map_data, save_path):
    surface_marking_set = map_data.sm_set.data
    link_set = map_data.link_set.lines
    
    to_csv_list = []
    to_csv_list.append(['FolderPath','PrefabName','InitPos','InitRot','GameObjectName'])
    vertex_face_sets = dict()

    if len(surface_marking_set) > 0:

        """ [STEP #1] 표지판 정보 """ 
        # 표지판 정보가 포함된 시뮬레이터 프로젝트 내 Path
        asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Models/'

        for sm in surface_marking_set:
            current_item = surface_marking_set[sm]
            if current_item.sub_type == 'speedbump':
                vertices, faces = edit_surfacemarking.create_mesh_gen_points(current_item)
                if current_item.sub_type in vertex_face_sets.keys():
                    vertex_face = vertex_face_sets[current_item.sub_type]

                    exiting_num_vertices = len(vertex_face['vertex'])

                    # 그 다음, face는 index 번호를 변경해주어야 한다
                    faces = np.array(faces) # 상수를 쉽게 더하기 위해서 np array로 변경한다
                    faces += exiting_num_vertices # vertex 리스트의 index가, 기존 vertex의 개수만큼 밀리게 되므로 이렇게 더해준다
                    
                    # 둘 다 리스트이므로, +로 붙여주면 된다.
                    vertex_face['vertex'] += vertices # 그냥 리스트이므로 이렇게 붙여준다
                    vertex_face['face'] += faces.tolist()
                    vertex_face['cnt'] += 1

                else:
                    vertex_face_sets[current_item.sub_type] = {'vertex': vertices, 'face': faces, 'cnt':1}

            else:
                sm_id = current_item.idx
                result, file_path, file_name =\
                    get_surface_marking_asset_path_and_name(current_item.sub_type, inspect_model_exists=True)
                if not result:
                    # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
                    continue
                file_path = asset_path_root + file_path

                """ 좌표 정보 찾기 """
                # if current_item.type != '5':
                return_link, return_link_index, return_lane, return_lane_index = edit_surfacemarking.find_link_near_surface_mark(current_item, link_set)

                sm_point = current_item.points
                centeroid = calculate_centroid(sm_point[0:-1])
                if return_lane is not None:
                    z_offset = return_lane_index
                    centeroid[2] = z_offset
                # if return_link is not None:
                #     x_offset = return_link.points[return_link_index][0]
                #     y_offset = return_link.points[return_link_index][1]
                #     centeroid[0] = x_offset
                #     centeroid[1] = z_offset
                pos = local_utm_to_sim_coord(centeroid)

                """ csv로 기록 """
                # 현재 포맷
                # FolderPath, PrefabName, InitPos, InitRot
                # 예시) Assets/Resources/Vehicle,KiaNiro.prefab,10.0/0.0/0.0,0.0/90.0/0.0
                position_string = '{}/{}/{}'.format(pos[0], pos[1], pos[2])
                orientation_string = '0.0/0.0/0.0'
                orientation_string = calculate_heading_for_sm(current_item, return_link, return_link_index)
                to_csv_list.append([file_path, file_name, position_string, orientation_string, sm_id])


        # 표지판 정보를 csv로 출력
        output_file_name = os.path.join(save_path, 'surface_marking_info.csv')
        with open(output_file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(to_csv_list)



##### 에셋 찾기 #####
def get_traffic_sign_asset_path_and_name(ts):
    # 주의표지	1
    # 규제표지	2
    # 지시표지	3
    # 보조표지	4
    idx = ts.idx
    prop_type = to_str_if_int(ts.type)
    prop_sub_type = to_str_if_int(ts.sub_type)
    prop_value = ts.value

    if prop_type == '9' or prop_sub_type is None:
        print('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with Type = {} (ts id = {})'.format(prop_type, idx))
        # print("{} Type = none or 9".format(idx))
        return False, '', ''

    # UPDATE(sglee): 지원 안 되는 prop_sub_type 지속적으로 업데이트
    if prop_sub_type in ['199', '299', '399', '499']:
        # 225: 최저 속도 제한 >> 최저 속도 값을 link에서 받아와야 모델을 특정할 수 있는데, link에 최저 속도 값이 없음 

        print('[WARNING] @ __get_traffic_sign_asset_path_and_name: no supported model for this prop_sub_type = {} (ts id = {})'.format(prop_sub_type, idx))
        return False, '', ''

    if prop_type == '1':
        file_path = '01_MapCommon_Signs/KR/01_Caution_Beam'
        file_name = '01_Caution_{}_Beam.prefab'.format(prop_sub_type)

    elif prop_type == '2':
        file_path = '01_MapCommon_Signs/KR/02_Restriction_Beam'
        
        if prop_sub_type == '224':
            if (prop_value is None) or (prop_value is '') or (prop_value is 0):
                prop_value = '60' # 최고 속도제한 60 으로 일단 정함
                # raise BaseException('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with sub_type = {} (ts id = {})'.format(prop_sub_type, idx))
            # prop_subtype을 변경해준다
            prop_sub_type = '{}_{}kph'.format(prop_sub_type, prop_value)
            
        if prop_sub_type == '225':
            if (prop_value is None) or (prop_value is '') or (prop_value is 0):
                prop_value = '60' # 최저 속도제한 60 으로 일단 정함
                # raise BaseException('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with sub_type = {} (ts id = {})'.format(prop_sub_type, idx))
            # prop_subtype을 변경해준다
            prop_sub_type = '{}_{}kph'.format(prop_sub_type, prop_value)

        if prop_sub_type == '220':
            if (prop_value is None) or (prop_value is '') or (prop_value is 0):
                prop_value = '40' # 차 중량 제한 40 으로 일단 정함
                # raise BaseException('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with sub_type = {} (ts id = {})'.format(prop_sub_type, idx))
            # prop_subtype을 변경해준다
            prop_sub_type = '{}_{}t'.format(prop_sub_type, prop_value)
        file_name = '02_Restriction_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '3':
        file_path = '01_MapCommon_Signs/KR/03_Indication_Beam'
        file_name = '03_Indication_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '4':
        file_path = '01_MapCommon_Signs/KR/04_Aux_Beam'
        file_name = '04_Aux_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == 'US':
        file_path = 'US_TS'
        file_name = '{}.prefab'.format(prop_sub_type)

    else:
        raise BaseException('[ERROR] @ get_traffic_sign_asset_path_and_name: unexpected prop_type! (ts id = {})'.format(idx))

    return True, file_path, file_name

def get_traffic_light_asset_path_and_name(tl):

    idx = tl.idx
    prop_type = tl.type
    prop_sub_type = tl.sub_type

    if prop_type == 'pedestrian':
        file_path = '01_MapCommon_PS/KR'
        file_name = 'PS_R_G.prefab'

    elif prop_type == 'car':
        file_path = '01_MapCommon_TL/KR'

        light_prefab = ''
        if tl.orientation == 'horizontal':
            light_prefab += 'TL_Hor'
        elif tl.orientation == 'vertical': 
            light_prefab += 'TL_Ver'
        
        for light_item in prop_sub_type:
            if light_item == 'red':
                light_prefab += '_R'
            elif light_item == 'yellow':
                light_prefab += '_Y'
            elif light_item == 'left':
                light_prefab += '_L'
            elif light_item == 'straight':
                light_prefab += '_G'
        file_name = '{}.prefab'.format(light_prefab)

    elif prop_type == 'bus':
        file_path = '01_MapCommon_TL/KR'
        # 현재 프리팹 기준
        light_prefab = 'TL_Hot_R_Y_G_Bus'
        # light_prefab = 'TL_Ver'
        # for light_item in prop_sub_type:
        #     if light_item == 'red':
        #         light_prefab += '_R'
        #     elif light_item == 'yellow':
        #         light_prefab += '_Y'
        #     elif light_item == 'left':
        #         light_prefab += '_L'
        #     elif light_item == 'straight':
        #         light_prefab += '_G'
        file_name = '{}.prefab'.format(light_prefab)


    # if prop_type == '1': # 삼색등
    #     file_path = '01_MapCommon_TL/KR'
    #     file_name = 'TL_Hor_R_Y_G.prefab'

    # elif prop_type == '2': # 사색등A	2
    #     file_path = '01_MapCommon_TL/KR'
    #     file_name = 'TL_Hor_R_Y_L_G.prefab'
    
    # elif prop_type =='5': # 종형 삼색등
    #     file_path = '01_MapCommon_TL/KR'
    #     file_name = 'TL_Ver_R_Y_G.prefab'

    # elif prop_type == '9': # 가변형 삼색등
    #     file_path = '01_MapCommon_TL/KR'
    #     file_name = 'TL_Hor_R_Y_L.prefab'

    # elif prop_type == '11':
    #     # 보행자 신호등 (NGII)
    #     file_path = '01_MapCommon_PS/KR'
    #     file_name = 'PS_RG.prefab'
    
    # # 미국 신호등
    # elif prop_type == 'US':
    #     file_path = 'US_TL'
    #     file_name = '{}.prefab'.format(prop_sub_type)
    
    # TODO: 세로 삼색등
    # else:
    #     file_path = '01_MapCommon_TL/KR'
    #     file_name = 'TL_Ver_R_Y_G.prefab'
    #     print('[ERROR] @ __get_traffic_light_asset_path_and_name: unexpected prop_type! (you passed = {} (tl id = {}))'.format(prop_type, idx))

    else:
        file_path = '01_MapCommon_TL/KR'
        file_name = 'TL_Misc_NGII_Shp2_{}.prefab'.format(prop_type)
        print('[ERROR] @ __get_traffic_light_asset_path_and_name: unexpected prop_type! (you passed = {} (tl id = {}))'.format(prop_type, idx))

    return True, file_path, file_name


def local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])


def _is_single_line_obj(coord_obj):
    """
    [NOTE] Point가 실제 어디서 나오는지 확인해야 한다.
    ----------
    Case #1 >> Type = 121과 같은 경우, 겹선으로 예상되는데,
    이 때는 실제 라인이 2개이므로, coord_obj가 실제로는 선의 list 이고, 
    coord_obj[0], coord_obj[1]이 각 선을 이루는 point의 집합이 되는 구조이다. 
    즉, line0 = coord_obj[0]라고 둔다면,
    coord_obj[0][0] 가 point0가 되고, len(coord_obj[0][0])이 3이 되고, type(coord_obj[0][0][0])이 float이다.
    ----------
    Case #2 >> 그 밖의 Case에서는, 
    coord_obj가 실제 point의 집합이 된다
    즉, line0 = coord_obj이다. (위에서는 coord_obj[0]이었음!)
    coord_obj[0] 가 point0가 되고, len(coord_obj[0])이 3이 되고, type(coord_obj[0][0])이 float이다.
    ----------
    결론 >> coord_obj[0][0] 의 type이 list인지, float인지 확인하면 된다.
    """

    if 'float' in type(coord_obj[0][0]).__name__ :
        # Case #2 같은 경우임 (일반적인 경우)
        # 즉, coord_obj 1가 유일한 선이고,
        # coord_obj[0]    이 첫번째 point이고,
        # coord_obj[0][0] 이 첫번째 point의 x좌표인것
        point0 = coord_obj[0]
        if len(point0) != 3:
            raise BaseException('[ERROR] @ len(point0) != 3')
        return True

    elif type(coord_obj[0][0]) is list:
        # Case #1 같은 경우임
        # 즉, coord_obj[0], coord_obj[1] 각각이 선이다
        # coord_obj[0]       이 첫번째 line이고,
        # coord_obj[0][0]    이 첫번째 line의 첫번째 point이고
        # coord_obj[0][0][0] 이 첫번째 line의 첫번째 point의 x좌표인 것
        point0 = coord_obj[0][0]
        if len(point0) != 3:
            raise BaseException('[ERROR] @ len(point0) != 3')

        return False
    else:
        raise BaseException('[ERROR] Unexpected type for coord_obj[0][0] = {}'.format(type(coord_obj[0][0])))


def _write_single_line(csvwriter, line, relative_loc, origin=None):
    for point in line:
        if relative_loc:
            point_rel = list()
            for i in range(len(point)):
                point_rel.append(point[i])
            csvwriter.writerow(point)
            continue
        else:
            csvwriter.writerow(point)


def get_surface_marking_asset_path_and_name(prop_type, inspect_model_exists=True):
    # UPDATE(sglee): 지원 안 되는 prop_subtype 지속적으로 업데이트
    if int(prop_type) in [598, 599]:
        # 599: Misc.

        print('[WARNING] @ get_surface_marking_asset_path_and_name: no supported model for this prop_type = {}'.format(prop_type))
        return False, '', ''

    file_path = 'KR_SurfaceMarking/KR'
    file_name = '05_SurfMark_{}.fbx'.format(prop_type)

    if inspect_model_exists:
        # 개발 PC에서의 경로를 입력해준다
        abs_path = 'D:\\workspace\\sim_platform\\MasterSimulator\\Assets\\0_Master\\3_Prefabs\\RoadObjects\\KR_SurfaceMarking'
        linked_file_full_path = os.path.join(abs_path, file_name)

        # print('[DEBUG] linked_file_full_path: ', linked_file_full_path)
        # if not (os.path.exists(linked_file_full_path) and os.path.isfile(linked_file_full_path)):
        #     # 해당 모델이 존재하지 않음
        #     raise BaseException('[ERROR] @ get_surface_marking_asset_path_and_name: Unsupported model file')
    
    return True, file_path, file_name



def __change_to_prefab_type(ts_set, type_def):
    if type_def == 'autoever':
        for ts in ts_set.signals:
            # 최고속도제한	224
            # 최저속도제한	225
            current_ts = ts_set.signals[ts]
            if current_ts.type == '1':
                current_ts.type = '2'
                current_ts.value = int(current_ts.sub_type)
                current_ts.sub_type = '224'
                current_ts.type_def = 'ngii_model2'
            elif current_ts.type == '2':
                current_ts.type = '2'
                current_ts.value = int(current_ts.sub_type)
                current_ts.sub_type = '225'
                current_ts.type_def = 'ngii_model2'
            else:
                print('[ERROR] @ __change_to_prefab_type: unexpected type! (you passed = {} (tl id = {}))'.format(current_ts.type, idx))


def find_close_crosswalk(scw, scw_set):
    boundary = np.array([-15, 15])
    centeroid = np.array(calculate_centroid(scw.points[0:-1]))
    boundary_x = boundary + centeroid[0]
    boundary_y = boundary + centeroid[1]
    min_dist = 15
    min_dist_scw = None
    for idx, scw_p in scw_set.items():
        if idx == scw.idx:
            continue
        if scw_p.is_out_of_xy_range(boundary_x, boundary_y):
            continue
        scw_p_centeroid = np.array(calculate_centroid(scw_p.points[0:-1]))
        v = centeroid - scw_p_centeroid
        dist = np.sqrt(pow(v[0], 2) + pow(v[1], 2) + pow(v[2], 2))
        if dist < min_dist:
            min_dist = dist
            min_dist_scw = scw_p
    return min_dist_scw

def find_close_link(scw, link_set):
    
    v1 = scw.points[1] - scw.points[0]
    heading_v1 = v1 / np.linalg.norm(v1)
    v2 = scw.points[-2] - scw.points[0]
    heading_v2 = v2 / np.linalg.norm(v2)

    boundary_x = np.array([min(scw.points[:,0]), max(scw.points[:,0])])
    boundary_y = np.array([min(scw.points[:,1]), max(scw.points[:,1])])
    centeroid = np.array(calculate_centroid(scw.points[0:-1]))
    min_dist = 20
    min_dist_link = None
    for idx, link_p in link_set.items():
        if link_p.is_out_of_xy_range(boundary_x, boundary_y):
            continue
        
        vl = link_p.points[-1] - link_p.points[0]
        heading_vl = vl / np.linalg.norm(vl)
        cv1 = np.inner(heading_v1, heading_vl)
        cv2 = np.inner(heading_v2, heading_vl)

        if abs(cv1) < 0.5 and abs(cv2) < 0.5:
            continue

        lpoint = [link_p.to_node.point, link_p.from_node.point]
        for pp in lpoint:
            v = centeroid - pp
            dist = np.sqrt(pow(v[0], 2) + pow(v[1], 2) + pow(v[2], 2))
            if dist < min_dist:
                min_dist = dist
                min_dist_link = link_p
    try:
        return_val = min_dist_link.from_node.from_links[0]
    except:
        return_val = min_dist_link

    return return_val

def print_crosswalk_to_lane_boudnary(scw, link_item, scw_set):


    link_vector = None
    if link_item is not None:
        link_vector = link_item.points[-1] - link_item.points[0]
        link_vector = link_vector / np.linalg.norm(link_vector, ord=2)
    # solid/broken double lane
    point_step = 0.1

    v1 = scw.points[1] - scw.points[0]
    dist1 = np.sqrt(pow(v1[0], 2) + pow(v1[1], 2) + pow(v1[2], 2))
    v2 = scw.points[-2] - scw.points[0]
    dist2 = np.sqrt(pow(v2[0], 2) + pow(v2[1], 2) + pow(v2[2], 2))

    v1_vector = v1 / np.linalg.norm(v1, ord=2)
    v2_vector = v2 / np.linalg.norm(v2, ord=2)
    # 자전거 횡단보도 한쪽은 점선, 한쪽은 실선 -> 중앙선 기준으로(?)
    if dist1 < dist2:
        point_idx = 0
        min_width = dist1
        max_width = dist2
    else:
        point_idx = 1
        min_width = dist2
        max_width = dist1

    if link_vector is not None and min_width > 5 and max_width > 6:
        if max_width-min_width < 6:
            if abs(np.inner(link_vector, v1_vector)) > 0.9:
                point_idx = 0
                min_width = dist1
                max_width = dist2
            elif abs(np.inner(link_vector, v2_vector)) > 0.9:
                point_idx = 1
                min_width = dist2
                max_width = dist1
                
    new_line_point = []
    new_point1 = (scw.points[point_idx] + scw.points[point_idx + 1]) / 2.0
    new_line_point.append(new_point1)
    new_point2 = (scw.points[point_idx + 2] + scw.points[point_idx + 3]) / 2.0
    new_line_point.append(new_point2)

        
    if scw.sign_type == '534':
        lane_width = 0.15
        double_line_interval = min_width
        close_scw = find_close_crosswalk(scw, scw_set)
        if close_scw is None:
            Logger.log_info('cresswalk(bike) id {} is no pedestrian crosswalk nearby.'.format(scw.idx))
            lane_shape = ['Solid', 'Broken']
        else:
            v1 = new_point1 - new_point2
            v2 = np.array(calculate_centroid(close_scw.points[0:-1])) - new_point2
            heading_v1 = v1 / np.linalg.norm(v1)
            heading_v2 = v2 / np.linalg.norm(v2)
            cross = np.cross(heading_v1[0:2], heading_v2[0:2])
            if cross < 0:
                lane_shape = ['Broken', 'Solid']
            else:
                lane_shape = ['Solid', 'Broken']
    else:
        lane_width = min_width
        double_line_interval = 0.1
        lane_shape = ['Broken']

    dash_interval = 0.5
    if 0 < max_width//dash_interval < dash_interval/2:
        dash_interval = max_width/(max_width//dash_interval)
    else:
        dash_interval = max_width/(max_width//dash_interval+1)

    newLine = LaneBoundary(points=np.array(new_line_point))
    edit_line.fill_in_points_evenly(newLine, 0.1)
    newLine.lane_shape = lane_shape
    newLine.lane_color = 'white'
    newLine.dash_interval_L1 = dash_interval
    newLine.dash_interval_L2 = dash_interval
    newLine.lane_width = lane_width
    newLine.double_line_interval = double_line_interval

    return newLine, min_width, max_width
        

class SelectExportLaneWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        widgetLayout = QGridLayout()

        label_main = QLabel(self)
        label_main.setText('Select the lane object to be exported')
        widgetLayout.addWidget(label_main, 0, 0)
        
        groupbox = QGroupBox('Lane Marking')
        vbox_lane = QVBoxLayout()
        self.normal_lane = QRadioButton('All Lane Marking', self)
        self.normal_lane.setChecked(True)
        self.stop_lane = QRadioButton('Stop Line Only', self)
        vbox_lane.addWidget(self.normal_lane)
        vbox_lane.addWidget(self.stop_lane)
        
        hbox = QHBoxLayout()
        label = QLabel(self)
        label.setText('Lanemarking Height')
        self.lane_height = QLineEdit(self)
        validator = QRegExpValidator(QRegExp(r'[0-9].+'))
        self.lane_height.setValidator(validator)
        self.lane_height.setText('0.0')
        hbox.addWidget(label)
        hbox.addWidget(self.lane_height)

        vbox_lane.addLayout(hbox)
        groupbox.setLayout(vbox_lane)
        widgetLayout.addWidget(groupbox, 1, 0)


        self.crosswalk = QCheckBox('Crosswalk', self)
        self.crosswalk.setChecked(True)
        vbox = QVBoxLayout()
        vbox.addWidget(self.crosswalk)
        widgetLayout.addLayout(vbox, 2, 0)
        

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        widgetLayout.addWidget(self.buttonbox, 3, 0)
        
        self.setLayout(widgetLayout)
        self.setWindowTitle('Export Lane')   

        # self.show()

    def showDialog(self):
        return super().exec_()
        
    def accept(self):
        self.done(1)

    def close(self):
        self.done(0)