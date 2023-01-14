import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import vtk
import numpy as np
from lib.common import file_io
from shp_common import *
from datetime import datetime
from functools import reduce


# l1-l2에 수직이고 중간점을 지나는 평면 ax+by+cz+d=0이 있을때, 해당 평면에 대칭인 점 dot'구하기
def GetPlaneSymmetry(dot, l1, l2):
    n = np.array([l2[0] - l1[0], l2[1] - l1[1], l2[2] - l1[2]])
    p = np.array([(l2[0] + l1[0]) / 2, (l2[1] + l1[1]) / 2, (l2[2] + l1[2]) / 2])
    l = np.array([dot[0], dot[1], dot[2]])
    t = sum(((p - l) / sum(n * n)) * n)
    i = l + t * n

    return i[0], i[1], i[2]


# 차선 중심으로 width만큼 평면 구하기
def GetLanePlane(x1, y1, z1, x2, y2, z2, fWitdh):
    if y1 == y2:
        if x1 < x2:
            s1 = (x1 - fWitdh / 2, y1, z1)
            s2 = (x1 + fWitdh / 2, y1, z1)
            e1 = (x2 - fWitdh / 2, y2, z2)
            e2 = (x2 + fWitdh / 2, y2, z2)
        else:
            s2 = (x1 - fWitdh / 2, y1, z1)
            s1 = (x1 + fWitdh / 2, y1, z1)
            e2 = (x2 - fWitdh / 2, y2, z2)
            e1 = (x2 + fWitdh / 2, y2, z2)
    elif x1 == x2:
        if y1 < y2:
            s1 = (x1, y1 - fWitdh / 2, z1)
            s2 = (x1, y1 + fWitdh / 2, z1)
            e1 = (x2, y2 - fWitdh / 2, z2)
            e2 = (x2, y2 + fWitdh / 2, z2)
        else:
            s2 = (x1, y1 - fWitdh / 2, z1)
            s1 = (x1, y1 + fWitdh / 2, z1)
            e2 = (x2, y2 - fWitdh / 2, z2)
            e1 = (x2, y2 + fWitdh / 2, z2)
    else:
        m = (y2 - y1) / (x2 - x1)
        r = fWitdh / 2
        a = x1 * x1 - (m * m * r * r) / (m * m + 1)
        ax = (2 * x1 + math.sqrt(4 * x1 * x1 - 4 * a)) / 2
        bx = (2 * x1 - math.sqrt(4 * x1 * x1 - 4 * a)) / 2
        ay = (-1 / m) * ax + y1 + x1 / m
        by = (-1 / m) * bx + y1 + x1 / m

        if y1 < y2:
            s1 = (ax, ay, z1)
            s2 = (bx, by, z1)
            e1 = (ax + (x2 - x1), ay + (y2 - y1), z2)
            e2 = (bx + (x2 - x1), by + (y2 - y1), z2)
        else:
            s2 = (ax, ay, z1)
            s1 = (bx, by, z1)
            e2 = (ax + (x2 - x1), ay + (y2 - y1), z2)
            e1 = (bx + (x2 - x1), by + (y2 - y1), z2)

    return s1, s2, e2, e1


def GetLaneOrder(lanes, reverseCheck):
    nexts = []
    last = (0, 0)
    for _i in range(len(lanes)):
        min = 160000
        dot1 = lanes[_i][0]
        next = (-1, 0)
        for _j in range(len(lanes)):
            if _i == _j:
                continue
            dot2 = lanes[_j][len(lanes[_j]) - 1]
            length = (dot1[0] - dot2[0]) * (dot1[0] - dot2[0]) + (dot1[1] - dot2[1]) * (dot1[1] - dot2[1])
            if min > length:
                min = length
                next = (_j, 0)

            dot2 = lanes[_j][0]
            length = (dot1[0] - dot2[0]) * (dot1[0] - dot2[0]) + (dot1[1] - dot2[1]) * (dot1[1] - dot2[1])
            if min > length:
                min = length
                next = (_j, 1)
        nexts.append(next)
        if next[0] == -1:
            last = (_i, 0)

    order = [last]
    while True:
        flag = True
        for _i in range(len(nexts)):
            if nexts[_i][0] == last[0]:
                last = (_i, nexts[_i][1])
                flag = False
                break
        for lane in order:
            if lane[0] == last[0]:
                flag = True
                break
        if flag:
            break
        order.append(last)

    dots = []
    for current in order:
        lane = lanes[current[0]]
        if current[1] == reverseCheck:
            lane = reversed(lane)
        for dot in lane:
            flag = True
            for _dot in dots:
                if dot[0] == _dot[0] and dot[1] == _dot[1]:
                    flag = False
                    break
            if flag:
                dots.append(dot)
    length = 0
    for _i in range(len(dots) - 2):
        length += (dots[_i][0] - dots[_i + 1][0]) * (dots[_i][0] - dots[_i + 1][0]) + (dots[_i][1] - dots[_i + 1][1]) * (dots[_i][1] - dots[_i + 1][1])
    return dots, length


def ConvexHull(dots):

    def cmp(a, b):
        return (a > b) - (a < b)

    def turn(p, q, r):
        return cmp((q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1]), 0)

    def _keep_left(hull, r):
        while len(hull) > 1 and turn(hull[-2], hull[-1], r) != 1:
            hull.pop()
        if not len(hull) or hull[-1] != r:
            hull.append(r)
        return hull

    dots = sorted(dots)
    l = reduce(_keep_left, dots, [])
    u = reduce(_keep_left, reversed(dots), [])
    ret = l.extend(u[i] for i in range(1, len(u) - 1)) or l
    return ret


def DrawRoadBase(mapInfo, outputDir, outputFileName='RoadBaseFromNode'):
    ret = None
    # https://vtk.org/Wiki/VTK/Examples/Python/DataManipulation/Cube.py
    laneSideShapeRecords = mapInfo['A1_LANE'].shapeRecords()
    linkLeftLaneData = {}
    linkRightLaneData = {}

    for shapeRecord in laneSideShapeRecords:
        record = shapeRecord.record
        dots = []
        dots.append(
            SHPLocationTransform.GetLocation(
                shapeRecord.shape.points[0][0],
                shapeRecord.shape.points[0][1],
                shapeRecord.shape.z[0]))

        min_z, max_z = shapeRecord.shape.z[0], shapeRecord.shape.z[len(shapeRecord.shape.z) - 1]
        if min_z > max_z:
            max_z, min_z = shapeRecord.shape.z[0], shapeRecord.shape.z[len(shapeRecord.shape.z) - 1]

        for i in range(len(shapeRecord.shape.z) - 1):
            _z = shapeRecord.shape.z[i + 1]
            if min_z > _z:
                _z = min_z
            if max_z < _z:
                _z = max_z

            dots.append(
                SHPLocationTransform.GetLocation(
                    shapeRecord.shape.points[i + 1][0],
                    shapeRecord.shape.points[i + 1][1],
                    _z))

        # 일단 외곽선으로는 안그리도록
        # 어차피 외곽 안에 차선이 따로 있음
        if record[6] == '2':
            continue
        if record[0] not in linkLeftLaneData:
            linkLeftLaneData[record[0]] = []
        linkLeftLaneData[record[0]].append(dots)
        if record[1] not in linkRightLaneData:
            linkRightLaneData[record[1]] = []
        linkRightLaneData[record[1]].append(dots)

    try:
        # 라인 색으로 사용할 것, 점, 라인
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)

        roadLinkShapeRecords = mapInfo['A3_LINK'].shapeRecords()
        roadNodeShapeRecords = mapInfo['C1_NODE'].shapeRecords()
        # 그리기 편하도록 ['rn_id': {'start':(), 'end':()},]로 변경
        roadNode = {}

        # ROAD_NODE 정보
        for shapeRecord in roadNodeShapeRecords:
            # RN_ID
            roadNode[shapeRecord.record[0]] = {
                'dot': (SHPLocationTransform.GetLocation(
                            shapeRecord.shape.points[0][0],
                            shapeRecord.shape.points[0][1],
                            shapeRecord.shape.z[0]))
            }

        # 순서대로 좌표값들, 면정보, 스칼라정보, 도로에사용된 육면체 갯수
        points = vtk.vtkPoints()
        polys = vtk.vtkCellArray()
        scalars = vtk.vtkFloatArray()
        nCube = 0

        # 도로 링크 정보들 로드
        for i in range(len(roadLinkShapeRecords)):
            # 35,
            if not (34 < i and i < 36):
                pass#continue
            shapeRecord = roadLinkShapeRecords[i]
            id = shapeRecord.record[0]

            leftLanes = linkLeftLaneData.get(id)
            rightLanes = linkRightLaneData.get(id)
            drawFailed = True

            if leftLanes is not None and rightLanes is not None:
                length = 0
                for j in range(len(shapeRecord.shape.z) - 2):
                    dot = (SHPLocationTransform.GetLocation(
                        shapeRecord.shape.points[j][0],
                        shapeRecord.shape.points[j][1],
                        shapeRecord.shape.z[j]))

                    dot2 = (SHPLocationTransform.GetLocation(
                        shapeRecord.shape.points[j + 1][0],
                        shapeRecord.shape.points[j + 1][1],
                        shapeRecord.shape.z[j + 1]))

                    length += (dot[0] - dot2[0]) * (dot[0] - dot2[0]) + (dot[1] - dot2[1]) * (dot[1] - dot2[1])
                leftDots, leftLength = GetLaneOrder(leftLanes, 0)
                rightDots, rightLength = GetLaneOrder(rightLanes, 1)

                # 차선이 한쪽에만 있다가 없어지거나 하면 도로가 아예 안그려짐
                if length * 0.2 > abs(abs(leftLength - length) - abs(rightLength - length)) and \
                    length * 0.2 > abs(leftLength - length) and length * 0.2 > abs(rightLength - length):
                    dots = []
                    dots.extend(leftDots)
                    dots.extend(rightDots)
                    nCube, points, polys, scalars = GetCubeData(dots, nCube, points, polys, scalars)
                    drawFailed = False

            # 위의 방법으로 제대로 안그려지는 부분은 도로폭 400으로 그림
            # convex hull을 해놔서커브부분이 옆으로 삐겨나가는 부분이 있음..
            # convex hull을 -99999999,-99999999와 99999999,99999999로 구분해서 할 수 있으면 될 거 같긴한데...
            if drawFailed:
                dots = []
                s_dots = []
                e_dots = []
                for j in range(len(shapeRecord.shape.z) - 2):
                    dot = (SHPLocationTransform.GetLocation(
                        shapeRecord.shape.points[j][0],
                        shapeRecord.shape.points[j][1],
                        shapeRecord.shape.z[j]))

                    dot2 = (SHPLocationTransform.GetLocation(
                        shapeRecord.shape.points[j + 1][0],
                        shapeRecord.shape.points[j + 1][1],
                        shapeRecord.shape.z[j + 1]))

                    s1, s2, e1, e2 = GetLanePlane(dot[0], dot[1], dot[2], dot2[0], dot2[1], dot2[2], 400)

                    s_dots.append(s1)
                    e_dots.append(s2)
                    if j == len(shapeRecord.shape.z) - 3:
                        s_dots.append(e2)
                        e_dots.append(e1)

                dots.extend(s_dots)
                dots.extend([dot for dot in reversed(e_dots)])
                dots = ConvexHull(dots)

                nCube, points, polys, scalars = GetCubeData(dots, nCube, points, polys, scalars, 3)

        # 그리기
        roadPolyData = vtk.vtkPolyData()
        roadPolyData.SetPoints(points)
        roadPolyData.SetPolys(polys)
        roadPolyData.GetPointData().SetScalars(scalars)
        ret = roadPolyData

        file_io.write_stl_and_obj(roadPolyData, outputDir + '/' + outputFileName + '_')
        # vtk_utils.show_poly_data(roadPolyData)

    except BaseException as e:
        print(e)
    return ret


if __name__ == '__main__':
    import os

    strDir = '../../rsc/map_data/shp_03_Sungnam_PangyoZeroCity/HDMap_UTM52N'
    outputDir = '../../output2/{}'.format(datetime.now().strftime('%Y-%m-%d'))

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))
    strDir = os.path.normcase(strDir)
    strDir = os.path.join(current_path, strDir)
    strDir = os.path.normpath(strDir)

    # Change output to Absolute Path
    outputDir = os.path.normcase(outputDir)
    outputDir = os.path.join(current_path, outputDir)
    outputDir = os.path.normpath(outputDir)

    # Check if the output path exists
    if not os.path.isdir(outputDir):
        os.makedirs(outputDir)

    # Get Map Information
    mapInfo = read_shp_files(strDir)

    # Do Tasks
    DrawRoadBase(mapInfo, outputDir)

    print('[INFO] DrawRoad Finished')
