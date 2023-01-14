"""
Author: MORAI.Inc
"""

from coord_trans_tm2ll import CoordTrans_TM2LL
import numpy as np

import lxml.etree as etree

class CoordTrans_CARLA2LLH:
    def __init__(self):
        self.tm2ll_obj = CoordTrans_TM2LL()
        self.local_origin_in_tm = np.array([0.0, 0.0, 0.0])

    def set_params_from_xodr_file(self, file_path):
        # parse xml file
        tree = etree.parse(file_path)
        root = tree.getroot()
        
        proj_str = root.xpath('//header/geoReference')[0].text
        proj_item_list = proj_str.split('+')
        proj_item_dict = dict()
        for proj_item in proj_item_list :
            if proj_item and len(proj_item.split('=')) == 2 :
                proj_item_split = proj_item.split('=')
                proj_item_dict[proj_item_split[0]] = proj_item_split[1].replace(' ', '')

        spheroid = proj_item_dict['ellps']        
        latitude_of_origin = float(proj_item_dict['lat_0'])   
        central_meridian = float(proj_item_dict['lon_0'])
        scale_factor = float(proj_item_dict['k'])   
        false_easting = int(proj_item_dict['x_0'])
        false_northing = int(proj_item_dict['y_0'])
        
        offset = root.xpath('//header/offset')[0]
        local_origin_in_tm = np.array([float(offset.attrib['x']), float(offset.attrib['y']), float(offset.attrib['z'])])

        self.set_params(
            local_origin_in_tm,
            spheroid,
            latitude_of_origin,
            central_meridian,
            scale_factor,
            false_easting, 
            false_northing
        )

    def set_params(self,
        local_origin_in_tm,
        spheroid, 
        latitude_of_origin, central_meridian,
        scale_factor,
        false_easting, false_northing):

        self.local_origin_in_tm = np.array(local_origin_in_tm)
        
        self.tm2ll_obj.set_tm_params(
            spheroid, 
            latitude_of_origin, central_meridian, 
            scale_factor,
            false_easting, false_northing)
        
    def carla_to_llh(self, carla_pos):
        # carla pos -> local TM
        # NOTE: TM 좌표계의 높이는 ellipsoidal height 이어야만 한다.
        # (geoid height를 고려한, orthometric height로의 conversion은 지원되지 않음)
        local_tm_pos = np.array([carla_pos[0], -1 * carla_pos[1], carla_pos[2]])

        # local TM -> TM
        global_tm_pos = self.local_origin_in_tm + local_tm_pos

        # TM -> LLH
        ll = self.tm2ll_obj.tm2ll(east=global_tm_pos[0], north=global_tm_pos[1])

        return [ll[0], ll[1], global_tm_pos[2]]


if __name__ == '__main__':
    import os
    import sys
    current_path = os.path.dirname(os.path.realpath(__file__))
    xodr_file_name = os.path.normpath(os.path.join(current_path, 'test_xodr_file_kcity.xodr'))

    coord_trans = CoordTrans_CARLA2LLH()

    coord_trans.set_params_from_xodr_file(xodr_file_name)

    # coord_trans.set_params(
    #     local_origin_in_tm=np.array([9.3516487166160834e+05, 1.9147363928760968e+06, 2.9184038301929832e+01]),
    #     spheroid='GRS80',
    #     latitude_of_origin=38.0,
    #     central_meridian=127.5,
    #     scale_factor=0.9996,
    #     false_easting=1000000,
    #     false_northing=2000000)   

    llh = coord_trans.carla_to_llh(np.array([385.7, -1143.1, 0.0]))

    print('llh = [{:.6f}, {:.6f}, {:.6f}]'.format(llh[0], llh[1], llh[2]))