import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/common/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib_ngii_shp_ver2/')))

from tkinter import filedialog

from lib.mgeo.class_defs import *
from mgeo_odr_converter import MGeoToOdrDataConverter


def functional_test_main():
    """저장된 mgeo 파일을 로드하고, OdrData로 만든 다음, OdrData를 파일로 출력한다"""

    init_path = '../../saved/'
    init_path = os.path.join(current_path, init_path)
    init_path = os.path.normpath(init_path)


    # Test input values >> 테스트용 파일이 있는 값으로 고정하는 것이 더 나을지도
    input_path = filedialog.askdirectory(
        initialdir=init_path,
        title='Load data'
    )
    if (input_path == '' or input_path == None):
        Logger.log_error('invalid input_path')
        return

    save_file_name = filedialog.asksaveasfilename(
        initialdir=init_path,
        title='Save file as',
        filetypes=[('OpenDRIVE', '.xodr')],
        defaultextension='.xodr'
    )
    if (save_file_name == '' or save_file_name == None):
        Logger.log_error('invalid save_file_name')
        return


    # STEP #1: Load MGeo data
    mgeo_data = MGeo.create_instance_from_json(input_path)


    # STEP #2: Convert into OdrData
    converter = MGeoToOdrDataConverter.get_instance()
    odr_data = converter.convert(mgeo_data)


    # STEP #3: Write into an xodr file
    xml_string = odr_data.to_xml_string()
    odr_data.write_xml_string_to_file(save_file_name, xml_string)
    

if __name__ == u'__main__':
    functional_test_main()