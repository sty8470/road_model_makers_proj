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
    folder_name = 'opendrive_support_program_{}'.format(path_utils.get_now_str(include_sec=True))
    if platform.system() == "Windows":
        folder_name += '_win' 
    if platform.system() == "Linux":
        folder_name += '_linux' 
    release_path = os.path.normpath(os.path.join(release_root_path, folder_name))

    program_path = os.path.normpath(os.path.join(release_path, 'program'))
    sample_opendrive_path = os.path.normpath(os.path.join(release_path, 'opendrive'))
    sample_config_path = os.path.normpath(os.path.join(release_path, 'config'))
    sample_output_path = os.path.normpath(os.path.join(release_path, 'output'))

    print('[INFO] Release Path: {}'.format(release_path))


    """ 패키징 프로젝트 경로 생성 """
    package_proj_path = os.path.abspath(os.path.join(current_path, '../../lib/opendrive'))


    #################### 프로그램 빌드 시작 ####################


    """ 패키징을 위해 spec 파일 복사 """
    spec_file_path = os.path.join(package_proj_path, 'xodr_to_mgeo.spec')
    shutil.copy(os.path.join(current_path, 'xodr_to_mgeo.spec'), spec_file_path)
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
   

    """ 파일 Copy """
    src = os.path.normpath(os.path.join(package_proj_path, 'dist/xodr_to_mgeo/'))
    print('[INFO] Copy Package files {} to {}'.format(src, release_path))
    shutil.copytree(src, program_path)
    print('[INFO] Copy Finished.')

    """ sample OpenDRIVE 파일 Copy """
    src = os.path.normpath(os.path.join(package_proj_path, 'sample_opendrive'))
    print('[INFO] Copy Sample OpenDRIVE files {} to {}'.format(src, release_path))
    shutil.copytree(src, sample_opendrive_path)
    print('[INFO] Copy Finished.')

    """ sample config 파일 Copy """
    src = os.path.normpath(os.path.join(package_proj_path, 'sample_config'))
    print('[INFO] Copy Sample Config files {} to {}'.format(src, release_path))
    shutil.copytree(src, sample_config_path)
    print('[INFO] Copy Finished.')

    """ output 폴더 만들기 """
    os.mkdir(sample_output_path)


    """ 바로가기 """
    print('[INFO] Creating Shortcut...')
    try:
        os.chdir(release_path)
        if platform.system() == "Windows":
            install_file_path = os.path.join(release_path, 'install.bat')
            shutil.copy(os.path.join(current_path, 'install.bat'), install_file_path)

        elif platform.system() == "Linux":
            cmd = 'ln -s ./program/opendrive_support_program'

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
        cmd = 'tar zcvf {}.tgz data program opendrive_support_program'.format(folder_name)
        
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
