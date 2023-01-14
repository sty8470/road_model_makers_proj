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
from lib.mgeo.edit.funcs import edit_link

import numpy as np

from lib.mgeo.class_defs import *
from xodr_signal import OdrSignal
from xodr_data import OdrData
from xodr_road import OdrRoad
from xodr_lane_section import OdrLaneSection


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
            1586401
            ]

        self.odr_conversion_config = None


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
            # Logger.log_warning('Road: {} is a closed-loop road. Link: {} will be used for the first lane'.format(link.road_id, searched_link[0].idx))
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
            arc = arc + np.sqrt((x[indx] - x[indx - 1])**2 + (y[indx] - y[indx - 1])**2)
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


    def create_geometry(self, odr_data):
        """
        Organizes vector data of each road's reference line before calculating geometries
        """
        road_residual = []
        for _notused, road in odr_data.roads.items():
            # initialize by road
            s_offset = 0
            lane_length = 0
            # iterate by OdrLaneSection
            for lane_section in road.get_lane_sections():
                ref_id = lane_section.reference_line_piece.idx
                Logger.log_info('Determining geometry for Link: {}'.format(ref_id))
                
                # initialize by lane section
                ref_line = lane_section.get_ref_lane().link

                # starting s value calculations for each lane
                s_offset += lane_length
                lane_length = 0
                lane_section.s_offset = s_offset
                vs_offset = s_offset
                arclength = 0

                # # check in case reference line has no lane markings
                # if ref_line.lane_mark_left is not []:
                #     ref_line_mark = ref_line.lane_mark_left[0]
                # else:
                #     ref_line_mark = ref_line
                #     Logger.log_warning('No Lane Marking found for Reference Lane {}'.format(ref_line.idx))
                ref_line_mark = ref_line
                # determine first and last points for the reference line
                road_from_point_True = 0
                road_to_point_True = 0
                try:
                    road_from_point = ref_line_mark.get_from_links()[0].points[-2]
                    road_from_point_True = 1
                except:
                    road_from_point = ref_line_mark.points[0]
                    road_pre_from_point = road_from_point 
                
                if road_from_point_True == 1:
                    try:
                        road_pre_from_point = ref_line_mark.get_from_links()[0].points[-3]
                    except:
                        try:
                            road_pre_from_point = ref_line_mark.get_from_links()[0].get_from_links()[0].points[-2]
                        except:
                            road_pre_from_point = road_from_point

                try:
                    road_to_point =  ref_line_mark.get_to_links()[0].points[1]
                    road_to_point_True =1
                except:
                    road_to_point =  ref_line_mark.points[-1]
                    road_aft_to_point = road_to_point
                
                if road_to_point_True == 1:
                    try:
                        road_aft_to_point = ref_line_mark.get_to_links()[0].points[2]
                    except:
                        try:
                            road_aft_to_point = ref_line_mark.get_to_links()[0].get_to_links()[0].points[1]
                        except:
                            road_aft_to_point = road_to_point


                # identify reference line geometry with the segmentation indices from
                # ref_line.geometry and divide the reference lane marking into user defined vectors
                vector_list = self.segment_geometry(ref_line_mark, ref_line_mark)
                residual_segment = []

                # run poly_geometry and poly_elevation
                for i in range(len(vector_list)):
                    vector = vector_list[i]
                    geometry_type = ref_line_mark.geometry[i]['method']
                    
                    # update sOffset 
                    vs_offset += arclength
                    lane_section.vector_s_offset.append(vs_offset)

                    # allocate points to determine boundary conditions
                    if len(vector_list) == 1:
                        from_point = road_from_point
                        to_point = road_to_point
                    else:
                        if i == 0:
                            from_point = road_from_point
                            try:
                                to_point = vector_list[i+1][1]
                            except:
                                to_point = vector_list[i][-1]

                        elif i == len(vector_list)-1:
                            to_point = road_to_point
                            try:
                                from_point = vector_list[i-1][-2]
                            except:
                                from_point = vector_list[i][0]
                        else:
                            try:
                                from_point = vector_list[i-1][-2]
                            except:
                                from_point = vector_list[i][-1]
                            try:
                                to_point = vector_list[i+1][1]
                            except:
                                to_point = vector_list[i][-1]
                            # if vector_list[i+1] ==[]:
                            #     to_point = vector_list[i][-1]
                            # else:
                            #     to_point = vector_list[i+1][1]
                    # fit for one of paramPoly3, poly3, or line
                    if geometry_type == 'paramPoly3':
                        # paramPoly3
                        # init_coord, heading, arclength, poly_geo, uv_point ,residual= \
                            # self.bezier_geometry_general_boundary_all_extended(vector, to_point, from_point,aft_to_point,pre_from_point)
                        if len(vector) < 1:
                            continue                       
                        init_coord, heading, arclength, poly_geo, uv_point, residual, to_slope = \
                            self.bezier_geometry_general_boundary_all(vector, to_point, from_point)

                        if max(np.abs(residual)) > 0.1:
                            # if the initial fit result is unsatisfactory, we divide the reference line into two
                            Logger.log_trace('Large residual detected at line {}, residual: {}'.format(ref_line_mark.idx, max(np.abs(residual))))
                            
                            # fit first segement
                            init_coord, heading, arclength, poly_geo, uv_point, residual, to_slope = \
                                self.bezier_geometry_general_boundary_all(vector[:len(vector)//2 +1], vector[len(vector)//2+1], from_point)

                            residual_segment += residual.tolist()
                            u = uv_point[:,0]
                            u_max = uv_point[-1][0]

                            poly_elev, check_coord_e = \
                                self.poly_elevation_bezier_boundary(vector[:len(vector)//2 +1], vector[len(vector)//2+1], from_point)
                            lane_length += arclength

                            # poly_super = \
                            #      self.poly_elevation_bezier_boundary_super(vector, to_point, from_point, right_lane, perpendicular_dist)

                            lane_section.init_coord.append(init_coord)
                            lane_section.heading.append(heading)
                            lane_section.arclength.append(arclength)
                            lane_section.geometry.append(poly_geo)
                            lane_section.geometry_u_max.append(u_max)
                            lane_section.elevation.append(poly_elev)
                            # lane_section.lateral.append(poly_super)

                            Logger.log_trace('split residual 1 {}'.format(max(np.abs(residual))))

                            # update vs_offset values
                            vs_offset += arclength
                            lane_section.vector_s_offset.append(vs_offset)

                            # fit second segment
                            init_coord, heading, arclength, poly_geo, uv_point ,residual, to_slope= \
                                self.bezier_geometry_general_boundary_all(vector[len(vector)//2:], to_point,vector[len(vector)//2-1])
                            
                            residual_segment += residual.tolist()
                            u = uv_point[:,0]
                            u_max = uv_point[-1][0]

                            poly_elev, check_coord_e = \
                                self.poly_elevation_bezier_boundary(vector[len(vector)//2:], to_point, vector[len(vector)//2-1])
                            lane_length += arclength
                            
                            # poly_super = \
                            #      self.poly_elevation_bezier_boundary_super(vector, to_point, from_point, right_lane, perpendicular_dist)

                            Logger.log_trace('End point boundary slope value {}'.format(to_slope))
                            Logger.log_trace('split residual 2 {}'.format(max(np.abs(residual))))

                        else:
                            # we stick with the initial fit results
                            residual_segment += residual.tolist()
                            u = uv_point[:,0]
                            u_max = uv_point[-1][0]

                            poly_elev, check_coord_e = \
                                self.poly_elevation_bezier_boundary(vector, to_point, from_point)
                            
                            # poly_super = \
                            #      self.poly_elevation_bezier_boundary_super(vector, to_point, from_point, right_lane, perpendicular_dist)
                            
                            # lane_section.lateral.append(poly_super)

                            # right_lane_poly_elev, check_coord_e = \
                            #     self.poly_elevation_bezier_boundary(vector_right, to_point, from_point)
                            
                            # perpendicular_dist = 
                            
                            # poly_super_elev = \
                            #     self.super_elevation(line_s_coord, poly_elev, right_lane_poly_elev, perpendicular_dist)

                            lane_length += arclength
                    
                    elif geometry_type == 'poly3':
                        init_coord, heading, arclength, poly_geo, uv_point, lat_misc_fit_result = \
                            self.poly_geometry(vector)
                        
                        u = uv_point[:,0]
                        u_max = uv_point[-1][0]
                        lane_length += arclength

                        poly_elev, check_coord_e, ele_misc_fit_result = \
                            self.poly_elevation(vector)

                        self.check_accuracy(ref_id, i, u, u_max, lat_misc_fit_result, ele_misc_fit_result)

                    else:
                        # designated as a line
                        init_coord, heading, arclength, poly_geo, uv_point, lat_misc_fit_result = \
                            self.poly_geometry(vector)
                            # self.poly_geometry(vector, linear=True)

                        u_max = uv_point[-1][0]
                        lane_length += arclength

                        poly_elev, check_coord_e, ele_misc_fit_result = \
                            self.poly_elevation(vector)

                    # save to OdrLaneSection
                    lane_section.init_coord.append(init_coord)
                    lane_section.heading.append(heading)
                    lane_section.arclength.append(arclength)
                    lane_section.geometry.append(poly_geo)
                    lane_section.geometry_u_max.append(u_max)
                    lane_section.elevation.append(poly_elev)
                    
                    # lane length is sum of vector arclengths
                    # lane_length += arclength

                # assign a total lane length (sum of all arclengths)
                lane_section.lane_length = lane_length
                
                # check rotation and polyfit results
                if (self.CHK is True
                    and road.road_id in self.CHK_ID):
                    self.check_geometry(uv_point, check_coord_e, poly_geo, poly_elev)
                    Logger.log_info('Checking: Road {}'.format(road.road_id))
                
                # check residuals and error
                if geometry_type == 'paramPoly3':
                    rms = np.sqrt(sum(map(lambda x: x**2, residual_segment))/len(residual_segment))
                    Logger.log_trace('- Segment RMS Residual {}'.format(rms))
                    Logger.log_trace('- Segment max Residual {}'.format(max(np.abs(residual_segment))))
                    road_residual += residual_segment

            # assign rest of OdrRoad properties
            road.road_length = s_offset + lane_length
        
        if geometry_type == 'paramPoly3':
            rms = np.sqrt(sum(map(lambda x: x**2, road_residual))/len(road_residual))
            Logger.log_info('- Road RMS Residual {}'.format(rms))
            Logger.log_info('- Road max Residual {}'.format(sorted(np.abs(road_residual))[-len(road_residual)//100:]))

    
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


    def get_linearity(self, x, y, angle):
        """
        Determines all vectors within a line are aligned within [angle] degrees

        Arguments:
        x: list of all vector x coordinates
        y: list of all vector y coordinates
        angle: the minimum angle allowed to be considered linear [degrees]
        """
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


    def bezier_geometry_general_boundary_all(self, lane_vector, to_point, from_point):
        lane_vector = lane_vector[:,0:2]
        
        x_init = lane_vector[0][0]
        y_init = lane_vector[0][1]
        
        init_coord = np.array([x_init, y_init])
        line_moved_origin = lane_vector - init_coord
        from_point = from_point[:2]
        to_point = to_point[:2]
        from_point_moved = from_point - init_coord
        to_point_moved = to_point - init_coord

        # from_u = line_moved_origin[1][0] - from_point_moved[0]
        # from_v = line_moved_origin[1][1] - from_point_moved[1]

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
        
        return init_coord, from_heading, arclength, poly_out, rotated_line, residual,b


    def find_distance(self, x, y):
        # because in OpenDRIVE, right > 0, and left < 0 we multiply the final distance
        # (the A coefficient value) value by (-1)
        distance = np.sqrt(x**2 + y**2)
        if y > 0:
            distance = distance*(-1)
        return distance


    def till_length(self, data):
        till_length = 0
        for j in range(1, len(data)):
            till_length += np.sqrt((data[j][0] - data[j-1][0])**2 + (data[j][1] - data[j-1][1])**2)
        return till_length
    

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
        linearity = self.get_linearity(line_x_coord, line_y_coord, 0.1)
        # linearity = self.get_linearity(line_x_coord, line_y_coord, 0.1, linear)
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


    # def poly_geometry(self, pt_array):
    #     # pt_array = lane_data.points
    #     pt_array = pt_array[:,0:2]

    #     # transform initial point to origin
    #     global_x_init = pt_array[0][0]
    #     global_y_init = pt_array[0][1]
    #     init_coord = np.array([global_x_init, global_y_init])
    #     line_moved_origin = pt_array - init_coord

    #     # get the heading for line segment individual_lane
    #     u = line_moved_origin[1][0]
    #     v = line_moved_origin[1][1]
    #     heading = np.arctan2(v, u)  # heading is in radians

    #     # get the arc length for each line segment individual_lane
    #     arc = self.arclength_of_line(line_moved_origin[:,0], line_moved_origin[:,1])
    #     arclength = arc + 0.1  # forced connections b/n roads

    #     # rotate the line coordinates by the heading
    #     inv_heading = (-1) * heading
    #     rotated_line = self.coordinate_transform(inv_heading, line_moved_origin)

    #     # arrange coordinates for polynomial fitting
    #     line_x_coord = rotated_line[:,0]
    #     line_y_coord = rotated_line[:,1]

    #     # avoid DLASCLS legality error (deprecate)
    #     # thresh = 0.0001
    #     # x_idx = list()
    #     # y_idx = list()
    #     # for idx, x_coord in enumerate(line_x_coord):
    #     #     if (abs(x_coord) < thresh) and (x_coord != 0):
    #     #         x_idx.append(idx)
    #     # for idx, y_coord in enumerate(line_y_coord):
    #     #     if (abs(y_coord) < thresh) and (y_coord != 0):
    #     #         y_idx.append(idx)
    #     # err_idx = x_idx
    #     # for y in y_idx:
    #     #     if y not in x_idx:
    #     #         err_idx.append(y)
    #     # poly_x_coord = np.delete(line_x_coord, err_idx, None)
    #     # poly_y_coord = np.delete(line_y_coord, err_idx, None)

    #     # check for linearity
    #     # linearity = self.get_linearity(poly_x_coord, poly_y_coord, 0.1)
    #     linearity = self.get_linearity(line_x_coord, line_y_coord, 0.1)

    #     # determine type of fit to use
    #     if linearity is True:
    #         poly_out = np.array([0, 0, 0, 0])
    #         misc_fit_result = (np.array([0]) ,) # TODO(sglee): temporary value!
    #     else:
    #         # refer to documentation for Polynomial.fit
    #         # https://numpy.org/doc/stable/reference/generated/numpy.polynomial.polynomial.Polynomial.fit.html?highlight=polynomial%20fit#numpy.polynomial.polynomial.Polynomial.fit
    #         series, misc_fit_result = np.polynomial.polynomial.Polynomial.fit(
    #             line_x_coord,
    #             line_y_coord,
    #             3,
    #             full=True
    #         )
    #         # residuals = misc_fit_result[0]
    #         poly_out = series.convert().coef

    #     return init_coord, heading, arclength, poly_out, rotated_line, misc_fit_result


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


    def poly_elevation_bezier_boundary_super(self, lane_vector, to_point, from_point, right_lane, perpendicular_dist):
        
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

        slope_first = self.get_angle( lane_vector[1], right_lane, perpendicular_dist) - self.get_angle(from_point, right_lane, perpendicular_dist) \
              / np.sqrt((line_x_coord[1] - from_point_moved[0])**2 +  (line_y_coord[1] - from_point_moved[1])**2)
        
        slope_last = self.get_angle( lane_vector[-2], right_lane, perpendicular_dist) - self.get_angle(to_point, right_lane, perpendicular_dist) \
              /  np.sqrt((to_point_moved[0]- line_x_coord[-2])**2 +  (to_point_moved[1]- line_y_coord[-2])**2)

        x = line_s_coord[-1]
        y = self.get_angle( lane_vector[-1], right_lane, perpendicular_dist)
        y_prime = slope_last
        
        a = self.get_angle( lane_vector[0], right_lane, perpendicular_dist)
        b = slope_first
        d =(y_prime - b + 2*(-y + a+ b*x  )/x )/(x**2)
        c = (y - d*(x**3) - (a+ b*x))/(x**2)
        
        poly_out_elev = np.array([a, b, c, d])
        
        return poly_out_elev


    def poly_elevation(self, pt_array):
        # pt_array = lane_data.points
        pt_array_xy = pt_array[:,0:2]
        
        # transform initial point to origin
        global_x_init = pt_array_xy[0][0]
        global_y_init = pt_array_xy[0][1]
        init_coord = np.array([global_x_init, global_y_init])
        line_moved_origin = pt_array_xy - init_coord

        line_x_coord = line_moved_origin[:,0]
        line_y_coord = line_moved_origin[:,1]

        line_s_coord = np.sqrt(np.power(line_x_coord,2)
            + np.power(line_y_coord, 2))
        line_h_coord = pt_array[:,2]

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
        """[TEMP] id shortening function to avoid carla errors"""
        carla_id_length = 13
        id_str = str(id)
        id_len = len(id_str)
        if id_len > carla_id_length:
            short_id = id_str[(id_len - 7):id_len]
            id_out = int(short_id)
        else:
            id_out = id
        return id_out


    def create_preliminary_odr_roads(self, link_set, id_shortening=True):
        if id_shortening:
            # [TEMP] id shortening to circumvent issues with carla integration
            for _notused, each_link in link_set.lines.items():
                short_id = self.shorten_id(each_link.road_id)
                each_link.road_id = short_id
            # [ENDTEMP]

        """link_set에서 road를 생성한다"""
        odr_data = OdrData()
        for idx, link in link_set.lines.items():
            
            road_id = link.road_id

            if (road_id is None) or (road_id == ''):
                Logger.log_error('Link: {} has no road_id'.format(idx))
                continue

            if road_id not in odr_data.roads.keys():
                # create new road
                road = OdrRoad()
                road.road_id = road_id 
                odr_data.append_road_to_data(road)

            else:
                road = odr_data.roads[road_id]

            road.link_list_not_organized.append(link)

        return odr_data


    def create_odr_roads(self, link_set, odr_persistent_data=None, id_shortening=True):
        if odr_persistent_data is not None:
            odr_data = odr_persistent_data
        else:
            odr_data = self.create_preliminary_odr_roads(link_set, id_shortening)

        # Link의 Reference Line 관련 정보를 모두 초기화한다
        for link in link_set.lines.values():
            edit_link.reset_odr_conv_variables(link)


        # 각 Road에 대해 Reference Line을 먼저 찾는다
        for road in odr_data.roads.values():
            Logger.log_info('Searching for ref line for road: {}'.format(road.road_id))
            if road.changed == False:
                road.find_reference_line()
                Logger.log_info('>> done OK. ref line: {}'.format(Link.get_id_list_string(road.ref_line)))
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
                Logger.log_info('>> done OK.')


        # gap이 설정되어있지 않은 lane에 대해 gap을 설정한다
        self.estimate_lane_gap(odr_data, link_set)


        # 각 Road에 대해 다음의 작업 수행
        for road in odr_data.roads.values():
            # frontmost_left, rearmost_left 계산하기
            frontmost_left = road.get_frontmost_left()
            rearmost_left = road.get_rearmost_left()

            predecessor_survey_results = road.find_predecessors()
            successor_survey_results = road.find_successors()

            """road의 predecessor_id, successor_id 설정 (id 및 road/junction 여부)"""

            # determine road predecessor_id successor_id ids
            pre_node = frontmost_left.get_from_node()
            suc_node = rearmost_left.get_to_node()
            pre_jc_cnt = len(pre_node.junctions)
            suc_jc_cnt = len(suc_node.junctions)

            # differentiate road-based predecessor_id/successor_id
            if len(predecessor_survey_results) > 0:
                predecessor_road_id = predecessor_survey_results[0]
            else:
                predecessor_road_id = None

            if len(successor_survey_results) > 0:
                successor_road_id = successor_survey_results[0]
            else:
                successor_road_id = None

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


    def set_junction_and_connecting_lanes(self, odr_data, junction_set):
        # find all the connecting lanes within each junction
        for _notused, junction in odr_data.mgeo_planner_map.junction_set.junctions.items():
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
            for connecting_link in connecting_lanes:
                # find out the road id of the preceding/incoming links
                # account for floating links with no from_links
                if len(connecting_link.get_from_links()) < 1:
                    if connecting_link.lane_ch_link_left is not None:
                        incoming_link = connecting_link.lane_ch_link_left.get_from_links()[0]
                    elif connecting_link.lane_ch_link_right is not None:
                        incoming_link = connecting_link.lane_ch_link_right.get_from_links()[0]
                    else:
                        raise BaseException('[ERROR] Connecting road lane does not have preceding element')
                else:
                    incoming_link = connecting_link.get_from_links()[0]

                # create or call junction.connecting_road
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
                    connector.idx = '{}'.format(junction.idx[2:]) + iter_str
                    connector.connecting = connecting_link.road_id
                    connector.incoming = incoming_link.road_id
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
                    adj_lane_id = index_list[connecting_link.ego_lane-1]
                    connector.to_lanes.append(adj_lane_id)

                elif connecting_link in connection_road.get_lane_sections()[0].get_right_lane_links():
                    diff = len(connection_road.get_lane_sections()[0].get_left_lane_links())
                    adj_lane_id = connecting_link.ego_lane - diff
                    connector.to_lanes.append((-1)*adj_lane_id)

                if incoming_link in incoming_road.get_lane_sections()[-1].get_left_lane_links():
                    index_list = []
                    total_lanes = len(incoming_road.get_lane_sections()[-1].get_left_lane_links())
                    for i in range(total_lanes):
                        index_list.append(i+1)
                    index_list.reverse()
                    adj_lane_id = index_list[incoming_link.ego_lane-1]
                    connector.from_lanes.append(adj_lane_id)
                    
                elif incoming_link in incoming_road.get_lane_sections()[-1].get_right_lane_links():
                    diff = len(incoming_road.get_lane_sections()[-1].get_left_lane_links())
                    adj_lane_id = incoming_link.ego_lane - diff
                    connector.from_lanes.append((-1)*adj_lane_id)


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

        config_superelevation = self.get_config('superelevation')
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
        odr_data = self.create_odr_roads(link_set, odr_persistent_data)
        odr_data.mgeo_planner_map = mgeo_data

        # create geometries based on road data
        self.create_geometry(odr_data)

        # determine lane expansions
        # NOTE: create_geometry가 먼저 수행되어야 함!
        # for road in odr_data.roads.values():
        #     Logger.log_debug('Determining lane expansion for road: {}'.format(road.road_id))
        #     self.determine_lane_expansion(road)
        #     Logger.log_debug('>> Done OK')

        # signal에 현재 매칭된 road가 적절하지 않아 이를 변경하려고 할 때,
        # 전체 road를 list로 전달해주어야 한다. 이를 위한 변수 생성
        all_road_list = []
        for road in odr_data.roads.values():
            all_road_list.append(road)

        # 시그널 생성 및 road에 추가
        if config_include_signal:
            # signals can be remade each convert() call
            for road in odr_data.roads.values():
                road.signals = []

            for signal in sign_set.signals.values():

                # initial check for non-connected signals
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
                        Logger.log_info('Signal ID: {} (Heading: {}) was allocated to the closest road object. (Road ID: {})'.format(signal.idx, signal.heading, signal.road_id))
            
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