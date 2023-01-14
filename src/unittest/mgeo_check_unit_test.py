
import os
import unittest.lib.test_check_mgeo as test_check_mgeo
import sys
import pytest
import logging



logger = logging.getLogger('test')

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

 
class TestCase1():
    @pytest.fixture
    def data(self):
        input_path = os.path.abspath(os.path.join(current_path, '../../data/mgeo_data/ngii_shp2_kcity-katri/KATRI_mgeo(IntTL)_220221/'))
        mgeo = test_check_mgeo.get_mgeo_data(input_path)
        return mgeo

    def test_check_max_speed(self, data):
        assert test_check_mgeo.check_max_speed(data) == True
    
    def test_check_related_signal(self, data):
        assert test_check_mgeo.check_related_signal(data)
    
    def test_check_mgeo_item_type_def(self, data):
        assert test_check_mgeo.check_mgeo_item_type_def(data)
    
    def test_check_on_stop_line(self, data):
        assert test_check_mgeo.check_on_stop_line(data)

    def test_check_dangling(self, data):
        assert test_check_mgeo.check_dangling(data)

    def test_check_lane_change(self, data):
        assert test_check_mgeo.check_lane_change(data)
    
    def test_check_mismatch(self, data):
        assert test_check_mgeo.check_mismatch(data)
    
    def test_check_link_point_interval(self, data):
        assert test_check_mgeo.check_link_point_interval(data)

# if __name__ == '__main__':
    
#     input_path = os.path.abspath(os.path.join(current_path, '../../data/mgeo_data/ngii_shp2_kcity-katri/KATRI_mgeo(IntTL)_220221/'))
#     mgeo = test_check_mgeo.get_mgeo_data(input_path)
#     test_check_mgeo.check_max_speed(mgeo)
