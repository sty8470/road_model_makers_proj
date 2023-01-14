import vtk
import os
import shapefile
import random
import numpy as np
import math
from lib.common import file_io
from lib.common import vtk_utils
from lib.common import path_utils
from shp_common import *


# l1-l2에 수직이고 중간점을 지나는 평면 ax+by+cz+d=0이 있을때, 해당 평면에 대칭인 점 dot'구하기
def GetPlaneSymmetry(dot, l1, l2):
    n = np.array([l2[0] - l1[0], l2[1] - l1[1], l2[2] - l1[2]])
    # d = (a * (l2[0] + l1[0]) + b * (l2[1] + l1[1]) + c * (l2[2] + l1[2])) * (-0.5)
    p = np.array([(l2[0] + l1[0]) / 2, (l2[1] + l1[1]) / 2, (l2[2] + l1[2]) / 2])
    l = np.array([dot[0], dot[1], dot[2]])
    t = sum(((p - l) / sum(n * n)) * n)
    i = l + t * n

    return i[0], i[1], i[2]


def DrawRoadBase(mapInfo, outputDir, outputFileName='RoadBaseFromNode', optionText=''):
    ret = None
    # https://vtk.org/Wiki/VTK/Examples/Python/DataManipulation/Cube.py
    try:
        # 라인 색으로 사용할 것, 점, 라인
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)

        roadLinkShapeRecords = mapInfo['2_ROAD_LINK_Uiwang_20190212'].shapeRecords()
        roadNodeShapeRecords = mapInfo['1_ROAD_NODE_Uiwang_20190211'].shapeRecords()
        # 그리기 편하도록 ['rn_id': {'start':(), 'end':()},]로 변경
        roadNode = {}

        # ROAD_NODE 정보
        for shapeRecord in roadNodeShapeRecords:
            # RN_ID
            roadNode[shapeRecord.record[0]] = {
                'start': (GetLocation(shapeRecord.shape.points[0][0], shapeRecord.shape.points[0][1],
                                      shapeRecord.shape.z[0])),
                'end': (
                    GetLocation(shapeRecord.shape.points[1][0], shapeRecord.shape.points[1][1], shapeRecord.shape.z[1]))
            }

        # 순서대로 좌표값들, 면정보, 스칼라정보, 도로에사용된 육면체 갯수
        points = vtk.vtkPoints()
        polys = vtk.vtkCellArray()
        scalars = vtk.vtkFloatArray()
        nCube = 0

        # 도로 링크 정보들 로드
        for i in range(len(roadLinkShapeRecords)):
            shapeRecord = roadLinkShapeRecords[i]
            # RL_ID
            id = shapeRecord.record[0]
            # ST_RN_ID
            start = roadNode[shapeRecord.record[1]]
            # ED_RN_ID
            end = roadNode[shapeRecord.record[4]]

            # ROAD_NODE로 만든 부분
            # 링크의 양끝 노드만 연결하면 곡선이 표시가 안되어서 링크의 점 단위로 끊어서 만들기
            before_start = start['start']
            before_end = start['end']
            for i in range(len(shapeRecord.shape.z) - 2):
                dot = (
                    GetLocation(shapeRecord.shape.points[i][0], shapeRecord.shape.points[i][1], shapeRecord.shape.z[i]))
                dot2 = (GetLocation(shapeRecord.shape.points[i + 1][0], shapeRecord.shape.points[i + 1][1],
                                    shapeRecord.shape.z[i + 1]))
                current_start = GetPlaneSymmetry(before_start, dot, dot2)
                current_end = GetPlaneSymmetry(before_end, dot, dot2)
                nCube, points, polys, scalars = GetCubeData([before_start, before_end, current_end, current_start],
                                                            nCube, points, polys, scalars)

                before_start = current_start
                before_end = current_end
            if shapeRecord.record[2] != shapeRecord.record[5]:
                nCube, points, polys, scalars = GetCubeData([before_start, before_end, end['end'], end['start']],
                                                            nCube, points, polys, scalars)
            else:
                nCube, points, polys, scalars = GetCubeData([before_start, before_end, end['start'], end['end']],
                                                            nCube, points, polys, scalars)

        # 그리기
        roadPolyData = vtk.vtkPolyData()
        roadPolyData.SetPoints(points)
        roadPolyData.SetPolys(polys)
        roadPolyData.GetPointData().SetScalars(scalars)
        ret = roadPolyData

        file_io.write_stl_and_obj(roadPolyData, outputDir + '/' + outputFileName + '_' + optionText)
        # vtk_utils.show_poly_data(roadPolyData)

    except BaseException as e:
        print(e)
    return ret


if __name__ == '__main__':
    import os, datetime

    inputFile = '../rsc/map_data/shp_HDMap_Uiwang_190213_WGS'
    outputFile = '../output/RoadBase_NoZ_{}'.format(path_utils.get_datetime_str(datetime.datetime.now()))

    # Change inputFile to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))
    inputFile = os.path.normcase(inputFile)
    inputFile = os.path.join(current_path, inputFile)
    inputFile = os.path.normpath(inputFile)

    # Change output to Absolute Path
    outputFile = os.path.normcase(outputFile)
    outputFile = os.path.join(current_path, outputFile)
    outputFile = os.path.normpath(outputFile)

    # Check if the output path exists
    outputDir = os.path.dirname(outputFile)
    if not os.path.isdir(outputDir):
        os.makedirs(outputDir)

    # Get Map Information
    mapInfo = read_shp_files(inputFile)

    # Do Tasks
    DrawRoad(mapInfo, outputFile)

    print('[INFO] DrawRoad Finished')
