import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import numpy as np

from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.common.logger import Logger

"""
CODE42에서 전달해준 SHP, geojson 데이터를 MGeo로 변환하기 위한 클래스

주요 기능의 input/ouput
input : CODE42 SHP 또는 GeoJSON 데이터가 포함된 경로
output: MGeo PlannerMap 클래스 인스턴스
"""
class HDMap42dotImporter:

    def sdx_filename_to_key(self, filename):
        if 'node' in filename:
            return 'node'

        elif 'link' in filename:
            return 'link'

        elif ('traffic_sign' in filename) and ('traffic_signal' not in filename):
            # 파일 이름이 traffic_signal 인 경우, [traffic_sign in filename] 부분이 True가 되므로
            # traffic_sign 인지를 정확히 체크하려면, traffic_signal은 아님까지 확인해야 한다
            return 'traffic_sign'

        elif 'traffic_signal' in filename:
            return 'traffic_signal'

        else:
            Logger.log_warning('Unexpected filename ({}) This data may not be imported correctly'.format(filename))
            return filename
    

    def import_shp_geojson(self, iuput_folder_path):
        # SHP 파일 읽기
        shp_data, shp_files = shp_common.read_shp_files(iuput_folder_path, filename_to_key_func=self.sdx_filename_to_key)
        geojson_data, geojson_files = geojson_common.read_geojson_files(iuput_folder_path, filename_to_key_func=self.sdx_filename_to_key)
        # shp_data, shp_files = shp_common.read_shp_files(iuput_folder_path)
        # geojson_data, geojson_files = geojson_common.read_geojson_files(iuput_folder_path)

        if 'node' not in shp_data.keys():
            raise BaseException('Invalid data. node.shp, node.dbf must be provided.')
        
        if 'link' not in shp_data.keys():
            raise BaseException('Invalid data. link.shp, link.dbf must be provided.')

        # Origin 설정
        origin = shp_common.get_first_shp_point(shp_data['node'])
        origin = np.array(origin)

        # 각 항목 별 객체 할당
        shp_node = shp_data['node']
        shp_link = shp_data['link']
        
        # Node, Link 목록 생성
        node_set, junction_set = self.__create_node_and_jucntion_set_from_shp(shp_node, origin)
        link_set = self.__create_link_set_from_shp(shp_link, origin, node_set)        
        # link_set = self.__set_all_left_right_links(link_set)
        
        # GeoJSON 파일을 읽어서 traffoc sign, traffic signal 목록 생성 및 반환
        if 'traffic_sign' in geojson_data.keys():
            geojson_traffic_sign = geojson_data['traffic_sign']['features']
            traffic_sign_set = self.__create_traffic_sign_set_from_geojson(geojson_traffic_sign, origin, link_set)
        else:
            traffic_sign_set = SignalSet() # empty set 

        if 'traffic_signal' in geojson_data.keys():
            geojson_traffic_light = geojson_data['traffic_signal']['features']        
            traffic_light_set = self.__create_traffic_light_set_from_geojson(geojson_traffic_light, origin, link_set)
        else:
            traffic_light_set = SignalSet() # empty set 

        # MGeo Planner Map Instance 생성
        mgeo_planner_map = MGeo(
            node_set=node_set, 
            link_set=link_set,
            junction_set=junction_set,
            sign_set=traffic_sign_set,
            light_set=traffic_light_set)

        # NOTE: project 파일 node.prj, link.prj 파일은 같다고 가정하여, 하나만 읽는다.
        prj_file = shp_files['node'] + '.prj'
        mgeo_planner_map.set_coordinate_system_from_prj_file(prj_file)
        mgeo_planner_map.set_origin(origin)

        return mgeo_planner_map


    def import_shp_geojson_legacy(self, iuput_folder_path):
        # SHP 파일 읽기
        shp_data, shp_files = shp_common.read_shp_files(iuput_folder_path, filename_to_key_func=self.sdx_filename_to_key)
        geojson_data, geojson_files = geojson_common.read_geojson_files(iuput_folder_path, filename_to_key_func=self.sdx_filename_to_key)
        # shp_data, shp_files = shp_common.read_shp_files(iuput_folder_path)
        # geojson_data, geojson_files = geojson_common.read_geojson_files(iuput_folder_path)

        if 'node' not in shp_data.keys():
            raise BaseException('Invalid data. node.shp, node.dbf must be provided.')
        
        if 'link' not in shp_data.keys():
            raise BaseException('Invalid data. link.shp, link.dbf must be provided.')

        # Origin 설정
        origin = shp_common.get_first_shp_point(shp_data['node'])
        origin = np.array(origin)

        # 각 항목 별 객체 할당
        shp_node = shp_data['node']
        shp_link = shp_data['link']
        
        # Node, Link 목록 생성
        node_set, junction_set = self.__create_node_and_jucntion_set_from_shp(shp_node, origin)
        link_set = self.__create_link_set_from_shp_legacy(shp_link, origin, node_set)        
        link_set = self.__set_all_left_right_links(link_set)
        
        # GeoJSON 파일을 읽어서 traffoc sign, traffic signal 목록 생성 및 반환
        if 'traffic_sign' in geojson_data.keys():
            geojson_traffic_sign = geojson_data['traffic_sign']['features']
            traffic_sign_set = self.__create_traffic_sign_set_from_geojson(geojson_traffic_sign, origin, link_set)
        else:
            traffic_sign_set = SignalSet() # empty set 

        if 'traffic_signal' in geojson_data.keys():
            geojson_traffic_light = geojson_data['traffic_signal']['features']        
            traffic_light_set = self.__create_traffic_light_set_from_geojson(geojson_traffic_light, origin, link_set)
        else:
            traffic_light_set = SignalSet() # empty set 

        # MGeo Planner Map Instance 생성
        mgeo_planner_map = MGeo(
            node_set = node_set,
            link_set = link_set,
            junction_set = junction_set,
            sign_set = traffic_sign_set,
            light_set = traffic_light_set)

        # NOTE: project 파일 node.prj, link.prj 파일은 같다고 가정하여, 하나만 읽는다.
        prj_file = shp_files['node'] + '.prj'
        mgeo_planner_map.set_coordinate_system_from_prj_file(prj_file)
        mgeo_planner_map.set_origin(origin)

        return mgeo_planner_map


    def __create_traffic_sign_set_from_geojson(self, sign_list, origin, link_set):   
        traffic_sign_set = SignalSet()

        for i in range(len(sign_list)):
            item = sign_list[i]
            prop = item['properties']
            points = item['geometry']['coordinates']
            
            if len(points) == 2:
                # z축 값이 없울 때 임의로 0 추가 
                points.append(0)
            points = np.array(points)
            
            # origin 무조건 전달, 상대좌표로 변경
            points -= origin
            
            # id는 모두 string으로 변경
            sign_id = to_str_if_int(prop['featureId'])
            link_id_list = to_str_if_int(prop['refLaneIds'] )

            traffic_sign = Signal(sign_id)
            traffic_sign.link_id_list = link_id_list
            traffic_sign.dynamic = False
            traffic_sign.orientation = '+'
            traffic_sign.country = 'KR'

            # LINK ID List를 사용해서 Link 참조 List 구성
            for i in range(len(traffic_sign.link_id_list)):
                if traffic_sign.link_id_list[i] in link_set.lines:
                    traffic_sign.link_list.append(link_set.lines[traffic_sign.link_id_list[i]])
                else:
                    raise BaseException('[ERROR] Could not find link ID mapped in link set.')
        
            for i in range(len(traffic_sign.link_list)):
                if traffic_sign.road_id == None :
                    traffic_sign.road_id = traffic_sign.link_list[i].road_id
                else :
                    # Signal이 참조하고 있는 lane들이 서로 다른 road id를 가진 경우 예외 발생
                    if traffic_sign.road_id != traffic_sign.link_list[i].road_id :
                        raise BaseException('[ERROR] The lanes referenced by signal have different road id.')

            traffic_sign.type = prop['code']
            traffic_sign.sub_type = prop['signType']

            # 사이즈 설정
            # type, sub_type 값을 설정한 후 호출해야 함
            traffic_sign.set_size()

            # 최고속도제한 규제표지
            if traffic_sign.type == 2 and traffic_sign.sub_type == 224 and traffic_sign.link_list.__len__ > 0  :
                traffic_sign.value = traffic_sign.link_list[traffic_sign.link_id_list[0]].max_speed_kph
            # 최저속도제한 규제표지
            elif traffic_sign.type == 2 and traffic_sign.sub_type == 225 and traffic_sign.link_list.__len__ > 0 :
                traffic_sign.value = traffic_sign.link_list[traffic_sign.link_id_list[0]].min_speed_kph
                
            traffic_sign.point = points
            
            traffic_sign_set.signals[traffic_sign.idx] = traffic_sign

        return traffic_sign_set


    def __create_traffic_light_set_from_geojson(self, signal_list, origin, link_set):
        traffic_light_set = SignalSet()

        for i in range(len(signal_list)):
            item = signal_list[i]
            prop = item['properties']
            points = item['geometry']['coordinates']
            
            if len(points) == 2:
                # z축 값이 없울 때 임의로 0 추가 
                points.append(0)
            points = np.array(points)
            
            # origin 무조건 전달, 상대좌표로 변경
            points -= origin

            signal_id = to_str_if_int(prop['featureId'])
            link_id_list = to_str_if_int(prop['refLaneIds'])

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
        
            for i in range(len(traffic_light.link_list)):
                if traffic_light.road_id == None :
                    traffic_light.road_id = traffic_light.link_list[i].road_id
                else :
                    # Signal이 참조하고 있는 lane들이 서로 다른 road id를 가진 경우 예외 발생
                    if traffic_light.road_id != traffic_light.link_list[i].road_id :
                        raise BaseException('[ERROR] The lanes referenced by signal have different road id.')      

            traffic_light.type = prop['code']
            traffic_light.sub_type = prop['signType']

            # 사이즈 설정
            # type, sub_type 값을 설정한 후 호출해야 함
            traffic_light.set_size()

            traffic_light.point = points
            
            traffic_light_set.signals[traffic_light.idx] = traffic_light

        return traffic_light_set


    def __create_node_and_jucntion_set_from_shp(self, sf, origin):
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
            node_id = to_str_if_int(dbf_rec['nodeId'])
            node = Node(node_id)
            node.point = shp_rec.points[0]

            # node를 node_set에 포함
            node_set.nodes[node.idx] = node

        return node_set, junction_set


    def __create_link_set_from_shp(self, sf, origin, node_set):
        line_set = LineSet()

        shapes = sf.shapes()
        records  = sf.records()
        fields = sf.fields

        laneSectionSets = dict()

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

            # id가 int로 해석되는 경우 string으로 변경 
            link_id = to_str_if_int(dbf_rec['laneId'])
            from_node_id = to_str_if_int(dbf_rec['fromNode'])
            to_node_id = to_str_if_int(dbf_rec['toNode'])
            road_id = to_str_if_int(dbf_rec['roadId'])
            section_id = to_str_if_int(dbf_rec['sectionId'])
            ego_lane = int(dbf_rec['egoLane'])

            # 현재는 전부 바로 point가 init되는 Link를 생성
            link = Link(points=shp_rec.points, idx=link_id, lazy_point_init=False)

            from_node = node_set.nodes[from_node_id]
            to_node = node_set.nodes[to_node_id]

            link.road_id = road_id
            link.ego_lane = ego_lane

            if dbf_rec['hov'] == 1:
                link.hov = True
            else:
                link.hov = False

            # 양 옆 차선 속성도 dbf 데이터로부터 획득
            link.lane_change_dir = dbf_rec['laneChange']

            link.set_from_node(from_node)
            link.set_to_node(to_node)
            
            # link_type_def 추가
            link.link_type_def = '42dot'

            line_set.lines[link.idx] = link

            """같은 lane Section을 묶는 dict 구조에 입력"""
            # 우선 key가 있는지 확인. 없으면 내부에 새로운 구조체 생성
            if section_id not in laneSectionSets.keys():
                laneSectionSets[section_id] = dict() # 여기 내부에 다시 egoLane 값을 key로하여 추가한다
            
            # 오류 검사: 같은 laneSection을 갖고, 같은 egoLane 값을 갖는 lane이 있는지 체크 (sdx 데이터에 있는 오류)
            if ego_lane in laneSectionSets[section_id].keys(): 
                existing_link = laneSectionSets[section_id][ego_lane]
                raise BaseException('Logical error in the sdx data: link id={} and id={} has same sectionId={} and egoLane={} value'.format(
                    existing_link.idx, link.idx, section_id, ego_lane))
    
            laneSectionSets[section_id][ego_lane] = link

        for lane_section_id, lane_section_links in laneSectionSets.items():
            # lane 수가 1인 lane_section은 그냥 넘어가면 된다
            if len(lane_section_links.keys()) == 1:
                continue
            
            for key in sorted(lane_section_links.keys()):
                current_link = lane_section_links[key]
                # print('laneSection: {}, key: {}, link id: {}, ego_lane: {}'.format(lane_section_id, key, current_link.idx, current_link.ego_lane))
            
                if key == 1:
                    # 첫번째의 경우는 right link만 설정하면 된다
                    right_link_key = key + 1
                    if right_link_key not in lane_section_links.keys():
                        raise BaseException('No link with ego_lane={} right to the link={} (ego_lane={})'.format(right_link_key, current_link.idx, current_link.ego_lane))
                    right_link = lane_section_links[right_link_key]
                    current_link.set_right_lane_change_dst_link(right_link)
                    
                    current_link.can_move_right_lane = True
                    
                elif key == sorted(lane_section_links.keys())[-1]:
                    # 마지막인 경우는 left link만 설정하면 된다
                    left_link_key = key - 1
                    if left_link_key not in lane_section_links.keys():
                        raise BaseException('No link with ego_lane={} left to the link={} (ego_lane={})'.format(left_link_key, current_link.idx, current_link.ego_lane))
                    left_link = lane_section_links[left_link_key]
                    current_link.set_left_lane_change_dst_link(left_link)
                    
                    current_link.can_move_left_lane = True
                    
                else:
                    # 그 밖의 경우는 left, right 모두 설정
                    left_link_key = key - 1
                    if left_link_key not in lane_section_links.keys():
                        raise BaseException('No link with ego_lane={} left to the link={} (ego_lane={})'.format(left_link_key, current_link.idx, current_link.ego_lane))
                    left_link = lane_section_links[left_link_key]
                    current_link.set_left_lane_change_dst_link(left_link)
                    
                    right_link_key = key + 1
                    if right_link_key not in lane_section_links.keys():
                        raise BaseException('No link with ego_lane={} right to the link={} (ego_lane={})'.format(right_link_key, current_link.idx, current_link.ego_lane))
                    right_link = lane_section_links[right_link_key]
                    current_link.set_right_lane_change_dst_link(right_link)

                    current_link.can_move_left_lane = True
                    current_link.can_move_right_lane = True        

        return line_set


    def __create_link_set_from_shp_legacy(self, sf, origin, node_set):
        line_set = LineSet()

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

            # id가 int로 해석되는 경우 string으로 변경 
            link_id = to_str_if_int(dbf_rec['laneId'])
            from_node_id = to_str_if_int(dbf_rec['fromNode'])
            to_node_id = to_str_if_int(dbf_rec['toNode'])
            road_id = to_str_if_int(dbf_rec['roadId'])

            # 현재는 전부 바로 point가 init되는 Link를 생성
            link = Link(points=shp_rec.points, idx=link_id, lazy_point_init=False)

            from_node = node_set.nodes[from_node_id]
            to_node = node_set.nodes[to_node_id]

            link.road_id = road_id
            link.ego_lane = dbf_rec['egoLane']

            if dbf_rec['hov'] == 1:
                link.hov = True
            else:
                link.hov = False

            # 양옆 차선 속성도 dbf 데이터로부터 획득
            link.lane_change_dir = dbf_rec['laneChange']

            link.set_from_node(from_node)
            link.set_to_node(to_node)
            line_set.lines[link.idx] = link

        return line_set


    def __set_all_left_right_links(self, link_set):
        '''
        author: HJP
        Link 객체의 좌/우 접한 차선 정보를 저장 가능한 self.lane_ch_link_left(or right)
        self.lane_ch_link_left(or right) 변수에 할당할 Link를 검색 후 저장
        '''
        for select_link in link_set.lines.values():

            selected_link_road = select_link.road_id
            selected_link_ego = select_link.ego_lane
            lane_left = select_link.lane_ch_link_left
            lane_right = select_link.lane_ch_link_right

            matched_list = list()
            
            # check lane id format for select_link
            lane_id = select_link.idx
            init_lane = lane_id[(len(lane_id)-3):len(lane_id)]
            init_lane = int(init_lane)
            init_lane = init_lane - (init_lane % 100)
            init_lane = str(init_lane)
            # NOTE: Designed to be foolproof, provided that the source data has properly
            # sequenced lane IDs (i.e. no omitted series like [101, 102, 104, 105])
            # and sequential egolane ids

            result = 0

            while result is not None:
                # init_lane 이 interger 였으면 그냥, 아래와 같이 계산했을 부분
                # init_lane += 1
                init_lane = str(int(init_lane) + 1) 
                
                leading_zero_id = '0{}'.format(init_lane)
                concat_lane_id = str(selected_link_road) + leading_zero_id
                # search_lane_id = int(concat_lane_id)
                result = link_set.lines.get(concat_lane_id)
                if result is not None:
                    matched_list.append(result)

            for matched_lane in matched_list:
                if matched_lane.ego_lane == selected_link_ego - 1:
                    select_link.set_left_lane_change_dst_link(matched_lane)
                    if select_link.link_type in ['1', '2', '3']:
                        select_link.can_move_left_lane = False
                    else:
                        select_link.can_move_left_lane = True
                elif matched_lane.ego_lane == selected_link_ego + 1:
                    select_link.set_right_lane_change_dst_link(matched_lane)
                    if select_link.link_type in ['1', '2', '3']:
                        select_link.can_move_right_lane = False
                    else:
                        select_link.can_move_right_lane = True

        return link_set


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

    