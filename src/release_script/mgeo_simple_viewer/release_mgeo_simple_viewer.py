import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) 

import shutil
from lib.common import path_utils


"""릴리즈할 메인 경로"""
release_root_path = os.path.normpath(os.path.join(current_path, '../../z_release'))
print('[INFO] Release Root Path: {}'.format(release_root_path))


"""이번 릴리즈를 출력할 경로 및 경로 생성"""
folder_name = 'mgeo_simple_viewer_{}'.format(path_utils.get_now_str(include_sec=True))
release_path = os.path.normpath(os.path.join(release_root_path, folder_name))

path_utils.make_dir_if_not_exist(release_path)
print('[INFO] Release Path: {}'.format(release_path))


""" 파일 Copy """
prj_root_path = os.path.normpath(os.path.join(current_path, '../../../'))
src_root_path = os.path.normpath(os.path.join(current_path, '../../'))

# [STEP #1] mgeo_basic_viewer 폴더 전체
src = os.path.normpath(os.path.join(src_root_path, 'mgeo_basic_viewer'))
dst = os.path.normpath(os.path.join(release_path, 'mgeo_basic_viewer'))
shutil.copytree(src, dst)


# [STEP #2] mgeo 복사
mgeo_class_defs = [
    # '__init__.py', # __init__.py는 다른 파일로 대체한다
    'base_line.py',
    'base_point.py',
    'junction.py',
    'junction_set.py',
    'line.py',
    'line_set.py',
    'link.py',
    'mgeo_planner_map.py',
    'node.py',
    'node_set.py',
    'signal.py',
    'signal_set.py']

for f in mgeo_class_defs:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/class_defs/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/class_defs/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


# __init__.py는 따로 복사
src = os.path.normpath(os.path.join(current_path, 'mgeo_class_def_init_simple_viewer.py'))
dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/class_defs/__init__.py'))
shutil.copy(src, dst)


mgeo_edit = [
    '__init__.py',
    'core_search_funcs.py',
    'core_select_funcs.py',
    'tasks/path_planning_using_dijkstra_task.py']

for f in mgeo_edit:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/edit/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/edit/' + f))
    
    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


mgeo_path_planning = [
    '__init__.py',
    'dijkstra.py',
    'polynomial_fit.py'
    ]

for f in mgeo_path_planning:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/path_planning/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/path_planning/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


mgeo_save_load = [
    '__init__.py',
    'subproc_load_link_ver1.py',
    'subproc_load_link_ver2.py']

for f in mgeo_save_load:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/save_load/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/save_load/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


mgeo_utils = [
    '__init__.py',
    'version.py']

for f in mgeo_utils:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/utils/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/utils/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)

# [STEP #03] data 복사
src = os.path.normpath(os.path.join(prj_root_path, 'data/mgeo/mgeo_kcity_from_ngii_shp_ver2/200803_PM0600_kcity_exported'))
dst = os.path.normpath(os.path.join(release_path, 'data/mgeo_kcity_from_ngii_shp_ver2/200803_PM0600_kcity_exported'))
shutil.copytree(src, dst)


# 


