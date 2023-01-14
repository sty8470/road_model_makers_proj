import os
import sys
import subprocess
from lib.command_manager.concrete_commands import FillPointsInAllLaneBoundary, SimplifyLaneBoundary
from lib.kakaomobility.kakaomobility_importer import KakaomobilityHDMapImporter

from lib.widget.select_node_type_window import SelectNodeTypeWindow
from lib.widget.select_mgeo_map import SelectMgeoMap
from proj_mgeo_editor_morai_opengl.GUI.create_road_mesh_handler import  export_lane_marking_as_csv, export_link_as_csv, export_structure_mesh
from proj_mgeo_editor_morai_opengl.mgeo_lanelet_manager import OsmConverter
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from os.path import getsize

from lib.common.logger import Logger
import lib.common.path_utils as path_utils

import json
import traceback

from lib.mgeo.class_defs.mgeo_map_planner import MgeoMapPlanners
from lib.mgeo.class_defs.mgeo import MGeo
from lib.fourtytwodot.hdmap_42dot_importer import HDMap42dotImporter
from lib.deepmap.deepmap_importer import DeepMapImporter
from lib.tomtom.tomtom_importer import TomTomImporter
from lib.civilmaps.civilmaps_importer import CivilmapsImporter
from lib.mobiltech.mobiltech_importer import MobiltechImporter

from lib.mscenario.class_defs.mscenario import MScenario
from lib.stryx.stryx_hdmap_importer import StryxHDMapImporter
from lib.naver.naver_hdmap_importer import NaverHDMapImporter

# NGII Library
from lib_ngii_shp1 import ngii_shp1_to_mgeo
from lib_ngii_shp_ver2 import ngii_shp2_to_mgeo, morai_sim_build_data_exporter
# from proj_kaist_geojson.road_sejong import load_road
from lib.roadrunner.roadrunner_geojson_importer import RoadrunnerImporter

from lib.widget.edit_world_projection_window import EditWorldProjectionWindow
from lib.widget.edit_world_origin_latlon_window import EditWorldOriginLatLonWindow
from lib.widget.opendrive_import_window import OpenDriveImportWindow
from lib.opendrive.xodr_converter import XodrConverter

# RAD-R
from lib.hyundai_autoever.hdmap_importer import AutoEverImporter

from GUI.opengl_canvas import OpenGLCanvas

from GUI.txt_data import import_txt_data, import_geojson_data, import_modelling_line_shp_file

from GUI.create_road_mesh_handler import SelectExportLaneWindow, simplify_lane_markings, fill_points_in_lane_markings
from GUI.create_road_mesh_handler import export_traffic_light_csv, export_traffic_sign_csv, export_surface_mark, export_road_mesh, export_lane_mesh
from lib.geojson.export_geojson import mgeo_to_geojson
from lib.geojson.import_geojson import mGeoGeojsonImporter
from lib.mgeo.edit.funcs import edit_road_poly

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from lib.openscenario.open_scenario_importer import OpenScenarioImporter
from lib.widget.create_new_open_scenario import NewOpenScenarioUI
#from lib.command_manager.command_receiver import MGeoReceiver
#from lib.command_manager.command_manager import CommandManager
#from lib.command_manager.concrete_commands import *


class LoadMgeoWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            self.mgeo_planner_map = MGeo.create_instance_from_json(self.input_path)
            self.check_result = self.mgeo_planner_map.check_mego_data(self.input_path)
            
        except BaseException as e:
            Logger.log_error('load_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class SaveMgeoWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, mgeo, out_path):
        super().__init__()
        self.mgeo_planner_map = mgeo
        self.output_path = out_path

    def run(self):
        try:
            # traffic_sign_set.json 및 traffic_light_set.json 파일 저장
            self.mgeo_planner_map.to_json(self.output_path)
            export_log_path = self.output_path + '/Log'
            if not os.path.isdir(export_log_path):
                os.makedirs(export_log_path)
            Logger.log_copy(export_log_path)
            Logger.log_trace('save MGeo data into: {}'.format(self.output_path))

        except BaseException as e:
            Logger.log_error('export_obj failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class AddMgeoWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, mgeo_maps_dict):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.mgeo_maps_dict = mgeo_maps_dict
        self.input_path = input_path

    def run(self):
        try:
            MgeoMapPlanners(self.mgeo_maps_dict, self.mgeo_planner_map).append_map(self.input_path)
            Logger.log_trace('Added Map Dictionaries {}'.format(self.mgeo_maps_dict))
            
        except BaseException as e:
            Logger.log_error('add_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class Import42DotWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            importer = HDMap42dotImporter()
            self.mgeo_planner_map = importer.import_shp_geojson(self.input_path)
            Logger.log_info("42Dot data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import 42Dot failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportStryxWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            importer = StryxHDMapImporter()
            self.mgeo_planner_map = importer.import_geojson(self.input_path)
            Logger.log_info("Stryx data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import Stryx failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()


class ImportNaverWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            importer = NaverHDMapImporter()
            self.mgeo_planner_map = importer.import_geojson(self.input_path)
            Logger.log_info("Naver data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import Naver failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportNgiiShp1Worker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            self.mgeo_planner_map = ngii_shp1_to_mgeo.import_all_data(self.input_path)
            Logger.log_info("NGII SHP (ver1) data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import NGII SHP (ver1) failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportNgiiShp1LanemarkingWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            self.mgeo_planner_map = ngii_shp1_to_mgeo.import_lane_marking_data(self.input_path)
            Logger.log_info("NGII SHP (ver1) Lane marking data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import NGII SHP (ver1) Lane marking failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportNgiiShp2Worker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            self.mgeo_planner_map = ngii_shp2_to_mgeo.import_all_data(self.input_path)
            Logger.log_info("NGII SHP (ver2) data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import NGII SHP (ver2) failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportNgiiShp2LanemarkingWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            self.mgeo_planner_map = ngii_shp2_to_mgeo.import_lane_marking_data(self.input_path)
            Logger.log_info("NGII SHP (ver2) lane marking data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import NGII SHP (ver2) lane marking failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportDeepMapWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            importer = DeepMapImporter()
            self.mgeo_planner_map = importer.geojson_to_mgeo(self.input_path)
            Logger.log_info("Deepmap data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import Deepmap failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportCivilMapWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            importer = CivilmapsImporter()
            self.mgeo_planner_map = importer.geojson_to_mgeo(self.input_path)
            Logger.log_info("Civilmaps data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import Civilmaps failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()
        
class ImportMobilTechWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            importer = MobiltechImporter()
            self.mgeo_planner_map = importer.shp_to_map_snu(self.input_path)
            Logger.log_info("Mobiltech data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import Mobiltech failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportOpenScenarioWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, importer):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.importer = importer
        self.check_result = ''

    def run(self):
        try:
            self.mgeo_planner_map = MGeo.create_instance_from_json(self.input_path)
            self.check_result = self.mgeo_planner_map.check_mego_data(self.input_path)
            
        except BaseException as e:
            Logger.log_error('load_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportTomTomWorker(QThread):
    """
    TomTom(특히 Avro) Import 를 위한 worker thread
    import
    """
    job_finished = pyqtSignal()

    def __init__(self, data_type, input_path, import_action_list, extract_setting = None):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.data_type = data_type
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.extract_setting = extract_setting
        self.check_result = ''

    def run(self):
        try:
            self.importer = TomTomImporter()
            if self.data_type == 'shp':
                self.mgeo_planner_map = self.importer.shp_to_map(self.input_path)
            elif self.data_type == 'avro':
                self.mgeo_planner_map = self.importer.avro_to_map(self.input_path, self.extract_setting)
            elif self.data_type == 'geojson':
                self.mgeo_planner_map = self.importer.geojson_to_map(self.input_path)
            elif self.data_type == 'json':
                self.mgeo_planner_map = self.importer.json_to_map(self.input_path)
            else:
                Logger.log_error('invalid input_path (your input: {})'.format(self.input_path))

        except BaseException as e:
            Logger.log_error('import_tomtom failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()


class ImportRadRWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            importer = AutoEverImporter()
            self.mgeo_planner_map = importer.geojson_to_mgeo(self.input_path)
        except BaseException as e:
            Logger.log_error('import_tomtom failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportMGeoGeojsonWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            self.mgeo_planner_map = mGeoGeojsonImporter(self.input_path)
        except BaseException as e:
            Logger.log_error('import_tomtom failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportOpenDriveWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list, vertex_distance, sidewalk_height, z_tolerance, traffic_direction, lanemarking_height, union_junction, clean_link, gen_mesh, project_lm):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.vertex_distance = vertex_distance
        self.sidewalk_height = sidewalk_height
        self.z_tolerance = z_tolerance
        self.traffic_direction = traffic_direction
        self.lanemarking_height = lanemarking_height
        self.union_junction = union_junction
        self.clean_link = clean_link
        self.gen_mesh = gen_mesh
        self.project_lm = project_lm
        self.check_result = ''

    def run(self):
        try:
            converter = XodrConverter(self.input_path)
            converter.set_vertex_distance(self.vertex_distance)
            converter.set_sidewalk_height(self.sidewalk_height)
            converter.set_lanemarking_height(self.lanemarking_height)
            converter.set_z_tolerance(self.z_tolerance)
            converter.set_traffic_direction(self.traffic_direction)
            converter.set_generate_mesh(self.gen_mesh)
            converter.set_union_junction(self.union_junction)
            converter.set_clean_link(self.clean_link)
            converter.set_project_lm(self.project_lm)
            self.mgeo_planner_map = converter.convert_to_mgeo()

        except BaseException as e:
            Logger.log_error('import_OpenDrive failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportLanelet2Worker(QThread) :
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list) :
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self) :
        try:
            converter = OsmConverter(self.input_path)
            self.mgeo_planner_map = converter.convert_to_mgeo()

        except BaseException as e:
            Logger.log_error('import_Lanelet2 failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportRoadRunnerGeoJson(QThread) :
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list, config) :
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.config = config
        self.check_result = ''

    def run(self) :
        try:
            spheroid = self.config['spheroid']
            latitude_of_origin = self.config['latitude_of_orign']
            central_meridian = self.config['central_meridian']
            scale_factor = self.config['scale_factor']
            false_easting = self.config['false_easting']
            false_northing = self.config['false_northing']
            world_origin_lat = self.config['world_orign_latitude']
            world_origin_lon = self.config['world_orign_longitude']

            self.mgeo_planner_map = RoadrunnerImporter(
                self.input_path, spheroid, latitude_of_origin, central_meridian, scale_factor, false_easting, false_northing,
                world_origin_lat, world_origin_lon)

        except BaseException as e:
            Logger.log_error('import_Lanelet2 failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ExportObjWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, mgeo, out_path):
        super().__init__()
        self.mgeo_planner_map = mgeo
        self.output_path = out_path

    def run(self):
        try:
            edit_road_poly.road_poly_to_obj(self.mgeo_planner_map.road_polygon_set, self.output_path)
            
            Logger.log_info('OBJ successfully saved (path : {})'.format(self.output_path))

        except BaseException as e:
            Logger.log_error('export_obj failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ExportGeoJsonWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, mgeo_maps_dict, out_path):
        super().__init__()
        self.mgeo_maps_dict = mgeo_maps_dict
        self.output_path = out_path

    def run(self):
        try:
            mgeo_to_geojson(self.mgeo_maps_dict, self.output_path)
            
            Logger.log_info('MGeo geoJSON successfully saved (path : {})'.format(self.output_path))

        except BaseException as e:
            Logger.log_error('export_geojson failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ExportSimDataWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, mgeo_maps_dict, out_path, mgeo_key, export_type, result=None):
        super().__init__()
        self.mgeo_maps_dict = mgeo_maps_dict
        self.output_path = out_path
        self.mgeo_key = mgeo_key
        self.export_type = export_type
        self.result = result

    def run(self):
        try:
            mgeo_planner_map = self.mgeo_maps_dict[self.mgeo_key]
            if self.export_type == 'TL':
                export_traffic_light_csv(mgeo_planner_map, self.output_path, self.mgeo_key)
            elif self.export_type == 'TS':
                export_traffic_sign_csv(mgeo_planner_map.sign_set, self.output_path, self.result)
            elif self.export_type == 'SM':
                export_surface_mark(mgeo_planner_map, self.output_path)
            elif self.export_type == 'Road':
                if self.result == '':
                    export_road_mesh(mgeo_planner_map, self.output_path, None)
                else:
                    step_len = float(self.result)
                    export_road_mesh(mgeo_planner_map, self.output_path, step_len)

            elif self.export_type == 'Lane':
                export_lane_mesh(mgeo_planner_map, self.output_path, self.mgeo_key, self.result)
            elif self.export_type == 'Structure' :
                export_structure_mesh(mgeo_planner_map, self.output_path)
            else:
                return
            Logger.log_info("Successfully road_mesh data is saved into: {}".format(self.output_path))

        except BaseException as e:
            Logger.log_error('export_sim_data failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ExportCsvWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, mgeo, out_path, is_merge, is_link, is_lanemarking):
        super().__init__()
        self.mgeo_planner_map = mgeo
        self.output_path = out_path
        self.is_merge = is_merge
        self.is_link = is_link
        self.is_lanemarking = is_lanemarking

    def run(self):
        try:
            if self.is_merge:
                save_file_name = self.output_path + '/all_lines.csv'

                if (save_file_name == '' or save_file_name == None):
                    Logger.log_error('invalid save_file_name (your input: {})'.format(save_file_name))
                    return

                # 저장하는 기능
                if os.path.exists(save_file_name):
                    print('[WARNING] Removing an existing file... ({})'.format(save_file_name))
                    os.remove(save_file_name)
                
                if self.is_link:
                    export_link_as_csv(self.mgeo_planner_map, save_file_name)

                if self.is_lanemarking:
                    export_lane_marking_as_csv(self.mgeo_planner_map, save_file_name)
                
                Logger.log_trace('save csv file as {}'.format(save_file_name))
            else:
                # 폴더 선택
                file_name = ''
                if self.is_link:
                    save_file_name = self.output_path +'/link.csv'
                    if os.path.exists(save_file_name):
                        print('[WARNING] Removing an existing file... ({})'.format(save_file_name))
                        os.remove(save_file_name)

                    export_link_as_csv(self.mgeo_planner_map, save_file_name)
                
                if self.is_lanemarking:
                    save_file_name = self.output_path + '/lane_boundary.csv'
                    if os.path.exists(save_file_name):
                        print('[WARNING] Removing an existing file... ({})'.format(save_file_name))
                        os.remove(save_file_name)

                    export_lane_marking_as_csv(self.mgeo_planner_map, save_file_name)
            
            export_path = os.path.dirname(save_file_name)
                       
            # MGEO 같이 저장
            export_mgeo_path = export_path + '/MGeo'
            if not os.path.isdir(export_mgeo_path):
                os.makedirs(export_mgeo_path)
            Logger.log_trace('save MGeo data into: {}'.format(export_mgeo_path))

            # traffic_sign_set.json 및 traffic_light_set.json 파일 저장
            self.mgeo_planner_map.to_json(export_mgeo_path)

            # Log 같이 저장
            export_log_path = export_path + '/Log'
            if not os.path.isdir(export_log_path):
                os.makedirs(export_log_path)
           
            Logger.log_copy(export_log_path)

        except BaseException as e:
            Logger.log_error('export_csv failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class ImportKakaomobilityWorker(QThread):
    job_finished = pyqtSignal()

    def __init__(self, input_path, import_action_list):
        super().__init__()
        self.mgeo_planner_map = MGeo()
        self.input_path = input_path
        self.import_action_list = import_action_list
        self.check_result = ''

    def run(self):
        try:
            importer = KakaomobilityHDMapImporter()
            self.mgeo_planner_map = importer.import_geojson(self.input_path)
            Logger.log_info("Kakaomobility data imported from: {}".format(self.input_path))
            
        except BaseException as e:
            Logger.log_error('Import Kakaomobility failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        self.job_finished.emit()

class FileIOFuncs(QObject):
    file_io_job_start = pyqtSignal(str)
    file_io_job_finished = pyqtSignal()
    next_job = None
    next_job_args = None
    command_manager = None

    def __init__(self, py_qt_window, canvas):
        super().__init__()
        self.py_qt_window = py_qt_window
        self.canvas = canvas
        self.mgeo_planner_map = None
        self.mscenario = None
        
        self.config = None
        self.config_file_path = None
        self.program_root_dir = None
        
        # 기존에 있던 load path 를 가지고 있을수 있는 path 그리고 mgeo_maps 들을 확인 할수 있는 dictionary
        self.loaded_path = None
        self.mgeo_maps_dict = dict()
        
        # Save the input path when tomtom importer used
        self.tomtom_import_path = None
        #self.command_manager = CommandManager()
        
    #테스트용 삭제 예정
    def do_something(self) :
        #set command
        #self.command_manager.execute()
        """"""
        
    def get_path_from_config(self, key):
        config = self.config['file_path'][0]
        if self.config is None:
            raise BaseException('Error in the initialization of this class: self.config is None')
        
        if self.config_file_path is None:
            raise BaseException('Error in the initialization of this class: self.config_file_path is None')
            
        if self.program_root_dir is None:
            raise BaseException('Error in the initialization of this class: self.program_root_dir is None')

        if key not in config.keys():
            raise BaseException('Error in the config file ({}): key: {} is missing'.format(self.config_file_path, key))

        path_in_config = config[key]
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
    
    
    def get_tm_setting_from_config(self):
        if self.config is None:
            raise BaseException('Error in the initialization of this class: self.config is None')
        
        if self.config_file_path is None:
            raise BaseException('Error in the initialization of this class: self.config_file_path is None')
            
        if self.program_root_dir is None:
            raise BaseException('Error in the initialization of this class: self.program_root_dir is None')

       
        config = self.config['world_setting'][0]

        return config

    def get_odr_import_setting_from_config(self):
        if self.config is None:
            raise BaseException('Error in the initialization of this class: self.config is None')
        
        if self.config_file_path is None:
            raise BaseException('Error in the initialization of this class: self.config_file_path is None')
            
        if self.program_root_dir is None:
            raise BaseException('Error in the initialization of this class: self.program_root_dir is None')

       
        config = self.config['odr_import'][0]

        return config
    
    def get_open_filename(self, title, init_path_config, extension):
        init_path = self.get_path_from_config(init_path_config)
        res = QFileDialog.getOpenFileName(QFileDialog(), title, init_path,
                                          filter="*.{};; All File(*)".format(extension),
                                          options=QFileDialog.DontUseNativeDialog )
        if not res or not res[0]:
            return ""
        else:
            filename = res[0]
        
        # Update config file (save latest file path)
        self.update_file_path_config(init_path_config,
                                     os.path.normpath(os.path.join(filename, '../')))
        return filename

    def get_open_filenames(self, title, init_path_config, extension):
        init_path = self.get_path_from_config(init_path_config)
        res = QFileDialog.getOpenFileNames(QFileDialog(), title, init_path,
                                           filter="*.{};; All File(*)".format(extension),
                                           options=QFileDialog.DontUseNativeDialog )
        if not res or not res[0]:
            return list()
        else:
            filename_list = res[0]
        
        # Update config file (save latest file path)
        self.update_file_path_config(init_path_config,
                                     os.path.normpath(os.path.join(filename_list[0], '../')))
        return filename_list
    
    def get_save_filename(self, title, init_path_config, extension, name_filter=None):
        init_path = self.get_path_from_config(init_path_config)

        saveDialog = QFileDialog()
        saveDialog.setDefaultSuffix(extension)
        saveDialog.setWindowTitle(title)
        saveDialog.setDirectory(init_path)
        saveDialog.setAcceptMode(QFileDialog.AcceptSave)
        if name_filter:
            saveDialog.setNameFilter(name_filter)
        saveDialog.setOptions(QFileDialog.DontUseNativeDialog)
        if saveDialog.exec_() != QFileDialog.Accepted:
            return ""
        res = saveDialog.selectedFiles()

        if not res or not res[0]:
            return ""
        else:
            filename = res[0]

        extension = '.' + extension
        if extension not in filename.split('/')[-1]:
            filename += extension
        
        # Update config file (save latest file path)
        self.update_file_path_config(init_path_config,
                                     os.path.normpath(os.path.join(filename, '../')))
        
        return filename
    
    def get_existing_directory(self, title, init_path_config):
        init_path = self.get_path_from_config(init_path_config)
        res = QFileDialog.getExistingDirectory(QFileDialog(), title, init_path,
                                               options=QFileDialog.DontUseNativeDialog)

        if not res:
            return ""
        else:
            dir_name = res

        # Update config file (save latest file path)
        self.update_file_path_config(init_path_config,
                                     os.path.normpath(os.path.join(dir_name, '../')))
        return dir_name
    
    def ask_save_current_data(self, program_name):
        try:
            Logger.log_trace('Called: ask_save_current_data')
            if self.canvas.mgeo_planner_map is not None and len(self.canvas.mgeo_planner_map.node_set.nodes) > 0:
                result = QMessageBox.question(self.canvas, program_name, 'Do you want to save your changes?')
                if result == QMessageBox.Yes:
                    Logger.log_trace('Save current MGeo data before load? -> Yes')
                    return True
                else:
                    Logger.log_trace('Save current MGeo data before load? -> No')
            else:
                Logger.log_trace('No MGeo data to save -> return')
            return False
        except BaseException as e:
            Logger.log_error('ask_save_current_data failed (traceback is down below) \n{}'.format(traceback.format_exc()))
            return False
        

    def update_file_path_config(self, key, new_value):
        config = self.config['file_path'][0]
        
        if self.config is None:
            raise BaseException('Error in the initialization of this class: self.config is None')
        
        if self.config_file_path is None:
            raise BaseException('Error in the initialization of this class: self.config_file_path is None')
            
        if self.program_root_dir is None:
            raise BaseException('Error in the initialization of this class: self.program_root_dir is None')

        if key not in config.keys():
            raise BaseException('Error in the config file ({}): key: {} is missing'.format(self.config_file_path, key))

        with open(self.config_file_path, 'w') as f:
            self.config['file_path'][0][key] = new_value
            json.dump(self.config, f, indent=4)


    def update_tm_setting_config(self, new_data_dict):
        if self.config is None:
            raise BaseException('Error in the initialization of this class: self.config is None')

        if self.config_file_path is None:
            raise BaseException('Error in the initialization of this class: self.config_file_path is None')

        if self.program_root_dir is None:
            raise BaseException('Error in the initialization of this class: self.program_root_dir is None')

        # string 형으로 변경
        for key in new_data_dict.keys():
            if type(new_data_dict[key]) is not str:
                new_data_dict[key] = str(new_data_dict[key])

        with open(self.config_file_path, 'w') as f:
            self.config['world_setting'][0] = new_data_dict
            json.dump(self.config, f, indent=4)


    def update_odr_import_setting_config(self, new_data_dict):
        if self.config is None:
            raise BaseException('Error in the initialization of this class: self.config is None')
        
        if self.config_file_path is None:
            raise BaseException('Error in the initialization of this class: self.config_file_path is None')
            
        if self.program_root_dir is None:
            raise BaseException('Error in the initialization of this class: self.program_root_dir is None')
        
        # string 형으로 변경
        for key in new_data_dict.keys():
            if type(new_data_dict[key]) is not str:
                new_data_dict[key] = str(new_data_dict[key])

        with open(self.config_file_path, 'w') as f:
            self.config['odr_import'][0] = new_data_dict
            json.dump(self.config, f, indent=4)
        

    def import_42dot(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('42dot_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains 42dot HDMap data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import 42dot HDMap data from: {}'.format(input_path))

            self.mgeo_maps_dict.clear()

            # 실제 import한 경로보다 한 경로 위를 저장
            self.update_file_path_config('42dot_MAP_IMPORT', os.path.normpath(os.path.join(input_path, '../')))

            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import 42Dot data from: {}'.format(input_path))
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = Import42DotWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_42dot failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_stryx(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('Stryx_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains Stryx HDMap data', init_import_path)

            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import Stryx HDMap data from: {}'.format(input_path))

            self.mgeo_maps_dict.clear()

            # 실제 import한 경로보다 한 경로 위를 저장
            self.update_file_path_config('Stryx_MAP_IMPORT', os.path.normpath(os.path.join(input_path, '../')))

            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import Stryx data from: {}'.format(input_path))
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportStryxWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_stryx failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_naver(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('Naver_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains Naver HDMap data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import Naver HDMap data from: {}'.format(input_path))

            self.mgeo_maps_dict.clear()

            # 실제 import한 경로보다 한 경로 위를 저장
            self.update_file_path_config('Naver_MAP_IMPORT', os.path.normpath(os.path.join(input_path, '../')))
            
            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import Naver data from: {}'.format(input_path))
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportNaverWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_naver failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_deepmap(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('DM_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains DeepMap data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import DeepMap data from: {}'.format(input_path))

            self.mgeo_maps_dict.clear()

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('DM_MAP_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))
            
            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import Deepmap data from: {}'.format(input_path))
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportDeepMapWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_deepmap failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_tomtom(self, import_action_list, data_type, program_name):
        try:
            Logger.log_trace('Called: import_tomtom')
            is_save = self.ask_save_current_data(program_name)

            if is_save :
                args = dict()
                args["import_action_list"] = import_action_list
                args["data_type"] = data_type
                args["program_name"] = program_name
                self.next_job = self.import_tomtom_thread
                self.next_job_args = args
                self.save_mgeo()
            else :
                self.import_tomtom_thread(import_action_list, data_type, program_name)

        except BaseException as e:
            self.next_job = None
            self.next_job_args = None
            Logger.log_error('import_tomtom failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def import_tomtom_thread(self, import_action_list, data_type, program_name):
        try:
            extract_boundary_setting = None
            if data_type == 'avro':
                QMessageBox.warning(self.canvas,
                    "Evaluation Version Notification",
                    "This feature is not fully implemented yet in the evaluation version. (e.g. Importing large files takes a lot of time.) Full features are to be provided in the final shipping version.")

                from lib.widget.edit_extract_boundary import EditExtractBoundary

                edit_extract_boundary = EditExtractBoundary()
                edit_extract_boundary.config_file_path = os.path.join(self.program_root_dir , 'config_extract_region.json')
                edit_extract_boundary.initUI()
                edit_extract_boundary.showDialog()
                if edit_extract_boundary.result() < 1:
                    Logger.log_error('No extraction region has been set.')
                    return

                extract_boundary_setting = edit_extract_boundary.extract_region_config
                Logger.log_info('Extract region setting : {}'.format(str(extract_boundary_setting)))

            init_import_path = self.get_path_from_config('TOMTOM_IMPORT')
            Logger.log_trace('init_import_path: {}({})'.format(init_import_path, data_type))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains TomTom {} data'.format(data_type), 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

            if (input_path == '' or input_path == None):
                Logger.log_error('Invalid input_path (your input: {})'.format(input_path))
                return

            # Save tomtom file path
            self.tomtom_import_path = input_path

            # 파일 크기가 100mb 이상인 파일이 있으면 지원하지 않는다.
            sub_files = []
            for path, subdirs, files in os.walk(input_path):
                for name in files:
                    sub_files.append(os.path.join(path, name))

            limit_file_size_mb = 100
            megabytes = 1024 * 1024
            limit_bytes = limit_file_size_mb * megabytes
            for file in sub_files:
                if getsize(file) > limit_bytes:
                    Logger.log_error('For this evaluation version, files that are larger than {}MB cannot be loaded.'.format(limit_file_size_mb))
                    QMessageBox.warning(self.canvas, 'Warning', "For this evaluation version, files that are larger than {}MB cannot be loaded.".format(limit_file_size_mb))
                    return

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('TOMTOM_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))

            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import TomTom data from: {}'.format(input_path))
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportTomTomWorker(data_type, input_path, import_action_list, extract_boundary_setting)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()
            
        except BaseException as e:
            Logger.log_error('import_tomtom_thread failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def import_civilmaps(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('CM_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains Civilmaps Json data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import civilmaps data from: {}'.format(input_path))

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('CM_MAP_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))

            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import Civilmaps data from: {}'.format(input_path))
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportCivilMapWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_civilmaps failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_mobiltech(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('MOBILTECH_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains mobiltech shp data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import mobiltech data from: {}'.format(input_path))

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('MOBILTECH_MAP_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))
            
            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import Mobiltech data from: {}'.format(input_path))
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportMobilTechWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_mobiltech failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_ngii_shp1_lane_marking(self, import_action_list):
        try:
            
            init_import_path = self.get_path_from_config('SHP1_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains ngii shp1 data(lane_boundary)', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import shp1 data from: {}'.format(input_path))

            self.mgeo_maps_dict.clear()

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('SHP1_MAP_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))
            
            self.file_io_job_start.emit('Importing data...')
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportNgiiShp1LanemarkingWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_ngii_shp1_lane_marking failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_ngii_shp1(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('SHP1_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains ngii shp1 data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import shp1 data from: {}'.format(input_path))

            self.mgeo_maps_dict.clear()

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('SHP1_MAP_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))
            
            self.file_io_job_start.emit('Importing data...')
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportNgiiShp1Worker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_ngii_shp1 failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_ngii_shp2_lane_marking(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('SHP2_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))


            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains ngii shp2 data(lane_boundary)', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import shp2 data from: {}'.format(input_path))

            self.mgeo_maps_dict.clear()

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('SHP2_MAP_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))
            
            self.file_io_job_start.emit('Importing data...')
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportNgiiShp2LanemarkingWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_ngii_shp2_lane_marking failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_ngii_shp2(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('SHP2_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains ngii shp2 data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import shp2 data from: {}'.format(input_path))

            self.mgeo_maps_dict.clear()

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('SHP2_MAP_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))

            self.file_io_job_start.emit('Importing data...')
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportNgiiShp2Worker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_ngii_shp2 failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def import_txt(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('TXT_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))
            
            from lib.widget.select_waypoint_file_type import SelectWaypointFileType

            select_file_type = SelectWaypointFileType()
            way_point_file_type = select_file_type.showDialog()

            if way_point_file_type != 1:
                return
            else:
                if select_file_type.shp_file.isChecked():
                    import_type = 'shp'
                else:
                    import_type = 'txt'

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains txt data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import txt data from: {}'.format(input_path))

            if import_type == 'shp':
                self.mgeo_planner_map = import_modelling_line_shp_file(input_path)
            else:
                self.mgeo_planner_map = import_geojson_data(input_path)

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

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('TXT_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))

            Logger.log_info("txt data imported from: {}".format(input_path))

        except BaseException as e:
            Logger.log_error('import_txt failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_roadrunner_geojson(self, import_action_list, program_name):
        try:
            self.mgeo_maps_dict.clear()
            Logger.log_trace('Called: import_roadrunner_geojson')
            is_save = self.ask_save_current_data(program_name)

            if is_save :
                args = dict()
                args["import_action_list"] = import_action_list
                args["program_name"] = program_name
                self.next_job = self.import_roadrunner_geojson_thread
                self.next_job_args = args
                self.save_mgeo()
            else :
                self.import_roadrunner_geojson_thread(import_action_list, program_name)
        except BaseException as e:
            self.next_job = None
            self.next_job_args = None
            Logger.log_error('import_roadrunner_geojson failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def import_roadrunner_geojson_thread(self, import_action_list, program_name):
        try:
            init_import_path = self.get_path_from_config('ROADRUNNER_GEOJSON_IMPORT')  
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            tm_setting_cofing = self.get_tm_setting_from_config()


            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains roadrunner geojson data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks  | QFileDialog.DontUseNativeDialog)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import_roadrunner_geojson from: {}'.format(input_path))


            # World Projection 설정 받아오기
            editWorldProjectionWindow = EditWorldProjectionWindow(tm_setting_cofing)
            if editWorldProjectionWindow.exec_():
                spheroid, latitude_of_origin, central_meridian, scale_factor, false_easting, false_northing = editWorldProjectionWindow.getParameters()
            else:
                Logger.log_info('import_roadrunner_geojson canceled by user (world projection not provided)')
                return

            # World Origin 받아오기
            editWorldOriginLatLonWindow = EditWorldOriginLatLonWindow(tm_setting_cofing)
            if editWorldOriginLatLonWindow.exec_():
                world_origin_lat, world_origin_lon = editWorldOriginLatLonWindow.getParameters()
            else:
                Logger.log_info('import_roadrunner_geojson canceled by user (world projection not provided)')
                return

            # 변경된 세팅 값 저장
            tm_setting_cofing['spheroid'] = spheroid
            tm_setting_cofing['latitude_of_orign'] = latitude_of_origin
            tm_setting_cofing['central_meridian'] = central_meridian
            tm_setting_cofing['scale_factor'] = scale_factor
            tm_setting_cofing['false_easting'] = false_easting
            tm_setting_cofing['false_northing'] = false_northing
            tm_setting_cofing['world_orign_latitude'] = world_origin_lat
            tm_setting_cofing['world_orign_longitude'] = world_origin_lon
            rr_config = dict.copy(tm_setting_cofing)

            self.update_tm_setting_config(tm_setting_cofing)

            # Config 파일 업데이트 (최근 파일 경로 저장)
            self.update_file_path_config('ROADRUNNER_GEOJSON_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))

            self.last_path = input_path                  #import_data_finished 에서 사용
            self.file_io_job_start.emit('Importing data...')
            self.import_thread = ImportRoadRunnerGeoJson(input_path, import_action_list, rr_config)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()
            
        except BaseException as e:
            Logger.log_error('import_roadrunner_geojson_thread failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def import_data_finished(self):
        try:
            self.mgeo_planner_map = self.import_thread.mgeo_planner_map        
            import_action_list = self.import_thread.import_action_list

            if len(self.import_thread.check_result) > 0:
                Logger.log_warning('Changes detail info {}'.format(self.import_thread.check_result))
                QMessageBox.warning(self.canvas, "Warning", 'Changes detected in the selected MGeo data.')

            Logger.log_info(self.last_path)

            self.mgeo_maps_dict.clear()
            self.mgeo_maps_dict[str(self.last_path.split("/")[-1])] = self.mgeo_planner_map

            self.canvas.setMGeoPlannerMap(self.mgeo_maps_dict)
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
            
            self.import_thread.quit()

            Logger.log_info("Data successfully loaded from: {}".format(self.import_thread.input_path))
    
        except BaseException as e:
            Logger.log_error('import_data_finished failed (traceback is down below) \n{}'.format(traceback.format_exc()))            
        
        finally:
            if self.import_thread.isRunning():
                self.import_thread.terminate()
                self.import_thread.wait()
                
            self.file_io_job_finished.emit()
            del self.import_thread
            self.command_manager.clear()

    def import_OpenDRIVE(self, import_action_list):
        try:
            Logger.log_trace('Called: import_openDRIVE')

            init_import_path = self.get_path_from_config('OpenDRIVE_IMPORT')

            input_path = QFileDialog.getOpenFileName(QFileDialog(), 'Select a Open Drive file', 
                        init_import_path, filter='*.xodr *.odr;; All File(*)',\
                             options= QFileDialog.DontUseNativeDialog)
                        
            if (input_path == '' or input_path == None or input_path[0] == ''):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            odr_import_setting_cofing = self.get_odr_import_setting_from_config()

            odrImportWindow = OpenDriveImportWindow(odr_import_setting_cofing)
            if odrImportWindow.exec_():
                vertex_distance, sidewalk_height, z_tolerance, traffic_direction, lanemarking_height, union_junction, clean_link, gen_mesh, project_lm = odrImportWindow.getParameters()
            else:
                Logger.log_info('import_OpenDRIVE canceled by user')
                return

            # 변경된 세팅 값 저장
            odr_import_setting_cofing['vertex_distance'] = vertex_distance
            odr_import_setting_cofing['sidewalk_height'] = sidewalk_height
            odr_import_setting_cofing['lanemarking_height'] = lanemarking_height
            odr_import_setting_cofing['z_tolerance'] = z_tolerance
            odr_import_setting_cofing['traffic_direction'] = traffic_direction
            odr_import_setting_cofing['union_junction'] = union_junction
            odr_import_setting_cofing['clean_link'] = clean_link
            odr_import_setting_cofing['project_lm'] = project_lm
            odr_import_setting_cofing['generate_mesh'] = gen_mesh

            self.update_odr_import_setting_config(odr_import_setting_cofing)

            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import OpenDRIVE data from: {}'.format(input_path[0]))

            # Config 파일 업데이트 (최근 파일 경로 저장)
            self.update_file_path_config('OpenDRIVE_IMPORT',
                os.path.normpath(os.path.join(input_path[0], '../')))

            # Import 를 위한 Thread 실행
            self.last_path = input_path[0]
            self.import_thread = ImportOpenDriveWorker(input_path[0],
                import_action_list, vertex_distance, sidewalk_height, z_tolerance,
                traffic_direction, lanemarking_height, union_junction, clean_link, gen_mesh, project_lm)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()
 
        except BaseException as e:
            Logger.log_error('import_openDRIVE failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_openscenario_finished(self):
        try:
            if len(self.import_thread.check_result) > 0:
                Logger.log_warning('Changes detail info {}'.format(self.import_thread.check_result))
                QMessageBox.warning(self.canvas, "Warning", 'Changes detected in the selected MGeo data.')

            importer = self.import_thread.importer
            importer.set_mgeo(self.import_thread.mgeo_planner_map)
            
            self.import_thread.quit()
            Logger.log_info("OpenSCENARIO is successfully loaded")
        except BaseException as e:
            Logger.log_error('Failed to import OpenSCENARIO (traceback is down below) \n{}'.format(traceback.format_exc()))            
        
        finally:
            if self.import_thread.isRunning():
                self.import_thread.terminate()
                self.import_thread.wait()
                
            self.file_io_job_finished.emit()
            del self.import_thread
            self.command_manager.clear()

    def import_OpenScenario(self, importer:OpenScenarioImporter, input_path=None):
        try:
            Logger.log_trace('Called: Import OpenScenario')

            if input_path is None:
                input_path = self.get_open_filename("Select an OpenSCENARIO file",
                                                    'OpenScenario_IMPORT','xosc')
            elif not os.path.exists(input_path):
                input_path = None
                raise ValueError("Given OpenSCENARIO file doesn't exist")

            if not input_path:
                return

            # Import OpenScenario
            importer.import_open_scenario(input_path)
            if importer.scenario_definition is None:
                raise Exception("ScenarioDefinition is not valid")
            
            # Load MGeo
            mgeo_folder_path = importer.get_mgeo_folder_path()
            if not os.path.exists(mgeo_folder_path):
                raise ValueError("Invalid MGeo folder path")
            else:
                Logger.log_info("Attempt to load the MGeo data from '{}'".format(
                                os.path.normpath(mgeo_folder_path)))

            self.last_path = mgeo_folder_path
            self.file_io_job_start.emit("Loading MGeo...")
            self.import_thread = ImportOpenScenarioWorker(mgeo_folder_path, importer)
            self.import_thread.job_finished.connect(self.import_openscenario_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('Failed to import OpenScenario: {}'.format(e))
            QMessageBox.critical(self.canvas, "Error", "Failed to import the OpenScenario file")

    def import_Lanelet2(self, import_action_list):
        try:
            Logger.log_trace('Called: import_Lanelet2')

            init_import_path = self.get_path_from_config('Lanelet2_IMPORT')

            input_path = QFileDialog.getOpenFileName(QFileDialog(), 'Select a Lanelet2 file', 
                        init_import_path, filter='*.osm;; All File(*)')
                        
            if (input_path == '' or input_path == None or input_path[0] == ''):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import Lanelet2 data from: {}'.format(input_path[0]))

            # Config 파일 업데이트 (최근 파일 경로 저장)
            self.update_file_path_config('Lanelet2_IMPORT',
                os.path.normpath(os.path.join(input_path[0], '../')))

            # Import 를 위한 Thread 실행
            self.last_path = input_path[0]
            self.import_thread = ImportLanelet2Worker(input_path[0], import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()
            
            # 먼저 테스트 코드 작성. 
            # self.import_thread = ImportLanelet2Worker(input_path[0], import_action_list)
            # self.import_thread.run()
  
        except BaseException as e:
            Logger.log_error('import_Lanelet2 failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def save_mgeo(self):
        try:
            init_save_path = self.get_path_from_config('MGEO_SAVE')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder to save MGeo data into', 
                        init_save_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks  | QFileDialog.DontUseNativeDialog)

            if save_path == '' or save_path == None:
                Logger.log_error('invalid save_path (your input: {})'.format(save_path))
                return

            # 실제 save한 경로보다 한 경로 위를 저장
            self.update_file_path_config('MGEO_SAVE', os.path.normpath(os.path.join(save_path, '../')))

            self.file_io_job_start.emit('Saving mgeo...')
            self.export_thread = SaveMgeoWorker(self.mgeo_planner_map, save_path)
            self.export_thread.job_finished.connect(self.export_finished)
            self.export_thread.start()

        except BaseException as e:
            Logger.log_error('save_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))
            
    def save_mscenario(self):
        try:
            init_save_path = self.get_path_from_config('MScenario_SAVE')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder to save MScenario data into', 
                        init_save_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

            if save_path == '' or save_path == None:
                Logger.log_error('invalid save_path (your input: {})'.format(save_path))
                return

            Logger.log_trace('save MScenario data into: {}'.format(save_path))

            # mgeo 파일 저장
            self.mgeo_planner_map.to_json(save_path)

            # mscenario 파일 저장
            mscenario_save_path = os.path.join(save_path, 'mscenario') 
            if os.path.isdir(mscenario_save_path):
                self.mscenario.save(mscenario_save_path)
            else:
                os.makedirs(mscenario_save_path)
                self.mscenario.save(mscenario_save_path)

            # 실제 save한 경로보다 한 경로 위를 저장
            self.update_file_path_config('MScenario_SAVE', os.path.normpath(os.path.join(save_path, '../')))
            Logger.log_info("Successfully MScenario data is saved into: {}".format(save_path))

        except BaseException as e:
            Logger.log_error('save_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def save_openscenario(self):
        try:
            importer:OpenScenarioImporter = self.canvas.get_open_scenario()
            if importer == None or importer.scenario_definition == None:
                Logger.log_error('Please Load the OpenScenario Data')
                return

            scenario_file_path = self.get_save_filename("Save OpenSCENARIO file",
                                                        'OpenScenario_SAVE',
                                                        'xosc',
                                                        "Scenario files (*.xosc)")
            if not scenario_file_path:
                return
            
            importer.write_xml(scenario_file_path)
            self.canvas.updateTreeWidget()
            Logger.log_info('Successfully OpenScenario data is saved into : {}'.format(scenario_file_path))

        except BaseException as e:
            Logger.log_info("save_openScenario failed (traceback is down below) \n{}".format(traceback.format_exc()))
    
    def create_new_openscenario(self, importer:OpenScenarioImporter):
        try:
            new_open_scenario = NewOpenScenarioUI(self)
            new_open_scenario.showDialog()

            map_name = new_open_scenario.map_name
            mgeo_folder_path = new_open_scenario.mgeo_folder_path
            if not map_name or not mgeo_folder_path:
                return
            
            importer.create_scenario_definition(map_name, mgeo_folder_path)
            
            self.last_path = mgeo_folder_path
            self.file_io_job_start.emit('Loading MGeo...')
            self.import_thread = ImportOpenScenarioWorker(mgeo_folder_path, importer)
            self.import_thread.job_finished.connect(lambda:self.import_openscenario_finished())
            self.import_thread.start()

        except BaseException as e:
            Logger.log_info("Failed to create new OpenSCENARIO (traceback is down below) \n{}".format(traceback.format_exc()))

    def load_mgeo(self, import_action_list, program_name):
        try:
            # Creates the command
            #cmd_load = Load_mgeo(self.command_reciever)
            #self.command_manager.set_command("load", cmd_load)
            
            Logger.log_trace('Called: load_mgeo')
            # 새로운 mgeo 로드 할 때 기존에 수정 중 이던 mgeo 저장 여부 물어보기
            
            is_save = self.ask_save_current_data(program_name)

            if is_save :
                args = dict()
                args["import_action_list"] = import_action_list
                args["program_name"] = program_name
                self.next_job = self.load_mgeo_thread
                self.next_job_args = args
                self.save_mgeo()
            else :
                self.load_mgeo_thread(import_action_list, program_name)
        except BaseException as e:
            self.next_job = None
            self.next_job_args = None
            Logger.log_error('load_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def load_mgeo_thread(self, import_action_list, program_name):
        try:
            init_load_path = self.get_path_from_config('MGEO_LOAD')
            Logger.log_trace('init_load_path: {}'.format(init_load_path))

            self.load_path = QFileDialog.getExistingDirectory(self.canvas, 'Select a folder that contains MGeo data',
                        init_load_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks | QFileDialog.DontUseNativeDialog)

            if (self.load_path == '' or self.load_path == None):
                Logger.log_error('invalid load_path (your input: {})'.format(self.load_path))
                return

            Logger.log_trace('load MGeo data from: {}'.format(self.load_path))

            # 실제 load한 경로보다 한 경로 위를 저장
            self.update_file_path_config('MGEO_LOAD', os.path.normpath(os.path.join(self.load_path, '../')))
            Logger.log_info("MGeo data successfully loaded from: {}".format(self.load_path))

            self.last_path = self.load_path                  #import_data_finished 에서 사용
            self.file_io_job_start.emit('Loading Mgeo...')
            self.import_thread = LoadMgeoWorker(self.load_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('load_mgeo_thread failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def add_mgeo_finished(self):
        try:
            self.canvas.setMGeoPlannerMap(self.mgeo_maps_dict)
            self.canvas.resetCamera()

            # import한 데이터 내용 추가
            self.canvas.updateTreeWidget()
            
            self.import_thread.quit()

            Logger.log_info("Mgeo successfully added from: {}".format(self.import_thread.input_path))
    
        except BaseException as e:
            Logger.log_error('add_mgeo_finished failed (traceback is down below) \n{}'.format(traceback.format_exc()))            
        
        finally:
            if self.import_thread.isRunning():
                self.import_thread.terminate()
                self.import_thread.wait()
                
            self.file_io_job_finished.emit()
            del self.import_thread

    def add_mgeo(self):
        try:
            #cmd_add = Add(self.command_reciever)
            #self.command_manager.set_command("add", cmd_add)
            Logger.log_trace('Called: add_mgeo')

            init_add_path = self.get_path_from_config('MGEO_ADD')

            Logger.log_trace('init_add_path: {}'.format(init_add_path))

            add_path = QFileDialog.getExistingDirectory(self.canvas, 'Select a folder that contains MGeo data', 
                        init_add_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks  | QFileDialog.DontUseNativeDialog)

            if (add_path == '' or add_path == None):
                Logger.log_error('invalid add_path (your input: {})'.format(add_path))
                return

            Logger.log_trace('add MGeo data from: {}'.format(add_path))

            # 실제 load한 경로보다 한 경로 위를 저장
            self.update_file_path_config('MGEO_ADD', os.path.normpath(os.path.join(add_path, '../')))

            self.last_path = add_path                  #import_data_finished 에서 사용
            self.file_io_job_start.emit('Adding Mgeo...')
            self.import_thread = AddMgeoWorker(add_path, self.mgeo_maps_dict)
            self.import_thread.job_finished.connect(self.add_mgeo_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('add_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def load_mscenario(self, import_action_list):
        try:
            init_load_path = self.get_path_from_config('MScenario_LOAD')
            Logger.log_trace('init_load_path: {}'.format(init_load_path))
            
            load_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains MGeo and MScenario data', 
                        init_load_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks  | QFileDialog.DontUseNativeDialog)

            if (load_path == '' or load_path == None):
                Logger.log_error('invalid load_path (your input: {})'.format(load_path))
                return

            Logger.log_trace('load MGeo and MScenario data from: {}'.format(load_path))

            # MGeo 로드
            self.mgeo_planner_map = MGeo.create_instance_from_json(load_path)

            # Mscenario 로드
            self.mscenario = MScenario()
            self.mscenario = self.mscenario.load(load_path)
           
            self.canvas.setMGeoPlannerMap(self.mgeo_planner_map)
            self.canvas.setMScenario(self.mscenario)
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
            self.update_file_path_config('MGEO_LOAD', os.path.normpath(os.path.join(load_path, '../')))
            Logger.log_info("MGeo data successfully loaded from: {}".format(load_path))

        except BaseException as e:
            Logger.log_error('load_mscenario failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def import_rad_r_data(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('RAD_R_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains RAD-R data', init_import_path)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import RAD-R data from: {}'.format(input_path))

            # 실제 import한 경로보다 한 경로 위를 저장
            self.update_file_path_config('RAD_R_IMPORT', os.path.normpath(os.path.join(input_path, '../')))

            # Import 를 위한 Thread 실행
            self.last_path = input_path
            self.file_io_job_start.emit('Importing RAD-R...')
            self.import_thread = ImportRadRWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_rad_r_data failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def import_mgeo_geojson(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('EXPORT_GEOJSON')
            Logger.log_trace('import_mgeo_geojson_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains MGeo GeoJSON data',\
                 init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks | QFileDialog.DontUseNativeDialog)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import MGeo GeoJSON from: {}'.format(input_path))

            # 실제 import한 경로보다 한 경로 위를 저장
            self.update_file_path_config('EXPORT_GEOJSON', os.path.normpath(os.path.join(input_path, '../')))

            # Import 를 위한 Thread 실행
            self.last_path = input_path
            self.file_io_job_start.emit('Importing MGeo GeoJSON...')
            self.import_thread = ImportMGeoGeojsonWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_rad_r_data failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def export_apollo(self):
        try:
            init_save_path = self.get_path_from_config('EXPORT_APOLLO')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_file_name = QFileDialog.getSaveFileName(
                QFileDialog(), 
                caption='Save Apollo xml file as', 
                directory=init_save_path, 
                initialFilter='.xml', 
                filter='OpenDRIVE (*.xml)',
                options = QFileDialog.DontUseNativeDialog )[0]
        

            if (save_file_name == '' or save_file_name == None):
                Logger.log_error('invalid save_file_name (your input: {})'.format(save_file_name))
                return
                
            Logger.log_trace('save xodr file as {}'.format(save_file_name))

            # STEP #3: Write into an xodr file
            
            xml_string = self.canvas.odr_data.to_xml_string_apollo()
            self.canvas.odr_data.write_xml_string_to_file(save_file_name, xml_string)

            # export한 경로를 저장
            export_path = os.path.dirname(save_file_name)
            self.update_file_path_config('EXPORT_ODR', export_path)
        
        except BaseException as e:
            Logger.log_error('export_odr failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def export_odr(self):
        try:
            init_save_path = self.get_path_from_config('EXPORT_ODR')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_file_name = QFileDialog.getSaveFileName(
                QFileDialog(), 
                caption='Save OpenDRIVE file as', 
                directory=init_save_path, 
                initialFilter='.xodr', 
                filter='OpenDRIVE (*.xodr)',
                options = QFileDialog.DontUseNativeDialog )[0]
        

            if (save_file_name == '' or save_file_name == None):
                Logger.log_error('invalid save_file_name (your input: {})'.format(save_file_name))
                return
                
            Logger.log_trace('save xodr file as {}'.format(save_file_name))

            # STEP #3: Write into an xodr file after checking its validity
            xml_string = self.canvas.odr_data.to_xml_string()
            if '.xodr' not in save_file_name.casefold():
                save_file_name += '.xodr'
            self.canvas.odr_data.write_xml_string_to_file(save_file_name, xml_string)

            # export한 경로를 저장
            export_path = os.path.dirname(save_file_name)
            self.update_file_path_config('EXPORT_ODR', export_path)
        
        except BaseException as e:
            Logger.log_error('export_odr failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def export_csv(self):
        try:
            init_save_path = self.get_path_from_config('EXPORT_CSV')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            edit_widget = self.canvas.open_export_csv_option()
            edit_widget.showDialog()
            # isMergeData, isLink, isLaneMarking = self.canvas.open_export_csv_option()

            if edit_widget.result()>0:
                isMergeData = edit_widget.isMergeAlldata
                isLink = edit_widget.isLink
                isLaneMarking = edit_widget.isLaneMarking
            else:
                return
            
            save_path_name = QFileDialog.getExistingDirectory(QFileDialog(),'Save CSV file as', init_save_path)
            
            if save_path_name == '':
                return

            self.update_file_path_config('EXPORT_CSV', save_path_name)
                      
            self.file_io_job_start.emit('Exporting data...')
            Logger.log_trace('Export Csv to: {}'.format(save_path_name))
            self.export_thread = ExportCsvWorker(self.mgeo_planner_map, save_path_name, isMergeData, isLink, isLaneMarking)
            self.export_thread.job_finished.connect(self.export_finished)
            self.export_thread.start()

        except BaseException as e:
            Logger.log_error('export_csv failed (traceback is down below) \n{}'.format(traceback.format_exc()))
            
    
    def export_obj(self):
        try:
            init_save_path = self.get_path_from_config('EXPORT_OBJ')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder to save obj file', 
                        init_save_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks | QFileDialog.DontUseNativeDialog)

            if (save_path == '' or save_path == None):
                Logger.log_error('invalid save_path (your input: {})'.format(save_path))
                return
                
            Logger.log_trace('save obj file as {}'.format(save_path))

            self.update_file_path_config('EXPORT_OBJ', os.path.normpath(os.path.join(save_path, '../')))

            self.file_io_job_start.emit('Exporting data...')
            Logger.log_trace('Export Obj to: {}'.format(save_path))

            self.export_thread = ExportObjWorker(self.mgeo_planner_map, save_path)
            self.export_thread.job_finished.connect(self.export_finished)
            self.export_thread.start()
        
        except BaseException as e:
            Logger.log_error('export_obj failed (traceback is down below) \n{}'.format(traceback.format_exc()))
            
    
    def export_geojson(self):
        try:
            init_save_path = self.get_path_from_config('EXPORT_GEOJSON')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))
            
            save_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder to save geoJSON data into', 
                        init_save_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks | QFileDialog.DontUseNativeDialog)

            if (save_path == '' or save_path == None):
                Logger.log_error('invalid save_path (your input: {})'.format(save_path))
                return
                
            Logger.log_trace('save geojson file as {}'.format(save_path))
            
            self.update_file_path_config('EXPORT_GEOJSON', os.path.normpath(os.path.join(save_path, '../')))

            self.file_io_job_start.emit('Exporting data...')
            Logger.log_trace('Export GeoJson to: {}'.format(save_path))

            self.export_thread = ExportGeoJsonWorker(self.canvas.mgeo_maps_dict, save_path)
            self.export_thread.job_finished.connect(self.export_finished)
            self.export_thread.start()
        
        except BaseException as e:
            Logger.log_error('export_odr failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    # tempy
    def export_path_csv(self):
        try:
            from lib.widget.select_export_path_csv import SelectExportPathCSV
            select_export_path = SelectExportPathCSV()
            export_type = select_export_path.showDialog()
            
            init_save_path = self.get_path_from_config('EXPORT_PATH_CSV')
            save_file_name = QFileDialog.getSaveFileName(
                QFileDialog(),
                caption = "Save CSV file as",
                directory = init_save_path,
                initialFilter = '.csv',
                filter='Path (*.csv)')[0]
            
            if (save_file_name == '' or save_file_name == None):
                Logger.log_error('invalid save_file_name (your input: {})'.format(save_file_name))
                return

            if export_type != 1:
                return
            else:
                if select_export_path.check1:
                    self.canvas.export_path_to_csv('link_list', save_file_name)
                elif select_export_path.check2:
                    self.canvas.export_path_to_csv('list_point_enu', save_file_name)
                elif select_export_path.check3:
                    self.canvas.export_path_to_csv('list_point_ll', save_file_name)
                  
        except BaseException as e:
            Logger.log_error('export_path_csv (traceback is down below) \n{}'.format(traceback.format_exc()))
    
    
    def export_oicd(self):
        try:
            init_save_path = self.get_path_from_config('EXPORT_OICD')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_file_name = QFileDialog.getSaveFileName(
                QFileDialog(), 
                caption='Save OICD file as', 
                directory=init_save_path, 
                initialFilter='.oicd', 
                filter='OICD (*.oicd)',
                options = QFileDialog.DontUseNativeDialog )[0]
        

            if (save_file_name == '' or save_file_name == None):
                Logger.log_error('invalid save_file_name (your input: {})'.format(save_file_name))
                return
                
            Logger.log_trace('save oicd file as {}'.format(save_file_name))

            # STEP #3: Write into an oicd file
            # TODO
            # xml_string = self.canvas.odr_data.to_xml_string()
            # self.canvas.odr_data.write_xml_string_to_file(save_file_name, xml_string)

            # export한 경로를 저장
            export_path = os.path.dirname(save_file_name)
            self.update_file_path_config('EXPORT_OICD', export_path)
        
        except BaseException as e:
            Logger.log_error('export_oicd failed (traceback is down below) \n{}'.format(traceback.format_exc()))
            
            

    def export_finished(self):
        try:
            self.export_thread.quit()

            Logger.log_info("Successfully exported to: {}".format(self.export_thread.output_path))
    
        except BaseException as e:
            Logger.log_error('export_finished failed (traceback is down below) \n{}'.format(traceback.format_exc()))            
        
        finally:
            if self.export_thread.isRunning():
                self.export_thread.terminate()
                self.export_thread.wait()
                
            self.file_io_job_finished.emit()
            del self.export_thread

            if self.next_job != None :
                self.next_job(**self.next_job_args)
                self.next_job = None
                self.next_job_args = None

    

    def find_all_duplicates(self, base_mgeo, add_mgeo):
        try:
            Logger.log_trace('Find all duplicates') 
            for idx, node in base_mgeo.node_set.nodes.items():
                for compare_idx, compare_node in add_mgeo.node_set.nodes.items():
                    if idx == compare_idx:
                        add_mgeo.node_set.nodes.pop(compare_idx)
            
            for idx, link in base_mgeo.link_set.lines.items():
                for compare_idx, compare_link in add_mgeo.link_set.lines.items():
                    if idx == compare_idx:
                        add_mgeo.link_set.lines.pop(compare_idx)
            
            for idx, sign in base_mgeo.sign_set.signals.items():
                for compare_idx, compare_link in add_mgeo.sign_set.signals.items():
                    if idx == compare_idx:
                        add_mgeo.sign_set.signals.pop(compare_idx)
            
            for idx, light in base_mgeo.light_set.signals.items():
                for compare_idx, compare_link in add_mgeo.light_set.signals.items():
                    if idx == compare_idx:
                        add_mgeo.light_set.signals.pop(compare_idx)
                        
            for idx, junction in base_mgeo.junction_set.junctions.items():
                for compare_idx, compare_link in add_mgeo.junction_set.junctions.items():
                    if idx == compare_idx:
                        add_mgeo.junction_set.junctions.pop(compare_idx) 
            
            for idx, lane_node in base_mgeo.lane_node_set.nodes.items():
                for compare_idx, compare_link in add_mgeo.lane_node_set.nodes.items():
                    if idx == compare_idx:
                        add_mgeo.lane_node_set.nodes.pop(compare_idx)
                        
            for idx, lane_boundary in base_mgeo.lane_boundary_set.lanes.items():
                for compare_idx, compare_link in add_mgeo.lane_boundary_set.lanes.items():
                    if idx == compare_idx:
                        add_mgeo.lane_boundary_set.lanes.pop(compare_idx)
            
            return add_mgeo
            
        except BaseException as e:
            Logger.log_error('find_all_duplicates Failed')
    
    
    def merge_mgeo(self, import_action_list):
        Logger.log_trace('Called: Merge Mgeo')
        try:
            map_dict_window = SelectMgeoMap(self.canvas.mgeo_maps_dict)
            return_map_dict_window = map_dict_window.showDialog()
            
            if return_map_dict_window != 1:
                return
            else:
                if len(map_dict_window.check_list) <= 1:
                    Logger.log_error("Please select two maps to merge at least")
                    return
                else:
                    merge_dict = {checked: self.mgeo_maps_dict[checked] for checked in map_dict_window.check_list if checked in self.mgeo_maps_dict}
                    
                    new_mgeo = MGeo()
                    base_data = list(merge_dict.values())[0]
                    
                    for mgeo in merge_dict.values():
                        
                        if base_data == mgeo:
                            continue
                        
                        else:
                            add_mgeo = self.find_all_duplicates(base_data, mgeo)
                            new_mgeo.node_set.nodes = {**base_data.node_set.nodes, **add_mgeo.node_set.nodes}
                            new_mgeo.link_set.lines = {**base_data.link_set.lines, **add_mgeo.link_set.lines}
                            new_mgeo.sign_set.signals = {**base_data.sign_set.signals, **add_mgeo.sign_set.signals}
                            new_mgeo.light_set.signals = {**base_data.light_set.signals, **add_mgeo.light_set.signals}
                            new_mgeo.junction_set.junctions = {**base_data.junction_set.junctions, **add_mgeo.junction_set.junctions}
                            new_mgeo.lane_boundary_set.lanes = {**base_data.lane_boundary_set.lanes, **add_mgeo.lane_boundary_set.lanes}
                            new_mgeo.lane_node_set.nodes = {**base_data.lane_node_set.nodes, **add_mgeo.lane_node_set.nodes}
                            new_mgeo.sm_set.data = {**base_data.sm_set.data, **add_mgeo.sm_set.data}
                            new_mgeo.scw_set.data = {**base_data.scw_set.data, **add_mgeo.scw_set.data}

                            new_mgeo.cw_set.data = {**base_data.cw_set.data, **add_mgeo.cw_set.data}
                            new_mgeo.synced_light_set.synced_signals = {**base_data.synced_light_set.synced_signals, **add_mgeo.synced_light_set.synced_signals}
                            new_mgeo.intersection_controller_set.intersection_controllers = {**base_data.intersection_controller_set.intersection_controllers, **add_mgeo.intersection_controller_set.intersection_controllers}

                            base_data = new_mgeo
                    
                    Logger.log_trace("Merged Map was created")
                    self.mgeo_maps_dict["merge_mgeo"] = base_data
                    

            self.canvas.setMGeoPlannerMap(self.mgeo_maps_dict)
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
            self.command_manager.clear()

        except BaseException as e:
            Logger.log_error('merge_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    """
    시뮬레이터 데이터 출력하기
    """
    # 차선 관련 
    def simplify_lane_markings(self):
        Logger.log_trace("Called: simplify_lane_markings")
        
        if len(self.mgeo_maps_dict) == 0:
            Logger.log_warning(self, "Error", "Please Add the Map Data")
            return
        else:
            cmd_simplify_lane_boundary = SimplifyLaneBoundary(self.canvas)
            self.command_manager.execute(cmd_simplify_lane_boundary)
            
    def fill_points_in_lane_markings(self):
        Logger.log_trace("Called: fill_points_in_lane_markings")
        step_len = 0.1
        # result, ok = QInputDialog.getText(self.canvas, 'fill points in lane marking', 'Enter step len', QLineEdit.Normal, '0.1')
        from lib.widget.select_fill_points_window import SelectFillPointsWindow
        select_widget = SelectFillPointsWindow()
        select_widget.showDialog()
        if select_widget.result() > 0:
            points_keep = False
            try:
                result = select_widget.step_length.text()
                if select_widget.no_erasing_points.isChecked():
                    points_keep = True
                step_len = float(result)
            except BaseException as e:
                Logger.log_error('Failed to Filled points in selected lanes: {}'.format(e))
                return

            if len(self.mgeo_maps_dict) == 0:
                Logger.log_warning(self, "Error", "Please Add the Map Data")
                return 
            else:
                cmd_fill_points_in_all_laneboundary = FillPointsInAllLaneBoundary(self.canvas, step_len, points_keep)
                self.command_manager.execute(cmd_fill_points_in_all_laneboundary)

    def export_sim_data(self, export_type):
        try:
            init_save_path = self.get_path_from_config('MGEO_SAVE')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder to save {} mesh data into'.format(export_type), 
                        init_save_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks  | QFileDialog.DontUseNativeDialog)

            if save_path == '' or save_path == None:
                Logger.log_error('invalid save_path (your input: {})'.format(save_path))
                return

            Logger.log_trace('save {} mesh data into: {}'.format(export_type, save_path))
            
            # 선택된 Key를 들고 온다
            mgeo_key = self.canvas.mgeo_key
            result = None

            if export_type == 'Road':
                result, ok = QInputDialog.getText(self.canvas, 'Point interval for road mesh output', 'Enter step len (m)', QLineEdit.Normal, '')
                if ok == False:
                    return
            elif export_type == 'Lane':
                export_lane_widget = SelectExportLaneWindow()
                return_export_lane = export_lane_widget.showDialog()

                result = {'lane_height' : 0.003, 'lane' : False, 'crosswalk' : False, 'stopline' : False}

                if return_export_lane != 1:
                    return
                else:
                    try:
                        lane_height = float(export_lane_widget.lane_height.text())
                    except:
                        lane_height = 0

                    result['lane_height'] = lane_height
                    result['lane'] = export_lane_widget.normal_lane.isChecked()
                    result['crosswalk'] = export_lane_widget.crosswalk.isChecked()
                    result['stopline'] = export_lane_widget.stop_lane.isChecked()

            self.file_io_job_start.emit('Exporting data...')

            self.export_thread =  ExportSimDataWorker(self.mgeo_maps_dict, save_path, mgeo_key, export_type, result)
            self.export_thread.job_finished.connect(self.export_finished)
            self.export_thread.start()

        except BaseException as e:
            Logger.log_error('export_{}_mesh failed (traceback is down below) \n{}'.format(export_type, traceback.format_exc()))
    

    def export_link_as_csv(self, filepath):
        if os.path.exists(filepath):
            print('[WARNING] Removing an existing file... ({})'.format(filepath))
            os.remove(filepath)

        export_link_as_csv(self.mgeo_planner_map, filepath)
    

    def export_lane_marking_as_csv(self, filepath):
        if os.path.exists(filepath):
            print('[WARNING] Removing an existing file... ({})'.format(filepath))
            os.remove(filepath)

        export_lane_marking_as_csv(self.mgeo_planner_map, filepath)
    
    
    def export_all_lines_as_csv(self, isLink, isLaneMarking, filepath):
        if os.path.exists(filepath):
            print('[WARNING] Removing an existing file... ({})'.format(filepath))
            os.remove(filepath)
        
        if isLink:
            export_link_as_csv(self.mgeo_planner_map, filepath)

        if isLaneMarking:
            export_lane_marking_as_csv(self.mgeo_planner_map, filepath)
        
    
    def export_osm(self, feature_sets_osm):
        try:
            init_save_path = self.get_path_from_config('EXPORT_OSM')
            Logger.log_trace('init_save_path: {}'.format(init_save_path))

            save_file_name = QFileDialog.getSaveFileName(
                QFileDialog(), 
                caption='Save OpenDRIVE file as', 
                directory=init_save_path, 
                initialFilter='.osm', 
                filter='Lanelet2 (*.osm)')[0]
        

            if (save_file_name == '' or save_file_name == None):
                Logger.log_error('invalid save_file_name (your input: {})'.format(save_file_name))
                return
                
            Logger.log_trace('save osm file as {}'.format(save_file_name))

            # STEP #3: Write into an osm file
            feature_sets_osm.initData(save_file_name)

            # export한 경로를 저장
            export_path = os.path.dirname(save_file_name)
            self.update_file_path_config('EXPORT_OSM', export_path)
        
        except BaseException as e:
            Logger.log_error('export_odr failed (traceback is down below) \n{}'.format(traceback.format_exc()))
    
    def import_kakaomobility(self, import_action_list):
        try:
            init_import_path = self.get_path_from_config('KAKAOMOBILITY_MAP_IMPORT')
            Logger.log_trace('init_import_path: {}'.format(init_import_path))

            input_path = QFileDialog.getExistingDirectory(QFileDialog(), 'Select a folder that contains kakaomobility hdmap data', 
                        init_import_path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
                        
            if (input_path == '' or input_path == None):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            Logger.log_trace('import kakaomobility hdmap data from: {}'.format(input_path))

            # Config 파일 업데이트 (최근 파일 경로 저장, 한 단계 위 경로 저장)
            self.update_file_path_config('KAKAOMOBILITY_MAP_IMPORT',
                os.path.normpath(os.path.join(input_path, '../')))
            
            self.file_io_job_start.emit('Importing data...')
            Logger.log_trace('Import Kakaomobility data from: {}'.format(input_path))
            
            # Import 를 위한 Thread 실행
            self.last_path = input_path                  #import_data_finished 에서 사용
            self.import_thread = ImportKakaomobilityWorker(input_path, import_action_list)
            self.import_thread.job_finished.connect(self.import_data_finished)
            self.import_thread.start()

        except BaseException as e:
            Logger.log_error('import_kakaomobility failed (traceback is down below) \n{}'.format(traceback.format_exc()))
