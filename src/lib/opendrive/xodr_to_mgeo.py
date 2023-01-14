import os
import sys
import json

#from lib.opendrive.xodr_parser import XodrParser

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
from lib.opendrive.xodr_converter import XodrConverter
from lib.mgeo.class_defs.mgeo import MGeo
from proj_mgeo_editor_license_management.rest_api_manager import *

from lib.common.logger import Logger
from lib.mgeo.edit.funcs import edit_road_poly

#default value
vertex_distance = 2.0
sidewalk_height = 0.15
z_tolerance = 0.1
traffic_direction = "right"

def odr_convert(conf_file, xodr_file, output_path_root):
    conf_filepath = os.path.abspath(conf_file)
    xodr_filepath = xodr_file
    output_path_mgeo = os.path.normpath(os.path.join(output_path_root, 'MgeoData'))
    output_path_obj = os.path.normpath(os.path.join(output_path_root, 'RoadMesh'))

    # output_path_root 확인
    if not os.path.isdir(output_path_root):
        # 비어있으면 경로 생성
        os.mkdir(output_path_root)
        Logger.log_trace('output_path_root is created.')

    if not os.path.isdir(output_path_mgeo):
        # 비어있으면 경로 생성
        os.mkdir(output_path_mgeo)
        Logger.log_trace('output_path_mgeo is created.')
    else:
        # MGeo 경로가 있으면, 해당 경로에 이미 데이터가 존재하는지 확인한다. 있으면 오류
        file_list = os.listdir(output_path_mgeo)
        if len(file_list) != 0:
            # 빈 폴더여야만 한다
            error_msg = 'The output path is not empty. Remove it manually first. (output path: {})'.format(output_path_mgeo)
            Logger.log_error(error_msg)
            raise BaseException(error_msg)
        else:
            Logger.log_trace('output_path_mgeo is checked OK.')

    if not os.path.isdir(output_path_obj):
        # 비어있으면 경로 생성
        os.mkdir(output_path_obj)
        Logger.log_trace('output_path_obj is created.')
    else:
        # MGeo 경로가 있으면, 해당 경로에 이미 데이터가 존재하는지 확인한다. 있으면 오류
        file_list = os.listdir(output_path_obj)
        if len(file_list) != 0:
            # 빈 폴더여야만 한다
            error_msg = 'The output path is not empty. Remove it manually first. (output path: {})'.format(output_path_obj)
            Logger.log_error(error_msg)
            raise BaseException(error_msg)
        else:
            Logger.log_trace('output_path_obj is checked OK.')

    if os.path.isfile(conf_filepath):
        with open(conf_filepath, 'r') as f:
            config = json.load(f)
            if 'vertex_distance' in config :
                vertex_distance = float(config['vertex_distance'])
            if 'sidewalk_height' in config :
                sidewalk_height = float(config['sidewalk_height'])
            if 'z_tolerance' in config :
                z_tolerance = float(config['z_tolerance'])
            if 'traffic_direction' in config :
                traffic_direction = config['traffic_direction']

    converter = XodrConverter(xodr_filepath)
    converter.set_vertex_distance(vertex_distance)      #default : 2.0
    converter.set_sidewalk_height(sidewalk_height)      #default : 0.0
    converter.set_z_tolerance(z_tolerance)
    converter.set_traffic_direction(traffic_direction)
    mgeo = converter.convert_to_mgeo()

    mgeo.to_json(output_path_mgeo)
    edit_road_poly.road_poly_to_obj(mgeo.road_polygon_set, output_path_obj)

#TODO : 파일로 저장 obj, mgeo
#입력 : XODR 파일, 설정 파일 또는 커맨드, 출력 파일 경로
#출력 : obj, mgeo json 파일

def remove_allfile(dir):
    if os.path.exists(dir):
        for f in os.scandir(dir):
            os.remove(f.path)
    else:
        os.mkdir(dir)

if __name__ == '__main__':    
    # call sign in api
    Logger.log_info("======= demo odr support =======")
    
    inst = RestApiManager.instance()
    while(True):
        Logger.log_info("Please enter user id: ")
        id = input()
        Logger.log_info("Please enter password: ")
        pw = input()
        result =  inst.sign_in_with_program_name(id, pw, 'odr_support_demo')
        if (result.success):
            break
        else:
            Logger.log_error('Failed to sign-in: {}'.format(result.error))   

    if len(sys.argv) < 7:        
        print("Usage: opendrive_support_program -c [config.json] -x [filename.xodr] -o [output_path]")
    else:
        conf_file = None
        xodr_file = None
        out_path = None

        arg_prev = ""
        for arg in sys.argv :
            if arg_prev == "-c":
                Logger.log_info("config file path : " + arg)
                conf_file = arg
            elif arg_prev == "-x":
                Logger.log_info("xodr file path   : " + arg)
                xodr_file = arg
            elif arg_prev == "-o":
                Logger.log_info("output file path : " + arg)
                out_path = arg
                remove_allfile(out_path)
            arg_prev = arg
        
        Logger.log_info("Please wait ...")
        odr_convert(conf_file, xodr_file, out_path)        
        
    #conf_file = 'D:\Dev\Morai\clone_develop_mgeo_editor\src\lib\opendrive\config.json'
    #conf_file = 'D:\\temp\\config.json'
    #xodr_file = "D:\\temp\\Suburb_With_Signal_3.xodr"
    #out_path = "D:\\temp\\aaa"
    #odr_convert(conf_file, xodr_file, out_path)        
    Logger.log_info("end")