"""
OdrLaneSection Module
"""

import os 
import sys
import numpy as np
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from lib.common.logger import Logger
import lxml.etree as etree

import mgeo_odr_converter as converter
from xodr_lane import OdrLane
from pyproj import Proj, transform
from xodr_data import OdrData
class OdrLaneSection(object):
    """
    OdrLaneSection Class
    """
    def __init__(self):
        self.lanes_L = list() 
        self.lanes_R = list() 
        self.lane_C = None

        self.sidewalk_width = None

        self.reference_line_piece = None

        # 
        self.parent_road = None

        # 
        self.s_offset = None
        self.lane_length = None

        self.vector_s_offset = list()

        # geometry
        self.init_coord = list()
        self.heading = list()
        self.arclength = list()
        self.geometry = list()
        self.geometry_u_max = list()

        self.elevation = list()
        self.elevation_soffset = list()
        self.lateral = list()

        self.lane_expand_left = 0
        self.lane_expand_right = 0
        self.lane_expand_left_slope = 0
        self.lane_expand_right_slope = 0
        self.has_lane_data = None

        # not used
        self.predecessor_id = None
        self.successor_id = None

        # odr parameter
        self.odr_param = None


    def get_lanes_L(self):
        return self.lanes_L
    

    def get_lanes_R(self):
        return self.lanes_R


    def get_lane_list_from_left_to_right(self):
        new_list = list()
        
        num = len(self.lanes_L)
        for i in range(num):
            new_list.append(self.lanes_L[num - i - 1])

        for lane in self.lanes_R:
            new_list.append(lane)

        return new_list


    def get_left_lane_links(self):
        links = []
        for lane in self.get_lanes_L():
            links.append(lane.get_link())
        return links


    def get_right_lane_links(self):
        links = []
        for lane in self.get_lanes_R():
            links.append(lane.get_link())
        return links


    def get_all_lane_links(self):
        return self.get_left_lane_links() + self.get_right_lane_links()


    def get_ref_lane(self):
        if len(self.get_lanes_R()) == 0:
            raise BaseException('Error @ get_ref_lane: self.get_lanes_R() is not initialized properly.')
        return self.get_lanes_R()[0]


    def initialize(self, reference_line_segment):
        self.parent_road = reference_line_segment.road_id
        self.set_lanes(reference_line_segment)
        self.set_lane_width_tt()


    def set_lanes(self, reference_line_segment):
        """
        본 LaneSection에서 reference line에 해당하는 링크와,
        좌우측 lane을 설정한다
        """
        self.reference_line_piece = reference_line_segment

        current_link = reference_line_segment

        # right lane의 첫번째가 reference line이 된다.
        self.add_lanes_right(current_link) # ref lane은 -1로 입력

        # 왼쪽 링크가 없을때까지 left link를 채운다
        # while (current_link.lane_ch_link_left is not None and
        #     current_link.can_move_left_lane is True):
        
        while (current_link.lane_ch_link_left is not None and
            current_link.lane_ch_link_left.road_id == current_link.road_id):
            current_link = current_link.lane_ch_link_left
            self.add_lanes_left(current_link)


        # 다시 현재 링크를 refence line으로 돌린다
        current_link = reference_line_segment

        # 오른쪽 링크가 없을때까지 right link를 채운다
        # while (current_link.lane_ch_link_right is not None and
        #     current_link.can_move_right_lane is True):  
        while (current_link.lane_ch_link_right is not None and
            current_link.lane_ch_link_right.road_id == current_link.road_id):  

            current_link = current_link.lane_ch_link_right
            self.add_lanes_right(current_link)

        # 마지막으로 center lane을 설정한다
        self.lane_C = OdrLane(link=None, idx=0, lane_section=self, lane_type='none')


    def set_lane_width_tt(self):
        if self.get_lane_num() <= 0:
            raise BaseException('Cannot set lane_width. Lanes must be set first.')

        if self.get_lane_num() == 1:
            # single lane
            lane = self.get_ref_lane()
            lane_link = lane.get_link()

            # new feature for tt eval
            # NOTE(hjp) refactor to use the __create_lane_gap_list_tt() function
            if (lane_link.lane_mark_left is not [] and lane_link.lane_mark_right is not []):
                try:
                    left = lane_link.lane_mark_left[0]
                except:
                   Logger.log_warning('Cannot find left lane markings for link {}'.format(lane_link.idx)) 
                
                try:
                    right = lane_link.lane_mark_right[0]
                except:
                    Logger.log_warning('Cannot find right lane markings for link {}'.format(lane_link.idx))
                
                try:
                    start_point_gap, end_point_gap = \
                        converter.MGeoToOdrDataConverter.get_lane_gaps(left, right)
                    lane.gap_known['start'] = start_point_gap
                    lane.gap_known['end'] = end_point_gap
                except:
                    #NOTE(CHI) lane boundary gap is 3.5 for sejong 
                    # we need to set 
                    lane.gap_known['start'] = 3.5
                    lane.gap_known['end'] = 3.5


            else:
                Logger.log_warning('Cannot find lane markings for link {}'.format(lane_link.idx))

        else:
            # multiple lanes
            lane_gaps = self.__create_lane_gap_list_tt()
            lane_list = self.get_lane_list_from_left_to_right()

            # 논리적인 오류 검사
            # lane_gaps 의 길이는 반드시 lane_num과 같아야 한다.
            # if len(lane_gaps) != self.get_lane_num():
            #     ref_lane_link_id = self.get_ref_lane().link.idx
            #     raise BaseException('Error found in LaneSection with Ref. Line Link: {} >> There seems to be a logical error here. len(lane_gaps) = {} where as self.get_lane_num() = {}'.format(ref_lane_link_id, len(lane_gaps), self.get_lane_num()))

            # # check
            # for gap in lane_gaps:
            #     if (gap['start'] is None or
            #         gap['end'] is None):
            #         Logger.log_warning('__create_lane_gap_list_tt() failed for road {}'.format(self.parent_road.road_id))

            for idx, lane in enumerate(lane_list):
                lane.gap_known['start'] = lane_gaps[idx]['start']
                lane.gap_known['end'] = lane_gaps[idx]['end']


    def set_lane_width(self):
        """
        lanes_L, lanes_R에 포함된 각 lane의 width를 설정한다.
        """

        if self.get_lane_num() <= 0:
            raise BaseException('Cannot set lane_width. lanes must be set first.')


        if self.get_lane_num() == 1:
            """ single lane인 경우, ref. line에 해당하는 link의 force_width flag가 true이면 그에 맞게 b.c.를 설정한다""" 
            # default_lane_width = self.reference_line_piece.width
            
            """ 여기 아래 부분은 예전에 사용하던 부분 """ 
            # [USER_OPTION] 
            # 차선이 1개밖에 없을 경우, 차로 폭 기본값
            # 국내 규정에선 최소 폭을 정의하고 있다. 
            # - 60 kph 미만의 도로에서 최소 3.0m 
            # - 고속도로면 최소 3.5m이다.
            # margin = 1.00 #  1.25 # 코드 상에서는 최솟값을 기준으로. 25%의 margin을 준다 >> 현재는 주지 않는 것으로 변경
            # default_lane_width = 3.5 * margin
            
            # TEMP: single lane이면 lane.gap이 없는 것으로 정의
            lane = self.get_ref_lane()
            lane_link = lane.get_link()
            if lane_link.force_width_start: 
                lane.gap['start']['L'] = 0.5 * lane_link.width_start
                lane.gap['start']['R'] = 0.5 * lane_link.width_start
            
            if lane_link.force_width_end: # 강제로 width를 설정한다
                lane.gap['end']['L'] = 0.5 * lane_link.width_end
                lane.gap['end']['R'] = 0.5 * lane_link.width_end
            # lane.gap_cannot_directly_set = True # TODO(sglee): 여기 코드 정리하기: 이 변수 필요 없을 것으로 예상됨
            # lane.gap['start']['L'] = default_lane_width / 2.0
            # lane.gap['start']['R'] = default_lane_width / 2.0
            # lane.gap['end']['L'] = default_lane_width / 2.0
            # lane.gap['end']['R'] = default_lane_width / 2.0

        else:
            """ multiple lane인 경우이다. 이 때는 각 차선 사이의 gap을 계산하고, 마지막 lane은 평균값 + margin으로 준다 """ 
            lane_gaps = self.__create_lane_gap_list()
            lane_list = self.get_lane_list_from_left_to_right()

            # 논리적인 오류 검사
            # lane_gaps 의 길이는 반드시 lane_num 보다 하나 작아야 한다.
            if len(lane_gaps) != self.get_lane_num() - 1:
                ref_lane_link_id = self.get_ref_lane().link.idx
                raise BaseException('Error found in LaneSection with Ref. Line Link: {} >> There seems to be a logical error here. len(lane_gaps) = {} where as self.get_lane_num() = {}'.format(ref_lane_link_id, len(lane_gaps), self.get_lane_num()))

            last_id = len(lane_list) - 1
            for i in range(len(lane_list)):
                lane = lane_list[i]
                
                if i == 0:
                    # 첫번째 lane을 항상 기준으로 잡고, 여기서 절반을 설정한다
                    gap_R = lane_gaps[i]

                    lane.gap['start']['R'] = gap_R['start'] / 2.0
                    lane.gap['end']['R'] = gap_R['end'] / 2.0

                    # TEMP(sglee): 데이터가 없는 왼쪽 값은 오른쪽 값을 이용하여 세팅한다
                    lane.gap['start']['L'] = lane.gap['start']['R']
                    lane.gap['end']['L'] = lane.gap['end']['R']

                elif i > 0 and i < last_id:
                    left_lane = lane_list[i - 1]
                    gap_L = lane_gaps[i - 1]
                    gap_R = lane_gaps[i]
                    
                    lane.gap['start']['L'] = gap_L['start'] - left_lane.gap['start']['R']
                    lane.gap['end']['L'] =  gap_L['end']  - left_lane.gap['end']['R']

                    # NOTE: 그 다음, 오른쪽의 gap은 현재 왼쪽 gap과 같은 값으로 설정한다.
                    #       주행 경로가 lane의 중심이 되어야하기 때문에, 왼쪽 gap과 오른쪽 gap이 같아야 한다. 
                    # 단, 이 때 gap_R 보다 이 gap 값이 작으면 논리적으로 데이터가 문제가 있다는 뜻이 된다.
                    # 예를 들면, 3개 링크가 있는데, gap이 6m, 3m이면 문제가 발생한다
                    # |            |        |
                    # |            |        | 
                    # |  <- 6m ->  | <-3m-> |
                    # 왜냐하면 첫번째 Lane에 6m / 2 => 3m를 할당하고나면,
                    # 그 다음 두번째 링크의 왼쪽에는 6 - 3 = 3m 를 할당해야 하는데, 두 번째 링크의 위치가 유지되려면,
                    # 해당 링크의 오른쪽에도 3m를 할당해야 한다.
                    # 그런데 문제는 오른쪽 링크의 갭이 겨우 3m 밖에 안 되기 때문에, 두번째 링크에 3m를 할당해주고 나면 남는 width가 전혀 없게 된다.
                    temp_gap_R_start = lane.gap['start']['L']
                    if gap_R['start'] <= temp_gap_R_start:
                        raise BaseException('Error found in Link: {} >> Unexpected lateral change in lane width. There is no gap left to assign for the next lane.'.format(lane.link.idx))

                    temp_gap_R_end = lane.gap['end']['L']
                    if gap_R['end'] <= temp_gap_R_end:
                        raise BaseException('Error found in Link: {} >> Unexpected lateral change in lane width. There is no gap left to assign for the next lane.'.format(lane.link.idx))

                    lane.gap['start']['R'] = temp_gap_R_start
                    lane.gap['end']['R'] = temp_gap_R_end

                else:
                    left_lane = lane_list[i - 1]
                    gap_L = lane_gaps[i - 1]

                    lane.gap['start']['L'] =  gap_L['start'] - left_lane.gap['start']['R']
                    lane.gap['end']['L'] =  gap_L['end']  - left_lane.gap['end']['R']

                    # TEMP(sglee): 데이터가 없는 오른쪽 값은 왼쪽 값을 이용하여 세팅한다
                    lane.gap['start']['R'] = lane.gap['start']['L']
                    lane.gap['end']['R'] = lane.gap['end']['L']
                

    def find_slope(self, lane):
        """
        차선의 시작 및 끝 간의 도로 넓이 값의 기울기를 계산한다
        """
        width_start = lane.gap[0]['start']
        width_end = lane.gap[0]['end']

        slope = (width_end - width_start) / self.lane_length

        return slope


    def __move_to_left_most(self, link):
        i = 0
        max_iter = 100
        while True:
            next_link = link.lane_ch_link_left
            
            # 다음 링크가 none이면, 현재 링크가 가장 왼쪽링크이다
            if next_link is None:
                return link

            # 다음 링크가 있으면, 현재 링크를 업데이트하고 계속 진행한다
            link = next_link
            i += 0
            if i == max_iter:
                raise BaseException('ERROR @ move_to_left_most: max_iter is reached. There should be logical error in the lane_ch_link_left assignment')
           

    def __create_lane_gap_list(self):
        lane_gap_list = []

        # 우선 가장 왼쪽 링크로 먼저 이동한다
        link = self.get_leftmost().link

        i = 0
        max_iter = 100
        while True:
            next_link = link.lane_ch_link_right
            
            # 다음 링크가 None이면, 현재 링크가 가장 가장 오른쪽 링크이다
            if next_link is None:
                break

            # 링크 시작점에서의 gap, 링크 끝에서의 gap을 계산한다
            start_point_gap, end_point_gap = converter.MGeoToOdrDataConverter.get_lane_gaps(link, next_link)

            lane_gap_list.append({
                'start': start_point_gap,
                'end': end_point_gap
            })

            # 다음 링크가 있으면, 현재 링크를 업데이트하고 계속 진행한다
            link = next_link

            # 만일 max_iter에 도달했으면, 논리적으로 무한루프가 존재한다고 가정하고 에러로 처리한다
            i += 0
            if i == max_iter:
                raise BaseException('ERROR @ create_lane_gap_list: max_iter is reached. There should be logical error in the lane_ch_link_right assignment')

        return lane_gap_list


    def __create_lane_gap_list_tt(self):
        lane_gap_list = []

        # 우선 가장 왼쪽 링크로 먼저 이동한다
        link = self.get_leftmost().link

        i = 0
        max_iter = 100
        while True:
            next_link = link.lane_ch_link_right
            
            # 현재 링크의 좌/우 lane marking을 호출
            
            if (link.lane_mark_left is not [] and link.lane_mark_right is not []):
                try:
                    left = link.lane_mark_left[0]
                except:
                   Logger.log_warning('Cannot find left lane markings for link {}'.format(link.idx)) 
                
                try:
                    right = link.lane_mark_right[0]
                except:
                    Logger.log_warning('Cannot find right lane markings for link {}'.format(link.idx))
                
            #left = link.lane_mark_left[0]
            #right = link.lane_mark_right[0]
            try:
                if (left is None or
                    right is None):
                    Logger.log_error('Lane marking missing while executing __create_lane_gap_list() for link {}'.format(link.idx))
                    raise BaseException('Lane marking missing while executing __create_lane_gap_list() for link {}'.format(link.idx))
            except:
                pass
            # 링크 시작점에서의 gap, 링크 끝에서의 gap을 계산한다
            


            try:
                start_point_gap, end_point_gap = \
                    converter.MGeoToOdrDataConverter.get_lane_gaps(left, right)      
            except:
                # NOTE(CHI) lane boundary gap is 3.5 for sejong 
                # we need to set 
                start_point_gap = 3.5
                end_point_gap = 3.5
            
            
            lane_gap_list.append({
                'start': start_point_gap,
                'end': end_point_gap
            })

            # 다음 링크가 None이면, 현재 링크가 가장 가장 오른쪽 링크이다
            if (next_link is None or
                next_link.road_id != link.road_id):
                break

            # 다음 링크가 있으면, 현재 링크를 업데이트하고 계속 진행한다
            link = next_link

            # 만일 max_iter에 도달했으면, 논리적으로 무한루프가 존재한다고 가정하고 에러로 처리한다
            i += 0
            if i == max_iter:
                raise BaseException('ERROR @ create_lane_gap_list: max_iter is reached. There should be logical error in the lane_ch_link_right assignment')

        return lane_gap_list


    def get_lane_num(self):
        return len(self.get_lanes_L()) + len(self.get_lanes_R())


    def add_lanes_left(self, link):
        idx = len(self.get_lanes_L()) + 1 # 1, 2, 3 ... (안쪽에서 바깥쪽으로)
        lane_type_odr = self.__set_lane_types(link)
        lane = OdrLane(link, idx=idx, lane_section=self, lane_type=lane_type_odr)

        # 상호 참조할 수 있게 한다
        link.odr_lane = lane
        self.get_lanes_L().append(lane)


    def add_lanes_right(self, link):
        idx = -1 * (len(self.get_lanes_R()) + 1) # -1, -2, ... (안쪽에서 바깥쪽으로)
        lane_type_odr = self.__set_lane_types(link)
        lane = OdrLane(link, idx=idx, lane_section=self, lane_type=lane_type_odr)
        
        # 상호 참조할 수 있게 한다
        link.odr_lane = lane
        self.get_lanes_R().append(lane)
    

    def get_leftmost(self):
        if len(self.get_lanes_L()) == 0:
            # ref line 이 leftmost 이다. >> reference line을 가져와야 한다
            return self.get_lanes_R()[0]
        else:
            return self.get_lanes_L()[-1]


    def get_rightmost(self):
        if len(self.get_lanes_R()) == 0:
            raise BaseException('This lane_section is not initialized properly. No lanes are set.')
        
        return self.get_lanes_R()[-1]


    def get_predecessor_road_ids(self):
        """
        현재 lane section을 구성하는 모든 lane의 from link의 road id를 반환한다
        """
        road_list = []

        for link in self.get_all_lane_links():
            for from_link in link.get_from_links():
                # 이미 추가된 road_id는 추가되지 않도록
                if from_link.road_id not in road_list:
                    road_list.append(from_link.road_id)

        return road_list


    def get_successor_road_ids(self):
        """
        현재 lane section을 구성하는 모든 lane의 to link의 road id를 반환한다
        """
        road_list = []

        for link in self.get_all_lane_links():
            for to_link in link.get_to_links():
                # 이미 추가된 road_id는 추가되지 않도록
                if to_link.road_id not in road_list:
                    road_list.append(to_link.road_id)

        return road_list


    def get_from_nodes(self):
        node_list = []

        for link in self.get_all_lane_links():
            if link.from_node not in node_list:
                if link.link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                    node_list.append(link.from_node)

        return node_list

    
    def get_end_nodes(self):
        node_list = []

        for link in self.get_all_lane_links():
            if link.to_node not in node_list:
                if link.link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                    node_list.append(link.to_node)

        return node_list


    def create_xml_string_lane_offset(self, parent, base_offset):

        xodr_lane_offset = etree.SubElement(parent, 'laneOffset')

        # 시작 지점에서의 offset : reference line의, start point의 left gap
        # 끝   지점에서의 offset : reference line의, end   point의 left gap 
        # 그 사이에서 Linear하게 동작하게 한다

        start_offset = self.get_ref_lane().gap['start']['L']
        end_offset = self.get_ref_lane().gap['end']['L']

        #start_offset = 1.7
        #end_offset = 0
        
        if start_offset is None:
            raise BaseException("Error: start_offset is None (failed to estimate gap['start']['L']) @ lane_section.get_ref_lane().link.id = {}".format(self.get_ref_lane().link.idx))
        if end_offset is None:
            raise BaseException("Error: end_offset is None (failed to estimate gap['end']['L']) @ lane_section.get_ref_lane().link.id = {}".format(self.get_ref_lane().link.idx))
        slope = (end_offset - start_offset) / self.lane_length

        xodr_lane_offset.set('s','{:.16e}'.format(base_offset))
        xodr_lane_offset.set('a','{:.16e}'.format(start_offset))
        xodr_lane_offset.set('b','{:.16e}'.format(slope))
        xodr_lane_offset.set('c','{:.16e}'.format(0))
        xodr_lane_offset.set('d','{:.16e}'.format(0))


    def create_xml_string(self, ref_line, parent, junction=None):
        xodr_lane_sctn = etree.SubElement(parent, 'laneSection')
        xodr_lane_sctn.set('s', '{:.16e}'.format(self.s_offset))
        xodr_lane_sctn.set('singleSide', 'true')
        
        # [Lane Section STEP #01] >> Left
        if len(self.get_lanes_L()) > 0:
            xodr_lane_sctn_left = etree.SubElement(xodr_lane_sctn, 'left')
            for lane in self.get_lanes_L():
                lane.create_xml_string(xodr_lane_sctn_left, ref_line)

        # [Lane Section STEP #02] >> Center
        xodr_lane_sctn_center = etree.SubElement(xodr_lane_sctn, 'center')
        self.lane_C.create_xml_string(xodr_lane_sctn_center, ref_line)

        # [Lane Section STEP #03] >> Right
        if len(self.get_lanes_R()) > 0:
            xodr_lane_sctn_right = etree.SubElement(xodr_lane_sctn, 'right')
            for lane in self.get_lanes_R():
                lane.create_xml_string(xodr_lane_sctn_right, ref_line)
        
       
        config_virtual_shoulder_flag = converter.MGeoToOdrDataConverter.get_instance().get_config('virtual_shoulder')
        if converter.MGeoToOdrDataConverter.get_instance().get_config('shoulder_width') !='':
            virtual_shoulder_width = float(converter.MGeoToOdrDataConverter.get_instance().get_config('shoulder_width'))
        if config_virtual_shoulder_flag == True:            
            
            jc_exist = len(lane.link.from_node.junctions) >0 and len(lane.link.to_node.junctions) >0
            lane_jc = False
            for road in lane.link.odr_road.get_from_roads():
                if len(road.get_to_roads())>1 and lane.link.from_node.from_links[0].lane_ch_link_right != None:
                    lane_jc = True
            
            for road in lane.link.odr_road.get_to_roads() :
                if len(road.get_from_roads())>1 and lane.link.to_node.to_links[0].lane_ch_link_right != None:
                    lane_jc = True

            if lane_jc == False:
                lane.create_xml_string_shoulder(xodr_lane_sctn_right, virtual_shoulder_width)


            
            # if len(lane.link.lane_mark_right[0].from_node.to_links) >1:    
            #     jc_links = lane.link.lane_mark_right[0].from_node.to_links
            #     try:
            #         rightmost_lane_boundary_candidate_norm = np.linalg.norm(jc_links[0].points[-1] - jc_links[0].points[0])
            #         rightmost_lane_boundary_candidate_norm_vector =(jc_links[0].points[-1] - jc_links[0].points[0])/rightmost_lane_boundary_candidate_norm
            #     except:
            #         rightmost_lane_boundary_candidate_norm = np.linalg.norm(jc_links[0].points[1] - jc_links[0].points[0])
            #         rightmost_lane_boundary_candidate_norm_vector =(jc_links[0].points[1] - jc_links[0].points[0])/rightmost_lane_boundary_candidate_norm
            #     most_right_lane_list = []
                
            #     for link in jc_links:
            #         try:
            #             jc_link = np.linalg.norm(link.points[-1] - link.points[0])
            #             jc_link =(link.points[-1] - link.points[0])/jc_link
            #         except:
            #             jc_link = np.linalg.norm(link.points[1] - link.points[0])
            #             jc_link =(link.points[1] - link.points[0])/jc_link
            #         cross_prod = np.cross(rightmost_lane_boundary_candidate_norm_vector, jc_link)
                    
            #         most_right_lane_list.append(cross_prod[2])
            #     min_value = min(most_right_lane_list)
            #     min_index = most_right_lane_list.index(min_value)
                
            #     if lane.link.lane_mark_right[0] == jc_links[min_index]:
            #         lane.create_xml_string_shoulder(xodr_lane_sctn_right, virtual_shoulder_width)

            # elif len(lane.link.lane_mark_right[-1].to_node.from_links) >1:
            #     jc_links = lane.link.lane_mark_right[0].to_node.from_links
            #     try:
            #         rightmost_lane_boundary_candidate_norm = np.linalg.norm(jc_links[0].points[0] - jc_links[0].points[-1])
            #         rightmost_lane_boundary_candidate_norm_vector =(jc_links[0].points[0] - jc_links[0].points[-1])/rightmost_lane_boundary_candidate_norm
            #     except:
            #         rightmost_lane_boundary_candidate_norm = np.linalg.norm(jc_links[0].points[-2] - jc_links[0].points[-1])
            #         rightmost_lane_boundary_candidate_norm_vector =(jc_links[0].points[-2] - jc_links[0].points[-1])/rightmost_lane_boundary_candidate_norm
            #     most_right_lane_list = []

            #     for link in jc_links:
            #         try:
            #             jc_link = np.linalg.norm(link.points[0] - link.points[-1])
            #             jc_link =(link.points[0] - link.points[-1])/jc_link
            #         except:
            #             jc_link = np.linalg.norm(link.points[-2] - link.points[-1])
            #             jc_link =(link.points[-2] - link.points[-1])/jc_link
            #         cross_prod = np.cross(rightmost_lane_boundary_candidate_norm_vector, jc_link)
            #         most_right_lane_list.append(cross_prod[2])
            #     max_value = max(most_right_lane_list)
            #     max_index = most_right_lane_list.index(max_value)
                    
            #     if lane.link.lane_mark_right[0] == jc_links[max_index]:
            #         lane.create_xml_string_shoulder(xodr_lane_sctn_right, virtual_shoulder_width)
            #     # if lane.link.lane_mark_right[0] == jc_links[-1]:
            #     #     lane.create_xml_string_shoulder(xodr_lane_sctn_right)
            
            
            # else:

            #     lane.create_xml_string_shoulder(xodr_lane_sctn_right, virtual_shoulder_width)
                

    def __set_lane_types(self, link):
        if link.link_type_def == 'TomTom_v2105a':
            
            # if link.is_exit:
            #     link_type = 'exit'
            # elif link.is_entrance:
            #     link_type = 'entry'
            if link.link_type == 'DRIVABLE_LANE':
                link_type = 'driving'
            elif link.link_type == 'NON_DRIVABLE_LANE':
                link_type = 'shoulder'
            elif link.link_type == 'EMERGENCY_LANE':
                link_type = 'stop'
            elif link.link_type == 'HOV_LANE':
                link_type = 'driving'
                link.hov = 'hov'
            elif link.link_type == 'BUS_LANE':
                link_type = 'driving'
                link.hov = 'bus'
            elif link.link_type == 'RESTRICTED_LANE':
                link_type = 'driving'
                link.hov = 'restricted' # TODO(hjpark): link to actual restriction data
            elif link.link_type == 'PARKING_LANE':
                link_type = 'parking'
            elif link.link_type == 'BICYCLE_LANE':
                link_type = 'biking'
            else:
                link_type = 'none'

        elif link.link_type_def == 'Hyundai AutoEver':
            if link.link_type == 'NORMAL':
                link_type = 'driving'
            elif link.link_type == 'REGULAR':
                link_type = 'driving'
            elif link.link_type == 'highway':
                link_type = 'driving'
            elif link.link_type == 'HOV':
                link_type = 'driving'
                link.hov = 'hov'
            else:
                link_type = 'none'    
        
        elif link.link_type_def == 'ngii_model2':
            link_type = 'driving'

        elif link.link_type_def == 'RoadRunner':
            if link.link_type == 'Driving':
                link_type = 'driving'
            elif link.link_type == 'Sidewalk':
                link_type = 'sidewalk'
            elif link.link_type == 'Shoulder':
                link_type = 'shoulder'
            elif link.link_type == 'Curb':
                link_type = 'curb'
            else:
                link_type = 'none'

        elif link.link_type_def == 'MGeo_2201a':
            if link.link_type == 'driving':
                link_type = 'driving'
            elif link.link_type == 'Sidewalk':
                link_type = 'sidewalk'
            elif link.link_type == 'Shoulder':
                link_type = 'shoulder'
            else:
                link_type = 'none'

        elif link.link_type_def == 'OpenDRIVE':
            if link.link_type == 'driving':
                link_type = 'driving'
            elif link.link_type == 'sidewalk':
                link_type = 'sidewalk'
            elif link.link_type == 'shoulder':
                link_type = 'shoulder'
            elif link.link_type == 'curb':
                link_type = 'curb'
            else:
                link_type = 'none'
        # NOTE(chi) despace 후 지우기 
        else:
            link.link_type_def = 'OpenDRIVE'
            if link.link_type == 'driving':
                link_type = 'driving'
            elif link.link_type == 'sidewalk':
                link_type = 'sidewalk'
            elif link.link_type == 'shoulder':
                link_type = 'shoulder'
            elif link.link_type == 'curb':
                link_type = 'curb'
            else:
                link_type = 'none'
            #raise BaseException('Error @ OdrLaneSection.__set_lane_types: undefined link_type_def = {}'.format(link.link_type_def))
            
        return link_type
    
    def point_to_longlat(self, point, mgeo_planner_map):
        offset = mgeo_planner_map.local_origin_in_global
        x, y, z  = point + offset
    
        proj = mgeo_planner_map.global_coordinate_system
        p = Proj(proj)
        lons, lats = p(x, y, inverse = True)
        return lons, lats

    def __create_xml_string_boundary_geometry(self, parent, boundary, mgeo_planner_map):

        lane_sctn_boundaries_boundary = etree.SubElement(parent, 'boundary')
        lane_sctn_boundaries_boundary.set('type', boundary)
        lane_sctn_boundaries_boundary_geometry = etree.SubElement(lane_sctn_boundaries_boundary, 'geometry')
        lane_sctn_boundaries_boundary_geometry_pointSet = etree.SubElement(lane_sctn_boundaries_boundary_geometry, 'pointSet')
        if boundary == 'leftBoundary':
            for leftBoundary in self.get_leftmost().link.lane_mark_left:
                for idx, point in enumerate(leftBoundary.points):
                    lons,lats = self.point_to_longlat(point, mgeo_planner_map)
                    pointSet = etree.SubElement(lane_sctn_boundaries_boundary_geometry_pointSet, 'point')
                    pointSet.set('x', '{:.16e}'.format(lons))
                    pointSet.set('y', '{:.16e}'.format(lats))
                    pointSet.set('z', '{:.16e}'.format(point[2]))



        else:
             for rightBoundary in self.get_rightmost().link.lane_mark_right:
                for idx, point in enumerate(rightBoundary.points):
                    lons,lats = self.point_to_longlat(point, mgeo_planner_map)

                    pointSet = etree.SubElement(lane_sctn_boundaries_boundary_geometry_pointSet, 'point')
                    pointSet.set('x', '{:.16e}'.format(lons))
                    pointSet.set('y', '{:.16e}'.format(lats))
                    pointSet.set('z', '{:.16e}'.format(point[2]))


    def create_xml_string_apollo(self, parent, mgeo_planner_map, junction):
        mgeo_planner_map = mgeo_planner_map
        xodr_lane_sctn = etree.SubElement(parent, 'laneSection')
        xodr_lane_sctn.set('singleSide', 'true')
        xodr_lane_sctn_boundaries = etree.SubElement(xodr_lane_sctn, 'boundaries')
        self.__create_xml_string_boundary_geometry(xodr_lane_sctn_boundaries, 'leftBoundary', mgeo_planner_map)
        self.__create_xml_string_boundary_geometry(xodr_lane_sctn_boundaries, 'rightBoundary', mgeo_planner_map)

        
        
        # [Lane Section STEP #01] >> Left
        if len(self.get_lanes_L()) > 0:
            xodr_lane_sctn_left = etree.SubElement(xodr_lane_sctn, 'left')
            for lane in self.get_lanes_L():
                lane.create_xml_string_apollo(xodr_lane_sctn_left, mgeo_planner_map, junction)

        # [Lane Section STEP #02] >> Center
        xodr_lane_sctn_center = etree.SubElement(xodr_lane_sctn, 'center')
        self.lane_C.create_xml_string_apollo(xodr_lane_sctn_center, mgeo_planner_map, junction)

        # [Lane Section STEP #03] >> Right
        if len(self.get_lanes_R()) > 0:
            xodr_lane_sctn_right = etree.SubElement(xodr_lane_sctn, 'right')
            for lane in self.get_lanes_R():
                lane.create_xml_string_apollo(xodr_lane_sctn_right, mgeo_planner_map, junction)
        
            # TODO(chi): True에 create opendrive에 shoulder 옵션 설정 필요
            config_virtual_shoulder = False
            if config_virtual_shoulder == True:
                jc_exist = len(lane.link.from_node.junctions) >0 and len(lane.link.to_node.junctions) >0
                
                if len(lane.link.lane_mark_right[0].from_node.to_links) >1:    
                    jc_links = lane.link.lane_mark_right[0].from_node.to_links
                    try:
                        rightmost_lane_boundary_candidate_norm = np.linalg.norm(jc_links[0].points[-1] - jc_links[0].points[0])
                        rightmost_lane_boundary_candidate_norm_vector =(jc_links[0].points[-1] - jc_links[0].points[0])/rightmost_lane_boundary_candidate_norm
                    except:
                        rightmost_lane_boundary_candidate_norm = np.linalg.norm(jc_links[0].points[1] - jc_links[0].points[0])
                        rightmost_lane_boundary_candidate_norm_vector =(jc_links[0].points[1] - jc_links[0].points[0])/rightmost_lane_boundary_candidate_norm
                    most_right_lane_list = []
                    
                    for link in jc_links:
                        try:
                            jc_link = np.linalg.norm(link.points[-1] - link.points[0])
                            jc_link =(link.points[-1] - link.points[0])/jc_link
                        except:
                            jc_link = np.linalg.norm(link.points[1] - link.points[0])
                            jc_link =(link.points[1] - link.points[0])/jc_link
                        cross_prod = np.cross(rightmost_lane_boundary_candidate_norm_vector, jc_link)
                        
                        most_right_lane_list.append(cross_prod[2])
                    min_value = min(most_right_lane_list)
                    min_index = most_right_lane_list.index(min_value)
                    
                    if lane.link.lane_mark_right[0] == jc_links[min_index]:
                        lane.create_xml_string_shoulder(xodr_lane_sctn_right)
                    # if lane.link.lane_mark_right[0] == jc_links[-1]:
                    #     lane.create_xml_string_shoulder(xodr_lane_sctn_right)
                elif len(lane.link.lane_mark_right[-1].to_node.from_links) >1:
                    jc_links = lane.link.lane_mark_right[0].to_node.from_links
                    try:
                        rightmost_lane_boundary_candidate_norm = np.linalg.norm(jc_links[0].points[0] - jc_links[0].points[-1])
                        rightmost_lane_boundary_candidate_norm_vector =(jc_links[0].points[0] - jc_links[0].points[-1])/rightmost_lane_boundary_candidate_norm
                    except:
                        rightmost_lane_boundary_candidate_norm = np.linalg.norm(jc_links[0].points[-2] - jc_links[0].points[-1])
                        rightmost_lane_boundary_candidate_norm_vector =(jc_links[0].points[-2] - jc_links[0].points[-1])/rightmost_lane_boundary_candidate_norm
                    most_right_lane_list = []

                    for link in jc_links:
                        try:
                            jc_link = np.linalg.norm(link.points[0] - link.points[-1])
                            jc_link =(link.points[0] - link.points[-1])/jc_link
                        except:
                            jc_link = np.linalg.norm(link.points[-2] - link.points[-1])
                            jc_link =(link.points[-2] - link.points[-1])/jc_link
                        cross_prod = np.cross(rightmost_lane_boundary_candidate_norm_vector, jc_link)
                        most_right_lane_list.append(cross_prod[2])
                    max_value = max(most_right_lane_list)
                    max_index = most_right_lane_list.index(max_value)
                        
                    if lane.link.lane_mark_right[0] == jc_links[max_index]:
                        lane.create_xml_string_shoulder(xodr_lane_sctn_right)
                    # if lane.link.lane_mark_right[0] == jc_links[-1]:
                    #     lane.create_xml_string_shoulder(xodr_lane_sctn_right)
                else:
                    lane.create_xml_string_shoulder(xodr_lane_sctn_right)
    # def create_xml_string(self, parent, junction=None):
    #     left_expanding = (self.lane_expand_left_slope > 0)
    #     right_expanding = (self.lane_expand_right_slope > 0)
    #     left_contracting = (self.lane_expand_left_slope < 0)
    #     right_contracting = (self.lane_expand_right_slope < 0)
    #     left_lane_count = len(self.get_lanes_L())
    #     right_lane_count = len(self.get_lanes_R())


    #     xodr_lane_sctn = etree.SubElement(parent, 'laneSection')
    #     xodr_lane_sctn.set('s', '{:.16e}'.format(self.s_offset))
    #     xodr_lane_sctn.set('singleSide', 'true')
        
    #     # [Lane Section STEP #01] >> Left 
    #     xodr_lane_sctn_left = etree.SubElement(xodr_lane_sctn, 'left')
    #     for lane_num, lane in enumerate(self.get_lanes_L()):
    #         lane_idx = lane_num+1
    #         xodr_l_lane = self.__create_xml_string_lane_header(xodr_lane_sctn_left, lane_idx, 'driving')

    #         slope = self.find_slope(lane)

    #         self.__create_xml_string_lane_access(xodr_l_lane, lane)
    #         self.__create_xml_string_lane_link(xodr_l_lane, lane)
    #         self.__create_xml_string_lane_width(xodr_l_lane, lane, slope=slope)
    #         self.__create_xml_string_lane_width(xodr_l_lane, lane)
    #         self.__create_xml_string_road_mark(xodr_l_lane, lane_change='both')


    #     if left_expanding == True:
    #         if left_lane_count == 0:
    #             lane_idx = 1
    #             xodr_l_lane = self.__create_xml_string_lane_header(xodr_lane_sctn_left, lane_idx, 'driving')

    #             # TODO(sglee): road mark string
    #             # width가 여러개 붙을 것 같은데, width 중간에 roadMark를 넣는 것 보단 앞으로 빼는게 낫겠다
    #             self.__create_xml_string_road_mark(xodr_l_lane, lane_change='both')

    #             xodr_l_lane_width = etree.SubElement(xodr_l_lane, 'width')
    #             xodr_l_lane_width.set('sOffset', '{:.16e}'.format(0))
    #             xodr_l_lane_width.set('a', '{:.16e}'.format(0))
    #             xodr_l_lane_width.set('b', '{:.16e}'.format(0))
    #             xodr_l_lane_width.set('c', '{:.16e}'.format(0))
    #             xodr_l_lane_width.set('d', '{:.16e}'.format(0))
                
    #         xodr_l_lane_width = etree.SubElement(xodr_l_lane, 'width')
    #         xodr_l_lane_width.set('sOffset', '{:.16e}'.format(self.lane_expand_left))
    #         xodr_l_lane_width.set('a', '{:.16e}'.format(self.lane_expand_left_slope))
    #         xodr_l_lane_width.set('b', '{:.16e}'.format(0))
    #         xodr_l_lane_width.set('c', '{:.16e}'.format(0))
    #         xodr_l_lane_width.set('d', '{:.16e}'.format(0))


    #     # [Lane Section STEP #02] >> Center
    #     xodr_lane_sctn_center = etree.SubElement(xodr_lane_sctn, 'center')
    #     lane_idx = 0
    #     xodr_c_lane = self.__create_xml_string_lane_header(xodr_lane_sctn_center, lane_idx, 'none')
    #     self.__create_xml_string_road_mark(xodr_c_lane, lane_change='none')


    #     # [Lane Section STEP #03] >> Right
    #     xodr_lane_sctn_right = etree.SubElement(xodr_lane_sctn, 'right')
    #     for lane_num, lane in enumerate(self.get_lanes_R()):
    #         lane_idx = -1 * (lane_num + 1)
    #         xodr_r_lane = self.__create_xml_string_lane_header(xodr_lane_sctn_right, lane_idx, 'driving')
            
    #         slope = self.find_slope(lane)
            
    #         self.__create_xml_string_lane_access(xodr_r_lane, lane)
    #         self.__create_xml_string_lane_link(xodr_r_lane, lane)

    #         right_s_offset = 0
            
    #         if (right_contracting == True
    #             and lane_num+1 == right_lane_count):
    #             right_s_offset = self.lane_expand_right

    #             xodr_r_lane_width = etree.SubElement(xodr_r_lane, 'width')
    #             xodr_r_lane_width.set('sOffset', '{:.16e}'.format(0))
    #             xodr_r_lane_width.set('a', '{:.16e}'.format(self.lane_expand_right_slope*(-1)))
    #             xodr_r_lane_width.set('b', '{:.16e}'.format(0))
    #             xodr_r_lane_width.set('c', '{:.16e}'.format(0))
    #             xodr_r_lane_width.set('d', '{:.16e}'.format(0))
    #             # user = etree.SubElement(xodr_r_lane, 'userData')
    #             # user.set('contract', 'true')

    #         xodr_r_lane_width = etree.SubElement(xodr_r_lane, 'width')
    #         xodr_r_lane_width.set('sOffset', '{:.16e}'.format(right_s_offset))
    #         xodr_r_lane_width.set('a', '{:.16e}'.format(lane.gap[0]['start']))
    #         xodr_r_lane_width.set('b', '{:.16e}'.format(slope))
    #         xodr_r_lane_width.set('c', '{:.16e}'.format(0))
    #         xodr_r_lane_width.set('d', '{:.16e}'.format(0))
    #         xodr_r_lane_width = etree.SubElement(xodr_r_lane, 'width')
    #         xodr_r_lane_width.set('sOffset', '{:.16e}'.format(self.lane_length))
    #         xodr_r_lane_width.set('a', '{:.16e}'.format(lane.gap[0]['end']))
    #         xodr_r_lane_width.set('b', '{:.16e}'.format(0))
    #         xodr_r_lane_width.set('c', '{:.16e}'.format(0))
    #         xodr_r_lane_width.set('d', '{:.16e}'.format(0))

    #         self.__create_xml_string_road_mark(xodr_r_lane, lane_change='both')

    #     # REIVEW(sglee): indentation 체크 필요 (한 단계 안 들어가도 되는건가?)
    #     # 어차피 right expanding 이면, 마지막 index에 있을 것이므로 이렇게 처리한 것 같은데..
    #     # 안으로 넣어야 겠다
    #     if right_expanding == True:
    #         xodr_r_lane_width = etree.SubElement(xodr_r_lane, 'width')
    #         xodr_r_lane_width.set('sOffset', '{:.16e}'.format(self.lane_expand_right))
    #         xodr_r_lane_width.set('a', '{:.16e}'.format(self.lane_expand_right_slope))
    #         xodr_r_lane_width.set('b', '{:.16e}'.format(0))
    #         xodr_r_lane_width.set('c', '{:.16e}'.format(0))
    #         xodr_r_lane_width.set('d', '{:.16e}'.format(0))

    #         self.__create_xml_string_road_mark(xodr_r_lane, lane_change='both')

    #     # 0.123456
    #     if self.sidewalk_width is not None and junction is None:
    #         lane_idx = -1 * (len(self.get_lanes_R()) + 1)
    #         xodr_r_sidewalk = self.__create_xml_string_lane_header(xodr_lane_sctn_right, lane_idx, 'sidewalk')

    #         xodr_r_sidewalk_link = etree.SubElement(xodr_r_sidewalk, 'link')
            
    #         xodr_r_sidewalk_width = etree.SubElement(xodr_r_sidewalk, 'width')
    #         xodr_r_sidewalk_width.set('sOffset', '{:.16e}'.format(0))
    #         xodr_r_sidewalk_width.set('a', '{:.16e}'.format(self.sidewalk_width))
    #         xodr_r_sidewalk_width.set('b', '{:.16e}'.format(0))
    #         xodr_r_sidewalk_width.set('c', '{:.16e}'.format(0))
    #         xodr_r_sidewalk_width.set('d', '{:.16e}'.format(0))
                
    #         self.__create_xml_string_road_mark(xodr_r_sidewalk, lane_change='none')






    