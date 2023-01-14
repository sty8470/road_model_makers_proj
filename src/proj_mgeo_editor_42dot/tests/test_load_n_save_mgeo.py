import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/common/')))

import numpy as np

from lib.mgeo.class_defs import *
from lib.mgeo.class_defs.mgeo import MGeo

from GUI.opengl_canvas import OpenGLCanvas
from GUI.feature_sets_error_fix import ErrorFix

import nose2
from nose2.tools import params
from nose2.tests._common import TestCase

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

input_path = os.path.normpath(os.path.join(current_path, '../../../saved/42dot_kcity_maps_release/201112_PM1117_KCity_Trimmed_Z0'))
input_file_mprj = os.path.normpath(os.path.join(current_path, '../../../saved/42dot_kcity_maps_release/load_mgeo_mprj/global_info.mprj'))
input_file_json = os.path.normpath(os.path.join(current_path, '../../../saved/42dot_kcity_maps_release/201112_PM1117_KCity_Trimmed_Z0/global_info.json'))
output_path = os.path.normpath(os.path.join(current_path, '../../../saved/save_mgeo'))
if not os.path.isdir(output_path):
    os.mkdir(output_path)


class TestLoadSave(TestCase):

    @params(input_path, input_file_mprj, input_file_json)
    def test_load_n_save_mgeo(self, value):
        mgeo_planner_map = MGeo.create_instance_from_json(value)
        print("create mgeo planner map")
        mgeo_planner_map.to_json(output_path)


if __name__ == '__main__':
    
    nose2.main()