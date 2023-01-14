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
from lib.common import path_utils

from lib.common.aes_cipher import AESCipher
from lib.common.logger import Logger
from lib.common.json_util import json_util


def build(release_version = None):     
    """ 이번 릴리즈를 출력할 경로 생성 """
    
    prj_root_path = os.path.normpath(os.path.join(current_path, '../../../'))

    release_root_path = os.path.normpath(os.path.join(current_path, '../../../z_release'))   
    folder_name = 'map_editor_{}'.format(path_utils.get_now_str(include_sec=True))
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
    src_user_path = os.path.abspath(os.path.join(mgeo_editor_path, 'GUI', 'Users', 'User_internal.json'))


    """ 패키징을 위해 spec 파일 복사 """
    spec_file_path = os.path.join(package_proj_path, 'sign_in_window.spec')
    shutil.copy(os.path.join(current_path, 'sign_in_window.spec'), spec_file_path)
    print('[INFO] Copy spec file: {}'.format(spec_file_path))

    """ PyInstaller 를 이용한 패키징 """
    print('[INFO] PyInstaller...')
    try:
        os.chdir(package_proj_path)
        os.system('pyinstaller --noconfirm {}'.format(spec_file_path))
    except BaseException as e:
        Logger.log_error('pyinstaller error -> {}'.format(e))

    """ spec 파일 삭제 """
    print('[INFO] remove spec file: {}'.format(spec_file_path))
    os.remove(spec_file_path)


    """ User 파일 복사 """
    print('[INFO] Copy user file: {} to {}'.format(src_user_path, dst_user_path))

    if release_version is not None:
        program_name = json_util.instnace().getValue(src_user_path, 'program_name')
        # version = program_name.split('(')[1]
        # version = version[:-1]
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
    
    
    
    # """ License 프로그램 Config 복사 """
    # src = os.path.normpath(os.path.join(prj_root_path, 'src/proj_mgeo_editor_license_management/setting.json'))
    dst = os.path.normpath(os.path.join(license_management_path, 'setting.json'))
    path_utils.make_dir_if_not_exist(license_management_path)
    # shutil.copy(src, dst)


    """ 바로가기 """
    print('[INFO] Creating Shortcut...')
    try:
        os.chdir(release_path)
        if platform.system() == "Windows":
            install_file_path = os.path.join(release_path, 'install.bat')
            shutil.copy(os.path.join(current_path, 'install.bat'), install_file_path)

        # elif platform.system() == "Linux":
        #     cmd = 'ln -s ./program/MapEditor'

        #     print('[INFO] Creating a symbolic link... cmd >> {}'.format(cmd))
        #     ret = os.system(cmd)
        #     if ret != 0:
        #         print('[ERROR] Creating a symbolic link failed (return: {})'.format(ret))
        #         return
        #     else:
        #         print('[INFO] Creating a symbolic link done successfully.')
            
        else:
            print('[ERROR] Unsupported platform : {}'.format(platform.system()))

    except Exception as e:
        print('[ERROR] Creating Shortcut... Failed', e)
        return
        
    print('[INFO] Creating Shortcut... Done')

    #################### 프로그램 빌드 완료 ####################


    #################### 데이터 복사 시작 ####################


    """경로 생성"""
    release_data_path = os.path.normpath(os.path.join(release_path, 'data'))
    release_data_mgeo_path = os.path.normpath(os.path.join(release_data_path, 'mgeo'))

    path_utils.make_dir_if_not_exist(release_data_path)
    path_utils.make_dir_if_not_exist(release_data_mgeo_path)


    """data 파일 복사"""
    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/tomtom_geojson_US_CA_SanFrancisco_Interstate101'))
    # dst = os.path.normpath(os.path.join(release_data_path, 'hdmap/tomtom_geojson_US_CA_SanFrancisco_Interstate101'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/tomtom_geojson_US_CA_SantaMonica'))
    # dst = os.path.normpath(os.path.join(release_data_path, 'hdmap/tomtom_geojson_US_CA_SantaMonica'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/tomtom_geojson_US_MI_FarmingtonHills'))
    # dst = os.path.normpath(os.path.join(release_data_path, 'hdmap/tomtom_geojson_US_MI_FarmingtonHills'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/42dot_mdl2009_yangjae'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/42dot_hdmap_yangjae'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/42dot_mdl2009_kcity (sdx_kcity_morai_5179 (v2.0.1))'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/42dot_hdmap_kcity'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/aict_shp_pangyo'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/aict_shp_pangyo'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/42dot_mdl2009_yangjae'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/42dot_mgeo_yangjae'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/42dot_mdl2009_kcity (sdx_kcity_morai_5179 (v2.0.1))'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/42dot_mgeo_kcity'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/42dot_mdl2102_sangam'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/42dot_mgeo_sangam'))
    # shutil.copytree(src, dst)
    
    # src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/naverlabs_geojson_pangyo'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/naverlabs_geojson_pangyo'))
    # shutil.copytree(src, dst)

    # src = os.path.normpath(os.path.join(prj_root_path, 'saved/ngii_shp_ver2_KCity'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/ngii_shp_ver2_KCity'))
    # shutil.copytree(src, dst)
    
    # src = os.path.normpath(os.path.join(prj_root_path, 'saved/ngii_shp_ver2_Seoul_Sangam'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/ngii_shp_ver2_Seoul_Sangam'))
    # shutil.copytree(src, dst)
    
    # src = os.path.normpath(os.path.join(prj_root_path, 'saved/ngii_shp2_Sejong'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/ngii_shp2_Sejong'))
    # shutil.copytree(src, dst)
    
    # src = os.path.normpath(os.path.join(prj_root_path, 'saved/ngii_shp_ver2_Daegu'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/ngii_shp_ver2_Daegu'))
    # shutil.copytree(src, dst)
    
    # src = os.path.normpath(os.path.join(prj_root_path, 'saved/ngii_shp2_Seongnam_Pangyo'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/ngii_shp2_Seongnam_Pangyo'))
    # shutil.copytree(src, dst)
    
    # src = os.path.normpath(os.path.join(prj_root_path, 'saved/rr_geojson_DefaultScene_4Way_StopSign'))
    # dst = os.path.normpath(os.path.join(release_path, 'hdmap/rr_geojson_DefaultScene_4Way_StopSign'))
    # shutil.copytree(src, dst)



    
    

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
        cmd = '7z a -tzip {}.zip {}'.format(release_path, release_path)

        print('[INFO] Zipping the output... cmd >> {}'.format(cmd))
        ret = os.system(cmd)
        if ret != 0:
            print('[ERROR] Zipping failed (return: {})'.format(ret))
            return
        else:
            print('[INFO] Zipping done successfully.') 
    if platform.system() == "Linux":
        os.system('cd {}'.format(release_path))
        os.system('tar zcvf {}.zip data program'.format(release_path))

    print('[INFO] Done (Output Path: {})'.format(release_path))


if __name__ == "__main__":
    # 7z 실행되는지 테스트 해볼 것
    # os.system('7z')
    if sys.argv.__len__() > 1:
        release_version = sys.argv[1]
        build(release_version)
    else:
        build()
    