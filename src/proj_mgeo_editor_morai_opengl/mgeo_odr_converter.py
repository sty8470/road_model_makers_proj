"""
MGeoToOdrDataConverter Module
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from lib.common.logger import Logger
from lib.common.singleton import Singleton

import numpy as np
import mgeo_odr_converter as converter
import mgeo_odr_converter

from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_link
from xodr_signal import OdrSignal
from xodr_data import OdrData
from xodr_road import OdrRoad
from xodr_lane_section import OdrLaneSection
from xodr_lane import OdrLane
#from opengl_canvas import OpenGLCanvas

class MGeoToOdrDataConverter(Singleton):
    """
    MGeo 데이터를 OpenDRIVE 클래스로 변경하기 위한 기능을 포함하는 클래스

    주요 기능의 input/output
    input : MGeo PlannerMap 클래스 인스턴스
    output: OdrData 클래스 인스턴스
    """
    def __init__(self):
        self.CHK = False
        self.CHK_ID = [
            77141
            ]
        
        self.odr_conversion_config = None
        self.optimization_flag = False
        self.smoothing_vector_flag = False
    def is_config_set(self):
        if self.odr_conversion_config is None:
            return False
        else:
            return True


    def get_config(self, key=None):
        """
        OpenDRIVE 변환 옵션을 리턴한다. key를 통해 특정 옵션만 받을 수 있다.

        key argument를 전달하지 않으면, 전체 config (dictionary)를 리턴한다
        key argument를 전달하면, 해당 key의 config만 리턴한다
        """
        if not self.is_config_set():
            raise BaseException('ERROR @ get_config: config must be set before this method being called.')

        if key is None:
            # key argument를 전달하지 않으면 전체 config dictionary를 리턴한다
            return self.odr_conversion_config

        else:
            # key argument를 전달하면, 해당 key의 값을 리턴한다
            return self.odr_conversion_config[key]


    def set_config_all(self, config, key=None):
        """
        OpenDRIVE 변환 옵션을 설정한다.
        """
        self.odr_conversion_config = config     


    def set_config(self, key, value):
        """
        OpenDRIVE 변환 옵션을 설정한다. 특정 key에 해당하는 값을 설정한다
        """
        self.odr_conversion_config[key] = value    


    def pick_an_item_not_none(self, list_to_check):
        for item in list_to_check:
            if item is not None:
                return item

        # if for loop completes with no hits
        return None


    def get_prev_lane_in_the_same_road(self, link):
        """
        If a from_lane is connected to the argument [link] object, returns it

        Returns:
        prev_lane -- the Link() object of the lane preceding [link]. returns None
        if prev_lane is empty or does not exist
        """
        prev_lane = None
        for from_lane in link.get_from_links():
            if from_lane.road_id == link.road_id:
                prev_lane = from_lane

        return prev_lane


    def get_next_lane_in_the_same_road(self, link):
        """
        If a to_lane is connected to the argument [link] object, returns it

        Returns:
        prev_lane -- the Link() object of the lane succeeding [link]. returns None
        if prev_lane is empty or does not exist
        """
        next_lane = None
        for to_lane in link.get_to_links():
            if to_lane.road_id == link.road_id:
                next_lane = to_lane

        return next_lane


    def get_foremost_lane_in_the_same_road(self, link):
        flag_repeat = True
        while flag_repeat is True:
            next_lane = self.get_prev_lane_in_the_same_road(link)
            if next_lane is None:
                flag_repeat = False
            else:
                link = next_lane
        
        return link


    def get_endmost_lane_in_the_same_road(self, link):
        flag_repeat = True
        while flag_repeat is True:
            next_lane = self.get_next_lane_in_the_same_road(link)
            if next_lane is None:
                flag_repeat = False
            else:
                link = next_lane
        
        return link


    def find_leftmost_lane(self, link):
        while link.lane_ch_link_left is not None:
            link = link.lane_ch_link_left            
        return link


    def find_rightmost_usable_lane(self, link):
        if link.link_type_def == 'TomTom_v2105a':
            while link.link_type in ['DRIVABLE_LANE','HOV_LANE','BUS_LANE','RESTRUCTED_LANE','NON_DRIVABLE_LANE','EMERGENCY_LANE',6]:
                if link.lane_ch_link_right == None:
                    return link
                else:
                    link = link.lane_ch_link_right
                return link
        else:    
            while link.link_type in ['NORMAL','REGULAR','highway','HOV', 'DRIVABLE_SHOULDER', 'EXPRESS', 'SLOW','PASSING','REGULATED_ACCESS',6]:
                if link.lane_ch_link_right == None:
                    return link
                else:
                    link = link.lane_ch_link_right
            return link


    def find_rightmost_lane(self, link):
        while link.lane_ch_link_right is not None:
            link = link.lane_ch_link_right            
        return link


    def find_frontmost_left_lane(self, link):
        # search left for the leftmost lane
        link = self.find_leftmost_lane(link)

        # this is to prevent an inifinite loop, caused by a closed-loop road
        searched_link = list()
        searched_link.append(link)
        closed_loop_road = False

        # search for the starting point of the leftmost lane
        is_same_road = True
        while is_same_road:
            next_lane = self.get_prev_lane_in_the_same_road(link)
            if next_lane is None:
                break
            else:
                # if next_lane is already in the searched_link list, this road is a closed-loop road (circualr road)
                if next_lane in searched_link:
                    closed_loop_road = True
                    break
                    
                link = next_lane
                searched_link.append(link)

        if closed_loop_road:
            Logger.log_error('Error detected in Link: {} >> Road: {} is a closed-loop road, which is not allowed.'.format(link.idx, link.road_id, searched_link[0].idx))
            raise BaseException('Error detected in Link: {} >> Road: {} has a logical error: It is a circular (closed-loop) road, which is not allowed.'.format(link.idx, link.road_id))
            
        # necessary additional check to see if any non connected from_links exist
        # since road lanes can expand and shrink, simply traversing to a corner
        # may miss lanes that expand for left turns or shrink after right turns
        is_same_road = True
        right_links_exist = True
        while is_same_road:
            survey_results = list()
            survey_link = link

            while right_links_exist is True:
                check_result = self.get_prev_lane_in_the_same_road(survey_link)
                survey_results.append(check_result)

                if survey_link.lane_ch_link_right is None:
                    right_links_exist = False
                else:
                    survey_link = survey_link.lane_ch_link_right

            from_lane = self.pick_an_item_not_none(survey_results)
            if from_lane is None:
                is_same_road = False
            else:
                link = from_lane

        # now we reached the true frontmost left lane
        frontmost_left = link
        return frontmost_left
    

    def arclength_of_line(self, x, y):
        if len(x) != len(y):
            Logger.log_error('Check dimensions of the line')
            return

        num_segments = len(x)
        arc = 0
        for indx in range(1, num_segments):
            arc = arc + (np.sqrt((x[indx] - x[indx - 1])**2 + (y[indx] - y[indx - 1])**2))
        return arc


    def coordinate_transform_point(self, angle, point):
        rotation = np.array(((np.cos(angle), -np.sin(angle)),
            (np.sin(angle), np.cos(angle))))

        transform_pt = rotation.dot(point[0:2])
        return transform_pt


    def coordinate_transform(self, angle, line):
        rotation = np.array(((np.cos(angle), -np.sin(angle)),
            (np.sin(angle), np.cos(angle))))
        
        transform_line = np.zeros((len(line), 2))

        for indx, point in enumerate(line):
            original_pt = np.array([point[0], point[1]])
            transform_pt = rotation.dot(original_pt)
            transform_line[indx] = transform_pt

        return transform_line


    def coordinate_transform_z(self, angle, line):
        rotation = np.array(((np.cos(angle), -np.sin(angle), 0),
            (np.sin(angle), np.cos(angle), 0),
            (0, 0, 1)))
        
        transform_line = np.zeros((len(line), 3))

        for indx, point in enumerate(line):
            original_pt = np.array([point[0], point[1], point[2]])
            transform_pt = rotation.dot(original_pt)
            transform_line[indx] = transform_pt

        return transform_line

    
    def find_first_last_points(self, ref_line_mark):

        # determine first and last points for the reference line
        try:
            from_from_vector = ref_line_mark.get_from_links()[0].points[-1] - ref_line_mark.get_from_links()[0].points[-2]
            from_vector  = ref_line_mark.points[1] - ref_line_mark.points[0]
            if np.dot(from_from_vector , from_vector) <0:
                road_from_point = ref_line_mark.points[0]
            else:
                road_from_point = ref_line_mark.get_from_links()[0].points[-2]

            if len(ref_line_mark.get_from_links()) >1:
                from_link_ref_list = []
                for from_link in ref_line_mark.get_from_links():
                    if from_link.ref_true:
                        from_link_ref_list.append(from_link)
                        road_from_point = from_link.points[-2]
                
                if len(from_link_ref_list)>1:
                
                    diff_dot_list =[]
                    
                    for i in range(0, len(ref_line_mark.get_from_links())):
                        
                        from_link_second = ref_line_mark.get_from_links()[i].points[-1]
                        from_link_first = ref_line_mark.get_from_links()[i].points[-2]
                        
                        from_link_vector = from_link_second-from_link_first
                        from_link_vector_nom = from_link_vector/np.linalg.norm(from_link_vector)

                        from_node_link_second = ref_line_mark.points[1]
                        from_node_link_first = ref_line_mark.points[0]
                        
                        ref_link_vector = from_node_link_second-from_node_link_first
                        ref_link_vector_nom = ref_link_vector/np.linalg.norm(ref_link_vector)

                        diff_dot_list.append(np.dot(from_link_vector_nom, ref_link_vector_nom))
                    
                    tmp = max(diff_dot_list)
                    if tmp >0:
                        min_idx = diff_dot_list.index(tmp)
                        from_road_link = ref_line_mark.get_from_links()[min_idx]
                        road_from_point =  from_road_link.points[-2]
                    else:
                        road_from_point = ref_line_mark.points[0]

        except:
            road_from_point = ref_line_mark.points[0]
            
        try:
            to_to_vector = ref_line_mark.get_to_links()[0].points[1] - ref_line_mark.get_to_links()[0].points[0]
            to_vector  = ref_line_mark.points[-1] - ref_line_mark.points[-2]
            if np.dot(to_to_vector , to_vector) <0:
                road_to_point = ref_line_mark.points[-1]
            else:
                road_to_point =  ref_line_mark.get_to_links()[0].points[1]

            if len(ref_line_mark.get_to_links()) >1:
                
                to_link_ref_list = []
                for to_link in ref_line_mark.get_to_links():
                    if to_link.ref_true:
                        to_link_ref_list.append(to_link)
                        road_to_point = to_link.points[1]
                
                if len(to_link_ref_list)>1:
                
                    diff_dot_list =[]
                    
                    for i in range(0, len(ref_line_mark.get_to_links())):
                        
                        to_link_second = ref_line_mark.get_to_links()[i].points[1]
                        to_link_first = ref_line_mark.get_to_links()[i].points[0]
                        to_link_vector = to_link_second-to_link_first
                        to_link_vector_nom = to_link_vector/np.linalg.norm(to_link_vector)
                        
                        to_node_link_second = ref_line_mark.points[-1]
                        to_node_link_first = ref_line_mark.points[-2]
                        ref_link_vector = to_node_link_second-to_node_link_first
                        ref_link_vector_nom = ref_link_vector/np.linalg.norm(ref_link_vector)

                        diff_dot_list.append(np.dot(to_link_vector_nom, ref_link_vector_nom))
                    
                    tmp = max(diff_dot_list)
                    if tmp>0:
                        min_idx = diff_dot_list.index(tmp)
                        to_road_link = ref_line_mark.get_to_links()[min_idx]
                        road_to_point =  to_road_link.points[1]
                    else:
                        road_to_point = ref_line_mark.points[-1]
        except:
            road_to_point =  ref_line_mark.points[-1]

        # identify reference line geometry with the segmentation indices from
        # ref_line.geometry and divide the reference lane marking into user defined vectors
                
        return road_from_point, road_to_point


    def right_lane_point(self, road):
        try:
            rightmost_lane_mark = self.find_rightmost_usable_lane(road.ref_line[0]).lane_mark_right[-1]
            right_lane_to_link_road = rightmost_lane_mark.get_to_links()[0].points
            right_lane_to_point = right_lane_to_link_road[1]
        except:
            try:
                rightmost_lane_mark = self.find_rightmost_usable_lane(road.ref_line[0]).lane_mark_right[-1]
            except:
                print(self.find_rightmost_usable_lane(road.ref_line[0]))
            right_lane_to_link_road = rightmost_lane_mark.points
            right_lane_to_point =right_lane_to_link_road[-1]
        try:
            rightmost_lane_mark = self.find_rightmost_usable_lane(road.ref_line[0]).lane_mark_right[-1]
            right_lane_from_link_road = rightmost_lane_mark.get_from_links()[0].points
            right_lane_from_point = right_lane_from_link_road[-2]
        except:
            try:
                rightmost_lane_mark = self.find_rightmost_usable_lane(road.ref_line[0]).lane_mark_right[-1]
            except:
                rightmost_lane_mark = self.find_rightmost_usable_lane(road.ref_line[0])
            
            right_lane_from_link_road = rightmost_lane_mark.points
            right_lane_from_point = right_lane_from_link_road[0]
        
        try:
            right_lane = road.lanes['lane_sections'][0].lanes_R[-1].link.lane_mark_right[0]
            right_lane_point = self.find_rightmost_lane(road.ref_line[0]).lane_mark_right[-1].points
        except:
            right_lane = road.lanes['lane_sections'][0].lanes_R[-1].link
            right_lane_point = self.find_rightmost_lane(road.ref_line[0]).points

        return right_lane, right_lane_point, right_lane_from_point, right_lane_to_point, right_lane_to_link_road, right_lane_from_link_road
    
    
    def smoothing_junction_road(self, ref_line_mark):
        
        new_point_length = 0.05
        for clane_node in [ref_line_mark.from_node, ref_line_mark.to_node]:

            to_dir_lane_list = []
            from_dir_lane_list = []
            lane_list = []
            try: 
                link_list  = clane_node.to_links + clane_node.from_links
            except:
                return [], [], [], []
            for lane in clane_node.to_links + clane_node.from_links:
                if lane.ref_true == True:
                    lane_list.append(lane)
                else:
                    pass
            
            if clane_node == ref_line_mark.from_node and len(lane_list) >2:
                to_lane_dir = ref_line_mark.points[1] - ref_line_mark.points[0]
                for lane in lane_list:
                    if lane.from_node == clane_node:
                        to_lane_dir_candidate = lane.points[1] - lane.points[0]
                    else:
                        to_lane_dir_candidate = lane.points[-2] - lane.points[-1]
                    
                    if np.dot(to_lane_dir, to_lane_dir_candidate) >0:
                        to_dir_lane_list.append(lane)
                    else:
                        from_dir_lane_list.append(lane)
                  

            elif clane_node == ref_line_mark.to_node and len(lane_list) >2:
                
                to_lane_dir = ref_line_mark.points[-1] - ref_line_mark.points[-2]
                
                for lane in lane_list:
                    if lane.to_node == clane_node:
                        to_lane_dir_candidate = lane.points[-2] - lane.points[-1]
                    else:
                        to_lane_dir_candidate = lane.points[1] - lane.points[0]
                  
                    if np.dot(to_lane_dir, to_lane_dir_candidate) >0:
                        to_dir_lane_list.append(lane)
                    else:
                        from_dir_lane_list.append(lane)
                    

            to_dir_outer_point_list = []
            from_dir_outer_point_list = []
            if to_dir_lane_list != []:
                for to_lane in to_dir_lane_list:                         
                    if to_lane.from_node == clane_node:
                        f_point = to_lane.points[0]
                        sec_point = to_lane.points[1]
                        length = np.linalg.norm(f_point - sec_point)
                        if length == 0:
                            continue
                        outer_point = (sec_point*new_point_length - (new_point_length + length)*f_point)/-length
                        from_dir_outer_point_list.append(outer_point)
                    
                    else:
                        f_point = to_lane.points[-1]
                        sec_point = to_lane.points[-2]
                        length = np.linalg.norm(f_point - sec_point)
                        if length ==0:
                            continue
                        outer_point = (sec_point*new_point_length - (new_point_length + length)*f_point)/-length
                        from_dir_outer_point_list.append(outer_point)
                try:
                    opposite_dir_point = sum(from_dir_outer_point_list)/len(from_dir_outer_point_list)
                except:
                    pass
            else:
                opposite_dir_point = []

            if from_dir_lane_list !=[]:
                for from_lane in from_dir_lane_list:
                    if from_lane.to_node == clane_node:
                        f_point = from_lane.points[-1]
                        sec_point = from_lane.points[-2]
                        length = np.linalg.norm(f_point - sec_point)
                        if length ==0:
                            continue
                        outer_point = (sec_point*new_point_length - (new_point_length + length)*f_point)/-length
                        to_dir_outer_point_list.append(outer_point)
                    else:
                        f_point = from_lane.points[0]
                        sec_point = from_lane.points[1]
                        length = np.linalg.norm(f_point - sec_point)
                        if length ==0:
                            continue
                        outer_point = (sec_point*new_point_length - (new_point_length + length)*f_point)/-length
                        to_dir_outer_point_list.append(outer_point)
                try:
                    right_dir_point = sum(to_dir_outer_point_list)/len(to_dir_outer_point_list)
                except:
                    pass
            else:
                right_dir_point = []

            if clane_node == ref_line_mark.from_node:
                from_node_right_point = right_dir_point
                from_node_opposite_point = opposite_dir_point
            else:
                to_node_right_point = right_dir_point
                to_node_opposite_point = opposite_dir_point

        return from_node_right_point, from_node_opposite_point, to_node_right_point, to_node_opposite_point
        

    def non_continuous_ref_line(self, road, ref_line_mark, non_continous_to_ref_line, non_continous_from_ref_line):
        if non_continous_from_ref_line == True:
            from_road_from_point, _from_road_to_point = self.smoothing_junction_road(road.get_from_roads()[0].ref_line)
        

    def curvature(self, line):
        fir_slope_list = []
        line_points = line

        for idx in range(len(line_points)):
            if idx == len(line_points)-1:
                continue
            diff = line_points[idx+1][:2] - line_points[idx][:2]
            if list(line_points[idx+1][:2]) == list(line_points[idx][:2]):
                continue
            fir_slope_list.append(diff)
            
        fir_angle_diff_list = []
        for idx in range(len(fir_slope_list)):
            if idx == len(fir_slope_list)-1:
                continue
            cos_diff = np.dot(fir_slope_list[idx+1] , fir_slope_list[idx])/(np.linalg.norm(fir_slope_list[idx+1])*np.linalg.norm(fir_slope_list[idx]))
            
            if cos_diff >1:
                cos_diff = 1

            angle_diff = np.arccos(cos_diff)
            fir_angle_diff_list.append(angle_diff)
            
        max_angle = max(np.abs(fir_angle_diff_list))

        if  fir_angle_diff_list.index(max_angle) == len(line)-1:
            return (len(line))//2
        elif fir_angle_diff_list.index(max_angle) <4 or fir_angle_diff_list.index(max_angle) > len(line)-5:
            return (len(line))//2
        return fir_angle_diff_list.index(max_angle)

    
    def curvature_elev(self, residual):
        fir_slope_list = []
        line_points = []
        fir_angle_diff_list =residual
            
        max_angle = max(np.abs(fir_angle_diff_list))

        if  fir_angle_diff_list.index(max_angle) == len(residual)-1:
            return (len(residual))//2
        elif fir_angle_diff_list.index(max_angle) <4 or fir_angle_diff_list.index(max_angle) > len(residual)-5:
            return (len(residual))//2
        return fir_angle_diff_list.index(max_angle)
        

    def geometry_optimization(self, vector, ref_line_mark, parameter_list = []):
        
        min_max_idx_list = self.curvature(vector)
        if min_max_idx_list ==1 or min_max_idx_list == len(vector)-2:
            min_max_idx_list = len(residual)//2
        vector_1 = vector[:min_max_idx_list+2]
        vector_2 = vector[min_max_idx_list-1:]
        vector_list = [vector_1, vector_2]
        if list(vector_1[0]) == list(vector_2[0]):
            vector_list = [vector_1]
        for vector in vector_list:
            init_coord, heading, arclength, poly_geo, u, u_max, residual, to_slope = \
                self.bezier_geometry_general_boundary_all_opt(vector, ref_line_mark)
            min_max_idx_list = self.curvature(vector)

            if max(np.abs(residual)) >0.1 and len(vector)>6 and len(vector_list) !=1:
                parameter_list = self.geometry_optimization(vector, ref_line_mark, parameter_list)
                
            else:
                parameter_list.append([init_coord, heading, arclength, poly_geo, u, u_max, residual, to_slope])

        return parameter_list


    def geometry_optimization_elevation(self, vector, ref_line_mark, residual, parameter_list = []):

        min_max_idx_list = self.curvature_elev(residual)
        if min_max_idx_list ==2 or  min_max_idx_list ==1 or min_max_idx_list == len(residual)-2 or min_max_idx_list == len(residual)-1:
            min_max_idx_list = len(residual)//2
        vector_1 = vector[:min_max_idx_list+2]
        vector_2 = vector[min_max_idx_list-1:]
        vector_list = [vector_1, vector_2]
        if list(vector_1[0]) == list(vector_2[0]):
            vector_list = [vector_1]
        for vector in vector_list:
            poly_elev, check_coord_e, residual, length = self.poly_elevation_bezier_boundary_opt(vector, ref_line_mark.idx)
            
            if max(np.abs(residual)) >0.5 and len(vector) >6 and len(vector_list) ==2 and len(residual)>3:
                parameter_list = self.geometry_optimization_elevation(vector, ref_line_mark, residual, parameter_list)
            else:
                parameter_list.append([poly_elev, length])
        return parameter_list


    def geometry_optimization_super(self, vector, ref_line_mark, right_lane_point, \
                right_lane_from_link, right_lane_to_link, perpendicular_dist, parameter_list = []):
        
        poly_super = \
            self.poly_elevation_bezier_boundary_super_opt_linear(vector, right_lane_point, \
                right_lane_from_link, right_lane_to_link, perpendicular_dist)
        
        parameter_list.append([poly_super])
        
        return parameter_list


    def smoothing_points(self, ref_line_mark):
        
        if ref_line_mark.smoothing_points == True:
            
            return ref_line_mark.road_from_point, ref_line_mark.road_to_point, ref_line_mark.from_node_right_point, ref_line_mark.to_node_opposite_point
        
        else:
            from_node_point, to_node_point = self.find_first_last_points(ref_line_mark)
            from_node_right_point, from_node_opposite_point, to_node_right_point, to_node_opposite_point = self.smoothing_junction_road(ref_line_mark)
            
            if from_node_opposite_point != []:
                road_from_point = from_node_opposite_point
            else:
                road_from_point = from_node_point

            if to_node_right_point != []:
                road_to_point = to_node_right_point
            else:
                road_to_point = to_node_point
            
            ref_line_mark.smoothing_points = True
            ref_line_mark.road_from_point = road_from_point
            ref_line_mark.road_to_point = road_to_point
            ref_line_mark.from_node_right_point = from_node_right_point
            ref_line_mark.to_node_opposite_point = to_node_opposite_point
        
            return road_from_point, road_to_point, from_node_right_point, to_node_opposite_point


    def smoothing_vector(self, ref_line_mark, road):

        vector = ref_line_mark.points
        road_from_point, road_to_point, from_node_right_point, to_node_opposite_point = self.smoothing_points(ref_line_mark) 
        to_continuous_ref = False
        from_continuous_ref = False
        
        for to_lane_mark in ref_line_mark.to_node.to_links:
            if to_lane_mark.ref_true:
                to_continuous_ref = True
                
                if list(to_node_opposite_point) != []:
                    vector = np.insert(vector,-1, to_node_opposite_point, axis =0)
                if road_to_point not in vector:
                    vector = np.insert(vector, len(vector), road_to_point, axis =0)
                break
        for from_lane_mark in ref_line_mark.from_node.from_links:
            if from_lane_mark.ref_true:
                from_continuous_ref = True
                if list(from_node_right_point) != []:
                    vector = np.insert(vector, 1, from_node_right_point, axis =0)
                if road_from_point not in vector:
                    vector = np.insert(vector, 0, road_from_point, axis =0)       
                break
        if to_continuous_ref == True:
            pass
        else:
            to_main_ref_line = []
            for to_road in road.get_to_roads():
                for from_ref_line_of_to_ref_line in to_road.ref_line[0].from_node.from_links:
                    if from_ref_line_of_to_ref_line.ref_true:
                        to_main_ref_line = [from_ref_line_of_to_ref_line, to_road.ref_line[0]]
                        break
            
            if to_main_ref_line == []:
                for to_road in road.get_to_roads():
                    if to_road.from_main_ref_line !=[]:
                        to_main_ref_line = to_road.from_main_ref_line
                        if to_main_ref_line[1] in to_main_ref_line[0].to_node.to_links:
                            pass
                        else:
                            to_main_ref_line = list(reversed(to_main_ref_line))
                        break
                if to_main_ref_line ==[]:
                    if len(road.ref_line[0].to_node.to_links) >1:
                        for line in road.link_list_not_organized:
                            if len(line.to_node.from_links) ==1 and len(line.to_node.to_links) ==1:
                                to_main_ref_line = [line, line.to_node.to_links[0]]
                    else:
                        if len(road.ref_line[0].to_node.to_links) !=0:
                            to_main_ref_line = [road.ref_line[0], road.ref_line[0].to_node.to_links[0]]
                        else: 
                            to_main_ref_line = []
                            Logger.log_trace('end road id:{}'.format(road.road_id))

            if to_main_ref_line !=[]:
                if to_main_ref_line[1] in to_main_ref_line[0].get_to_links():
                    pass
                else:
                    to_main_ref_line = list(reversed(to_main_ref_line))
                road.to_main_ref_line = to_main_ref_line
                for to_road in road.get_to_roads():
                    if to_road.from_main_ref_line ==[]:
                        to_road.from_main_ref_line =to_main_ref_line

                main_road_from_point, main_road_to_point, main_from_node_right_point, main_to_node_opposite_point = self.smoothing_points(to_main_ref_line[0].lane_mark_left[0])
                
                position = to_main_ref_line[0].lane_mark_left[0].to_node.point
                if main_to_node_opposite_point == []:
                    ref_vector = (main_road_to_point[0:2] - to_main_ref_line[0].lane_mark_left[0].points[-2][0:2])/np.linalg.norm(to_main_ref_line[0].lane_mark_left[0].points[-2][0:2] - main_road_to_point[0:2])
                else:
                    ref_vector = (main_road_to_point[0:2] - main_to_node_opposite_point[0:2])/np.linalg.norm(main_to_node_opposite_point[0:2] - main_road_to_point[0:2])
                
                delete_list = []
                for point in reversed(ref_line_mark.points):
                    delete_candidate = point[0:2] - position[0:2]
                    if np.dot(delete_candidate, ref_vector) >0:
                        delete_list.append(point)
                    else:
                        break
                if len(delete_list) >0: 
                    for d_point in delete_list:
                        vector= vector[:-(len(delete_list))]
                else:
                    vector= vector[:(len(vector)-1)]
                conti_ref_line_diff_xy = np.linalg.norm(to_main_ref_line[1].lane_mark_left[0].points[1][0:2] - to_main_ref_line[0].lane_mark_left[0].points[-2][0:2])
                conti_ref_line_diff_z = to_main_ref_line[1].lane_mark_left[0].points[1][2] - to_main_ref_line[0].lane_mark_left[0].points[-2][2]

                if np.dot(road.ref_line[0].lane_mark_left[0].points[-1][0:2] - position[0:2], road.ref_line[0].lane_mark_left[0].points[-1][0:2] - road.ref_line[0].lane_mark_right[0].points[-1][0:2])>0:
                    heading_vector = self.coordinate_transform(np.pi/2, [ref_vector])
                    cum_width = 0
                    
                    if to_main_ref_line[0].road_id != road.road_id:
                        main_left_link = to_main_ref_line[1].lane_ch_link_left
                        if main_left_link == None:
                            raise BaseException('link id {} is not linked with side lane. check lane_ch_link_left'.format(to_main_ref_line[1].idx))

                        while main_left_link.lane_mark_left[0] not in ref_line_mark.to_node.to_links:
                            if main_left_link.lane_ch_link_left ==None:
                                break
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[0][0:2] - main_left_link.lane_mark_right[0].points[0][0:2])
                            main_left_link = main_left_link.lane_ch_link_left

                        if main_left_link.lane_mark_left[0] == ref_line_mark.to_node.to_links[0]:
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[0][0:2] - main_left_link.lane_mark_right[0].points[0][0:2])

                    else:
                        main_left_link = to_main_ref_line[0].lane_ch_link_left
                        if main_left_link == None:
                            raise BaseException('link id {} is not linked with side lane. check lane_ch_link_left'.format(to_main_ref_line[1].idx))

                        while main_left_link.lane_mark_left[0] != ref_line_mark:
                            if main_left_link.lane_ch_link_left ==None:
                                break
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[-1][0:2] - main_left_link.lane_mark_right[0].points[-1][0:2])
                            main_left_link = main_left_link.lane_ch_link_left

                        if main_left_link.lane_mark_left[0] == ref_line_mark:
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[-1][0:2] - main_left_link.lane_mark_right[0].points[-1][0:2])
                    
                    if abs(cum_width - np.linalg.norm(position[0:2]- road.ref_line[0].lane_mark_left[0].points[-1][0:2])) >3:

                        main_ref_width_1 = heading_vector*np.linalg.norm(position[0:2]- road.ref_line[0].lane_mark_left[0].points[-1][0:2])
                    else:
                        main_ref_width_1 = heading_vector*cum_width
                    
                    main_ref_width_1 = np.insert(main_ref_width_1[0], 2,0 )
                    # if len(vector)>1:
                    #     vector= vector[:(len(vector)-1)]
                    vector = np.insert(vector, len(vector), position + main_ref_width_1 + np.array([0,0,-position[2]  + ref_line_mark.points[-1][2]]), axis =0)
                else:
                    cum_width = 0
                    
                    if to_main_ref_line[0].road_id !=road.road_id:
                        main_left_link = to_main_ref_line[1]
                        
                        while main_left_link.lane_mark_left[0] not in ref_line_mark.to_node.to_links:
                            if main_left_link.lane_ch_link_right ==None:
                                break
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[0][0:2] - main_left_link.lane_mark_right[0].points[0][0:2])
                            main_left_link = main_left_link.lane_ch_link_right
                    else:
                        main_left_link = to_main_ref_line[0]
                        
                        while main_left_link.lane_mark_left[0] != ref_line_mark:
                            if main_left_link.lane_ch_link_right ==None:
                                break
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[-1][0:2] - main_left_link.lane_mark_right[-1].points[-1][0:2])
                            main_left_link = main_left_link.lane_ch_link_right
                
                    heading_vector = self.coordinate_transform(-np.pi/2, [ref_vector])
                    if abs(cum_width - np.linalg.norm(position[0:2]-road.ref_line[0].lane_mark_left[0].points[-1][0:2]))>3:
                        main_ref_width_2 = heading_vector*np.linalg.norm(position[0:2]-road.ref_line[0].lane_mark_left[0].points[-1][0:2])
                    else:
                        main_ref_width_2 = heading_vector*cum_width
                    
                    main_ref_width_2 = np.insert(main_ref_width_2[0], 2,0)
                    # if len(vector)>1:
                    #     vector= vector[:(len(vector)-1)]
        
                    vector = np.insert(vector, len(vector), position + main_ref_width_2 + np.array([0,0, -position[2] + ref_line_mark.points[-1][2]]), axis =0)
                
                ref_vector = np.insert(ref_vector, 2,0 ) 
                
                if ref_line_mark.to_node.to_links !=[]:
                    
                    # point_scale = np.linalg.norm(ref_line_mark.to_node.to_links[0].points[1][0:2] - vector[-2][0:2])
                    
                    # new_point = ref_line_mark.to_node.to_links[0].points[1] - ref_vector*point_scale
                    # vector[-2] = np.insert(new_point[0:2], 2, vector[-2][2])
                    # # vector= np.insert(vector, len(vector), ref_line_mark.to_node.to_links[0].points[1], axis =0)

                    point_scale = np.linalg.norm(to_main_ref_line[1].points[1][0:2] - to_main_ref_line[0].points[-2][0:2])
                    z_scale = to_main_ref_line[1].points[1][2] - to_main_ref_line[0].points[-2][2]
                    new_point = vector[-2] + ref_vector*point_scale*10
                    new_point=np.insert(new_point[0:2], 2, vector[-2][2] + z_scale*10)
                    vector= np.insert(vector, len(vector), new_point, axis =0)


                else:
                    # point_scale = np.linalg.norm(to_main_ref_line[1].points[1][0:2] - to_main_ref_line[0].points[-2][0:2])
                    # # new_point = - ref_line_mark.points[-1] + ref_vector*point_scale
                    # new_point =  vector[-2] + ref_vector*point_scale*1.5
                    # # vector[-2] = np.insert(new_point[0:2], 2, vector[-2][2])
                    # # vector[-2] = new_point
                    # vector= np.insert(vector, len(vector), new_point, axis =0)
                    point_scale = np.linalg.norm(to_main_ref_line[1].points[1][0:2] - to_main_ref_line[0].points[-2][0:2])
                    z_scale = to_main_ref_line[1].points[1][2] - to_main_ref_line[0].points[-2][2]
                    new_point = vector[-2] + ref_vector*point_scale*10
                    new_point=np.insert(new_point[0:2], 2, vector[-2][2] + z_scale*10)
                    vector= np.insert(vector, len(vector), new_point, axis =0)




        if from_continuous_ref == True:
            pass
        else:
            from_main_ref_line = []
            for from_road in road.get_from_roads():
                for to_ref_line_of_from_ref_line in from_road.ref_line[0].to_node.to_links:
                    if to_ref_line_of_from_ref_line.ref_true:
                        from_main_ref_line = [to_ref_line_of_from_ref_line, from_road.ref_line[0]]
                        break
            
            if from_main_ref_line == []:
                for from_road in road.get_from_roads():
                    if from_road.to_main_ref_line !=[]:
                        from_main_ref_line = from_road.to_main_ref_line
                        if from_main_ref_line[1] in from_main_ref_line[0].from_node.from_links:
                            pass
                        else:
                            from_main_ref_line = list(reversed(from_road.to_main_ref_line))
                        break
                
                if from_main_ref_line ==[]:
                    if len(road.ref_line[0].from_node.from_links) >1:
                        for line in road.link_list_not_organized:
                            if len(line.from_node.from_links) ==1 and len(line.from_node.to_links) ==1:
                                from_main_ref_line = [line, line.from_node.from_links[0]]
                    else:
                        if len(road.ref_line[0].from_node.from_links) !=0:
                            from_main_ref_line = [road.ref_line[0], road.ref_line[0].from_node.from_links[0]]
                        else: 
                            from_main_ref_line = []
                            Logger.log_trace('end road id:{}'.format(road.road_id))
            
            if from_main_ref_line != []:
                if from_main_ref_line[1] in from_main_ref_line[0].get_from_links():
                    pass
                else:
                    from_main_ref_line = list(reversed(from_main_ref_line))
                road.from_main_ref_line = from_main_ref_line
                for from_road in road.get_from_roads():
                    if from_road.to_main_ref_line ==[]:
                        from_road.to_main_ref_line =from_main_ref_line

                main_road_from_point, main_road_to_point, main_from_node_right_point, main_to_node_opposite_point = self.smoothing_points(from_main_ref_line[0].lane_mark_left[0])
                
                position = from_main_ref_line[0].lane_mark_left[0].from_node.point
                
                if main_from_node_right_point == []:
                    ref_vector = (from_main_ref_line[0].lane_mark_left[0].points[1][0:2]- main_road_from_point[0:2])/np.linalg.norm(from_main_ref_line[0].lane_mark_left[0].points[1][0:2] - main_road_from_point[0:2])
                else:
                    ref_vector = (main_from_node_right_point[0:2] - main_road_from_point[0:2])/np.linalg.norm(main_from_node_right_point[0:2] - main_road_from_point[0:2])

                delete_list = []
                for point in ref_line_mark.points:
                    delete_candidate = point[0:2] - position[0:2]
                    if np.dot(delete_candidate, ref_vector) <0:
                        delete_list.append(point)
                    else:
                        break
                if len(delete_list) >0:

                    for d_point in delete_list:
                        vector= vector[(len(delete_list)):]
                else:
                    
                    vector =vector[1:]

                conti_ref_line_diff_xy = np.linalg.norm(from_main_ref_line[1].lane_mark_left[0].points[-2][0:2] - from_main_ref_line[0].lane_mark_left[0].points[1][0:2])
                conti_ref_line_diff_z = from_main_ref_line[1].lane_mark_left[0].points[1][2] - from_main_ref_line[0].lane_mark_left[0].points[-2][2]
                
                #나눠지는 road 위치 
                if np.dot(road.ref_line[0].lane_mark_left[0].points[0][0:2] - position[0:2], road.ref_line[0].lane_mark_left[0].points[0][0:2] - road.ref_line[0].lane_mark_right[0].points[0][0:2])>0:
                    
                    heading_vector = self.coordinate_transform(np.pi/2, [ref_vector])
                    main_ref_width_1 = heading_vector*np.linalg.norm(position[0:2]- road.ref_line[0].lane_mark_left[0].points[0][0:2])
                    main_ref_width_1 = np.insert(main_ref_width_1[0], 2,0 )
                    # vector = vector[1:]
                    cum_width = 0
                    # 인덱스 0번이 같은 방향
                    
                    if from_main_ref_line[0].road_id != road.road_id:
                        main_left_link = from_main_ref_line[1].lane_ch_link_left
                        if main_left_link == None:
                            raise BaseException('link id {} is not linked with side lane. check lane_ch_link_left'.format(to_main_ref_line[1].idx))
                        while main_left_link.lane_mark_left[0] not in ref_line_mark.from_node.from_links:
                            if main_left_link.lane_ch_link_left ==None:
                                break
                                    
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[-1][0:2] - main_left_link.lane_mark_right[0].points[-1][0:2])
                            main_left_link = main_left_link.lane_ch_link_left
                        
                        if main_left_link.lane_mark_left[0] in ref_line_mark.from_node.from_links:
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[-1][0:2] - main_left_link.lane_mark_right[0].points[-1][0:2])
                    
                    else:
                        main_left_link = from_main_ref_line[0].lane_ch_link_left
                        if main_left_link == None:
                            raise BaseException('link id {} is not linked with side lane. check lane_ch_link_left'.format(to_main_ref_line[1].idx))
                        while main_left_link.lane_mark_left[0] != ref_line_mark:
                            if main_left_link.lane_ch_link_left ==None:
                                break
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[0][0:2] - main_left_link.lane_mark_right[0].points[0][0:2])
                            main_left_link = main_left_link.lane_ch_link_left
                        
                        if main_left_link.lane_mark_left[0] == ref_line_mark:
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[0][0:2] - main_left_link.lane_mark_right[0].points[0][0:2])

                    if abs(cum_width - np.linalg.norm(position[0:2]- road.ref_line[0].lane_mark_left[0].points[0][0:2]))>3:
                        main_ref_width_1 = heading_vector*np.linalg.norm(position[0:2]- road.ref_line[0].lane_mark_left[0].points[0][0:2])
                    else:
                        main_ref_width_1 = heading_vector*cum_width
                    main_ref_width_1 = np.insert(main_ref_width_1[0], 2,0 )
                    
                    vector = np.insert(vector, 0, position + main_ref_width_1 + np.array([0,0, -position[2]  + ref_line_mark.points[0][2]]), axis =0)
                else:
                    heading_vector = self.coordinate_transform(-np.pi/2, [ref_vector])
                    main_ref_width_2 = heading_vector*np.linalg.norm(position[0:2]-road.ref_line[0].lane_mark_left[0].points[0][0:2])
                    main_ref_width_2 = np.insert(main_ref_width_2[0], 2,0)

                    cum_width = 0
            
                    if from_main_ref_line[0].road_id != road.road_id:
                        main_left_link = from_main_ref_line[1]
                        while main_left_link.lane_mark_left[0] not in ref_line_mark.from_node.from_links:
                            if main_left_link.lane_ch_link_right ==None:
                                break
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[-1][0:2] - main_left_link.lane_mark_right[0].points[-1][0:2])
                            main_left_link = main_left_link.lane_ch_link_right
                    else:
                        main_left_link = from_main_ref_line[0]
                        while main_left_link.lane_mark_left[0] != ref_line_mark:
                            if main_left_link.lane_ch_link_right ==None:
                                break
                            cum_width += np.linalg.norm(main_left_link.lane_mark_left[0].points[0][0:2] - main_left_link.lane_mark_right[0].points[0][0:2])
                            main_left_link = main_left_link.lane_ch_link_right
                    
                    if abs(cum_width  - np.linalg.norm(position[0:2]-road.ref_line[0].lane_mark_left[0].points[0][0:2]))>3:
                        main_ref_width_2 = heading_vector*np.linalg.norm(position[0:2]-road.ref_line[0].lane_mark_left[0].points[0][0:2])
                    else:
                        main_ref_width_2 = heading_vector*cum_width
                    main_ref_width_2 = np.insert(main_ref_width_2[0], 2,0)
                    vector = np.insert(vector, 0, position + main_ref_width_2 + np.array([0,0, -position[2] + ref_line_mark.points[0][2]]), axis =0)
                
                ref_vector = np.insert(ref_vector, 2,0) 
                if ref_line_mark.from_node.from_links !=[]:
                    point_scale = np.linalg.norm(from_main_ref_line[1].points[-2][0:2] - from_main_ref_line[0].points[1][0:2])
                    z_diff = from_main_ref_line[0].points[1][2] - from_main_ref_line[1].points[-2][2] 
                    new_point = vector[1] - ref_vector*point_scale*10
                    new_point = np.insert(new_point[0:2], 2, vector[1][2] + z_diff*10)
                    vector= np.insert(vector, 0, new_point, axis =0)
                else:
                    point_scale = np.linalg.norm(from_main_ref_line[1].points[-2][0:2] - from_main_ref_line[0].points[1][0:2])
                    z_diff = from_main_ref_line[0].points[1][2] - from_main_ref_line[1].points[-2][2] 
                    new_point = vector[1] - ref_vector*point_scale*10
                    new_point = np.insert(new_point[0:2], 2, vector[1][2] + z_diff*10)
                    vector= np.insert(vector, 0, new_point, axis =0)

        return vector


    def create_geometry(self, odr_road):
        """
        Organizes vector data of each road's reference line before calculating geometries
        """
        road_residual = []
        residual_list = []
        # self.optimization_flag 
        if converter.MGeoToOdrDataConverter.get_instance().get_config('reference_line_fitting'):
            self.optimization_flag = True
        else:
            self.optimization_flag = False
        flag_smoothing_junction = True
        self.smoothing_vector_flag = mgeo_odr_converter.MGeoToOdrDataConverter.get_instance().get_config('smoothing_road')
        for _notused, road in odr_road.roads.items():
            # initialize by road
            
            s_offset = 0
            lane_length = 0
            # iterate by OdrLaneSection
            for lane_section in road.get_lane_sections():
                ref_id = lane_section.reference_line_piece.idx
                Logger.log_info('Determining geometry for Link: {}'.format(ref_id))
                
                # initialize by lane section
                ref_line = lane_section.reference_line_piece

                # starting s value calculations for each lane
                s_offset += lane_length
                lane_length = 0
                lane_section.s_offset = s_offset
                vs_offset = 0
                arclength = 0

                # check in case reference line has no lane markings
                try:
                    if ref_line.lane_mark_left != []:
                        ref_line_mark = ref_line.lane_mark_left[0]
                    else:
                        ref_line_mark = ref_line
                        Logger.log_warning('No Lane Marking found for Reference Lane {}'.format(ref_line.idx))
                except:
                    ref_line_mark = ref_line

                right_lane, right_lane_point, right_lane_from_point, right_lane_to_point, right_lane_to_link_road, right_lane_from_link_road\
                     = self.right_lane_point(road)

                right_lane_vector_list = self.segment_geometry_right(ref_line_mark, right_lane)
                perpendicular_dist = np.sqrt(sum((right_lane_point[0][:2] - ref_line_mark.points[0][:2])**2))
                # perpendicular_dist_from = np.sqrt(sum((right_lane_from_point[:2] - road_from_point[:2])**2))
                # perpendicular_dist_to = np.sqrt(sum((right_lane_to_point[:2] - road_to_point[:2])**2))
             
                residual_segment = []

                if self.smoothing_vector_flag:

                    road_vector = self.smoothing_vector(ref_line_mark, road) 
                    if len(road_vector) ==3:
                        road_vector = ref_line_mark.points
                        
                        if ref_line_mark.to_node.to_links !=[]:
                            road_vector = np.insert(road_vector, len(ref_line_mark.points), ref_line_mark.to_node.to_links[0].points[1], axis =0)
                        else:
                            road_vector = np.insert(road_vector, len(ref_line_mark.points), ref_line_mark.points[-1], axis =0)
                        
                        if ref_line_mark.from_node.from_links !=[]:
                            road_vector = np.insert(road_vector, 0, ref_line_mark.from_node.from_links[0].points[-2], axis =0)
                        else:
                            road_vector = np.insert(road_vector, 0, ref_line_mark.points[0], axis =0)
                else:
                    road_vector = ref_line_mark.points
                    
                    if ref_line_mark.to_node.to_links !=[]:
                        road_vector = np.insert(road_vector, len(ref_line_mark.points), ref_line_mark.to_node.to_links[0].points[1], axis =0)
                    else:
                        road_vector = np.insert(road_vector, len(ref_line_mark.points), ref_line_mark.points[-1], axis =0)
                    
                    if ref_line_mark.from_node.from_links !=[]:
                        road_vector = np.insert(road_vector, 0, ref_line_mark.from_node.from_links[0].points[-2], axis =0)
                    else:
                        road_vector = np.insert(road_vector, 0, ref_line_mark.points[0], axis =0)

                if self.optimization_flag:
        
                    init_coord, heading, arclength, poly_geo, u, u_max, residual, to_slope = \
                        self.bezier_geometry_general_boundary_all_opt(road_vector, ref_line_mark.idx)
                    
                    if max(np.abs(residual)) > 0.1 and len(road_vector)> 10:
                        Logger.log_trace('Large residual detected at line {}, residual: {}'.format(ref_line_mark.idx, max(np.abs(residual))))
                        parameter_list = []
                        parameter_list = self.geometry_optimization(road_vector, ref_line_mark, parameter_list = [])
                    else:
                        parameter_list = [[init_coord, heading, arclength, poly_geo, u, u_max, residual, to_slope]]
                    lane_length = 0
                    vs_offset = 0

                    for parameter in parameter_list:
                        lane_section.init_coord.append(parameter[0])
                        lane_section.heading.append(parameter[1])
                        lane_section.arclength.append(parameter[2])
                        lane_section.geometry.append(parameter[3])
                        lane_section.geometry_u_max.append(parameter[5])
                        lane_length += parameter[2]
                        lane_section.vector_s_offset.append(vs_offset)
                        vs_offset += parameter[2]
                        residual_list.append((max(np.abs(parameter[6]))))
                        residual_segment += residual_list

                    rms = np.sqrt(sum(map(lambda x: x**2, residual_segment))/len(residual_segment))
                    Logger.log_trace('- Segment RMS Residual {}'.format(rms))
                    Logger.log_trace('- Segment max Residual {}'.format(max(np.abs(residual_segment))))
                    road_residual += residual_segment

                    road.road_length = lane_length
                    lane_section.lane_length = lane_length
                    
                    right_lane_to_link = right_lane_to_link_road
                    right_lane_from_link = right_lane_from_link_road

                    vs_offset = 0
                    poly_elev, check_coord_e, residual, length = self.poly_elevation_bezier_boundary_opt(road_vector, ref_line_mark.idx)
                    
                    if max(np.abs(residual)) > 0.1 and len(road_vector)> 10:
                        parameter_list = []
                        parameter_list_elevation = self.geometry_optimization_elevation(road_vector, ref_line_mark, residual, parameter_list = [])
                    else:
                        parameter_list_elevation = [[poly_elev, length]]
                    elevation_soffset = 0
                    for parameter in parameter_list_elevation:
                        
                        lane_section.elevation.append(parameter[0])

                        lane_section.elevation_soffset.append(elevation_soffset)
                        elevation_soffset += parameter[1]

                    parameter_list_super = self.geometry_optimization_super(road_vector, ref_line_mark, right_lane_point, \
                        right_lane_from_link, right_lane_to_link, perpendicular_dist,  parameter_list = [])
                
                    for parameter in parameter_list_super:
                        lane_section.lateral.append(parameter[0])
                else:
                    # vector_list = self.segment_geometry(ref_line_mark, ref_line_mark)
                    # run poly_geometry and poly_elevation
                    road_from_point = road_vector[0]
                    road_to_point = road_vector[-1]
                    # vector_list = self.segment_geometry(ref_line_mark, ref_line_mark)
                    vector_list = self.segment_geometry_opt(ref_line_mark, road_vector[1:-1])
                    geometry_type = ref_line_mark.geometry[0]['method']
                    for i in range(len(vector_list)):
                        vector = vector_list[i]
                        # geometry_type = ref_line_mark.geometry[i]['method']
                        # update sOffset 
                        vs_offset += arclength
                        lane_section.vector_s_offset.append(vs_offset)

                        # allocate points to determine boundary conditions
                        if len(vector_list) == 1:
                            from_point = road_from_point
                            to_point = road_to_point
                            right_lane_to_link = right_lane_to_link_road
                            right_lane_from_link = right_lane_from_link_road   
                        else:
                            if i == 0:
                                from_point = road_from_point
                                to_point = vector_list[i+1][1]
                                right_lane_to_link = right_lane_point
                                right_lane_from_link = right_lane_from_link_road
                            elif i == len(vector_list)-1:
                                to_point = road_to_point
                                from_point = vector_list[i-1][-2]
                                right_lane_from_link = right_lane_point
                                right_lane_to_link = right_lane_to_link_road
                            else:
                                from_point = vector_list[i-1][-2]
                                to_point = vector_list[i+1][1]
                                right_lane_to_link = right_lane_point
                                right_lane_from_link = right_lane_point
                       
                        # fit for one of paramPoly3, poly3, or line
                        if geometry_type == 'paramPoly3':
                            # paramPoly3
                        
                            init_coord, heading, arclength, poly_geo, uv_point, residual, to_slope = \
                                self.bezier_geometry_general_boundary_all(vector, to_point, from_point, ref_line_mark.idx)

                            if max(np.abs(residual)) > 0.1:
                                Logger.log_trace('Large residual detected at line {}, residual: {}'.format(ref_line_mark.idx, max(np.abs(residual))))

                                init_coord, heading, arclength, poly_geo, uv_point, residual, to_slope = \
                                    self.bezier_geometry_general_boundary_all(vector[:len(vector)//2 +1], vector[len(vector)//2+1], from_point, ref_line_mark.idx)

                                residual_segment += residual.tolist()
                                u = uv_point[:,0]
                                u_max = uv_point[-1][0]

                                poly_elev, check_coord_e = \
                                    self.poly_elevation_bezier_boundary(vector[:len(vector)//2 +1], vector[len(vector)//2+1], from_point)
                                lane_length += arclength
                                
                                if i == len(vector_list)-1:
                                    right_lane_to_link = right_lane_point
                                
                                poly_super = \
                                    self.poly_elevation_bezier_boundary_super(vector[:len(vector)//2 +1], right_lane_point, vector[len(vector)//2+1], from_point \
                                        ,right_lane_from_link, right_lane_to_link \
                                            , perpendicular_dist, i)

                                lane_section.init_coord.append(init_coord)
                                lane_section.heading.append(heading)
                                lane_section.arclength.append(arclength)
                                lane_section.geometry.append(poly_geo)
                                lane_section.geometry_u_max.append(u_max)
                                lane_section.elevation.append(poly_elev)
                                lane_section.lateral.append(poly_super)

                                Logger.log_trace('split residual 1 {}'.format(max(np.abs(residual))))

                                # update vs_offset values
                                vs_offset += arclength
                                lane_section.vector_s_offset.append(vs_offset)

                                # fit second segment
                                init_coord, heading, arclength, poly_geo, uv_point ,residual, to_slope= \
                                    self.bezier_geometry_general_boundary_all(vector[len(vector)//2:], to_point, vector[len(vector)//2-1], ref_line_mark.idx)
                                
                                residual_segment += residual.tolist()
                                u = uv_point[:,0]
                                u_max = uv_point[-1][0]

                                poly_elev, check_coord_e = \
                                    self.poly_elevation_bezier_boundary(vector[len(vector)//2:], to_point, vector[len(vector)//2-1])
                                
                                lane_length += arclength
                                
                                right_lane_from_link = right_lane_point
                                if i == len(vector_list)-1:
                                    right_lane_to_link = right_lane_to_link_road
                                
                                poly_super = \
                                    self.poly_elevation_bezier_boundary_super(vector[len(vector)//2:], right_lane_point, to_point, vector[len(vector)//2-1] \
                                        ,right_lane_from_link, right_lane_to_link \
                                            , perpendicular_dist, i)
                                
                                Logger.log_trace('End point boundary slope value {}'.format(to_slope))
                                Logger.log_trace('split residual 2 {}'.format(max(np.abs(residual))))

                            else:
                                # we stick with the initial fit results
                                residual_segment += residual.tolist()
                                u = uv_point[:,0]
                                u_max = uv_point[-1][0]

                                poly_elev, check_coord_e = \
                                    self.poly_elevation_bezier_boundary(vector, to_point, from_point)
                                
                                poly_super = \
                                    self.poly_elevation_bezier_boundary_super(vector, right_lane_point, to_point, from_point \
                                        ,right_lane_from_link, right_lane_to_link, \
                                            perpendicular_dist, i)

                                lane_length += arclength
                        
                        elif geometry_type == 'poly3':
                            init_coord, heading, arclength, poly_geo, uv_point, lat_misc_fit_result = \
                                self.poly_geometry(vector)
                            
                            u = uv_point[:,0]
                            u_max = uv_point[-1][0]
                            lane_length += arclength

                            poly_elev, check_coord_e, ele_misc_fit_result = \
                                self.poly_elevation(vector)

                            poly_super = \
                                    self.poly_elevation_bezier_boundary_super(vector, right_lane_point, to_point, from_point \
                                        ,right_lane_from_link, right_lane_to_link, \
                                            perpendicular_dist, i)

                            self.check_accuracy(ref_id, i, u, u_max, lat_misc_fit_result, ele_misc_fit_result)

                        else:
                            # designated as a line
                            init_coord, heading, arclength, poly_geo, uv_point, lat_misc_fit_result = \
                                self.poly_geometry(vector, linear=True)

                            u_max = uv_point[-1][0]
                            lane_length += arclength

                            poly_elev, check_coord_e, ele_misc_fit_result = \
                                self.poly_elevation(vector)

                            poly_super = \
                                    self.poly_elevation_bezier_boundary_super(vector, right_lane_point, to_point, from_point \
                                        ,right_lane_from_link, right_lane_to_link, \
                                            perpendicular_dist, i)
                            
                        # save to OdrLaneSection
                        lane_section.init_coord.append(init_coord)
                        lane_section.heading.append(heading)
                        lane_section.arclength.append(arclength)
                        lane_section.geometry.append(poly_geo)
                        lane_section.geometry_u_max.append(u_max)
                        lane_section.elevation.append(poly_elev)
                        lane_section.lateral.append(poly_super)
                        # lane length is sum of vector arclengths
                        # lane_length += arclength
                        if geometry_type == 'paramPoly3':
                            rms = np.sqrt(sum(map(lambda x: x**2, residual_segment))/len(residual_segment))
                            Logger.log_trace('- Segment RMS Residual {}'.format(rms))
                            Logger.log_trace('- Segment max Residual {}'.format(max(np.abs(residual_segment))))
                            road_residual += residual_segment
                    # assign a total lane length (sum of all arclengths)
                    lane_section.lane_length = lane_length
                    
                    # check rotation and polyfit results
                    if (self.CHK is True
                        and road.road_id in self.CHK_ID):
                        self.check_geometry(uv_point, check_coord_e, poly_geo, poly_elev)
                        Logger.log_info('Checking: Road {}'.format(road.road_id))
                    
                    # # check residuals and error
                    # if geometry_type == 'paramPoly3':
                    #     rms = np.sqrt(sum(map(lambda x: x**2, residual_segment))/len(residual_segment))
                    #     Logger.log_trace('- Segment RMS Residual {}'.format(rms))
                    #     Logger.log_trace('- Segment max Residual {}'.format(max(np.abs(residual_segment))))
                    #     road_residual += residual_segment

                    # assign rest of OdrRoad properties
                    road.road_length = s_offset + lane_length
                
                   
    
        rms = np.sqrt(sum(map(lambda x: x**2, road_residual))/len(road_residual))
        Logger.log_info('- Road RMS Residual {}'.format(rms))
        Logger.log_info('- Road max Residual {}'.format(sorted(np.abs(road_residual))[-len(road_residual)//200:]))



    def check_accuracy(self, id, segment, u, u_max, lat_fit, elev_fit):
        # check polyfit results
        residual_threshold = 0.1
        try:
            if u.max() != u_max:
                Logger.log_error('polyfit will not work for this lane section. u is not monotonically increasing.') 
        except Exception as ex:
            raise ex
        
        if len(lat_fit[0]) == 1:
            lat_res = lat_fit[0][0]
        elif len(lat_fit[0]) == 0:
            lat_res = 0
        else:
            raise BaseException('  - unexpected residuals form. len(lat_misc_fit_result[0]) = {}'.format(len(lat_fit[0])))

        if lat_res > residual_threshold:
            Logger.log_warning('  - Link: {}, geometry[{}], fitting residuals (higher than threshold = 0.1) lateral: {:8.5f}'.format(id, segment, lat_res))
        else:
            Logger.log_debug('  - fitting residuals lateral: {}'.format(lat_res))
        
        if len(elev_fit[0]) == 1:
            ele_res = elev_fit[0][0]
        elif len(elev_fit[0]) == 0:
            ele_res = 0
        else:
            raise BaseException('  - unexpected residuals form. len(ele_misc_fit_result[0]) = {}'.format(len(elev_fit[0])))

        if ele_res > residual_threshold:
            Logger.log_warning('  - Link: {}, geometry[{}], fitting residuals (higher than threshold = 0.1) elevation: {:8.5f} '.format(id, segment, ele_res))
        else:
            Logger.log_debug('  - fitting residuals elevation: {}'.format(ele_res))

    def segment_geometry_right(self, reference_line, current_line):
        '''
        Divides an input vector [current_line] according to the geometry indexes of
        the [reference_line]
        '''
        vector_list = list()
        ref_vector_list = []
       
        if len(reference_line.geometry) <= 1:
            # reference line is a single vector, pass it
            vector_list.append(current_line.points)
        else:
            # else vector geometry is segmented
            geometry = reference_line.geometry
            
            for cnt in range(len(geometry)):
                if cnt == len(geometry)-1:
                    slice_id = [geometry[cnt]['id'], len(current_line.points)]
                else:
                    slice_id = [geometry[cnt]['id'], geometry[cnt+1]['id']+1]

                vector_list.append(current_line.points[slice_id[0]:slice_id[1], :])
                ref_vector_list.append((reference_line.points[slice_id[0]:slice_id[1], :]))
        
        return vector_list


    def segment_geometry(self, reference_line, current_line):
        '''
        Divides an input vector [current_line] according to the geometry indexes of
        the [reference_line]
        '''
        vector_list = list()

        if len(reference_line.geometry) <= 1:
            # reference line is a single vector, pass it
            vector_list.append(current_line.points)
        else:
            # else vector geometry is segmented
            geometry = reference_line.geometry

            for cnt in range(len(geometry)):
                if cnt == len(geometry)-1:
                    slice_id = [geometry[cnt]['id'], len(reference_line.points)]
                else:
                    slice_id = [geometry[cnt]['id'], geometry[cnt+1]['id']+1]

                vector_list.append(current_line.points[slice_id[0]:slice_id[1], :])

        return vector_list


    def segment_geometry_opt(self, reference_line, vector):
        '''
        Divides an input vector [current_line] according to the geometry indexes of
        the [reference_line]
        '''

        vector_list = list()
        if len(vector)>7:
            for i in range(len(vector)//4):
                if i == len(vector)//4 -1:
                    vector_list.append(vector[4*i:])
                else:
                    vector_list.append(vector[4*i:4*i+4])
        else:
            return [vector]


        # if len(reference_line.geometry) <= 1:
        #     # reference line is a single vector, pass it
        #     vector_list.append(vector)
        # else:
        #     # else vector geometry is segmented
        #     geometry = reference_line.geometry

        #     for cnt in range(len(geometry)):
        #         if cnt == len(geometry)-1:
        #             slice_id = [geometry[cnt]['id'], len(vector)]
        #         else:
        #             slice_id = [geometry[cnt]['id'], geometry[cnt+1]['id']+1]

        #         vector_list.append(vector[slice_id[0]:slice_id[1], :])

        return vector_list

    
    def get_linearity(self, x, y, angle, is_linear=False):
        """
        Determines all vectors within a line are aligned within [angle] degrees

        Arguments:
        x: list of all vector x coordinates
        y: list of all vector y coordinates
        angle: the minimum angle allowed to be considered linear [degrees]
        is_linear: passed when the user needs a linear output
        """
        if is_linear is True:
            return True

        x = x - x[0]
        y = y - y[0]
        min_angle = np.deg2rad(angle)  # determines linearity condition
        for i in range(len(x) - 1):
            cross_prod_2d = x[i]*y[i+1] - x[i+1]*y[i]
            cross_mag = np.sqrt(cross_prod_2d**2)
            mag = np.sqrt((x[i]**2 + y[i]**2) * (x[i+1]**2 + y[i+1]**2))
            threshold = np.sin(min_angle) * mag
            if cross_mag > threshold:
                return False
        return True


    def find_distance(self, x, y):
        # because in OpenDRIVE, right > 0, and left < 0 we multiply the final distance
        # (the A coefficient value) value by (-1)
        distance = np.sqrt(x**2 + y**2)
        if y > 0:
            distance = distance*(-1)
        return distance
     

    def poly3_func(self, coefficient,t):
        return coefficient[0] +coefficient[1]*t +coefficient[2]*(t**2)+coefficient[3]*(t**3)
     

    def super_elevation(self, line_s_coord, poly_elev, right_lane_poly_elev, perpendicular_dist):
        
        ref_elev_first = self.poly3_func(poly_elev,0)
        ref_elev_middle = self.poly3_func(poly_elev,1/2*line_s_coord[-1])
        ref_elev_last = self.poly3_func(poly_elev,line_s_coord[-1])
        
        right_ref_elev_first = self.poly3_func(right_lane_poly_elev,0)
        right_ref_elev_middle = self.poly3_func(right_lane_poly_elev,1/2*line_s_coord[-1])
        right_ref_elev_last = self.poly3_func(right_lane_poly_elev,*line_s_coord[-1])

        ref_elev_first_dt = self.poly3_func(poly_elev,0.1*line_s_coord[-1])
        ref_elev_last_dt = self.poly3_func(poly_elev,0.9*line_s_coord[-1])

        right_ref_elev_first_dt = self.poly3_func(right_lane_poly_elev,0.1*line_s_coord[-1])
        right_ref_elev_last_dt = self.poly3_func(right_lane_poly_elev,0.9*line_s_coord[-1])

        super_elev_first = np.arctan2(ref_elev_first - right_ref_elev_first, perpendicular_dist) 
        super_elev_middle= np.arctan2(ref_elev_middle - right_ref_elev_middle, perpendicular_dist)
        super_elev_last = np.arctan2(ref_elev_last - right_ref_elev_last, perpendicular_dist)
        
        super_elev_first_dt = np.arctan2(ref_elev_first_dt - right_ref_elev_first_dt, perpendicular_dist)
        super_elev_last_dt = np.arctan2(ref_elev_last_dt - right_ref_elev_last_dt, perpendicular_dist)

        super_elev_slope_first = (super_elev_first_dt - super_elev_first ) / (line_s_coord[-1]*0.1)
        super_elev_slope_last = (super_elev_last - super_elev_last_dt ) / (line_s_coord[-1]*0.1)
        
        x = line_s_coord[-1]
        y = super_elev_last
        y_prime = super_elev_slope_last

        a = super_elev_last
        b = super_elev_slope_first
        d =(y_prime - b + 2*(-y + a+ b*x  )/x )/(x**2)
        c = (y - d*(x**3) - (a+ b*x))/(x**2)
        
        poly_super_elev = np.array([a, b, c, d])

        return poly_super_elev


    def till_length(self, data):
        till_length = 0
        for j in range(1, len(data)):
            till_length += np.sqrt((data[j][0] - data[j-1][0])**2 + (data[j][1] - data[j-1][1])**2)
        return till_length
    

    def residual_exact(self, coeff_out, point, dt=100):
        x = 0
        width_list= []
        dx = point[:,0][-1]/dt
        
        for idx, line_fir in enumerate(point):
            length = 10000
            for i in range(dt):
                x_n = x + dx*i
                y_n = (coeff_out[0]+ coeff_out[1]*(x_n)+ coeff_out[2]*(x_n**2) + coeff_out[3]*(x_n**3))
                    
                if length > np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2):
                    length = np.sqrt((y_n - line_fir[1])**2 + (x_n -line_fir[0] )**2)
                else:
                    width_list.append(length)
                    break
        
        return width_list


    def residual(self, coeff_out, line_x_coord, line_y_coord ):
        return coeff_out[0]*(line_x_coord**2) + coeff_out[1]*(line_x_coord**3) - line_y_coord


    def poly(self, line_x_coord, line_y_coord, to_slope=0):
        x = line_x_coord[-1]
        y = line_y_coord[-1]
        if to_slope == 0:
            to_slope = (line_y_coord[-1] - line_y_coord[-2]) / (line_x_coord[-1] - line_x_coord[-2])
        d = ((to_slope - 2*(y/x))/(x**2))
        c = y/(x**2) - d*x
        coeff_out = np.array([c, d])

        return coeff_out


    def curve_length(self, line_x_coord, coeff_out, half=True, dt=1000):
        x = 0
        y = 0 
        dx = line_x_coord[-1]/dt
        whole_length = 0
        for i in range(dt):
            x_n = x + dx
            y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                 
            whole_length += np.sqrt((y_n - y)**2 + dx**2)
            y = y_n
            x = x_n
    
        length = 0
        x = 0
        y = 0
        while True:
            x_n = x + dx
            y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
            length += np.sqrt((y_n - y)**2 + dx**2)
            y = y_n
            x = x_n
            if length > whole_length/2 > 0:
                return whole_length, length, [x, y]


    def bezier_geometry_general_boundary_all(self, lane_vector, to_point, from_point, idx):
        lane_vector = lane_vector[:,0:2]
        
        x_init = lane_vector[0][0]
        y_init = lane_vector[0][1]
        
        init_coord = np.array([x_init, y_init])
        line_moved_origin = lane_vector - init_coord
        from_point = lane_vector[0]
        to_point = lane_vector[-1]
        from_point_moved = from_point - init_coord
        to_point_moved = to_point - init_coord

        from_u =  (line_moved_origin[1][0] + line_moved_origin[0][0])/2 - (from_point_moved[0] +  line_moved_origin[0][0])/2
        from_v = (line_moved_origin[1][1] + line_moved_origin[0][1])/2  - (from_point_moved[1] +  line_moved_origin[0][1])/2

        from_heading = np.arctan2(from_v, from_u) 
        from_inv_heading = (-1) * from_heading

        rotated_line = self.coordinate_transform(from_inv_heading, line_moved_origin)
        rotated_to_point_moved = self.coordinate_transform(from_inv_heading, [to_point_moved])
        
        arc = self.arclength_of_line(line_moved_origin[:,0], line_moved_origin[:,1])
        arclength = arc + 0.1  # forced connections b/n roads
    
        line_x_coord = rotated_line[:,0]
        line_y_coord = rotated_line[:,1]
        if ( (rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 - (rotated_line[-2][0] + rotated_line[-1][0])/2 ) == 0:
            print(idx)
        # determine bezier curves
        a = 0
        b = ((rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 -  (rotated_line[-2][1] + rotated_line[-1][1])/2) \
            / ( (rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 - (rotated_line[-2][0] + rotated_line[-1][0])/2 )

        if np.abs(b) < 10**(-5):
            whole_length, length, maxpoint = self.curve_length(line_x_coord,self.poly(line_x_coord, line_y_coord, to_slope=b), dt=100000)
        else:
            whole_length, length, maxpoint = self.curve_length(line_x_coord,self.poly(line_x_coord, line_y_coord, to_slope=b))

        residual = self.residual(self.poly(line_x_coord, line_y_coord, to_slope=b), line_x_coord, line_y_coord)
        arclength = whole_length
        
        if b == 0 or np.abs(b) < 10**(-6):
            poly_out = [0, 0, 0 ,0, 0, 0, 0, 0]
            return init_coord, from_heading, arclength, poly_out, rotated_line, residual, b

        if (max(line_x_coord) > line_x_coord[-1]):
            min = whole_length
            
            for i in range(2, len(rotated_line)):
                if np.abs(self.till_length(rotated_line[:i]) - self.till_length(rotated_line)/2) < min:
                    min = np.abs(self.till_length(rotated_line[:i]) - self.till_length(rotated_line)/2)
                    maxpoint = rotated_line[i]

        x_t = (8*(maxpoint[1]- a*maxpoint[0]) + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))
        x_k = (8*maxpoint[0] - 3*x_t - rotated_line[-1][0]) / 3
        y_k = a*x_k
        y_t = b*(x_t - rotated_line[-1][0]) + rotated_line[-1][1]
        
        line_x_coord = [line_x_coord[0], x_k, x_t, line_x_coord[-1]]
        line_y_coord = [line_y_coord[0], y_k, y_t, line_y_coord[-1]]

        dU = line_x_coord[3] - 3*line_x_coord[2] + 3*line_x_coord[1]
        cU = 3*line_x_coord[2] - 6*line_x_coord[1]
        bU = 3*line_x_coord[1]

        dV = line_y_coord[3] - 3*line_y_coord[2]
        cV = 3*line_y_coord[2]
        poly_out = [0, bU, cU ,dU, 0, 0, cV, dV]
        
        return init_coord, from_heading, arclength, poly_out, rotated_line, residual, b


    def bezier_geometry_general_boundary_all_opt(self, lane_vector, ref_line_mark):
        
      
        from_point = lane_vector[0][0:2]
        to_point = lane_vector[-1][0:2]
        lane_vector = lane_vector[1:-1,0:2]
      
        x_init = lane_vector[0][0]
        y_init = lane_vector[0][1]
        
        init_coord = np.array([x_init, y_init])
        line_moved_origin = lane_vector - init_coord
        
        from_point_moved = from_point - init_coord
        to_point_moved = to_point - init_coord

        from_u =  (line_moved_origin[1][0] + line_moved_origin[0][0])/2 - (from_point_moved[0] +  line_moved_origin[0][0])/2
        from_v = (line_moved_origin[1][1] + line_moved_origin[0][1])/2  - (from_point_moved[1] +  line_moved_origin[0][1])/2

        from_heading = np.arctan2(from_v, from_u) 
        from_inv_heading = (-1) * from_heading

        rotated_line = self.coordinate_transform(from_inv_heading, line_moved_origin)
        rotated_to_point_moved = self.coordinate_transform(from_inv_heading, [to_point_moved])
        
        arc = self.arclength_of_line(line_moved_origin[:,0], line_moved_origin[:,1])
        arclength = arc + 0.1  # forced connections b/n roads
        
        u = rotated_line[:,0]
        u_max = rotated_line[-1][0]

        line_x_coord = rotated_line[:,0]
        line_y_coord = rotated_line[:,1]
        if ( (rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 - (rotated_line[-2][0] + rotated_line[-1][0])/2 ) == 0:
            print(ref_line_mark)
        # determine bezier curves
        a = 0
        b = ((rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 -  (rotated_line[-2][1] + rotated_line[-1][1])/2) \
            / ( (rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 - (rotated_line[-2][0] + rotated_line[-1][0])/2 )

        if np.abs(b) < 10**(-5):
            whole_length, length, maxpoint = self.curve_length(line_x_coord,self.poly(line_x_coord, line_y_coord, to_slope=b), dt=100000)
        else:
            whole_length, length, maxpoint = self.curve_length(line_x_coord,self.poly(line_x_coord, line_y_coord, to_slope=b))

        residual = self.residual(self.poly(line_x_coord, line_y_coord, to_slope=b), line_x_coord, line_y_coord)
        arclength = whole_length
        
        if b == 0 or np.abs(b) < 10**(-6):
            poly_out = [0, 0, 0 ,0, 0, 0, 0, 0]
            return init_coord, from_heading, arclength, poly_out, u, u_max, residual, b

        if (max(line_x_coord) > line_x_coord[-1]):
            min = whole_length
            
            for i in range(2, len(rotated_line)):
                if np.abs(self.till_length(rotated_line[:i]) - self.till_length(rotated_line)/2) < min:
                    min = np.abs(self.till_length(rotated_line[:i]) - self.till_length(rotated_line)/2)
                    maxpoint = rotated_line[i]

        x_t = (8*(maxpoint[1]- a*maxpoint[0]) + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))
        x_k = (8*maxpoint[0] - 3*x_t - rotated_line[-1][0]) / 3
        y_k = a*x_k
        y_t = b*(x_t - rotated_line[-1][0]) + rotated_line[-1][1]
        
        line_x_coord = [line_x_coord[0], x_k, x_t, line_x_coord[-1]]
        line_y_coord = [line_y_coord[0], y_k, y_t, line_y_coord[-1]]

        dU = line_x_coord[3] - 3*line_x_coord[2] + 3*line_x_coord[1]
        cU = 3*line_x_coord[2] - 6*line_x_coord[1]
        bU = 3*line_x_coord[1]

        dV = line_y_coord[3] - 3*line_y_coord[2]
        cV = 3*line_y_coord[2]
        poly_out = [0, bU, cU ,dU, 0, 0, cV, dV]
        
        

        return init_coord, from_heading, arclength, poly_out, u, u_max, residual, b


    def poly_geometry(self, lane_vector, linear=False):
        # strip away elevation coordinate values
        # ref_vector = ref_vector[:,0:2]
        lane_vector = lane_vector[:,0:2]

        # establish the initial point of the reference vector as the swivel point
        # ref_x_init = ref_vector[0][0]
        # ref_y_init = ref_vector[0][1]
        x_init = lane_vector[0][0]
        y_init = lane_vector[0][1]

        # transform initial point to origin
        # init_coord = np.array([ref_x_init, ref_y_init])
        init_coord = np.array([x_init, y_init])

        # ref_line_moved_origin = ref_vector - init_coord
        line_moved_origin = lane_vector - init_coord

        # get the heading for line segment individual_lane
        # u = ref_line_moved_origin[1][0]
        # v = ref_line_moved_origin[1][1]
        u = line_moved_origin[1][0]
        v = line_moved_origin[1][1]
        heading = np.arctan2(v, u)  # heading is in radians

        # get the arc length for each line segment individual_lane
        arc = self.arclength_of_line(line_moved_origin[:,0], line_moved_origin[:,1])
        arclength = arc + 0.1  # forced connections b/n roads

        # rotate the line coordinates by the heading
        inv_heading = (-1) * heading
        rotated_line = self.coordinate_transform(inv_heading, line_moved_origin)

        # arrange coordinates for polynomial fitting
        line_x_coord = rotated_line[:,0]
        line_y_coord = rotated_line[:,1]
        
        # distance (used only when linear)
        width = self.find_distance(line_x_coord[0], line_y_coord[0])

        # check for linearity
        # linearity = self.get_linearity(poly_x_coord, poly_y_coord, 0.1)
        linearity = self.get_linearity(line_x_coord, line_y_coord, 0.1, linear)

        # determine type of fit to use
        if linearity is True:
            poly_out = np.array([0, 0, 0, 0])
            misc_fit_result = (np.array([0]) ,) # TODO(sglee): temporary value!
        else:
            # refer to documentation for Polynomial.fit
            # https://numpy.org/doc/stable/reference/generated/numpy.polynomial.polynomial.Polynomial.fit.html?highlight=polynomial%20fit#numpy.polynomial.polynomial.Polynomial.fit
            series, misc_fit_result = np.polynomial.polynomial.Polynomial.fit(
                line_x_coord,
                line_y_coord,
                3,
                full=True
            )
            # residuals = misc_fit_result[0]
            poly_out = series.convert().coef

        return init_coord, heading, arclength, poly_out, rotated_line, misc_fit_result


    def poly_elevation_bezier_boundary_opt(self, lane_vector, idx):
        
        from_point = lane_vector[0]
        to_point = lane_vector[-1]
        # lane_vector = lane_vector[1:-1,0:2]
        lane_vector = lane_vector[1:-1,:]
        lane_vector_xy = lane_vector[:,0:2]
        
        # transform initial point to origin
        global_x_init = lane_vector_xy[0][0]
        global_y_init = lane_vector_xy[0][1]
        init_coord = np.array([global_x_init, global_y_init])

        line_moved_origin = lane_vector_xy - init_coord

        from_h_point = from_point[2]
        to_h_point = to_point[2]
        from_point_xy = from_point[:2]
        to_point_xy = to_point[:2]
        
        from_point_moved = from_point_xy - init_coord
        to_point_moved =  to_point_xy - init_coord 
        
        line_x_coord = line_moved_origin[:,0]
        line_y_coord = line_moved_origin[:,1]

        line_s_coord = np.sqrt(np.power(line_x_coord,2)
            + np.power(line_y_coord, 2))
        
        line_h_coord = lane_vector[:,2]

        check_coord = np.array([line_s_coord, line_h_coord])

        x = line_s_coord[-1]
        y = line_h_coord[-1]
       
        try:
            y_prime = (to_h_point - line_h_coord[-2]) / np.sqrt((to_point_moved[0]- line_x_coord[-2])**2 +  (to_point_moved[1]- line_y_coord[-2])**2)
        except:
            raise BaseException('points of lane_boundary id: {} need to be tied up'.format(idx))
        a = line_h_coord[0]
        
        b = (line_h_coord[1] - from_h_point)/ np.sqrt((line_x_coord[1] - from_point_moved[0])**2 +  (line_y_coord[1] - from_point_moved[1])**2)
       
        d =(y_prime - b + 2*(-y + a+ b*x  )/x )/(x**2)
        c = (y - d*(x**3) - (a+ b*x))/(x**2)
        
        

        poly_out = np.array([a, b, c, d])
        line_points = []

        for s_coord, h_coord in zip(line_s_coord, line_h_coord):
            line_points.append(np.array([s_coord, h_coord]))
        line_points = np.array(line_points)

        residual = self.residual_exact(poly_out, line_points)


        return poly_out, check_coord, residual, line_s_coord[-1]


    def poly_elevation_bezier_boundary(self, lane_vector, to_point, from_point):
        
        lane_vector_xy = lane_vector[:,0:2]
        
        # transform initial point to origin
        global_x_init = lane_vector_xy[0][0]
        global_y_init = lane_vector_xy[0][1]
        init_coord = np.array([global_x_init, global_y_init])

        line_moved_origin = lane_vector_xy - init_coord

        from_h_point = from_point[2]
        to_h_point = to_point[2]
        from_point_xy = from_point[:2]
        to_point_xy = to_point[:2]
        
        from_point_moved = from_point_xy - init_coord
        to_point_moved =  to_point_xy - init_coord 
        
        line_x_coord = line_moved_origin[:,0]
        line_y_coord = line_moved_origin[:,1]

        line_s_coord = np.sqrt(np.power(line_x_coord,2)
            + np.power(line_y_coord, 2))
        
        line_h_coord = lane_vector[:,2]

        check_coord = np.array([line_s_coord, line_h_coord])

        x = line_s_coord[-1]
        y = line_h_coord[-1]
        y_prime = (to_h_point - line_h_coord[-2]) / np.sqrt((to_point_moved[0]- line_x_coord[-2])**2 +  (to_point_moved[1]- line_y_coord[-2])**2)
        
        a = line_h_coord[0]
        b = (line_h_coord[1] - from_h_point)/ np.sqrt((line_x_coord[1] - from_point_moved[0])**2 +  (line_y_coord[1] - from_point_moved[1])**2)
        d =(y_prime - b + 2*(-y + a+ b*x  )/x )/(x**2)
        c = (y - d*(x**3) - (a+ b*x))/(x**2)
        
        poly_out = np.array([a, b, c, d])

        return poly_out, check_coord 
    

    def get_angle(self, ref_point, right_lane, perpendicular_dist):
         
        right_lane_index, min_dist = self.get_closest_pt_on_line_index_dist(right_lane, ref_point)
        if min_dist > (perpendicular_dist**2)*1.5:
            reversed_right_lane = []
            for i in reversed(range(len(right_lane))):
                reversed_right_lane.append(list(right_lane[i]))
            right_lane_index, min_dist = self.get_closest_pt_on_line_index_dist(reversed_right_lane, ref_point)
            right_height = right_lane[len(right_lane)-right_lane_index-1][2]
        else:
            right_height = right_lane[right_lane_index][2]
        return np.arctan2(ref_point[2] - right_height, perpendicular_dist)


    def get_angle_height_over_perpendi(self,ref_point, right_lane, perpendicular_dist):

        return np.arctan2(ref_point[2] - right_lane[2], perpendicular_dist)


    def poly_elevation_bezier_boundary_super_opt(self, lane_vector, right_lane_point, \
        right_lane_from_link, right_lane_to_link, perpendicular_dist):
        
        from_point = lane_vector[0]
        to_point = lane_vector[-1]
        # lane_vector = lane_vector[1:-1,0:2]
        
        lane_vector_xy = lane_vector[:,0:2]
        
        # transform initial point to origin
        global_x_init = lane_vector_xy[0][0]
        global_y_init = lane_vector_xy[0][1]
        init_coord = np.array([global_x_init, global_y_init])

        line_moved_origin = lane_vector_xy - init_coord

        from_point_xy = from_point[:2]
        to_point_xy = to_point[:2]
        
        from_point_moved = from_point_xy - init_coord
        to_point_moved =  to_point_xy - init_coord 
        
        line_x_coord = line_moved_origin[:,0]
        line_y_coord = line_moved_origin[:,1]

        line_s_coord = np.sqrt(np.power(line_x_coord,2)
            + np.power(line_y_coord, 2))

        slope_first = (self.get_angle(lane_vector[1], right_lane_point, perpendicular_dist) - self.get_angle(from_point, right_lane_from_link, perpendicular_dist)) \
              / np.sqrt((line_x_coord[1] - from_point_moved[0])**2 +  (line_y_coord[1] - from_point_moved[1])**2)

        slope_last = (self.get_angle(to_point, right_lane_to_link, perpendicular_dist) - self.get_angle(lane_vector[-2], right_lane_point, perpendicular_dist)) \
              /  np.sqrt((to_point_moved[0]- line_x_coord[-2])**2 +  (to_point_moved[1]- line_y_coord[-2])**2)

        x = line_s_coord[-1]
        y = self.get_angle(lane_vector[-1], right_lane_point, perpendicular_dist)
        y_prime = slope_last
        
        a = self.get_angle(lane_vector[0], right_lane_point, perpendicular_dist)
        b = slope_first
        d =(y_prime - b + 2*(-y + a+ b*x  )/x )/(x**2)
        c = (y - d*(x**3) - (a+ b*x))/(x**2)
        
        poly_out_elev = np.array([a, b, c, d])
        line_angle_coord = []
        
        
        # for 


        # for s_coord, angle_coord in zip(line_s_coord, line_angle_coord):
        #     line_points.append(np.array([s_coord, angle_coord]))
        # line_points = np.array(line_points)
        # residual = self.residual_exact(poly_out_elev, line_points)

        return poly_out_elev #, residual


    def poly_elevation_bezier_boundary_super_opt_linear(self, lane_vector, right_lane_point, \
        right_lane_from_link, right_lane_to_link, perpendicular_dist):
        
        from_point = lane_vector[0]
        to_point = lane_vector[-1]
        # lane_vector = lane_vector[1:-1,0:2]
        lane_vector = lane_vector[1:-1]
        lane_vector_xy = lane_vector[:,0:2]
        
        # transform initial point to origin
        global_x_init = lane_vector_xy[0][0]
        global_y_init = lane_vector_xy[0][1]
        init_coord = np.array([global_x_init, global_y_init])

        line_moved_origin = lane_vector_xy - init_coord

        from_point_xy = from_point[:2]
        to_point_xy = to_point[:2]
        
        from_point_moved = from_point_xy - init_coord
        to_point_moved =  to_point_xy - init_coord 
        
        line_x_coord = line_moved_origin[:,0]
        line_y_coord = line_moved_origin[:,1]

        line_s_coord = np.sqrt(np.power(line_x_coord,2)
            + np.power(line_y_coord, 2))

        slope_first = (self.get_angle(lane_vector[1], right_lane_point, perpendicular_dist) - self.get_angle(from_point, right_lane_from_link, perpendicular_dist)) \
              / np.sqrt((line_x_coord[1] - from_point_moved[0])**2 +  (line_y_coord[1] - from_point_moved[1])**2)

        slope_last = (self.get_angle(to_point, right_lane_to_link, perpendicular_dist) - self.get_angle(lane_vector[-2], right_lane_point, perpendicular_dist)) \
              /  np.sqrt((to_point_moved[0]- line_x_coord[-2])**2 +  (to_point_moved[1]- line_y_coord[-2])**2)

        x = line_s_coord[-1]
        y = self.get_angle(lane_vector[-1], right_lane_point, perpendicular_dist)
        y_prime = slope_last
        
        # a = self.get_angle(lane_vector[0], right_lane_point, perpendicular_dist)
        # b = slope_first
        # d =(y_prime - b + 2*(-y + a+ b*x  )/x )/(x**2)
        # c = (y - d*(x**3) - (a+ b*x))/(x**2)
        a = self.get_angle(lane_vector[0], right_lane_point, perpendicular_dist)
        b = y/x
        c= 0
        d = 0
        poly_out_elev = np.array([a, b, c, d])
        line_angle_coord = []
        
        
        # for 


        # for s_coord, angle_coord in zip(line_s_coord, line_angle_coord):
        #     line_points.append(np.array([s_coord, angle_coord]))
        # line_points = np.array(line_points)
        # residual = self.residual_exact(poly_out_elev, line_points)

        return poly_out_elev #, residual


    def poly_elevation_bezier_boundary_super(self, lane_vector, right_lane_point, to_point, from_point \
            ,right_lane_from_link, right_lane_to_link \
            , perpendicular_dist , i):
        
        lane_vector_xy = lane_vector[:,0:2]
        
        # transform initial point to origin
        global_x_init = lane_vector_xy[0][0]
        global_y_init = lane_vector_xy[0][1]
        init_coord = np.array([global_x_init, global_y_init])

        line_moved_origin = lane_vector_xy - init_coord

        from_point_xy = from_point[:2]
        to_point_xy = to_point[:2]
        
        from_point_moved = from_point_xy - init_coord
        to_point_moved =  to_point_xy - init_coord 
        
        line_x_coord = line_moved_origin[:,0]
        line_y_coord = line_moved_origin[:,1]

        line_s_coord = np.sqrt(np.power(line_x_coord,2)
            + np.power(line_y_coord, 2))

        slope_first = (self.get_angle(lane_vector[1], right_lane_point, perpendicular_dist) - self.get_angle(from_point, right_lane_from_link, perpendicular_dist)) \
              / np.sqrt((line_x_coord[1] - from_point_moved[0])**2 +  (line_y_coord[1] - from_point_moved[1])**2)

        slope_last = (self.get_angle(to_point, right_lane_to_link, perpendicular_dist) - self.get_angle(lane_vector[-2], right_lane_point, perpendicular_dist)) \
              /  np.sqrt((to_point_moved[0]- line_x_coord[-2])**2 +  (to_point_moved[1]- line_y_coord[-2])**2)

        x = line_s_coord[-1]
        y = self.get_angle(lane_vector[-1], right_lane_point, perpendicular_dist)
        y_prime = slope_last
        
        a = self.get_angle(lane_vector[0], right_lane_point, perpendicular_dist)
        b = slope_first
        d =(y_prime - b + 2*(-y + a+ b*x  )/x )/(x**2)
        c = (y - d*(x**3) - (a+ b*x))/(x**2)
        
        poly_out_elev = np.array([a, b, c, d])
        
        return poly_out_elev


    def poly_elevation_bezier(self, lane_vector):
        lane_vector_xy = lane_vector[:,0:2]
        
        # transform initial point to origin
        global_x_init = lane_vector_xy[0][0]
        global_y_init = lane_vector_xy[0][1]
        init_coord = np.array([global_x_init, global_y_init])
        line_moved_origin = lane_vector_xy - init_coord

        line_x_coord = line_moved_origin[:,0]
        line_y_coord = line_moved_origin[:,1]

        line_s_coord = np.sqrt(np.power(line_x_coord, 2)
            + np.power(line_y_coord, 2))
        line_h_coord = lane_vector[:,2]

        check_coord = np.array([line_s_coord, line_h_coord])

        # linearity = self.get_linearity(line_s_coord, line_h_coord, 1)

        if (len(lane_vector) == 2 or len(lane_vector) == 3):
            b = (line_h_coord[-1] - line_h_coord[0]) / (line_s_coord[-1] - line_s_coord[0])
            a = -line_s_coord[0]*b + line_h_coord[0]
            poly_out = np.array([a, b, 0, 0])
            return poly_out, check_coord
    
        elif len(lane_vector) >= 4:
            length = line_s_coord[-1]
            a = line_h_coord[0]
            b = (3*line_h_coord[1] - 3*line_h_coord[0]) / (length**1)
            c = (3*line_h_coord[-2] - 6*line_h_coord[1] + 3*line_h_coord[0]) / (length**2)
            d = (line_h_coord[-1] - 3*line_h_coord[-2] + 3*line_h_coord[1] - line_h_coord[0]) / (length**3)
            poly_out = np.array([a, b, c, d])
            return poly_out, check_coord

    
    def poly_elevation(self, lane_vector):
        lane_vector_xy = lane_vector[:,0:2]
        
        # transform initial point to origin
        global_x_init = lane_vector_xy[0][0]
        global_y_init = lane_vector_xy[0][1]
        init_coord = np.array([global_x_init, global_y_init])
        line_moved_origin = lane_vector_xy - init_coord

        line_x_coord = line_moved_origin[:,0]
        line_y_coord = line_moved_origin[:,1]

        line_s_coord = np.sqrt(np.power(line_x_coord,2)
            + np.power(line_y_coord, 2))
        line_h_coord = lane_vector[:,2]

        check_coord = np.array([line_s_coord, line_h_coord])

        linearity = self.get_linearity(line_s_coord, line_h_coord, 1)

        if linearity is True:
            series, misc_fit_result = np.polynomial.polynomial.Polynomial.fit(
                line_s_coord,
                line_h_coord,
                1,
                full=True
            )
            series_out = series.convert().coef
            if len(series_out) > 1:
                poly_out = np.array([series_out[0], series_out[1], 0, 0])
            else:
                poly_out = np.array([series_out[0], 0, 0, 0])
        else:        
            series, misc_fit_result = np.polynomial.polynomial.Polynomial.fit(
                line_s_coord,
                line_h_coord,
                3,
                full=True
            )
            poly_out = series.convert().coef
        
        return poly_out, check_coord, misc_fit_result

    
    def check_geometry_in(self, actual_x, actual_y, poly):
        import matplotlib.pyplot as plt
        x_plot = np.linspace(actual_x.min(), actual_x.max(), 100)
        poly3 = np.poly1d(np.flip(poly))

        fig, ax = plt.subplots(1, 1)
        ax.plot(actual_x, actual_y, '--b', label='Source')
        ax.plot(x_plot, poly3(x_plot), 'r', label='Polyfit')
        ax.set_title('Road Geometry Test')
        ax.axis('equal')
        ax.legend()

        plt.show()


    def check_geometry(self, check_geo, check_elev, poly_geo, poly_elev):
        import matplotlib.pyplot as plt

        check_x = check_geo[:, 0]
        check_y = check_geo[:, 1]
        x_plot = np.linspace(check_x.min(), check_x.max(), 100)
        poly3 = np.poly1d(np.flip(poly_geo))

        check_s = check_elev[0, :]
        check_h = check_elev[1, :]
        x_plot_e = np.linspace(check_s.min(), check_s.max(), 100)
        polye = np.poly1d(np.flip(poly_elev))

        fig, ax = plt.subplots(2, 1)
        ax[0].plot(check_x, check_y, '--b', label='Source')
        ax[0].plot(x_plot, poly3(x_plot), 'r', label='Polyfit')
        ax[0].set_title('Road Geometry Test')
        ax[0].axis('equal')
        ax[0].legend()

        ax[1].plot(check_s, check_h, '--b')
        ax[1].plot(x_plot_e, polye(x_plot_e), 'r')
        ax[1].set_title('Road Elevation Test')
        ax[1].axis('equal')

        plt.show()


    def shorten_id(self, id):
        """
        id shortening function to avoid import errors for specific third-party testing
        tools or simulation programs (CARLA)
        """
        id_length_limit = 13
        id_str = str(id)
        id_len = len(id_str)
        if id_len > id_length_limit:
            short_id = id_str[(id_len - 7):id_len]
            id_out = short_id
        else:
            id_out = id
        return id_out
        

    def create_preliminary_odr_roads(self, mgeo_data, id_shortening=False):
        link_set = mgeo_data.link_set

        if id_shortening:
            for _notused, each_link in link_set.lines.items():
                short_id = self.shorten_id(each_link.road_id)
                each_link.road_id = short_id

        # link_set에서 road를 생성한다
        odr_data = OdrData(mgeo_planner_map=mgeo_data)

        num_id = 0
        for idx, link in link_set.lines.items():
            #if link.link_type_def == 'ngii_model2':
               # road_id = link.idx
           # else:
            road_id = link.road_id

            if (road_id is None) or (road_id == ''):
                Logger.log_error('Link: {} has no road_id'.format(idx))
                continue

            if road_id not in odr_data.roads.keys():
                # create new road
                num_id += 1
                road = OdrRoad(
                    num_id=num_id,
                    road_id=road_id,
                    road_type=mgeo_data.road_type,
                    country=mgeo_data.get_country_name_iso3166_alpha2(),
                    traffic_dir=mgeo_data.traffic_dir)
                odr_data.append_road_to_data(road)

            else:
                road = odr_data.roads[road_id]

            road.link_list_not_organized.append(link)

        return odr_data


    def creat_odr_roads_selected(self, mgeo_data, list_sp):
        odr_data = self.create_preliminary_odr_roads(mgeo_data, None)

        link_set = mgeo_data.link_set

        # Link의 Reference Line 관련 정보를 모두 초기화한다
        for link in link_set.lines.values():
            ##############
            if link.road_id in list_sp:
                edit_link.reset_odr_conv_variables(link)
        ################
        list_sp_id_set = [list_sp[i]["id"] for i in range(len(list_sp)) ]
        odr_data_roads =  list(odr_data.roads.keys())
        for croad in odr_data_roads:
            if croad not in list_sp_id_set:
                odr_data.remove_road_to_data(odr_data.roads[croad])
        
        # 각 Road에 대해 Reference Line을 먼저 찾는다
        for road in odr_data.roads.values():
            Logger.log_info('Searching for ref line for road: {}'.format(road.road_id))
            singleSide = False
            
            if singleSide == True:
                road.find_reference_line()
            else:
                road.find_reference_line_doubleSide()

            Logger.log_info('>> Ref line found - ID: {}'.format(Link.get_id_list_string(road.ref_line)))


        # 각 Road에 대해 Lane Section을 생성한다
        for road in odr_data.roads.values():
            Logger.log_info('Creating lane section for road: {}'.format(road.road_id))
            road.create_lane_section()
            # Logger.log_info('>> done OK.')


        # gap이 설정되어있지 않은 lane에 대해 gap을 설정한다
        # FIXME(HJP): tt eval version doesn't need estimate_lane_gap
        # self.estimate_lane_gap(odr_data, link_set)

        # 각 Road에 대해 다음의 작업 수행
        for road in odr_data.roads.values():
            # frontmost_left, rearmost_left 계산하기
            try:
                frontmost_left = road.get_frontmost_left()
                while frontmost_left.link_type not in ['NORMAL','REGULAR','highway','HOV', 'DRIVABLE_SHOULDER', 'EXPRESS', 'SLOW','PASSING','REGULATED_ACCESS']:
                    frontmost_left = frontmost_left.lane_ch_link_right
                
                rearmost_left = road.get_rearmost_left()
                while rearmost_left.link_type not in ['NORMAL','REGULAR','highway','HOV', 'DRIVABLE_SHOULDER', 'EXPRESS', 'SLOW','PASSING','REGULATED_ACCESS']:
                    rearmost_left = rearmost_left.lane_ch_link_right
            except:
                frontmost_left = road.get_frontmost_left()
                while frontmost_left.link_type not in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                    frontmost_left = frontmost_left.lane_ch_link_right
                
                rearmost_left = road.get_rearmost_left()
                while rearmost_left.link_type not in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                    rearmost_left = rearmost_left.lane_ch_link_right
        
            # determine road predecessor_id successor_id ids
            predecessor_survey_results = road.find_predecessors()
            successor_survey_results = road.find_successors()

            """road의 predecessor_id, successor_id 설정 (id 및 road/junction 여부)"""

            pre_node = frontmost_left.get_from_node()
            suc_node = rearmost_left.get_to_node()
            pre_jc_cnt = len(pre_node.junctions)
            suc_jc_cnt = len(suc_node.junctions)

            if len(predecessor_survey_results) > 0 and predecessor_survey_results[0] in odr_data.roads:
                predecessor_road_id = odr_data.roads[predecessor_survey_results[0]].id
            else:
                predecessor_road_id = None

            if len(successor_survey_results) > 0 and successor_survey_results[0] in odr_data.roads:
                successor_road_id = odr_data.roads[successor_survey_results[0]].id
            else:
                successor_road_id = None

            # allocate depending on jc or road connection
            if (pre_jc_cnt == 1
                and suc_jc_cnt == 1):
                if pre_node.junctions[0] != suc_node.junctions[0]:
                    # JC-R-JC connection
                    road.predecessor_id = pre_node.junctions[0].idx
                    road.successor_id = suc_node.junctions[0].idx
                    road.is_pre_junction = True
                    road.is_suc_junction = True
                elif pre_node.junctions[0] == suc_node.junctions[0]:
                    # R-JC-R connection
                    road.junction = pre_node.junctions[0]
                    road.predecessor_id = predecessor_road_id
                    road.successor_id = successor_road_id

            elif (pre_jc_cnt == 2
                and suc_jc_cnt == 2):
                # JC-JC-JC connection
                for pre_jc in pre_node.junctions:
                    if pre_jc in suc_node.junctions:
                        middle_jc = pre_jc
                road.junction = middle_jc
                for pre_jc in pre_node.junctions:
                    if pre_jc is not middle_jc:
                        road.predecessor_id = pre_jc.idx
                for suc_jc in suc_node.junctions:
                    if suc_jc is not middle_jc:
                        road.successor_id = suc_jc.idx
                road.is_pre_junction = True
                road.is_suc_junction = True

            elif ((pre_jc_cnt == 2) and not(suc_jc_cnt == 2)
                or not(pre_jc_cnt == 2) and (suc_jc_cnt ==2)):
                # R-JC-JC or JC-JC-R connection
                for pre_jc in pre_node.junctions:
                    if pre_jc in suc_node.junctions:
                        middle_jc = pre_jc
                road.junction = middle_jc
                for pre_jc in pre_node.junctions:
                    if pre_jc is not middle_jc:
                        road.predecessor_id = pre_jc.idx
                        road.successor_id = successor_road_id
                        road.is_pre_junction = True
                for suc_jc in suc_node.junctions:
                    if suc_jc is not middle_jc:
                        road.successor_id = suc_jc.idx
                        road.predecessor_id = predecessor_road_id
                        road.is_suc_junction = True

            elif pre_jc_cnt == 1:
                # JC-R-R connection
                road.predecessor_id = pre_node.junctions[0].idx
                road.successor_id = successor_road_id
                road.is_pre_junction = True

            elif suc_jc_cnt == 1:
                # R-R-JC connection
                road.predecessor_id = predecessor_road_id
                road.successor_id = suc_node.junctions[0].idx
                road.is_suc_junction = True
                
            else:
                # R-R-R connection
                road.predecessor_id = predecessor_road_id
                road.successor_id = successor_road_id
        
        odr_data.junction_set = JunctionSet()
        
        for road in odr_data.roads.values():
            if road.junction != None:
                odr_data.junction_set.append_junction(road.junction)
            
        return odr_data 


    def create_odr_roads(self, mgeo_data, odr_persistent_data = None):
        if odr_persistent_data is not None:
            odr_data = odr_persistent_data
        else:
            odr_data = self.create_preliminary_odr_roads(mgeo_data, None)

        link_set = mgeo_data.link_set
        
        # Link의 Reference Line 관련 정보를 모두 초기화한다
        for link in link_set.lines.values():
            edit_link.reset_odr_conv_variables(link)
            # link.reset_odr_conv_variables()
            # NOTE(chi) lane_node와 lane_node에 road 정보 추가 
           # for lane_mark in link.lane_mark_left():
             #   lane_mark.road_id = link.road_id
             #   if lane_mark.from_node.road_id 

        # 각 Road에 대해 Reference Line을 먼저 찾는다
        for road in odr_data.roads.values():
            road.odr_roads = odr_data.roads
            Logger.log_info('Searching for ref line for road: {}'.format(road.road_id))
            if road.changed == False:
                singleSide = True 
                
                if singleSide == True:
                    road.find_reference_line()
                else:
                    road.fine_reference_line_doubleSide()
                
                # Logger.log_info('>> Ref line found - ID: {}'.format(Link.get_id_list_string(road.ref_line)))
                Logger.log_info('>> Ref line found - ID: {}'.format(road.ref_line[0].idx))
            else:
                Logger.log_trace('Reference line changed by user at ID {}'.format(road.road_id))

        # 각 Road에 대해 Lane Section을 생성한다
        for road in odr_data.roads.values():
            Logger.log_info('Creating lane section for road: {}'.format(road.road_id))
            if odr_persistent_data is not None:
                road.reset_lane_sections()
                road.create_lane_section()
            else:
                road.create_lane_section()


        # gap이 설정되어있지 않은 lane에 대해 gap을 설정한다
        # FIXME(HJP): tt eval version doesn't need estimate_lane_gap
        # self.estimate_lane_gap(odr_data, link_set)
        # 각 Road에 대해 다음의 작업 수행
        for road in odr_data.roads.values():
            # frontmost_left, rearmost_left 계산하기
            
            # NOTE(chi) temporary in rad-d case
            try:
                frontmost_left = road.get_frontmost_left()
                while frontmost_left.link_type not in ['NORMAL','REGULAR','highway','HOV', 'DRIVABLE_SHOULDER', 'EXPRESS', 'SLOW','PASSING','REGULATED_ACCESS', 'driving', 'Shoulder', 'shoulder']:
                    frontmost_left = frontmost_left.lane_ch_link_right
                
                rearmost_left = road.get_rearmost_left()
                while rearmost_left.link_type not in ['NORMAL','REGULAR','highway','HOV', 'DRIVABLE_SHOULDER', 'EXPRESS', 'SLOW','PASSING','REGULATED_ACCESS', 'driving', 'Shoulder', 'shoulder']:
                    rearmost_left = rearmost_left.lane_ch_link_right
            except:
                try:
                    frontmost_left = road.get_frontmost_left()
                    while frontmost_left.link_type not in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                        frontmost_left = frontmost_left.lane_ch_link_right
                    
                    rearmost_left = road.get_rearmost_left()
                    while rearmost_left.link_type not in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                        rearmost_left = rearmost_left.lane_ch_link_right
                except:
                    # temporary get in
                    try:
                        frontmost_left = road.get_frontmost_left()
                        while frontmost_left.link_type not in ['1', '4', '6']:
                            frontmost_left = frontmost_left.lane_ch_link_right
                        
                        rearmost_left = road.get_rearmost_left()
                        while rearmost_left.link_type not in ['1', '4', '6']:
                            rearmost_left = rearmost_left.lane_ch_link_right
                    except:
                        try:
                            frontmost_left = road.get_frontmost_left()
                            while frontmost_left.link_type not in ['Driving']:
                                frontmost_left = frontmost_left.lane_ch_link_right
                        except:
                            pass
                        rearmost_left = road.get_rearmost_left()
                        while rearmost_left.link_type not in ['Driving']:
                            rearmost_left = rearmost_left.lane_ch_link_right
            
            # determine road predecessor_id successor_id ids
            predecessor_survey_results = road.find_predecessors()
            successor_survey_results = road.find_successors()

            """road의 predecessor_id, successor_id 설정 (id 및 road/junction 여부)"""

            pre_node = frontmost_left.get_from_node()
            suc_node = rearmost_left.get_to_node()
            pre_jc_cnt = len(pre_node.junctions)
            suc_jc_cnt = len(suc_node.junctions)

            if len(predecessor_survey_results) > 0 and predecessor_survey_results[0] in odr_data.roads:
                predecessor_road_id = odr_data.roads[predecessor_survey_results[0]].id
            else:
                predecessor_road_id = None

            if len(successor_survey_results) > 0 and successor_survey_results[0] in odr_data.roads:
                successor_road_id = odr_data.roads[successor_survey_results[0]].id
            else:
                successor_road_id = None

            # allocate depending on jc or road connection
            if (pre_jc_cnt == 1
                and suc_jc_cnt == 1):
                if pre_node.junctions[0] != suc_node.junctions[0]:
                    # JC-R-JC connection
                    road.predecessor_id = pre_node.junctions[0].idx
                    road.successor_id = suc_node.junctions[0].idx
                    road.is_pre_junction = True
                    road.is_suc_junction = True
                elif pre_node.junctions[0] == suc_node.junctions[0]:
                    # R-JC-R connection
                    road.junction = pre_node.junctions[0]
                    road.predecessor_id = predecessor_road_id
                    road.successor_id = successor_road_id

            elif (pre_jc_cnt == 2
                and suc_jc_cnt == 2):
                # JC-JC-JC connection
                for pre_jc in pre_node.junctions:
                    if pre_jc in suc_node.junctions:
                        middle_jc = pre_jc
                road.junction = middle_jc
                for pre_jc in pre_node.junctions:
                    if pre_jc is not middle_jc:
                        road.predecessor_id = pre_jc.idx
                for suc_jc in suc_node.junctions:
                    if suc_jc is not middle_jc:
                        road.successor_id = suc_jc.idx
                road.is_pre_junction = True
                road.is_suc_junction = True

            elif ((pre_jc_cnt == 2) and not(suc_jc_cnt == 2)
                or not(pre_jc_cnt == 2) and (suc_jc_cnt ==2)):
                # R-JC-JC or JC-JC-R connection
                for pre_jc in pre_node.junctions:
                    if pre_jc in suc_node.junctions:
                        middle_jc = pre_jc
                try:
                    road.junction = middle_jc
                except:
                    pass
                for pre_jc in pre_node.junctions:
                    if pre_jc is not middle_jc:
                        road.predecessor_id = pre_jc.idx
                        road.successor_id = successor_road_id
                        road.is_pre_junction = True
                for suc_jc in suc_node.junctions:
                    if suc_jc is not middle_jc:
                        road.successor_id = suc_jc.idx
                        road.predecessor_id = predecessor_road_id
                        road.is_suc_junction = True

            elif pre_jc_cnt == 1:
                # JC-R-R connection
                road.predecessor_id = pre_node.junctions[0].idx
                road.successor_id = successor_road_id
                road.is_pre_junction = True

            elif suc_jc_cnt == 1:
                # R-R-JC connection
                road.predecessor_id = predecessor_road_id
                road.successor_id = suc_node.junctions[0].idx
                road.is_suc_junction = True
                
            else:
                # R-R-R connection
                road.predecessor_id = predecessor_road_id
                road.successor_id = successor_road_id

        return odr_data 


    def set_lane_gap_recursively_toward_start_direction(self, link):
        # 현재 링크 하나에 대해서, 다음을 수행한다

        # [종료 조건 #1] 현재 링크의 start 쪽이 설정이 안 되어 있다면,현재 링크에서 시작할 수 없으므로 그냥 종료한다
        if link.odr_lane.is_gap_not_set(end_type='start'):
            return 
        
        # 즉, 현재 링크의 start쪽이 설정된 링크만 아래 과정을 진행한다
        # 우선 이전 링크의 리스트를 받아온다
        prev_links = link.get_from_links()

        # 모든 이전 링크에 대해 다음을 수행한다
        # [종료 조건 #2] 이전 링크가 없으면 바로 종료된다 (즉, source link 이면 바로 종료된다)
        for prev_link in prev_links:

            if prev_link.odr_lane is None:
                raise BaseException('ERROR: prev link (id: {}) has no odr_lane (There might be logical error in the link left/right pair value in each link'.format(prev_link.idx))

            # 이전 링크 중에서 end 쪽 gap이 이미 설정된 링크는 그냥 넘어간다
            if not prev_link.odr_lane.is_gap_not_set(end_type='end'):
                # TODO(sglee) 현재 링크의 start쪽 width와, 이전 링크의 end쪽 width가 다르면 오류
                continue

            # 즉, end 쪽 gap이 설정되지 않은 링크에 대해서만 다음을 수행한다            
            # 이전 링크의 끝 gap을 현재 링크의 시작쪽 gap과 맞춰준다 
            prev_link.odr_lane.gap['end'] = link.odr_lane.gap['start']


            # 이제, 이전 링크의 start 쪽 gap을 체크한다. 이미 설정되어 있으면 그냥 넘어간다
            if not prev_link.odr_lane.is_gap_not_set(end_type='start'):            
                continue

            # 즉, start 쪽 gap이 설정되지 않은 링크에 대해서, 아래를 수행한다
            # start 쪽 gap도 end 쪽과 같이 설정한다 
            gap_result, prev_lane_end_gap = prev_link.odr_lane.get_prev_lane_end_width()
            if gap_result:
                prev_link.odr_lane.gap['start'] = prev_lane_end_gap   
            else:
                prev_link.odr_lane.gap['start'] = prev_link.odr_lane.gap['end'] 

            self.set_lane_gap_recursively_toward_start_direction(prev_link)


    def set_lane_gap_recursively_toward_end_direction(self, link):
        # 현재 링크 하나에 대해서, 다음을 수행한다

        # [종료 조건 #1] 현재 링크의 end 쪽이 설정이 안 되어 있다면,현재 링크에서 시작할 수 없으므로 그냥 종료한다
        if link.odr_lane.is_gap_not_set(end_type='end'):
            return 
        
        # 즉, 현재 링크의 end 설정된 링크만 아래 과정을 진행한다
        # 우선 다음 링크의 리스트를 받아온다
        next_links = link.get_to_links()

        # 모든 다음 링크에 대해 다음을 수행한다
        # [종료 조건 #2] 다음 링크가 없으면 바로 종료된다 (즉, sink link 이면 바로 종료된다)
        for next_link in next_links:

            # 다음 링크 중에서 start 쪽 gap이 이미 설정된 링크는 그냥 넘어간다
            if not next_link.odr_lane.is_gap_not_set(end_type='start'):
                # TODO(sglee) 현재 링크의 end쪽 width와, 다음 링크의 start쪽 width가 다르면 오류
                continue

            # 즉, start 쪽 gap이 설정되지 않은 링크에 대해서만 다음을 수행한다            
            # 다음 링크의 start 쪽 gap을 현재 링크의 end 쪽 gap과 맞춰준다 
            next_link.odr_lane.gap['start'] = link.odr_lane.gap['end']


            # 이제, 다음 링크의 end 쪽 gap을 체크한다. 이미 설정되어 있으면 그냥 넘어간다
            if not next_link.odr_lane.is_gap_not_set(end_type='end'):            
                continue

            # 즉, end 쪽 gap이 설정되지 않은 링크에 대해서, 아래를 수행한다
            # end쪽 gap에 값을 줄 수 있는 b.c.가 있는지 확인한다 (즉 그 다음 lane에 width가 설정되어있는지)
            gap_result, next_lane_start_gap = next_link.odr_lane.get_next_lane_start_width()
            if gap_result:
                # 그러면, 현재 링크의
                next_link.odr_lane.gap['end'] = next_lane_start_gap
            else:
                # 2) end 쪽 gap도 start 쪽과 같이 설정한다 
                next_link.odr_lane.gap['end'] = next_link.odr_lane.gap['start'] 

            self.set_lane_gap_recursively_toward_end_direction(next_link)


    def propagate(self, link_set):
        # [STEP #1] start 방향으로, width가 없는 lane 찾기
        for link in link_set.lines.values():
            # 자기 자신은 start 쪽에 width가 설정되어 있고
            # 다른 lane은 end 쪽에 width가 설정되어있지 않는 경우
            # 이 값을 전달해야한다
            self.set_lane_gap_recursively_toward_start_direction(link)

        # [STEP #2] start 방향으로, width가 없는 lane 찾기
        for link in link_set.lines.values():
            # 자기 자신은 start 쪽에 width가 설정되어 있고
            # 다른 lane은 end 쪽에 width가 설정되어있지 않는 경우
            # 이 값을 전달해야한다
            self.set_lane_gap_recursively_toward_end_direction(link)

        left_unset = []

        # 다시 한번 체크한다. set이 안 된게 있는지
        for link in link_set.lines.values():
            if link.odr_lane.is_gap_not_set(end_type='both'):
                Logger.log_debug('ERROR >> Link: {} : gaps for both ends are not set'.format(link.idx))
                left_unset.append(link)
                continue
            
            if link.odr_lane.is_gap_not_set(end_type='start'):
                Logger.log_debug('ERROR >> Link: {} : gap for end_type = start is not set'.format(link.idx))
                left_unset.append(link)
                continue

            if link.odr_lane.is_gap_not_set(end_type='end'):
                Logger.log_debug('ERROR >> Link: {} : gap for end_type = end is not set'.format(link.idx))
                left_unset.append(link)
                continue

        return left_unset


    def estimate_lane_gap(self, odr_data, link_set):
        left_unset = self.propagate(link_set)
        iter_num = 1

        first_estimate_success = True
        max_iter = 100
        while len(left_unset) > 0:
            Logger.log_debug('---------- Iter # {} ----------'.format(iter_num))
            left_unset = self.propagate(link_set)
            iter_num += 1

            if iter_num == max_iter:
                first_estimate_success = False
                idx_str_list = '['
                for link_cannot_set in left_unset:
                    idx_str_list += '{}, '.format(link_cannot_set.idx)
                idx_str_list += ']'

                Logger.log_warning('estimate_lane_gap failed at its first try. Manually setting lane width is required. Try setting lane width manually for some links: {}'.format(idx_str_list))
                break
                # raise BaseException('estimate_lane_gap failed. Manually setting lane width is required. Try setting lane width manually for some links: {}'.format(idx_str_list))
        

        # 위 과정으로 estimate가 잘 되었으면 그냥 return하면 된다
        if first_estimate_success:
            return

        # 만일 아닌 경우, 이제부터가 문제이다.
        # 우선 1차선인 lane에 대해 gap을 할당해준다
        # 실제로는 width가 최종적으로 필요한거지만, 내부 로직은 gap을 기준으로 동작하므로 이렇게 해준다
        for road in odr_data.roads.values():
            for lane_section in road.lanes['lane_sections']:
                # lane이 1개인 경우에 대해
                if lane_section.get_lane_num() == 1:
                    # 그러면 해당 lane은 ref_lane 이고, r
                    ref_lane = lane_section.get_ref_lane()
                    if ref_lane.get_link().force_width_start:
                        ref_lane.gap['start']['L'] = ref_lane.get_link().width_start / 2.0
                        ref_lane.gap['start']['R'] = ref_lane.get_link().width_start / 2.0

                    if ref_lane.get_link().force_width_end:
                        ref_lane.gap['end']['L'] = ref_lane.get_link().width_end / 2.0
                        ref_lane.gap['end']['R'] = ref_lane.get_link().width_end / 2.0



        max_iter += max_iter # max_iter를 2배로 늘린다 (iter_num을 초기화하지 않고 더 수행한다)
        while len(left_unset) > 0:
            Logger.log_debug('---------- Iter # {} ----------'.format(iter_num))
            left_unset = self.propagate(link_set)
            iter_num += 1

            if iter_num == max_iter:
                first_estimate_success = False
                idx_str_list = '['
                for link_cannot_set in left_unset:
                    idx_str_list += '{}, '.format(link_cannot_set.idx)
                idx_str_list += ']'

                #Logger.log_warning('estimate_lane_gap failed at its first try. Manually setting lane width is required. Try setting lane width manually for some links: {}'.format(idx_str_list))
                # 이제는 그냥 오류를 아예 출력하고 실패로 종료한다
                raise BaseException('estimate_lane_gap failed. Manually setting lane width is required. Try setting lane width manually for some links: {}'.format(idx_str_list))
        

    def estimate_lane_gap_legacy(self, odr_data, link_set):
        """전체 Road 에 대해, width의 boundary condition을 만족할 수 있게 한다"""
        # [STEP #1] source lane 찾기
        search_start_point_source_lane = []
        for link in link_set.lines.values():
            if link.is_source():
                # 해당 링크가 single lane인지 확인한다
                if link.odr_lane.is_gap_not_set():
                    search_start_point_source_lane.append(link.odr_lane)
                    Logger.log_debug('Link: {} is a single lane, source link'.format(link.idx))


        # [STEP #2] source lane에서 b.c.가 있는 lane을 찾아 fix하기
        for source_lane in search_start_point_source_lane:
            # source 이므로, to 방향으로 찾아가면서 gap이 설정되었는지를 찾는다
            lane_with_gap_bc, lanes_to_fix = self.find_lane_with_its_gap_set(source_lane, direction='to')
            
            if lane_with_gap_bc is not None: # b.c.를 제공할 수 있는 lane을 찾은 것
                # 찾았으면 lanes_to_fix 를 보고 세팅해야 한다
                # 이 때 lane_with_gap_bc 의 start 쪽 값을 이용하여 전부 세팅한다
                for i, lane_to_fix in enumerate(lanes_to_fix):
                    # gap이 설정된 lane의 start쪽 gap 값을 이용하여, fix할 lane의 end쪽 gap을 설정한다
                    lane_to_fix.gap['end']['L'] = lane_with_gap_bc.gap['start']['L'] # boundary condition이 start 쪽이므로
                    lane_to_fix.gap['end']['R'] = lane_with_gap_bc.gap['start']['R']

                    # fix할 lane의 start쪽 또한 이 값으로 설정한다
                    lane_to_fix.gap['start']['L'] = lane_with_gap_bc.gap['start']['L']
                    lane_to_fix.gap['start']['R'] = lane_with_gap_bc.gap['start']['R']
                            

        # [STEP #3] sink lane 찾기
        search_start_point_sink_lane = []
        for link in link_set.lines.values():
            if link.is_sink():
                # 해당 링크가 single lane인지 확인한다
                if link.odr_lane.is_gap_not_set():
                    search_start_point_sink_lane.append(link.odr_lane)
                    Logger.log_debug('Link: {} is a single lane, sink link'.format(link.idx))


        # [STEP #4] source lane에서 b.c.가 있는 lane을 찾아 fix하기
        for source_lane in search_start_point_sink_lane:
            # source 이므로, to 방향으로 찾아가면서 gap이 설정되었는지를 찾는다
            lane_with_gap_bc, lanes_to_fix = self.find_lane_with_its_gap_set(source_lane, direction='from')
            
            if lane_with_gap_bc is not None: # b.c.를 제공할 수 있는 lane을 찾은 것
                # 찾았으면 lanes_to_fix 를 보고 세팅해야 한다
                # 이 때 lane_with_gap_bc 의 end쪽 값을 이용하여 전부 세팅한다
                for i, lane_to_fix in enumerate(lanes_to_fix):
                    # gap이 설정된 lane의 end쪽 gap 값을 이용하여, fix할 lane의 start쪽 gap을 설정한다
                    lane_to_fix.gap['start']['L'] = lane_with_gap_bc.gap['end']['L'] # boundary condition이 end 쪽이므로
                    lane_to_fix.gap['start']['R'] = lane_with_gap_bc.gap['end']['R']

                    # fix할 lane의 end쪽 또한 이 값으로 설정한다
                    lane_to_fix.gap['end']['L'] = lane_with_gap_bc.gap['end']['L']
                    lane_to_fix.gap['end']['R'] = lane_with_gap_bc.gap['end']['R']


        # [STEP #5] source, sink 도 아닌 lane을 찾아 fix하기
        for link in link_set.lines.values():
            # 1) source, sink 인데 위에서 해결이 되지 않은 lane 이거나
            # 2) sounce, sink 가 아닌 single lane 인데, 해당 lane 앞/뒤로 gap이 정해진 lane이 있는 경우
            if link.odr_lane.is_gap_not_set(): 
                Logger.log_debug('Estimating single-lane (Link: {}) width using boundary condition'.format(link.idx))  
                link.odr_lane.estimate_lane_width_for_single_lane_legacy()


    def find_lane_with_its_gap_set(self, lane, direction):
        # to 방향으로 찾아가는 경로이다. 향후 b.c.를 찾으면 이 경로에 있는 모든 값을 세팅해야 한다
        lanes_to_fix = [lane]
        lane_with_gap = None
        
        i = 0
        max_iter = 1000 # 무한루프 방지용
        
        current_lane = lane
        while lane_with_gap is None:
            if direction == 'to':
                next_links = current_lane.get_link().get_to_links()
            else:
                next_links = current_lane.get_link().get_from_links()

            # [STEP #1] 다음 링크 개수에 따른 동작 수항 
            if len(next_links) == 0:
                # 이렇게 되면, b.c.를 못 찾는 것이다. break로 종료한다
                lanes_to_fix.reverse() # 마지막 검색한 lane이 처음에 오도록한다
                break
            
            elif len(next_links) > 1:
                # 이렇게 되면, 좀 복잡하다
                lanes_to_fix.reverse() # 마지막 검색한 lane이 처음에 오도록한다
                Logger.log_warning('Failed to search b.c. from lane (link: {}). multiple next_links (#: {}) are found at link: {}'.format(
                    lane.get_link().idx, len(next_links), current_lane.get_link()))
                break 
                #raise BaseException('Not implemented for this case yet.')

            # [STEP #2] 링크 -> Lane을 얻어와서, 해당 Lane에 gap이 설정되어있는지 판단
            next_link = next_links[0]
            next_lane = next_link.odr_lane
            if next_lane.is_gap_not_set():
                # 이 current_lane 또한 gap이 설정되어있지 않으면, 나중에 fix할 lane에 저장하고, 루프를 계속해야 한다
                lanes_to_fix.append(next_lane)
                current_lane = next_lane # lane을 변경해준다
            else:
                # 이를 통해 종료한다
                lane_with_gap = next_lane


            # 무한 루프 방지용 코드
            i += 1
            if i == max_iter:
                lanes_to_fix.reverse() # 마지막 검색한 lane이 처음에 오도록한다
                raise BaseException('Error @ find_lane_with_its_gap_set: max_iter is reached')

        lanes_to_fix.reverse() # 마지막 검색한 lane이 처음에 오도록한다
        return lane_with_gap, lanes_to_fix


    def check_if_junction_should_be_created(self, odr_data):
        for road_id, road in odr_data.roads.items():
            error_nodes = road.get_no_junction_error_nodes_front()
            if len(error_nodes) > 0:
                Logger.log_error('Road: {} needs new junctions to be set in the front'.format(road_id))            

            error_nodes = road.get_no_junction_error_nodes_end() 
            if len(error_nodes) > 0:
                Logger.log_error('Road: {} needs new junctions to be set in the end'.format(road_id))            


    def determine_lane_expansion(self, road):
        """차선 확장/축소가 일어나는 곳이 왼쪽인지 오른쪽인지 찾아내고, slope를 계산한다"""
        # lane_section 이 1개이면 lane expansion이 존재할 수 없다 => skip
        if len(road.get_lane_sections()) == 1:
            return

        for lane_sec_num in range(len(road.get_lane_sections())-1):
            expected_slope = 0.5

            # build two lists of each lane section pair one from actual lane
            # data taken from get_lane_sections().lanes_R/lanes_L, and another from
            # extracting the to/from links of the other lane section pair
            to_list = list()
            from_list = list()
            lane_sec_lead = road.get_lane_sections()[lane_sec_num]
            lane_sec_follow = road.get_lane_sections()[lane_sec_num+1]
            
            
            all_lanes_lead = lane_sec_lead.get_all_lane_links()
            all_lanes_follow = lane_sec_follow.get_all_lane_links()
            
            actual_to_list = all_lanes_follow
            actual_from_list = all_lanes_lead


            for lane in actual_from_list:
                to_survey = lane.get_to_links()
                for to_link in to_survey:
                    to_list.append(to_link)
            for lane in actual_to_list:
                from_survey = lane.get_from_links()
                for from_link in from_survey:
                    from_list.append(from_link)


            # check if lists match or not 
            if to_list != actual_to_list:
                # case 1: lane expansion
                # determine if expansion is on left or right
                for lane in actual_to_list:
                    if lane not in to_list:
                        on_left = lane.lane_ch_link_right is not None
                        on_right = lane.lane_ch_link_left is not None
                        # skip lanes that aren't end lanes
                        if on_left and on_right:
                            continue
                        # calculate expansion slope and s_offset point
                        if on_left is True:
                            if len(lane_sec_lead.get_lanes_L()) < 1:
                                lead_lane_width = 0
                            else:
                                lead_lane_width = lane_sec_lead.get_lanes_L()[-1].gap
                            follow_lane_width = lane_sec_follow.get_lanes_L()[-1].gap
                            expand_length = follow_lane_width / expected_slope
                            expand_s_offset = lane_sec_lead.lane_length - expand_length
                            if expand_s_offset < 0:  # account for short lanes
                                expand_s_offset = lane_sec_lead.lane_length
                            lane_sec_lead.lane_expand_left = expand_s_offset
                            lane_sec_lead.lane_expand_left_slope = lead_lane_width + follow_lane_width
                        if on_right is True:
                            lead_lane_width = lane_sec_lead.get_lanes_R()[-1].gap
                            follow_lane_width = lane_sec_follow.get_lanes_R()[-1].gap
                            expand_length = follow_lane_width / expected_slope
                            expand_s_offset = lane_sec_lead.lane_length - expand_length
                            if expand_s_offset < 0:  # account for short lanes
                                expand_s_offset = lane_sec_lead.lane_length
                            lane_sec_lead.lane_expand_right = expand_s_offset
                            lane_sec_lead.lane_expand_right_slope = lead_lane_width + follow_lane_width


            if from_list != actual_from_list:
                # case 2: lane contraction
                # determine if contraction is left or right
                for lane in actual_from_list:
                    if lane not in from_list:
                        on_left = lane.lane_ch_link_right is not None
                        on_right = lane.lane_ch_link_left is not None
                        # skip lanes that aren't end lanes
                        if on_left and on_right:
                            continue
                        # calculate contraction slope and s_offset point
                        if on_left is True:
                            if len(lane_sec_follow.get_lanes_L()) < 1:
                                follow_lane_width = 0
                            else:
                                follow_lane_width = lane_sec_follow.get_lanes_L()[-1].gap
                            lead_lane_width = lane_sec_lead.get_lanes_L()[-1].gap
                            expand_length = lead_lane_width / expected_slope
                            expand_s_offset = expand_length
                            if expand_s_offset > lane_sec_follow.lane_length:
                                expand_s_offset = lane_sec_follow.lane_length
                            lane_sec_follow.lane_expand_left = expand_s_offset
                            lane_sec_follow.lane_expand_left_slope = (-1)*(lead_lane_width + follow_lane_width)
                        if on_right is True:
                            lead_lane_width = lane_sec_lead.get_lanes_R()[-1].gap
                            follow_lane_width = lane_sec_follow.get_lanes_R()[-1].gap
                            expand_length = lead_lane_width / expected_slope
                            expand_s_offset = expand_length
                            if expand_s_offset > lane_sec_follow.lane_length:
                                expand_s_offset = lane_sec_follow.lane_length
                            lane_sec_follow.lane_expand_right = expand_s_offset
                            lane_sec_follow.lane_expand_right_slope = (-1)*(lead_lane_width + follow_lane_width)

 
    def convert_selected(self, mgeo_data, list_sp = []):
         # OpenDRIVE 변환 설정을 받아온다
        config_include_signal = self.get_config('include_signal')
        Logger.log_trace('OpenDRIVE Conv. Config: Include Signal: {}'.format(config_include_signal))

        config_fix_signal_road_id = self.get_config('fix_signal_road_id')
        Logger.log_trace('OpenDRIVE Conv. Config: Fix Signal Road ID: {}'.format(config_fix_signal_road_id))
        
        # OpenDRIVE 변환 설정에 따라 Lane 사이의 Link를 생략할 수 있다
        # => Junction 등을 생성하지 않고 CARLA에서 로드하기 위한 옵션으로, Autopliot은 동작하지 않게 된다
        # => Warning을 출력해준다.
        config_disable_lane_link = self.get_config('disable_lane_link')
        Logger.log_trace('OpenDRIVE Conv. Config: Disable Lane Link: {}'.format(config_disable_lane_link))
        if config_disable_lane_link:
            Logger.log_warning('Link information between links is omitted by the user. It will allow CARLA to open xodr files without any junctions, but disable autopilot function at the same time. Use this option to check road geometry only.')

        config_superelevation  = self.get_config('superelevation')
        Logger.log_trace('OpenDRIVE Conv. Config: superelevation: {}'.format(config_superelevation))
        

        if len(list_sp) != 0:
            odr_data = self.creat_odr_roads_selected(mgeo_data, list_sp)
        else:
            odr_data = self.create_odr_roads(mgeo_data)

        node_set = mgeo_data.node_set
        link_set = mgeo_data.link_set
        sign_set = mgeo_data.sign_set
        light_set = mgeo_data.light_set
        origin = mgeo_data.local_origin_in_global
        junction_set  = odr_data.junction_set

        # check any link without road id
        for link in link_set.lines.values():
            if link.road_id is None:
                raise BaseException('link.road_id is None (link: {})'.format(link.idx))
            elif link.road_id == '':
                raise BaseException('link.road_id is an empty string (link: {})'.format(link.idx))
        
        self.create_geometry(odr_data)

        all_road_list = [] 
        for road in odr_data.roads.values():
            all_road_list.append(road)

        if config_include_signal:
            # insert traffic signs to road
            # tomtom 데이터에 road/link 정보 없어서 추가해야함
            for signal in sign_set.signals.values():

                if signal.road_id == '' or signal.road_id is None:
                    candidate_roads = []
                    xlim = [signal.point[0] - 30, signal.point[0] + 30]
                    ylim = [signal.point[1] - 30, signal.point[1] + 30]

                    signal_heading_vec = np.array([np.cos(np.radians(signal.heading)), np.sin(np.radians(signal.heading))])
                    com_dist = np.inf
                    
                    for road in odr_data.roads.values():

                        if road.ref_line[0].is_out_of_xy_range(xlim, ylim) is False:

                            ref_line_point = road.ref_line[0].lane_mark_left[0].points
                            ref_line_geometry = road.ref_line[0].lane_mark_left[0].geometry

                            for cnt in range(len(ref_line_geometry)):
                                if cnt == len(ref_line_geometry) - 1:
                                    p0 = ref_line_point[ref_line_geometry[cnt]['id']][0:2]
                                    p1 = ref_line_point[-1][0:2]
                                else:
                                    p0 = ref_line_point[ref_line_geometry[cnt]['id']][0:2]
                                    p1 = ref_line_point[ref_line_geometry[cnt+1]['id']][0:2]
                                road_heading_vec = (p1-p0) / np.linalg.norm(p1-p0)

                            # ref_line_point = road.ref_line[0].points
                            # ref_line_geometry = road.ref_line[0].lane_mark_left.geometry

                            # for cnt in range(len(ref_line_point)):
                                
                            #     if cnt == len(ref_line_point) - 1:
                            #         break
                            #     else:
                            #         p0 = ref_line_point[cnt][0:2]
                            #         p1 = ref_line_point[cnt+1][0:2]

                                road_heading_vec = (p1-p0) / np.linalg.norm(p1-p0)

                                if np.inner(signal_heading_vec, road_heading_vec) > 0:
                                    if road in candidate_roads:
                                        continue

                                    dist = self.get_closest_pt_on_line(road.ref_line[0].points, signal.point)
                                    if com_dist > dist:
                                        com_dist = dist
                                        candidate_roads.insert(0, road)
                                    else:
                                        candidate_roads.append(road)

                    if len(candidate_roads) > 0:
                        result, solution, matching_road = OdrSignal.FindMatchingRoad(signal, candidate_roads)

                        if result:
                            matching_road = matching_road
                        else:
                            matching_road = candidate_roads[0]
                        signal.road_id = matching_road.road_id
                        signal.link_id_list.append(matching_road.ref_line[0].idx)
                        signal.link_list.append(matching_road.ref_line[0])
                        
                    else:
                        min_road = []
                        min_dist = np.inf
                        for road in odr_data.roads.values():
                            if road.ref_line[0].is_out_of_xy_range(xlim, ylim) is False:
                                dist = self.get_closest_pt_on_line(road.ref_line[0].points, signal.point)
                                if min_dist > dist:
                                    min_dist = dist
                                    min_road.insert(0, road)
                                else:
                                    min_road.append(road)

                        result, solution, matching_road = OdrSignal.FindMatchingRoad(signal, candidate_roads)
                        if result:
                            matching_road = matching_road
                        elif len(min_road) < 1:
                            continue
                        else:
                            matching_road = min_road[0]
                        
                        signal.road_id = matching_road.road_id
                        signal.link_id_list.append(matching_road.ref_line[0].idx)
                        signal.link_list.append(matching_road.ref_line[0])
                        Logger.log_info('Signal id: {} (heading: {}) was allocated to the closest road object. (road id: {})'.format(signal.idx, signal.heading, signal.road_id))


                if signal.road_id in odr_data.roads: 
                    road = odr_data.roads[signal.road_id]

                    odr_signal, matching_odr_road = OdrSignal.CreateInstanceFromMGeoSignal(
                        signal, road,
                        fix_road=config_fix_signal_road_id,
                        candidate_roads=all_road_list)

                    # 실제 road와 매칭되는 road가 다를 수 있으므로, matchin_odr_road를 체크해야 함
                    if matching_odr_road is not None:
                        matching_odr_road.add_signal(odr_signal)
                    else:
                        # matching_odr_road가 None인 경우는, 따로 매칭시킬 road가 없다.
                        # positionInertial을 이용할 수 있으므로, 초기 데이터의 road에 매칭시킨다
                        road.add_signal(odr_signal)
                        
                else: 
                    Logger.log_error('signal ID: {}'.format(signal.idx))
                    #raise BaseException('[ERROR] Could not find road ID mapped in odr_data.roads.')

            # insert traffic lights to road (traffic sign 경우와 완전히 동일 작업)
            for signal in light_set.signals.values():
                if signal.road_id == '' or signal.road_id is None:
                    candidate_roads = []
                    xlim = [signal.point[0] - 30, signal.point[0] + 30]
                    ylim = [signal.point[1] - 30, signal.point[1] + 30]

                    signal_heading_vec = np.array([np.cos(np.radians(signal.heading)), np.sin(np.radians(signal.heading))])
                    com_dist = np.inf
                    
                    for road in odr_data.roads.values():

                        if road.ref_line[0].is_out_of_xy_range(xlim, ylim) is False:

                            ref_line_point = road.ref_line[0].lane_mark_left[0].points
                            ref_line_geometry = road.ref_line[0].lane_mark_left[0].geometry

                            for cnt in range(len(ref_line_geometry)):
                                if cnt == len(ref_line_geometry) - 1:
                                    p0 = ref_line_point[ref_line_geometry[cnt]['id']][0:2]
                                    p1 = ref_line_point[-1][0:2]
                                else:
                                    p0 = ref_line_point[ref_line_geometry[cnt]['id']][0:2]
                                    p1 = ref_line_point[ref_line_geometry[cnt+1]['id']][0:2]
                                road_heading_vec = (p1-p0) / np.linalg.norm(p1-p0)
                                road_heading_vec = (p1-p0) / np.linalg.norm(p1-p0)

                                if np.inner(signal_heading_vec, road_heading_vec) > 0:
                                    if road in candidate_roads:
                                        continue

                                    dist = self.get_closest_pt_on_line(road.ref_line[0].points, signal.point)
                                    if com_dist > dist:
                                        com_dist = dist
                                        candidate_roads.insert(0, road)
                                    else:
                                        candidate_roads.append(road)

                    if len(candidate_roads) > 0:
                        result, solution, matching_road = OdrSignal.FindMatchingRoad(signal, candidate_roads)

                        if result:
                            matching_road = matching_road
                        else:
                            matching_road = candidate_roads[0]
                        signal.road_id = matching_road.road_id
                        signal.link_id_list.append(matching_road.ref_line[0].idx)
                        signal.link_list.append(matching_road.ref_line[0])
                        
                    else:
                        min_road = []
                        min_dist = np.inf
                        for road in odr_data.roads.values():
                            if road.ref_line[0].is_out_of_xy_range(xlim, ylim) is False:
                                dist = self.get_closest_pt_on_line(road.ref_line[0].points, signal.point)
                                if min_dist > dist:
                                    min_dist = dist
                                    min_road.insert(0, road)
                                else:
                                    min_road.append(road)

                        result, solution, matching_road = OdrSignal.FindMatchingRoad(signal, candidate_roads)
                        if result:
                            matching_road = matching_road
                        elif len(min_road) < 1:
                            continue
                        else:
                            matching_road = min_road[0]
                        
                        signal.road_id = matching_road.road_id
                        signal.link_id_list.append(matching_road.ref_line[0].idx)
                        signal.link_list.append(matching_road.ref_line[0])
                        Logger.log_info('Signal id: {} (heading: {}) was allocated to the closest road object. (road id: {})'.format(signal.idx, signal.heading, signal.road_id))
     
        # find all the connecting lanes within each junction
        for _notused, junction in junction_set.junctions.items():
            connecting_lanes = list()
            for node in junction.get_jc_nodes():
                survey_from_links = node.get_from_links()
                for survey_links in survey_from_links:
                    last_link = self.get_foremost_lane_in_the_same_road(survey_links)
                    survey_jc = last_link.get_from_node().junctions
                    if len(survey_jc) != 0:
                        for jc_candidate in survey_jc:
                            if jc_candidate == junction:
                                connecting_lanes.append(last_link)
                                
            repeat_list = list()
            iterator = 1

            # determine properties of each connecting road
            for connection in connecting_lanes:
                # find out the road id of the preceding lane
                # account for floating links with no from_links
                if len(connection.get_from_links()) < 1 or connection.get_from_links()[0].road_id not in odr_data.roads:
                    if connection.lane_ch_link_left is not None:
                        if len(connection.lane_ch_link_left.get_from_links()) < 1:
                            Logger.log_warning('debug connection {}'.format(connection.idx))
                            incoming = None
                            raise BaseException('No incoming lane into the connecting lane (link id: {})'.format(connection.idx))
                        else:
                            if connection.lane_ch_link_left.get_from_links()[0].road_id in odr_data.roads:
                                incoming = connection.lane_ch_link_left.get_from_links()[0]
                            else:
                                raise BaseException('No incoming lane into the connecting lane (link id: {})'.format(connection.idx))
                    elif connection.lane_ch_link_right is not None:
                        if len(connection.lane_ch_link_right.get_from_links()) < 1:
                            Logger.log_warning('debug connection {}'.format(connection.idx))
                            incoming = None
                            raise BaseException('No incoming lane into the connecting lane (link id: {})'.format(connection.idx))
                        else:
                            if connection.lane_ch_link_right.get_from_links()[0].road_id in odr_data.roads:
                                incoming = connection.lane_ch_link_right.get_from_links()[0]
                            else:
                                raise BaseException('No incoming lane into the connecting lane (link id: {})'.format(connection.idx))
                    else:
                        raise BaseException('[ERROR] Connecting road lane does not have preceding element (link id={})'.format(connection.idx))
                else:
                    incoming = connection.get_from_links()[0]

                # create or call connecting_road
                if connection.road_id not in repeat_list:
                    # create new connecting road objects
                    junction.connecting_road[connection.road_id] = ConnectingRoad()
                    repeat_list.append(connection.road_id)
                    
                    # assign properties to the connecting road object
                    connector = junction.connecting_road[connection.road_id]
                    if iterator < 10:
                        iter_str = '0{}'.format(iterator)
                    else:
                        iter_str = '{}'.format(iterator)
                    connector.idx = '{}'.format(junction.idx[2:]) + iter_str
                    if connection.road_id in odr_data.roads:
                        connector.connecting = odr_data.roads[connection.road_id].id
                    else:
                        BaseException('[ERROR] All of connecting road lane in junction are not in the selected road (link id={})'.format(connection.idx))
                    if incoming is not None:    
                        connector.incoming = odr_data.roads[incoming.road_id].id
                    
                    iterator += 1
                elif connection.road_id in repeat_list:
                    # call existing connecting road object
                    connector = junction.connecting_road[connection.road_id]

                # assign to/from lanes to connecting_road
                if incoming is not None:
                    incoming_road = odr_data.roads[incoming.road_id]
                # type check
                    if isinstance(incoming.ego_lane, str):
                        incoming.ego_lane = int(incoming.ego_lane)

                # check left/right lane assignments for connection roads
                if connection.road_id in odr_data.roads:
                    connection_road = odr_data.roads[connection.road_id]
                    
                    if isinstance(connection.ego_lane, str):
                        connection.ego_lane = int(connection.ego_lane)
                    
                    if connection in connection_road.get_lane_sections()[0].get_left_lane_links():
                        index_list = []
                        total_lanes = len(connection_road.get_lane_sections()[0].get_left_lane_links())
                        for i in range(total_lanes):
                            index_list.append(i+1)
                        index_list.reverse()
                        adj_lane_id = index_list[connection.ego_lane-1]
                        connector.to_lanes.append(adj_lane_id)

                    elif connection in connection_road.get_lane_sections()[0].get_right_lane_links():
                        diff = len(connection_road.get_lane_sections()[0].get_left_lane_links())
                        adj_lane_id = connection.ego_lane - diff
                        connector.to_lanes.append((-1)*adj_lane_id)
                    
                    if incoming in incoming_road.get_lane_sections()[-1].get_left_lane_links() :
                        index_list = []
                        total_lanes = len(incoming_road.get_lane_sections()[-1].get_left_lane_links())
                        for i in range(total_lanes):
                            index_list.append(i+1)
                        index_list.reverse()
                        adj_lane_id = index_list[incoming.ego_lane-1]
                        connector.from_lanes.append(adj_lane_id)
                        
                    elif incoming in incoming_road.get_lane_sections()[-1].get_right_lane_links() and incoming is not None:
                        diff = len(incoming_road.get_lane_sections()[-1].get_left_lane_links())
                        adj_lane_id = incoming.ego_lane - diff
                        connector.from_lanes.append((-1)*adj_lane_id)
                else:
                    BaseException('[ERROR] All of connecting road lane in junction are not in the selected road (link id={})'.format(connection.idx))
                
        odr_data.set_junction_set(junction_set)

        # junction이 생성되어야 하는데 생성되지 않은 곳이 있는지 확인한다
        self.check_if_junction_should_be_created(odr_data)

        return odr_data


    def set_junction_and_connecting_lanes(self, odr_data, junction_set):
        for _notused, junction in junction_set.junctions.items():
            connecting_lanes = list()
            
            # find all the connecting lanes within each junction
            for node in junction.get_jc_nodes():
                survey_from_links = node.get_from_links()
                for survey_links in survey_from_links:
                    foremost_link = self.get_foremost_lane_in_the_same_road(survey_links)
                    survey_jc = foremost_link.get_from_node().junctions
                    if len(survey_jc) != 0:
                        for jc_candidate in survey_jc:
                            if jc_candidate == junction:
                                connecting_lanes.append(foremost_link)

            repeat_list = list()
            iterator = 1

            # determine properties of each connecting road
            for connecting_link in connecting_lanes:
                
                # find out the road id of the incoming road for each connecting road
                # account for floating links with no from_links
                if len(connecting_link.get_from_links()) < 1:
                    if connecting_link.lane_ch_link_left is not None:
                        if len(connecting_link.lane_ch_link_left.get_from_links()) < 1:
                            raise BaseException('No incoming lane into the connecting lane (link id: {})'.format(connecting_link.idx))
                        else:
                            incoming_link = connecting_link.lane_ch_link_left.get_from_links()[0] # search until the left lane link has a from_link
                    elif connecting_link.lane_ch_link_right is not None:
                        if len(connecting_link.lane_ch_link_right.get_from_links()) < 1:
                            raise BaseException('No incoming lane into the connecting lane (link id: {})'.format(connecting_link.idx))
                        else:
                            incoming_link = connecting_link.lane_ch_link_right.get_from_links()[0]
                    else:
                        raise BaseException('[ERROR] Connecting road lane does not have preceding element (link id={})'.format(connecting_link.idx))
                else:
                    incoming_link = connecting_link.get_from_links()[0]

                # either create or call connecting_road
                if connecting_link.road_id not in repeat_list:
                    # create new connecting road objects
                    junction.connecting_road[connecting_link.road_id] = ConnectingRoad()
                    repeat_list.append(connecting_link.road_id)

                    # assign properties to the connecting road object
                    connector = junction.connecting_road[connecting_link.road_id]
                    if iterator < 10:
                        iter_str = '0{}'.format(iterator)
                    else:
                        iter_str = '{}'.format(iterator)
                    # connector.idx = '{}'.format(junction.idx[2:]) + iter_str
                    connector.idx = '{}'.format(junction.idx) + iter_str
                    connector.connecting = odr_data.roads[connecting_link.road_id].id
                    connector.incoming = odr_data.roads[incoming_link.road_id].id

                    iterator += 1
                elif connecting_link.road_id in repeat_list:
                    # call existing connecting road object
                    connector = junction.connecting_road[connecting_link.road_id]

                # find and extract the road info of the connecting and incoming
                # roads within the junction
                connection_road = odr_data.roads[connecting_link.road_id]
                incoming_road = odr_data.roads[incoming_link.road_id]

                # type check just in case
                if isinstance(connecting_link.ego_lane, str):
                    connecting_link.ego_lane = int(connecting_link.ego_lane)
                if isinstance(incoming_link.ego_lane, str):
                    incoming_link.ego_lane = int(incoming_link.ego_lane)

                # connect lane ids between the incoming and connecting roads
                if connecting_link in connection_road.get_lane_sections()[0].get_left_lane_links():
                    index_list = []
                    total_lanes = len(connection_road.get_lane_sections()[0].get_left_lane_links())
                    for i in range(total_lanes):
                        index_list.append(i+1)
                    index_list.reverse()
                    
                    if (connecting_link.ego_lane) > 10:
                        adj_lane_id = index_list[0]
                    else:
                        try:
                            adj_lane_id = index_list[(connecting_link.ego_lane)-1]
                        except:
                            adj_lane_id = index_list[-(connecting_link.ego_lane)-1]
                    connector.to_lanes.append(adj_lane_id)

                elif connecting_link in connection_road.get_lane_sections()[0].get_right_lane_links():
                    diff = len(connection_road.get_lane_sections()[0].get_left_lane_links())
                    adj_lane_id = connecting_link.ego_lane - diff
                    connector.to_lanes.append((1)*adj_lane_id)

                if incoming_link in incoming_road.get_lane_sections()[-1].get_left_lane_links():
                    index_list = []
                    total_lanes = len(incoming_road.get_lane_sections()[-1].get_left_lane_links())
                    for i in range(total_lanes):
                        index_list.append(i+1)
                    index_list.reverse()
                    
                    if (incoming_link.ego_lane) > 10:
                        adj_lane_id = index_list[0]
                    else:
                        try:
                            adj_lane_id = index_list[incoming_link.ego_lane-1]
                        except:
                            adj_lane_id = index_list[-incoming_link.ego_lane-1]
                    connector.from_lanes.append(adj_lane_id)

                elif incoming_link in incoming_road.get_lane_sections()[-1].get_right_lane_links():
                    diff = len(incoming_road.get_lane_sections()[-1].get_left_lane_links())
                    adj_lane_id = incoming_link.ego_lane - diff
                    connector.from_lanes.append((1)*adj_lane_id)


    def convert(self, mgeo_data, odr_persistent_data):
        """
        Converts mgeo data and repackages it into a OdrData() object

        Arguments:
        mgeo_data -- node, link, junction, sign data loaded from mgeo save files 

        Returns:
        odr_data -- a OdrData() object with a list of OdrRoad() objects and
        JunctionSet() objects
        """

        # OpenDRIVE 변환 설정을 받아온다
        config_include_signal = self.get_config('include_signal')
        Logger.log_trace('OpenDRIVE Conv. Config: Include Signal: {}'.format(config_include_signal))

        config_fix_signal_road_id = self.get_config('fix_signal_road_id')
        Logger.log_trace('OpenDRIVE Conv. Config: Fix Signal Road ID: {}'.format(config_fix_signal_road_id))
        
        # OpenDRIVE 변환 설정에 따라 Lane 사이의 Link를 생략할 수 있다
        # => Junction 등을 생성하지 않고 CARLA에서 로드하기 위한 옵션으로, Autopliot은 동작하지 않게 된다
        # => Warning을 출력해준다.
        config_disable_lane_link = self.get_config('disable_lane_link')
        Logger.log_trace('OpenDRIVE Conv. Config: Disable Lane Link: {}'.format(config_disable_lane_link))
        if config_disable_lane_link:
            Logger.log_warning('Link information between links is omitted by the user. It will allow CARLA to open xodr files without any junctions, but disable autopilot function at the same time. Use this option to check road geometry only.')

        config_superelevation  = self.get_config('superelevation')
        Logger.log_trace('OpenDRIVE Conv. Config: Superelevation: {}'.format(config_superelevation))

        # extract mgeo_data 
        node_set = mgeo_data.node_set
        link_set = mgeo_data.link_set
        junction_set = mgeo_data.junction_set
        sign_set = mgeo_data.sign_set
        light_set = mgeo_data.light_set
        origin = mgeo_data.local_origin_in_global

        # check any link without road id
        for link in link_set.lines.values():
            if link.road_id is None:
                raise BaseException('link.road_id is None (link: {})'.format(link.idx))
            elif link.road_id == '':
                raise BaseException('link.road_id is an empty string (link: {})'.format(link.idx))

        # link_set으로부터 기본이 되는 odr road를 생성
        odr_data = self.create_odr_roads(mgeo_data, odr_persistent_data)

        # create geometries based on road data
        self.create_geometry(odr_data)

        # determine lane expansions
        # for road in odr_data.roads.values():
        #     Logger.log_debug('Determining lane expansion for road: {}'.format(road.road_id))
        #     self.determine_lane_expansion(road)
        #     Logger.log_debug('>> Done OK')

        # signal에 현재 매칭된 road가 적절하지 않아 이를 변경하려고 할 때,
        # 전체 road를 list로 전달해주어야 한다. 이를 위한 변수 생성
        all_road_list = [] 
        for road in odr_data.roads.values():
            if type(road.road_id) == str:    
                if road.road_id[:7] == "virtual":
                    continue
            all_road_list.append(road)

        # 시그널 생성 및 road에 추가
        if config_include_signal:
            # insert traffic signs to road
            # tomtom 데이터에 road/link 정보 없어서 추가해야함

            #signal initializing
            for road in odr_data.roads.values():
                road.signals = []
        
            for signal in sign_set.signals.values():

                if signal.road_id == '' or signal.road_id is None:
                    candidate_roads = []
                    xlim = [signal.point[0] - 30, signal.point[0] + 30]
                    ylim = [signal.point[1] - 30, signal.point[1] + 30]

                    signal_heading_vec = np.array([np.cos(np.radians(signal.heading)), np.sin(np.radians(signal.heading))])
                    com_dist = np.inf
                    
                    for road in odr_data.roads.values():
                        if road.ref_line[0].is_out_of_xy_range(xlim, ylim) is False:
                            try:
                                ref_line_point = road.ref_line[0].lane_mark_left[0].points
                            except:
                                pass
                            ref_line_geometry = road.ref_line[0].lane_mark_left[0].geometry

                            for cnt in range(len(ref_line_geometry)):
                                if cnt == len(ref_line_geometry) - 1:
                                    p0 = ref_line_point[ref_line_geometry[cnt]['id']][0:2]
                                    p1 = ref_line_point[-1][0:2]
                                else:
                                    p0 = ref_line_point[ref_line_geometry[cnt]['id']][0:2]
                                    p1 = ref_line_point[ref_line_geometry[cnt+1]['id']][0:2]
                                
                                road_heading_vec = (p1-p0) / np.linalg.norm(p1-p0)

                                if np.inner(signal_heading_vec, road_heading_vec) > 0:
                                    if road in candidate_roads:
                                        continue

                                    dist = self.get_closest_pt_on_line(road.ref_line[0].points, signal.point)
                                    if com_dist > dist:
                                        com_dist = dist
                                        candidate_roads.insert(0, road)
                                    else:
                                        candidate_roads.append(road)

                    if len(candidate_roads) > 0:
                        result, solution, matching_road = OdrSignal.FindMatchingRoad(signal, candidate_roads)

                        if result:
                            matching_road = matching_road
                        else:
                            matching_road = candidate_roads[0]
                        signal.road_id = matching_road.road_id
                        signal.link_id_list.append(matching_road.ref_line[0].idx)
                        signal.link_list.append(matching_road.ref_line[0])
                        
                    else:
                        min_road = []
                        min_dist = np.inf
                        for road in odr_data.roads.values():
                            if road.ref_line[0].is_out_of_xy_range(xlim, ylim) is False:
                                dist = self.get_closest_pt_on_line(road.ref_line[0].points, signal.point)
                                if min_dist > dist:
                                    min_dist = dist
                                    min_road.insert(0, road)
                                else:
                                    min_road.append(road)

                        result, solution, matching_road = OdrSignal.FindMatchingRoad(signal, candidate_roads)
                        if result:
                            matching_road = matching_road
                        else:
                            matching_road = min_road[0]

                        signal.road_id = matching_road.road_id
                        signal.link_id_list.append(matching_road.ref_line[0].idx)
                        signal.link_list.append(matching_road.ref_line[0])
                        Logger.log_info('Signal id: {} (heading: {}) was allocated to the closest road object. (road id: {})'.format(signal.idx, signal.heading, signal.road_id))

                # insert traffic signs to road
                if signal.road_id in odr_data.roads: 
                    road = odr_data.roads[signal.road_id]

                    odr_signal, matching_odr_road = OdrSignal.CreateInstanceFromMGeoSignal(
                        signal,
                        road,
                        fix_road=config_fix_signal_road_id,
                        candidate_roads=all_road_list)

                    # 실제 road와 매칭되는 road가 다를 수 있으므로, matching_odr_road를 체크해야 함
                    if matching_odr_road is not None:
                        matching_odr_road.add_signal(odr_signal)
                    else:
                        # matching_odr_road가 None인 경우는, 따로 매칭시킬 road가 없다.
                        # positionInertial을 이용할 수 있으므로, 초기 데이터의 road에 매칭시킨다
                        road.add_signal(odr_signal)
                        
                else: 
                    Logger.log_error('Road ID: {}'.format(signal.road_id))
                    raise BaseException('[ERROR] Could not find road ID mapped in odr_data.roads.')

            # insert traffic lights to road (traffic sign 경우와 완전히 동일 작업)
            for signal in light_set.signals.values():
                
                if signal.road_id == '' or signal.road_id is None:
                    
                    if len(signal.link_id_list) != 0:
                        signal.road_id = link_set.lines[signal.link_id_list[0]].road_id
                    else:
                        candidate_roads = []
                        xlim = [signal.point[0] - 30, signal.point[0] + 30]
                        ylim = [signal.point[1] - 30, signal.point[1] + 30]

                        signal_heading_vec = np.array([np.cos(np.radians(signal.heading)), np.sin(np.radians(signal.heading))])
                        com_dist = np.inf
                        
                        for road in odr_data.roads.values():
                            if road.ref_line[0].is_out_of_xy_range(xlim, ylim) is False:
                                ref_line_point = road.ref_line[0].lane_mark_left[0].points
                                ref_line_geometry = road.ref_line[0].lane_mark_left[0].geometry

                                for cnt in range(len(ref_line_geometry)):
                                    if cnt == len(ref_line_geometry) - 1:
                                        p0 = ref_line_point[ref_line_geometry[cnt]['id']][0:2]
                                        p1 = ref_line_point[-1][0:2]
                                    else:
                                        p0 = ref_line_point[ref_line_geometry[cnt]['id']][0:2]
                                        p1 = ref_line_point[ref_line_geometry[cnt+1]['id']][0:2]
                                    
                                    road_heading_vec = (p1-p0) / np.linalg.norm(p1-p0)

                                    if np.inner(signal_heading_vec, road_heading_vec) > 0:
                                        if road in candidate_roads:
                                            continue

                                        dist = self.get_closest_pt_on_line(road.ref_line[0].points, signal.point)
                                        if com_dist > dist:
                                            com_dist = dist
                                            candidate_roads.insert(0, road)
                                        else:
                                            candidate_roads.append(road)

                        if len(candidate_roads) > 0:
                            result, solution, matching_road = OdrSignal.FindMatchingRoad(signal, candidate_roads)

                            if result:
                                matching_road = matching_road
                            else:
                                matching_road = candidate_roads[0]
                            signal.road_id = matching_road.road_id
                            signal.link_id_list.append(matching_road.ref_line[0].idx)
                            signal.link_list.append(matching_road.ref_line[0])
                            
                        else:
                            min_road = []
                            min_dist = np.inf
                            for road in odr_data.roads.values():
                                if road.ref_line[0].is_out_of_xy_range(xlim, ylim) is False:
                                    dist = self.get_closest_pt_on_line(road.ref_line[0].points, signal.point)
                                    if min_dist > dist:
                                        min_dist = dist
                                        min_road.insert(0, road)
                                    else:
                                        min_road.append(road)

                            result, solution, matching_road = OdrSignal.FindMatchingRoad(signal, candidate_roads)
                            if result:
                                matching_road = matching_road
                            else:
                                matching_road = min_road[0]

                            signal.road_id = matching_road.road_id
                            signal.link_id_list.append(matching_road.ref_line[0].idx)
                            signal.link_list.append(matching_road.ref_line[0])
                            Logger.log_info('Signal id: {} (heading: {}) was allocated to the closest road object. (road id: {})'.format(signal.idx, signal.heading, signal.road_id))
                
                if signal.road_id in odr_data.roads: 
                    road = odr_data.roads[signal.road_id]

                    odr_signal, matching_odr_road = OdrSignal.CreateInstanceFromMGeoSignal(
                        signal,
                        road,
                        fix_road=config_fix_signal_road_id,
                        candidate_roads=all_road_list)

                    # 실제 road와 매칭되는 road가 다를 수 있으므로, matching_odr_road를 체크해야 함
                    if matching_odr_road is not None:
                        matching_odr_road.add_signal(odr_signal)
                    else:
                        # matching_odr_road가 None인 경우는, 따로 매칭시킬 road가 없다.
                        # positionInertial을 이용할 수 있으므로, 초기 데이터의 road에 매칭시킨다
                        road.add_signal(odr_signal)
                        
                else: 
                    Logger.log_error('Road ID: {}'.format(signal.road_id))
                    raise BaseException('[ERROR] Could not find road ID mapped in odr_data.roads.')
                #if signal.road_id == "" or signal.road_id == None:
                #    signal.road_id = list(odr_data.roads.keys())[0]
                    
                #if signal.road_id in odr_data.roads:
                #    road = odr_data.roads[signal.road_id]

                #    odr_signal, matching_odr_road = OdrSignal.CreateInstanceFromMGeoSignal(
                #        signal,
                #        road,
                #        fix_road=config_fix_signal_road_id,
                #        candidate_roads=all_road_list)

                #    # 실제 road와 매칭되는 road가 다를 수 있으므로, matching_odr_road를 체크해야 함
                #    if matching_odr_road is not None:
                #        matching_odr_road.add_signal(odr_signal)
                #    else:
                #        # matching_odr_road가 None인 경우는, 따로 매칭시킬 road가 없다.
                        # positionInertial을 이용할 수 있으므로, 초기 데이터의 road에 매칭시킨다
                #        road.add_signal(odr_signal)

                #else: 
                #    Logger.log_error('Road ID: {}'.format(signal.road_id))
                #    raise BaseException('[ERROR] Could not find road ID mapped in odr_data.roads.')
        
        # find all the connecting lanes within each junction
        self.set_junction_and_connecting_lanes(odr_data, junction_set)

        # loads junction data into the OdrData class
        odr_data.set_junction_set(junction_set)

        # junction이 생성되어야 하는데 생성되지 않은 곳이 있는지 확인한다
        self.check_if_junction_should_be_created(odr_data)

        return odr_data


    @staticmethod
    def get_lane_gaps(left_lane, right_lane):
        def get_distance(point1, point2):
            x_diff = point1[0] - point2[0]
            y_diff = point1[1] - point2[1]
            distance = np.sqrt(x_diff**2 + y_diff**2)
            return distance

        point_left = left_lane.points[0][0:2]
        point_right = right_lane.points[0][0:2]

        endpoint_left = left_lane.points[-1][0:2]
        endpoint_right = right_lane.points[-1][0:2]

        return [get_distance(point_left, point_right),
            get_distance(endpoint_left, endpoint_right)]


    def get_closest_pt_on_line(self, points, P):
        """
        point 부터 road(ref_line) 까지의 최소 거리 구하기
        """
        min_dist = np.inf

        for index in range(len(points)-1):
            A = points[index]
            B = points[index + 1]
            a_to_p = [P[0] - A[0], P[1] - A[1]]
            a_to_b = [B[0] - A[0], B[1] - A[1]]
            atb2 = a_to_b[0]**2 + a_to_b[1]**2
            atp_dot_atb = a_to_p[0]*a_to_b[0] + a_to_p[1]*a_to_b[1]
            distance = atp_dot_atb / atb2
            if distance < 0:
                qq = a_to_p[0]**2 + a_to_p[1]**2
            elif distance > 1: 
                b_to_p = [P[0] - B[0], P[1] - B[1]]
                qq = b_to_p[0]**2 + b_to_p[1]**2
            else:
                scaleAB = [a_to_b[0] * distance, a_to_b[1] * distance]
                perpendicular_point = [A[0] +scaleAB[0] , A[1] + scaleAB[1]]
                perperdicular_p_to_p = [P[0] - perpendicular_point[0], P[1] - perpendicular_point[1]]
                qq = perperdicular_p_to_p[0]**2 + perperdicular_p_to_p[1]**2

            if min_dist > qq:
                min_dist = qq

        return min_dist


    def get_closest_pt_on_line_index(self, points, P):
        """
        point 부터 road(ref_line) 까지의 index 구하기
        """
        min_dist = np.inf
        min_index = 0
        for index in range(len(points)-1):
            A = points[index]
            B = points[index + 1]
            a_to_p = [P[0] - A[0], P[1] - A[1]]
            a_to_b = [B[0] - A[0], B[1] - A[1]]
            atb2 = a_to_b[0]**2 + a_to_b[1]**2
            atp_dot_atb = a_to_p[0]*a_to_b[0] + a_to_p[1]*a_to_b[1]
            distance = atp_dot_atb / atb2
            if distance < 0:
                
                min_index = index
        
        return min_index
    
    
    def get_closest_pt_on_line_index_dist(self, points, P):
        """
        point 부터 road(ref_line) 까지의 index 구하기
        """
        min_dist = np.inf
        for index in range(len(points)):
            min = sum((np.array(points[index][:2]) - np.array(P)[:2])**2)
            
            if min_dist > min:
                min_dist = min
                if index ==  len(points)-1:
                    return index, min_dist
            else:    
                return index-1 , min_dist
            