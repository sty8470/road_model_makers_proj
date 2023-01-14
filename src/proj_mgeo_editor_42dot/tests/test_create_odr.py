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

import nose2
from nose2.tests._common import TestCase

input_path = os.path.normpath(os.path.join(current_path, '../../../saved/42dot_kcity_maps_release/201112_PM1117_KCity_Trimmed_Z0'))

class TestCreateOdr(TestCase):

    def test_output_odr(self):
        """폴더 경로"""
        mgeo_data = MGeo.create_instance_from_json(input_path)

        converter = MGeoToOdrDataConverter.get_instance()
        config = {}
        config['include_signal'] = True
        config['fix_signal_road_id'] = False
        config['disable_lane_link'] = False

        converter.set_config_all(config)
        odr_data = converter.convert(mgeo_data)

        xml_string = odr_data.to_xml_string()
        odr_data.write_xml_string_to_file('test_odr.xodr', xml_string)
        

if __name__ == '__main__':
    nose2.main()