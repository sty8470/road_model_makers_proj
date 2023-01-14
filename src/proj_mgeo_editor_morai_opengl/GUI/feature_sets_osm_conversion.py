import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import lxml.etree as etree

from lib.common.logger import Logger

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from lib.mgeo.class_defs import *
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction, edit_mgeo_planner_map
from lib.mgeo.utils import error_fix

from mgeo_lanelet_manager import MgeoToLanenetDataManager

from GUI.feature_sets_base import BaseFeatureSet


class OsmConversion(BaseFeatureSet):
    """
    osm은 node가 위치를 기반이로 지도에 표시되어 있다.
    node는 여러 가지 정보를 담을 수 있다.

    도로는 node를 진행 방향 순으로 연결하고 way로 묶으면 표현할 수 있다.

    mgeo link의 시작포인트는 node이고 진행 방향을 points로 가지고 있다.

    동일한 데이터로 변경하려면 mgeo link를 osm way로 대치하여야 한다.

    """

    def __init__(self, canvas):
        super(OsmConversion, self).__init__(canvas)

        self.lanelet_manager = MgeoToLanenetDataManager.get_instance()
        

    def initData(self, save_file_path):
        Logger.log_trace('OsmConverter::start convert')
        '''
        self.save_path = save_file_path

        mgeo_planner_map = self.canvas.mgeo_planner_map

        self.lanelet_manager.init_node_id(mgeo_planner_map)

        # xml 생성.
        self.createXMLFile() 
        '''
        # 저장경로.
        self.save_path = save_file_path
        mgeo_planner_map = self.canvas.mgeo_planner_map
        # 데이터 변환.
        self.lanelet_manager.start_convert(mgeo_planner_map)
        # xml 구성.
        self.createOsmFile()

    def createOsmFile(self) :
        root = etree.Element('osm')
        root.set("generator", "MORAI Inc")
        root.set("version", "0.6")              # osm api가 v0.6까지 최신.
        
        self.createOsmNode(root)
        self.createOsmWay(root)
        self.createOsmLanelet(root)
        

        
        tree = etree.ElementTree(root)
        tree.write(self.save_path, encoding="UTF-8", xml_declaration=True)

        Logger.log_trace('OsmConverter::Finished')
    
    
    def createOsmNode(self, root_element) :
        node_list = self.lanelet_manager.osm_node_list

        for nd in node_list :
            nd.createXmlElement(root_element)

    def createOsmWay(self, root_element) :
        way_dic = self.lanelet_manager.osm_way_dic

        for w_k, w_v in way_dic.items() :
            w_v.createXmlElement(root_element)

    def createOsmLanelet(self, root_element) :
        lanelet_list = self.lanelet_manager.osm_lanelet_list

        for lanlet_obj in lanelet_list :
            lanlet_obj.createXmlElement(root_element)

 