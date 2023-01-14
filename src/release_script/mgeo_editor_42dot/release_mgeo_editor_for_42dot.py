from ntpath import join
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
from lib.common.logger import Logger


def build(): 
    release_root_path = os.path.normpath(os.path.join(current_path, '../../../z_release'))
    folder_name = 'map_editor_42dot_{}'.format(path_utils.get_now_str(include_sec=True))

    if platform.system() == "Windows":
        folder_name += '_win' 
    if platform.system() == "Linux":
        folder_name += '_linux'     
    release_path = os.path.normpath(os.path.join(release_root_path, folder_name))
    
    program_path = os.path.normpath(os.path.join(release_path, 'program'))
    license_management_path = os.path.normpath(os.path.join(release_path, 'program/proj_mgeo_editor_license_management'))
    print('[INFO] Release Path: {}'.format(release_path))

    """ 패키징 프로젝트 경로 생성 """
    package_proj_path = os.path.abspath(os.path.join(current_path, '../../proj_mgeo_editor_license_management'))

    # 임시로 빌드되는 경로
    dst_user_path = os.path.abspath(os.path.join(package_proj_path, 'dist/sign_in_window/proj_mgeo_editor_42dot', 'User.json'))
    about_path = os.path.abspath(os.path.join(package_proj_path, 'dist/sign_in_window/proj_mgeo_editor_42dot', 'about.json'))
    mgeo_editor_path = os.path.abspath(os.path.join(current_path, '../../proj_mgeo_editor_42dot'))
    src_user_path = os.path.abspath(os.path.join(mgeo_editor_path, 'GUI', 'Users', 'User_42dot.json'))

    #################### 프로그램 빌드 시작 ####################


    """ 패키징을 위해 spec 파일 복사 """
    spec_file_path = os.path.join(package_proj_path, 'sign_in_window.spec')
    shutil.copy(os.path.join(current_path, 'sign_in_window.spec'), spec_file_path)
    print('[INFO] Copy spec file: {}'.format(spec_file_path))


    """ PyInstaller 를 이용한 패키징 """
    print('[INFO] PyInstaller...')
    try:
        os.chdir(package_proj_path)
        return_value = os.system('pyinstaller --noconfirm {}'.format(spec_file_path))
        print('[INFO] pyinstaller result: {}'.format(return_value))
    except BaseException as e:
        Logger.log_error('pyinstaller error -> {}'.format(e))


    """ spec 파일 삭제 """
    print('[INFO] remove spec file: {}'.format(spec_file_path))
    os.remove(spec_file_path)


    """ User 파일 복사 """
    print('[INFO] Copy user file: {} to {}'.format(src_user_path, dst_user_path))
    aes_cipher = AESCipher()
    aes_cipher.encrypt_file(src_user_path, dst_user_path)


    """ About 파일 생성 """
    about_contents = {}
    about_contents['Build Time'] = str(datetime.datetime.now())
    print('[INFO] about : {}'.format(str(about_contents)))
    try:
        with open(about_path, 'w') as f:
            json.dump(about_contents, f, indent=2)
    except:
        print('[ERROR] Failed to create the about info file')


    """ 파일 Copy """
    src = os.path.normpath(os.path.join(package_proj_path, 'dist/sign_in_window/'))
    print('[INFO] Copy Package files {} to {}'.format(src, release_path))
    shutil.copytree(src, program_path)
    print('[INFO] Copy Finished.')

    # """ License 프로그램 Config 복사 """
    # src = os.path.normpath(os.path.join(prj_root_path, 'src/proj_mgeo_editor_license_management/setting.json'))
    dst = os.path.normpath(os.path.join(license_management_path, 'setting.json'))
    path_utils.make_dir_if_not_exist(license_management_path)


    # """경로 생성"""
    # release_data_path = os.path.normpath(os.path.join(release_path, 'data'))
    # release_data_mgeo_path = os.path.normpath(os.path.join(release_data_path, 'mgeo'))

    # path_utils.make_dir_if_not_exist(release_data_path)
    # path_utils.make_dir_if_not_exist(release_data_mgeo_path)


    # # 압축파일생성
    # if platform.system() == "Windows":
    #     all_files = os.path.join(release_path, '*')
    #     cmd = '7z a -tzip {}.zip {}'.format(release_path, all_files)

    #     print('[INFO] Zipping the output... cmd >> {}'.format(cmd))
    #     ret = os.system(cmd)
    #     if ret != 0:
    #         print('[ERROR] Zipping failed (return: {})'.format(ret))
    #         return 
    #     else:
    #         print('[INFO] Zipping done successfully.') 
    # if platform.system() == "Linux":
    #     os.system('tar zcvf {}.tgz data program mgeo_mscenario_editor_sim'.format(folder_name))
    

    print('[INFO] Done (Output Path: {})'.format(release_path))

if __name__ == "__main__":
    # 7z 실행되는지 테스트 해볼 것
    # os.system('7z')
    build()
