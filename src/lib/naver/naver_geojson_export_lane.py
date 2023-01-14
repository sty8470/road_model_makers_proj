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
import lib.common.centroid as cent

from lib.naver.naver_geojson import *
from lib.naver.naver_load_geojson_lane import load_naver_lane


def export_lane(input_path):

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

    """
    출력 파일 Dict 만들기
    """
    output_file_name_prefix = ''
    output_file_name_suffix = '.csv'
    output_file_name_list = dict()
    type_name_list = list()
    type_names = ['A1LANE_CenterLine', 
                        'A1LANE_NormalLane', 
                        'A1LANE_MiscLane', 
                        'A1LANE_RoadEdge',
                        'A1LANE_SafeArea',
                        'A1LANE_Barrier',
                        'A2STOP_StopLine',
                        'A3LINK_DrivePath']

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

    node_file_name = next((item for item in map_info.keys() if 'NODE' in item), False)
    link_file_name = next((item for item in map_info.keys() if 'LINK' in item), False)
    lane_file_name = next((item for item in map_info.keys() if 'LANE' in item), False)
    stop_file_name = next((item for item in map_info.keys() if 'STOP' in item), False)

    origin = map_info[node_file_name]['features'][0]['geometry']['coordinates']
    a1_lane = map_info[lane_file_name]['features']
    a2_stop = map_info[stop_file_name]['features']
    a3_link = map_info[link_file_name]['features']


    for each_line in a1_lane:
        obj_prop = each_line['properties']

        lane_id = obj_prop['id']
        lane_type = obj_prop['lanecode']
        
        obj_geo = each_line['geometry']
        lane_points = obj_geo['coordinates']

        if lane_type == '1':
            key = 'A1LANE_CenterLine'
        elif lane_type == '3':
            key = 'A1LANE_NormalLane'
        elif lane_type == '7':
            key = 'A1LANE_RoadEdge'
        elif lane_type == '11':
            key = 'A1LANE_SafeArea'
        else:
            key = 'A1LANE_MiscLane'

        fileOpenMode = 'a'
        each_out = output_file_name_list[key]

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            # coord_obj가
            # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
            # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
            is_single_line = _is_single_line_obj(lane_points)
                
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = lane_points
                _write_single_line(writer, line, relative_loc, origin)

            else:
                print('[DEBUG] line type = {}, # of line = {}'.format(key, len(lane_points)))
                for line in lane_points:
                    _write_single_line(writer, line, relative_loc, origin)

    for each_line in a2_stop:
        obj_prop = each_line['properties']

        lane_id = obj_prop['id']
        
        obj_geo = each_line['geometry']
        lane_points = obj_geo['coordinates']
        key = 'A2STOP_StopLine'

        fileOpenMode = 'a'
        each_out = output_file_name_list[key]

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            # coord_obj가
            # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
            # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
            is_single_line = _is_single_line_obj(lane_points)
                
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = lane_points
                _write_single_line(writer, line, relative_loc, origin)

            else:
                print('[DEBUG] line type = {}, # of line = {}'.format(key, len(lane_points)))
                for line in lane_points:
                    _write_single_line(writer, line, relative_loc, origin)

    for each_line in a3_link:
        obj_prop = each_line['properties']

        lane_id = obj_prop['linkid']
        
        obj_geo = each_line['geometry']
        lane_points = obj_geo['coordinates']
        key = 'A3LINK_DrivePath'

        fileOpenMode = 'a'
        each_out = output_file_name_list[key]

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            # coord_obj가
            # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
            # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
            is_single_line = _is_single_line_obj(lane_points)
                
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = lane_points
                _write_single_line(writer, line, relative_loc, origin)

            else:
                print('[DEBUG] line type = {}, # of line = {}'.format(key, len(lane_points)))
                for line in lane_points:
                    _write_single_line(writer, line, relative_loc, origin)

    print('------------------ road_mesh END')

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

    if type(coord_obj[0][0]) is float:
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
                point_rel.append(point[i] - origin[i])

            csvwriter.writerow(point_rel)
            continue
        else:
            csvwriter.writerow(point)


def _node_set_link_set(c1_node, a3_link, origin):
    node_set = NodeSet()
    for item in c1_node:
        obj_prop = item['properties']

        coord_obj = np.array(item['geometry']['coordinates'])
        if coord_obj.shape != (3,):
            raise BaseException('[ERROR] @ create_node_set_and_link_set, coord_obj.shape is not (3,).')

        coord_obj -= origin

        node = Node(obj_prop['nodeid'])
        node.point = coord_obj
        node_set.nodes[node.idx] = node

    link_set = LineSet()

    for item in a3_link:
        obj_prop = item['properties']
        coord_obj = np.array(item['geometry']['coordinates'])
        coord_obj -= origin
        # 현재는 전부 바로 point가 init되는 Link를 생성
        link = Link(points=coord_obj, idx=obj_prop['linkid'], lazy_point_init=False, link_type=None)
        # 링크의 최대 속도, 최저 속도 설정 >> 최저 속도는 keys에 현재 없는 것 같아 조건문으로 처리함.
        if 'MaxSpeed' in obj_prop.keys():
            link.set_max_speed_kph(int(obj_prop['MaxSpeed']))
        if 'MinSpeed' in obj_prop.keys():
            link.set_min_speed_kph(int(obj_prop['MinSpeed']))

        error_link_from_node = False
        error_link_to_node = False

        # link의 끝점 또는 시작점이 FromNode, ToNode 시작점과 같은 위치에 있는지 
        # 판단할 때 사용하는 거리 기준값
        dist_threshold = 0.3 

        # FromNode를 찾을 수 없는 경우가 있으므로 이렇게 체크
        error_msg1 = '  ERROR  >> '  
        if obj_prop['fromnode'] in node_set.nodes:          
            from_node = node_set.nodes[obj_prop['fromnode']]

            # 노드가 있더라도, 우선 위치가 맞는지 검색해본다
            # NOTE: 가끔 z좌표가 이상한 경우가 있어, x,y 좌표만 거리 계산에 사용    
            point = link.points[0] # 링크의 시작점
            dist = np.linalg.norm(point[0:2] - from_node.point[0:2], ord=2)
            if dist > dist_threshold:
                error_msg1 += 'Incorrect FromNode = {} (distance = {:.2f} m)'.format(obj_prop['FromNodeID'], dist)
                error_link_from_node = True
            else:
                # 정상인 경우 -> from_node로 설정해준다
                link.set_from_node(from_node)
            
        else:
            error_msg1 += 'Cannot find FromNode = {}'.format(obj_prop['fromnode'])
            error_link_from_node = True

        # ToNode를 찾을 수 없는 경우가 있으므로 이렇게 체크
        error_msg2 = '  ERROR  >> '
        if obj_prop['tonode'] in node_set.nodes:
            to_node = node_set.nodes[obj_prop['tonode']]

            # 노드가 있더라도, 우선 위치가 맞는지 검색해본다
            # NOTE: 가끔 z좌표가 이상한 경우가 있어, x,y 좌표만 거리 계산에 사용    
            point = link.points[-1] # 링크의 끝점
            dist = np.linalg.norm(point[0:2] - to_node.point[0:2], ord=2)
            if dist > dist_threshold:
                error_msg2 += 'Incorrect ToNode = {} (distance = {:.2f} m)'.format(obj_prop['ToNodeID'], dist)
                error_link_to_node = True
            else:
                # 정상인 경우 -> to_node로 설정해준다
                link.set_to_node(to_node)
        else:
            error_msg2 += 'Cannot find ToNode = {}'.format(obj_prop['tonode'])
            error_link_to_node = True

        solved_msg1 = '  SOLVED >> '
        if error_link_from_node:
            find_result, node_idx = error_fix.search_for_a_from_node_and_set(link, node_set, from_node)
            if find_result:
                solved_msg1 += 'Connected to an existing node = {}'.format(node_idx)
            else:
                solved_msg1 += 'Created a new node = {}'.format(node_idx)

        solved_msg2 = '  SOLVED >> '
        if error_link_to_node:
            find_result, node_idx = error_fix.search_for_a_to_node_and_set(link, node_set, to_node)
            if find_result:
                solved_msg2 += 'Connected to an existing node = {}'.format(node_idx)
            else:
                solved_msg2 += 'Created a new node = {}'.format(node_idx)

        # 에러 발생한 경우 리포트
        if error_link_from_node or error_link_to_node:
            print('[ERROR in Link = {}]'.format(obj_prop['linkid']))
            if error_link_from_node:
                print(error_msg1)
                print(solved_msg1)
            if error_link_to_node:
                print(error_msg2)
                print(solved_msg2)

            print('----------------------------------')

        # [NOTE] ERROR 있는 링크 visualization 따로 할 경우 주석 해제
        if error_link_from_node or error_link_to_node:
            link.set_vis_mode_manual_appearance(1, 'r')
        else:
            link.set_vis_mode_manual_appearance(1, 'k')

        link_set.lines[link.idx] = link

    return node_set, link_set

    
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
    

    node_file_name = next((item for item in map_info.keys() if 'NODE' in item), False)
    link_file_name = next((item for item in map_info.keys() if 'LINK' in item), False)

    origin = map_info[node_file_name]['features'][0]['geometry']['coordinates']

    # node_set, link_set
    node_set, link_set = _node_set_link_set(map_info[node_file_name]['features'], map_info[link_file_name]['features'], origin)

    # SurfaceMark 정보가 포함된 시뮬레이터 프로젝트 내 Path
    asset_path_root = '/Assets/1_Module/Map/MapManagerModule/RoadObject/Models/'

    # csv 작성을 위한 리스트
    to_csv_list = []
    
    # 양보표시
    surfsign_pln = next((item for item in map_info.keys() if 'SURFSIGN_PLANE' in item), False)
    surfsign_dir = next((item for item in map_info.keys() if 'SURFSIGN_DIRECTION' in item), False)

    surface_pln = map_info[surfsign_pln]['features']
    surface_mark = map_info[surfsign_dir]['features']

    for each_obj in surface_mark:
        props = each_obj['properties']

        # Kind 값으로, 로드해야 할 모델명을 찾아준다
        kind = convert_type_sm_kind(props['signtype'])

        if kind == 'kind':
            continue
        result, file_path, file_name =\
            get_surface_marking_asset_path_and_name(kind, inspect_model_exists=True)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue
        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path

        """ 좌표 정보 찾기 """
        # 좌표 정보
        pos = each_obj['geometry']['coordinates']
        # pos를 구성하는 polygon은 [[[...], [...], [...], [...], [...]]] 이런 형태이어야 한다.
        # 즉, 선 1개로 구성된 polygon이어야 한다 
        assert len(pos) == 1, 'len(pos) must be 1. This polygon must be defined with multiple lines for this, which is unexpected.'

        # polygon을 구성하는 선 (점의 집합)을 np array로 만든다
        polygon_line = np.array(pos[0])
        polygon_line -= origin

        # simulator 좌표계로 변경
        pos = local_utm_to_sim_coord(polygon_line)
        centeroid = cent.calculate_centroid(polygon_line[0:-1])
        # centeroid = _calculate_centeroid_in_polygon(polygon_line[0:-1])
        pos = local_utm_to_sim_coord(centeroid)

        """ csv로 기록 """
        # 현재 포맷
        # FolderPath, PrefabName, InitPos, InitRot
        # 예시) Assets/Resources/Vehicle,KiaNiro.prefab,10.0/0.0/0.0,0.0/90.0/0.0
        position_string = '{}/{}/{}'.format(pos[0], pos[1], pos[2])
        orientation_string = '0.0/0.0/0.0'
        to_csv_list.append([file_path, file_name, position_string, orientation_string, each_obj['properties']['id']])

    for each_obj in surface_pln:
        props = each_obj['properties']

        # Kind 값으로, 로드해야 할 모델명을 찾아준다
        kind = props['signtype']
        if kind != '9':
            continue
        result, file_path, file_name =\
            get_surface_marking_asset_path_and_name(kind, inspect_model_exists=True)
            # get_surface_marking_asset_path_and_name('kind', inspect_model_exists=True)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue
        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path

        """ 좌표 정보 찾기 """
        # 좌표 정보
        pos = each_obj['geometry']['coordinates']
        # pos를 구성하는 polygon은 [[[...], [...], [...], [...], [...]]] 이런 형태이어야 한다.
        # 즉, 선 1개로 구성된 polygon이어야 한다 
        assert len(pos) == 1, 'len(pos) must be 1. This polygon must be defined with multiple lines for this, which is unexpected.'

        # polygon을 구성하는 선 (점의 집합)을 np array로 만든다
        polygon_line = np.array(pos[0])
        polygon_line -= origin

        # simulator 좌표계로 변경
        pos = local_utm_to_sim_coord(polygon_line)
        centeroid = cent.calculate_centroid(polygon_line[0:-1])
        # centeroid = _calculate_centeroid_in_polygon(polygon_line[0:-1])
        pos = local_utm_to_sim_coord(centeroid)

        """ csv로 기록 """
        # 현재 포맷
        # FolderPath, PrefabName, InitPos, InitRot
        # 예시) Assets/Resources/Vehicle,KiaNiro.prefab,10.0/0.0/0.0,0.0/90.0/0.0
        position_string = '{}/{}/{}'.format(pos[0], pos[1], pos[2])
        orientation_string = '0.0/0.0/0.0'
        to_csv_list.append([file_path, file_name, position_string, orientation_string, each_obj['properties']['id']])

    # 표지판 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'surface_marking_info.csv')

    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)

    print('--------------- surface_marking_info END')


def convert_type_sm_kind(signtype):
    # 101 > 5371 직진
    if signtype == '101':
        kind = '5371'
    # 102 > 5373 우회전
    elif signtype == '102':
        kind = '5373'
    # 103 > 5372 좌회전
    elif signtype == '103':
        kind = '5372'
    # 104 > 5382 직우회전
    elif signtype == '104':
        kind = '5382'
    # 105 > 5381 직좌회전
    elif signtype == '105':
        kind = '5381'
    # 106 > 5392 좌회전유턴
    elif signtype == '106':
        kind = '5392'
    # 107 > 5391 유턴
    elif signtype == '107':
        kind = '5391'
    # 108 > 5379 전체방향
    elif signtype == '108':
        kind = '5379'
    # 110 > 5383 직진유턴
    elif signtype == '110':
        kind = '5383'
    # 201 > 5431 좌합류
    elif signtype == '201':
        kind = '5431'
    # 202 > 5432 우합류
    elif signtype == '202':
        kind = '5432'
    else:
        kind = '599'
        
    return kind

def convert_type_cw_kind(signtype):
    # 1 > 524 정차금지대
    if signtype == '1':
        kind = '524'
    # 2 > ? 유도면
    # 3 > 544 오르막 경사면
    elif signtype == '3':
        kind = '544'
    # 4 > 5321 횡단보도
    elif signtype == '4':
        kind = '5321'
    # 5 > 533 고원식 횡단보도
    elif signtype == '5':
        kind = '533'
    # 6 > 534 자전거 횡단보도
    elif signtype == '6':
        kind = '534'
    # 7 > 과속방지턱
    elif signtype == '7':
        kind = '7'
    # 8> 직진좌회전가능/우회전불가능 화살표
    elif signtype == '8':
        kind = ''
    # 9 > 522 ▽ 이렇게 생긴거 (원형교차로 입구)잠시멈춤같은데 양보
    elif signtype == '9':
        kind = '522'
    # 90 > 지하차도
    elif signtype == '90':
        kind = ''
    # 97 > 주차장 혹은 건물
    elif signtype == '97':
        kind = '97'
    #98 > 속도제한 표시 ○(안에 숫자)
    elif signtype == '98':
        kind = '517'
    #99 > 노면글자표시(어린이 보호구역, BUS 등)
    elif signtype == '99':
        kind = '536'
    else:
        pass

    return kind


def export_crosswalk(input_path):

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
    
    node_file_name = next((item for item in map_info.keys() if 'NODE' in item), False)
    link_file_name = next((item for item in map_info.keys() if 'LINK' in item), False)

    origin = map_info[node_file_name]['features'][0]['geometry']['coordinates']

    surfsign_pln = next((item for item in map_info.keys() if 'SURFSIGN_PLANE' in item), False)

    cw_set = CrossWalkSet()
    surface_plane = map_info[surfsign_pln]['features']
    for each_obj in surface_plane:
        props = each_obj['properties']
        geo = each_obj['geometry']
        cw_id = props['id']
        points = np.array(geo['coordinates'])
        points -= origin
        cw = CrossWalk(points=points, idx=cw_id)
        cw.type_code_def = 'NGII_SHP2'
        cw.type = convert_type_cw_kind(props['signtype'])
        cw_set.append_data(cw)

    """포인트 내부를 수정"""
    point_interval = 0.1
    for obj in cw_set.data.values():
        obj.fill_in_points_evenly(step_len=point_interval)

    vertex_face_sets = dict()

    """ Crosswalk 데이터에 대한 작업 """
    for idx, obj in cw_set.data.items():
        if obj.type == '5321':
            file_name = 'crosswalk_pedestrian'
        elif obj.type == '534':
            file_name = 'crosswalk_bike'
        elif obj.type == '533':
            file_name = 'crosswalk_plateau_pedestrian'
        # elif obj.type == '522':
        #     file_name = 'yield_sign'
        elif obj.type == '7':
            file_name = 'speedbump'
        elif obj.type == '97':
            file_name = 'parking_lot'
        elif obj.type == '98':
            file_name = 'speed_symbol'
        else:
            # 우선 횡단보도가 아닌 대상은 우선 mesh 생성에서 제외한다.
            print('[WARNING] cw: {} skipped (currently not suppored type)'.format(idx))
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

    for file_name, vertex_face in vertex_face_sets.items():
        print('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
        file_name = os.path.normpath(os.path.join(output_path, file_name))  

        mesh_gen_vertices = vertex_face['vertex']
        mesh_gen_vertex_subsets_for_each_face = vertex_face['face']

        poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face)
        write_obj(poly_obj, file_name)

    print('--------------- crosswalk & speedbump END')


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


if __name__ == u'__main__':
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\naverlabs_pangyo'
    
    # export_lane(input_path) 
    # export_surfacemark(input_path)
    export_crosswalk(input_path)
    
