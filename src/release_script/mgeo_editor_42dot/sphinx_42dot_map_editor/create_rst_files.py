import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))

from rst_file_maker import RstFileMaker

rst_folder = os.path.normpath(os.path.join(current_path, 'rst'))
src_folder1 = os.path.normpath(os.path.join(current_path, '../42dot_map_editor'))
src_folder2 = os.path.normpath(os.path.join(current_path, '../lib'))

RstFileMaker.create_all(rst_folder, [src_folder1, src_folder2])