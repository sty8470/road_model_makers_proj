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
import re
# import win32com.client # TEMP(sglee): 임시로 주석처리

from lib.common import path_utils

from lib.common.aes_cipher import AESCipher
from lib.common.logger import Logger

from lib.common.json_util import json_util


def build(release_version = None):     
    """ 이번 릴리즈를 출력할 경로 생성 """
    
    prj_root_path = os.path.normpath(os.path.join(current_path, '../../../'))

    release_root_path = os.path.normpath(os.path.join(current_path, '../../../z_release'))
    folder_name = 'map_viewer_{}'.format(path_utils.get_now_str(include_sec=True))
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
    dst_user_path = os.path.abspath(os.path.join(package_proj_path, 'dist/sign_in_window/proj_mgeo_editor_morai_opengl', 'User.json'))
    about_path = os.path.abspath(os.path.join(package_proj_path, 'dist/sign_in_window/proj_mgeo_editor_morai_opengl', 'about.json'))
    mgeo_editor_path = os.path.abspath(os.path.join(current_path, '../../proj_mgeo_editor_morai_opengl'))
    src_user_path = os.path.abspath(os.path.join(mgeo_editor_path, 'GUI', 'Users', 'User_sim.json'))


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

    if release_version is not None:
        program_name = json_util.instnace().getValue(src_user_path, 'program_name')
        program_name_split = re.split(r'[(v,)]', program_name)
        program = str.strip(program_name_split[0])
        version = str.strip(program_name_split[2])
        if version == release_version:
            pass
        else:
            new_program_name = str.format('{} (v{})', program, release_version)

            json_util.instnace().setValue(src_user_path, 'program_name', new_program_name)


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


    # """ Delete Config Files for License Management """
    # config_file_license_management = os.path.normpath(os.path.join(prj_root_path,\
    #     'src/proj_mgeo_editor_license_management/setting.json'))
    # os.remove(config_file_license_management)


    # """ License 프로그램 Config 복사 """
    # src = os.path.normpath(os.path.join(prj_root_path, 'src/proj_mgeo_editor_license_management/setting.json'))
    dst = os.path.normpath(os.path.join(license_management_path, 'setting.json'))
    path_utils.make_dir_if_not_exist(license_management_path)
    # shutil.copy(src, dst)


    # TEMP(sglee): 임시로 주석처리
    # """ 바로가기 """
    # print('[INFO] Creating Shortcut...')
    # try:
    #     os.chdir(release_path)
    #     if platform.system() == "Windows":

    #         path = os.path.join(release_path, program_name + '.lnk')
    #         destination = os.path.join(release_path, "program\MapViewer.exe")
    #         icon = os.path.join(release_path, "program\map.ico")
            
    #         print('\tDeploying shortcut at: {}.'.format(path))

    #         try:
    #             ws = win32com.client.Dispatch("wscript.shell")
    #             shortcut = ws.CreateShortCut(path)
    #             shortcut.TargetPath = destination
    #             shortcut.WorkingDirectory = os.path.join(release_path, "program")
    #             shortcut.IconLocation = icon
    #             shortcut.Save()
    #         except Exception as exception:
    #             error = 'Failed to deploy shortcut! {}\nArgs: {}, {}'.format(exception, path, destination)
    #             print(error)

    #         # exe_program_name = program_name + '.exe'
    #         # command = str.format('mklink "{}" ".\program\mgeo_mscenario_editor_sim.exe"', exe_program_name)
    #         # os.system(command)
    #         # os.system('mklink "mgeo_mscenario_editor_internal.exe " ".\program\mgeo_mscenario_editor_internal.exe"')
    #     elif platform.system() == "Linux":
    #         # os.system('ln -s ./program/release_mgeo_mscenario_editor_internal')
    #         release_program_name = 'release_' + program_name
    #         os.system('ln -s ./program/'+ release_program_name)
    #     else:
    #         print('[ERROR] Unsupported platform : {}'.format(platform.system()))
    # except Exception as e:
    #     print('[ERROR] Creating Shortcut... Failed', e)
    #     return        
    # print('[INFO] Creating Shortcut... Done')

    #################### 프로그램 빌드 완료 ####################


    #################### 데이터 복사 시작 ####################


    """경로 생성"""
    release_data_path = os.path.normpath(os.path.join(release_path, 'data'))
    release_data_mgeo_path = os.path.normpath(os.path.join(release_data_path, 'mgeo'))

    path_utils.make_dir_if_not_exist(release_data_path)
    path_utils.make_dir_if_not_exist(release_data_mgeo_path)


    """data 파일 복사"""
    



    
    

    """MGeo 파일 복사"""


    #################### 데이터 복사 완료 ####################


    #################### 다른 Release용 Config 파일 삭제 시작 ####################


    # config_file_io_MORAI_internal = os.path.normpath(os.path.join(program_path,\
    #     'proj_mgeo_editor_morai_opengl/GUI/config_file_io_default_MORAI.json'))
    # os.remove(config_file_io_MORAI_internal)

    # 내부용 파일 삭제
    # config_file_io_MORAI_internal = os.path.normpath(os.path.join(program_path,\
    #     'proj_mgeo_editor_morai_opengl/GUI/config_file_io_default_internal.json'))
    # os.remove(config_file_io_MORAI_internal)

    # Release용 파일을 Internal용 이름으로 변경 (User.json 파일을 동일하게 사용하도록)
    # src = os.path.normpath(os.path.join(program_path,\
    #     'proj_mgeo_editor_morai_opengl/GUI/config_file_io_default_internal_Release.json'))
    # dst = os.path.normpath(os.path.join(program_path,\
    #     'proj_mgeo_editor_morai_opengl/GUI/config_file_io_default_internal.json'))
    # os.rename(src, dst)

    #################### 다른 Release용 Config 파일 삭제 완료 ####################

    # 압축파일생성
    if platform.system() == "Windows":
        all_files = os.path.join(release_path, '*')
        cmd = '7z a -tzip {}.zip {}'.format(release_path, all_files)

        print('[INFO] Zipping the output... cmd >> {}'.format(cmd))
        ret = os.system(cmd)
        if ret != 0:
            print('[ERROR] Zipping failed (return: {})'.format(ret))
            return 
        else:
            print('[INFO] Zipping done successfully.') 
    if platform.system() == "Linux":
        os.system('tar zcvf {}.tgz data program mgeo_mscenario_editor_sim'.format(folder_name))
    

    print('[INFO] Done (Output Path: {})'.format(release_path))


if __name__ == "__main__":
    # 7z 실행되는지 테스트 해볼 것
    # os.system('7z')
    if sys.argv.__len__() > 1:
        release_version = sys.argv[1]
        # os_type = '0.3'
        build(release_version)
    else:
        build()
