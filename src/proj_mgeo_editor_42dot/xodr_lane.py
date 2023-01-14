"""
OdrLaneSection Module
"""

import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from lib.common.logger import Logger
import mgeo_odr_converter
import lxml.etree as etree


class OdrLane(object):
    """
    OdrLane Class
    """
    def __init__(self, link, idx, lane_section, lane_type='driving'):
        self.link = link
        self.lane_type = lane_type
        self.idx = idx

        # 해당 Lane을 갖는 LaneSection에 대한 참조
        self.lane_section = lane_section

        # self.gap = None
        # self.gap = [{'start':None, 'end':None}]
        # self.gap_cannot_directly_set = False  # TODO(sglee): 여기 코드 정리하기: 이 변수 필요 없을 것으로 예상됨
        self.gap = {
            'start':{'L': None, 'R': None},
            'end': {'L': None, 'R': None}}


    def get_next_lanes(self):
        next_lanes = []

        for to_link in self.get_link().get_to_links():
            if to_link.odr_lane is None:
                raise BaseException('Error @ get_next_lanes: to_link (id: {}) does not have odr_lane set. (current link: {})'.format(to_link.idx, self.get_link().idx))
            else:
                next_lanes.append(to_link.odr_lane)
        
        return next_lanes


    def get_prev_lanes(self):
        prev_lanes = []

        for from_link in self.get_link().get_from_links():
            if from_link.odr_lane is None:
                raise BaseException('Error @ get_next_lanes: from_link (id: {}) does not have odr_lane set. (current link: {})'.format(from_link.idx, self.get_link().idx))
            else:
                prev_lanes.append(from_link.odr_lane)
        
        return prev_lanes


    def get_lane_change_direction(self):
        """
        현재 링크에서 차선 변경 가능한 방향을 얻어온다. roadMark 와는 상이하다
        """
        # center lane이면 무조건 none
        if self.idx == 0:
            return 'none'

        # left or right lane
        if self.link is None:
            raise BaseException('idx != 0, which is meant to be either a left lane or a right lane does not have link instance connected to this lane.')


        # 제일 왼쪽에 있는 링크이면, 더 이상 왼쪽으로 차선 변경 불가
        if self is self.lane_section.get_leftmost():
            lane_change_left = False 
        else:
            lane_change_left = True 

        # 제일 오른쪽에 있는 링크이면, 더 이상 오른쪽으로 차선 변경 불가
        if self is self.lane_section.get_rightmost():
            lane_change_right = False
        else:
            lane_change_right = True

        
        if (lane_change_left == False) and (lane_change_right == True):
            lane_change_direction = 'decrease'

        elif (lane_change_left == True) and (lane_change_right == True):
            lane_change_direction = 'both'

        elif (lane_change_left == True) and (lane_change_right == False):
            lane_change_direction = 'increase'

        else:
            # 어느쪽으로도 차선 변경 불가
            lane_change_direction = 'none'
            
        return lane_change_direction


    def get_road_mark_lane_change_direction(self):
        """
        현재 lane 오른쪽에 있는 차선의, 차선 변경 방향을 설정한다.
        가장 오른쪽 차선이 아니면, both로 설정하면 된다.
        """
        # center lane이면 무조건 none
        if self.idx == 0:
            return 'none'

        # left or right lane
        if self.link is None:
            raise BaseException('idx != 0, which is meant to be either a left lane or a right lane does not have link instance connected to this lane.')


        # 제일 오른쪽에 있는 링크이면, 더 이상 오른쪽으로 차선 변경 불가
        if self is self.lane_section.get_rightmost():
            lane_change_direction = 'none'
        else:
            lane_change_direction = 'both'
            
        return lane_change_direction


    def create_xml_string(self, parent):
        if self.idx is None:
            raise BaseException('idx is not initialized (link id: {})'.format(self.link.idx))

        if self.gap is None:
            raise BaseException('idx is not initialized (link id: {})'.format(self.link.idx))

        
        # OpenDRIVE conversion option에 따라 lane_link를 생략할 수 있다
        config_enable_lane_link = not mgeo_odr_converter.MGeoToOdrDataConverter.get_instance().get_config('disable_lane_link')

        # center lane
        xml_lane = self.__create_xml_string_lane_header(parent)

        if self.idx != 0: # center lane 이 아닌 경우에만
            # left or right lane
            if self.link is None:
                raise BaseException('idx != 0, which is meant to be either a left lane or a right lane does not have link instance connected to this lane.')
            self.__create_xml_string_lane_access(xml_lane)

            if config_enable_lane_link:
                self.__create_xml_string_lane_link(xml_lane)

            self.__create_xml_string_lane_width(xml_lane)
        
        self.__create_xml_string_road_mark(xml_lane, self.get_road_mark_lane_change_direction())
        
        # if self.idx == 0:
        #     # center lane
        #     xml_lane = self.__create_xml_string_lane_header(parent)
        #     self.__create_xml_string_road_mark(xml_lane, 'none')
        # else:
        #     # left or right lane
        #     if self.link is None:
        #         raise BaseException('idx != 0, which is meant to be either a left lane or a right lane does not have link instance connected to this lane.')
            
        #     xml_lane = self.__create_xml_string_lane_header(parent)
        #     self.__create_xml_string_lane_access(xml_lane)
        #     self.__create_xml_string_lane_link(xml_lane)
        #     self.__create_xml_string_lane_width(xml_lane)
        #     self.__create_xml_string_road_mark(xml_lane, lane_change_direction)


    def __create_xml_string_lane_header(self, parent):
        xml_lane = etree.SubElement(parent, 'lane')
        xml_lane.set('id', '{}'.format(self.idx))
        xml_lane.set('type', self.lane_type)
        xml_lane.set('level', 'false')
        return xml_lane


    def __create_xml_string_lane_access(self, parent):
        if self.get_link().hov is True:
            xml_lane_access = etree.SubElement(parent, 'access')
            xml_lane_access.set('sOffset', '{}'.format(0))
            xml_lane_access.set('rule', 'allow')
            xml_lane_access.set('restriction', 'bus')


    def __create_xml_string_lane_link(self, parent):
        xml_link = etree.SubElement(parent, 'link')

        # TODO(sglee): Refactor here >> link의 ID를 받아오는 판단의 영역은 string으로 출력하는 것과 별개이므로.
        from_links = self.get_link().get_from_links()    
        if len(from_links) == 1:
            from_lane = from_links[0].odr_lane    
            xodr_r_lane_link_pre = etree.SubElement(xml_link, 'predecessor')
            xodr_r_lane_link_pre.set('id', '{}'.format(from_lane.idx))

        to_links = self.get_link().get_to_links()    
        if len(to_links) == 1:
            to_lane = to_links[0].odr_lane
            xodr_r_lane_link_suc = etree.SubElement(xml_link, 'successor')
            xodr_r_lane_link_suc.set('id', '{}'.format(to_lane.idx))


    def __create_xml_string_lane_width(self, parent):
        xodr_l_lane_width = etree.SubElement(parent, 'width')
        
        # lane_gap 값을 찾은 다음 width를 설정하는 방법
        start_width = self.gap['start']['L'] + self.gap['start']['R']
        end_width = self.gap['end']['L'] + self.gap['end']['R']
        slope = (end_width - start_width) / self.lane_section.lane_length
        
        xodr_l_lane_width.set('sOffset', '{:.16e}'.format(0))
        xodr_l_lane_width.set('a', '{:.16e}'.format(start_width))
        xodr_l_lane_width.set('b', '{:.16e}'.format(slope))
        xodr_l_lane_width.set('c', '{:.16e}'.format(0))
        xodr_l_lane_width.set('d', '{:.16e}'.format(0))


    def __create_xml_string_road_mark(self, parent, lane_change):
        road_mark = etree.SubElement(parent, 'roadMark')
        road_mark.set('sOffset', '{}'.format(0.0))
        road_mark.set('type', 'none')
        road_mark.set('width',  '{}'.format(0.0))
        road_mark.set('color', 'standard')

        if lane_change not in ['none', 'both', 'increase', 'decrease']:
            raise BaseException('lane_change value is invalid')
        else:
            road_mark.set('laneChange', lane_change)


    def is_gap_not_set(self, end_type='both'):
        if end_type == 'both':
            if (self.gap['start']['L'] is None) or (self.gap['start']['R'] is None) or (self.gap['end']['L'] is None) or (self.gap['end']['R'] is None):

                # 그런데, gap이 설정되어있지 않더라도, 현재 lane section이 1차선이고,
                if self.lane_section.get_lane_num() == 1:
                    # 또 해당 link의 width가 force 되어있으면, width가 있는 거라고 보면 된다
                    if self.get_link().force_width_start or self.get_link().force_width_end:
                        return False

                return True
            else:
                return False
        
        elif end_type == 'start':
            if (self.gap['start']['L'] is None) or (self.gap['start']['R'] is None):
                
                # 그런데, gap이 설정되어있지 않더라도, 현재 lane section이 1차선이고,
                if self.lane_section.get_lane_num() == 1:
                    # 또 해당 link의 width가 force 되어있으면, width가 있는 거라고 보면 된다
                    if self.get_link().force_width_start:
                        return False

                return True
            else:
                return False

        elif end_type == 'end':
            if (self.gap['end']['L'] is None) or (self.gap['end']['R'] is None):

                # 그런데, gap이 설정되어있지 않더라도, 현재 lane section이 1차선이고,
                if self.lane_section.get_lane_num() == 1:
                    # 또 해당 link의 width가 force 되어있으면, width가 있는 거라고 보면 된다
                    if self.get_link().force_width_end:
                        return False

                return True
            else:
                return False

        else:
            raise BaseException("Invalid argument: argument end_type should be one of these: 'both', 'start', 'end'. Your input: {}".format(end))



    def get_next_lane_start_width(self):
        # 다음 lane 중에서, start 쪽 gap이 있는지 확인한다
        for next_lane in self.get_next_lanes():
            # Lane을 받아오고, 해당 lane의 start쪽에 gap이 설정되었는지 확인한다
            if not next_lane.is_gap_not_set(end_type='start'): # gap이 하나라도 설정되어있으면 문제 없음
                return True, next_lane.gap['start']

        # 모든 next_lane의 start쪽 gap 설정이 안 되어있다
        return False, None


    def get_prev_lane_end_width(self):
        # 다음 lane 중에서, end쪽 gap이 있는지 확인한다
        for prev_lane in self.get_prev_lanes():
            # Lane을 받아오고, 해당 lane의 end쪽에 gap이 설정되었는지 확인한다
            if not prev_lane.is_gap_not_set(end_type='end'): # gap이 하나라도 설정되어있으면 문제 없음
                return True, prev_lane.gap['end']

        # 모든 prev_lane의 end쪽 gap 설정이 안 되어있다
        return False, None


    def does_next_lane_have_width(self):
        result, gap = self.get_next_lane_start_width()
        return result


    def does_prev_lane_have_width(self):
        result, gap = self.get_prev_lane_end_width()
        return result


    def estimate_lane_width_for_single_lane_legacy(self):
        """
        gap 이 None으로 설정된 single lane 인 lane에 대해, 해당 lane의 앞 뒤를 검색하여 width를 추정한다
        """
        if self.link.idx in ['70990101', '72990101']:
            print('DEBUG POINT')

        if not self.is_gap_not_set():
            return
            
        if self.lane_section.get_lane_num() != 1:
            raise BaseException('Initialization error. There is no lane.gap value set for non-singular lane_section')        

        from_links = self.get_link().get_from_links()    
        if len(from_links) == 1:            
            from_lane = self.find_from_lane_with_valid_gap()
            self.gap['start']['L'] = from_lane.gap['end']['L']
            self.gap['start']['R'] = from_lane.gap['end']['R']

            # 이렇게 하니까, from_lane의 gap이 None 인 경우들이 있어 안 된다
            # from_lane = from_links[0].odr_lane    
            # self.gap['start']['L'] = from_lane.gap['end']['L']
            # self.gap['start']['R'] = from_lane.gap['end']['R']
        
        elif len(from_links) > 1:
            # 여러 link에서 나오는 경우
            print('Warning: singular lane originated from multiple links')
        
            default_lane_width = self.lane_section.reference_line_piece.width
            self.gap['start']['L'] = default_lane_width / 2.0
            self.gap['start']['R'] = default_lane_width / 2.0

        else: # len(from_links) == 0 
            # source lane 인 경우
            print('Warning: this lane is a source lane')
        
            default_lane_width = self.lane_section.reference_line_piece.width
            self.gap['start']['L'] = default_lane_width / 2.0
            self.gap['start']['R'] = default_lane_width / 2.0


        to_links = self.get_link().get_to_links()    
        if len(to_links) == 1:
            to_lane = self.find_to_lane_with_valid_gap()
            self.gap['end']['L'] = to_lane.gap['start']['L']
            self.gap['end']['R'] = to_lane.gap['start']['R']

            # 이렇게 하니까, from_lane의 gap이 None 인 경우들이 있어 안 된다
            # to_lane = to_links[0].odr_lane
            # self.gap['end']['L'] = to_lane.gap['start']['L']
            # self.gap['end']['R'] = to_lane.gap['start']['R']

        elif len(to_links) > 1:
            # 여러 link로 향하는 경우
            print('Warning: singular lane led into multiple links')

            default_lane_width = self.lane_section.reference_line_piece.width
            self.gap['end']['L'] = default_lane_width / 2.0
            self.gap['end']['R'] = default_lane_width / 2.0

        else:
            # sink lane 인 경우
            print('Warning: this lane is a sink lane')

            default_lane_width = self.lane_section.reference_line_piece.width
            self.gap['end']['L'] = default_lane_width / 2.0
            self.gap['end']['R'] = default_lane_width / 2.0
            

    def find_from_lane_with_valid_gap(self):
        from_links = self.get_link().get_from_links()   
        while len(from_links) > 0:
            next_from_links = []

            # from link 중에서 end 쪽 gap이 설정된 경우를 찾아 리턴한다
            for link in from_links:
                Logger.log_debug('@ find_to_lane_with_valid_gap >> inspecting from_link: {}'.format(link.idx))
                if (link.odr_lane.gap['end']['L'] is not None) and (link.odr_lane.gap['end']['R'] is not None):
                    return link.odr_lane

                for temp_link in link.get_from_links():
                    next_from_links.append(temp_link)
            
            from_links = next_from_links

        return None


    def find_to_lane_with_valid_gap(self):
        to_links = self.get_link().get_to_links()   
        while len(to_links) > 0:
            next_to_links = []

            # to_links 중에서 start 쪽 width가 설정된 경우를 찾아 리턴한다
            for link in to_links:
                Logger.log_debug('@ find_to_lane_with_valid_gap >> inspecting to_link: {}'.format(link.idx))
                if (link.odr_lane.gap['start']['L'] is not None) and (link.odr_lane.gap['start']['R'] is not None):
                    return link.odr_lane

                for temp_link in link.get_to_links():
                    next_to_links.append(temp_link)
            
            to_links = next_to_links

        return None


    def get_link(self):
        return self.link


    def get_predecessor(self):
        pass


    def get_successor(self):
        pass