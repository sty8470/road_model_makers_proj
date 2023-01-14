import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.normpath(os.path.join(current_path, '../src/release_script/sphinx_util')))
from rst_file_maker import RstFileMaker

rst_folder = os.path.normpath(os.path.join(current_path, 'rst'))
src_folder1 = os.path.normpath(os.path.join(current_path, '../src/proj_mgeo_editor_42dot'))
src_folder2 = os.path.normpath(os.path.join(current_path, '../src/lib'))

RstFileMaker.create_all(rst_folder, [src_folder1, src_folder2])