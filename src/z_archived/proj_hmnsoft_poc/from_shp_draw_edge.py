import vtk
import numpy as np
from lib.common import file_io
from shp_common import *
from datetime import datetime


# 차선 중심으로 width만큼 평면 구하기
def GetLanePlane(x1, y1, z1, x2, y2, z2, fWitdh):
    if y1 == y2:
        s1 = (x1 - fWitdh / 2, y1, z1)
        s2 = (x1 + fWitdh / 2, y1, z1)
        e1 = (x2 - fWitdh / 2, y2, z2)
        e2 = (x2 + fWitdh / 2, y2, z2)
    elif x1 == x2:
        s1 = (x1, y1 - fWitdh / 2, z1)
        s2 = (x1, y1 + fWitdh / 2, z1)
        e1 = (x2, y2 - fWitdh / 2, z2)
        e2 = (x2, y2 + fWitdh / 2, z2)
    else:
        m = (y2 - y1) / (x2 - x1)
        r = fWitdh
        a = x1 * x1 - (m * m * r * r) / (m * m + 1)
        ax = (2 * x1 + math.sqrt(4 * x1 * x1 - 4 * a)) / 2
        bx = (2 * x1 - math.sqrt(4 * x1 * x1 - 4 * a)) / 2
        ay = (-1 / m) * ax + y1 + x1 / m
        by = (-1 / m) * bx + y1 + x1 / m

        s1 = (ax, ay, z1)
        s2 = (bx, by, z1)
        e1 = (ax + (x2 - x1), ay + (y2 - y1), z2)
        e2 = (bx + (x2 - x1), by + (y2 - y1), z2)

    return s1, s2, e1, e2


# l1-l2에 수직이고 중간점을 지나는 평면 ax+by+cz+d=0이 있을때, 해당 평면에 대칭인 점 dot'구하기
def GetPlaneSymmetry(dot, l1, l2):
    n = np.array([l2[0] - l1[0], l2[1] - l1[1], l2[2] - l1[2]])
    # d = (a * (l2[0] + l1[0]) + b * (l2[1] + l1[1]) + c * (l2[2] + l1[2])) * (-0.5)
    p = np.array([(l2[0] + l1[0]) / 2, (l2[1] + l1[1]) / 2, (l2[2] + l1[2]) / 2])
    l = np.array([dot[0], dot[1], dot[2]])
    t = sum(((p - l) / sum(n * n)) * n)
    i = l + t * n

    return i[0], i[1], i[2]


def DrawEdge(mapInfo,  outputDir, outputFileName='RoadEdge', optionText=''):
    ret = None
    # https://vtk.org/Wiki/VTK/Examples/Python/DataManipulation/Cube.py
    try:
        # 라인 색으로 사용할 것, 점, 라인
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)

        roadEdgeShapeRecords = mapInfo['5_ROAD_EDGE_Uiwang_20190211'].shapeRecords()
        # 순서대로 좌표값들, 면정보, 스칼라정보, 도로에사용된 육면체 갯수
        points = vtk.vtkPoints()
        polys = vtk.vtkCellArray()
        scalars = vtk.vtkFloatArray()
        nCube = 0

        # ROAD_EDGE 정보
        for shapeRecord in roadEdgeShapeRecords:
            if shapeRecord.record[1] != 1:
                continue
            fHeight = 30
            fWidth = 15

            dots = []
            for i in range(len(shapeRecord.shape.points)):
                dots.append((GetLocation(shapeRecord.shape.points[i][0], shapeRecord.shape.points[i][1],
                                         shapeRecord.shape.z[i])))

            for i in range(len(dots) - 1):
                start = dots[i];
                end = dots[i + 1];

                s1, s2, e1, e2 = GetLanePlane(start[0], start[1], start[2], end[0], end[1], end[2], fWidth)
                nCube, points, polys, scalars = GetCubeData([s1, s2, e2, e1], nCube, points, polys, scalars, fHeight)

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
    import os

    inputFile = '../rsc/map_data/shp_HDMap_Uiwang_190213_WGS'
    outputFile = '../output/{}/RoadEdge_NoZ_190908_PM0428'.format(datetime.now().strftime('%Y-%m-%d'))

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
    DrawEdge(mapInfo, outputFile)

    print('[INFO] DrawRoad Finished')
