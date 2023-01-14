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

import lxml.etree as etree
import datetime


class OdrData:
    """
    OdrData
    """
    def __init__(self):
        self.roads = dict()
        self.junction_set = None
        self.mgeo_planner_map = None

    def append_road_to_data(self, road):
        road.parent_odr_data = self
        self.roads[road.road_id] = road

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
        # DEPRECATED
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
        xodr_header.set('revMajor', '1')
        xodr_header.set('revMinor', '6')
        xodr_header.set('name', '')
        xodr_header.set('version', '')
        xodr_header.set('date', current_date_iso8601)
        xodr_header.set('north', '{:.16e}'.format(0))
        xodr_header.set('south', '{:.16e}'.format(0))
        xodr_header.set('east', '{:.16e}'.format(0))
        xodr_header.set('west', '{:.16e}'.format(0))
        xodr_header.set('vendor', 'MORAI')

        xodr_geo_reference = etree.SubElement(xodr_header, 'geoReference')
        xodr_geo_reference.text = etree.CDATA(self.mgeo_planner_map.global_coordinate_system)
        
        xodr_offset = etree.SubElement(xodr_header, 'offset')
        xodr_offset.set('x', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[0]))
        xodr_offset.set('y', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[1]))
        xodr_offset.set('z', '{:.16e}'.format(self.mgeo_planner_map.local_origin_in_global[2]))

        for _notused, road in self.roads.items():
            # start xodr write here
            road.create_xml_string(xodr_root)

        for _notused, junction in self.mgeo_planner_map.junction_set.junctions.items():
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
                    xodr_conn_lanelink.set('from', '{}'.format(connector.from_lanes[lane_num]))
                    xodr_conn_lanelink.set('to', '{}'.format(connector.to_lanes[lane_num]))

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
        