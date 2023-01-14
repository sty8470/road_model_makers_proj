import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/common/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib_ngii_shp_ver2/')))


from lib.lib_42dot.hdmap_42dot_importer import HDMap42dotImporter
from shp_common import *
import shapefile

import numpy as np
import matplotlib.pyplot as plt
from tkinter import filedialog

from lib_ngii_shp_ver2.shp_edit_funcs import UserInput, scr_zoom, create_link_editor
from lib.mgeo.class_defs import *
import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save


def load_shp():
    """CODE42 정밀지도 데이터가 SHP포맷으로만 되어있을 때 import 하는 코드"""
    input_path = '../../rsc/map_data/code42_shp_yangjae/'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)   

    output_path = '../../saved/'
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    importer = HDMap42dotImporter()
    mgeo_planner_map = importer.import_shp(input_path)
    mgeo_planner_map.to_json(output_path)


def load_shp_geojson():
    """CODE42 정밀지도 데이터 중 node, link는 SHP포맷으로 되어있고, signal은 geojson으로 되어있을 때 사용하는 코드"""
    input_path = '../../rsc/map_data/code42_shp_yangjae/'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)   

    output_path = '../../saved/'
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    importer = HDMap42dotImporter()
    mgeo_planner_map = importer.import_shp_geojson(input_path)
    mgeo_planner_map.to_json(output_path)


if __name__ == u'__main__':
    #load_shp()
    load_shp_geojson()