import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로
sys.path.append(current_path + '/../lib/common') # 프로젝트 Root 경로

import numpy as np

from lib.mgeo.class_defs import *
import shp_common


def import_all_data(input_path, origin_node_id=None):

    map_info, filename_map = shp_common.read_shp_files(input_path)

    shp_node = map_info['C1_NODE']
    shp_link = map_info['A3_LINK']
    shp_ts = map_info['B1_SIGN_POINT']
    shp_tl = map_info['B1_SIGNAL_POINT']


    if origin_node_id is not None:
        # 아이디 지정해서 origin으로 넣고 싶을 때
        origin_id = next((i for i, item in enumerate(shp_node.records()) if item['NODEID'] == origin_node_id), None)
        shapes = shp_node.shapes()
        origin_e = shapes[origin_id].points[0][0]
        origin_n = shapes[origin_id].points[0][1]
        origin_z = shapes[origin_id].z[0]
        origin = np.array([origin_e, origin_n, origin_z])
    else:
        origin = shp_common.get_first_shp_point(shp_node)
        origin = np.array(origin)
    print('[INFO] Origin =', origin)

    # Node, 일반 Link
    node_set, junction_set = __create_node_and_junction_set(shp_node, origin)
    link_set = __create_link_set(shp_link, origin, node_set)

    # TS, TL 생성
    ts_set = __create_traffic_sign_set_from_shp(shp_ts, origin, link_set)
    tl_set = __create_traffic_light_set_from_shp(shp_tl, origin, link_set)

    # MGeo Planner Map 생성
    mgeo_planner_map = MGeo(node_set=node_set, 
                                        link_set=link_set, 
                                        junction_set=junction_set, 
                                        sign_set=ts_set, 
                                        light_set=tl_set)

    # NOTE: 모든 prj 파일은 같다고 가정하여, 하나만 읽는다.
    prj_file = os.path.normpath(os.path.join(input_path, 'C1_NODE.prj'))
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
        node = Node(dbf_rec['NODEID'])
        node.point = shp_rec.points[0] 
        node.set_node_type(int(dbf_rec['NODETYPE']))
        its_id = dbf_rec['ITS_NODEID']

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
        shp_rec.points -= origin

        # 현재는 전부 바로 point가 init되는 Link를 생성
        link_id = dbf_rec['LINKID']
        link = Link(points=shp_rec.points, idx=link_id, lazy_point_init=False)
    
        if dbf_rec['FROMNODE'] not in node_set.nodes.keys():           
            # FromNodeID에 해당하는 노드가 없는 경우이다.
            # 새로운 노드를 생성해서 해결
            idx = dbf_rec['FROMNODE']
            print('[WARN] FROMNODE (id={}) does not exist. (for Link id={}) Thus one is automatically created.'.format(idx, link_id))            
            node = Node(idx)
            node.point = shp_rec.points[0] 
            node_set.append_node(node)
            from_node = node
        else:
            from_node = node_set.nodes[dbf_rec['FROMNODE']]

        if dbf_rec['TONODE'] not in node_set.nodes.keys():
            # ToNodeID에 해당하는 노드가 없는 경우이다.
            # 새로운 노드를 생성해서 해결
            idx = dbf_rec['TONODE']
            print('[WARN] TONODE (id={}) does not exist. (for Link id={})  Thus one is automatically created.'.format(idx, link_id))            
            node = Node(idx)
            node.point = shp_rec.points[0] 
            node_set.append_node(node)
            to_node = node
        else:
            to_node = node_set.nodes[dbf_rec['TONODE']]

        link.set_from_node(from_node)
        link.set_to_node(to_node)
        
        # 차선 변경 여부를 결정하는데 사용한다
        # NGII에는 Road Type만 있음
        # 1: 일반가로, 2: 터널, 3: 교량, 4: 지하도로, 5: 고가차도, 6: 톨게이트, 7: 하이패스차로
        # NGII2에는 Road Type, Link Type 분리되어 있음
        # 1: 교차로내 주행경로, 2: 하이패스차로, 3: 톨게이트차로, 4: 버스전용차로, 5: 가변차선차로, 6: 일반주행차로 등등
        # link.link_type = dbf_rec['ROADTYPE']
        link_type = dbf_rec['ROADTYPE']
        if link_type == '6':
            link.link_type = '3'
        elif link_type == '7':
            link.link_type = '2'
        else:
            link.link_type = '6'

        link.road_id = dbf_rec['ROADNO']
        
        # ego_lane 추가
        link.ego_lane = dbf_rec['LANE']
        # link_type_def 추가
        link.link_type_def = 'ngii_model1'

        # Max Speed 추가
        link.set_max_speed_kph(dbf_rec['SPEED'])

        # link_set에 추가
        line_set.lines[link.idx] = link

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
        signal_id = to_str_if_int(dbf_rec['HDUFID'])
        link_id_list = [to_str_if_int(dbf_rec['LINKID'])]

        signal = Signal(signal_id)
        signal.link_id_list = link_id_list 

        signal.dynamic = False
        signal.orientation = '+'
        signal.country = 'KR'
        signal.type = dbf_rec['CODE']
        signal.sub_type = dbf_rec['SIGNTYPE']

        # 사이즈 설정
        # type, sub_type 값을 설정한 후 호출해야 함
        signal.set_size()

        # 최고속도제한 규제표지
        if signal.type == 2 and signal.sub_type == 221 and signal.link_list.__len__ > 0  :
            signal.value = signal.link_list[signal.link_id_list[0]].max_speed_kph
        # 최저속도제한 규제표지
        elif signal.type == 2 and signal.sub_type == 222 and signal.link_list.__len__ > 0 :
            signal.value = signal.link_list[signal.link_id_list[0]].min_speed_kph
            
        signal.point = shp_rec.points[0]
        
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
        signal_id = to_str_if_int(dbf_rec['HDUFID'])
        link_id_list = [to_str_if_int(dbf_rec['LINKID'])]

        signal = Signal(signal_id)
        signal.link_id_list = link_id_list

        signal.dynamic = True
        signal.orientation = '+'
        signal.country = 'KR'

        signal.type = dbf_rec['CODE']
        signal.sub_type = dbf_rec['SIGNTYPE']

        signal.set_size()

        signal.point = shp_rec.points[0]

        traffic_light_set.signals[signal.idx] = signal

    return traffic_light_set   

def import_lane_marking_data(input_path, origin_node_id=None):

    map_info, filename_map = shp_common.read_shp_files(input_path)

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 C1_NODE 중 ID가 206I10440403 인 데이터를 원점으로 한다.
    NGII SHP2 데이터에서 같은 위치의 ID는 A119AS305498 이다.
    """
    # 융기원 데이터에서는,
    sf = map_info['C1_NODE']
    shapes = sf.shapes()
    records = sf.records()
    fields = sf.fields


    if origin_node_id is not None:
        # 아이디 지정해서 origin으로 넣고 싶을 때
        origin_id = next((i for i, item in enumerate(sf.records()) if item['NODEID'] == origin_node_id), None)
        shapes = sf.shapes()
        origin_e = shapes[origin_id].points[0][0]
        origin_n = shapes[origin_id].points[0][1]
        origin_z = shapes[origin_id].z[0]
        origin = np.array([origin_e, origin_n, origin_z])
    else:
        origin = shp_common.get_first_shp_point(sf)
        origin = np.array(origin)
    print('[INFO] Origin =', origin)

    # 각각을 line으로 만들고 mgeo_planner_map에서 접근할 수 있게 해준다.
    lane_node_set = NodeSet()
    lane_boundary_set = LaneBoundarySet()

    a1_lane = map_info['A1_LANE']
    a2_stop = map_info['A2_STOP']
    b2_surfsign_line = map_info['B2_SURFSIGN_LINE']

    shp_node = map_info['C1_NODE']
    shp_link = map_info['A3_LINK']

    # Node, 일반 Link
    node_set, junction_set = __create_node_and_junction_set(shp_node, origin)
    link_set = __create_link_set(shp_link, origin, node_set)

    __create_lane_marking_from_a1_lane(a1_lane, lane_node_set, lane_boundary_set, origin)
    __create_lane_marking_from_a2_stop(a2_stop, lane_node_set, lane_boundary_set, origin)
    __create_lane_marking_from_b2_surfsign_line(b2_surfsign_line, lane_node_set, lane_boundary_set, origin)

    mgeo_planner_map = MGeo(
        node_set=node_set, link_set=link_set, lane_node_set=lane_node_set, lane_boundary_set=lane_boundary_set, junction_set=junction_set)

    mgeo_planner_map.set_origin(origin)

    return mgeo_planner_map


def __create_lane_marking_from_a1_lane(sf, node_set, line_set, origin):
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')
    
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # 먼저 dbf rec를 보고 lane이 아닌 것은 넘어간다
        if dbf_rec['CODE'] == '2':
            # CODE가 2이면, barrier 이다. skip.
            continue

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        lane_marking_id = dbf_rec['HDUFID']

        # 처음 포인트, 마지막 포인트에 node 생성하기
        start_node = Node(lane_marking_id+'S')
        start_node.point = shp_rec.points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = shp_rec.points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=shp_rec.points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        # 세부 속성 설정 >> LANETYPE에서 색상, 형태를 얻어낸다
        if int(dbf_rec['LANETYPE'][0]) == 1:
            line_color = ['yellow']
        elif int(dbf_rec['LANETYPE'][0]) == 2:
            line_color = ['white']
        elif int(dbf_rec['LANETYPE'][0]) == 3:
            line_color = ['blue']
        else:
            raise BaseException('Unexpected line_color: {}'.format(dbf_rec['LANETYPE'][0]))

        line_num = int(dbf_rec['LANETYPE'][1])
        if line_num != 1 and line_num != 2:
            raise BaseException('Unexpected line_num: {}'.format(dbf_rec['LANETYPE'][1]))
        
        if int(dbf_rec['LANETYPE'][2]) == 1:
            if line_num == 1:
                line_shape = ['solid']
            else:
                line_shape = ['solid', 'solid']
        elif int(dbf_rec['LANETYPE'][2]) == 2:
            if line_num == 1:
                line_shape = ['dashed']
            else:
                line_shape = ['dashed', 'dashed']
        elif int(dbf_rec['LANETYPE'][2]) == 3:
            if line_num == 1:
                raise BaseException("Incompatiblity between line num & shape. line_num: 1, but shape: ['dashed', 'solid']")
            else:
                line_shape = ['dashed', 'solid']
        elif int(dbf_rec['LANETYPE'][2]) == 4:
            if line_num == 1:
                raise BaseException("Incompatiblity between line num & shape. line_num: 1, but shape: ['solid', 'dashed']")
            else:
                line_shape = ['solid', 'dashed'] 
        else:
            raise BaseException('Unexpected line_shape: {}'.format(dbf_rec['LANETYPE'][2]))


        lane_boundary.lane_color = line_color
        lane_boundary.lane_shape = line_shape

        # 세부 속성 >> 차선의 역할인데, NGII SHP1에서는 유턴구역선만 확인하면 된다.
        lane_type = int(dbf_rec['LANECODE'])
        lane_boundary.lane_type_def = 'NGII_SHP2' # SH1 데이터인데, 이를 변경한다
        
        if lane_type == 1: # 중앙선 (문서에 있음) -> 501
            lane_boundary.lane_type = [501]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3

        elif lane_type == 2: # 유턴 구역선 (문서에 있음) -> 502
            lane_boundary.lane_type = [502]
            lane_boundary.lane_width = 0.35 # 너비가 0.3~0.45 로 규정되어있다.
            lane_boundary.dash_interval_L1 = 0.5
            lane_boundary.dash_interval_L2 = 0.5

        elif lane_type == 3: # (일반) 차선 (문서에 있음) -> 503
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

        elif lane_type == 4: # 버스 전용 차선 (전용차선으로 문서에 있음) -> 504
            lane_boundary.lane_type = [504]
            lane_boundary.lane_width = 0.15 
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3

        elif lane_type == 5: # 진로 변경 제한선 (문서에 있음) -> 506
            lane_boundary.lane_type = [506]
            lane_boundary.lane_width = 0.15 #점선일 때 너비가 0.1 ~ 0.5로, 넓을 수도 있다.
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
        
        elif lane_type == 6: # 가변차선 (문서에 없음. 버스 전용차선과 동일하게 처리) -> 5011
            lane_boundary.lane_type = [5011]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3

        elif lane_type == 7: # 길 가장자리 구역선 (문서에 있음) -> 505
            lane_boundary.lane_type = [505]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.

        elif lane_type == 8: # 주차금지표시 (문서에 없음) -> 515
            lane_boundary.lane_type = [515]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
        
        elif lane_type == 9: # 정차,주차 금지 표시 (문서에 없음) -> 515
            lane_boundary.lane_type = [515]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.

        elif lane_type == 10: # 자전거도로 (문서에 없음) -> 535
            lane_boundary.lane_type = [535]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.

        elif lane_type == 11: # 안전지대구역선 (문서에 없음) -> 531
            lane_boundary.lane_type = [531]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
        
        elif lane_type == 12: # 톨게이트병목구간건 (문서에 없음) -> 599
            lane_boundary.lane_type = [599]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.

        elif lane_type == 19: # 기타표시 (문서에 없음) -> 599
            lane_boundary.lane_type = [599]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
        
        else:
            raise BaseException('Unexpected lane_type = {}'.format(dbf_rec['LANECODE']))

        lane_boundary.lane_type_offset = [0]
        line_set.lanes[lane_boundary.idx] = lane_boundary


def __create_lane_marking_from_a2_stop(sf, node_set, line_set, origin):
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

        lane_marking_id = dbf_rec['HDUFID']

        # 처음 포인트, 마지막 포인트에 node 생성하기
        start_node = Node(lane_marking_id+'S')
        start_node.point = shp_rec.points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = shp_rec.points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=shp_rec.points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        # 세부 속성 설정
        lane_boundary.lane_color = ['white']
        lane_boundary.lane_shape = ['solid']
 
        lane_boundary.lane_type = [530] # 정지선이 표현 가능한 NGII_SHP2 코드로 변경한다
        lane_boundary.lane_type_def = 'NGII_SHP2'

        lane_boundary.lane_width = 0.6 # 정지선은 0.3 ~ 0.6
        lane_boundary.dash_interval_L1 = 0 # 정지선에서는 의미가 없다
        lane_boundary.dash_interval_L2 = 0 # 정지선에서는 의미가 없다.

        line_set.lanes[lane_boundary.idx] = lane_boundary


def __create_lane_marking_from_b2_surfsign_line(sf, node_set, line_set, origin):
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

        lane_marking_id = dbf_rec['HDUFID']

        # 처음 포인트, 마지막 포인트에 node 생성하기
        start_node = Node(lane_marking_id+'S')
        start_node.point = shp_rec.points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = shp_rec.points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=shp_rec.points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        # 세부 속성 설정
        lane_boundary.lane_color = ['white']
        lane_boundary.lane_shape = ['dashed']
 
        lane_boundary.lane_type = [525] # 유도선이 표현 가능한 NGII_SHP2 코드로 변경한다
        lane_boundary.lane_type_def = 'NGII_SHP2'

        lane_boundary.lane_width = 0.15
        lane_boundary.dash_interval_L1 = 0.75 # 0.5 ~ 1.0
        lane_boundary.dash_interval_L2 = 0.75 # 0.5 ~ 1.0

        line_set.lanes[lane_boundary.idx] = lane_boundary


def import_crowsswalk_and_surface_marking_data(input_path):
    map_info = shp_common.read_shp_files(input_path)   

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 C1_NODE 중 ID가 206I10440403 인 데이터를 원점으로 한다.
    NGII SHP2 데이터에서 같은 위치의 ID는 A119AS305498 이다.
    """
    sf = map_info['C1_NODE']
    shapes = sf.shapes()
    records = sf.records()
    fields = sf.fields

    for i in range(len(sf)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        if dbf_rec['NODEID'] == '206I10440403':
            e = shp_rec.points[0][0]
            n = shp_rec.points[0][1] 
            z = shp_rec.z[0]
            origin = [e, n ,z]
            break

    origin = np.array([e, n ,z])
    print('[INFO] Origin =', origin.tolist())
    # 이렇게 구한 Origin은 다음과 같다 (TM좌표계임에 유의)
    # [INFO] Origin = [209402.0923992687, 533433.0495021925, 39.684636742713245]

    cw_set, sm_set = __create_sm_set(map_info['B2_SURFSIGN_PLANE'], origin)

    return cw_set, sm_set 


def __create_sm_set(sf, origin):

    sm_set = SurfaceMarkingSet()
    cw_set = CrossWalkSet()

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

        # 상대좌표로 변경
        shp_rec.points -= origin


        sign_type = int(dbf_rec['SIGNTYPE'])
        # 1: 정차금지지대
        # 2: 유도면
        # 3: 오르막경사면
        # 4: 횡단보도
        # 5: 고원식횡단보도
        # 6: 자전거횡단보도
        # 7: 과속방지턱
        # 8: 기타

        if sign_type in [4, 6]:
            # 
            cw = CrossWalk(points=shp_rec.points, idx=dbf_rec['HDUFID'])

            cw.type_code_def = 'NGII_SHP1'
            cw.type = sign_type

            # cw_set에 추가
            cw_set.append_data(cw)

        elif sign_type in [1, 7]:
            # Surface Marking 인스턴스 생성
            sm = SurfaceMarking(points=shp_rec.points, idx=dbf_rec['HDUFID'])
            
            sm.type_code_def = 'NGII_SHP1'
            sm.type = sign_type

            # sm_set에 추가
            sm_set.append_data(sm)
        else:
            # TODO(sglee) 우선은 AICT 판교 데이터에 포함된 것만 고려한 것이다. 
            # 향후 다른 데이터가 발견되면 어떻게 처리할지 고민
            raise BaseException('Unexpected type: {}'.format(sign_type))
        

    return cw_set, sm_set 


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