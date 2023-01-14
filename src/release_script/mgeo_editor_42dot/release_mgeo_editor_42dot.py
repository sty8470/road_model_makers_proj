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
folder_name = '42dot_map_editor_{}'.format(path_utils.get_now_str(include_sec=True))
release_path = os.path.normpath(os.path.join(release_root_path, folder_name))

path_utils.make_dir_if_not_exist(release_path)
print('[INFO] Release Path: {}'.format(release_path))


""" 파일 Copy """
prj_root_path = os.path.normpath(os.path.join(current_path, '../../../'))
src_root_path = os.path.normpath(os.path.join(current_path, '../../'))


# [STEP #1-1] proj_mgeo_editor_42dot 폴더 전체
src = os.path.normpath(os.path.join(src_root_path, 'proj_mgeo_editor_42dot'))
dst = os.path.normpath(os.path.join(release_path, '42dot_map_editor'))
shutil.copytree(src, dst)


# config 파일 삭제
config_canvas = os.path.normpath(os.path.join(release_path, '42dot_map_editor/config_canvas.json'))
os.remove(config_canvas)

config_file_io = os.path.normpath(os.path.join(release_path, '42dot_map_editor/config_file_io.json'))
os.remove(config_file_io)

config_odr_param = os.path.normpath(os.path.join(release_path, '42dot_map_editor/config_odr_param.json'))
os.remove(config_odr_param)


# 로그 폴더 안의 내용 삭제
log_folder = os.path.normpath(os.path.join(release_path, '42dot_map_editor/log'))
shutil.rmtree(log_folder)
os.mkdir(log_folder)


# GUI/config_file_io_default.json은 따로 복사 (위에서 proj_mgeo_editor_42dot 폴더 전체 복사시 같이 복사된 파일을 overwrite)
src = os.path.normpath(os.path.join(current_path, 'GUI/config_file_io_default.json'))
dst = os.path.normpath(os.path.join(release_path, '42dot_map_editor/GUI/config_file_io_default.json'))
shutil.copy(src, dst)


# [STEP #1-2] lib_42dot 폴더 전체
src = os.path.normpath(os.path.join(src_root_path, 'lib/fourtytwodot'))
dst = os.path.normpath(os.path.join(release_path, 'lib/fourtytwodot'))
shutil.copytree(src, dst)


# [STEP #1-3] lib/common 폴더 내 일부 파일
files_to_copy = [
    '__init__.py',
    'path_utils.py',
    'geojson_common.py',
    'shp_common.py',
    'logger.py',
    'log_type.py',
    'singleton.py',
    'coord_trans_carla2llh.py',
    'coord_trans_tm2ll.py',
    'polygon_util.py', # added
    'aes_cipher.py' # added
    ]

for f in files_to_copy:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/common/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/common/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)

# [STEP #1-4] widget 폴더 일부
files_to_copy = [
    # 'display_item_prop.py', # release 폴더 내의 것으로 대체
    'display_item_style.py',
    'display_log.py',
    'edit_item_prop.py',
    'edit_odr_param.py',
    'edit_autogenerate_geometry_points.py'
    ]

for f in files_to_copy:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/widget/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/widget/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)

# display_item_prop.py는 release_42dot_map_editor 내의 파일로 대체
src = os.path.normpath(os.path.join(src_root_path, 'lib/widget/release_42dot_map_editor/display_item_prop.py'))
dst = os.path.normpath(os.path.join(release_path, 'lib/widget/display_item_prop.py'))
shutil.copy(src, dst)


##########


# [STEP #2] mgeo 복사
mgeo_class_defs = [
    # '__init__.py', # __init__.py는 다른 파일로 대체한다
    # 'mgeo_planner_map.py', # mgeo_planner_map.py는 다른 파일로 대체한다
    'base_line.py',
    'base_point.py',
    'base_plane.py',
    'junction.py',
    'junction_set.py',
    'line.py',
    'line_set.py',
    'link.py',
    'node.py',
    'node_set.py',
    'signal.py',
    'signal_set.py',
    'surface_marking.py',
    'surface_marking_set.py',
    'connectors.py',
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
src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/class_defs/release_42dot_map_editor/mgeo_class_def_init_42dot.py'))
dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/class_defs/__init__.py'))
shutil.copy(src, dst)

# mgeo_planner_map.py는 따로 복사
#src = os.path.normpath(os.path.join(current_path, 'mgeo_class_def_mgeo_planner_map.py'))
src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/class_defs/release_42dot_map_editor/mgeo_planner_map_42dot.py'))
dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/class_defs/mgeo_planner_map.py'))
shutil.copy(src, dst)


##########


# STEP 2-1 MGeo 내 Edit 폴더 복사
mgeo_edit = [
    '__init__.py']

for f in mgeo_edit:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/edit/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/edit/' + f))
    
    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


##########

# STEP 2-2 MGeo/Edit/Funcs 폴더 복사
mgeo_edit_funcs = [
    'edit_node.py',
    'edit_link.py',
    'edit_signal.py',
    'edit_junction.py',
    'edit_lane_marking.py',
    'edit_singlecrosswalk.py',
    'edit_crosswalk.py',
    'edit_mgeo_planner_map.py']

for f in mgeo_edit_funcs:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/edit/funcs/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/edit/funcs/' + f))
    
    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


##########


# STEP 2-3 MGeo/Save_Load 폴더 복사
mgeo_save_load = [
    '__init__.py',
    'subproc_load_link_ver1.py',
    'subproc_load_link_ver2.py']

for f in mgeo_save_load:
    src = os.path.normpath(os.path.join(src_root_path, 'lib/mgeo/save_load/' + f))
    dst = os.path.normpath(os.path.join(release_path, 'lib/mgeo/save_load/' + f))

    path_utils.make_dir_of_file_if_not_exist(dst)
    shutil.copy(src, dst)


##########


# STEP 2-4 MGeo/Utils 폴더 복사
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


##########


# [STEP #3] mscenario 복사


##########


# [STEP #04] .vscode 폴더 전체
src = os.path.normpath(os.path.join(src_root_path, 'release_script/.vscode'))
dst = os.path.normpath(os.path.join(release_path, '.vscode'))
shutil.copytree(src, dst)


##########


# [STEP #05] data 복사
src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/42dot_mdl2009_yangjae'))
dst = os.path.normpath(os.path.join(release_path, 'data/42dot_hdmap/42dot_hdmap_yangjae'))
shutil.copytree(src, dst)

src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/42dot_mdl2009_kcity (sdx_kcity_morai_5179 (v2.0.1))'))
dst = os.path.normpath(os.path.join(release_path, 'data/42dot_hdmap/42dot_hdmap_kcity'))
shutil.copytree(src, dst)

src = os.path.normpath(os.path.join(prj_root_path, 'data/hdmap/42dot_mdl2102_sangam'))
dst = os.path.normpath(os.path.join(release_path, 'data/42dot_hdmap/42dot_hdmap_sangam'))
shutil.copytree(src, dst)

src = os.path.normpath(os.path.join(prj_root_path, 'data/mgeo/42dot_yangjae_maps_release'))
dst = os.path.normpath(os.path.join(release_path, 'data/mgeo/42dot_mgeo_yangjae'))
shutil.copytree(src, dst)

src = os.path.normpath(os.path.join(prj_root_path, 'data/mgeo/42dot_kcity_maps_release'))
dst = os.path.normpath(os.path.join(release_path, 'data/mgeo/42dot_mgeo_kcity'))
shutil.copytree(src, dst)

src = os.path.normpath(os.path.join(prj_root_path, 'data/mgeo/42dot_sangam_maps_release'))
dst = os.path.normpath(os.path.join(release_path, 'data/mgeo/42dot_mgeo_sangam'))
shutil.copytree(src, dst)


##########


# [STEP #06] sphinx 복사
src = os.path.normpath(os.path.join(current_path, 'sphinx_42dot_map_editor'))
dst = os.path.normpath(os.path.join(release_path, 'sphinx'))
shutil.copytree(src, dst)

src = os.path.normpath(os.path.join(current_path, '../sphinx_util/rst_file_maker.py'))
dst = os.path.normpath(os.path.join(release_path, 'sphinx/rst_file_maker.py'))
shutil.copy(src, dst)

src = os.path.normpath(os.path.join(current_path, '../sphinx_util/default_module.rst'))
dst = os.path.normpath(os.path.join(release_path, 'sphinx/default_module.rst'))
shutil.copy(src, dst)

src = os.path.normpath(os.path.join(current_path, '../sphinx_util/default_modules.rst'))
dst = os.path.normpath(os.path.join(release_path, 'sphinx/default_modules.rst'))
shutil.copy(src, dst)


##########