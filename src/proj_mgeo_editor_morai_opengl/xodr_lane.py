"""
OdrLaneSection Module
"""

from asyncio.log import logger
import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from lib.common.logger import Logger
import mgeo_odr_converter 
import lxml.etree as etree
import numpy as np
import mgeo_odr_converter as converter
from pyproj import Proj
import mgeo_odr_converter as converter
class OdrLane(object):
    """
    OdrLane Class
    """
    def __init__(self, link, idx, lane_section, lane_type='driving'):
        self.link = link
        self.idx = idx
        self.lane_type = lane_type

        # 해당 Lane을 갖는 LaneSection에 대한 참조
        self.lane_section = lane_section
        # geometry
        # self.vector_s_offset = list()
        # self.init_coord = list()
        # self.heading = list()
        # self.arclength = list()
        # self.geometry = list()
        # self.geometry_u_max = list()

        # lane gap when actual lane dimensions are known
        self.gap_known = {'start': None, 'end': None}

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


    def get_road_mark_lane_change_direction_tt(self, lane_mark):
        if lane_mark.pass_restr is not None:
            if lane_mark.pass_restr == 'passingnotallowed':
                lane_restrict = 'none'
            elif lane_mark.pass_restr == 'passingfromleftandright':
                lane_restrict = 'both'
            elif lane_mark.pass_restr == 'passingonlylefttoright':
                lane_restrict = 'decrease'
            elif lane_mark.pass_restr == 'passingonlyrighttoleft':
                lane_restrict = 'increase'
            else:
                lane_restrict = None

        return lane_restrict


    def create_xml_string_shoulder(self, parent, virtual_shoulder_width):
        xml_lane = self.__create_xml_string_lane_header_shoulder(parent)
        self.__create_xml_string_lane_idx_shoulder(xml_lane)
        self.__create_xml_string_lane_width_shoulder(xml_lane, start_width = virtual_shoulder_width)
        #self.__create_xml_string_road_mark(xml_lane, self.get_road_mark_lane_change_direction())


    def curvature(self, line):
        fir_slope_list = []
        line_points = line.points
        for idx in range(len(line_points)):
            if idx == len(line_points)-1:
                continue
            diff = line_points[idx+1][:2] - line_points[idx][:2]
            fir_slope_list.append(diff)
        
        fir_angle_diff_list = []
        for idx in range(len(fir_slope_list)):
            if idx == len(fir_slope_list)-1:
                continue
            cos_diff = abs(np.dot(fir_slope_list[idx+1] , fir_slope_list[idx])/(np.linalg.norm(fir_slope_list[idx+1])*np.linalg.norm(fir_slope_list[idx])))
            if cos_diff >1:
                cos_diff = 1
            angle_diff = np.arccos(cos_diff)
            fir_angle_diff_list.append(angle_diff)

        return np.sum(fir_angle_diff_list)


    def create_xml_string(self, parent, ref_line):
        """
        차선의 (lane) xml element 생성 및 속성 할당하는 메인 함수
        """
        if self.idx is None:
            raise BaseException('Link id is not initialized (link id: {})'.format(self.link.idx))

        # if self.gap is None:
        #     raise BaseException('idx is not initialized (link id: {})'.format(self.link.idx))
        if self.gap_known is None:
            raise BaseException('Lane widths are not initialized (link id: {})'.format(self.link.idx))

        # OpenDRIVE conversion option에 따라 lane_link를 생략할 수 있다
        config_enable_lane_link = not mgeo_odr_converter.MGeoToOdrDataConverter.get_instance().get_config('disable_lane_link')

        # center lane
        xml_lane = self.__create_xml_string_lane_header(parent)

        # for all other lanes
        if self.idx != 0:
            # left or right lane
            # NOTE TT eval version deactivated legacy lane width functions
            #      included new function __create_xml_string_lane_width_tt()
            #      added the __create_xml_string_lane_idx() function for tt data
            #      completely changed the __create_xml_string_road_mark() function
            #      replaced the get_road_mark_lane_change_direction() function with a tt version
            if self.link is None:
                raise BaseException('idx != 0, which is meant to be either a left lane or a right lane does not have link instance connected to this lane.')
           
            self.__create_xml_string_lane_idx(xml_lane)

            if config_enable_lane_link:
                self.__create_xml_string_lane_link(xml_lane)

            # self.__create_xml_string_lane_width(xml_lane)
            # self.__create_xml_string_lane_width_poly(xml_lane)
            
            start_width = self.gap_known['start']
            end_width = self.gap_known['end']
            #NOTE(chi) 5% 이상 차이나는 구간만 poly3로 작성 
            left_middle_point = self.link.lane_mark_left[0].points[len(self.link.lane_mark_left[0].points)//2]
            right_middle_point = self.link.lane_mark_right[0].points[len(self.link.lane_mark_right[0].points)//2]
            middle_vector = left_middle_point - right_middle_point 
            middle_width = np.linalg.norm(middle_vector)
            
            left_lane_mark = self.link.lane_mark_left[0]
            right_lane_mark = self.link.lane_mark_right[0]
            ref_line_left_lane_mark = ref_line.lane_mark_left[0]
            # diff_compare_ref = abs(self.curvature(left_lane_points) - self.curvature(ref_line_points))
            left_lane_mark_curvature = self.curvature(left_lane_mark)
            right_lane_mark_cuvature = self.curvature(right_lane_mark)
            diff_compare = abs(left_lane_mark_curvature -right_lane_mark_cuvature)
            
            # NOTE(geometrical threshold UI 또는 최적화 필요)
            config_width_threshold_flag = converter.MGeoToOdrDataConverter.get_instance().get_config('width_threshold')
            config_s_offset_detection_threshold_flag = converter.MGeoToOdrDataConverter.get_instance().get_config('s_offset_detection_threshold')
            # 일반차선
            if abs(start_width - end_width) <0.1 and diff_compare < 0.2 and middle_width - start_width < 1:
                self.__create_xml_string_lane_width_tt(xml_lane)
            #확장 후 다시 수렴하는 차선
            elif abs(start_width - end_width) <0.1 and diff_compare/left_lane_mark_curvature >0.2 and middle_width - start_width > 1:
                soffset_list, lane_width_list = self.lane_section_soffsets_middle(ref_line, float(config_width_threshold_flag), float(config_s_offset_detection_threshold_flag))
                self.__create_xml_string_lane_width_poly3(xml_lane, soffset_list, lane_width_list)
            # 확장 차선(확장 시작 soffset 설정 필요)
            elif diff_compare/left_lane_mark_curvature >0.2:# and middle_width - start_width > 0.5 :
            # elif abs(start_width - end_width) >2 or (diff_compare/left_lane_mark_curvature >0.2 and middle_width - start_width > 0.5):
                soffset_list, lane_width_list = self.lane_section_soffsets(ref_line, float(config_width_threshold_flag), float(config_s_offset_detection_threshold_flag))
                self.__create_xml_string_lane_width_poly3(xml_lane, soffset_list, lane_width_list)
            # 일반 확장 차선(확장 시작 soffset 설정 불필요)
            
            else:
                self.__create_xml_string_lane_width_poly3(xml_lane, soffset_list = [], lane_width_list = [])

            self.__create_xml_string_lane_access(xml_lane)
            self.__create_xml_string_speed_limit(xml_lane)

        self.__create_xml_string_road_mark(xml_lane, self.get_road_mark_lane_change_direction())
        

    def create_xml_string_apollo(self, parent, mgeo_planner_map, junction):
        
        xml_lane = self.__create_xml_string_lane_header_apollo(parent)
        
        self.__create_xml_string_centerLine(xml_lane, mgeo_planner_map)
        self.__create_xml_string_border(xml_lane, mgeo_planner_map)
        self.__create_xml_link(xml_lane)
        self.__create_xml_string_speed(xml_lane)
        self.__create_xml_string_sampleAssociates(xml_lane)
        self.__create_xml_string_leftRoadSampleAssociations(xml_lane)
        self.__create_xml_string_rightRoadSampleAssociatations(xml_lane)
        self.__create_xml_string_signalOverlapGroup(xml_lane)
        self.__create_xml_string_objectOverlapGroup(xml_lane)
        self.__create_xml_string_junctionOverlapGroup(xml_lane, junction)
        
    def __create_xml_link(self, parent):
        xml_lane_link = etree.SubElement(parent, 'link')
        if self.idx != 0:
            
            for to_link in self.link.to_node.to_links:
                xml_lane_link_successor = etree.SubElement(xml_lane_link, 'successor')
                xml_lane_link_successor.set('id', '{}'.format(to_link.idx))
            
            for from_link in self.link.from_node.from_links:
                xml_lane_link_predecessor = etree.SubElement(xml_lane_link, 'predecessor')
                xml_lane_link_predecessor.set('id', '{}'.format(from_link.idx))


        if self.idx != 0:
            if self.link.lane_ch_link_left != None:
                left_link = self.link.lane_ch_link_left
                xml_lane_link_neighbor = etree.SubElement(xml_lane_link, 'neighbor')
                xml_lane_link_neighbor.set('id', '{}'.format(left_link.idx))
                xml_lane_link_neighbor.set('side', '{}'.format('left'))
                xml_lane_link_neighbor.set('direction', '{}'.format('same'))
            
            if self.link.lane_ch_link_right !=None:
                right_link = self.link.lane_ch_link_right
                xml_lane_link_neighbor = etree.SubElement(xml_lane_link, 'neighbor')
                xml_lane_link_neighbor.set('id', '{}'.format(right_link.idx))
                xml_lane_link_neighbor.set('side', '{}'.format('right'))
                xml_lane_link_neighbor.set('direction', '{}'.format('same'))
       


    def point_to_longlat(self, point, mgeo_planner_map):
        offset = mgeo_planner_map.local_origin_in_global
        x, y, z  = point + offset
    
        proj = mgeo_planner_map.global_coordinate_system
        p = Proj(proj)
        lons, lats = p(x, y, inverse = True)
        return lons, lats


    def __create_xml_string_sampleAssociates(self, parent):
        xml_lane_sampleAssociates = etree.SubElement(parent, 'sampleAssociates')

        if self.link != None:
            if self.link.lane_mark_right ==[]:
                rightWidth = 1.7
            else:
                rightWidth = np.linalg.norm(self.link.points[0]-self.link.lane_mark_right[0].points[0] , 2)
            leftWidth = np.linalg.norm(self.link.points[0]-self.link.lane_mark_left[0].points[0] , 2)
            
            xml_lane_sampleAssociate = etree.SubElement(xml_lane_sampleAssociates, 'sampleAssociate')
            xml_lane_sampleAssociate.set('sOffset', '{}'.format(0))
            xml_lane_sampleAssociate.set('leftWidth', '{}'.format(leftWidth))
            xml_lane_sampleAssociate.set('rightWidth', '{}'.format(rightWidth))


    def __create_xml_string_leftRoadSampleAssociations(self, parent):
        xml_lane_leftRoadSampleAssociations = etree.SubElement(parent, 'leftRoadSampleAssociations')
        if self.link != None:
            width = np.linalg.norm(self.link.points[0] - self.lane_section.get_leftmost().link.lane_mark_left[0].points[0], 2)
            xml_lane_leftRoadSampleAssociation = etree.SubElement(xml_lane_leftRoadSampleAssociations, 'sampleAssociation')
            xml_lane_leftRoadSampleAssociation.set('sOffset', '{}'.format(0))
            xml_lane_leftRoadSampleAssociation.set('width', '{}'.format(width))


    def __create_xml_string_rightRoadSampleAssociatations(self, parent):
        xml_lane_rightRoadSampleAssociatations = etree.SubElement(parent, 'rightRoadSampleAssociations')
        if self.link != None:
            if self.link.lane_mark_right ==[]:
                width = 1.7
            else:
                width = np.linalg.norm(self.link.points[0] - self.lane_section.get_rightmost().link.lane_mark_right[0].points[0], 2)
            xml_lane_rightRoadSampleAssociatation = etree.SubElement(xml_lane_rightRoadSampleAssociatations, 'sampleAssociation')
            xml_lane_rightRoadSampleAssociatation.set('sOffset', '{}'.format(0))
            xml_lane_rightRoadSampleAssociatation.set('width', '{}'.format(width))


    def __create_xml_string_signalOverlapGroup(self, parent):
        xml_lane_signalOverlapGroup = etree.SubElement(parent, 'signalOverlapGroup')
    
    
    def __create_xml_string_objectOverlapGroup(self, parent):
        xml_lane_objectOverlapGroup = etree.SubElement(parent, 'objectOverlapGroup')
    
    
    def __create_xml_string_junctionOverlapGroup(self, parent, junction):
        xml_lane_junctionOverlapGroup = etree.SubElement(parent, 'junctionOverlapGroup')
        if junction != None:
            xml_lane_junctionOverlapGroup_ref = etree.SubElement(xml_lane_junctionOverlapGroup, 'junctionReference')
            xml_lane_junctionOverlapGroup_ref.set('id', junction.idx)
            xml_lane_junctionOverlapGroup_ref.set('startOffset', '0')
            xml_lane_junctionOverlapGroup_ref.set('endOffset', '{}'.format(self.lane_section.arclength[0]))
   

    def __create_xml_string_speed(self, parent):
        xml_lane_speed = etree.SubElement(parent, 'speed')
        xml_lane_speed.set('max', '{}'.format(60))

    def __create_xml_string_border(self, parent, mgeo_planner_map):
        xml_lane_border = etree.SubElement(parent, 'border')
        xml_lane_border.set('virtual', 'true')
        self.__create_xml_string_lane_geometry(xml_lane_border, mgeo_planner_map, 'border')
        self.__create_xml_string_borderType(xml_lane_border)
    

    def __create_xml_string_borderType(self, parent):
        mgeo_converter = mgeo_odr_converter.MGeoToOdrDataConverter()
        if self.idx == 0:
            soffset = 0
            eoffset = 0
            for lane_mark in self.lane_section.reference_line_piece.lane_mark_left:

                xml_borderType = etree.SubElement(parent, 'borderType')
                if lane_mark.lane_shape != []:
                    if lane_mark.lane_shape[0].lower() =='undefined' or lane_mark.lane_color[0].lower() == 'undefined':
                        xml_borderType.set('type', '{}'.format('none'))
                        xml_borderType.set('color', '{}'.format('none'))
                    else:
                        xml_borderType.set('type', '{}'.format(lane_mark.lane_shape[0].lower()))
                        
                        if lane_mark.lane_shape[0].lower() =='solid'\
                            and lane_mark.lane_color[0].lower() !='white'\
                                and lane_mark.lane_color[0].lower() !='yellow':
                            
                            xml_borderType.set('color', '{}'.format('white'))

                        elif lane_mark.lane_shape[0].lower() =='broken'\
                            and lane_mark.lane_color[0].lower() !='white'\
                                and lane_mark.lane_color[0].lower() !='yellow':

                            xml_borderType.set('color', '{}'.format('white'))

                        elif lane_mark.lane_shape[0].lower() =='none':
                            xml_borderType.set('color', '{}'.format('none'))
                        
                        else:
                            if lane_mark.lane_color[0].lower() == 'undefined':
                                xml_borderType.set('color', '{}'.format('none'))
                            else:
                                xml_borderType.set('color', '{}'.format(lane_mark.lane_color[0].lower()))
                else:
                    xml_borderType.set('type', '{}'.format('none'))
                    xml_borderType.set('color', '{}'.format('none'))

                xml_borderType.set('sOffset', '{}'.format(soffset))
                eoffset = soffset + mgeo_converter.arclength_of_line(lane_mark.points[:,0], lane_mark.points[:,1])
                soffset = eoffset
                xml_borderType.set('eOffset', '{}'.format(eoffset))
    
        elif self.idx >0:
            soffset = 0
            eoffset = 0
            for lane_mark in self.link.lane_mark_left:

                xml_borderType = etree.SubElement(parent, 'borderType')
                if lane_mark.lane_shape != []:
                    if lane_mark.lane_shape[0].lower() =='undefined' or lane_mark.lane_color.lower() == 'undefined':
                        xml_borderType.set('type', '{}'.format('none'))
                        xml_borderType.set('color', '{}'.format('none'))
                    else:
                        xml_borderType.set('type', '{}'.format(lane_mark.lane_shape[0].lower()))
                        
                        if lane_mark.lane_shape[0].lower() =='solid'\
                            and lane_mark.lane_color.lower() !='white'\
                                and lane_mark.lane_color.lower() !='yellow':
                            
                            xml_borderType.set('color', '{}'.format('white'))

                        elif lane_mark.lane_shape[0].lower() =='broken'\
                            and lane_mark.lane_color.lower() !='white'\
                                and lane_mark.lane_color.lower() !='yellow':

                            xml_borderType.set('color', '{}'.format('white'))

                        elif lane_mark.lane_shape[0].lower() =='none':
                            xml_borderType.set('color', '{}'.format('none'))
                        
                        else:
                            if lane_mark.lane_color.lower() == 'undefined':
                                xml_borderType.set('color', '{}'.format('none'))
                            else:
                                xml_borderType.set('color', '{}'.format(lane_mark.lane_color.lower()))
                else:
                    xml_borderType.set('type', '{}'.format('none'))
                    xml_borderType.set('color', '{}'.format('none'))
                
                xml_borderType.set('sOffset', '{}'.format(soffset))
                eoffset = soffset + mgeo_converter.arclength_of_line(lane_mark.points[:,0], lane_mark.points[:,1])
                soffset = eoffset
                xml_borderType.set('eOffset', '{}'.format(eoffset))


        else:
            soffset = 0
            eoffset = 0
            for lane_mark in self.link.lane_mark_right:

                xml_borderType = etree.SubElement(parent, 'borderType')
                if lane_mark.lane_shape != []:
                    if lane_mark.lane_shape[0].lower() =='undefined' or lane_mark.lane_color[0].lower() == 'undefined':
                        xml_borderType.set('type', '{}'.format('none'))
                        xml_borderType.set('color', '{}'.format('none'))
                    else:
                        xml_borderType.set('type', '{}'.format(lane_mark.lane_shape[0].lower()))
                        
                        if lane_mark.lane_shape[0].lower() =='solid'\
                            and lane_mark.lane_color[0].lower() !='white'\
                                and lane_mark.lane_color[0].lower() !='yellow':
                            
                            xml_borderType.set('color', '{}'.format('white'))

                        elif lane_mark.lane_shape[0].lower() =='broken'\
                            and lane_mark.lane_color[0].lower() !='white'\
                                and lane_mark.lane_color[0].lower() !='yellow':

                            xml_borderType.set('color', '{}'.format('white'))

                        elif lane_mark.lane_shape[0].lower() =='none':
                            xml_borderType.set('color', '{}'.format('none'))
                        
                        else:
                            if lane_mark.lane_color[0].lower() == 'undefined':
                                xml_borderType.set('color', '{}'.format('none'))
                            else:
                                xml_borderType.set('color', '{}'.format(lane_mark.lane_color[0].lower()))
                else:
                    xml_borderType.set('type', '{}'.format('none'))
                    xml_borderType.set('color', '{}'.format('none'))
                
                xml_borderType.set('sOffset', '{}'.format(soffset))
                eoffset = soffset + mgeo_converter.arclength_of_line(lane_mark.points[:,0], lane_mark.points[:,1])
                soffset = eoffset
                xml_borderType.set('eOffset', '{}'.format(eoffset))


    def __create_xml_string_centerLine(self, parent, mgeo_planner_map):
        xml_lane = etree.SubElement(parent, 'centerLine')
        self.__create_xml_string_lane_geometry(xml_lane, mgeo_planner_map, 'lane')


    def __create_xml_string_lane_geometry(self, parent, mgeo_planner_map, laneOrBorder):
        mgeo_converter = mgeo_odr_converter.MGeoToOdrDataConverter()
        if self.link != None:
            if laneOrBorder  == 'lane':
                lons,lats = self.point_to_longlat(self.link.points[0], mgeo_planner_map)
                z = self.link.points[0][2]
            else:
                if self.link.lane_mark_right != []:
                    lons,lats = self.point_to_longlat(self.link.lane_mark_right[0].points[0], mgeo_planner_map)
                    z = self.link.lane_mark_right[0].points[0][2]
                else:
                    lons, lats, z = (0,0,0)
                    points = self.link.points
                    xml_lane_geometry = etree.SubElement(parent, 'geometry')
                    xml_lane_geometry.set('sOffset', '{}'.format(0))
                    xml_lane_geometry.set('x', '{}'.format(lons))
                    xml_lane_geometry.set('y', '{}'.format(lats))
                    xml_lane_geometry.set('z', '{}'.format(z))
                    arclength = mgeo_converter.arclength_of_line(self.link.points[:,0], self.link.points[:,1])
                    xml_lane_geometry.set('length', '{}'.format(arclength))
                    xml_lane_geometry_pointSet = etree.SubElement(xml_lane_geometry, 'pointSet')
        
        elif self.link == None and laneOrBorder == 'border' :
            points = self.lane_section.reference_line_piece.lane_mark_left[0].points
            lons, lats = self.point_to_longlat(points[0], mgeo_planner_map)
            z = points[0][2]
        
        else:
            lons, lats, z = (0,0,0)
            #points = self.lane_section.reference_line_piece.lane_mark_left[0].points
            xml_lane_geometry = etree.SubElement(parent, 'geometry')
            xml_lane_geometry.set('sOffset', '{}'.format(0))
            xml_lane_geometry.set('x', '{}'.format(lons))
            xml_lane_geometry.set('y', '{}'.format(lats))
            xml_lane_geometry.set('z', '{}'.format(z))
            #arclength = mgeo_converter.arclength_of_line(points[:,0], points[:,1])
            xml_lane_geometry.set('length', '{}'.format(0))
            xml_lane_geometry_pointSet = etree.SubElement(xml_lane_geometry, 'pointSet')
        
        if self.link != None:
            if laneOrBorder  == 'lane':
                points = self.link.points
                xml_lane_geometry = etree.SubElement(parent, 'geometry')
                xml_lane_geometry.set('sOffset', '{}'.format(0))
                xml_lane_geometry.set('x', '{}'.format(lons))
                xml_lane_geometry.set('y', '{}'.format(lats))
                xml_lane_geometry.set('z', '{}'.format(z))
                arclength = mgeo_converter.arclength_of_line(self.link.points[:,0], self.link.points[:,1])
                xml_lane_geometry.set('length', '{}'.format(arclength))
                xml_lane_geometry_pointSet = etree.SubElement(xml_lane_geometry, 'pointSet')
                for idx, point in enumerate(points):
                    lons,lats = self.point_to_longlat(point, mgeo_planner_map)
                    pointSet = etree.SubElement(xml_lane_geometry_pointSet, 'point')
                    pointSet.set('x', '{:.16e}'.format(lons))
                    pointSet.set('y', '{:.16e}'.format(lats))
                    pointSet.set('z', '{:.16e}'.format(point[2]))
            else:
                soffset = 0
                xml_lane_geometry = etree.SubElement(parent, 'geometry')
                xml_lane_geometry.set('sOffset', '{}'.format(soffset))
                xml_lane_geometry.set('x', '{}'.format(lons))
                xml_lane_geometry.set('y', '{}'.format(lats))
                xml_lane_geometry.set('z', '{}'.format(z))
                arclength = 0 
                for i in range(len(self.link.lane_mark_right)):
                    arclength += mgeo_converter.arclength_of_line(self.link.lane_mark_right[i].points[:,0], self.link.lane_mark_right[i].points[:,1])
                xml_lane_geometry.set('length', '{}'.format(arclength))
                
                xml_lane_geometry_pointSet = etree.SubElement(xml_lane_geometry, 'pointSet')
                
                points = []
                for lane_mark in self.link.lane_mark_right:
                    points += list(lane_mark.points)
        
                for idx, point in enumerate(points):
                    lons,lats = self.point_to_longlat(point, mgeo_planner_map)
                    pointSet = etree.SubElement(xml_lane_geometry_pointSet, 'point')
                    pointSet.set('x', '{:.16e}'.format(lons))
                    pointSet.set('y', '{:.16e}'.format(lats))
                    pointSet.set('z', '{:.16e}'.format(point[2]))

        elif self.link == None and laneOrBorder == 'border':
            soffset = 0  
            xml_lane_geometry = etree.SubElement(parent, 'geometry')
            xml_lane_geometry.set('sOffset', '{}'.format(soffset))
            xml_lane_geometry.set('x', '{}'.format(lons))
            xml_lane_geometry.set('y', '{}'.format(lats))
            xml_lane_geometry.set('z', '{}'.format(z))
            arclength = 0
            for i in range(len(self.lane_section.reference_line_piece.lane_mark_left)):
                arclength += mgeo_converter.arclength_of_line(self.lane_section.reference_line_piece.lane_mark_left[i].points[:,0], self.lane_section.reference_line_piece.lane_mark_left[i].points[:,1])
            xml_lane_geometry.set('length', '{}'.format(arclength))
            
            xml_lane_geometry_pointSet = etree.SubElement(xml_lane_geometry, 'pointSet')
            
            points = self.lane_section.reference_line_piece.lane_mark_left[0].points
            for idx, point in enumerate(points):
                lons,lats = self.point_to_longlat(point, mgeo_planner_map)
                pointSet = etree.SubElement(xml_lane_geometry_pointSet, 'point')
                pointSet.set('x', '{:.16e}'.format(lons))
                pointSet.set('y', '{:.16e}'.format(lats))
                pointSet.set('z', '{:.16e}'.format(point[2]))


    def __create_xml_string_lane_header(self, parent):
        xodr_lane = etree.SubElement(parent, 'lane')
        xodr_lane.set('id', '{}'.format(self.idx))
        xodr_lane.set('type', self.lane_type)
        xodr_lane.set('level', 'false')
        return xodr_lane


    def __create_xml_string_lane_header_apollo(self, parent):
        xodr_lane = etree.SubElement(parent, 'lane')
        xodr_lane.set('id', '{}'.format(self.idx))
        if self.link == None:
            xodr_lane.set('uid', '{}'.format(self.lane_section.reference_line_piece.lane_mark_left[0].idx))
        else:
            xodr_lane.set('uid', '{}'.format(self.link.idx))
        
        if self.lane_type == 'none' or self.lane_type == 'shoulder':
            xodr_lane.set('type', 'shoulder')
        else:
            xodr_lane.set('type', '{}'.format('driving'))
        
        if self.idx != 0:
            xodr_lane.set('type', '{}'.format('driving'))
        else:
            xodr_lane.set('type', 'shoulder')

        xodr_lane.set('direction', 'forward')
        xodr_lane.set('turnType', 'noTurn')
        
        return xodr_lane


    def __create_xml_string_lane_header_shoulder(self, parent):
        xodr_lane = etree.SubElement(parent, 'lane')
        xodr_lane.set('id', '{}'.format(self.idx -1))
        xodr_lane.set('type', 'shoulder')
        xodr_lane.set('level', 'false')
        return xodr_lane


    def __create_xml_string_lane_idx(self, parent):
        xodr_lane_user_data = etree.SubElement(parent, 'userData')
        xodr_lane_user_data.set('laneId', self.link.idx)


    def __create_xml_string_lane_idx_shoulder(self, parent):
        xodr_lane_user_data = etree.SubElement(parent, 'userData')
        xodr_lane_user_data.set('laneId', 'virtual shoulder')


    def __create_xml_string_lane_access(self, parent):
        # lane access - autonomousTraffic/pedestrian/passengerCar/bus/delivery/emergency/
        #               taxi/throughTraffic/truck/bicycle/motorcycle/none/trucks
        access_type = self.get_link().hov
        if access_type is not None:
            xodr_lane_access = etree.SubElement(parent, 'access')
            xodr_lane_access.set('sOffset', '{}'.format(0))

            if access_type == 'bus':
                xodr_lane_access.set('rule', 'allow')
                xodr_lane_access.set('restriction', 'bus')
            elif access_type == 'hov':
                xodr_lane_access.set('rule', 'allow')
                xodr_lane_access.set('restriction', 'bus') # NOTE(hjp): no OpenDRIVE equivalent for HOV (as of v1.6)
            else:
                xodr_lane_access.set('rule', 'deny')
                xodr_lane_access.set('restriction', 'none')
                Logger.log_trace('Unknown lane access type {} returned by {}'.format(access_type, self.get_link().idx))


    def __create_xml_string_speed_limit(self, parent):
        # TODO(hjp): give users the option of converting speed limit units
        speed_limit = self.get_link().max_speed

        # unit - [m/s][mph][km/h]
        unit_in = self.get_link().speed_unit
        if unit_in.casefold() == 'mph':
            unit = 'mph'
        elif unit_in.casefold() == 'kph':
            unit = 'km/h'
        elif unit_in.casefold() == 'mps':
            unit = 'm/s'
        else:
            Logger.log_trace('Unknown speed limit unit [{}] returned by {}'.format(unit_in, self.get_link().idx))
            return

        xodr_lane_speed = etree.SubElement(parent, 'speed')
        xodr_lane_speed.set('sOffset', '{}'.format(0))
        xodr_lane_speed.set('max', '{}'.format(speed_limit))
        xodr_lane_speed.set('unit', unit)


    def __create_xml_string_lane_link(self, parent):
        xml_link = etree.SubElement(parent, 'link')

        # TODO(sglee): Refactor here >> link의 ID를 받아오는 판단의 영역은 string으로 출력하는 것과 별개이므로.
        from_links = self.get_link().get_from_links()
        if len(from_links) == 1:
            # from_lane = from_links[0].odr_lane
            xodr_lane_link_pre = etree.SubElement(xml_link, 'predecessor')
            try:
                # xodr_lane_link_pre.set('id', '{}'.format(from_lane.idx))
                xodr_lane_link_pre.set('id', '{}'.format(from_links[0].ego_lane))
            except:
                pass
        to_links = self.get_link().get_to_links()
        if len(to_links) == 1:
             #to_lane = to_links[0].odr_lane
            xodr_lane_link_suc = etree.SubElement(xml_link, 'successor')
            # xodr_lane_link_suc.set('id', '{}'.format(to_lane.idx))
            xodr_lane_link_suc.set('id', '{}'.format(to_links[0].ego_lane))


    def __create_xml_string_lane_width(self, parent):
        xodr_lane_width = etree.SubElement(parent, 'width')
        
        # lane_gap 값을 찾은 다음 width를 설정하는 방법
        start_width = self.gap['start']['L'] + self.gap['start']['R']
        end_width = self.gap['end']['L'] + self.gap['end']['R']
        slope = (end_width - start_width) / self.lane_section.lane_length
        
        xodr_lane_width.set('sOffset', '{:.16e}'.format(0))
        # FIXME lane width soffset hard coded to 0?
        # consider running lane widths for each geometry vector
        xodr_lane_width.set('a', '{:.16e}'.format(start_width))
        xodr_lane_width.set('b', '{:.16e}'.format(slope))
        xodr_lane_width.set('c', '{:.16e}'.format(0))
        xodr_lane_width.set('d', '{:.16e}'.format(0))


    def __create_xml_string_lane_width_shoulder(self, parent, start_width =1):
        xodr_lane_width = etree.SubElement(parent, 'width')
        xodr_lane_width.set('sOffset', '{:.16e}'.format(0))
        xodr_lane_width.set('a', '{:.16e}'.format(start_width))
        xodr_lane_width.set('b', '{:.16e}'.format(0))
        xodr_lane_width.set('c', '{:.16e}'.format(0))
        xodr_lane_width.set('d', '{:.16e}'.format(0))


    def __create_xml_string_lane_width_shoulder_poly3(self, parent):
        xodr_lane_width = etree.SubElement(parent, 'width')
        
        start_width = self.gap_known['start']
        end_width = self.gap_known['end']
        
        x = self.link.length
        y = end_width

        a = start_width
        b = 0
        d = (-b + 2*(-y + a + b*x) / x) / (x**2)
        c = (y - d*(x**3) - (a + b*x)) / (x**2)

        xodr_lane_width.set('sOffset', '{:.16e}'.format(0))
        xodr_lane_width.set('a', '{:.16e}'.format(a))
        xodr_lane_width.set('b', '{:.16e}'.format(b))
        xodr_lane_width.set('c', '{:.16e}'.format(c))
        xodr_lane_width.set('d', '{:.16e}'.format(d))
    

    def curve_point_length(self, ref_line, point_lane_mark, dt=100):
        x = 0
        width_list = []
        soffset_list = []
        # fir_lane_mark = self.link.lane_mark_left[0].points
        ref_lane_mark = ref_line.lane_mark_left[0].points

        coeff_out, residual, arclength, rotated_line_fir, width_list = self.ref_line_coeff(ref_lane_mark, point_lane_mark)
        dx = rotated_line_fir[:,0][-1]/dt
        
        for idx, line_fir in enumerate(rotated_line_fir):
            length = 10000
            for i in range(dt):
                x_n = x + dx*i
                y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                    
                if length > np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2):
                    length = np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2)
                else:
                    # width_list.append(length)
                    soffset_list.append(x_n-dx)
                    break
        
        return soffset_list
    

    def curve_point_length_ref(self, ref_line, dt=100):
        x = 0
        fir_length_list = []
        fir_soffset_list = []
        fir_lane_mark = self.link.lane_mark_left[0].points
        ref_lane_mark = ref_line.lane_mark_left[0].points
        coeff_out, residual, arclength, rotated_line_fir = self.ref_line_coeff(ref_lane_mark, fir_lane_mark)
        dx = rotated_line_fir[:,0][-1]/dt
        
        for idx, line_fir in enumerate(rotated_line_fir):
            length = 10000
            for i in range(dt):
                x_n = x + dx*i
                y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                    
                if length > np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2):
                    length = np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2)
                else:
                    fir_length_list.append(length)
                    fir_soffset_list.append(x_n-dx)
                    break
        
        sec_length_list = []
        sec_soffset_list = []

        sec_lane_mark = self.link.lane_mark_right[0].points
        ref_lane_mark = ref_line.lane_mark_left[0].points
        coeff_out, residual, arclength, rotated_line_sec = self.ref_line_coeff(ref_lane_mark, sec_lane_mark)

        for idx, line_fir in enumerate(rotated_line_sec):
            length = 10000
            for i in range(dt):
                x_n = x + dx*i
                y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                    
                if length > np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2):
                    length = np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2)
                else:
                    sec_length_list.append(length)
                    sec_soffset_list.append(x_n-dx)
                    break
        if len(sec_length_list) > len(fir_length_list):

            length_candidate = fir_length_list
            soffset_list = fir_soffset_list
        else:
            length_candidate = sec_length_list
            soffset_list = sec_soffset_list
        width_list = []

        for length_idx in range(len(length_candidate)):
            width_list.append(abs(fir_length_list[length_idx] - sec_length_list[length_idx]))
        
        return width_list, soffset_list


    def ref_line_coeff(self,sec_lane_mark_points, fir_lane_mark_points):
        
        mgeo_converter = converter.MGeoToOdrDataConverter()
        
        init_coord = np.array([sec_lane_mark_points[0][0], sec_lane_mark_points[0][1]])
        line_moved_origin_sec = sec_lane_mark_points[:,0:2] - init_coord
        line_moved_origin_fir = fir_lane_mark_points[:,0:2] - init_coord

        from_u = line_moved_origin_sec[1][0] - line_moved_origin_sec[0][0]
        from_v = line_moved_origin_sec[1][1] - line_moved_origin_sec[0][1]
        from_heading = np.arctan2(from_v, from_u) 
        from_inv_heading = (-1) * from_heading

        rotated_line_sec = mgeo_converter.coordinate_transform(from_inv_heading, line_moved_origin_sec)
        rotated_line_fir = mgeo_converter.coordinate_transform(from_inv_heading, line_moved_origin_fir)

        line_x_coord = rotated_line_sec[:,0]
        line_y_coord = rotated_line_sec[:,1]

        
        coeff_out = mgeo_converter.poly(line_x_coord, line_y_coord)
        residual = mgeo_converter.residual(coeff_out, line_x_coord, line_y_coord)
        
        # when the residual is being over, coeff is changed by tuning points finely.  
        if  max(np.abs(residual)) > 0.1:
            coeff_list = []
            residual_list = []
            for i in range(5):
                line_x_coord = np.delete(line_x_coord,-2)
                line_y_coord = np.delete(line_y_coord, -2)
                
                coeff_out_candidate = mgeo_converter.poly(line_x_coord,line_y_coord)
                residual_candidate = mgeo_converter.residual(coeff_out_candidate, line_x_coord, line_y_coord)
                if max(np.abs(residual_candidate)) < 0.1:
                    coeff_out = coeff_out_candidate
                    residual = residual_candidate
                coeff_list.append(coeff_out_candidate)
                residual_list.append(residual_candidate)
                if len(line_x_coord) <3:
                    break
        arc = mgeo_converter.arclength_of_line(line_moved_origin_sec[:,0], line_moved_origin_sec[:,1])
        arclength = arc + 0.1  # forced connections b/n roads
        
        width_list = []
        dt=100
        dx = rotated_line_fir[:,0][-1]/dt
        x = 0
        for idx, line_fir in enumerate(rotated_line_fir):
            length = 10000
            for i in range(dt):
                x_n = x + dx*i
                y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                    
                if length > np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2):
                    length = np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2)
                else:
                    width_list.append(length)
                    break

        return coeff_out, residual, arclength, rotated_line_fir, width_list
    

    def soffset_for_ref_line(self, ref_line):
        fir_lane_mark = self.link.lane_mark_left[0].points
        ref_lane_mark = ref_line.lane_mark_left[0].points
        coeff_out, residual, arclength, rotated_line_fir = self.ref_line_coeff(ref_lane_mark, fir_lane_mark)
        soffset_list = []
        for idx, line_fir in enumerate(rotated_line_fir):
            dt = 100
            dx = ref_lane_mark[:,0][-1]/dt
            x = 0
            
            length = 1000000
            for i in range(dt):
                x_n = x + dx*i
                y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                    
                if length > np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2):
                    length = np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2)
                else:
                   
                    soffset_list.append(x_n-dx)
                    break
        return soffset_list


    def lane_section_soffsets_middle(self, ref_line, width_threshold, s_offset_detection_threshold):
        lane_section_soffsets = []
        lane_width_list = []
        mgeo_converter = converter.MGeoToOdrDataConverter()
        sec_lane_mark = self.link.lane_mark_right[0].points
        fir_lane_mark = self.link.lane_mark_left[0].points

        coeff_out_1, residual_1, arclength_1, rotated_line_fir_1, width_list_1 = self.ref_line_coeff(sec_lane_mark, fir_lane_mark)
        coeff_out_2, residual_2, arclength_2, rotated_line_fir_2, width_list_2 = self.ref_line_coeff(fir_lane_mark, sec_lane_mark)
        
        if max(residual_1) > max(residual_2):
            coeff_out = coeff_out_2
            residual = residual_2
            arclength = arclength_2
            rotated_line_fir = rotated_line_fir_2
            width_list = width_list_2
            lane_mark_point = sec_lane_mark
        else:
            coeff_out = coeff_out_1
            residual = residual_1
            arclength = arclength_1
            rotated_line_fir = rotated_line_fir_1
            width_list = width_list_1
            lane_mark_point = fir_lane_mark
        coeff_list = []
        num_interval = 1
        arclength_list = []
        rotated_line_fir_list = []
        residual_list = []
        

        if coeff_list ==[]:
            coeff_list.append(coeff_out)
            rotated_line_fir_list.append(rotated_line_fir)
            arclength_list.append(0)
            arclength_list.append(arclength)
        
        for j in range(len(coeff_list)):
            rotated_line_fir = rotated_line_fir_list[j]
            coeff_out = coeff_list[j]
            
            soffset_list = self.curve_point_length(ref_line, lane_mark_point)
            
            for i in range(len(width_list)):
                if i ==0:
                    continue
                elif abs(width_list[i] - width_list[0]) > 0.2:
                    lane_section_soffsets.append(soffset_list[i-1]*s_offset_detection_threshold/100)
                    lane_width_list.append(max(width_list)*(width_threshold/100))
                    # lane_width_list.append(width_list[i-1])
                    break
                if i == len(rotated_line_fir)-2:
                    break
            
            for i in range(len(width_list)):
                if i ==0:
                    continue
                if abs(width_list[i]-max(width_list)) <0.3:
                    lane_section_soffsets.append(soffset_list[i-1]*s_offset_detection_threshold/100)
                    lane_width_list.append(max(width_list)*(width_threshold/100))
                    # lane_width_list.append(width_list[i-1])
                    break
                if i == len(rotated_line_fir)-2:
                    break
            
            for i in range(len(width_list)-1, 0, -1):
                if i == len(width_list)-1:
                    continue
                if abs(width_list[i]-max(width_list)) <0.3:  
                    lane_section_soffsets.append(soffset_list[i+1])
                    lane_width_list.append(max(width_list)*(width_threshold/100))
                    # lane_width_list.append(width_list[i+1])
                    break
                if i == 1:
                    break
            
            for i in range(len(width_list)-1, 0, -1):
                if i == len(width_list)-1:
                    continue
                elif abs(width_list[i] - width_list[i+1])>0.2:
                    lane_section_soffsets.append(soffset_list[i])
                    # lane_width_list.append(width_list[i])
                    lane_width_list.append(max(width_list)*(width_threshold/100))
                    break
                if i == 1:
                    break

        return lane_section_soffsets, lane_width_list


    def lane_section_soffsets(self, ref_line, width_threshold, s_offset_detection_threshold):
        lane_section_soffsets = []
        lane_width_list = []
        mgeo_converter = converter.MGeoToOdrDataConverter()
        sec_lane_mark = self.link.lane_mark_right[0].points
        fir_lane_mark = self.link.lane_mark_left[0].points

        # sec_link = self.link.points
        # fir_link = self.link.points

        coeff_out_1, residual_1, arclength_1, rotated_line_fir_1, width_list_1 = self.ref_line_coeff(sec_lane_mark, fir_lane_mark)
        coeff_out_2, residual_2, arclength_2, rotated_line_fir_2, width_list_2 = self.ref_line_coeff(fir_lane_mark, sec_lane_mark)
        
        # coeff_out_1, residual_1, arclength_1, rotated_line_fir_1, width_list_1 = self.ref_line_coeff(sec_link, fir_link)
        # coeff_out_2, residual_2, arclength_2, rotated_line_fir_2, width_list_2 = self.ref_line_coeff(fir_link, sec_link)

        if np.sum(np.array(residual_1**2)) > np.sum(np.array(residual_2**2)):
            coeff_out = coeff_out_2
            residual = residual_2
            arclength = arclength_2
            rotated_line_fir = rotated_line_fir_2
            width_list = width_list_2
            point_lane_mark = sec_lane_mark
        else:
            coeff_out = coeff_out_1
            residual = residual_1
            arclength = arclength_1
            rotated_line_fir = rotated_line_fir_1
            width_list = width_list_1
            point_lane_mark = fir_lane_mark
        
        coeff_list = []
        num_interval = 1
        arclength_list = []
        rotated_line_fir_list = []
        residual_list = []
        

        if coeff_list ==[]:
            coeff_list.append(coeff_out)
            rotated_line_fir_list.append(rotated_line_fir)
            arclength_list.append(0)
            arclength_list.append(arclength)
        
        for j in range(len(coeff_list)):
            rotated_line_fir = rotated_line_fir_list[j]
            coeff_out = coeff_list[j]
            
            soffset_list = self.curve_point_length(ref_line, point_lane_mark)
            
            for i in range(len(width_list)):
                if i ==0:
                    continue
                elif abs(width_list[i] - width_list[i-1]) >0.3 or (width_list[i]>0.1 and width_list[0] <0.001):
                    if soffset_list[i-1] <0.001:

                        lane_section_soffsets.append(soffset_list[i-1])
                    else:
                        lane_section_soffsets.append(soffset_list[i-1]*s_offset_detection_threshold/100)

                    lane_width_list.append(width_list[i-1])
                    break
                if i == len(rotated_line_fir)-2:
                    break
            
            for i in range(len(width_list)-1, 0, -1):
                if i == len(width_list)-1:
                    continue
                elif abs(width_list[i] - width_list[i+1]) > 0.3 or (width_list[i]/max(width_list) <0.8 and width_list[0]<0.001):
                    # try:
                    #     lane_section_soffsets.append(soffset_list[i+2])
                    # except:
                    if lane_section_soffsets[0] <0.001:
                        lane_section_soffsets.append(soffset_list[i]*s_offset_detection_threshold/100)
                        lane_width_list.append(max(width_list)*(width_threshold/100))
                    else:
                        lane_section_soffsets.append(soffset_list[i])
                        lane_width_list.append(max(width_list)*(width_threshold/100))
                    break
                if i == 1:
                    break
       
        return lane_section_soffsets, lane_width_list


    def __create_xml_string_lane_width_poly3(self, parent, soffset_list = [], lane_width_list = []):
     
        start_width = self.gap_known['start']
        end_width = self.gap_known['end']

        if soffset_list == []:

            xodr_lane_width = etree.SubElement(parent, 'width')
            start_width = self.gap_known['start']
            end_width = self.gap_known['end']
            a = start_width
            x = self.lane_section.lane_length 
            y = end_width
            b = 0
            d = (-b + 2*(-y + a + b*x) / x) / (x**2)
            c = (y - d*(x**3) - (a + b*x)) / (x**2)
            xodr_lane_width.set('sOffset', '{:.16e}'.format(0))
            xodr_lane_width.set('a', '{:.16e}'.format(a))
            xodr_lane_width.set('b', '{:.16e}'.format(b))
            xodr_lane_width.set('c', '{:.16e}'.format(c))
            xodr_lane_width.set('d', '{:.16e}'.format(d))
        else:   
            soffset_list.insert(0,0)
            for idx, soffset in enumerate(soffset_list):
                
                if idx == 0:
                    
                    soffset = 0
                    x = soffset_list[idx+1]
                    if x <0.001:
                        continue
                    xodr_lane_width = etree.SubElement(parent, 'width')
                    y = lane_width_list[idx]
                    a = start_width
                    
                elif idx != len(soffset_list)-1:
                    xodr_lane_width = etree.SubElement(parent, 'width')
                    
                    # in the first offset ==0 case
                    if soffset_list[1] <0.001:
                        soffset = 0
                        x = soffset_list[idx+1]
                        y = lane_width_list[idx]
                        a = start_width
                    else:
                        x = soffset_list[idx+1] - soffset
                        y = lane_width_list[idx]
                        a = lane_width_list[idx-1]
                else:
                    xodr_lane_width = etree.SubElement(parent, 'width')
                    x = self.lane_section.lane_length - soffset
                    y = end_width
                    a = lane_width_list[idx-1]
                
                b = 0
                d = (-b + 2*(-y + a + b*x) / x) / (x**2)
                c = (y - d*(x**3) - (a + b*x)) / (x**2)

                xodr_lane_width.set('sOffset', '{:.16e}'.format(soffset))
                xodr_lane_width.set('a', '{:.16e}'.format(a))
                xodr_lane_width.set('b', '{:.16e}'.format(b))
                xodr_lane_width.set('c', '{:.16e}'.format(c))
                xodr_lane_width.set('d', '{:.16e}'.format(d))


    def __create_xml_string_lane_width_tt(self, parent, offset_list = []):
        xodr_lane_width = etree.SubElement(parent, 'width')
        
        # lane_gap 값을 찾은 다음 width를 설정하는 방법
        start_width = self.gap_known['start']
        end_width = self.gap_known['end']
        slope = (end_width - start_width) / self.lane_section.lane_length
        
        xodr_lane_width.set('sOffset', '{:.16e}'.format(0))
        # TODO(hjp) lane width soffset hard coded to 0?
        # consider running lane widths for each geometry vector
        xodr_lane_width.set('a', '{:.16e}'.format(start_width))
        # xodr_lane_width.set('a', '{:.16e}'.format(3.5))
        xodr_lane_width.set('b', '{:.16e}'.format(slope))
        # xodr_lane_width.set('b', '{:.16e}'.format(0))
        xodr_lane_width.set('c', '{:.16e}'.format(0))
        xodr_lane_width.set('d', '{:.16e}'.format(0))


    def __create_xml_string_lane_width_poly(self, parent):
        # NOTE: Experimental function - do not enable on release
        xodr_lane_width = etree.SubElement(parent, 'width')
        if self in self.lane_section.get_lanes_R():
            idx = abs(self.idx)
            lane = self.lane_section.lanes_R[idx]
        elif self in self.lane_section.get_lanes_L():
            idx = abs(self.idx) - 1
            lane = self.lane_section.lanes_L[idx]

        for idx in range(len(lane.geometry)):
            xodr_lane_width.set('sOffset', '{:.16e}'.format(lane.vector_s_offset[idx]))
            xodr_lane_width.set('a', '{:.16e}'.format(lane.geometry[idx][0]))
            xodr_lane_width.set('b', '{:.16e}'.format(lane.geometry[idx][1]))
            xodr_lane_width.set('c', '{:.16e}'.format(lane.geometry[idx][2]))
            xodr_lane_width.set('d', '{:.16e}'.format(lane.geometry[idx][3]))


    def __create_xml_string_road_mark(self, parent, lane_change):
        # determine the current lane type
        try:
            if self.idx == 0:
                # center lane
                lane_mark = self.lane_section.get_ref_lane().link.lane_mark_left[0]
            elif self.idx > 0:
                # left lane
                lane_mark = self.link.lane_mark_left[0]
            elif self.idx < 0:
                # right lane
                lane_mark = self.link.lane_mark_right[0]
        except:
            Logger.log_error('Lane assignment issue for OpenDRIVE conversion. Skipped link')
            return

        if lane_mark.lane_type_def == 'Hyundai AutoEver' or lane_mark.lane_type_def == 'ngii_model2':
            # TODO(hjp): combine autoever logic with above
            for i in range(len(lane_mark.lane_shape)):
                lane_type = lane_mark.lane_shape[i].lower()


                # weight - standard/bold (optional)
                lane_weight = 'standard'

                # color - white/yellow/blue/orange/red/green (required)
                lane_color = lane_mark.lane_color[i]
                if lane_color is None:
                    lane_color = 'white'
                    Logger.log_trace('Lane marking color properties empty at {}'.format(lane_mark.idx))
                elif lane_color is 'none':
                    lane_color = 'white'
                    Logger.log_trace('Lane marking color properties none at {}'.format(lane_mark.idx))
                # NOTE(hjp): OpenDRIVE 1.6 UML에는 흰색은 'standard'로 사용 가능하다고 게재되어있으나,
                # 보통 사용되는 툴들은 1.4, 1.5 기준으로 OpenDRIVE 파일 생산하니 우선 'white' 로 유지
                
                # material - (default is 'standard') (optional)
                lane_material = 'standard'

                # width - (in meters) (optional)
                lane_width = 0.15

                # height - (in meters) (optional)
                lane_height = 0.001

                # NOTE(hjp): length 및 space 속성은 기본 <roadMark>에 포함된 값이 아니라, roadMark.type.line에
                # 포함되는 값이므로 로직은 준비 되어있으나, 현재 필수 항목이 아닌 관계로 주석처리

                # length - (in meters)
                lane_length = lane_mark.dash_interval_L1 # not used

                # space - (in meters)
                lane_space = lane_mark.dash_interval_L2 # not used

                soffset = self.lane_section.lane_length * lane_mark.lane_type_offset[i]

                xodr_road_mark = etree.SubElement(parent, 'roadMark')
                xodr_road_mark.set('sOffset', '{:.16e}'.format(soffset))
                xodr_road_mark.set('type', '{}'.format(lane_type))
                xodr_road_mark.set('weight', lane_weight)
                xodr_road_mark.set('color', '{}'.format(lane_color))
                xodr_road_mark.set('material', '{}'.format(lane_material))
                xodr_road_mark.set('width',  '{}'.format(lane_width))
                # xodr_road_mark.set('length', '{}'.format(lane_length))
                # xodr_road_mark.set('space', '{}'.format(lane_space))
                xodr_road_mark.set('height', '{}'.format(lane_height))

                lane_change_tt = self.get_road_mark_lane_change_direction_tt(lane_mark)
                if lane_change_tt not in ['none', 'both', 'increase', 'decrease']:
                    xodr_road_mark.set('laneChange', 'none')
                    Logger.log_trace('Unknown laneChange attribute value at lane mark id: {}'.format(lane_mark.idx))
                else:
                    xodr_road_mark.set('laneChange', lane_change_tt)

                xodr_road_mark_user_data = etree.SubElement(xodr_road_mark, 'userData')
                xodr_road_mark_user_data.set('laneMarkId', lane_mark.idx)

        elif (len(lane_mark.lane_shape) > 0 or len(lane_mark.lane_color) > 0):
            # sanity check
            if len(lane_mark.lane_shape) != len(lane_mark.lane_color) or len(lane_mark.lane_shape) != len(lane_mark.lane_type_offset):
                raise BaseException('Lane boundary properties missing, property lists have different lenghths')

            for cnt in range(len(lane_mark.lane_type_offset)):
                xodr_road_mark = etree.SubElement(parent, 'roadMark')

                # NOTE: opendrive importer 정상화 이후 그대로 s값 들고 오도록 수정 필요
                soffset_ratio = lane_mark.lane_type_offset[cnt]
                soffset = soffset_ratio * self.lane_section.lane_length 
                xodr_road_mark.set('sOffset', '{:.16e}'.format(soffset))
                
                lane_type = lane_mark.lane_shape[cnt]
                xodr_road_mark.set('type', '{}'.format(lane_type))
                if lane_type not in ['solid', 'broken', 'solid solid', 'solid broken', 'broken solid', 'broken broken']:
                    Logger.log_trace('Unknown lane marking property at {}'.format(lane_mark.idx))

                lane_weight = 'standard'
                xodr_road_mark.set('weight', lane_weight)

                lane_color = lane_mark.lane_color[cnt]
                if lane_color == 'standard' or lane_color == 'none':
                    lane_color = 'white'
                xodr_road_mark.set('color', '{}'.format(lane_color))
                if lane_color not in ['white', 'yellow', 'blue', 'orange', 'red', 'green']:
                    Logger.log_trace('Unknown lane mark color at {}'.format(lane_mark.idx))
                
                lane_material = 'standard'
                xodr_road_mark.set('material', '{}'.format(lane_material))
                
                lane_width = 0.15
                xodr_road_mark.set('width', '{}'.format(lane_width))
                
                lane_height = 0.001
                xodr_road_mark.set('height', '{}'.format(lane_height))
                
                lane_change_tt = self.get_road_mark_lane_change_direction_tt(lane_mark)
                if lane_change_tt not in ['none', 'both', 'increase', 'decrease']:
                    xodr_road_mark.set('laneChange', lane_change)
                    Logger.log_trace('Used link network context to determine lane change for lane mark id: {}'.format(lane_mark.idx))
                    # Logger.log_trace('Unknown laneChange attribute value at lane mark id: {}'.format(lane_mark.idx))
                else:
                    xodr_road_mark.set('laneChange', lane_change_tt)

            xodr_road_mark_user_data = etree.SubElement(xodr_road_mark, 'userData')
            xodr_road_mark_user_data.set('laneMarkId', lane_mark.idx)

        else:
            # type - solid/broken/solid solid/solid broken/broken solid/broken broken/
            #        botts dots/grass/curb/custom/edge (required)
            if len(lane_mark.lane_type) > 0:
                if lane_mark.lane_type[0] in [1021, 1022, 1023, 199, 105]:
                    # physical
                    lane_type = 'edge' # test
                elif lane_mark.lane_type[0] == 103:
                    # painted line
                    lane_type = lane_mark.lane_shape[0].lower()
                elif lane_mark.lane_type[0] == 101:
                    # curb
                    lane_type = 'curb'
                else:
                    lane_type = 'unknown'
                    Logger.log_trace('Unknown lane marking property at {}'.format(lane_mark.idx))
                    # return

                # weight - standard/bold (optional)
                lane_weight = 'standard'

                # color - white/yellow/blue/orange/red/green (required)
                lane_color = lane_mark.lane_color[0]
                if lane_color is None:
                    lane_color = 'white'
                    Logger.log_trace('Lane marking color properties empty at {}'.format(lane_mark.idx))
                # NOTE(hjp): OpenDRIVE 1.6 UML에는 흰색은 'standard'로 사용 가능하다고 게재되어있으나,
                # 보통 사용되는 툴들은 1.4, 1.5 기준으로 OpenDRIVE 파일 생산하니 우선 'white' 로 유지
                
                # material - (default is 'standard') (optional)
                lane_material = 'standard'

                # width - (in meters) (optional)
                lane_width = 0.15

                # height - (in meters) (optional)
                lane_height = 0.001

                # NOTE(hjp): length 및 space 속성은 기본 <roadMark>에 포함된 값이 아니라, roadMark.type.line에
                # 포함되는 값이므로 로직은 준비 되어있으나, 현재 필수 항목이 아닌 관계로 주석처리

                # length - (in meters)
                lane_length = lane_mark.dash_interval_L1 # not used

                # space - (in meters)
                lane_space = lane_mark.dash_interval_L2 # not used

                xodr_road_mark = etree.SubElement(parent, 'roadMark')
                xodr_road_mark.set('sOffset', '{}'.format(0.0))
                xodr_road_mark.set('type', '{}'.format(lane_type))
                xodr_road_mark.set('weight', lane_weight)
                xodr_road_mark.set('color', '{}'.format(lane_color))
                xodr_road_mark.set('material', '{}'.format(lane_material))
                xodr_road_mark.set('width',  '{}'.format(lane_width))
                # xodr_road_mark.set('length', '{}'.format(lane_length))
                # xodr_road_mark.set('space', '{}'.format(lane_space))
                xodr_road_mark.set('height', '{}'.format(lane_height))

                lane_change_tt = self.get_road_mark_lane_change_direction_tt(lane_mark)
                if lane_change_tt not in ['none', 'both', 'increase', 'decrease']:
                    # raise BaseException('lane_change value is invalid')
                    xodr_road_mark.set('laneChange', 'none')
                    Logger.log_trace('Unknown laneChange attribute value at lane mark id: {}'.format(lane_mark.idx))
                else:
                    # xodr_road_mark.set('laneChange', lane_change)
                    xodr_road_mark.set('laneChange', lane_change_tt)

                xodr_road_mark_user_data = etree.SubElement(xodr_road_mark, 'userData')
                xodr_road_mark_user_data.set('laneMarkId', lane_mark.idx)


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
            raise BaseException("Invalid argument: argument end_type should be one of these: 'both', 'start', 'end'. Your input: {}".format(end_type))


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