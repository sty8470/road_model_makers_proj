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
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common


from lib.common.logger import Logger

from pyproj import Proj, transform

proj_1 = Proj('epsg:5186')
# proj_1 = Proj('+proj=tmerc +lat_0=38 +lon_0=129.0028902777778 +k=1 +x_0=200000 +y_0=500000 +ellps=bessel +units=m +no_defs +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43')
proj_2 = Proj(proj='utm', zone=52, ellps='WGS84', preserve_units=False)

class MobiltechImporter:


    def shp_to_map_snu(self, input_path):
        # 서울대 지도 데이터가 A1_NODE, A2_LINK, B2_SURFACELINEMARK 밖에 없어서 따로 작성
        
        map_info, filename_map = shp_common.read_shp_files(input_path)

        origin = shp_common.get_first_shp_point(map_info['A2_LINK'])
        origin[0], origin[1] = transform(proj_1, proj_2, origin[1], origin[0])
        origin = np.array(origin)

        Logger.log_info('Origin ={}'.format(origin))

        node_set = NodeSet()
        junction_set = JunctionSet()
        
        shapes = map_info['A1_NODE'].shapes()
        records  = map_info['A1_NODE'].records()
        fields = map_info['A1_NODE'].fields

        if len(shapes) != len(records):
            raise BaseException('[ERROR] len(shapes) != len(records)')
        
        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]

            # Convert to numpy array
            shp_rec.points = np.array(shp_rec.points)
            new_points = []
            for point in shp_rec.points:
                new_point = point
                new_point[0], new_point[1] = transform(proj_1, proj_2, point[1], point[0])
                new_points.append(new_point)
            new_points = np.array(new_points)
            shp_rec.z = np.array(shp_rec.z)

            # Point에 z축 값도 그냥 붙여버리자
            new_points = np.c_[new_points, shp_rec.z]

            # origin 무조건 전달, 상대좌표로 변경
            new_points -= origin

            # node로 추가
            node = Node(dbf_rec['ID'])
            node.point = new_points[0]
            node.node_type = dbf_rec['NODETYPE']
            node.node_type_def = dbf_rec['MAKER']
            its_id = dbf_rec['ITSNODEID']

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

        
        link_set = LineSet()

        shapes = map_info['A2_LINK'].shapes()
        records  = map_info['A2_LINK'].records()
        fields = map_info['A2_LINK'].fields

        if len(shapes) != len(records):
            raise BaseException('[ERROR] len(shapes) != len(records)')

            
        # 우선 링크셋을 만든다
        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]

            # Convert to numpy array
            shp_rec.points = np.array(shp_rec.points)
            new_points = []
            for point in shp_rec.points:
                new_point = point
                new_point = transform(proj_1, proj_2, point[1], point[0])
                new_points.append(new_point)
            new_points = np.array(new_points)
            shp_rec.z = np.array(shp_rec.z)

            # Point에 z축 값도 그냥 붙여버리자
            new_points = np.c_[new_points, shp_rec.z]

            # origin 무조건 전달, 상대좌표로 변경
            new_points -= origin

            # 현재는 전부 바로 point가 init되는 Link를 생성
            link_id = dbf_rec['ID']
            link = Link(points=new_points, idx=link_id, lazy_point_init=False)
        
            if dbf_rec['FROMNODEID'] not in node_set.nodes.keys():           
                # FromNodeID에 해당하는 노드가 없는 경우이다.
                # 새로운 노드를 생성해서 해결
                idx = dbf_rec['FROMNODEID']
                print('[WARN] FromNode (id={}) does not exist. (for Link id={}) Thus one is automatically created.'.format(idx, link_id))            
                node = Node(idx)
                node.point = new_points[0] 
                node_set.append_node(node)
                from_node = node
            else:
                from_node = node_set.nodes[dbf_rec['FROMNODEID']]

            if dbf_rec['TONODEID'] not in node_set.nodes.keys():
                # ToNodeID에 해당하는 노드가 없는 경우이다.
                # 새로운 노드를 생성해서 해결
                idx = dbf_rec['TONODEID']
                print('[WARN] ToNode (id={}) does not exist. (for Link id={})  Thus one is automatically created.'.format(idx, link_id))            
                node = Node(idx)
                node.point = new_points[0] 
                node_set.append_node(node)
                to_node = node
            else:
                to_node = node_set.nodes[dbf_rec['TONODEID']]

            link.set_from_node(from_node)
            link.set_to_node(to_node)
            
            link.road_type = dbf_rec['ROADTYPE']
            
            # 차선 변경 여부를 결정하는데 사용한다
            # 1: 교차로내 주행경로, 2 & 3: 톨게이트차로(하이패스, 비하이패스)
            link.link_type = dbf_rec['LINKTYPE']
            if link.link_type == '1':
                link.from_node.on_stop_line = True
                link.related_signal = 'straight'
                if dbf_rec['LANENO'] > 90:
                    link.related_signal = 'left'

            # Max Speed 추가
            link.set_max_speed_kph(dbf_rec['MAXSPEED'])

            # ego_lane 추가
            link.ego_lane = dbf_rec['LANENO']
            # link_type_def 추가
            link.link_type_def = dbf_rec['SECTIONID']
            link.road_id = dbf_rec['MAKER']
            # link_set에 추가
            link_set.lines[link.idx] = link


        # 차선 변경을 위해, 좌/우에 존재하는 링크에 대한 Reference를 추가한다
        # 단, 좌/우에 존재하는 링크라고해서 반드시 차선 변경이 가능한 것은 아니다
        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]

            link = link_set.lines[dbf_rec['ID']]

            # 양옆 차선 속성도 dbf 데이터로부터 획득
            if dbf_rec['R_LINKID'] is not '': # NOTE: 일부 파일에는 소문자 k에 오타가 있어 R_LinKID로 조회해야할 수 있다. 
                lane_ch_link_right = link_set.lines[dbf_rec['R_LINKID']] # NOTE: 일부 파일에는 소문자 k에 오타가 있어 R_LinKID로 조회해야할 수 있다. 
                link.lane_ch_link_right = lane_ch_link_right
                link.can_move_right_lane = True

            if dbf_rec['L_LINKID'] is not '': # NOTE: 일부 파일에는 소문자 k에 오타가 있어 L_LinKID로 조회해야할 수 있다. 
                lane_ch_link_left = link_set.lines[dbf_rec['L_LINKID']] # NOTE: 일부 파일에는 소문자 k에 오타가 있어 L_LinKID로 조회해야할 수 있다. 
                link.lane_ch_link_left = lane_ch_link_left
                link.can_move_left_lane = True


        lane_node_set = NodeSet()
        lane_set = LaneBoundarySet()

        sf = map_info['B2_SURFACELINEMARK']

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
            new_points = []
            for point in shp_rec.points:
                new_point = point
                new_point = transform(proj_1, proj_2, point[1], point[0])
                new_points.append(new_point)
            new_points = np.array(new_points)
            shp_rec.z = np.array(shp_rec.z)

            # Point에 z축 값도 그냥 붙여버리자
            new_points = np.c_[new_points, shp_rec.z]

            # origin 무조건 전달, 상대좌표로 변경
            new_points -= origin
            
            lane_marking_id = dbf_rec['ID']

            start_node = Node(lane_marking_id+'S')
            start_node.point = new_points[0]
            lane_node_set.nodes[start_node.idx] = start_node

            end_node = Node(lane_marking_id+'E')
            end_node.point = new_points[-1]
            lane_node_set.nodes[end_node.idx] = end_node

            lane_boundary = LaneBoundary(points=new_points, idx=lane_marking_id)
            lane_boundary.set_from_node(start_node)
            lane_boundary.set_to_node(end_node)

            lane_boundary.lane_type_def = dbf_rec['MAKER']
            
            line_admincode = dbf_rec['TYPE']
            
            lane_boundary.lane_shape = _surfline_Type_code_to_str(line_admincode[1:3])
            lane_boundary.lane_color = _color_code_to_string(line_admincode[0])
            lane_boundary.lane_type_offset = [0]
            _lane_type_and_width(dbf_rec['KIND'], lane_boundary)
            lane_set.lanes[lane_boundary.idx] = lane_boundary

            if dbf_rec['L_LINKID'] in link_set.lines:
                link_set.lines[dbf_rec['L_LINKID']].lane_mark_right.append(lane_boundary)
            if dbf_rec['R_LINKID'] in link_set.lines:
                link_set.lines[dbf_rec['R_LINKID']].lane_mark_left.append(lane_boundary)
        
        
        mgeo = MGeo(node_set=node_set,
                                link_set=link_set, 
                                lane_node_set=lane_node_set, 
                                lane_boundary_set=lane_set)
        mgeo.set_origin(origin)
        # mgeo.global_coordinate_system = Proj('epsg:5186').definition_string()
        mgeo.global_coordinate_system = '+proj=utm +zone=52 +datum=WGS84 +units=m +no_defs'

        return mgeo

    def shp_to_map(self, input_path):

        # output_path = os.path.join(input_path, 'output') 
        # relative_loc = True
        # try:
        #     if not os.path.exists(output_path):
        #         os.makedirs(output_path)
        # except OSError:
        #     Logger.log_error('Error: Creating directory. {}'.format(output_path))


        # # Change StrDir to Absolute Path
        # current_path = os.path.dirname(os.path.realpath(__file__)) 

        # Logger.log_info('input  path: {}'.format(input_path))
        # Logger.log_info('output path: {}'.format(output_path))
        
        # Get File List
        map_info, filename_map = shp_common.read_shp_files(input_path)

        # mgeo
        node = next((item for item in map_info.keys() if 'NODE' in item), False)
        link = next((item for item in map_info.keys() if 'LINK' in item), False)
        sign = next((item for item in map_info.keys() if 'SIGN_POINT' in item), False)
        signal = next((item for item in map_info.keys() if 'SIGNAL_POINT' in item), False)

        origin = shp_common.get_first_shp_point(map_info[link])
        Logger.log_info('Origin ={}'.format(origin))

        node_set, link_set = self.create_node_and_link_set_from_shp(map_info, origin)
        lane_node_set, lane_set = self.create_lane_marking_set_from_shp(map_info, origin)

        mego_planner_map = MGeo(node_set=node_set,
                                            link_set=link_set, 
                                            lane_node_set=lane_node_set, 
                                            lane_boundary_set=lane_set)
        mego_planner_map.set_origin(origin)

        return mego_planner_map
        
    def create_node_and_link_set_from_shp(self, map_info, origin):
        
        link = next((item for item in map_info.keys() if 'LINK' in item), False)

        node_set = NodeSet()
        link_set = LineSet()

        idx = 0
        sf = map_info[link]
        
        shapes = sf.shapes()
        records  = sf.records()
        fields = sf.fields
        if len(shapes) != len(records):
            raise BaseException('[ERROR] len(shapes) != len(records)')

        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]

            shp_rec.points = np.array(shp_rec.points)
            shp_rec.z = np.array(shp_rec.z)
            shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
            shp_rec.points -= origin
            
            link_id = 'LINK{}'.format(idx)
            idx += 1

            start_node = Node(link_id+'S')
            start_node.point = shp_rec.points[0]
            node_set.nodes[start_node.idx] = start_node

            end_node = Node(link_id+'E')
            end_node.point = shp_rec.points[-1]
            node_set.nodes[end_node.idx] = end_node

            link = Link(points=shp_rec.points, idx=link_id, lazy_point_init=False)
            link.set_from_node(start_node)
            link.set_to_node(end_node)

            
            # link_type_def 추가
            link.link_type_def = 'mobiltech'

            link_set.lines[link.idx] = link

        return node_set, link_set


    def create_lane_marking_set_from_shp(self, map_info, origin):

        # lane
        lane = next((item for item in map_info.keys() if 'LANE' in item), False)
        stop = next((item for item in map_info.keys() if 'STOP' in item), False)
        sur_line = next((item for item in map_info.keys() if 'SURFSIGN_LINE' in item), False)
        sur_plane = next((item for item in map_info.keys() if 'SURFSIGN_PLANE' in item), False)
        sur_pit = next((item for item in map_info.keys() if 'SURFSIGN_POINT' in item), False)

        node_set = NodeSet()
        lane_set = LaneBoundarySet()

        lane_sf = map_info[lane]
        stop_sf = map_info[stop]
        sur_sf = map_info[sur_line]

        lane_id = 0

        shapes = lane_sf.shapes()
        records  = lane_sf.records()
        fields = lane_sf.fields

        if len(shapes) != len(records):
            raise BaseException('[ERROR] len(shapes) != len(records)')

        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]

            shp_rec.points = np.array(shp_rec.points)
            shp_rec.z = np.array(shp_rec.z)
            shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
            shp_rec.points -= origin
            
            # lane_marking_id = dbf_rec['id']
            lane_marking_id = 'LANE{}'.format(lane_id)
            lane_id += 1

            start_node = Node(lane_marking_id+'S')
            start_node.point = shp_rec.points[0]
            node_set.nodes[start_node.idx] = start_node

            end_node = Node(lane_marking_id+'E')
            end_node.point = shp_rec.points[-1]
            node_set.nodes[end_node.idx] = end_node

            lane_boundary = LaneBoundary(points=shp_rec.points, idx=lane_marking_id)
            lane_boundary.set_from_node(start_node)
            lane_boundary.set_to_node(end_node)

            lane_boundary.lane_type_def = 'sample'
            lane_boundary.lane_type = [599]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_shape = ["Solid"]
            lane_boundary.lane_color = ['white']
            
            lane_set.lanes[lane_boundary.idx] = lane_boundary


        shapes = stop_sf.shapes()
        records  = stop_sf.records()
        fields = stop_sf.fields

        if len(shapes) != len(records):
            raise BaseException('[ERROR] len(shapes) != len(records)')

        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]

            shp_rec.points = np.array(shp_rec.points)
            shp_rec.z = np.array(shp_rec.z)
            shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
            shp_rec.points -= origin
            
            # lane_marking_id = dbf_rec['id']
            lane_marking_id = 'STOP{}'.format(lane_id)
            lane_id += 1

            start_node = Node(lane_marking_id+'S')
            start_node.point = shp_rec.points[0]
            node_set.nodes[start_node.idx] = start_node

            end_node = Node(lane_marking_id+'E')
            end_node.point = shp_rec.points[-1]
            node_set.nodes[end_node.idx] = end_node

            lane_boundary = LaneBoundary(points=shp_rec.points, idx=lane_marking_id)
            lane_boundary.set_from_node(start_node)
            lane_boundary.set_to_node(end_node)

            lane_boundary.lane_type_def = 'sample'
            lane_boundary.lane_type = [530]
            lane_boundary.lane_width = 0.6
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_shape = ["Solid"]
            lane_boundary.lane_color = ['white']
            
            lane_set.lanes[lane_boundary.idx] = lane_boundary

        shapes = sur_sf.shapes()
        records  = sur_sf.records()
        fields = sur_sf.fields

        if len(shapes) != len(records):
            raise BaseException('[ERROR] len(shapes) != len(records)')

        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]

            shp_rec.points = np.array(shp_rec.points)
            shp_rec.z = np.array(shp_rec.z)
            shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
            shp_rec.points -= origin

            # lane_marking_id = dbf_rec['id']
            lane_marking_id = 'SURLINE{}'.format(lane_id)
            lane_id += 1

            start_node = Node(lane_marking_id+'S')
            start_node.point = shp_rec.points[0]
            node_set.nodes[start_node.idx] = start_node

            end_node = Node(lane_marking_id+'E')
            end_node.point = shp_rec.points[-1]
            node_set.nodes[end_node.idx] = end_node

            lane_boundary = LaneBoundary(points=shp_rec.points, idx=lane_marking_id)
            lane_boundary.set_from_node(start_node)
            lane_boundary.set_to_node(end_node)

            lane_boundary.lane_type_def = 'sample'
            lane_boundary.lane_type = [525]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 0.75 # 0.5 ~ 1.0
            lane_boundary.dash_interval_L2 = 0.75 # 0.5 ~ 1.0
            lane_boundary.lane_shape = ["Broken"]
            lane_boundary.lane_color = ['white']
            
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
        return ['undefined']
        # raise BaseException('[ERROR] Undefined color_code = {}'.format(color_code))

def _surfline_Type_code_to_str(shape_code):
    if shape_code == '11':
        return [ "Solid" ]
    elif shape_code == '12':
        return [ "Broken" ]
    # 임시
    elif shape_code =='14':
        return [ "Solid" ]

    elif shape_code == '21':
        return [ "Solid", "Solid"]
    elif shape_code == '22':
        return [ "Broken", "Broken"]
    elif shape_code == '23':
        return [ "Broken", "Solid" ]
    elif shape_code == '24':
        return [ "Solid", "Broken" ]
    else:
        return [ "Solid" ]
        print('[ERROR] Undefined shape_code = {}'.format(shape_code))
        # raise BaseException('[ERROR] Undefined shape_code = {}'.format(shape_code))

def _lane_type_and_width(lane_type, lane_boundary):

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

        lane_boundary.lane_color = ['white']
        lane_boundary.lane_shape = ["Broken"]

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
        
        lane_boundary.lane_color = ['white']
        lane_boundary.lane_shape = ["Solid"]
    
    elif lane_type == '506':  # 진로변경제한선
        lane_boundary.lane_type = [506]
        lane_boundary.lane_width = 0.15 #점선일 때 너비가 0.1 ~ 0.5로, 넓을 수도 있다.
        lane_boundary.dash_interval_L1 = 3
        lane_boundary.dash_interval_L2 = 3
        
        lane_boundary.lane_color = ['white']
        lane_boundary.lane_shape = ["Solid"]

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
        
        lane_boundary.lane_color = ['white']
        lane_boundary.lane_shape = ["Broken"]

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
        raise BaseException('Unexpected lane_type = {}'.format(lane_type))
    


if __name__ == u'__main__':
    input_path = 'D:\\01.지도\\210831_[mobiltech]SHP_seoul_univ_test_track_V1'
    importer = MobiltechImporter()
    importer.shp_to_map_snu(input_path)
    