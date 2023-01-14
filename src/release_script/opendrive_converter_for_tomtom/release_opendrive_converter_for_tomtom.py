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

from elevate import elevate
from lib.common.aes_cipher import AESCipher


def build():
    """ 이번 릴리즈를 출력할 경로 생성 """
    prj_root_path = os.path.normpath(os.path.join(current_path, '../../../'))

    release_root_path = os.path.normpath(os.path.join(current_path, '../../../z_release'))
    folder_name = 'opendrive_converter_for_tomtom_{}'.format(path_utils.get_now_str(include_sec=True))
    if platform.system() == "Windows":
        folder_name += '_win' 
    if platform.system() == "Linux":
        folder_name += '_linux' 
    release_path = os.path.normpath(os.path.join(release_root_path, folder_name))

    program_path = os.path.normpath(os.path.join(release_path, 'program'))
    license_management_path = os.path.normpath(os.path.join(release_path, 'program/proj_mgeo_editor_license_management'))
    # path_utils.make_dir_if_not_exist(program_path)
    # path_utils.make_dir_if_not_exist(license_management_path)


    print('[INFO] Release Path: {}'.format(release_path))


    """ 패키징 프로젝트 경로 생성 """
    package_proj_path = os.path.abspath(os.path.join(current_path, '../../proj_mgeo_editor_license_management'))

    # 임시로 빌드되는 경로
    dst_user_path = os.path.abspath(os.path.join(package_proj_path, 'dist/sign_in_window/proj_mgeo_editor_morai_opengl', 'User.json'))
    about_path = os.path.abspath(os.path.join(package_proj_path, 'dist/sign_in_window/proj_mgeo_editor_morai_opengl', 'about.json'))
    mgeo_editor_path = os.path.abspath(os.path.join(current_path, '../../proj_mgeo_editor_morai_opengl'))
    src_user_path = os.path.abspath(os.path.join(mgeo_editor_path, 'GUI', 'Users', 'User_TomTom.json'))


    #################### 프로그램 빌드 시작 ####################


    """ 패키징을 위해 spec 파일 복사 """
    spec_file_path = os.path.join(package_proj_path, 'sign_in_window.spec')
    shutil.copy(os.path.join(current_path, 'sign_in_window.spec'), spec_file_path)
    print('[INFO] Copy spec file: {}'.format(spec_file_path))


    """ PyInstaller 를 이용한 패키징 """
    os.chdir(package_proj_path)
    cmd ='pyinstaller --noconfirm {}'.format(spec_file_path)
    print('[INFO] Building using PyInstaller... cmd >> {}'.format(cmd))
    ret = os.system(cmd)
    if ret != 0:
        print('[ERROR] The build process failed (return: {})'.format(ret))
        return
    else:
        print('[INFO] The build done successfully.')


    """ spec 파일 삭제 """
    print('[INFO] Remove spec file: {}'.format(spec_file_path))
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


    # """ Delete Config Files for License Management """
    # config_file_license_management = os.path.normpath(os.path.join(prj_root_path,\
    #     'src/proj_mgeo_editor_license_management/setting.json'))
    # os.remove(config_file_license_management)


    # """ License 프로그램 Config 복사 """
    # src = os.path.normpath(os.path.join(prj_root_path, 'src/proj_mgeo_editor_license_management/setting.json'))
    dst = os.path.normpath(os.path.join(license_management_path, 'setting.json'))
    path_utils.make_dir_if_not_exist(license_management_path)
    # shutil.copy(src, dst)


    #  """ Delete License 프로그램 Config 복사 """
    # config_file_license_management = os.path.normpath(os.path.join(license_management_path, 'setting.json'))
    # os.remove(config_file_license_management)
    # src = os.path.normpath(os.path.join(prj_root_path, 'src/proj_mgeo_editor_license_management/setting.json'))
    # dst = os.path.normpath(os.path.join(license_management_path, 'setting.json'))
    # path_utils.make_dir_if_not_exist(license_management_path)
    # shutil.copy(src, dst)


    """ 바로가기 """
    print('[INFO] Creating Shortcut...')
    try:
        os.chdir(release_path)
        if platform.system() == "Windows":
            install_file_path = os.path.join(release_path, 'install.bat')
            shutil.copy(os.path.join(current_path, 'install.bat'), install_file_path)

        elif platform.system() == "Linux":
            cmd = 'ln -s ./program/OpenDRIVE_Converter_for_TomTom'

            print('[INFO] Creating a symbolic link... cmd >> {}'.format(cmd))
            ret = os.system(cmd)
            if ret != 0:
                print('[ERROR] Creating a symbolic link failed (return: {})'.format(ret))
                return
            else:
                print('[INFO] Creating a symbolic link done successfully.')
            
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
    release_data_tomtom_path = os.path.normpath(os.path.join(release_data_path, 'tomtom'))
    release_data_mgeo_path = os.path.normpath(os.path.join(release_data_path, 'mgeo'))

    path_utils.make_dir_if_not_exist(release_data_path)
    path_utils.make_dir_if_not_exist(release_data_tomtom_path)
    # path_utils.make_dir_if_not_exist(release_data_mgeo_path) # tomtom_mgeo_release 내부 전체를 복사할 때는 만들면 오류난다


    """TomTom 파일 복사"""
    src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/tomtom_geojson_US_CA_SanFrancisco_Interstate101'))
    dst = os.path.normpath(os.path.join(release_data_tomtom_path, 'tomtom_geojson_US_CA_SanFrancisco_Interstate101'))
    shutil.copytree(src, dst)

    src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/tomtom_geojson_US_CA_SantaMonica'))
    dst = os.path.normpath(os.path.join(release_data_tomtom_path, 'tomtom_geojson_US_CA_SantaMonica'))
    shutil.copytree(src, dst)

    src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/tomtom_geojson_US_MI_FarmingtonHills'))
    dst = os.path.normpath(os.path.join(release_data_tomtom_path, 'tomtom_geojson_US_MI_FarmingtonHills'))
    shutil.copytree(src, dst)

    # shutil.copytree(src, dst)

    src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/tomtom_geojson_US_NV_LasVegas'))
    dst = os.path.normpath(os.path.join(release_data_tomtom_path, 'tomtom_geojson_US_NV_LasVegas'))
    shutil.copytree(src, dst)


    """MGeo 파일 복사"""

    copy_release_only = True

    if copy_release_only:
        # 참고: tomtom_release 내부 데이터 전체를, data/mgeo 내로 옮기는 방식이면, mgeo 폴더를 미리 생성하면 안 된다.
        #       shutil.copytree에서 오류 발생함.
        src = os.path.normpath(os.path.join(prj_root_path, 'data/mgeo_data/tomtom_mgeo_release'))
        dst = os.path.normpath(os.path.join(release_data_mgeo_path, 'tomtom_mgeo_release'))
        # dst = release_data_mgeo_path
        shutil.copytree(src, dst)

    else:
        src = os.path.normpath(os.path.join(prj_root_path, 'data/mgeo_data/tomtom_test_data'))
        dst = os.path.normpath(os.path.join(release_data_mgeo_path, 'tomtom_test_data'))
        shutil.copytree(src, dst)

        src = os.path.normpath(os.path.join(prj_root_path, 'data/mgeo_data/tomtom_mgeo_no_release'))
        dst = os.path.normpath(os.path.join(release_data_mgeo_path, 'tomtom_mgeo_no_release'))
        shutil.copytree(src, dst)


    #################### 데이터 복사 완료 ####################


    #################### 다른 Release용 Config 파일 삭제 시작 ####################


    config_file_io_MORAI_internal = os.path.normpath(os.path.join(program_path,\
        'proj_mgeo_editor_morai_opengl/GUI/config_file_io_default_MORAI.json'))
    os.remove(config_file_io_MORAI_internal)

    # TomTom 내부용 파일 삭제
    config_file_io_MORAI_internal = os.path.normpath(os.path.join(program_path,\
        'proj_mgeo_editor_morai_opengl/GUI/config_file_io_default_TomTom.json'))
    os.remove(config_file_io_MORAI_internal)

    # TomTom Release용 파일을 Internal용 이름으로 변경 (User.json 파일을 동일하게 사용하도록)
    src = os.path.normpath(os.path.join(program_path,\
        'proj_mgeo_editor_morai_opengl/GUI/config_file_io_default_TomTom_Release.json'))
    dst = os.path.normpath(os.path.join(program_path,\
        'proj_mgeo_editor_morai_opengl/GUI/config_file_io_default_TomTom.json'))
    os.rename(src, dst)

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
    elif platform.system() == "Linux":
        cmd = 'tar zcvf {}.tgz data program OpenDRIVE_Converter_for_TomTom'.format(folder_name)
        
        print('[INFO] Zipping the output... cmd >> {}'.format(cmd))
        ret = os.system(cmd)
        if ret != 0:
            print('[ERROR] Zipping failed (return: {})'.format(ret))
            return
        else:
            print('[INFO] Zipping done successfully.')

    print('[INFO] Done (Output Path: {})'.format(release_path))
    

if __name__ == "__main__":
    # 7z 실행되는지 테스트 해볼 것
    # os.system('7z')

    if platform.system() == "Windows":
        # elevate()
        build()
    elif platform.system() == "Linux":
        build()
