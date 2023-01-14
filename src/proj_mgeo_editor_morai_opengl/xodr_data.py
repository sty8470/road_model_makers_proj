"""
OdrData Module
"""

import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from lib.common.logger import Logger
import mgeo_odr_converter
from pyproj import Proj
import lxml.etree as etree
import datetime 
import json
import numpy as np
from scipy.spatial import ConvexHull
class OdrData:
    """
    OdrData
    """
    def __init__(self, mgeo_planner_map):
        self.roads = dict()
        self.junction_set = None # REFACTOR(sglee): mgeo_planner_map을 전달받으므로, junction_set을 별도로 받을 필요가 없다
        self.mgeo_planner_map = mgeo_planner_map
        self.flag_keep_data = False

    def append_road_to_data(self, road):
        road.parent_odr_data = self
        self.roads[road.road_id] = road

    def remove_road_to_data(self, road):
        # if road.road_id not in self.roads.keys():
        #     Logger.log_error('road.idx={} not in self.roads.keys()'.format(road.road_id))
        self.roads.pop(road.road_id)

    def current_date(self):
        # refer to python documentation for strftime() syntax
        # https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        current = datetime.datetime.now()
        current_str = current.strftime('%Y-%m-%dT%H:%M:%S')
        return current_str

    def is_line(self, polynomial):
        for constant in polynomial:
            if constant != 0:
                return False
        return True

    def set_junction_set(self, junction_set):
        self.junction_set = junction_set

    def to_xml_string(self):
        """
        Generates a XML string using road data from OdrData().roads
        """
        # OpenDRIVE 변환 설정에 따라 Lane 사이의 Link를 생략할 수 있다
        # => Junction 등을 생성하지 않고 CARLA에서 로드하기 위한 옵션으로, Autopliot은 동작하지 않게 된다
        # => Warning을 출력해준다.
        config_disable_lane_link = mgeo_odr_converter.MGeoToOdrDataConverter.get_instance().get_config('disable_lane_link')
        if config_disable_lane_link:
            Logger.log_warning('Link information between links is omitted by the user. It will allow CARLA to open xodr files without any junctions, but disable autopilot function at the same time. Use this option to check road geometry only.')

        current_date_iso8601 = self.current_date()
        
        xodr_root = etree.Element('OpenDRIVE')
        xodr_header = etree.SubElement(xodr_root, 'header')
        
        # version_type을 config 파일에서 직접 저장한 뒤에 불러옵니다.
        version_type_major = mgeo_odr_converter.MGeoToOdrDataConverter.get_instance().get_config('version_type').split('.')[0]
        version_type_minor = mgeo_odr_converter.MGeoToOdrDataConverter.get_instance().get_config('version_type').split('.')[1]
        xodr_header.set('revMajor', version_type_major)
        xodr_header.set('revMinor', version_type_minor)
        xodr_header.set('name', '')
        xodr_header.set('version', '1')
        xodr_header.set('date', current_date_iso8601)
        north, south, east, west = self.range_of_map()
        xodr_header.set('north', '{:.16e}'.format(north)) # FIXME(hjp): get max min range
        xodr_header.set('south', '{:.16e}'.format(south))
        xodr_header.set('east', '{:.16e}'.format(east))
        xodr_header.set('west', '{:.16e}'.format(west))
        xodr_header.set('vendor', 'MORAI')

        xodr_geo_reference = etree.SubElement(xodr_header, 'geoReference')
        xodr_geo_reference.text = etree.CDATA(self.mgeo_planner_map.global_coordinate_system)
        
        xodr_offset = etree.SubElement(xodr_header, 'offset')
        xodr_offset.set('x', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[0]))
        xodr_offset.set('y', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[1]))
        xodr_offset.set('z', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[2]))

        for _notused, road in self.roads.items():
            # flag_skip = False
            # for _lane_sec in road.get_lane_sections():
            #     for _geo in _lane_sec.geometry:
            #         if len(_geo) != 4:
            #             flag_skip = True
            # if flag_skip is True:
            #     Logger.log_warning('Road {} skipped in to_xml_string()'.format(road.road_id))
            #     continue

            # start xodr write here
            road.create_xml_string(xodr_root)
        # synced_signal_set 없을 때
        cont_id = 1
        ints = self.mgeo_planner_map.intersection_controller_set.intersection_controllers
        for controller_id in ints:
            for i, sync in enumerate(ints[controller_id].TL):
                xodr_controller = etree.SubElement(xodr_root, 'controller')
                xodr_controller.set('name', controller_id)
                xodr_controller.set('id', str(cont_id))
                cont_id += 1
                for synced_signal in sync:
                    xodr_synced_signal = etree.SubElement(xodr_controller, 'control')
                    xodr_synced_signal.set('signalId', '{}'.format(synced_signal))
                    xodr_synced_signal.set('type','0')

        # for controller, synced_signal in self.mgeo_planner_map.synced_light_set.synced_signals.items():
        #     xodr_controller = etree.SubElement(xodr_root, 'controller')
        #     xodr_controller.set('name', '{}'.format(controller))
        #     xodr_controller.set('id', '{}'.format(synced_signal.idx))
            
        #     for synced_signal in synced_signal.signal_id_list:
        #         xodr_synced_signal = etree.SubElement(xodr_controller, 'control')
        #         xodr_synced_signal.set('signalId', '{}'.format(synced_signal))
        #         xodr_synced_signal.set('type','0')
        
        for _notused, junction in self.junction_set.junctions.items():
            xodr_junction = etree.SubElement(xodr_root, 'junction')
            xodr_junction.set('name', '{}'.format(junction.idx))
            xodr_junction.set('id', '{}'.format(junction.idx))
            xodr_junction.set('type', 'default')

            for _notused, connector in junction.connecting_road.items():
                xodr_connection = etree.SubElement(xodr_junction, 'connection')
                xodr_connection.set('id', '{}'.format(connector.idx))
                xodr_connection.set('incomingRoad', '{}'.format(connector.incoming))
                xodr_connection.set('connectingRoad', '{}'.format(connector.connecting))
                xodr_connection.set('contactPoint', 'start')  # only true for @singleSide

                for lane_num in range(len(connector.from_lanes)):
                    xodr_conn_lanelink = etree.SubElement(xodr_connection, 'laneLink')
                    xodr_conn_lanelink.set('from', '{}'.format(-connector.from_lanes[lane_num]))
                    try:
                        xodr_conn_lanelink.set('to', '{}'.format(-connector.to_lanes[lane_num]))
                    except:
                        pass
        etree.indent(xodr_root, space='    ')
        str_data = etree.tostring(
            xodr_root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        )

        Logger.log_info('.xodr compile complete')  
        return str_data
    

    def write_xml_string_to_file(self, save_file_name, xml_string):
        if (save_file_name == '' or save_file_name == None):
            Logger.log_info('xodr export operation cancelled')
            return

        with open(save_file_name, 'wb') as writer:
            writer.write(xml_string)

        Logger.log_info('.xodr write to {} complete'.format(save_file_name))        
    

    def range_of_map(self):
        
        init_point = list(self.mgeo_planner_map.node_set.nodes.values())[0].point
        north_candidate = init_point
        south_candidate = init_point
        east_candidate = init_point
        west_candidate = init_point

        for node in self.mgeo_planner_map.node_set.nodes.values():
            
            if node.point[1] > north_candidate[1]:
                north_candidate = node.point
            elif node.point[1] < south_candidate[1]:
                south_candidate = node.point
            if node.point[0] > east_candidate[0]:
                east_candidate = node.point
            elif node.point[0] < west_candidate[0]:
                west_candidate = node.point
        
        vertical_range = north_candidate[1] - south_candidate[1]
        horizental_range =  east_candidate[0] - west_candidate[0]

        north_point = north_candidate + np.array([0, vertical_range*0.1, 0])
        south_point = south_candidate -  np.array([0, vertical_range*0.1, 0])
        east_point = east_candidate + np.array([horizental_range*0.1, 0, 0])
        west_point = west_candidate - np.array([horizental_range*0.1, 0, 0])
        
        proj = self.mgeo_planner_map.global_coordinate_system
        new_proj = ' '.join(s for s in proj.split() if not s.startswith('+geoidgrids') and not s.startswith('+vunits'))
        p = Proj(new_proj)
        offset = self.mgeo_planner_map.local_origin_in_global
        
        
        x, y, z  = north_point + offset
        north_lons, north_lats = p(x, y, inverse = True)

        x, y, z  = south_point + offset
        south_lons, south_lats = p(x, y, inverse = True)

        x, y, z  = east_point + offset
        east_lons, east_lats = p(x, y, inverse = True)

        x, y, z  = west_point + offset
        west_lons, west_lats = p(x, y, inverse = True)

        return north_lats, south_lats, east_lons, west_lons

    def to_xml_string_apollo(self):
        
        current_date_iso8601 = self.current_date()
        
        xodr_root = etree.Element('OpenDRIVE')
        xodr_header = etree.SubElement(xodr_root, 'header')
        
        xodr_header.set('revMajor', '5')
        xodr_header.set('revMinor', '0')
        xodr_header.set('name', '')
        xodr_header.set('version', '1')
        xodr_header.set('date', current_date_iso8601)
        north, south, east, west = self.range_of_map()
        xodr_header.set('north', '{:.16e}'.format(north)) # FIXME(hjp): get max min range
        xodr_header.set('south', '{:.16e}'.format(south))
        xodr_header.set('east', '{:.16e}'.format(east))
        xodr_header.set('west', '{:.16e}'.format(west))
        xodr_header.set('vendor', 'MORAI')

        xodr_geo_reference = etree.SubElement(xodr_header, 'geoReference')
        xodr_geo_reference.text = etree.CDATA('+proj=longlat +datum=WGS84 +no_defs')
        
        # xodr_offset = etree.SubElement(xodr_header, 'offset')
        # xodr_offset.set('x', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[0]))
        # xodr_offset.set('y', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[1]))
        # xodr_offset.set('z', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[2]))

        for _notused, road in self.roads.items():
            road.create_xml_string_apollo(xodr_root, self.mgeo_planner_map)
        
        # for controller, synced_signal in self.mgeo_planner_map.synced_light_set.synced_signals.items():
        #     xodr_controller = etree.SubElement(xodr_root, 'controller')
        #     xodr_controller.set('name', '{}'.format(controller))
        #     xodr_controller.set('id', '{}'.format(synced_signal.idx))
            
        #     for synced_signal in synced_signal.signal_id_list:
        #         xodr_synced_signal = etree.SubElement(xodr_controller, 'control')
        #         xodr_synced_signal.set('signalId', '{}'.format(synced_signal))
        #         xodr_synced_signal.set('type','0')
        
        for _notused, junction in self.junction_set.junctions.items():
            xodr_junction = etree.SubElement(xodr_root, 'junction')
            xodr_junction.set('id', '{}'.format(junction.idx))
            xodr_junction.set('name', '{}'.format(junction.idx))
            
           

            for _notused, connector in junction.connecting_road.items():
                xodr_connection = etree.SubElement(xodr_junction, 'connection')
                xodr_connection.set('id', '{}'.format(connector.idx))
                xodr_connection.set('incomingRoad', '{}'.format(connector.incoming))
                xodr_connection.set('connectingRoad', '{}'.format(connector.connecting))
                xodr_connection.set('contactPoint', 'start')  # only true for @singleSide

                for lane_num in range(len(connector.from_lanes)):
                    xodr_conn_lanelink = etree.SubElement(xodr_connection, 'laneLink')
                    from_ego_lane = connector.from_lanes[lane_num]
                    if from_ego_lane >90:
                        from_ego_lane = 1
                    xodr_conn_lanelink.set('from', '{}'.format(-from_ego_lane))

                for lane_num in range(len(connector.to_lanes)):
                    xodr_conn_lanelink = etree.SubElement(xodr_connection, 'laneLink')
                    to_ego_lane = connector.to_lanes[lane_num]
                    if to_ego_lane >90:
                        to_ego_lane = 1
                    xodr_conn_lanelink.set('to', '{}'.format(-to_ego_lane))
                  
            apollo_objectOverlapGroup = etree.SubElement(xodr_junction, 'objectOverlapGroup')
            apollo_outline = etree.SubElement(xodr_junction, 'outline')
            outline_list = []
            if len(junction.connecting_road)>5:
                outline_lane_mark_set = []
                for road_id in junction.connecting_road.keys():
                    road = self.roads[road_id]
                    # junction 의 from road 는 하나뿐이라고 가정
                    if road.get_from_roads()[0].get_frontmost_right().lane_mark_right[0].to_node.to_links[0] !=[]:
                        outline_lane_mark = road.get_from_roads()[0].get_frontmost_right().lane_mark_right[0].to_node.to_links[0]
                    else:
                        outline_lane_mark = road.get_from_roads()[0].get_frontmost_right().lane_mark_right[0]
                    
                    outline_lane_mark_set.append(outline_lane_mark)

                outline_lane_mark_set = list(set(outline_lane_mark_set))
                outline_lane_mark_point_set = []
                
                for lane_mark in outline_lane_mark_set:
                    
                    for point in lane_mark.points:
                        outline_lane_mark_point_set.append(point)
                
                #outline_list = outline_lane_mark_point_set + [node.point for node in junction.jc_nodes]
                
                outline_list = [node.point for node in junction.jc_nodes]
                
                outline_list_xy = [node.point[0:2] for node in junction.jc_nodes]
                hull = ConvexHull(outline_list_xy)
                outline_list_sorted = []
                for idx in hull.vertices:
                    outline_list_sorted.append(outline_list[idx])

            elif len(junction.connecting_road)==2:
                outline_lane_mark_set = []
                for road_id in junction.connecting_road.keys():
                    road = self.roads[road_id]
                    outline_lane_mark_left = road.get_frontmost_right().lane_mark_right[0] 
                    outline_lane_mark_right = road.get_frontmost_left().lane_mark_right[0]
                    outline_lane_mark_set.append(outline_lane_mark_left)
                    outline_lane_mark_set.append(outline_lane_mark_right)
                
                outline_lane_mark_point_set = []
                
                for lane_mark in outline_lane_mark_set:
                    
                    for point in lane_mark.points:
                        outline_lane_mark_point_set.append(point)

                outline_list = outline_lane_mark_point_set + [node.point for node in junction.jc_nodes]
                outline_list =  [node.point for node in junction.jc_nodes]
            else:
                outline_list = [node.point for node in junction.jc_nodes]
            #elif len(junction.connecting_road)==3:

            outline_list = [node.point for node in junction.jc_nodes]
                
            outline_list_xy = [node.point[0:2] for node in junction.jc_nodes]
            hull = ConvexHull(outline_list_xy)
            outline_list_sorted = []
            for idx in hull.vertices:
                outline_list_sorted.append(outline_list[idx])
            
            for point in outline_list_sorted:
                
                proj = self.mgeo_planner_map.global_coordinate_system
                p = Proj(proj)
                offset = self.mgeo_planner_map.local_origin_in_global
                x, y, z  = point + offset
                lons, lats = p(x, y, inverse = True)
                apollo_outline_point = etree.SubElement(apollo_outline, 'cornerGlobal')
                apollo_outline_point.set('x', '{}'.format(format(lons,"e")))
                apollo_outline_point.set('y', '{}'.format(format(lats,"e")))
                apollo_outline_point.set('z', '{}'.format(format(z,"e")))

        etree.indent(xodr_root, space='    ')
        str_data = etree.tostring(
            xodr_root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        )

        Logger.log_info('.xodr compile complete')  
        return str_data