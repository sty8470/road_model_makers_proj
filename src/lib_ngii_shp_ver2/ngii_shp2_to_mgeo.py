#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from lib.mgeo.utils import logger
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로
sys.path.append(current_path + '/../lib/common') # 프로젝트 Root 경로

import numpy as np

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_signal
import shp_common

# overlapped node 제거
from lib.mgeo.utils.error_fix import search_overlapped_node, repair_overlapped_node
from lib.mgeo.edit.funcs import edit_node


from lib.common.polygon_util import minimum_bounding_rectangle, calculate_centroid

key_L_LINKID = 'L_LinkID'
key_R_LINKID = 'R_LinkID'


def import_all_data(input_path, enable_offset=True, origin_node_id=None):
    map_info = shp_common.read_shp_files(input_path, encoding_ansi=True)[0]

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 A1_NODE에서 검색되는 첫번째 포인트로한다
    """

    # 이제 여기서 NODE, LINK 파일을 읽어준다.
    shp_node = map_info['A1_NODE']
    shp_link = map_info['A2_LINK']
    shp_ts = map_info['B1_SAFETYSIGN']
    shp_tl = map_info['C1_TRAFFICLIGHT']
    shp_sm = map_info['B3_SURFACEMARK']
    shp_sb = None
    if 'C4_SPEEDBUMP' in map_info:
        shp_sb = map_info['C4_SPEEDBUMP']

    if enable_offset:
        if origin_node_id is not None:
            # 아이디 지정해서 origin으로 넣고 싶을 때
            origin_id = next((i for i, item in enumerate(shp_node.records()) if item['ID'] == origin_node_id), None)
            shapes = shp_node.shapes()
            origin_e = shapes[origin_id].points[0][0]
            origin_n = shapes[origin_id].points[0][1]
            origin_z = shapes[origin_id].z[0]
            origin = np.array([origin_e, origin_n, origin_z])
        else:
            origin = shp_common.get_first_shp_point(map_info['A1_NODE'])
            origin = np.array(origin)
        
        print('[INFO] Origin =', origin)
    else:
        origin = np.array(0, 0, 0)

    # Node, 일반 Link
    node_set, junction_set = __create_node_and_junction_set(shp_node, origin)
    link_set = __create_link_set(shp_link, origin, node_set)
    
    # TS, TL 생성
    ts_set = __create_traffic_sign_set_from_shp(shp_ts, origin, link_set)
    tl_set = __create_traffic_light_set_from_shp(shp_tl, origin, link_set)

    # SM 생성
    sm_set = __create_surface_marking_set_from_shp(shp_sm, shp_sb, origin, link_set)
    
    cw_set = __create_crosswalk_set_from_shp(shp_sm, origin, link_set)

    # MGeo Planner Map 생성
    mgeo_planner_map = MGeo(
        node_set = node_set, link_set = link_set, junction_set = junction_set,
        sign_set = ts_set, light_set = tl_set, sm_set = sm_set, scw_set = cw_set)

    # NOTE: 모든 prj 파일은 같다고 가정하여, 하나만 읽는다.
    prj_file = os.path.normpath(os.path.join(input_path, 'A1_NODE.prj'))
    mgeo_planner_map.set_coordinate_system_from_prj_file(prj_file)

    mgeo_planner_map.set_origin(origin)

    return mgeo_planner_map


def __create_node_and_junction_set(sf, origin):
    node_set = NodeSet()
    junction_set = JunctionSet()
    
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')
    
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        # node로 추가
        node = Node(dbf_rec['ID'])
        node.point = shp_rec.points[0]
        node.node_type = dbf_rec['NodeType']
        its_id = dbf_rec['ITSNodeID']

        # junction 존재 여부 판단 및 추가
        if its_id is not '':
            if its_id in junction_set.junctions.keys():
                # junction exists in set
                junction_set.junctions[its_id].add_jc_node(node)
            else:
                # junction is completely new
                junction = Junction(its_id)
                junction.add_jc_node(node)

                junction_set.append_junction(junction)

        # node를 node_set에 포함
        node_set.nodes[node.idx] = node

    return node_set, junction_set


def __create_link_set(sf, origin, node_set):
    line_set = LineSet()

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')


    # [파일 내부 오류로 인한 체크]
    # dbf 파일 내부 L_LinkID 또는 R_LinkID에 오타가 있는 경우가 있다
    # 때문에 L_LinkID, R_LinkID라고 생각되는 필드 이름을 검색해서 찾아준다
    global key_L_LINKID, key_R_LINKID
    
    for i in range(len(sf.fields)):
        each_field_def = sf.fields[i]
        field_name = each_field_def[0]
        if field_name in ['L_LinkID', 'L_LinKID']: # 필드 이름이 이 리스트에 있는 것 중 하나면 적합한 필드라고 간주한다
            key_L_LINKID = field_name
            break

        if i == len(sf.fields):
            # field_name 이 생각한 옵션에 걸렸으면, 이 부분이 실행이 안 된다
            # 이 부분이 실행이 된다는 것은 결국 Left Link ID로 생각되는 필드가 없다는 것
            raise BaseException('Cannot find dbf key for Left Link ID')
    
    for i in range(len(sf.fields)):
        each_field_def = sf.fields[i]
        field_name = each_field_def[0]
        if field_name in ['R_LinkID', 'R_LinKID']: # 필드 이름이 이 리스트에 있는 것 중 하나면 적합한 필드라고 간주한다
            key_R_LINKID = field_name
            break
        
        if i == len(sf.fields):
            # field_name 이 생각한 옵션에 걸렸으면, 이 부분이 실행이 안 된다
            # 이 부분이 실행이 된다는 것은 결국 Left Link ID로 생각되는 필드가 없다는 것
            raise BaseException('Cannot find dbf key for Right Link ID')
        
    # 우선 링크셋을 만든다
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        # shp_rec.points -= origin

        line_points = list()
        for k in range(len(shp_rec.points)):
            e = shp_rec.points[k][0] - origin[0]
            n = shp_rec.points[k][1] - origin[1]
            z = shp_rec.z[k] - origin[2]

            line_points.append([e,n,z])

        shp_rec.points = np.array(line_points)


        # 현재는 전부 바로 point가 init되는 Link를 생성
        link_id = dbf_rec['ID']
        link = Link(points=shp_rec.points, idx=link_id, lazy_point_init=False)
    
        if dbf_rec['FromNodeID'] not in node_set.nodes.keys():           
            # FromNodeID에 해당하는 노드가 없는 경우이다.
            # 새로운 노드를 생성해서 해결
            idx = dbf_rec['FromNodeID']
            print('[WARN] FromNode (id={}) does not exist. (for Link id={}) Thus one is automatically created.'.format(idx, link_id))            
            node = Node(idx)
            node.point = shp_rec.points[0] 
            node_set.append_node(node)
            from_node = node
        else:
            from_node = node_set.nodes[dbf_rec['FromNodeID']]

        if dbf_rec['ToNodeID'] not in node_set.nodes.keys():
            # ToNodeID에 해당하는 노드가 없는 경우이다.
            # 새로운 노드를 생성해서 해결
            idx = dbf_rec['ToNodeID']
            print('[WARN] ToNode (id={}) does not exist. (for Link id={})  Thus one is automatically created.'.format(idx, link_id))            
            node = Node(idx)
            node.point = shp_rec.points[0] 
            node_set.append_node(node)
            to_node = node
        else:
            to_node = node_set.nodes[dbf_rec['ToNodeID']]

        link.set_from_node(from_node)
        link.set_to_node(to_node)
        
        link.road_type = dbf_rec['RoadType']
        link.road_id = dbf_rec['SectionID']
        
        # 차선 변경 여부를 결정하는데 사용한다
        # 1: 교차로내 주행경로, 2 & 3: 톨게이트차로(하이패스, 비하이패스)
        link.link_type = dbf_rec['LinkType']
        if link.link_type == '1':
            link.from_node.on_stop_line = True
            link.related_signal = 'straight'
            if dbf_rec['LaneNo'] > 90:
                link.related_signal = 'left'

        # Max Speed 추가
        try:
            link.set_max_speed_kph(dbf_rec['MaxSpeed'])
        except:
            link.set_max_speed_kph(0)

        # ego_lane 추가
        link.ego_lane = dbf_rec['LaneNo']
        # link_type_def 추가
        link.link_type_def = 'ngii_model2'
        # link_set에 추가
        line_set.lines[link.idx] = link


    # 차선 변경을 위해, 좌/우에 존재하는 링크에 대한 Reference를 추가한다
    # 단, 좌/우에 존재하는 링크라고해서 반드시 차선 변경이 가능한 것은 아니다
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        link = line_set.lines[dbf_rec['ID']]

        # 양옆 차선 속성도 dbf 데이터로부터 획득
        if dbf_rec[key_R_LINKID] is not '': # NOTE: 일부 파일에는 소문자 k에 오타가 있어 R_LinKID로 조회해야할 수 있다. 
            lane_ch_link_right = line_set.lines[dbf_rec[key_R_LINKID]] # NOTE: 일부 파일에는 소문자 k에 오타가 있어 R_LinKID로 조회해야할 수 있다. 
            link.lane_ch_link_right = lane_ch_link_right
            link.can_move_right_lane = True

        if dbf_rec[key_L_LINKID] is not '': # NOTE: 일부 파일에는 소문자 k에 오타가 있어 L_LinKID로 조회해야할 수 있다. 
            lane_ch_link_left = line_set.lines[dbf_rec[key_L_LINKID]] # NOTE: 일부 파일에는 소문자 k에 오타가 있어 L_LinKID로 조회해야할 수 있다. 
            link.lane_ch_link_left = lane_ch_link_left
            link.can_move_left_lane = True

    return line_set 


def __create_traffic_sign_set_from_shp(sf, origin, link_set):   
    traffic_sign_set = SignalSet()

    shapes = sf.shapes()
    records  = sf.records()

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')
    
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        # id 관련 변수는 전부 string으로 처리
        signal_id = to_str_if_int(dbf_rec['ID'])
        link_id_list = [to_str_if_int(dbf_rec['LinkID'])]

        signal = Signal(signal_id)
        signal.link_id_list = link_id_list

        # if dbf_rec['LinkID']:
        #     signal.link_id_list = dbf_rec['LinkID'].split(',') 

        signal.dynamic = False
        signal.orientation = '+'
        signal.country = 'KR'

        # LINK ID List를 사용해서 Link 참조 List 구성     
        for link_id in signal.link_id_list:
            if link_id in link_set.lines.keys():
                link = link_set.lines[link_id]
                signal.add_link_ref(link)
            else:
                print('[ERROR] Cannot find Link (id={}) for TS (id={}) Skipping this one'.format(link_id, signal_id))
                # raise BaseException('[ERROR] Could not find link ID mapped in link set.')
    
        for link in signal.link_list:
            # class A
            # Aobj1, Aobj2
            # Aobj1 == Aobj2 >> True
            # Aobj1 is Aobj2 >> False
            if signal.road_id is None :
                signal.road_id = link.road_id
            else:
                pass
                # Signal이 참조하고 있는 lane들이 서로 다른 road id를 가진 경우 예외 발생
                # if signal.road_id != link.road_id:
                #     raise BaseException('[ERROR] The lanes referenced by signal have different road id.')

        signal.type = dbf_rec['Type']
        try:
            signal.sub_type = dbf_rec['SubType']
        except:
            signal.sub_type = None

        # 사이즈 설정
        # type, sub_type 값을 설정한 후 호출해야 함
        signal.set_size()

        # 최고속도제한 규제표지
        if signal.type == 2 and signal.sub_type == 224 and signal.link_list.__len__ > 0  :
            signal.value = signal.link_list[signal.link_id_list[0]].max_speed_kph
        # 최저속도제한 규제표지
        elif signal.type == 2 and signal.sub_type == 225 and signal.link_list.__len__ > 0 :
            signal.value = signal.link_list[signal.link_id_list[0]].min_speed_kph
            
        signal.point = shp_rec.points[0]
        signal.type_def = 'ngii_model2'
        traffic_sign_set.signals[signal.idx] = signal
    
    return traffic_sign_set


def __create_traffic_light_set_from_shp(sf, origin, link_set):
    traffic_light_set = SignalSet()

    shapes = sf.shapes()
    records  = sf.records()

    if len(shapes) != len(records) :
        raise BaseException('[ERROR] len(shapes) != len(records)')
    
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        # id 관련 변수는 전부 string으로 처리
        signal_id = to_str_if_int(dbf_rec['ID'])
        link_id_list = [to_str_if_int(dbf_rec['LinkID'])]

        signal = Signal(signal_id)
        signal.link_id_list = link_id_list
        signal.type_def = 'ngii_model2'

        # if dbf_rec['LinkID'] :
        #     signal.link_id_list = dbf_rec['LinkID'].split(',') 

        signal.dynamic = True
        signal.orientation = '+'
        signal.country = 'KR'

        # LINK ID List를 사용해서 Link 참조 List 구성
        for link_id in signal.link_id_list:
            if link_id in link_set.lines.keys():
                link = link_set.lines[link_id]
                signal.add_link_ref(link)
            else:
                print('[ERROR] Cannot find Link (id={}) for TL (id={}) Skipping this one'.format(link_id, signal_id))

        for link in signal.link_list:
            if signal.road_id is None or signal.road_id == '':
                signal.road_id = link.road_id
            else:
                # Signal이 참조하고 있는 lane들이 서로 다른 road id를 가진 경우 예외 발생
                if signal.road_id != link.road_id :
                    raise BaseException('[ERROR] The lanes referenced by signal have different road id.')             

        signal.type = dbf_rec['Type']
        if int(signal.type) == 99:
            if '이색등' in dbf_rec['Remark']:
                signal.type = '10'
        signal.sub_type = ''
        signal.type_def = 'ngii_model2'

        # 사이즈 설정
        # type, sub_type 값을 설정한 후 호출해야 함
        signal.set_size()

        signal.point = shp_rec.points[0]
        edit_signal.ToMgeo_210311(signal)
        
        traffic_light_set.signals[signal.idx] = signal
    
    return traffic_light_set        


def __create_surface_marking_set_from_shp(shp_sm, shp_sb, origin, link_set):
    sm_set = SurfaceMarkingSet()

    shapes = shp_sm.shapes()
    records  = shp_sm.records()

    if len(shapes) != len(records) :
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]
    
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        sm_id = to_str_if_int(dbf_rec['ID'])
        link_id_list = [to_str_if_int(dbf_rec['LinkID'])]

        sm = SurfaceMarking(points=shp_rec.points, idx=sm_id)
        sm.link_id_list = link_id_list

        # LINK ID List를 사용해서 Link 참조 List 구성
        for link_id in sm.link_id_list:
            if link_id in link_set.lines.keys():
                link = link_set.lines[link_id]
                sm.add_link_ref(link)
            else:
                print('[ERROR] Cannot find Link (id={}) for SM (id={}) Skipping this one'.format(link_id, sm_id))

        sm.type = dbf_rec['Type']
        sm.sub_type = dbf_rec['Kind']

        # surface marking set에 추가
        sm_set.append_data(sm, create_new_key=False)
    if shp_sb is not None:
        
        shapes = shp_sb.shapes()
        records  = shp_sb.records()

        if len(shapes) != len(records) :
            raise BaseException('[ERROR] len(shapes) != len(records)')

        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]
        
            # Convert to numpy array
            shp_rec.points = np.array(shp_rec.points)
            shp_rec.z = np.array(shp_rec.z)

            # Point에 z축 값도 그냥 붙여버리자
            shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

            # origin 무조건 전달, 상대좌표로 변경
            shp_rec.points -= origin
            points = np.array(minimum_bounding_rectangle(shp_rec.points))
            points = np.vstack((points, points[0]))
            shp_rec.points = points

            sm_id = to_str_if_int(dbf_rec['ID'])
            link_id_list = [to_str_if_int(dbf_rec['LinkID'])]

            sm = SurfaceMarking(points=shp_rec.points, idx=sm_id)
            sm.link_id_list = link_id_list

            # LINK ID List를 사용해서 Link 참조 List 구성
            for link_id in sm.link_id_list:
                if link_id in link_set.lines.keys():
                    link = link_set.lines[link_id]
                    sm.add_link_ref(link)
                else:
                    print('[ERROR] Cannot find Link (id={}) for SM (id={}) Skipping this one'.format(link_id, sm_id))

            sm.type = dbf_rec['Type']
            sm.sub_type = 'speedbump'

            # surface marking set에 추가
            sm_set.append_data(sm, create_new_key=False)
            
    return sm_set

def __create_crosswalk_set_from_shp(sf, origin, link_set):
    cw_set = SingleCrosswalkSet()

    shapes = sf.shapes()
    records  = sf.records()

    if len(shapes) != len(records) :
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]
    
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        points = np.array(minimum_bounding_rectangle(shp_rec.points))
        points = np.vstack((points, points[0]))
        shp_rec.points = points

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        cw_id = to_str_if_int(dbf_rec['ID'])
        link_id_list = [to_str_if_int(dbf_rec['LinkID'])]
        sm_type =  to_str_if_int(dbf_rec['Type'])
        
        if sm_type == '5':
            cw = SingleCrosswalk(points=shp_rec.points, idx=cw_id)
            cw.sign_type = dbf_rec['Kind']
            cw.type_code_def = 'ngii_model2'
            cw.link_id_list = link_id_list
            cw_set.append_data(cw, create_new_key=False)
    return cw_set


def to_str_if_int(val):
    # list인 경우 먼저 체크
    if isinstance(val, list):
        ret_list = list()
        for each_val in val:
            if isinstance(each_val, int):
                ret_list.append(str(each_val))
            else:
                ret_list.append(each_val)
        return ret_list

    # 단일 값인 경우
    if isinstance(val, int):
        return str(val)
    else:
        return val

def import_lane_marking_data(input_path, enable_offset=True, origin_node_id=None):
    map_info = shp_common.read_shp_files(input_path, encoding_ansi=True)[0]

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 A1_NODE에서 검색되는 첫번째 포인트로한다
    """

    # 이제 여기서 NODE, LINK 파일을 읽어준다.
    shp_node = map_info['A1_NODE']
    shp_link = map_info['A2_LINK']
    shp_ts = map_info['B1_SAFETYSIGN']
    shp_tl = map_info['C1_TRAFFICLIGHT']
    shp_sm = map_info['B3_SURFACEMARK']
    shp_sb = None
    if 'C4_SPEEDBUMP' in map_info:
        shp_sb = map_info['C4_SPEEDBUMP']

    if enable_offset:
        if origin_node_id is not None:
            # 아이디 지정해서 origin으로 넣고 싶을 때
            origin_id = next((i for i, item in enumerate(shp_node.records()) if item['ID'] == origin_node_id), None)
            shapes = shp_node.shapes()
            origin_e = shapes[origin_id].points[0][0]
            origin_n = shapes[origin_id].points[0][1]
            origin_z = shapes[origin_id].z[0]
            origin = np.array([origin_e, origin_n, origin_z])
        else:
            origin = shp_common.get_first_shp_point(map_info['A1_NODE'])
            origin = np.array(origin)
        
        print('[INFO] Origin =', origin)
    else:
        origin = np.array(0, 0, 0)

    # Node, 일반 Link
    node_set, junction_set = __create_node_and_junction_set(shp_node, origin)
    link_set = __create_link_set(shp_link, origin, node_set)

    lane_node_set, lane_boundary_set = __create_lane_set(map_info['B2_SURFACELINEMARK'], map_info['C3_VEHICLEPROTECTIONSAFETY'], origin, link_set)
    
    # 오버랩노드 제거
    lane_nodes_of_no_use = repair_overlapped_node(search_overlapped_node(lane_node_set, 0.1))
    edit_node.delete_nodes(lane_node_set, lane_nodes_of_no_use)

    # TS, TL 생성
    ts_set = __create_traffic_sign_set_from_shp(shp_ts, origin, link_set)
    tl_set = __create_traffic_light_set_from_shp(shp_tl, origin, link_set)

    # SM 생성
    sm_set = __create_surface_marking_set_from_shp(shp_sm, shp_sb, origin, link_set)
    cw_set = __create_crosswalk_set_from_shp(shp_sm, origin, link_set)

    # MGeo Planner Map 생성
    mgeo_planner_map = MGeo(
        node_set = node_set, link_set = link_set, junction_set = junction_set, 
        lane_node_set = lane_node_set, lane_boundary_set=lane_boundary_set,
        sign_set = ts_set, light_set = tl_set, sm_set = sm_set, scw_set = cw_set)

    # NOTE: 모든 prj 파일은 같다고 가정하여, 하나만 읽는다.
    prj_file = os.path.normpath(os.path.join(input_path, 'A1_NODE.prj'))
    mgeo_planner_map.set_coordinate_system_from_prj_file(prj_file)

    mgeo_planner_map.set_origin(origin)

    return mgeo_planner_map


def __create_lane_set(sf, vh, origin, link_set):
    '''
    Lane은 차선, 도로 경계 등 다양한 정보가 섞여있고, DBF Record를 통해
    어떤 데이터인지 확인을 우선 해야 한다.
    '''
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    
    vh_shapes = vh.shapes()
    vh_records  = vh.records()
    vh_fields = vh.fields

    line_set_obj = LineSet()

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    # 데이터간 dbf 필드값이 달라서 예외 처리
    left_link_key = None
    right_link_key = None
    
    for field_names in fields:
        if 'L_linkID' in field_names:
            left_link_key = 'L_linkID'
        elif 'L_LinkID' in field_names:
            left_link_key = 'L_LinkID'

        if 'R_linkID' in field_names:
            right_link_key = 'R_linkID'
        elif 'R_LinkID' in field_names:
            right_link_key = 'R_LinkID'

    if (left_link_key is None 
        or right_link_key is None):
        raise BaseException('Unexpected link keys in .dbf source files')

    # 각 line의 양끝점을 모은 endpoints array 선언
    # endpoints = np.zeros((1, 5))
    # j = 0

    node_set = NodeSet()
    lane_set = LaneBoundarySet()

    for i in range(len(shapes)):
        dbf_rec = records[i]
        shp_rec = shapes[i]

        # kind_val == 'Border' >> our interest
        # kind_val = surfline_kind_code_to_str(dbf_rec['Kind'], lane_prefix=False)
        # type_val = surfline_type_code_to_str(dbf_rec['Type'])
        if len(shp_rec.points) == 0:
            print('[WARN] Skipping data at i={}: len(shp_rec.points)=0'.format(i))
            continue

        if len(shp_rec.points) != len(shp_rec.z):
            print('[WARN] Skipping data at i={}: len(shp_rec.points)={}, where as len(shp_rec.z)={}'.format(
                i, len(shp_rec.points), len(shp_rec.z)))
            continue

        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        idx = dbf_rec['ID']
        start_node = Node('R{}S'.format(idx))
        start_node.point = shp_rec.points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node('R{}E'.format(idx))
        end_node.point = shp_rec.points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=shp_rec.points, idx='{}'.format(idx))
        lane_boundary.lane_type_def = 'ngii_model2'
        # lane_boundary.fill_in_points_evenly_accor_to_leng(0.5)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)
        
        lane_type = str(dbf_rec['Kind'])
        
        lane_shape = dbf_rec['Type'][1:3]
        lane_color = dbf_rec['Type'][0]

        # if dbf_rec['Remark'] == '유도선':
        #     lane_type = '525'
        #     lane_shape = '12'
        #     lane_color = '2'
        # if dbf_rec['Remark'] == '정지선':
        #     lane_type = '530'
        #     lane_shape = '11'
        #     lane_color = '2'
        
        # 외곽선만 뽑아야할때 주석풀면 됌.
        # if lane_type not in ('505', '515'):
        #     continue

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
            logger.Logger.log_info('Unexpected lane_type = {}'.format(dbf_rec['Kind']))
        
        lane_boundary.lane_shape =  surfline_Type_code_to_str(lane_shape)
        lane_boundary.lane_color = _color_code_to_string(lane_color)
        lane_boundary.lane_type_offset = [0]

        if lane_type == '501':
            lane_boundary.lane_shape = ['Solid']
            # 531만 null값으로 있어서 넣음
        if lane_type == '531':
            lane_boundary.lane_shape = [ "Solid" ]
        if lane_type == '530':
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = ['white']
        if lane_type == '525':
            lane_boundary.lane_shape = [ "Broken" ]
            lane_boundary.lane_color = ['white']
        
        lane_set.lanes[lane_boundary.idx] = lane_boundary

        # Link에 Lane Marking 정보 설정
        # 535 : 자전거 도로, 599 : 기타선
        if dbf_rec[left_link_key]:
            if lane_type != '535' and lane_type != '599':
                link_set.lines[dbf_rec[left_link_key]].lane_mark_right.append(lane_boundary)
                # 값 비교해서 넣기
                # Link 방향이랑 비교
                # link_points = link_set.lines[dbf_rec[left_link_key]].points
                # link_vector = link_points[int(np.floor(len(link_points)/2))] - link_points[0]
                # link_heding = link_vector / np.linalg.norm(link_vector)
                # lane_vector = lane_boundary.points[int(np.floor(len(lane_boundary.points)/2))] - link_points[0]
                # lane_heding = lane_vector / np.linalg.norm(lane_vector)

                # cross = np.cross(link_heding[0:2], lane_heding[0:2])

                # if cross < 0:
                #     link_set.lines[dbf_rec[left_link_key]].lane_mark_right.append(lane_boundary)
                # else:
                #     link_set.lines[dbf_rec[left_link_key]].lane_mark_left.append(lane_boundary)

            
        if dbf_rec[right_link_key]:
            if lane_type != '535' and lane_type != '599':
                link_set.lines[dbf_rec[right_link_key]].lane_mark_left.append(lane_boundary)
                # 값 비교해서 넣기
                # Link 방향이랑 비교
                # link_points = link_set.lines[dbf_rec[right_link_key]].points
                # link_vector = link_points[int(np.floor(len(link_points)/2))] - link_points[0]
                # link_heding = link_vector / np.linalg.norm(link_vector)
                # lane_vector = lane_boundary.points[int(np.floor(len(lane_boundary.points)/2))] - link_points[0]
                # lane_heding = lane_vector / np.linalg.norm(lane_vector)

                # cross = np.cross(link_heding[0:2], lane_heding[0:2])

                # if cross > 0:
                #     link_set.lines[dbf_rec[right_link_key]].lane_mark_left.append(lane_boundary)
                # else:
                #     link_set.lines[dbf_rec[right_link_key]].lane_mark_right.append(lane_boundary)
                

    for i in range(len(vh_shapes)):
        dbf_rec = vh_records[i]
        shp_rec = vh_shapes[i]

        if len(shp_rec.points) == 0:
            print('[WARN] Skipping data at i={}: len(shp_rec.points)=0'.format(i))
            continue

        if len(shp_rec.points) != len(shp_rec.z):
            print('[WARN] Skipping data at i={}: len(shp_rec.points)={}, where as len(shp_rec.z)={}'.format(
                i, len(shp_rec.points), len(shp_rec.z)))
            continue
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        idx = dbf_rec['ID']
        start_node = Node('R{}S'.format(idx))
        start_node.point = shp_rec.points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node('R{}E'.format(idx))
        end_node.point = shp_rec.points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=shp_rec.points, idx='{}'.format(idx))
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)
        lane_boundary.lane_type_def = 'ngii_model2'
        lane_boundary.lane_type = [int(dbf_rec['Type'])]
        lane_boundary.lane_color = ['Curb']
        lane_boundary.lane_shape =  ['Solid']
        lane_boundary.lane_type_offset = [0]

        try:
            if dbf_rec['Type'] == '4':
                # 중앙분리대
                if dbf_rec['IsCentral'] == '1':
                    lane_boundary.lane_type = [1111]
                    lane_boundary.lane_color = ['Green']
                    lane_boundary.lane_shape =  ['Solid']
                
                elif dbf_rec['IsCentral'] == '0':
                    lane_boundary.lane_type = [4]
                    lane_boundary.lane_color = ['Undefined']
                    lane_boundary.lane_shape =  ['Solid']
        except:
            lane_boundary.lane_type = [4]
            lane_boundary.lane_color = ['Undefined']
            lane_boundary.lane_shape =  ['Solid']

        if 'Remark' in dbf_rec:
            if lane_boundary.lane_type[0] == 99:
                if dbf_rec['Remark'] == '녹지대':
                    lane_boundary.lane_type = [9999]
                    lane_boundary.lane_color = ['Green']
                    lane_boundary.lane_shape =  ['Solid']

        # 2 : 가드레일 6 : 중앙분리대 개구부
        # 3 : 콘크리트방호벽 7 : 임시구조물
        # 4 : 콘크리트연석 8 : 벽
        # 5 : 무단횡단방지시설 99 : 기타 시설물
        lane_set.lanes[lane_boundary.idx] = lane_boundary

    return node_set, lane_set


def _color_code_to_string(color_code):
    color_code = int(color_code)

    if color_code == 1:
        return ['yellow']
    elif color_code == 2:
        return ['white']
    elif color_code == 3:
        return ['blue']
    else:
        pass
        # raise BaseException('[ERROR] Undefined color_code = {}'.format(color_code))

def surfline_Type_code_to_str(shape_code):
    if shape_code == '11':
        return [ "Solid" ]
    elif shape_code == '12':
        return [ "Broken" ]
    # 임시
    elif shape_code =='14':
        return [ "Solid" ]

    elif shape_code == '21':
        return [ "Solid Solid"]
    elif shape_code == '22':
        return [ "Broken Broken"]
    elif shape_code == '23':
        return [ "Broken Solid" ]
    elif shape_code == '24':
        return [ "Solid Broken" ]
    else:
        print('[ERROR] Undefined shape_code = {}'.format(shape_code))
        # raise BaseException('[ERROR] Undefined shape_code = {}'.format(shape_code))

def is_out_of_xy_range(points, xlim, ylim):

    x = points[:,0]
    y = points[:,1]
    z = points[:,2]

    if x.max() < xlim[0] or xlim[1] < x.min():
        x_out = True
    else:
        x_out = False

    # y축에 대해
    if y.max() < ylim[0] or ylim[1] < y.min():
        y_out = True
    else:
        y_out = False
        
    return x_out or y_out

def create_crosswalk_mesh(input_path):
    print(input_path)
    map_info = shp_common.read_shp_files(input_path)[0]
    output_path = '../../rsc/map_data/ngii_shp_ver2_Seoul_Sangam/output/crosswalk'
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    """
    Origin이 되는 Point를 찾는다
    """
    # sf = map_info['A1_NODE']
    # shapes = sf.shapes()
    # records = sf.records()
    # fields = sf.fields

    # 서울 상암 origin
    origin = [ 313008.55819800857, 4161698.628368007, 35.66435583359189 ]
    origin = np.array(origin)
    print('[INFO] Origin =', origin.tolist())

    cw_set = CrossWalkSet()
    # sf = map_info['B3_SURFACEMARK']
    sf = map_info['B3_SURFACEMARK']
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        if is_out_of_xy_range(shp_rec.points, [-90, 735], [-445, 240]) != False:
            continue


        cw_id = dbf_rec['ID']
        cw_type = dbf_rec['Kind']

        cw = CrossWalk(points=shp_rec.points, idx=cw_id)
        cw.type_code_def = 'NGII_SHP2'
        cw.type = cw_type

        cw_set.append_data(cw)


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


    for file_name, vertex_face in vertex_face_sets.items():
        print('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
        file_name = os.path.normpath(os.path.join(output_path, file_name))  

        mesh_gen_vertices = vertex_face['vertex']
        mesh_gen_vertex_subsets_for_each_face = vertex_face['face']

        poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face)
        write_obj(poly_obj, file_name)


    print('END')


    

if __name__ == "__main__":
    input_path = 'D:\\road_model_maker\\data\\hdmap\\ngii_shp2_Sejong\\SEC01_BRT_UTM52N_EllipsoidHeight'
    create_crosswalk_mesh(input_path)