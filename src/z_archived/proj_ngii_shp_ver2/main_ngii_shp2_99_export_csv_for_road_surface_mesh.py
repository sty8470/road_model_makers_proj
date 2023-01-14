"""
road surface mesh를 생성하기 위한 csv 파일을 출력한다
road edge, link, lane marking 정보를 csv 파일로 변경하는데,
각각의 선 인스턴스를 구분하지 않고, 모든 선을 구성하는 모든 점을 하나의 csv 파일로 모은다
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common')

from shp_common import read_shp_files, 
from shp_csv_export import to_csv_exportable_data
import shapefile
import csv
from tkinter import filedialog


def main(dir_selection_using_gui):

    # 상대좌표로 뽑을 것인가를 결정
    relative_loc = True

    if dir_selection_using_gui:
        """INPUT/OUTPUT 경로를 GUI로 설정한다"""
        # 초기 경로
        input_init_dir = os.path.join(current_path, '../../rsc/map_data/')

        # 맵 로드할 경로
        input_path = filedialog.askdirectory(
            initialdir = input_init_dir,
            title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능   

        # 출력 초기 경로
        output_init_dir = os.path.join(current_path, '../../saved/csv/') 


        # csv 저장할 경로
        output_path = filedialog.askdirectory(
            initialdir = output_init_dir,
            title = 'Save files to') # defaultextension = 'json') 과 같은거 사용 가능
    else:
        """INPUT/OUTPUT 경로를 코드로 설정한다"""
        input_path = os.path.join(current_path, '../../rsc/map_data/ngii_shp_ver2_Daegu/SEC02_테크노폴리스/HDMap_UTM52N_타원체고')
        output_path = os.path.join(current_path, '../../saved/csv/대구테크노폴리스') 

        input_path = os.path.normpath(input_path)
        output_path = os.path.normpath(output_path)

    # Get Map Information
    map_info = read_shp_files(input_path)
    if map_info is None:
        raise BaseException('[ERROR] There is no input data (input_path might be incorrect)')

    # Find origin, using A1_NODE
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)   

    # csv로 변경할 key 종류들
    key_list = ['A2_LINK', 'B2_SURFACELINEMARK', 'C3_VEHICLEPROTECTIONSAFETY']

    for key in key_list:
        input_shape = map_info[key]
        
        # shp data -> exportable data
        export_data = to_csv_exportable_data(input_shape, origin)

        # exportable data -> csv file
        output_file = os.path.join(output_path, key) + '.csv'
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            writer.writerows(export_data)


    print('END')


if __name__ == u'__main__':
    main(dir_selection_using_gui=False)