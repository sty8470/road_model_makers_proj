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
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction, edit_mgeo_planner_map
from lib.mgeo.utils import error_fix
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


class TestUILoad(TestCase):
    
    app = QtWidgets.QApplication(sys.argv)
    opengl_canvas = OpenGLCanvas()

    def set_up_mgeo(self, value):
        mgeo_planner_map = MGeo.create_instance_from_json(value)
        print("create mgeo planner map")
        self.opengl_canvas.setMGeoPlannerMap(mgeo_planner_map)

    def test_delete_items(self):
        self.set_up_mgeo(input_path)
        sp_type = MGeoItem.LINK
        sp_list = []
        lines = self.opengl_canvas.getLinkSet().lines
        for i, line in enumerate(lines):
            if i == 3:
                break
            sp_list.append({'type': sp_type, 'id': line})
        # 메세지 박스
        self.opengl_canvas.delete_item(sp_list)
        print("delete links", sp_list)

    def test_delete_item(self):
        self.set_up_mgeo(input_path)
        sp_type = MGeoItem.LINK
        sp_list = []
        lines = self.opengl_canvas.getLinkSet().lines
        for i, line in enumerate(lines):
            if i == 1:
                break
            sp_list.append({'type': sp_type, 'id': line})
        # 메세지 박스
        self.opengl_canvas.delete_item(sp_list)
        print("delete link", sp_list)

    def test_delete_xy_range(self):
        self.set_up_mgeo(input_path)
        edit_mgeo_planner_map.delete_object_inside_xy_range(self.opengl_canvas.mgeo_planner_map, [0, 100], [0, 100])
        print("Delete objects inside the range, x = [0, 100], y = [0, 100]")

    # def test_edit_item_date(self):
    #     self.set_up_mgeo(input_path)
    #     qTreeWidget = QTreeWidget()
    #     qTreeWidget.setColumnCount(3)
    #     qTreeWidget.setHeaderLabels(["Properties", "Type", "Value"])
    #     self.opengl_canvas.tree_attr = qTreeWidget
        
        

if __name__ == '__main__':
    nose2.main()