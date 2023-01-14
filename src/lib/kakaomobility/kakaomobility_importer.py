import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(current_path + '/../lib/common/')
import numpy as np

from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_signal
from lib.mgeo.class_defs.synced_signal_set import SyncedSignalSet
from lib.mgeo.class_defs.synced_signal import SyncedSignal
from lib.mgeo.class_defs.intersection_controller import IntersectionController
from lib.mgeo.class_defs.intersection_controller_set import IntersectionControllerSet

import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common
from pyproj import Proj
import json
import ast


"""
kakaomobility 에서 전달해준 geojson 데이터를 MGeo로 변환하기 위한 클래스

주요 기능의 input/ouput
input : GeoJSON 데이터가 포함된 경로
output: MGeo PlannerMap 클래스 인스턴스
"""
class KakaomobilityHDMapImporter:

    def import_geojson(self, iuput_folder_path):
        geojson_files = geojson_common.read_geojson_files(iuput_folder_path)[0]
        origin = geojson_common.get_first_geojson_point(geojson_files['A1_NODE']['features'])

        # GeoJSON 파일을 읽어서 traffoc sign, traffic signal 목록 생성 및 반환
        if 'A1_NODE' in geojson_files.keys():
            geojson_node = geojson_files['A1_NODE']['features']
            node_set = self.__create_node_set_from_geojson(geojson_node, origin)       
        else:
            node_set = NodeSet() # empty set 

        if 'A2_LINK' in geojson_files.keys():
            geojson_link = geojson_files['A2_LINK']['features']        
            link_set = self.__create_link_set_from_geojson(geojson_link, node_set, origin)
        else:
            link_set = LineSet() # empty set 

        if 'B2_SURFACELINEMARK' in geojson_files.keys():
            geojson_lane = geojson_files['B2_SURFACELINEMARK']['features']
            lane_node_set, lane_set = self.__create_lane_set_from_geojson(geojson_lane, origin, link_set)
        else:
            lane_node_set = NodeSet()
            lane_set = LaneBoundarySet()

        if 'C3_VEHICLEPROTECTIONSAFETY' in geojson_files.keys():
            geojson_lane = geojson_files['C3_VEHICLEPROTECTIONSAFETY']['features']
            lane_node_set, lane_set = self.__add_lane_set_from_geojson(geojson_lane, lane_node_set, lane_set, origin)
        
        if 'C1_TRAFFICLIGHT' in geojson_files.keys():
            geojson_traffic_light = geojson_files['C1_TRAFFICLIGHT']['features']
            traffic_light_set = self.__create_traffic_light_set_from_geojson(geojson_traffic_light, origin, link_set)
        else:
            traffic_light_set = SignalSet() # empty set 
            
        if 'B3_SURFACEMARK' in geojson_files.keys():
            features = geojson_files['B3_SURFACEMARK']['features']   
            sm_set, scw_set = self.__create_sm_set(features, origin)
        else:
            sm_set = SurfaceMarkingSet()
            scw_set = SingleCrosswalkSet()

        if 'C4_SPEEDBUMP' in geojson_files.keys():
            features = geojson_files['C4_SPEEDBUMP']['features']   
            sm_set = self.__create_speedbump_set(features, origin, sm_set)

        # MGeo Planner Map Instance 생성
        mgeo_planner_map = MGeo(node_set=node_set, 
                                link_set=link_set, 
                                lane_node_set=lane_node_set,
                                lane_boundary_set=lane_set,
                                light_set=traffic_light_set, 
                                sm_set = sm_set,
                                scw_set = scw_set)
        mgeo_planner_map.set_origin(origin)
        # UTM52N
        mgeo_planner_map.global_coordinate_system = Proj('+proj=utm +zone=52 +datum=WGS84 +units=m +no_defs').srs
        
        return mgeo_planner_map

    
    def __create_node_set_from_geojson(self, node_list, origin):   

        node_set = NodeSet()

        # id/ID/Id
        id_text = next((item for item in list(node_list[0]['properties'].keys()) if item.lower() == 'id'), None)
        if id_text is None:
            raise BaseException('Cannot find Node ID')

        for i in range(len(node_list)):
            item = node_list[i]            
            prop = item['properties']
            points = item['geometry']['coordinates']                      
            points = np.array(points)
            
            # origin 무조건 전달, 상대좌표로 변경
            points -= origin
            
            node = Node(prop[id_text])
            if 'NodeType' in prop:
                node.node_type = int(prop['NodeType'])
            # stop line 없음, group 있음
            # node.group = bool(prop['group'])
            # node.on_stop_line = bool(prop['StopLine'])
            node.point = points

            # node를 node_set에 포함
            node_set.nodes[node.idx] = node

        return node_set


    def __create_link_set_from_geojson(self, link_list, node_set, origin):
        link_set = LineSet()

        
        # id/ID/Id
        id_text = next((item for item in list(link_list[0]['properties'].keys()) if item.lower() == 'id'), None)
        if id_text is None:
            raise BaseException('Cannot find Link ID')


        for i in range(len(link_list)):
            item = link_list[i]            
            prop = item['properties']
            points = item['geometry']['coordinates']

            # Type이 MultiLineString 인 경우 감싸진 3번째 배열 괄호 제거
            if item['geometry']['type'] == 'MultiLineString':
                for j in points:
                    points = j

            points = np.array(points)
            
            # origin 무조건 전달, 상대좌표로 변경
            points -= origin
            
            link = Link(points=points, idx=prop[id_text], link_type=prop['LinkType'], road_type=prop['RoadType'], lazy_point_init=False)
            
            if prop['FromNodeID'] and prop['FromNodeID'] in node_set.nodes:
                link.set_from_node(node_set.nodes[prop['FromNodeID']])
            else:
                from_node = Node('{}S'.format(prop[id_text]))
                from_node.point = points[0]
                node_set.append_node(from_node)
                link.set_from_node(from_node)

            if prop['ToNodeID'] and prop['ToNodeID'] in node_set.nodes:
                link.set_to_node(node_set.nodes[prop['ToNodeID']])
            else:
                to_node = Node('{}E'.format(prop[id_text]))
                to_node.point = points[-1]
                node_set.append_node(to_node)
                link.set_to_node(to_node)

            link.set_max_speed_kph(prop['MaxSpeed'])  

            # if prop['L_LaneChan']:
            #     link.can_move_left_lane = bool(prop['L_LaneChan'])

            # if prop['R_LaneChan']:
            #     link.can_move_right_lane = bool(prop['R_LaneChan'])

            if prop['Direction']:
                if prop['Direction'] == 'ZZ':
                    link.related_signal = 'stright'
                elif prop['Direction'] == 'LL':
                    link.related_signal = 'left'
                elif prop['Direction'] == 'UU':
                    link.related_signal = 'uturn_normal'
                elif prop['Direction'] == 'RR':
                    link.related_signal = 'right_unprotected'

            if prop['RoadType']:
                link.road_type = prop['RoadType']           

            # link_type_def 추가
            link.link_type_def = prop['Maker'] 
            # node를 node_set에 포함
            link_set.lines[link.idx] = link

        # 차선변경 링크 정보설정
        self.__set_change_link(link_list, link_set)

        return link_set


    def __set_change_link(self, link_list, link_set):

        # id/ID/Id
        id_text = next((item for item in list(link_list[0]['properties'].keys()) if item.lower() == 'id'), None)
        if id_text is None:
            raise BaseException('Cannot find Link ID')

        for i in range(len(link_list)):
            item = link_list[i]            
            prop = item['properties']

            link = link_set.lines[prop[id_text]]

            if prop['L_LinkID'] and prop['L_LinkID'] in link_set.lines:
                link.lane_ch_link_left = link_set.lines[prop['L_LinkID']]
                if link.link_type not in ['1', '2', '4']:
                    link.can_move_left_lane = True

            if prop['R_LinkID'] and prop['R_LinkID'] in link_set.lines:
                link.lane_ch_link_right = link_set.lines[prop['R_LinkID']]
                if link.link_type not in ['1', '2', '4']:
                    link.can_move_right_lane = True


    def __create_traffic_light_set_from_geojson(self, signal_list, origin, link_set):
        traffic_light_set = SignalSet()

        for i in range(len(signal_list)):
            item = signal_list[i]
            prop = item['properties']
            points = item['geometry']['coordinates']
            
            points = np.array(points)
            
            # origin 무조건 전달, 상대좌표로 변경
            points -= origin
            
            signal_id = prop['ID']

            # 참조 Link 정보 설정
            link_id_list = []
            synced_traffic_light = None

            if prop['LinkID']:
                link_id_list.append(prop['LinkID'])

            traffic_light = Signal(signal_id)
            traffic_light.link_id_list = link_id_list
            traffic_light.dynamic = True
            traffic_light.orientation = '+'
            traffic_light.country = 'KR'

            # LINK ID List를 사용해서 Link 참조 List 구성
            for i in range(len(traffic_light.link_id_list)):
                if traffic_light.link_id_list[i] in link_set.lines:
                    traffic_light.link_list.append(link_set.lines[traffic_light.link_id_list[i]])
                else:
                    raise BaseException('[ERROR] Could not find link ID mapped in link set.')
        
            traffic_light.type = prop['Type']
            traffic_light.type_def = 'ngii_model2'
            edit_signal.ToMgeo_210311(traffic_light)
            traffic_light.point = points            
            traffic_light_set.signals[traffic_light.idx] = traffic_light

        return traffic_light_set

    def __create_traffic_sign_set_from_geojson(self, signal_list, origin, link_set):
        
        # LinkID/LinkIDs
        link_id_text = next((item for item in list(signal_list[0]['properties'].keys()) if 'linkid' in item.lower()), None)
        if link_id_text is None:
            raise BaseException('Cannot find LinkID')

        traffic_sign_set = SignalSet()

        for i in range(len(signal_list)):
            item = signal_list[i]
            prop = item['properties']
            points = item['geometry']['coordinates']
            
            points = np.array(points)
            
            # origin 무조건 전달, 상대좌표로 변경
            points -= origin
            
            signal_id = prop['id']

            # 참조 Link 정보 설정
            link_id_list = []
            if prop[link_id_text]:
                link_id_list.append(prop[link_id_text])

            traffic_sign = Signal(signal_id)
            traffic_sign.link_id_list = link_id_list
            traffic_sign.dynamic = True
            traffic_sign.orientation = '+'
            traffic_sign.country = 'KR'

            # LINK ID List를 사용해서 Link 참조 List 구성
            for i in range(len(traffic_sign.link_id_list)):
                if traffic_sign.link_id_list[i] in link_set.lines:
                    traffic_sign.link_list.append(link_set.lines[traffic_sign.link_id_list[i]])
                else:
                    raise BaseException('[ERROR] Could not find link ID mapped in link set.')
        
            traffic_sign.type = prop['Type']
            traffic_sign.sub_type = prop['SubType']
            traffic_sign.value = prop['Value']      
            traffic_sign.unit = prop['Unit']           
            traffic_sign.point = points            
            traffic_sign_set.signals[traffic_sign.idx] = traffic_sign

        return traffic_sign_set


    def __create_lane_set_from_geojson(self, surf_lines, origin, link_set):

        # id/ID/Id
        id_text = next((item for item in list(surf_lines[0]['properties'].keys()) if item.lower() == 'id'), None)
        if id_text is None:
            raise BaseException('Cannot find Lane boundary ID')

        lane_node_set = NodeSet()
        lane_boundary_set = LaneBoundarySet()

        for surf_line in surf_lines:
        
            lane_marking_id = surf_line['properties'][id_text]
            points = surf_line['geometry']['coordinates']
            while type(points[0][0]) == list:
                points = points[0]
            points = np.array(points)
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
            
            if surf_line['properties']['Type'] is not None:
                lane_shape = surf_line['properties']['Type'][1:3]
                lane_color = surf_line['properties']['Type'][0]

                lane_boundary.lane_shape =  _surfline_Type_code_to_str(lane_shape)
                lane_boundary.lane_color = _color_code_to_string(lane_color)
            else:
                lane_boundary.lane_shape =  ['none']
                lane_boundary.lane_color =  ['none']

            lane_boundary.lane_type_offset = [0]
            lane_boundary.lane_type_def = surf_line['properties']['Maker'] 
            
            right_link_id = surf_line['properties']['R_LinkID'] 
            if right_link_id is not None and right_link_id in link_set.lines:
                link_set.lines[right_link_id].set_lane_mark_left(lane_boundary)

            left_link_id = surf_line['properties']['L_LinkID'] 
            if left_link_id is not None and left_link_id in link_set.lines:
                link_set.lines[left_link_id].set_lane_mark_right(lane_boundary)

            on_stop_link_id = surf_line['properties']['StopLinkID']
            if on_stop_link_id in link_set.lines:
                link_set.lines[on_stop_link_id].to_node.on_stop_line = True
            
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

        return lane_node_set, lane_boundary_set

    def __add_lane_set_from_geojson(self, features, lane_node_set, lane_boundary_set, origin):

        # id/ID/Id
        id_text = next((item for item in list(features[0]['properties'].keys()) if item.lower() == 'id'), None)
        if id_text is None:
            id_text = next((item for item in list(features[0].keys()) if item.lower() == 'id'), None)
        
        if id_text is None:
            raise BaseException('Cannot find Lane boundary ID')

        for feature in features:
            
            if id_text in feature['properties'].keys():
                lane_marking_id = feature['properties'][id_text]
            else:
                lane_marking_id = feature[id_text]

            
            if feature is None:
                print(lane_marking_id)
                continue
            
            if feature['geometry'] is None:
                print(lane_marking_id, 'geometry is None')
                continue

            points = feature['geometry']['coordinates']
            while type(points[0][0]) == list:
                points = points[0]
            points = np.array(points)
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
            
            lane_boundary.lane_shape = ['Solid']
            lane_boundary.lane_color = ['Undefined']
            lane_boundary.lane_type_offset = [0]
            lane_boundary.lane_type_def = feature['properties']['Maker']

            lane_boundary.lane_type = [int(feature['properties']['Type'])]
        
            try:
                if lane_boundary.lane_type == 4:
                    # 중앙분리대
                    if feature['properties']['IsCentral'] == '1':
                        lane_boundary.lane_type = [1111]
                        lane_boundary.lane_color = ['Green']
                        lane_boundary.lane_shape =  ['Solid']
                    
                    elif feature['properties']['IsCentral'] == '0':
                        lane_boundary.lane_type = [4]
                        lane_boundary.lane_color = ['Undefined']
                        lane_boundary.lane_shape =  ['Solid']
            except:
                lane_boundary.lane_type = [4]
                lane_boundary.lane_color = ['Undefined']
                lane_boundary.lane_shape =  ['Solid']

            if lane_boundary.lane_type[0] == 99:
                if feature['properties']['Remark'] == '고속도로':
                    lane_boundary.lane_type = [9999]
                    lane_boundary.lane_color = ['Express']
                    lane_boundary.lane_shape =  ['Solid']

            lane_boundary_set.lanes[lane_boundary.idx] = lane_boundary

        return lane_node_set, lane_boundary_set


    def __create_speedbump_set(self, features, origin, sm_set):

        # id/ID/Id
        id_text = next((item for item in list(features[0]['properties'].keys()) if item.lower() == 'id'), None)
        if id_text is None:
            id_text = next((item for item in list(features[0].keys()) if item.lower() == 'id'), None)
        
        if id_text is None:
            raise BaseException('Cannot find Speedbump ID')

        for feature in features:

            if id_text in feature['properties'].keys():
                cw_id = feature['properties'][id_text]
            else:
                cw_id = feature[id_text]

            points = feature['geometry']['coordinates']
            while len(points) == 1:
                points = points[0]
            points = np.array(points)
            points -= np.array(origin)
            sb = SurfaceMarking(points=points, idx=cw_id)
            sb.type_code_def = feature['properties']['Maker']
            sb.sign_type = 'speedbump'
            sm_set.append_data(sb)
            
        return sm_set

    def __create_sm_set(self, features, origin):

        # LinkID/LinkIDs
        link_id_text = next((item for item in list(features[0]['properties'].keys()) if 'linkid' in item.lower()), None)
        if link_id_text is None:
            raise BaseException('Cannot find LinkID')

        scw_set = SingleCrosswalkSet()
        sm_set = SurfaceMarkingSet()

        for feature in features:
            sm_id = feature['properties']['ID']
            points = np.array([feature['geometry']['coordinates']])
            while len(points) == 1:
                points = points[0]
            points -= origin

            feature_type = feature['properties']['Kind']
            if feature['properties']['Kind'] in ['5321', '5322', '5323', '533', '534']:
                item = SingleCrosswalk(points=points, idx=sm_id, cw_type=feature_type)
                scw_set.append_data(item)

            else:

                item = SurfaceMarking(points=points, idx=sm_id)
                item.type_code_def = feature['properties']['Maker']
                item.type = feature['properties']['Type']
                item.sub_type = feature['properties']['Kind']
                sm_set.append_data(item)

            if link_id_text in feature['properties']:
                link_id_list = [feature['properties'][link_id_text]]
                item.link_id_list = link_id_list


        return sm_set, scw_set

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

def _surfline_Type_code_to_str(shape_code):
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



if __name__ == "__main__":
    iuput_folder_path = 'C:\\Users\\sjhan\\Downloads\\수정본'
    importer = KakaomobilityHDMapImporter()
    mgeo = importer.import_geojson(iuput_folder_path)

    mgeo.to_json('C:\\Users\\sjhan\\Downloads\\mgeo')