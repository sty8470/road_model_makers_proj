import os 
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import lxml.etree as etree
from lib.opendrive.xodr_parser_element import XodrRoad, XodrJunction, XodrController

class XodrParser:
    def __init__(self, xodr_file_path):
        self.xodr_file_path = xodr_file_path
        
    def parse(self):
        if not os.path.isfile(self.xodr_file_path):
            return False

        tree = etree.parse(self.xodr_file_path)
        self.parse_geo_ref(tree)
        self.parse_header(tree)
        self.parse_road(tree)
        self.parse_junction(tree)
        self.parse_controller(tree)

        return True

    def parse_road(self, tree):
        road_list = tree.findall("road")
        self.road_data = dict()

        for road in road_list :
            self.road_data[road.attrib['id']] = XodrRoad(road)

    def parse_junction(self, tree):
        junction_list = tree.findall("junction")
        self.junction_data = dict()

        for junction in junction_list :
            self.junction_data[junction.attrib["id"]] = XodrJunction(junction)

    def parse_controller(self, tree) :
        controller_list = tree.findall("controller")
        self.controller_data = dict()

        for controller in controller_list :
            self.controller_data[controller.attrib["id"]] = XodrController(controller)

    def parse_header(self, tree) :
        header = tree.find("header")
        self.vendor = None
        if "vendor" in header.attrib :
            self.vendor = header.attrib['vendor']

    def parse_geo_ref(self, tree) :
        geo_ref = tree.find("header/geoReference")
        geo_os = tree.find('header/offset')
        self.geo_offset = None
        if geo_os is not None:
            self.geo_offset = geo_os.attrib
            
        if geo_ref == None :
            self.geo_reference = "+proj=tmerc +lat_0=0 +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +geoidgrids=egm96_15.gtx +vunits=m +no_defs"
        else : 
            self.geo_reference = geo_ref.text
