import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/common/')))


from mgeo_odr_converter import MGeoToOdrDataConverter
from shp_common import *
import shapefile

import numpy as np

from lib.mgeo.class_defs import *
import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save

from lib.mgeo.utils import lane_change_link_creation

import nose2
from nose2.tools import params
from nose2.tests._common import TestCase

testcase01 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_01'))
testcase02 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_02'))
testcase03 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_03'))
testcase03_2 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_03_2'))
testcase04 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_04'))
testcase05 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_05'))
testcase06 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_06'))
testcase08 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_08'))
testcase08_2 = os.path.normpath(os.path.join(current_path, '../../../saved/lane_change_test_file/test_08_2'))


class TestCreateLaneChange(TestCase):

    # @params(testcase01, testcase02, testcase03, testcase03_2, testcase04, testcase05, testcase06)
    @params(testcase08, testcase08_2)
    def test_create_lane_change(self, input_path):
        """폴더 경로"""
        
        print()
        print(input_path)
        test_mgeo_data = MGeo.create_instance_from_json(input_path + '/before')
        standard_mgeo_data = MGeo.create_instance_from_json(input_path + '/after')

        node_set = test_mgeo_data.node_set
        link_set = test_mgeo_data.link_set

        count_duplicated_link = []

        for node in node_set.nodes:
            if len(node_set.nodes[node].to_links) > 1:
                for i in node_set.nodes[node].to_links:
                    count_duplicated_link.append(i.idx)
            if len(node_set.nodes[node].from_links) > 1:
                for i in node_set.nodes[node].from_links:
                    count_duplicated_link.append(i.idx)

        # print(count_duplicated_link)

        # 차선 변경 데이터 만들기
        lane_ch_link_set = lane_change_link_creation.create_lane_change_link_auto_depth_using_length(
                link_set, method=1, min_length_for_lane_change=20)

        link_set = LineSet.merge_two_sets(link_set, lane_ch_link_set)
        test_mgeo_data.link_set = link_set

        test_node_set = test_mgeo_data.node_set.nodes
        test_du_set = []
        for idx, node in test_node_set.items():
            to_links = node.to_links
            if len(to_links) > 0:
                for link in to_links:
                    this_to_node = link.to_node.idx
                    com_to_node = next((item for item in to_links if item.to_node.idx == this_to_node), False)
                    if com_to_node and link.idx != com_to_node.idx:
                        test_du_set.append([link.idx, com_to_node.idx])
        
        standard_node_set = standard_mgeo_data.node_set.nodes
        standard_du_set = []
        for idx, node in standard_node_set.items():
            to_links = node.to_links
            if len(to_links) > 0:
                for link in to_links:
                    this_to_node = link.to_node.idx
                    com_to_node = next((item for item in to_links if item.to_node.idx == this_to_node), False)
                    if com_to_node and link.idx != com_to_node.idx:
                        standard_du_set.append([link.idx, com_to_node.idx])

        print('test - standard(더 생긴 것): ', [x for x in test_du_set if x not in standard_du_set])
        print('standard - test(덜 생긴 것): ', [x for x in standard_du_set if x not in test_du_set])

if __name__ == '__main__':
    nose2.main()