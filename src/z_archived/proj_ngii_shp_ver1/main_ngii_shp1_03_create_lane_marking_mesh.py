import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')

import vtk
import math
from lib.common import file_io
from shp_common import *
from datetime import datetime

from GetRoadData import GetRoadDataSet
from GetPolyData import GetPolyDataSet
from GetOutlineData import GetOutlineDataSet


def DrawLane(mapInfo, outputDir, outputFileName='RoadLane', optionText=''):
    # 두파일에 나눠져 있는 차선 정보 기록위한 데이터
    laneSideDataSet = GetRoadDataSet(mapInfo)
    polyDataSet = GetPolyDataSet(laneSideDataSet)

    """ #01 차선 그리기 (필요 시 주석 해제)""" 
    for strPrefix, data in polyDataSet.items():
        linesPolyData = vtk.vtkPolyData()
        linesPolyData.SetPoints(data['points'])
        linesPolyData.SetPolys(data['polys'])
        linesPolyData.GetPointData().SetScalars(data['scalars'])

        strFileName = outputFileName + '_' + strPrefix + '_' + optionText
        file_io.write_stl_and_obj(linesPolyData, outputDir + '/' + strFileName)
    

if __name__ == '__main__':
    import os

    print('[INFO] Drawing Road Model Starts...')
    mapInputDir = '../../rsc/map_data/ngii_shp_ver1_KCity/'
    outputDir = '../../saved/ngii_shp_ver1_KCity/mesh_lane_{}'.format(datetime.now().strftime('%Y-%m-%d'))
    origin = [451140.341000, 3947642.281000, 70.125000]


    """ 서울 """
    # mapInputDir = '../../rsc/map_data/shp_01_Seoul_AutonomousDrivingTestbed/HDMap_UTM52N'
    # outputDir = '../../saved/mesh_lane/shp_01_Seoul_AutonomousDrivingTestbed/shp_ver1_{}'.format(datetime.now().strftime('%Y-%m-%d'))
    # origin = [313008.55819800857, 4161698.628368007, 35.6643558335918]

    """ 대구 """
    # mapInputDir = '../../rsc/map_data/ngii_shp_ver1_Daegu/SEC02_테크노폴리스/HDMap_UTM52N_타원체고'
    # outputDir = '../../saved/mesh_lane/Daegu_Technopolis/shp_ver1_{}'.format(datetime.now().strftime('%Y-%m-%d'))
    # origin = [451140.341000, 3947642.281000, 70.125000]

    """ 판교 """
    # mapInputDir = '../../rsc/map_data/shp_03_Sungnam_PangyoZeroCity/HDMap_UTM52N'
    # outputDir = '../../output/shp_03_Sungnam_PangyoZeroCity/{}'.format(datetime.now().strftime('%Y-%m-%d'))
   

    # Change mapInputDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))
    mapInputDir = os.path.normcase(mapInputDir)
    mapInputDir = os.path.join(current_path, mapInputDir)
    mapInputDir = os.path.normpath(mapInputDir)


    # Change outputDir to Absolute Path
    outputDir = os.path.normcase(outputDir)
    outputDir = os.path.join(current_path, outputDir)
    outputDir = os.path.normpath(outputDir)

    # Check if the output path exists
    if not os.path.isdir(outputDir):
        os.makedirs(outputDir)


    print('[INFO] input  path:', mapInputDir)
    print('[INFO] output path:', outputDir)

    # Get Map Information
    mapInfo = read_shp_files(mapInputDir)
    if mapInfo is None:
        raise BaseException('[ERROR] There is no input data (input_path might be incorrect)')
    

    # origin을 하드코딩으로 입력할 경우, 아래 부분은 그냥 주석처리한다
    origin = get_first_shp_point(mapInfo['A1_LANE'])
    SHPLocationTransform.SetOrigin(origin)
    print('[INFO] Origin =', origin)


    # Do Tasks
    print('[INFO] Creating Lane Markings... ')
    DrawLane(mapInfo, outputDir)
    print('[INFO] Creating Lane Markings: DONE')



    print('[INFO] Drawing Road Model Finished.')
