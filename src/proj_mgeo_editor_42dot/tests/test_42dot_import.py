import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/common/')))


from lib.lib_42dot.hdmap_42dot_importer import HDMap42dotImporter
from shp_common import *
import shapefile

import numpy as np

from lib.mgeo.class_defs import *

import nose2
from nose2.tools import params
from nose2.tests._common import TestCase

folder_path = os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae'))

file_list = [
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/link.dbf')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/link.prj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/link.prj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/link.shp')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/link.shx')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/node.dbf')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/node.prj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/node.shp')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/node.shx')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/traffic_sign.geojson')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/traffic_signal.geojson')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGN_POINT.cpg')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGN_POINT.dbf')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGN_POINT.prj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGN_POINT.qpj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGN_POINT.shp')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGN_POINT.shx')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGNAL_POINT.cpg')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGNAL_POINT.dbf')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGNAL_POINT.prj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGNAL_POINT.qpj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGNAL_POINT.shp')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B1_SIGNAL_POINT.shx')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_PLANE.cpg')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_PLANE.dbf')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_PLANE.prj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_PLANE.qpj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_PLANE.shp')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_PLANE.shx')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_POINT.cpg')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_POINT.dbf')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_POINT.prj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_POINT.qpj')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_POINT.shp')),
    os.path.normpath(os.path.join(current_path, '../../../rsc/map_data/42dot_mdl2009_yangjae/yangjae_B2_SURFSIGN_POINT.shx'))]

output_path = os.path.normpath(os.path.join(current_path, '../../../saved/test_42dot_save'))
if not os.path.isdir(output_path):
    os.mkdir(output_path)

# 일반적인 unittest 스타일로 작성된 간단한 테스트 코드
class Test42DotImport(TestCase):

    def setUp(self):
        self.loader = HDMap42dotImporter()

    @params(folder_path, file_list)
    def test_import_shp(self, value):
        mgeo_planner_map = self.loader.import_shp_geojson(value)
        mgeo_planner_map.to_json(output_path)


    # def test_load_shp(self):
    #     """폴더 경로"""
    #     input_path = folder_path

    #     importer = HDMap42dotImporter()
    #     mgeo_planner_map = importer.import_shp_geojson(input_path)
    #     mgeo_planner_map.to_json(output_path)


    # def test_load_shp_geojson(self):
    #     input_path = file_list

    #     importer = HDMap42dotImporter()
    #     mgeo_planner_map = importer.import_shp_geojson(input_path)
    #     mgeo_planner_map.to_json(output_path)


if __name__ == '__main__':
    nose2.main()