import os 
import sys

from numpy.lib.type_check import isreal

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.mgeo.class_defs import *

import unittest.lib.test_check_mgeo as test_check_mgeo
import unittest.lib.file_upload_download_manager as file_manager
import lib.common.path_utils as path_util
import time
import platform

from tkinter import filedialog


def release_all_data(file_path = None, is_release = False):
    fail_case = 0
    success_case = 0

    if file_path == None :
        input_path = '../../data/'
        input_path = os.path.join(current_path, input_path)
        input_path = os.path.normpath(input_path)

        file_path = filedialog.askdirectory(initialdir = input_path, 
            title = 'Load files from')
    
    file_list = os.listdir(file_path)
    
    test_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    

    for map_name in file_list:
        if map_name.__contains__('log'):
            continue
        result = release_one_mgeo_map(map_name, test_time, is_release, file_path )
        if not result['success']:
            fail_case += 1
        else:
            success_case += 1
        
    total_case = success_case + fail_case
    print('Test Finished: PASS: {}/{}, FAIL: {}/{}'.format(success_case, total_case, fail_case, total_case ))
  

def run_test_one_map(file_path = None, is_release = False): # file_path 가 None 이면 file browser 열림
    if file_path == None :
        input_path = '../../data/'
        input_path = os.path.join(current_path, input_path)
        input_path = os.path.normpath(input_path)

        file_path = filedialog.askdirectory(initialdir = input_path, 
            title = 'Load files from')
        if file_path is None or len(file_path) == 0:
            print('No input file was returned')
            return
    
    if file_path.__contains__('/'):
        map_name = file_path.split('/')[-1]
    elif file_path.__contains__('\\'):
        map_name = file_path.split('\\')[-1]
   
    test_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))

    release_one_mgeo_map(map_name, test_time, is_release, file_path)


def release_one_mgeo_map(map_name, test_time, is_release, file_path): 
    
    if map_name in file_path:
        mgeo_path = file_path
    else:
        mgeo_path = os.path.join(file_path, map_name)

    log_path = os.path.normpath(os.path.join(file_path, '../log/{}'.format(test_time)))
    log_file_name = 'log_{}_{}.log'.format(test_time, map_name)
    result = test_check_mgeo.check_mgeo_data(mgeo_path, log_path, log_file_name)

    if is_release:
        if result['success']:
            release_mgeo_file(mgeo_path, test_time, map_name)

    return result


def extract_file(file_name, file_path):
    if platform.system() == "Windows":
        cmd = '7z x {} -o{}'.format(file_name, file_path)

        ret = os.system(cmd)
        if ret != 0:
            print('[ERROR] Zipping failed (return: {})'.format(ret))
            return 
        else:
            print('[INFO] Zipping done successfully.')     


def run_test_for_all_map_with_s3(is_release = False):
    # release_one_mgeo_map('R_KR_PG_K-City', None)
    file_path = os.path.join(current_path, '../../data/temp')

    s3_file_path = 'morai_sim_map_repository/'

    file_manager.download_bucket(s3_file_path, file_path, 'morai-internal')

    # 압축풀기
    file_list = os.listdir(file_path)
    for map_name in file_list:
        if 'log' in map_name or '.zip' in map_name:
            continue
        zip_file_path = os.path.join(file_path, map_name)
        inner_file_list = os.listdir(zip_file_path)
        for file_name in inner_file_list:
            if not file_name.__contains__('.zip'):
                continue
            else:
                zip_file_name = file_name
        
        if zip_file_name is not None:
            all_path = os.path.join(zip_file_path, zip_file_name)

            extract_file(all_path, zip_file_path)
            zip_file_name = None

    release_all_data(file_path, is_release)


def run_test_for_all_map(File_path = None, is_release = False):
    release_all_data(File_path, is_release)


def release_mgeo_file(file_path, test_time, map_name):
    # zip 파일로 압축
    zip_file_name = 'mgeo_{}_{}'.format(map_name, test_time)
    
    release_path = os.path.normpath(os.path.join(file_path, zip_file_name))
    
    if platform.system() == "Windows":
        all_files = os.path.join(file_path, '*')
        cmd = '7z a -tzip {}.zip {}'.format(release_path, all_files)

        print('[INFO] Zipping the output... cmd >> {}'.format(cmd))
        ret = os.system(cmd)
        if ret != 0:
            print('[ERROR] Zipping failed (return: {})'.format(ret))
            return 
        else:
            print('[INFO] Zipping done successfully.') 
    # if platform.system() == "Linux":
    #     os.system('tar zcvf {}.tgz data program mgeo_mscenario_editor_sim'.format(folder_name))

    # s3 업로드
    s3_path = 'morai_sim_map_repository/{}/{}.zip'.format(map_name,zip_file_name)
    release_path = release_path + '.zip'
    file_manager.upload_file(release_path, 'morai-internal',  s3_path)


if __name__ == u'__main__':
    # s3에서 모든 맵을 가져와 검사
    # run_test_for_all_map_with_s3()
    
    # 로컬 폴더에있는 모든 맵을 검사
    run_test_for_all_map(File_path = None, is_release = True)

    # 로컬 폴더에있는 하나의 맵만 검사 (폴더명 반드시 맵이름이여야함)
    # run_test_one_map(file_path = None, is_release=True)
    # file_path = 'D:/Work/Maps/morai_map_editor/data/mgeo/release/V_RHT_Suburb_02'
    # run_test_one_map(file_path, is_release=True)