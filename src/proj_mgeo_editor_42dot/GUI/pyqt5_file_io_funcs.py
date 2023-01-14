import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger
import lib.common.path_utils as path_utils

import json
import traceback

# from lib.mgeo.class_defs.mgeo_planner_map import MGeo
from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.edit.funcs import edit_mgeo_planner_map

from lib.fourtytwodot.hdmap_42dot_importer import HDMap42dotImporter

from GUI.opengl_canvas import OpenGLCanvas

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class FileIOFuncs:
    def __init__(self, canvas):
        self.canvas = canvas
        self.mgeo_planner_map = None

        self.config = None
        self.config_file_path = None
        self.program_root_dir = None

        self.auto_select_file = None

    def get_path_from_config(self, key):
        if self.config is None:
            raise BaseException('Error in the initialization of this class: self.config is None')
        
        if self.config_file_path is None:
            raise BaseException('Error in the initialization of this class: self.config_file_path is None')
            
        if self.program_root_dir is None:
            raise BaseException('Error in the initialization of this class: self.program_root_dir is None')

        if key not in self.config.keys():
            raise BaseException('Error in the config file ({}): key: {} is missing'.format(self.config_file_path, key))
    
        path_in_config = self.config[key]
        if not os.path.isabs(path_in_config):
            path_in_config = os.path.normpath(os.path.join(self.program_root_dir, path_in_config))

        result, valid_path = path_utils.get_valid_parent_path(path_in_config)

        # 디버그 모드에서 테스트용 >> 존재하지 않을 경로를 넣어서 확인
        # test_dir ='k:\\test\\'
        # result, valid_path = path_utils.get_valid_parent_path(test_dir)
        
        if not result:
            Logger.log_warning('Since there is no valid path for key: {}, program root dir: {} will be used instead.'.format(key, self.program_root_dir))
            return self.program_root_dir
        else:
            return valid_path


    def update_config(self, key, new_value):
        if self.config is None:
            raise BaseException('Error in the initialization of this class: self.config is None')
        
        if self.config_file_path is None:
            raise BaseException('Error in the initialization of this class: self.config_file_path is None')
            
        if self.program_root_dir is None:
            raise BaseException('Error in the initialization of this class: self.program_root_dir is None')

        if key not in self.config.keys():
            raise BaseException('Error in the config file ({}): key: {} is missing'.format(self.config_file_path, key))

        with open(self.config_file_path, 'w') as f:
            self.config[key] = new_value
            json.dump(self.config, f, indent=4)


    def import_42dot(self, import_action_list, use_legacy=False):
        try:
            init_import_path = self.get_path_from_config('42dot_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            # HDMap 데이터에서 원하는 파일(선택)만 가져올 수 있게
            input_path = QFileDialog.getOpenFileNames(
                self.canvas, 
                'Select a folder that contains 42dot HDMap data', 
                init_import_path, 
                'All Files (*)')[0]

            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import 42dot HDMap data from: {}'.format(input_path))

            importer = HDMap42dotImporter()
            if use_legacy:
                self.mgeo_planner_map = importer.import_shp_geojson_legacy(input_path)
            else:
                self.mgeo_planner_map = importer.import_shp_geojson(input_path)

            self.canvas.setMGeoPlannerMap(self.mgeo_planner_map)
            self.canvas.resetCamera()

            # node data 유/무에 따라 (find_overlapped_node, find_dangling_nodes) menu action enable
            if self.mgeo_planner_map.node_set is not None:
                for i in import_action_list:
                    i.setDisabled(False)
            else:
                for i in import_action_list:
                    i.setDisabled(True)
                
            # import한 데이터 내용 추가
            self.canvas.updateTreeWidget()
            
            # 실제 import한 경로보다 한 경로 위를 저장
            if type(input_path) == list:
                input_path = os.path.dirname(input_path[0])
            self.update_config('42dot_MAP_IMPORT', os.path.normpath(os.path.join(input_path, '../')))
            Logger.log_info("42dot HDMap data successfully loaded from: {}".format(input_path))

        except BaseException as e:
            Logger.log_error('import_42dot failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def save_mgeo(self):
        try:
            init_save_path = self.get_path_from_config('MGEO_SAVE')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_path = QFileDialog.getExistingDirectory(self.canvas, 'Select a folder to save MGeo data into', 
                        init_save_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

            if save_path == '' or save_path == None:
                Logger.log_error('invalid save_path (your input: {})'.format(save_path))
                return

            Logger.log_trace('save MGeo data into: {}'.format(save_path))

            # traffic_sign_set.json 및 traffic_light_set.json 파일 저장
            self.mgeo_planner_map.to_json(save_path)

            # 실제 save한 경로보다 한 경로 위를 저장
            self.update_config('MGEO_SAVE', os.path.normpath(os.path.join(save_path, '../')))
            Logger.log_info("Successfully MGeo data is saved into: {}".format(save_path))

        except BaseException as e:
            Logger.log_error('save_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def load_mgeo(self, import_action_list):
        try:
            init_load_path = self.get_path_from_config('MGEO_LOAD')
            Logger.log_trace('init_load_path: {}'.format(init_load_path))

            # global_info.mprj 파일 선택할 수 있게 설정
            # load_path = QFileDialog.getOpenFileName(
            #     self.canvas, 
            #     caption='Select a folder that contains MGeo Project File', 
            #     directory=init_load_path,
            #     filter='Mgeo project file (*.mprj);; All File (*.*)')[0]

            load_path = QFileDialog.getExistingDirectory(
                self.canvas,
                'Select a folder that contains MGeo project files',
                init_load_path,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

            if (load_path == '' or load_path == None):
                Logger.log_error('invalid load_path (your input: {})'.format(load_path))
                return

            Logger.log_trace('load MGeo data from: {}'.format(load_path))

            self.mgeo_planner_map = MGeo.create_instance_from_json(load_path)
           
            self.canvas.setMGeoPlannerMap(self.mgeo_planner_map)
            self.canvas.resetCamera()

            # node data 유/무에 따라 (find_overlapped_node, find_dangling_nodes) menu action enable
            if self.mgeo_planner_map.node_set is not None:
                for i in import_action_list:
                    i.setDisabled(False)
            else:
                for i in import_action_list:
                    i.setDisabled(True)
                
            # import한 데이터 내용 추가
            self.canvas.updateTreeWidget()

            # 실제 load한 경로보다 한 경로 위를 저장
            self.update_config('MGEO_LOAD', os.path.normpath(os.path.join(load_path, '../')))
            Logger.log_info("MGeo data successfully loaded from: {}".format(load_path))

        except BaseException as e:
            Logger.log_error('load_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def export_odr(self):
        try:
            init_save_path = self.get_path_from_config('EXPORT_ODR')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_file_name = QFileDialog.getSaveFileName(
                self.canvas, 
                caption='Save OpenDRIVE file as', 
                directory=init_save_path, 
                initialFilter='.xodr', 
                filter='OpenDRIVE (*.xodr)' )[0]
        

            if (save_file_name == '' or save_file_name == None):
                Logger.log_error('invalid save_file_name (your input: {})'.format(save_file_name))
                return
                
            Logger.log_trace('save xodr file as {}'.format(save_file_name))

            # STEP #3: Write into an xodr file
            xml_string = self.canvas.odr_data.to_xml_string()
            self.canvas.odr_data.write_xml_string_to_file(save_file_name, xml_string)

            # export한 경로를 저장
            export_path = os.path.dirname(save_file_name)
            self.update_config('EXPORT_ODR', export_path)
        
        except BaseException as e:
            Logger.log_error('export_odr failed (traceback is down below) \n{}'.format(traceback.format_exc()))
    
    def merge_mgeo(self, import_action_list):
        len_node = len(self.canvas.mgeo_planner_map.node_set.nodes)
        if len_node == 0:
            Logger.log_info("load_mgeo")
            self.load_mgeo(import_action_list)
        else:
            try:
                init_load_path = self.get_path_from_config('MGEO_LOAD')
                Logger.log_trace('init_load_path: {}'.format(init_load_path))

                # global_info.mprj 파일 선택할 수 있게 설정
                load_path = QFileDialog.getOpenFileName(
                    self.canvas, 
                    caption='Select a folder that contains MGeo Project File', 
                    directory=init_load_path,
                    filter='Mgeo project file (*.mprj);; All File (*.*)')[0]
                            
                load_path = os.path.dirname(load_path)   
                
                if (load_path == '' or load_path == None):
                    Logger.log_error('invalid load_path (your input: {})'.format(load_path))
                    return

                Logger.log_trace('load MGeo data from: {}'.format(load_path))

                merge_mgeo = MGeo.create_instance_from_json(load_path)
                new_origin = self.canvas.mgeo_planner_map.get_origin()
                edit_mgeo_planner_map.change_origin(merge_mgeo, new_origin, retain_global_position=True)

                self.canvas.mgeo_planner_map.node_set.merge_node_set(merge_mgeo.node_set.nodes)
                self.canvas.mgeo_planner_map.link_set.merge_line_set(merge_mgeo.link_set.lines)
                self.canvas.mgeo_planner_map.light_set.merge_signal_set(merge_mgeo.light_set.signals)
                self.canvas.mgeo_planner_map.sign_set.merge_signal_set(merge_mgeo.sign_set.signals)
                self.canvas.mgeo_planner_map.junction_set.merge_junction_set(merge_mgeo.junction_set.junctions)

                self.canvas.resetCamera()

                # import한 데이터 내용 추가
                self.canvas.updateTreeWidget()

                # 실제 load한 경로보다 한 경로 위를 저장
                self.update_config('MGEO_LOAD', os.path.normpath(os.path.join(load_path, '../')))
                Logger.log_info("MGeo data successfully loaded from: {}".format(load_path))

            except BaseException as e:
                Logger.log_error('load_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))