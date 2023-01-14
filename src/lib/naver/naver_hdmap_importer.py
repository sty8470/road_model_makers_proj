import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import numpy as np

from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common


"""
Naver에서 전달해준 geojson 데이터를 MGeo로 변환하기 위한 클래스

주요 기능의 input/ouput
input : GeoJSON 데이터가 포함된 경로
output: MGeo PlannerMap 클래스 인스턴스
"""
class NaverHDMapImporter:

    def import_geojson(self, iuput_folder_path):
        geojson_files = geojson_common.read_geojson_files(iuput_folder_path)[0]

        node_file_name = next((item for item in geojson_files.keys() if 'NODE' in item), False)
        link_file_name = next((item for item in geojson_files.keys() if 'LINK' in item), False)
        lane_file_name = next((item for item in geojson_files.keys() if 'LANE' in item), False)
        stop_file_name = next((item for item in geojson_files.keys() if 'STOP' in item), False)
        
        surface_plane_file_name = next((item for item in geojson_files.keys() if 'PLANE' in item), False)

        origin = geojson_common.get_first_geojson_point(geojson_files[node_file_name]['features'])

        # GeoJSON 파일을 읽어서 traffic sign, traffic signal 목록 생성 및 반환
        if node_file_name:
            geojson_node = geojson_files[node_file_name]['features']
            node_set = self.__create_node_set_from_geojson(geojson_node, origin)
        else:
            node_set = NodeSet() # empty set 

        if link_file_name:
            geojson_link = geojson_files[link_file_name]['features']        
            link_set = self.__create_link_set_from_geojson(geojson_link, node_set, origin)
        else:
            link_set = LineSet() # empty set 

        if lane_file_name and stop_file_name:
            a1_lane = geojson_files[lane_file_name]['features']
            a2_stop = geojson_files[stop_file_name]['features']      
            lane_node_set, lane_boundary_set = self.__create_lane_boundary_set_from_geojson(a1_lane, a2_stop, origin)
        else:
            lane_node_set = NodeSet()
            lane_boundary_set = LaneBoundarySet()
            
        if surface_plane_file_name:
            b2_surface_plane = geojson_files[surface_plane_file_name]['features']        
            singlecrosswalk_set = self.__create_singlecrosswalk_set_from_geojson(b2_surface_plane, origin)
        else:
            singlecrosswalk_set = SingleCrosswalkSet() # empty set 

        # MGeo Planner Map Instance 생성
        mgeo_planner_map = MGeo(node_set=node_set, link_set=link_set, lane_node_set=lane_node_set, lane_boundary_set=lane_boundary_set, scw_set=singlecrosswalk_set)
        mgeo_planner_map.set_origin(origin)
        
        return mgeo_planner_map

    
    def __create_node_set_from_geojson(self, node_list, origin):   
        node_set = NodeSet()

        for i in range(len(node_list)):
            item = node_list[i]            
            prop = item['properties']
            points = item['geometry']['coordinates']                      
            points = np.array(points)
            
            # origin 무조건 전달, 상대좌표로 변경
            points -= origin
            
            node = Node(prop['nodeid'])
            node.node_type = int(prop['nodetype']) if prop['nodetype'] else None
            node.point = points

            # node를 node_set에 포함
            node_set.nodes[node.idx] = node

        return node_set


    def __create_link_set_from_geojson(self, link_list, node_set, origin):   
        link_set = LineSet()

        for i in range(len(link_list)):
            item = link_list[i]            
            prop = item['properties']
            points = item['geometry']['coordinates']

            points = np.array(points)
            
            # origin 무조건 전달, 상대좌표로 변경
            points -= origin
            
            link = Link(points=points, idx=prop['linkid'], road_type=prop['route_id'], lazy_point_init=False)
            
            if prop['fromnode']:
                try:
                    from_node = node_set.nodes[prop['fromnode']]
                    link.set_from_node(from_node)
                except:
                    from_node = Node(prop['fromnode'])
                    from_node.point = points[0]
                    node_set.nodes[from_node.idx] = from_node
                    link.set_from_node(from_node)

            if prop['tonode']:
                try:
                    to_node = node_set.nodes[prop['tonode']]
                    link.set_to_node(to_node)
                except:
                    to_node = Node(prop['tonode'])
                    to_node.point = points[-1]
                    node_set.nodes[to_node.idx] = to_node
                    link.set_to_node(to_node)

           
            # link_type_def 추가
            link.link_type_def = 'naver'
            # link를 link_set에 포함
            link_set.lines[link.idx] = link

        return link_set

    def __create_lane_boundary_set_from_geojson(self, a1_lane, a2_stop, origin):

        lane_node_set = NodeSet()
        lane_boundary_set = LaneBoundarySet()

        for lane in a1_lane:
            lane_marking_id = lane['properties']['id']
            points = lane['geometry']['coordinates']
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

            lane_type = lane['properties']['lanecode']

            if lane_type == '1': # 중앙선
                lane_boundary.lane_type = [501]
                lane_boundary.lane_width = 0.15
                lane_boundary.dash_interval_L1 = 3
                lane_boundary.dash_interval_L2 = 3
                lane_boundary.lane_color = ['yellow']
                lane_boundary.lane_shape = ["Solid"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            elif lane_type == '2': # U턴구역선
                lane_boundary.lane_type = [502]
                lane_boundary.lane_width = 0.35 # 너비가 0.3~0.45 로 규정되어있다.
                lane_boundary.dash_interval_L1 = 0.5
                lane_boundary.dash_interval_L2 = 0.5
                lane_boundary.lane_shape = [ "Broken" ]
                lane_boundary.lane_color = ["white"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            elif lane_type == '3': # 차선
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
                lane_boundary.lane_color = ['white']
                lane_boundary.lane_shape = ["Broken"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            elif lane_type == '4': # 버스전용차선
                lane_boundary.lane_type = [504]
                lane_boundary.lane_width = 0.15 
                lane_boundary.dash_interval_L1 = 3
                lane_boundary.dash_interval_L2 = 3
                lane_boundary.lane_shape = [ "Solid" ]
                lane_boundary.lane_color = ["blue"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            elif lane_type == '5': # 길가장자리구역선
                lane_boundary.lane_type = [505]
                lane_boundary.lane_width = 0.15
                lane_boundary.dash_interval_L1 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
                lane_boundary.dash_interval_L2 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
                lane_boundary.lane_shape = [ "Solid" ]
                lane_boundary.lane_color = "white"
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            elif lane_type == '6': # 진로변경제한선
                lane_boundary.lane_type = [506]
                lane_boundary.lane_width = 0.15 #점선일 때 너비가 0.1 ~ 0.5로, 넓을 수도 있다.
                lane_boundary.dash_interval_L1 = 3
                lane_boundary.dash_interval_L2 = 3
                lane_boundary.lane_shape = [ "Solid" ]
                lane_boundary.lane_color = ["white"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)
            
            elif lane_type == '7': # 길가장자리구역선
                lane_boundary.lane_type = [505]
                lane_boundary.lane_width = 0.15
                lane_boundary.dash_interval_L1 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
                lane_boundary.dash_interval_L2 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
                lane_boundary.lane_color = ['yellow']
                lane_boundary.lane_shape = ["Solid"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            elif lane_type == '8': # 주정차금지선
                lane_boundary.lane_type = [515]
                lane_boundary.lane_width = 0.15
                lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
                lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
                lane_boundary.lane_shape = [ "Solid" ]
                lane_boundary.lane_color = ["yellow"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            elif lane_type == '9': # 주정차금지선
                lane_boundary.lane_type = [515]
                lane_boundary.lane_width = 0.15
                lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
                lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
                lane_boundary.lane_shape = [ "Solid" ]
                lane_boundary.lane_color = ["yellow"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            elif lane_type == '11': # 안전지대구역선
                lane_boundary.lane_type = [531]
                lane_boundary.lane_width = 0.15
                lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
                lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
                lane_boundary.lane_color = ['yellow']
                lane_boundary.lane_shape = ["Solid"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)
            
            elif lane_type == '12' or lane_type == '99': # 99
                lane_boundary.lane_type = [599]
                lane_boundary.lane_width = 0.15
                lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
                lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
                lane_boundary.lane_color = ['yellow']
                lane_boundary.lane_shape = ["Solid"]
                # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            else:
                raise BaseException('Unexpected lane_type = {}'.format(lane_type))

            lane_boundary.lane_type_def = 'naver'
            lane_boundary.lane_type_offset = [0]
            lane_boundary_set.lanes[lane_boundary.idx] = lane_boundary

        for lane in a2_stop:
            lane_marking_id = lane['properties']['id']
            points = lane['geometry']['coordinates']
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

            lane_boundary.lane_type = [530]
            lane_boundary.lane_width = 0.6
            lane_boundary.dash_interval_L1 = 0 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 0 # 문서에 없어 임의로 설정.
            lane_boundary.lane_color = ['white']
            lane_boundary.lane_shape = ["Solid"]

            lane_boundary.lane_type_def = 'naver'
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

            lane_boundary_set.lanes[lane_boundary.idx] = lane_boundary 

        return lane_node_set, lane_boundary_set

    def __create_singlecrosswalk_set_from_geojson(self, b2_surface_plane, origin):
        singlecrosswalk_set = SingleCrosswalkSet()

        for cw in b2_surface_plane:
            cw_id = cw['properties']['id']
            points = cw['geometry']['coordinates'][0]
            cw_type = cw['properties']['signtype']
            if cw_type == '4' or cw_type == '5' or cw_type == '6':
                points -= np.array(origin)
                crosswalk = SingleCrosswalk(points, cw_id, cw_type)
                singlecrosswalk_set.append_data(crosswalk, False)

        return singlecrosswalk_set