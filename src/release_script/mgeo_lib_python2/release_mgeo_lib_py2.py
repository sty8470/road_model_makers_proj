import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../../'))) 

import shutil
from lib.common import path_utils


"""릴리즈할 메인 경로"""
release_root_path = os.path.normpath(os.path.join(current_path, '../../../z_release'))
print('[INFO] Release Root Path: {}'.format(release_root_path))


"""이번 릴리즈를 출력할 경로 및 경로 생성"""
folder_name = 'mgeo_lib_{}'.format(path_utils.get_now_str(include_sec=True))
release_path = os.path.normpath(os.path.join(release_root_path, folder_name))

path_utils.make_dir_if_not_exist(release_path)
print('[INFO] Release Path: {}'.format(release_path))


""" 파일 Copy """
prj_root_path = os.path.normpath(os.path.join(current_path, '../../../'))
src_root_path = os.path.normpath(os.path.join(current_path, '../../'))


##########

# [STEP 00] Lib 폴더 내 __init__.py 파일
# 폴더 생성
folder_name = 'lib'
lib_path = os.path.normpath(os.path.join(release_path, folder_name))

path_utils.make_dir_if_not_exist(lib_path)
print('[INFO] Release Path: {}'.format(lib_path))

# 파일 복사 
src = os.path.normpath(os.path.join(src_root_path, 'lib/__init__.py'))
dst = os.path.normpath(os.path.join(release_path, 'lib/__init__.py'))
shutil.copy(src, dst)


# [STEP 01-1] MGeo Library 복사
mgeo_class_defs = [
    # '__init__.py', # __init__.py는 다른 파일로 대체한다
    'base_line.py',
    'base_point.py',
    'base_plane.py',
    'junction.py',
    'junction_set.py',
    'line.py',
    'line_set.py',
    'link.py',
    # 'mgeo_planner_map.py', # mgeo_planner_map.py는 다른 파일로 대체한다
    'node.py',
    'node_set.py',
    'signal.py',
    'signal_set.py',
    'key_maker.py',
    'mgeo_item.py',
    ]

for f in mgeo_class_defs:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/class_defs/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/class_defs/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


# __init__.py는 따로 복사
#src = os.path.normpath(os.path.join(current_path, 'mgeo_class_def_init.py'))
src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/class_defs/release_mgeo_lib_py2/mgeo_class_def_init_mgeo_lib_py2.py'))
dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/class_defs/__init__.py'))
shutil.copy(src, dst)

# mgeo_planner_map.py는 따로 복사
#src = os.path.normpath(os.path.join(current_path, 'mgeo_class_def_mgeo_planner_map.py'))
src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/class_defs/release_mgeo_lib_py2/mgeo_planner_map_mgeo_lib_py2.py'))
dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/class_defs/mgeo_planner_map.py'))
shutil.copy(src, dst)


# [STEP 01-2] MGeo Edit 복사
mgeo_edit_funcs = [
    'edit_node.py',
    'edit_link.py',
    'edit_signal.py',
    'edit_junction.py',
    'edit_mgeo_planner_map.py']

for f in mgeo_edit_funcs:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/edit/funcs/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/edit/funcs/' + f))
    
    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


# [STEP 01-3] MGeo Save & Load 복사
mgeo_save_load = [
    '__init__.py',
    'subproc_load_link_ver1.py',
    'subproc_load_link_ver2.py']

for f in mgeo_save_load:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/save_load/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/save_load/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


# [STEP 01-4] MGeo Utils 복사
mgeo_utils = [
    '__init__.py',
    'logger.py',
    'version.py',
    'error_fix.py']

for f in mgeo_utils:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/utils/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/utils/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


# [STEP 02] Common Library 복사
files_to_copy = [
    '__init__.py',
    'path_utils.py',
    'geojson_common.py',
    'shp_common.py',
    'logger.py',
    'log_type.py',
    'singleton.py',
    'coord_trans_tm2ll.py',
    'coord_trans_utils.py',
    ]

for f in files_to_copy:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/common/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/common/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


# [STEP 03] 테스트 코드 & 데이터 복사 (폴더 전체)
src = os.path.normpath(os.path.join(src_root_path, 'test_python2_release'))
dst = os.path.normpath(os.path.join(release_path, 'test'))
shutil.copytree(src, dst)


# [STEP #04] .vscode 폴더 전체
src = os.path.normpath(os.path.join(src_root_path, 'release_script/.vscode'))
dst = os.path.normpath(os.path.join(release_path, '.vscode'))
shutil.copytree(src, dst)