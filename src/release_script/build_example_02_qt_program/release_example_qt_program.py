import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) 
sys.path.append(os.path.normpath(os.path.join(current_path, '../../'))) 

import platform
import json
import datetime
import shutil

from lib.common import path_utils
from lib.common.aes_cipher import AESCipher
from lib.common.json_util import json_util


"""프로젝트 Root 경로"""
prj_root_path = os.path.normpath(os.path.join(current_path, '../../../'))


"""빌드하려는 프로그램 경로"""
src_path = os.path.normpath(os.path.join(prj_root_path, 'src/test_build_example_02_qt_program'))
print('[INFO] Program Source Path: {}'.format(src_path))


"""pyinstaller에 의해 생성되는 임시 빌드 경로"""
build_path = os.path.normpath(os.path.join(src_path, 'build'))
dist_path = os.path.normpath(os.path.join(src_path, 'dist'))


def build():
    """
    빌드하기
    """
    if platform.system() != "Windows":
        raise BaseException('Build only supports windows currently.')

    program_name = 'scenario_runner'
    release_root_path = os.path.normpath(os.path.join(current_path, '../../../z_release'))
    
    folder_name = program_name + '_{}'.format(path_utils.get_now_str(include_sec=True))
    if platform.system() == "Windows":
        folder_name += '_win' 
    if platform.system() == "Linux":
        folder_name += '_linux'    
    release_path = os.path.normpath(os.path.join(release_root_path, folder_name))
    print('[INFO] Release Path: {}'.format(release_path))


    """ PyInstaller 를 이용한 패키징 """
    print('[INFO] PyInstaller...')
    os.chdir(src_path)
    
    spec_file_path = os.path.normpath(os.path.join(src_path, 'example_qt_program.spec'))
    ret_val = os.system('pyinstaller --noconfirm {}'.format(spec_file_path))
    if ret_val != 0:
        print('[ERROR] Build failed.\n')
    else:
        print('[INFO] Build using pyinstaller is done successfully.')


def clean():    
    print('[INFO] Deleting build_path: {}'.format(build_path))
    if os.path.exists(build_path):
        shutil.rmtree(build_path)
        print('[INFO] build_path is deleted successfully.')
    else:
        print('[INFO] build_path does not exist -> skipped.')

    print('[INFO] Deleting dist_path: {}'.format(dist_path))
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
        print('[INFO] dist_path is deleted successfully.')
    else:
        print('[INFO] dist_path does not exist -> skipped.')


if __name__ == "__main__":
    clean()
    build()
    