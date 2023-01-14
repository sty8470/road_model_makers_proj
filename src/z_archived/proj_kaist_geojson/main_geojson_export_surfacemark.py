import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')

import json
import csv
import numpy as np

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.stryx.stryx_load_geojson_lane import *
from lib.stryx.stryx_geojson import *

def export_surfacemark(input_path):

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

    """ 우선 Node, Link를 로드해야 한다 (링크의 최고 속도 등 부가적인 정보를 찾기 위함) """
    node_set, link_set = create_node_set_and_link_set(map_info['A1_NODE']['features'], map_info['A2_LINK']['features'], origin)

    """ [STEP #1] 표지판 정보 """ 
    # 표지판 정보가 포함된 시뮬레이터 프로젝트 내 Path
    asset_path_root = '/Assets/1_Module/Map/MapManagerModule/RoadObject/Models/'

    # csv 작성을 위한 리스트
    to_csv_list = []

    surface_mark = map_info['B3_SURFACEMARK']['features']

    # 각 표지판에 대한 배치 정보 등을 출력
    for each_obj in surface_mark:
        """ DBF-like 정보 -> model 파일명 찾기 """
        # DBF-like 정보
        props = each_obj['properties']

        # # 연결된 링크
        # if props['LinkID'] not in link_set.lines.keys():
        #     print('[WARNING] Cannot find LinkID={} in the link_set for B1_SAFETYSIGN={}'.format(props['LinkID'], props['id']))
        #     related_link = None
        # else:
        #     related_link = link_set.lines[props['LinkID']]

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
        assert each_obj['geometry']['type'] == 'Point'

        # 좌표 정보
        pos = each_obj['geometry']['coordinates']

        # pos를 구성하는 polygon은 [[[...], [...], [...], [...], [...]]] 이런 형태이어야 한다.
        # 즉, 선 1개로 구성된 polygon이어야 한다 
        # assert len(pos) == 1, 'len(pos) must be 1. This polygon must be defined with multiple lines for this, which is unexpected.'

        # polygon을 구성하는 선 (점의 집합)을 np array로 만든다
        # polygon_line = np.array(pos[0])
        # kaist 데이터는 점데이터라 생략

        polygon_point = np.array(pos)

        # relative pos로 변경
        polygon_point -= origin 
        
        # 마지막 점을 제외하고, center of mass를 구한다.
        # 마지막 점을 제외하는 이유: 첫번째 점과 같은 점이다.
        # centeroid = _calculate_centeroid_in_polygon(polygon_point[0:-1])

        # simulator 좌표계로 변경
        pos = local_utm_to_sim_coord(polygon_point)


        """ csv로 기록 """
        # 현재 포맷
        # FolderPath, PrefabName, InitPos, InitRot
        # 예시) Assets/Resources/Vehicle,KiaNiro.prefab,10.0/0.0/0.0,0.0/90.0/0.0
        position_string = '{}/{}/{}'.format(pos[0], pos[1], pos[2])
        orientation_string = '0.0/0.0/0.0'
        to_csv_list.append([file_path, file_name, position_string, orientation_string, props['id']])


    # 표지판 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'surface_marking_info.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


if __name__ == u'__main__': 
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201203_KAIST_3rd'
    export_surfacemark(input_path)