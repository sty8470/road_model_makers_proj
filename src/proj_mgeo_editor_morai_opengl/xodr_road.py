"""
OdrRoad Module
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import numpy as np 
from lib.mgeo.class_defs import Link
from lib.mgeo.edit.funcs import edit_link
from lib.common.logger import Logger
from xodr_lane_section import OdrLaneSection
from xodr_signal import OdrSignal
import mgeo_odr_converter as converter
import lxml.etree as etree
from collections import OrderedDict
# from mgeo_odr_converter import MGeoToOdrDataConverter

class OdrRoad(object):
    """
    Open Drive의 Road 정보를 담고 있는 클래스
    """
    def __init__(self, num_id, road_id, road_type='', country='', traffic_dir='', superelevation=''):
        """
        초기화 함수
        """
        self.road_id = road_id
        self.id = num_id
        self.road_length = None
        self.road_type = road_type
        self.country = country
        self.traffic_dir = traffic_dir
        self.superelevation = superelevation
        if self.road_type == '':
            Logger.log_warning('An empty string is passed for the road_type (road_id: {})'.format(road_id))
        if self.country == '':
            Logger.log_warning('An empty string is passed for the country (road_id: {})'.format(road_id))
        if self.traffic_dir == '':
            Logger.log_warning('An empty string is passed for the traffic_dir (road_id: {})'.format(road_id))
        elif self.traffic_dir not in ['RHT', 'LHT']:
            Logger.log_warning('An Unexpected string is passed for the traffic_dir: {} (Either RHT or LHT should be used.) (road_id: {})'.format(traffic_dir, road_id))

        self.junction = None

        self.predecessor_id = None
        self.is_pre_junction = None
        self.successor_id = None
        self.is_suc_junction = None
        self.left_expand_lane = False
        self.lane_section_offsets = []
        self.lane_width_list = []
        # self.total_offset = None
        self.main_ref_line = []
        self.ref_line = list()
        self.lanes = {
            'lane_offsets':list(),
            'lane_sections':list()
        }
        # self.lanes['lane_sections'] = list()

        self.signals = list()

        self.parent_odr_data = None
        self.from_main_ref_line = []
        self.to_main_ref_line = []
        self.link_list_not_organized = list() 
        self.changed = False

    def get_to_roads(self):
        next_road_id_set = []
        for road_link in self.link_list_not_organized:
            if len(road_link.get_to_links()) > 1:
                for to_link in road_link.get_to_links():
                    next_road_id_set.append(to_link.road_id)
            elif len(road_link.get_to_links()) == 1:
                next_road_id_set.append(road_link.get_to_links()[0].road_id)
            else:
                pass
        next_road_set = []
        for road_id in list(set(next_road_id_set)):
            try:
                next_road_set.append(self.odr_roads[road_id])
            except:
                next_road_set.append(self.parent_odr_data.roads[road_id])

        return next_road_set


    def get_from_roads(self):
        from_road_id_set = []
        for road_link in self.link_list_not_organized:
            
            if len(road_link.get_from_links()) > 1:
                for to_link in road_link.get_from_links():
                    from_road_id_set.append(to_link.road_id)
            elif len(road_link.get_from_links()) == 1:
                from_road_id_set.append(road_link.get_from_links()[0].road_id)
            else:
                pass
        from_road_set = []
        for road_id in list(set(from_road_id_set)):
            try:
                from_road_set.append(self.odr_roads[road_id])
            except:
                from_road_set.append(self.parent_odr_data.roads[road_id])

        return from_road_set


    def get_to_node_set_in_road(self):
        to_node_set = []
        for road_link in self.link_list_not_organized:
            to_node_set.append(road_link.to_node)
        return to_node_set


    def get_from_node_set_in_road(self):
        from_node_set = []
        for road_link in self.link_list_not_organized:
            from_node_set.append(road_link.from_node)
        return from_node_set


    def add_lane_section(self, lane_section):
        """
        lane section을 추가하는 함수
        """
        self.lanes['lane_sections'].append(lane_section)


    def add_signal(self, odr_signal):
        self.signals.append(odr_signal)
    
    
    def is_line(self, polynomial):
        for constant in polynomial:
            if constant != 0:
                return False
        return True

    
    def get_ref_line_id_list(self):
        ref_line_id_list = []
        for line in self.ref_line:
            ref_line_id_list.append(line.idx)

        return ref_line_id_list


    def get_all_link_id_list(self):
        all_link_id_list = []

        for lane_section in self.lanes['lane_sections']:
            for line in lane_section.get_lanes_L():
                all_link_id_list.append(line.idx)
            for line in lane_section.get_lanes_R():
                all_link_id_list.append(line.idx)

        return all_link_id_list


    def get_all_link_list_not_organized_id_list(self):
        all_link_id_list = []

        for link in self.link_list_not_organized:
            all_link_id_list.append(link.idx)

        return all_link_id_list


    def get_predecessor_roads(self):
        if self.parent_odr_data is None:
            return []

        if self.predecessor_id not in self.parent_odr_data.roads.keys():
            return []

        else:
            return [self.parent_odr_data.roads[self.predecessor_id]]


    def get_successor_roads(self):
        if self.parent_odr_data is None:
            return []

        if self.successor_id not in self.parent_odr_data.roads.keys():
            return []

        else:
            return [self.parent_odr_data.roads[self.successor_id]]


    def get_multi_depth_predecessor_roads(self, depth):
        if depth < 1:
            return []

        def find_1step_predecessors(road_list):
            all_1step_predecessors = []
            for road in road_list:
                all_1step_predecessors += road.get_predecessor_roads()
            return all_1step_predecessors

        all_predecessor = list()

        # 첫번째 depth은 아래와 같이 계산
        this_step_predecessors = self.get_predecessor_roads()
        all_predecessor += this_step_predecessors

        # 그 다음 depth부터는 아래와 같이 계산
        for i in range(1, depth):
            this_step_predecessors = find_1step_predecessors(this_step_predecessors)
            all_predecessor += this_step_predecessors

        return all_predecessor


    def get_multi_depth_successor_roads(self, depth):
        if depth < 1:
            return []

        def find_1step_successors(road_list):
            all_1step_successors = []
            for road in road_list:
                all_1step_successors += road.get_successor_roads()
            return all_1step_successors

        all_successor = list()

        # 첫번째 depth은 아래와 같이 계산
        this_step_successors = self.get_successor_roads()
        all_successor += this_step_successors

        # 그 다음 depth부터는 아래와 같이 계산
        for i in range(1, depth):
            this_step_successors = find_1step_successors(this_step_successors)
            all_successor += this_step_successors

        return all_successor

    
    def get_lane_sections(self):
        return self.lanes['lane_sections']
        

    def fine_reference_line_doubleSide(self):
        ref_line_candidates = []
        for link in self.link_list_not_organized:
            boundary_dir = link.lane_mark_left[0].points[1] - link.lane_mark_left[0].points[0]  
            link_dir = link.points[1] - link.points[0]
    
            if np.dot(boundary_dir, link_dir) < 0:
                self.ref_line = [link]
        
        return self.ref_line


    def find_reference_line(self):
        max_value = 0
        ref_line_candidates = [] # ref_line은 유일한 경우로 존재하지 않아서, 여러 가능한 경우가 있을 수 있다
        
        if self.ref_line !=[]:
            return self.ref_line

        for link in self.link_list_not_organized:
            # NOTE(hjp): for TT maps, we want to exclude non drivable lanes from being included in the
            # ref_line candidate pool
            link.odr_road = self
            if link.link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE', '1', '4', '6', "driving", "Driving",'Shoulder']:
                num, new_ref_line_candidate = edit_link.get_max_succeeding_links_within_the_same_road(link)
                print('for link: {}, following links: {}'.format(link.idx, Link.get_id_list_string(new_ref_line_candidate)))
                
                # 더 크면 무조건 업데이트하면 되고, 이 때 ref_line_candidate는 완전히 리셋하고 이 candidate로만 사용한다
                if num > max_value:
                    print('max_val: {}, num: {}'.format(max_value, num))
                    max_value = num
                    ref_line_candidates = [new_ref_line_candidate]

                # 만일 같으면, 누가 더 선행하는 ref line인지 따져봐야한다. 이는 나중에 수행할 예정으로,
                # 우선 ref_line_candidates에 입력한다
                elif num == max_value:
                    ref_line_candidates.append(new_ref_line_candidate)
                    
            elif link.link_type in ['NORMAL','REGULAR','highway','HOV', 'EXPRESS', 'SLOW','PASSING','REGULATED_ACCESS']:
                num, new_ref_line_candidate = edit_link.get_max_succeeding_links_within_the_same_road(link)
                print('for link: {}, following links: {}'.format(link.idx, Link.get_id_list_string(new_ref_line_candidate)))
                
                # 더 크면 무조건 업데이트하면 되고, 이 때 ref_line_candidate는 완전히 리셋하고 이 candidate로만 사용한다
                if num > max_value:
                    print('max_val: {}, num: {}'.format(max_value, num))
                    max_value = num
                    ref_line_candidates = [new_ref_line_candidate]

                # 만일 같으면, 누가 더 선행하는 ref line인지 따져봐야한다. 이는 나중에 수행할 예정으로,
                # 우선 ref_line_candidates에 입력한다
                elif num == max_value:
                    ref_line_candidates.append(new_ref_line_candidate)
        
        # ref_line_candidates에서 가장 적절한 ref line 고르기 
        if len(ref_line_candidates) == 1:
            # 만일 ref_line_candidate가 1개 뿐이면, 유일하게 결정할 수 있는 경우이다.
            self.ref_line = ref_line_candidates[0]

        elif len(ref_line_candidates) > 1:
            # ref_line_candidate가 여러개이면, 이 중에서 가장 왼쪽에 존재하는 것으로 고른다.
            self.ref_line = ref_line_candidates[0]
            
            # 가장 왼쪽에 존재하는 reference line을 찾는다
            left_most_ref_line = ref_line_candidates[0]
            
            for i in range(1, len(ref_line_candidates)):
                candidate = ref_line_candidates[i]

                # 현재 체크하는 reference line (candidate)의 0번 링크가
                # 기존의 left_most_ref_line의 0번 링크보다 왼쪽이면, 업데이트한다
                is_on_the_side, direction =\
                    candidate[0].is_in_the_left_or_right_side(left_most_ref_line[0])
                    
                if not is_on_the_side:
                    try:
                        raise BaseException('Road: {} has a logical error. The first link of each reference line candidate are not placed on the side of each other.'.format(self.road_id))
                    except:
                        pass
                else:
                    if direction == 'left':
                        left_most_ref_line = candidate
                 
            ref_line_change = False
            self.ref_line = left_most_ref_line
            if len(left_most_ref_line[0].lane_mark_left[0].from_node.to_links) >1 or len(left_most_ref_line[0].lane_mark_right[0].from_node.to_links) >1:
                
                if len(self.get_from_roads()) ==1:
                    from_road_ref_line = self.get_from_roads()[0].find_reference_line()
                    for link in self.link_list_not_organized:
                        if link in from_road_ref_line[0].get_to_links() and link is not left_most_ref_line[0] and len(link.lane_mark_right[0].from_node.to_links) ==1:
                            
                            #  and (len(link.lane_mark_left[0].from_node.to_links) ==1) :
                            self.ref_line = [link]
                            ref_line_change = True
                    if ref_line_change != True:
                        for link in self.link_list_not_organized:
                            if len(link.lane_mark_left[0].from_node.to_links) == 1:
                                self.ref_line = [link]
                                ref_line_change = True

                elif len(self.get_from_roads()) >1:
                    for from_road in self.get_from_roads():
                        from_road_ref_line = from_road.find_reference_line()
                        for link in self.link_list_not_organized:
                            # if len(link.lane_mark_right) == 0:
                            #     pass
                            #     # self.ref_line = [link]
                            #     # ref_line_change = True
                            if link in from_road_ref_line[0].get_to_links() and link is not left_most_ref_line[0]\
                                and len(link.lane_mark_right[0].from_node.to_links) ==1:
                                self.ref_line = [link]
                                ref_line_change = True
                                break
                else:

                    if left_most_ref_line[0].lane_ch_link_right != None:
                        
                        if ref_line_change == False:
                            for link in self.link_list_not_organized:
                                if len(link.lane_mark_right[0].from_node.to_links)==1:
                                    left_most_ref_line = [link]
                                    self.ref_line = left_most_ref_line
                                    ref_line_change = True
                                    break
                                elif len(link.lane_mark_right[0].from_node.to_links)==0:
                                    left_most_ref_line = [link]
                                    self.ref_line = left_most_ref_line
                                    ref_line_change = True
                        if ref_line_change == False:
                            if left_most_ref_line[0].lane_ch_link_right.lane_ch_link_right !=None:
                                left_most_ref_line = [left_most_ref_line[0].lane_ch_link_right.lane_ch_link_right]
                                self.ref_line = left_most_ref_line
                                ref_line_change = True
                            elif left_most_ref_line[0].lane_ch_link_right != None:
                                left_most_ref_line = [left_most_ref_line[0].lane_ch_link_right]
                                self.ref_line = left_most_ref_line
                                ref_line_change = True
           
            if len(left_most_ref_line[0].lane_mark_left[0].to_node.from_links) >1 or len(left_most_ref_line[0].lane_mark_right[0].to_node.from_links) >1:
                
                if len(self.get_to_roads()) ==1:
                    to_road_ref_line = self.get_to_roads()[0].find_reference_line()
                    for link in self.link_list_not_organized:
                        if link in to_road_ref_line[0].get_from_links() and link is not left_most_ref_line[0] and len(link.lane_mark_right[0].to_node.from_links) ==1:
                            #  and len(link.lane_mark_left[0].to_node.from_links) ==1:
                            self.ref_line = [link]
                            ref_line_change = True
                    
                    if ref_line_change != True:
                        for link in self.link_list_not_organized:
                            if len(link.lane_mark_left[0].to_node.from_links) == 1:
                                self.ref_line = [link]
                                ref_line_change = True

                elif len(self.get_from_roads()) >1:
                    for to_road in self.get_to_roads():
                        to_road_ref_line = to_road.find_reference_line()
                        for link in self.link_list_not_organized:
                            if link in to_road_ref_line[0].get_from_links() and link is not left_most_ref_line[0]\
                                and len(link.lane_mark_right[0].to_node.from_links) ==1:
                                self.ref_line = [link]
                                ref_line_change = True
                                break
                else:
                    if left_most_ref_line[0].lane_ch_link_right != None:
                    
                        if ref_line_change == False:
                            for link in self.link_list_not_organized:
                                if len(link.lane_mark_right[0].from_node.to_links)==1:
                                    left_most_ref_line = [link]
                                    self.ref_line = left_most_ref_line
                                    ref_line_change = True
                                    break
                        else:
                            left_most_ref_line = [left_most_ref_line[0].lane_ch_link_right]
                            self.ref_line = left_most_ref_line
                            ref_line_change = True
           
            self.ref_line[0].ref_true = True
            
            self.ref_line[0].lane_mark_left[0].ref_true = True 
            
            if ref_line_change == False:
                if len(self.get_from_roads()) == 1:
                    for from_road in self.get_from_roads():
                        from_road_ref_line = from_road.find_reference_line()
                        for link in self.link_list_not_organized:
                            if link in from_road_ref_line[0].get_to_links():
                                self.ref_line = [link]
                                ref_line_change = True
                                break

                elif len(self.get_to_roads()) == 1:
                    for to_road in self.get_to_roads():
                        to_road_ref_line = to_road.find_reference_line()
                        for link in self.link_list_not_organized:
                            if link in to_road_ref_line[0].get_from_links():
                                self.ref_line = [link]
                                ref_line_change = True
                                break
                
        elif len(self.link_list_not_organized) ==1:
            self.ref_line = self.link_list_not_organized
        else:
            # 0이라면, 이는 오류이다.
            raise BaseException('Failed to find reference line for road: {}'.format(self.road_id))
        self.ref_line[0].ref_true = True
        self.ref_line[0].lane_mark_left[0].ref_true = True 

        for link in self.link_list_not_organized:
            if link != self.ref_line[0] and len(link.lane_mark_left) != 0:
                link.lane_mark_left[0].ref_true = False
                link.ref_true = False
        return self.ref_line


    # def virtual_lane_bounadry_slope(self, from_or_to):

    def lane_section_soffsets(self, fir_lane_mark, sec_lane_mark):
        lane_section_soffsets = []
        lane_width_list = []
        mgeo_converter = converter.MGeoToOdrDataConverter()
        
        init_coord = np.array([sec_lane_mark[0][0], sec_lane_mark[0][1]])
        line_moved_origin_sec = sec_lane_mark[:,0:2] - init_coord
        line_moved_origin_fir = fir_lane_mark[:,0:2] - init_coord

        from_u = line_moved_origin_sec[1][0] - line_moved_origin_sec[0][0]
        from_v = line_moved_origin_sec[1][1] - line_moved_origin_sec[0][1]
        from_heading = np.arctan2(from_v, from_u) 
        from_inv_heading = (-1) * from_heading

        rotated_line_sec = mgeo_converter.coordinate_transform(from_inv_heading, line_moved_origin_sec)
        rotated_line_fir = mgeo_converter.coordinate_transform(from_inv_heading, line_moved_origin_fir)

        line_x_coord = rotated_line_sec[:,0]
        line_y_coord = rotated_line_sec[:,1]

        coeff_out = mgeo_converter.poly(line_x_coord,line_y_coord)
        for i in range(len(rotated_line_fir)):

            if abs( rotated_line_fir[i][1] - rotated_line_fir[i+1][1] \
                - coeff_out[0]*(rotated_line_fir[i][0] - rotated_line_fir[i+1][0]) \
                    - coeff_out[1]*(rotated_line_fir[i][0] -rotated_line_fir[i+1][0])) >0.1:
                lane_section_soffsets.append(rotated_line_fir[i][0])
                lane_width_list.append(abs(rotated_line_fir[i][1]))
                break
            if i == len(rotated_line_fir)-2:
                break
        
        for i in range(len(rotated_line_fir)-1, 0, -1):

            if abs( rotated_line_fir[i][1] - rotated_line_fir[i-1][1] \
                - coeff_out[0]*(rotated_line_fir[i][0] - rotated_line_fir[i-1][0]) \
                    - coeff_out[1]*(rotated_line_fir[i][0] -rotated_line_fir[i-1][0])) >0.1:
                lane_section_soffsets.append(rotated_line_fir[i][0])
                lane_width_list.append(abs(rotated_line_fir[i][1]))
                break
            if i == 1:
                break
        if lane_width_list!=[] and lane_width_list[-1] >10:
            pass
        if lane_width_list!=[] and lane_width_list[-1] >10:
            lane_section_soffsets=[]
            lane_width_list=[]
        return lane_section_soffsets, lane_width_list


    def create_lane_section(self):
        """
        Moves w.r.t the reference line to search for and save all lane data

        The reference line is the first of the right-hand lanes.
        All lanes left of the reference line are left-hand lanes.
        Every lane is uni-directional. (singleSide property assumed)

        Returns:
        lane_section -- a OdrLaneSection() object that contains all properties
        required for each lane section
        """
        for reference_line_segment in self.ref_line:
            lane_section = OdrLaneSection()
            lane_section.initialize(reference_line_segment)
            self.add_lane_section(lane_section)

        return self.lanes['lane_sections']


    def reset_lane_sections(self):
        self.lanes['lane_sections'] = list()


    def get_frontmost_left(self):
        return self.lanes['lane_sections'][0].get_leftmost().get_link()
    

    def get_frontmost_right(self):
        return self.lanes['lane_sections'][0].get_rightmost().get_link()


    def get_rearmost_left(self):
        return self.lanes['lane_sections'][-1].get_leftmost().get_link()


    def find_predecessors(self):
        # NOTE: 다음과 같이 리팩토링이 가능하다 >> self.get_lane_sections()[0].get_predecessor_road_ids()
        # 하지만 위와 같이 리팩토링 할 경우, 반드시 lane_section이 구축되어야하는 제약이 있으므로 refactoring 하지 않는다
        predecessor_survey_results = list()
        current_link = self.get_frontmost_left()
        right_links_exist = True

        while right_links_exist is True:
            try:
                predecessor_survey = current_link.get_from_links()
            except:
                current_link = self.get_frontmost_right()
                predecessor_survey = current_link.get_from_links()
            for pre_candidate in predecessor_survey:
                if pre_candidate.road_id in predecessor_survey_results:
                    pass
                else:
                    predecessor_survey_results.append(pre_candidate.road_id)

            if current_link.lane_ch_link_right is None:
                right_links_exist = False
            else:
                current_link = current_link.lane_ch_link_right

        return predecessor_survey_results    


    def find_successors(self):
        # NOTE: 다음과 같이 리팩토링이 가능하다 >> self.get_lane_sections()[-1].get_successor_road_ids()
        # 하지만 위와 같이 리팩토링 할 경우, 반드시 lane_section이 구축되어야하는 제약이 있으므로 refactoring 하지 않는다

        successor_survey_results = list()
        current_link = self.get_rearmost_left()
        right_links_exist = True
        
        while right_links_exist is True:
            successor_survey = current_link.get_to_links()
            for suc_candidate in successor_survey:
                if suc_candidate.road_id in successor_survey_results:
                    pass
                else:
                    successor_survey_results.append(suc_candidate.road_id)
            if current_link.lane_ch_link_right is None:
                right_links_exist = False
            else:
                current_link = current_link.lane_ch_link_right

        return successor_survey_results


    def get_frontmost_nodes(self):
        lane_sections = self.get_lane_sections()
        if len(lane_sections) == 0:
            raise BaseException('ERROR @ get_frontmost_nodes: lane_section must be created first before calling this method. (road id: {})'.format(self.road_id))

        return lane_sections[0].get_from_nodes()


    def get_rearmost_nodes(self):
        lane_sections = self.get_lane_sections()
        if len(lane_sections) == 0:
            raise BaseException('ERROR @ get_rearmost_nodes: lane_section must be created first before calling this method. (road id: {})'.format(self.road_id))

        return lane_sections[-1].get_end_nodes()


    def get_no_junction_error_nodes_front(self):
        """
        junction이 생성되어 있어야 하는데, 되어있지 않은 노드가 있는지 확인한다
        True가 반환되면, 이 road의 앞쪽 node에는 junction이 생성되어야 한다
        """
        pre_road_ids = self.find_predecessors()

        # 앞쪽으로 연결된 road가 없거나 / 하나만 존재하면, 체크할 필요가 없다
        if len(pre_road_ids) <= 1:
            return []

        error_nodes = [] 
        
        # 이 road 가장 앞쪽 node에서 junction이 설정되지 않은 node가 있는지 확인한다
        for node in self.get_frontmost_nodes():
            if len(node.get_junctions()) == 0:
                error_nodes.append(node)

        return error_nodes


    def get_no_junction_error_nodes_end(self):
        """
        junction이 생성되어 있어야 하는데, 되어있지 않은 노드가 있는지 확인한다
        True가 반환되면, 이 road의 뒤쪽 node에는 junction이 생성되어야 한다
        """
        suc_road_ids = self.find_successors()

        # 앞쪽으로 연결된 road가 없거나 / 하나만 존재하면, 체크할 필요가 없다
        if len(suc_road_ids) <= 1:
            return []
        
        error_nodes = [] 

        # 이 road 가장 앞쪽 node에서 junction이 설정되지 않은 node가 있는지 확인한다
        for node in self.get_rearmost_nodes():
            if len(node.get_junctions()) == 0:
                error_nodes.append(node)

        return error_nodes


    def create_xml_string(self, xodr_root):
        xodr_road = etree.SubElement(xodr_root, 'road')

        self.create_xml_header(parent=xodr_road)
        self.create_xml_link(parent=xodr_road)
        self.create_xml_type(parent=xodr_road)
        self.create_xml_plan_view(parent=xodr_road)
        self.create_xml_elevation_profile(parent=xodr_road)
        if converter.MGeoToOdrDataConverter.get_instance().get_config('superelevation'):
            self.create_xml_lateral_profile(parent=xodr_road)
        self.create_xml_lane(parent=xodr_road)
        self.create_xml_signal(parent=xodr_road)


    def create_xml_string_apollo(self, xodr_root, mgeo_planner_map):
        xodr_road = etree.SubElement(xodr_root, 'road')
        self.create_xml_header_apollo(parent=xodr_road)
        self.create_xml_link(parent=xodr_road)
        self.create_xml_lane_apollo(parent=xodr_road, mgeo_planner_map=mgeo_planner_map)
        

    def create_xml_header_apollo(self, parent):
        parent.set('name', '{}'.format(self.road_id))
        parent.set('id', '{}'.format(self.id))
        
        if self.junction is None:
            jc_id = '-1'
        else:
            jc_id = self.junction.idx

        parent.set('junction', '{}'.format(jc_id))


    def create_xml_header(self, parent):
        parent.set('name', '{}'.format(self.road_id))
        parent.set('length', '{:.16e}'.format(self.road_length))
        # parent.set('id', '{}'.format(self.road_id))
        parent.set('id', '{}'.format(self.id))
        
        if self.junction is None:
            jc_id = '-1'
        else:
            jc_id = self.junction.idx

        parent.set('junction', '{}'.format(jc_id))
        parent.set('rule', '{}'.format(self.traffic_dir))


    def create_xml_link(self, parent):
        """
        OpenDRIVE에서 road 다음의 link 정보를 생성한다
        """
        xodr_road_link = etree.SubElement(parent, 'link')

        if self.predecessor_id is not None:
            xodr_road_link_pre = etree.SubElement(xodr_road_link, 'predecessor')

            if self.is_pre_junction is True:
                xodr_road_link_pre.set('elementType', 'junction')
                xodr_road_link_pre.set('elementId', '{}'.format(self.predecessor_id))
            else:
                xodr_road_link_pre.set('elementType', 'road')
                xodr_road_link_pre.set('elementId', '{}'.format(self.predecessor_id))
                xodr_road_link_pre.set('contactPoint', 'end')

        if self.successor_id is not None:
            xodr_road_link_suc = etree.SubElement(xodr_road_link, 'successor')
            
            if self.is_suc_junction is True:
                xodr_road_link_suc.set('elementType', 'junction')
                xodr_road_link_suc.set('elementId', '{}'.format(self.successor_id))
            else:
                xodr_road_link_suc.set('elementType', 'road')
                xodr_road_link_suc.set('elementId', '{}'.format(self.successor_id))
                xodr_road_link_suc.set('contactPoint', 'start')


    def create_xml_type(self, parent):
        xodr_road_type = etree.SubElement(parent, 'type')
        xodr_road_type.set('s', '{:.16e}'.format(0))
        xodr_road_type.set('type', self.road_type)
        xodr_road_type.set('country', self.country)


    def create_xml_plan_view(self, parent):
        xodr_road_planview = etree.SubElement(parent, 'planView')
        for lane_section in self.lanes['lane_sections']:
            for v_idx, vector in enumerate(lane_section.geometry):
                xodr_road_geometry = etree.SubElement(xodr_road_planview, 'geometry')
                xodr_road_geometry.set('s', '{:.16e}'.format(lane_section.vector_s_offset[v_idx]))
                xodr_road_geometry.set('x', '{:.16e}'.format(lane_section.init_coord[v_idx][0]))
                xodr_road_geometry.set('y', '{:.16e}'.format(lane_section.init_coord[v_idx][1]))
                xodr_road_geometry.set('hdg', '{:.16e}'.format(lane_section.heading[v_idx]))
                xodr_road_geometry.set('length', '{:.16e}'.format(lane_section.arclength[v_idx]))

                if self.is_line(lane_section.geometry[v_idx]):
                    xodr_road_geometry_line = etree.SubElement(xodr_road_geometry, 'line')
                elif len(lane_section.geometry[v_idx]) == 4:
                    xodr_road_geometry_p3 = etree.SubElement(xodr_road_geometry, 'poly3')
                    xodr_road_geometry_p3.set('a', '{:.16e}'.format(lane_section.geometry[v_idx][0]))
                    xodr_road_geometry_p3.set('b', '{:.16e}'.format(lane_section.geometry[v_idx][1]))
                    xodr_road_geometry_p3.set('c', '{:.16e}'.format(lane_section.geometry[v_idx][2]))
                    xodr_road_geometry_p3.set('d', '{:.16e}'.format(lane_section.geometry[v_idx][3]))
                else:
                    xodr_road_geometry_param3 = etree.SubElement(xodr_road_geometry, 'paramPoly3')
                    xodr_road_geometry_param3.set('aU', '{:.16e}'.format(lane_section.geometry[v_idx][0]))
                    xodr_road_geometry_param3.set('bU', '{:.16e}'.format(lane_section.geometry[v_idx][1]))
                    xodr_road_geometry_param3.set('cU', '{:.16e}'.format(lane_section.geometry[v_idx][2]))
                    xodr_road_geometry_param3.set('dU', '{:.16e}'.format(lane_section.geometry[v_idx][3]))
                    xodr_road_geometry_param3.set('aV', '{:.16e}'.format(lane_section.geometry[v_idx][4]))
                    xodr_road_geometry_param3.set('bV', '{:.16e}'.format(lane_section.geometry[v_idx][5]))
                    xodr_road_geometry_param3.set('cV', '{:.16e}'.format(lane_section.geometry[v_idx][6]))
                    xodr_road_geometry_param3.set('dV', '{:.16e}'.format(lane_section.geometry[v_idx][7]))
                    xodr_road_geometry_param3.set('pRange', '{}'.format('normalized'))


    def create_xml_elevation_profile(self, parent):
        odr_converter = converter.MGeoToOdrDataConverter()
        xodr_road_elevation_prof = etree.SubElement(parent, 'elevationProfile')
        for lane_section in self.lanes['lane_sections']:
            for v_idx, vector in enumerate(lane_section.elevation):
                xodr_road_elevation = etree.SubElement(xodr_road_elevation_prof, 'elevation')
                if converter.MGeoToOdrDataConverter.get_instance().get_config('reference_line_fitting'):
                    xodr_road_elevation.set('s','{:.16e}'.format(lane_section.elevation_soffset[v_idx]))
                else:
                    xodr_road_elevation.set('s','{:.16e}'.format(lane_section.vector_s_offset[v_idx]))
                    # xodr_road_elevation.set('s','{:.16e}'.format(lane_section.lanes_R[0].vector_s_offset[v_idx]))
                xodr_road_elevation.set('a','{:.16e}'.format(lane_section.elevation[v_idx][0]))
                xodr_road_elevation.set('b','{:.16e}'.format(lane_section.elevation[v_idx][1]))
                xodr_road_elevation.set('c','{:.16e}'.format(lane_section.elevation[v_idx][2]))
                xodr_road_elevation.set('d','{:.16e}'.format(lane_section.elevation[v_idx][3]))


    def create_xml_lateral_profile(self, parent):
        odr_converter = converter.MGeoToOdrDataConverter()
        xodr_road_lateral_superelevation = etree.SubElement(parent, 'lateralProfile')
        for lane_section in self.lanes['lane_sections']:
            for v_idx, vector in enumerate(lane_section.lateral):
                xodr_road_elevation = etree.SubElement(xodr_road_lateral_superelevation, 'superelevation')
                if odr_converter.optimization_flag:
                    xodr_road_elevation.set('s','{:.16e}'.format(lane_section.vector_s_offset[v_idx]))
                else:
                    xodr_road_elevation.set('s','{:.16e}'.format(lane_section.vector_s_offset[v_idx]))
                    # xodr_road_elevation.set('s','{:.16e}'.format(lane_section.lanes_R[0].vector_s_offset[v_idx]))
                xodr_road_elevation.set('a','{:.16e}'.format(lane_section.lateral[v_idx][0]))
                xodr_road_elevation.set('b','{:.16e}'.format(lane_section.lateral[v_idx][1]))
                xodr_road_elevation.set('c','{:.16e}'.format(lane_section.lateral[v_idx][2]))
                xodr_road_elevation.set('d','{:.16e}'.format(lane_section.lateral[v_idx][3]))


    def create_xml_lane(self, parent):
        xodr_lane = etree.SubElement(parent, 'lanes')

        # FIXME(hjp) not using offsets for TT evaluation
        # self.create_xml_lane_offset(xodr_lane)

        for lane_section in self.lanes['lane_sections']:
            ref_line = self.ref_line[0]
            lane_section.create_xml_string(ref_line, parent=xodr_lane, junction=self.junction)
    

    def create_xml_lane_apollo(self, parent, mgeo_planner_map):
        xodr_lane = etree.SubElement(parent, 'lanes')

        for lane_section in self.lanes['lane_sections']:
            lane_section.create_xml_string_apollo(parent=xodr_lane, mgeo_planner_map = mgeo_planner_map, junction=self.junction)
    

    def create_xml_lane_offset(self, parent):
        sOffset = 0
        
        if self.left_expand_lane == True:
            pass 
           
        else:
            for lane_section in self.lanes['lane_sections']:

                lane_section.create_xml_string_lane_offset(parent, sOffset)
                sOffset += lane_section.lane_length


    def create_xml_string_lane_offset(self, parent, soffset, start_offset, end_offset):
        xodr_lane_offset = etree.SubElement(parent, 'laneOffset')


        xodr_lane_offset.set('s','{:.16e}'.format(soffset))
        xodr_lane_offset.set('a','{:.16e}'.format(a))
        xodr_lane_offset.set('b','{:.16e}'.format(b))
        xodr_lane_offset.set('c','{:.16e}'.format(c))
        xodr_lane_offset.set('d','{:.16e}'.format(d))


    def create_xml_signal(self, parent):
        xodr_road_signals = etree.SubElement(parent, 'signals')
        for signal in self.signals:
            if signal.s == signal.t == signal.position_inertial_ori[2] == 0:
                continue
            signal.ToXml(xodr_road_signals)


    def item_prop(self):
        prop_data = OrderedDict()
        prop_data['road_id'] = {'type' : 'string', 'value' : self.road_id }
        prop_data['id'] = {'type' : 'string', 'value' : self.id }
        prop_data['is_pre_junction'] = {'type' : 'boolean', 'value' : self.is_pre_junction}
        prop_data['predecessor_id'] = {'type' : 'boolean', 'value' : self.predecessor_id}
        prop_data['is_suc_junction'] = {'type' : 'boolean', 'value' : self.is_suc_junction}
        prop_data['successor_id'] = {'type' : 'string', 'value' : self.successor_id}
        prop_data['ref_lines'] = {'type' : 'list<string>', 'value' : self.get_ref_line_id_list()}
        prop_data['links'] = {'type' : 'list<string>', 'value' : self.get_all_link_list_not_organized_id_list()}
        return prop_data