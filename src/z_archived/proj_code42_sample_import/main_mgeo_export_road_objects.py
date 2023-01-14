#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로

from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt

from lib_ngii_shp_ver2.shp_edit_funcs import *
from lib.mgeo.class_defs import *
from lib.mgeo.utils import utils
import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save
import lib.mgeo.utils.error_fix as mgeo_error_fix
import lib.mgeo.utils.lane_change_link_creation as mgeo_lane_ch_link_gen

from code42_geojson import * 
import csv


def local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])


def _get_traffic_light_asset_path_and_name():
    pass


# TODO(sglee): Refactor this! Polygon 인 Surface Marking의 Point를 계산하는데 사용되는 함수 
def _calculate_centeroid_in_polygon(point_list):
    '''
    polygon을 구성하는 점들로부터 centeroid를 계산한다.
    밀도가 균일하다면 center of mass와 동일하며,
    이 점은 각 좌표의 산술 평균이다.
    '''
    x = point_list[:,0]
    y = point_list[:,1]
    z = point_list[:,2]

    return np.array([np.mean(x), np.mean(y), np.mean(z)])


# TODO(sglee): Refactor this! Polygon 인 Surface Marking의 Point를 계산하는데 사용되는 함수 
def _find_nearest_node_in_link(ref_point, link_points, distance_using_xy_only, dist_threshold=10):
    '''
    link_points 내부의 많은 점들 가운데서, ref_point와 가장 가까운 point를 찾아준다
    '''
    # 가장 가까운 노드와, 노드까지의 거리를 찾는다
    min_dist = np.inf
    nearest_point = None

    for point in link_points:       
        if distance_using_xy_only:
            pos_vect = point[0:2] - ref_point[0:2]
        else:
            pos_vect = point - ref_point
        
        dist = np.linalg.norm(pos_vect, ord=2)
        if dist < min_dist:
            min_dist = dist
            nearest_point = point
    
    # 가장 가까운 노드까지의 거리가 정한 값보다 작으면, 적합한 노드가 있는 것이다
    if min_dist < dist_threshold:
        return True, nearest_point
    else:
        return False, None


def convert_code42_geojson_to_mgeo_road_objects():
    '''
    CODE42의 GeoJSON 데이터에서 mgeo Node & Link를 생성하고 저장한다
    '''
    input_path = '../../rsc/map_data/geojson_Code42_Sample/toGwacheonSample'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  

    init_dir = '../../saved/road_objs/CODE42_과천'
    init_dir = os.path.join(current_path, init_dir)
    init_dir = os.path.normpath(init_dir)  

    # 저장할 경로
    output_path = filedialog.askdirectory(
        initialdir = init_dir, 
        title = 'Save in the folder below') # defaultextension = 'json') 과 같은거 사용 가능   

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)


    """ 파일 읽어오기 """
    map_info = read_geojson_files(input_path)
    
    origin = get_origin(map_info)
    origin = np.array(origin)
    print('[INFO] Origin Set as: ', origin)


    """ 우선 Node, Link를 로드해야 한다 (링크의 최고 속도 등 부가적인 정보를 찾기 위함) """
    node_set, link_set = create_node_set_and_link_set(map_info, origin)


    """ [STEP #1] 표지판 정보 """ 
    # 표지판 정보가 포함된 시뮬레이터 프로젝트 내 Path
    asset_path_root = 'Assets/0_Master/3_Prefabs/RoadObjects/'
    
    # csv 작성을 위한 리스트
    to_csv_list = []

    # 각 표지판에 대한 배치 정보 등을 출력
    for i in range(len(map_info['B1_SAFETYSIGN']['features'])):
        
        each_obj =  map_info['B1_SAFETYSIGN']['features'][i]

        """ DBF-like 정보 -> model 파일명 찾기 """
        # DBF-like 정보
        props = each_obj['properties']

        # 연결된 링크
        if props['LinkID'] not in link_set.lines.keys():
            print('[WARNING] Cannot find LinkID={} in the link_set for B1_SAFETYSIGN={}'.format(props['LinkID'], props['ID']))
            related_link = None
        else:
            related_link = link_set.lines[props['LinkID']]
        

        # Type, SubType을 
        result, file_path, file_name =\
            get_traffic_sign_asset_path_and_name(props['Type'], props['SubType'], link=related_link)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path
        
        """ 좌표 정보 찾기 """
        # 좌표 정보
        pos = each_obj['geometry']['coordinates']
        pos = np.array(pos)

        # relative pos로 변경
        pos = pos -  origin

        # simulator 좌표계로 변경
        pos = local_utm_to_sim_coord(pos)
       

        """ csv로 기록 """
        # 현재 포맷
        # FolderPath, PrefabName, InitPos, InitRot
        # 예시) Assets/Resources/Vehicle,KiaNiro.prefab,10.0/0.0/0.0,0.0/90.0/0.0
        position_string = '{}/{}/{}'.format(pos[0], pos[1], pos[2])
        orientation_string = '0.0/0.0/0.0'
        to_csv_list.append([file_path, file_name, position_string, orientation_string])

    # 표지판 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'traffic_sign_info.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


    """ [STEP #2] 노면표시 정보 """
    # 노면표시 정보가 포함된 시뮬레이터 프로젝트 내 Path
    asset_path_root = 'Assets/0_Master/3_Prefabs/RoadObjects/'

    # csv 작성을 위한 리스트
    to_csv_list = []

    # 각 노면 표시 배치 정보 등을 출력
    for i in range(len(map_info['B3_SURFACEMARK']['features'])):
        each_obj = map_info['B3_SURFACEMARK']['features'][i]

        """ DBF-like 정보 -> model 파일명 찾기 """
        # DBF-like 정보
        props = each_obj['properties']

        # 연결된 링크
        if props['LinkID'] not in link_set.lines.keys():
            print('[WARNING] Cannot find LinkID={} in the link_set for B1_SAFETYSIGN={}'.format(props['LinkID'], props['ID']))
            related_link = None
        else:
            related_link = link_set.lines[props['LinkID']]

        # 일부 SURFACEMARK에서 횡단보도(5321)는 따로 관리, Skip 한다
        if int(props['Kind']) in [5321]:
            continue 

        # Kind 값으로, 로드해야 할 모델명을 찾아준다
        result, file_path, file_name =\
            get_surface_marking_asset_path_and_name(props['Kind'], inspect_model_exists=True)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path
        

        """ 좌표 정보 찾기 """
        # B3_SURFACEMARK는 Polygon이다
        assert each_obj['geometry']['type'] == 'Polygon'
        
        # 좌표 정보
        pos = each_obj['geometry']['coordinates']

        # pos를 구성하는 polygon은 [[[...], [...], [...], [...], [...]]] 이런 형태이어야 한다.
        # 즉, 선 1개로 구성된 polygon이어야 한다 
        assert len(pos) == 1, 'len(pos) must be 1. This polygon must be defined with multiple lines for this, which is unexpected.'

        # polygon을 구성하는 선 (점의 집합)을 np array로 만든다
        polygon_line = np.array(pos[0])

        # relative pos로 변경
        polygon_line -= origin 
        
        # 마지막 점을 제외하고, center of mass를 구한다.
        # 마지막 점을 제외하는 이유: 첫번째 점과 같은 점이다.
        centeroid = _calculate_centeroid_in_polygon(polygon_line[0:-1])

        """ 디버깅용, 남겨둘 것 >> centeroid 를 link로 snap 시켜보려고 했는데, 결과적으로 좋지 않았음. 
        link의 점이 불균일한 것도 이유가 되긴하는데, 어차피 손이 가야할 부분이라, centeroid를 그대로 사용하는 것이 나아보임 """
        # # 그런데, plot으로 보면, 실제 이 도형의 중심은 아닐 것 같은 경우들이 있다.
        # # 왜냐하면, 점이 균일하게 찍혀있지 않기 때문이다.
        # # 따라서, centeroid를 link로 snap 시키는 것이 나을 것 같다.
        # snap_result, snapped_centeroid =\
        #     _find_nearest_node_in_link(centeroid, related_link.points, True, dist_threshold=100)
        # # assert snap_result, '[ERROR] snap_failed!'
        # if snap_result:

        #     plt.figure()
        #     plt.plot(polygon_line[:,0], polygon_line[:,1], 'b-o')
        #     plt.plot(centeroid[0], centeroid[1], 'ro')
            
        #     link_set.draw_plot(plt.gca())
        #     plt.plot(related_link.points[:,0], related_link.points[:,1], 'g-x')
        #     plt.plot(snapped_centeroid[0], snapped_centeroid[1], 'ko', markersize=5)
        #     plt.axis('equal')
        #     plt.show()

        # else:
        #     print('[WARNING] snap_failed!!!')

        #     plt.figure()
        #     plt.plot(polygon_line[:,0], polygon_line[:,1], 'b-o')
        #     plt.plot(centeroid[0], centeroid[1], 'ro')
            
        #     link_set.draw_plot(plt.gca())
        #     plt.plot(related_link.points[:,0], related_link.points[:,1], 'g-x')
        #     plt.axis('equal')
        #     plt.show()

        # simulator 좌표계로 변경
        pos = local_utm_to_sim_coord(centeroid)


        """ csv로 기록 """
        # 현재 포맷
        # FolderPath, PrefabName, InitPos, InitRot
        # 예시) Assets/Resources/Vehicle,KiaNiro.prefab,10.0/0.0/0.0,0.0/90.0/0.0
        position_string = '{}/{}/{}'.format(pos[0], pos[1], pos[2])
        orientation_string = '0.0/0.0/0.0'
        to_csv_list.append([file_path, file_name, position_string, orientation_string])


    # 표지판 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'surface_marking_info.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


    """ [STEP3] 신호등 정보 """
    # 노면표시 정보가 포함된 시뮬레이터 프로젝트 내 Path
    asset_path_root = 'Assets/0_Master/3_Prefabs/RoadObjects/'

    # csv 작성을 위한 리스트
    to_csv_list = []

    # 신호등 정보
    for i in range(len(map_info['C1_TRAFFICLIGHT']['features'])):
        each_obj = map_info['C1_TRAFFICLIGHT']['features'][i]
    
        """ DBF-like 정보 -> model 파일명 찾기 """
        # DBF-like 정보
        props = each_obj['properties']
       
        # NOTE: 현재 모든 정보가 None으로 되어있다.
        assert props['Type'] is None, '[ERROR] If type is not None, a proper traffic light model needs to be defined'

        file_path = 'KR_TrafficSign'
        file_name = 'TLight_Hor_RYLgG.prefab'

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path


        """ 좌표 정보 찾기 """
        # 좌표 정보
        pos = each_obj['geometry']['coordinates']
        pos = np.array(pos)

        # relative pos로 변경
        pos = pos -  origin

        # simulator 좌표계로 변경
        pos = local_utm_to_sim_coord(pos)


        """ csv로 기록 """
        # 현재 포맷
        # FolderPath, PrefabName, InitPos, InitRot
        # 예시) Assets/Resources/Vehicle,KiaNiro.prefab,10.0/0.0/0.0,0.0/90.0/0.0
        position_string = '{}/{}/{}'.format(pos[0], pos[1], pos[2])
        orientation_string = '0.0/0.0/0.0'
        to_csv_list.append([file_path, file_name, position_string, orientation_string])


    # 신호등 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'traffic_light_info.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


    print('END')



if __name__ == u'__main__':
    """ CODE42의 원본 데이터를 불러와서 편집하고 저장하는 모드""" 
    convert_code42_geojson_to_mgeo_road_objects()

    """ 위에서 저장한 Node, Link를 확인하기 위한 모드 """
    # start_from_empty_link()