"""
국토지리정보원 Shape Ver2 모델의 파일로부터 차선 mesh를 생성한다
"""
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')
sys.path.append(current_path + '/../lib_ngii_shp_ver2/')

from shp_common import *


def main():
    input_path = '../../rsc/map_data/ngii_shp_ver2_Daegu/SEC02_테크노폴리스/HDMap_UTM52N_타원체고'
    output_path = '../../saved/mesh_lane/대구테크노폴리스'
    relative_loc = True

    # 절대 경로로 변경
    # input_path = os.path.normcase(input_path)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)   

    # 절대 경로로 변경
    # output_path = os.path.normcase(output_path)
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get Map Information
    map_info = read_shp_files(input_path)
    if map_info is None:
        raise BaseException('[ERROR] There is no input data (input_path might be incorrect)')
    
    # Find origin, using A1_NODE
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)

    print('END')

if __name__ == u'__main__':
    main()

