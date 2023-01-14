import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
import numpy as np
from lib.common.coord_trans_ll2utm import CoordTrans_LL2UTM
from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
from lib.common.polygon_util import calculate_centroid
from pyproj import Proj, Transformer

# overlapped node 제거
from lib.mgeo.utils.error_fix import search_overlapped_node, repair_overlapped_node
from lib.mgeo.edit.funcs import edit_node


class AutoEverImporter:

    trans = CoordTrans_LL2UTM(52)
    cm_to_m = 100

    def geojson_to_mgeo(self, input_folder_path):
        geojson_files, map_data = geojson_common.read_geojson_files(input_folder_path)
        # origin = self.get_origin(geojson_files)
        origin = np.array([
            339063.68,
            4125500.53,
            0.0
        ])

        lane_files = {}
        localization_files = {}
        for data in geojson_files:
            if 'lane' in data:
                lane_files[data] = geojson_files[data]
            elif 'localization' in data:
                localization_files[data] = geojson_files[data]

        road_node, road_link, lane_side, lane_link = self.lane_to_data(lane_files, origin)
        
        road_info = self.__create_road_info(road_link)

        lane_node_set, lane_set = self.__create_lane_boundary_set(lane_side, origin)
        link_set, node_set = self.__create_link_set(lane_link, origin, lane_set, road_info)


        road_sign, traffic_sign, road_mark, road_edge = self.localization_to_data(localization_files, origin)

        ts_set = self.__create_ts_set(traffic_sign, road_sign, origin)

        sm_set, scw_set = self.__create_rm_set(road_mark, origin)

        lan_node_set, lane_set = self.__create_rd_set(road_edge, lane_node_set, lane_set, origin)

        # 오버랩노드 제거
        node_nodes_of_no_use = repair_overlapped_node(search_overlapped_node(node_set, 0.1))
        edit_node.delete_nodes(node_set, node_nodes_of_no_use)
        lane_nodes_of_no_use = repair_overlapped_node(search_overlapped_node(lane_node_set, 0.1))
        edit_node.delete_nodes(lane_node_set, lane_nodes_of_no_use)


        mgeo = MGeo(node_set=node_set, link_set=link_set, lane_node_set=lane_node_set, lane_boundary_set=lane_set, sign_set=ts_set, sm_set=sm_set, scw_set=scw_set)
        mgeo.set_origin(origin)
        
        mgeo.global_coordinate_system = Proj('+proj=utm +zone=52 +ellps=WGS84 +lat_0=37.288146 +lon_0=127.116767 +units=m +no_defs').crs.srs
        
        # mgeo.global_coordinate_system = Proj('+proj=tmerc +lat_0=0 +lon_0=129 +k=0.9996 +x_0=500000 +y_0=0 +ellps=WGS84 +units=m +no_defs').crs.srs
        return mgeo

    def get_origin(self, files):
        indices = files.keys()
        first_idx = list(indices)[0]
        latlng = files[first_idx]['features'][0]['geometry']['coordinates'][0]
        east, north = self.trans.ll2utm(latlng[1], latlng[0])
        origin = np.array([east, north, latlng[2]/self.cm_to_m])
        return origin

    
    def lane_to_data(self, files, origin):
        road_node = []
        road_link = []
        lane_side = []
        lane_link = []
        for file_id in files:
            lanes = files[file_id]['features']
            for feature in lanes:
                # 'ROAD_NODE', 'ROAD_LINK', 'LANE_SIDE', 'LANE_LINK'
                idx = feature['properties']['ID']
                coor_type = feature['geometry']['type']

                if coor_type != 'LineString':
                    print(coor_type)

                split_val = idx.split('.')[0]
                if split_val == 'ROAD_NODE':
                    road_node.append(feature)
                elif split_val == 'ROAD_LINK':
                    road_link.append(feature)
                elif split_val == 'LANE_SIDE':
                    lane_side.append(feature)
                elif split_val == 'LANE_LINK':
                    lane_link.append(feature)

        return road_node, road_link, lane_side, lane_link

    def localization_to_data(self, files, origin):

        road_sign = []
        traffic_sign = []
        road_mark = []
        road_edge = []

        for file_id in files:
            localizations = files[file_id]['features']
            for feature in localizations:
                # 'ROAD_NODE', 'ROAD_LINK', 'LANE_SIDE', 'LANE_LINK'
                idx = feature['properties']['ID']

                split_val = idx.split('.')[0]
                if split_val == 'ROAD_SIGN':
                    road_sign.append(feature)
                elif split_val == 'TRAFFIC_SIGN':
                    traffic_sign.append(feature)
                elif split_val == 'ROAD_MARK':
                    road_mark.append(feature)
                elif split_val == 'ROAD_EDGE':
                    road_edge.append(feature)

        return road_sign, traffic_sign, road_mark, road_edge

    def __create_connect_info(self, features):

        connect_info = dict()

        for feature in features:
            print(feature)

    def __create_road_info(self, features):

        road_info = dict()

        for feature in features:
            road_link_id = str(feature['properties']['RL_ID'])
            is_urban = feature['properties']['IS_URBAN']
            # rl_length = feature['properties']['RL_LENGTH']

            # st_RN_id = feature['properties']['ST_RN_ID']
            # ed_RN_id = feature['properties']['ED_RN_ID']
            # st_RN_index = feature['properties']['ST_RN_INDEX']
            # ed_RN_index = feature['properties']['ED_RN_INDEX']

            # st_side = feature['properties']['ST_SIDE']
            # ed_side = feature['properties']['ED_SIDE']
            # st_angle = feature['properties']['START_ANGLE']
            # ed_angle = feature['properties']['END_ANGLE']
            # st_range = feature['properties']['ST_RANGE']
            # ed_range = feature['properties']['ED_RANGE']

            attribute_list = feature['properties']['ATTRIBUTE_LIST']

            rl_facility = None 
            rl_link_kind = None 
            rl_speed_limit = None 
            rl_link_category = None 
            rl_road_kind = None

            for attribute in attribute_list:
                # [7, 8, 9, 12, 13]
                for info in attribute['ATTR_INFO']:
                    attr_class = info['ATTR_CLASS']
                    attr_code = info['ATTR_CODE']
                    if attr_class == 7: # RL_FACILITY
                        if attr_code == 0 : rl_facility = 'normal' # 일반
                        elif attr_code == 1 : rl_facility = 'tunnel' # 터널
                        elif attr_code == 2 : rl_facility = 'underpass' # 지하차도
                        elif attr_code == 3 : rl_facility = 'Tunnel-type soundproof facilities.' # 터널형 방음시설
                    
                    elif attr_class == 8: # RL_LINK_KIND
                        if attr_code == 0 : rl_link_kind = 'normal' # 일반
                        elif attr_code == 1 : rl_link_kind = 'intersection' # 교차로
                        elif attr_code == 2 : rl_link_kind = 'roundabout' # 회전교차로
                        elif attr_code == 3 : rl_link_kind = 'u-turn' # 유턴
                        elif attr_code == 4 : rl_link_kind = 'divided road' # 분리 차로
                        elif attr_code == 5 : rl_link_kind = 'boundary' # 경계

                    elif attr_class == 9: # RL_SPEED_LIMIT
                        rl_speed_limit = attr_code

                    elif attr_class == 12: # RL_LINK_CATEGORY
                        if attr_code == 0 : rl_link_category = 'Unexamined' # 미조사
                        elif attr_code == 1 : rl_link_category = 'Default' # Default / 본선(비분리)
                        elif attr_code == 2 : rl_link_category = 'Multiply Digitized' # Multiply Digitized / 본선(분리)
                        elif attr_code == 3 : rl_link_category = 'JC' # 연결로(JC)
                        elif attr_code == 4 : rl_link_category = 'Plural Junction' # 교차로의 통로 / Plural Junction
                        elif attr_code == 5 : rl_link_category = 'IC' # 연결로 (IC)
                        elif attr_code == 6 : rl_link_category = 'Parking lot' # Parking lot
                        elif attr_code == 7 : rl_link_category = 'SA-Layer' # SA-Layer
                        elif attr_code == 8 : rl_link_category = 'Link within the complex IC' # 복합 교차점 내 링크
                        elif attr_code == 9 : rl_link_category = 'Roundabout' # 로터리 내 링크 / Roundabout

                    elif attr_class == 13: # RL_ROAD_KIND
                        if attr_code == 0 : rl_road_kind = 'normal' # 일반
                        elif attr_code == 1 : rl_road_kind = 'highway' # 고속도로
                        elif attr_code == 2 : rl_road_kind = 'city_highway' # 도시고속도로
                        elif attr_code == 3 : rl_road_kind = 'national_highway' # 국도
                        elif attr_code == 4 : rl_road_kind = 'national_local_road' # 국가지원지방도
                        elif attr_code == 5 : rl_road_kind = 'local_road' # 지방도
                        elif attr_code == 6 : rl_road_kind = 'road' # 주요도로1
                        elif attr_code == 7 : rl_road_kind = 'road' # 주요도로2
                        elif attr_code == 8 : rl_road_kind = 'road' # 주요도로3
                        elif attr_code == 9 : rl_road_kind = 'etc' # 기타도로1
                        elif attr_code == 10 : rl_road_kind = 'etc' # 기타도로2
                        elif attr_code == 11 : rl_road_kind = 'etc' # 세도로
                        elif attr_code == 12 : rl_road_kind = 'ferry_route' # 페리항로

            road_info[road_link_id] = {
                'RL_FACILITY' : rl_facility, 
                'RL_LINK_KIND' : rl_link_kind, 
                'RL_SPEED_LIMIT' : rl_speed_limit, 
                'RL_LINK_CATEGORY' : rl_link_category, 
                'RL_ROAD_KIND' : rl_road_kind }

        return road_info

    def __create_link_set(self, features, origin, lane_set, road_info):

        node_set = NodeSet()
        link_set = LineSet()
        
        link_group = dict()

        for feature in features:
            mgeo_road_id = str(feature['properties']['RL_ID'])

            left_side_seq = feature['properties']['LEFT_SIDE_SEQ']
            right_side_seq = feature['properties']['RIGHT_SIDE_SEQ']
            ll_num = feature['properties']['LL_NUM']
            
            link_id = feature['properties']['ID']
            latlng = feature['geometry']['coordinates']
            points = []
            for i in latlng:
                east, north = self.trans.ll2utm(i[1], i[0])
                point = np.array([east, north, i[2]/self.cm_to_m])
                points.append(point)
            points = np.array(points)
            points -= origin

            link = Link(idx=link_id, points=points, lazy_point_init=False)
            link.link_type_def = 'Hyundai AutoEver'
            link_set.append_line(link)

            # 양쪽 링크 설정
            if str(mgeo_road_id) not in link_group:
                link_group[str(mgeo_road_id)] = [link]
            else:
                link_group[str(mgeo_road_id)].insert(ll_num - 1, link)


            # 양쪽 차선 설정
            left_side = 'LANE_SIDE.{}_{}'.format(mgeo_road_id, left_side_seq)
            right_side = 'LANE_SIDE.{}_{}'.format(mgeo_road_id, right_side_seq)
            if left_side in lane_set.lanes:
                left_lane_mark = lane_set.lanes[left_side]
                link.set_lane_mark_left(left_lane_mark)
            if right_side in lane_set.lanes:
                right_lane_mark = lane_set.lanes[right_side]
                link.set_lane_mark_right(right_lane_mark)
            
            # ego lane 설정
            link.ego_lane = ll_num

            # from/to 설정
            from_node = Node(link_id+'S')
            from_node.point = points[0] 
            node_set.append_node(from_node)
            from_node.node_type = 'Hyundai AutoEver'

            to_node = Node(link_id+'E')
            to_node.point = points[-1] 
            node_set.append_node(to_node)
            to_node.node_type = 'Hyundai AutoEver'

            link.set_from_node(from_node)
            link.set_to_node(to_node)

            road_attri = road_info[mgeo_road_id]
            link.road_id = mgeo_road_id
            link.road_type = road_attri['RL_ROAD_KIND']
            link.set_max_speed_kph(road_attri['RL_SPEED_LIMIT'])
            link.speed_unit = 'km/h'

            attribute_list = feature['properties']['ATTRIBUTE_LIST']
            for attribute in attribute_list:
                # [3, 4, 10, 100]
                for info in attribute['ATTR_INFO']:
                    attr_class = info['ATTR_CLASS']
                    attr_code = info['ATTR_CODE']
                    if attr_class == 3: # 엑셀에 없음
                        # print('class: {}, code: {}'.format(attr_class, attr_code))
                        pass
                    elif attr_class == 4: # 엑셀에 없음
                        # print('class: {}, code: {}'.format(attr_class, attr_code))
                        pass
                    elif attr_class == 10: # ADD_INFO
                        return_type = 'ADD_INFO'
                        if attr_code == 1 : link.link_type = 'NORMAL' # 일반
                        elif attr_code == 2 : link.link_type = 'BUS' # 버스정차차로
                        elif attr_code == 3 : link.link_type = 'HIPASS'  # 하이패스
                        elif attr_code == 4 : link.link_type = 'SMART HIPASS'  # 스마트 하이패스
                        elif attr_code == 5 : link.link_type = 'TG'  # 톨게이트 일반
                    elif attr_class == 100: # CATEGORY
                        if attr_code == 0 : link.link_type = 'UNKNOWN'
                        elif attr_code == 1 : link.link_type = 'REGULAR'
                        elif attr_code == 2 : link.link_type = 'HOV'
                        elif attr_code == 3 : link.link_type = 'DRIVABLE_SHOULDER'
                        elif attr_code == 4 : link.link_type = 'BICYCLE'
                        elif attr_code == 5 : link.link_type = 'PARKING'
                        elif attr_code == 6	: link.link_type = 'REVERSIBLE'
                        elif attr_code == 7 : link.link_type = 'EXPRESS'
                        elif attr_code == 8 : link.link_type = 'ACCELERATION'
                        elif attr_code == 9 : link.link_type = 'DECELERATION'
                        elif attr_code == 10 : link.link_type = 'AUXILIARY'
                        elif attr_code == 11 : link.link_type = 'SLOW'
                        elif attr_code == 12 : link.link_type = 'PASSING'
                        elif attr_code == 13 : link.link_type = 'REGULATED_ACCESS'
                        elif attr_code == 14 : link.link_type = 'TURN'
                        elif attr_code == 15 : link.link_type = 'CENTER_TURN'
                        elif attr_code == 16 : link.link_type = 'TRUCK_PARKING'
                        elif attr_code == 17 : link.link_type = 'SHOULDER'
                        elif attr_code == 18 : link.link_type = 'VARIABLE_DRIVING'
                        elif attr_code == 19 : link.link_type = 'DRIVABLE_PARKING'
                        elif attr_code == 20 : link.link_type = 'OTHER'
        
        for idx in link_group:
            group = link_group[idx]
            if len(group) < 2:
                continue
            for i in range(len(group)):
                left_link = None
                right_link = None
                if i == 0:
                    right_link = group[i+1]
                elif i == len(group)-1:
                    left_link = group[i-1]
                else:
                    left_link = group[i-1]
                    right_link = group[i+1]

                if left_link is not None:
                    group[i].set_left_lane_change_dst_link(left_link)
                    group[i].can_move_left_lane = True
                if right_link is not None:
                    group[i].set_right_lane_change_dst_link(right_link)
                    group[i].can_move_right_lane = True
                    
        return link_set, node_set

    def __create_lane_boundary_set(self, features, origin):

        lane_node_set = NodeSet()
        lane_set = LaneBoundarySet()

        for feature in features:
            mgeo_road_id = feature['properties']['RL_ID']
            side_seq = feature['properties']['SIDE_SEQ']
            lane_id = feature['properties']['ID']

            latlng = feature['geometry']['coordinates']
            points = []
            for i in latlng:
                east, north = self.trans.ll2utm(i[1], i[0])
                point = [east, north, i[2]/self.cm_to_m]
                points.append(point)
            points = np.array(points)
            points -= origin

            lane = LaneBoundary(points=points, idx=lane_id)
            lane_set.append_line(lane)
            lane.lane_type_def = 'Hyundai AutoEver'

            from_node = Node(lane_id+'S')
            from_node.point = points[0] 
            lane_node_set.append_node(from_node)
            from_node.node_type = 'Hyundai AutoEver'

            to_node = Node(lane_id+'E')
            to_node.point = points[-1] 
            lane_node_set.append_node(to_node)
            to_node.node_type = 'Hyundai AutoEver'

            lane.set_from_node(from_node)
            lane.set_to_node(to_node)

            attribute_list = feature['properties']['ATTRIBUTE_LIST']

            for attribute in attribute_list:

                start_range = attribute['ST_RANGE']
                end_range = attribute['ED_RANGE']
                attr_Seq = attribute['ATTR_SEQ']
                lane.set_lane_type_list(start_range)

                for info in attribute['ATTR_INFO']:
                    attr_class = info['ATTR_CLASS']
                    attr_code = info['ATTR_CODE']
                    if attr_class == 1: # LINE_TYPE
                        lane.lane_type.append(attr_code)
                        # 1	    실선
                        # 2	    파선
                        # 4	    지그재그
                        # 128	연석
                        # 129	가드레일
                        # 130	중앙분리대
                        # 131	방음벽
                        # 132	벽
                        # 133	연석-화단
                        # 134	연석-펜스
                        # 135	비상대피시설
                        # 136	배리어
                        # 254	기타
                        # 255	가상선
                        # 513 -> 255 + 255(대각선) + 1 + 2
                        # [128 - 연석, 1 - 실선, 255 - 가상선, 136 - 배리어, 2 - 파선, 513 - 가상선가상선실선파선, 258 - 실선파선, 132, 135]

                        if attr_code == 2:
                            lane.lane_shape.append('Broken')
                            lane.dash_interval_L1 = 3
                            lane.dash_interval_L2 = 3
                        elif attr_code == 4:
                            lane.lane_shape.append('Zigzag')
                        elif attr_code == 3:
                            lane.lane_shape.append('Broken Solid')
                            lane.dash_interval_L1 = 3
                            lane.dash_interval_L2 = 3
                        elif attr_code == 258:
                            lane.lane_shape.append('Solid Broken')
                            lane.dash_interval_L1 = 3
                            lane.dash_interval_L2 = 3
                        elif attr_code == 513:
                            lane.lane_shape.append('Undefined Solid Broken')
                            lane.dash_interval_L1 = 3
                            lane.dash_interval_L2 = 3
                        else:
                            lane.lane_shape.append('Solid')
                    elif attr_class == 2: # LINE_COLOR
                        if attr_code == 1: # 흰색
                            lane.lane_color.append('white')
                        elif attr_code == 2: # 노란색
                            lane.lane_color.append('yellow')
                        elif attr_code == 3: # 파란색
                            lane.lane_color.append('blue')
                        elif attr_code == 4: # 붉은색
                            lane.lane_color.append('red')
                        elif attr_code == 5: # 녹색
                            lane.lane_color.append('green')
                        elif attr_code == 6: # 주황색
                            lane.lane_color.append('orange')
                        elif attr_code == 7: # 보라색
                            lane.lane_color.append('purple')
                        elif attr_code == 254: # Other
                            lane.lane_color.append('etc')
                        elif attr_code == 255: # 색상없음
                            lane.lane_color.append('undefined')
                        elif attr_code == 257: # 흰색, 흰색
                            lane.lane_color.append('undefined white white')
        return lane_node_set, lane_set

    def __create_ts_set(self, features_ts, features_rs, origin):

        ts_set = SignalSet()
        sm_set = SurfaceMarkingSet()

        for feature in features_ts:
            idx = feature['properties']['ID']

            # rs_id = feature['properties']['RS_ID']
            # rs_code = feature['properties']['RS_CODE']
            # rs_degree = feature['properties']['RS_DEGREE']

            ts_id = feature['properties']['TS_ID']
            ts_code = feature['properties']['TS_CODE']
            # 0	Unknown
            # 1	Maximum Speed Limit Sign >> 224
            # 2	Minimum Speed Limit Sign >> 225
            # 3	Warning Sign
            # 4	Stop Sign
            # 5	Yield Sign
            # 6	No Overtaking Sign
            # 7	End No Overtaking Sign
            # 8	End Restriction Sign
            # 9	Do Not Enter Sign
            # 10	No Access Sign
            # 99	Other
            ts_sub_code = feature['properties']['TS_SUB_CODE']

            # rm_id = feature['properties']['RM_ID']
            # rm_type = feature['properties']['RM_TYPE']
            # rm_id = feature['properties']['RM_SUB_TYPE']

            # re_id = feature['properties']['RE_ID']
            # re_type = feature['properties']['RE_TYPE']

            latlng = feature['geometry']['coordinates']
            east, north = self.trans.ll2utm(latlng[1], latlng[0])
            point = [east, north, latlng[2]/self.cm_to_m]
            point = np.array(point)
            point -= origin

            ts = Signal(_id=idx)
            ts.point = point
            ts.type_def = 'autoever'
            ts.orientation = '+'
            ts.dynamic = False
            ts.country = 'KR'
            ts.set_size()

            if ts_code == 1:
                ts.type = '2'
                ts.sub_type = '224'
                ts.value = ts_sub_code
            elif ts_code == 2:
                ts.type = '2'
                ts.sub_type = '225'
                ts.value = ts_sub_code

            ts_set.append_signal(ts)

    
        for feature in features_rs:
            idx = feature['properties']['ID']

            rs_id = feature['properties']['RS_ID']
            rs_code = feature['properties']['RS_CODE']
            # 0	미조사
            # 1	편지식
            # 2	문형식
            # 3	단주식
            # 4	복주식
            rs_degree = feature['properties']['RS_DEGREE']
            latlng = feature['geometry']['coordinates']
            points = []
            for i in latlng:
                east, north = self.trans.ll2utm(i[1], i[0])
                point = [east, north, i[2]/self.cm_to_m]
                points.append(point)
            points = np.array(points)
            points -= origin
            point = calculate_centroid(points)

            ts = Signal(_id=idx)
            ts.point = point
            ts.type_def = 'autoever'
            ts.orientation = '+'
            ts.dynamic = False
            ts.country = 'KR'
            ts.type = '4'

            if rs_code == 0:
                ts.sub_type = '499'
            elif rs_code == 1:
                ts.sub_type = '499'
            elif rs_code == 2:
                ts.sub_type = '499'
            elif rs_code == 3:
                ts.sub_type = '499'
            elif rs_code == 4:
                ts.sub_type = '499'

            ts_set.append_signal(ts)

        return ts_set

    def __create_rm_set(self, features_rm, origin):

        sm_set = SurfaceMarkingSet()
        scw_set = SingleCrosswalkSet()

        for feature in features_rm:
            idx = feature['properties']['ID']

            rm_id = feature['properties']['RM_ID']
            rm_type = feature['properties']['RM_TYPE']
            rm_sub_type = feature['properties']['RM_SUB_TYPE']
            
            if len(feature['geometry']['coordinates']) == 1:
                latlngs = feature['geometry']['coordinates'][0]
            else:
                latlngs = feature['geometry']['coordinates']

            points = []
            for i in latlngs:
                east, north = self.trans.ll2utm(i[1], i[0])
                point = np.array([east, north, i[2]/self.cm_to_m])
                points.append(point)
            points = np.array(points)
            points -= origin
            
            if rm_type == 1:
                rm_sub_type = '5321'
                scw = SingleCrosswalk(points=points,idx=idx,cw_type=rm_sub_type)
                scw_set.append_data(scw)

            elif rm_type == 2:
                rm_sub_type = 'speedbump'
                scw = SingleCrosswalk(points=points,idx=idx,cw_type=rm_sub_type)
                scw_set.append_data(scw)

            elif rm_type == 3:
                if rm_sub_type == 1:
                    rm_sub_type = '5371'
                elif rm_sub_type == 2:
                    rm_sub_type = '5372'
                elif rm_sub_type == 3:
                    rm_sub_type = '5373'
                elif rm_sub_type == 4:
                    rm_sub_type = '5381'
                elif rm_sub_type == 5:
                    rm_sub_type = '5382'
                elif rm_sub_type == 10:
                    rm_sub_type = '511'
                elif rm_sub_type == 12:
                    rm_sub_type = '512'
                elif rm_sub_type == 28:
                    rm_sub_type = '598'
                sm = SurfaceMarking(points=points,idx=idx)
                sm.type = "3"
                sm.sub_type = rm_sub_type
                sm.type_code_def = "hyundai"
                sm_set.append_data(sm)

            elif rm_type == 4:
                sm = SurfaceMarking(points=points,idx=idx)
                sm.type = "4"
                sm.sub_type = rm_sub_type
                sm.type_code_def = "hyundai"
                sm_set.append_data(sm)

            elif rm_type == 5:
                sm = SurfaceMarking(points=points,idx=idx)
                sm.type = "5"
                sm.sub_type = rm_sub_type
                sm.type_code_def = "hyundai"
                sm_set.append_data(sm)

        return sm_set, scw_set

    def __create_rd_set(self, features_rd, lane_node_set, lane_set, origin):

        for feature in features_rd:
            idx = feature['properties']['ID']

            re_type = feature['properties']['RE_TYPE']
            
            if len(feature['geometry']['coordinates']) == 1:
                latlngs = feature['geometry']['coordinates'][0]
            else:
                latlngs = feature['geometry']['coordinates']

            points = []
            for i in latlngs:
                east, north = self.trans.ll2utm(i[1], i[0])
                point = np.array([east, north, i[2]/self.cm_to_m])
                points.append(point)
            points = np.array(points)
            points -= origin

            lane = LaneBoundary(points=points, idx=idx)
            lane_set.append_line(lane)
            lane.lane_type_def = 'Hyundai AutoEver'

            from_node = Node(idx+'S')
            from_node.point = points[0] 
            lane_node_set.append_node(from_node)
            from_node.node_type = 'Hyundai AutoEver'

            to_node = Node(idx+'E')
            to_node.point = points[-1] 
            lane_node_set.append_node(to_node)
            to_node.node_type = 'Hyundai AutoEver'

            lane.set_from_node(from_node)
            lane.set_to_node(to_node)

            # RAD-R
            """
            Value	설명	고속	도심
                0	NULL	X	O
                1	연석	O	O
                2	가드레일	X	O
                3	중앙분리대	X	O
                4	방음벽	X	O
                5	벽	O	O
                6	터널램프	X	O
                7	차선규제봉	O	O
                8	연석-화단	X	O
                9	연석-펜스	X	O
                10	비상대피시설	O	O
                11	벽-빌딩	X	O
                12	배리어	O	O
                13	Unknown	O	O
                14	벽-빌딩1(0~4m)	X	O
                15	벽-빌딩2(4~15m)	X	O
                20	연석(주정차금지)	X	O
            """
            attr_code = 600 + re_type
            # if re_type == 0: attr_code = 600 
            # elif re_type == 1: attr_code = 601
            # elif re_type == 2: attr_code = 602
            # elif re_type == 3: attr_code = 603
            # elif re_type == 4: attr_code = 604
            # elif re_type == 5: attr_code = 605
            # elif re_type == 6: attr_code = 606
            # elif re_type == 7: attr_code = 607
            # elif re_type == 8: attr_code = 608
            # elif re_type == 9: attr_code = 609
            # elif re_type == 10: attr_code = 610
            # elif re_type == 11: attr_code = 611
            # elif re_type == 12: attr_code = 612
            # elif re_type == 13: attr_code = 613
            # elif re_type == 14: attr_code = 614
            # elif re_type == 15: attr_code = 615
            # elif re_type == 20: attr_code = 620
            lane.set_lane_type_list(0)
            lane.lane_type.append(attr_code)
            lane.lane_shape.append('Solid')
            lane.lane_color.append('undefined')

        return lane_node_set, lane_set

def import_and_save(input_path):
    
    output_path = os.path.join(input_path, 'output') 
    relative_loc = True
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    except OSError:
        print('Error: Creating directory. ' +  output_path)

    
    importer = AutoEverImporter()
    mgeo = importer.geojson_to_mgeo(input_path)
    mgeo.to_json(output_path)

if __name__ == "__main__":
    import_and_save('D:\\01.지도\\211102_현대오토에버\\rad_r')