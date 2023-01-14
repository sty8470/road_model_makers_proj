import vtk
import math
import threading
from lib.common import file_io
from shp_common import *
from datetime import datetime


# 차선 중심으로 width만큼 평면 구하기
def GetLanePlaneDouble(x1, y1, z1, x2, y2, z2, fWitdh, type, dotStart):
    fWitdh2 = fWitdh / 3
    if y1 == y2:
        s1 = (x1 - fWitdh / 2, y1, z1)
        s2 = (x1 - fWitdh2 / 2, y1, z1)
        e1 = (x2 - fWitdh / 2, y2, z2)
        e2 = (x2 - fWitdh2 / 2, y2, z2)

        s1_2 = (x1 + fWitdh2 / 2, y1, z1)
        s2_2 = (x1 + fWitdh / 2, y1, z1)
        e1_2 = (x2 + fWitdh2 / 2, y2, z2)
        e2_2 = (x2 + fWitdh / 2, y2, z2)
    elif x1 == x2:
        s1 = (x1, y1 - fWitdh / 2, z1)
        s2 = (x1, y1 - fWitdh2 / 2, z1)
        e1 = (x2, y2 - fWitdh / 2, z2)
        e2 = (x2, y2 - fWitdh2 / 2, z2)

        s1_2 = (x1, y1 + fWitdh2 / 2, z1)
        s2_2 = (x1, y1 + fWitdh / 2, z1)
        e1_2 = (x2, y2 + fWitdh2 / 2, z2)
        e2_2 = (x2, y2 + fWitdh / 2, z2)
    else:
        m = (y2 - y1) / (x2 - x1)
        r = fWitdh / 2
        r2 = fWitdh2 / 2
        a = x1 * x1 - (m * m * r * r) / (m * m + 1)
        a2 = x1 * x1 - (m * m * r2 * r2) / (m * m + 1)

        ax = (2 * x1 + math.sqrt(4 * x1 * x1 - 4 * a)) / 2
        bx = (2 * x1 + math.sqrt(4 * x1 * x1 - 4 * a2)) / 2
        ay = (-1 / m) * ax + y1 + x1 / m
        by = (-1 / m) * bx + y1 + x1 / m

        s1 = (ax, ay, z1)
        s2 = (bx, by, z1)
        e1 = (ax + (x2 - x1), ay + (y2 - y1), z2)
        e2 = (bx + (x2 - x1), by + (y2 - y1), z2)

        ax = (2 * x1 - math.sqrt(4 * x1 * x1 - 4 * a2)) / 2
        bx = (2 * x1 - math.sqrt(4 * x1 * x1 - 4 * a)) / 2
        ay = (-1 / m) * ax + y1 + x1 / m
        by = (-1 / m) * bx + y1 + x1 / m

        s1_2 = (ax, ay, z1)
        s2_2 = (bx, by, z1)
        e1_2 = (ax + (x2 - x1), ay + (y2 - y1), z2)
        e2_2 = (bx + (x2 - x1), by + (y2 - y1), z2)

    dots = []
    if type == 257:  # solid, solid
        dots = [[[s1, s2, e2, e1]], [[s1_2, s2_2, e2_2, e1_2]]]
    else:
        dx, dy, dz = e1[0] - s1[0], e1[1] - s1[1], e1[2] - s1[2]
        if type == 258:  # dot, solid
            start = ((s1[0] + s2[0]) / 2, (s1[1] + s2[1]) / 2, (s1[2] + s2[2]) / 2)
            dot, dotStart = GetDotLane(dx, dy, dz, 0, 1, start, fWitdh / 3, dotStart)
            dots.append(dot)
            dots.append([[s1_2, s2_2, e2_2, e1_2]])
        elif type == 513:  # solid, dot
            dots = [[[s1, s2, e2, e1]]]
            start = ((s1_2[0] + s2_2[0]) / 2, (s1_2[1] + s2_2[1]) / 2, (s1_2[2] + s2_2[2]) / 2)
            dot, dotStart = GetDotLane(dx, dy, dz, 0, 1, start, fWitdh / 3, dotStart)
            dots.append(dot)
        elif type == 514:  # dot, dot
            start = ((s1[0] + s2[0]) / 2, (s1[1] + s2[1]) / 2, (s1[2] + s2[2]) / 2)
            dot, dotStart = GetDotLane(dx, dy, dz, 0, 1, start, fWitdh / 3, dotStart)
            dots.append(dot)
            start = ((s1_2[0] + s2_2[0]) / 2, (s1_2[1] + s2_2[1]) / 2, (s1_2[2] + s2_2[2]) / 2)
            dot, dotStart = GetDotLane(dx, dy, dz, 0, 1, start, fWitdh / 3, dotStart)
            dots.append(dot)
    return dots, dotStart


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
        r = fWitdh / 2
        a = x1 * x1 - (m * m * r * r) / (m * m + 1)
        ax = (2 * x1 + math.sqrt(4 * x1 * x1 - 4 * a)) / 2
        bx = (2 * x1 - math.sqrt(4 * x1 * x1 - 4 * a)) / 2
        ay = (-1 / m) * ax + y1 + x1 / m
        by = (-1 / m) * bx + y1 + x1 / m

        s1 = (ax, ay, z1)
        s2 = (bx, by, z1)
        e1 = (ax + (x2 - x1), ay + (y2 - y1), z2)
        e2 = (bx + (x2 - x1), by + (y2 - y1), z2)

    return s1, s2, e2, e1


# 색, 타입 숫자값을 파일이름으로 쓸 텍스트로 변경
def GetLaneTypeColorToStr(color, type, kind):
    dictColor = {1: 'W', 2: 'Y', 3: 'B', 255: 'NONE', 257: 'W_W',
                 258: 'W_Y', 259: 'W_B', 513: 'Y_W', 514: 'Y_Y', 515: 'Y_B',
                 769: 'W_B', 770: 'Y_B', 771: 'B_B'}
    dictType = {1: 'solid', 2: 'dotted', 257: 'double_ss', 258: 'double_ds', 513: 'double_sd',
                514: 'double_dd', 128: 'curb', 129: 'barrier', 255: 'virtual'}
    # double_ss : 겹선, solid  + solid
    # double_ds : 겹선, dotted + solid
    # double_sd : 겹선, solid  + dotted
    # dobule_dd : 겹선, dotted + dotted
    try:
        strColor = dictColor[color]
    except:
        strColor = str(color)
    try:
        strType = dictType[type]
    except:
        strType = str(type)

    if kind == 2:
        strKind = '_center'
    else:
        strKind = ''

    return strColor + '_' + strType + strKind


def GetRoadDatas(mapInfo):
    laneSideShapeRecords = mapInfo['4_LANE_SIDE_Uiwang_20190212'].shapeRecords()
    laneSideAttrData = mapInfo['2_LANE_SIDE_ATTR_Uiwang_20190213']
    laneSideDatas = {}
    roadInfo = {}

    # LS_ID, ST_RN_ID, ST_SPOT_SE, ED_RN_ID, ED_SPOT_SE
    for shapeRecord in laneSideShapeRecords:
        laneSideData = {'info': {}}
        dots = []
        length = 0
        dots.append(
            (GetLocation(shapeRecord.shape.points[0][0], shapeRecord.shape.points[0][1], shapeRecord.shape.z[0])))

        min_z, max_z = shapeRecord.shape.z[0], shapeRecord.shape.z[len(shapeRecord.shape.z) - 1]
        if min_z > max_z:
            max_z, min_z = shapeRecord.shape.z[0], shapeRecord.shape.z[len(shapeRecord.shape.z) - 1]

        for i in range(len(shapeRecord.shape.z) - 1):
            _z = shapeRecord.shape.z[i + 1]
            if min_z > _z:
                _z = min_z
            if max_z < _z:
                _z = max_z

            dots.append((GetLocation(shapeRecord.shape.points[i + 1][0], shapeRecord.shape.points[i + 1][1], _z)))
            dx = dots[i + 1][0] - dots[i][0]
            dy = dots[i + 1][1] - dots[i][1]
            dz = dots[i + 1][2] - dots[i][2]
            length = length + math.sqrt(dx * dx + dy * dy + dz * dz)
        laneSideData['length'] = length
        laneSideData['dots'] = dots

        # 점선문제로 차선을 연속된건 같이 그려야 해서 연속된걸 구하기 위하여 rn_id와 차선 번호를 저장
        laneSideData['st_id'] = "%d_%d" % (shapeRecord.record[1], shapeRecord.record[2])
        laneSideData['ed_id'] = "%d_%d" % (shapeRecord.record[3], shapeRecord.record[4])
        laneSideDatas[shapeRecord.record[0]] = laneSideData

    # RL_ID, SIDE_SEQ를 이용하여 LANE_SIDE를 특정하고, ATTR_CLASS, ATTR_CODE를 가지고 차선 정보를 만듬
    # RL_ID, SIDE_SEQ, ATTR_CLASS, ATTR_SEQ, ST_RANGE, ED_RANGE, ATTR_CODE, WIDTH
    for record in laneSideAttrData.records():
        if not record[0] in roadInfo:
            roadInfo[record[0]] = []
        if not record[1] in roadInfo[record[0]]:
            roadInfo[record[0]].append(record[1])
        roadInfo[record[0]].sort()

        strLS_ID = str(record[0]) + '_' + str(record[1])
        nATTR_CLASS = record[2]
        nATTR_CODE = record[6]
        fST_RANGE = record[4]
        fED_RANGE = record[5]
        fWidth = record[7] * 100
        key = str(fST_RANGE)

        if key not in laneSideDatas[strLS_ID]['info']:
            laneSideDatas[strLS_ID]['info'][key] = {'start': fST_RANGE, 'end': fED_RANGE, 'kind': 1,
                                                    'width': fWidth}
        if nATTR_CLASS == 1:  # type
            laneSideDatas[strLS_ID]['info'][key]['type'] = nATTR_CODE
        elif nATTR_CLASS == 2:  # color
            laneSideDatas[strLS_ID]['info'][key]['color'] = nATTR_CODE
        elif nATTR_CLASS == 5:  # kind
            laneSideDatas[strLS_ID]['info'][key]['kind'] = nATTR_CODE

    return laneSideDatas, roadInfo


def GetDotLane(dx, dy, dz, dStartPart, dEndPart, start, fWidth, dotStart):
    from copy import deepcopy
    dots = []
    full_length = math.sqrt(dx * dx + dy * dy + dz * dz) * (dEndPart - dStartPart)
    dot_length = 300
    blank_length = 500
    interval = [dot_length / full_length, blank_length / full_length]
    nType = 0
    flag = True
    current = deepcopy(dotStart / full_length)

    while flag:
        end = current + interval[nType]
        if end >= dEndPart:
            end = dEndPart
            flag = False
        if nType == 0:
            if current < 0:
                current = 0
            if current < end:
                dots.append(GetLanePlane(start[0] + dx * current, start[1] + dy * current, start[2] + dz * current,
                                         start[0] + dx * end, start[1] + dy * end, start[2] + dz * end, fWidth))
            dotStart = current
        else:
            dotStart = current + interval[nType]
        nType = 1 - nType
        current = end
    return dots, (dotStart - 1) * full_length


def __GetNewPolyData():
    return {
        'points': vtk.vtkPoints(),
        'polys': vtk.vtkCellArray(),
        'scalars': vtk.vtkFloatArray(),
        'nCube': 0
    }


def __GetCubeData(polyData, dots, fHeight):
    for i in range(len(dots)):
        polyData['nCube'], polyData['points'], polyData['polys'], polyData['scalars'] = GetCubeData(dots[i],
                                                                                                    polyData['nCube'],
                                                                                                    polyData['points'],
                                                                                                    polyData['polys'],
                                                                                                    polyData['scalars'],
                                                                                                    fHeight)
    return polyData


def GetLanePolyDatas(polyDatas, laneSideData, dotStart):
    dLength = 0
    for _, data in laneSideData['info'].items():
        key = GetLaneTypeColorToStr(data['color'], data['type'], data['kind'])
        # 너비정보가 있는 경우
        fWidth = data['width'] if data['width'] > 1 else 10
        # 연석이나 장애물, 가상선은 높이 바꿈
        fHeight = 15 if data['type'] == 128 else (
            35 if data['type'] == 129 else (5 if data['type'] == 255 else 6))

        # 겹선 처리
        if data['type'] == 257 or data['type'] == 258 or data['type'] == 513 or data['type'] == 514:
            key1 = key + '_left'
            key2 = key + '_right'
            if key1 not in polyDatas:
                polyDatas[key1] = __GetNewPolyData()
            if key2 not in polyDatas:
                polyDatas[key2] = __GetNewPolyData()

            for i in range(len(laneSideData['dots']) - 1):
                start = laneSideData['dots'][i];
                end = laneSideData['dots'][i + 1];
                dx, dy, dz = end[0] - start[0], end[1] - start[1], end[2] - start[2]
                dStartPart, dEndPart = GetOverlap(dLength / laneSideData['length'],
                                                  (dLength + math.sqrt(dx * dx + dy * dy + dz * dz)) /
                                                  laneSideData['length'], data['start'], data['end'])
                if dStartPart >= dEndPart:
                    continue

                # 겹선 정보 저장
                dots, dotStart = GetLanePlaneDouble(start[0] + dx * dStartPart, start[1] + dy * dStartPart,
                                                    start[2] + dz * dStartPart, start[0] + dx * dEndPart,
                                                    start[1] + dy * dEndPart, start[2] + dz * dEndPart, fWidth,
                                                    data['type'], dotStart)
                polyDatas[key1] = __GetCubeData(polyDatas[key1], dots[0], fHeight)
                polyDatas[key2] = __GetCubeData(polyDatas[key2], dots[1], fHeight)
                dLength = dLength + math.sqrt(dx * dx + dy * dy + dz * dz)

        # 나머지 처리
        else:
            if key not in polyDatas:
                polyDatas[key] = __GetNewPolyData()

            for i in range(len(laneSideData['dots']) - 1):
                start = laneSideData['dots'][i];
                end = laneSideData['dots'][i + 1];
                dx, dy, dz = end[0] - start[0], end[1] - start[1], end[2] - start[2]
                dStartPart, dEndPart = GetOverlap(dLength / laneSideData['length'],
                                                  (dLength + math.sqrt(dx * dx + dy * dy + dz * dz)) /
                                                  laneSideData['length'], data['start'], data['end'])
                if dStartPart >= dEndPart:
                    continue

                dots = []
                # 점선 정보 저장
                if data['type'] == 2:
                    dots, dotStart = GetDotLane(dx, dy, dz, dStartPart, dEndPart, start, fWidth, dotStart)
                # 일반 차선 저장
                else:
                    dots.append(GetLanePlane(start[0] + dx * dStartPart, start[1] + dy * dStartPart,
                                             start[2] + dz * dStartPart, start[0] + dx * dEndPart,
                                             start[1] + dy * dEndPart, start[2] + dz * dEndPart, fWidth))
                polyDatas[key] = __GetCubeData(polyDatas[key], dots, fHeight)
                dLength = dLength + math.sqrt(dx * dx + dy * dy + dz * dz)
    return dotStart


def GetNextPolyDatas(polyDatas, laneSideDatas, current, flag, dotStart):
    # 점선 시작시 이전 구간이 점선이면 어디까지 그렸는지를 넣을 수 있게 바꾸면 될 거 같음
    dotStart = GetLanePolyDatas(polyDatas, current, dotStart)

    for key, laneSideData in laneSideDatas.items():
        # 연결된 거 쭉 찾아서 그리기
        if current['ed_id'] == laneSideData['st_id']:
            if key not in flag:
                flag.append(key)
                GetNextPolyDatas(polyDatas, laneSideDatas, laneSideData, flag, dotStart)
            break


def GetPolyDataSet(laneSideDatas):
    polyDatas = {}
    endKeys = []
    flag = []

    # ed_id로 나오는 것들 저장
    for _, laneSideData in laneSideDatas.items():
        endKeys.append(laneSideData['ed_id'])

    for key, laneSideData in laneSideDatas.items():
        # st_id들 중에 사용안한 것만 사용
        if key not in flag and key not in endKeys:
            flag.append(key)
            GetNextPolyDatas(polyDatas, laneSideDatas, laneSideData, flag, 0)

    return polyDatas


def DrawLane(mapInfo, outputDir, outputFileName='RoadLane', optionText=''):
    try:
        # 두파일에 나눠져 있는 차선 정보 기록위한 데이터
        laneSideDatas, roadInfo = GetRoadDatas(mapInfo)
        polyDatas = GetPolyDataSet(laneSideDatas)

        # 차선 그리기
        for strPrefix, data in polyDatas.items():
            linesPolyData = vtk.vtkPolyData()
            linesPolyData.SetPoints(data['points'])
            linesPolyData.SetPolys(data['polys'])
            linesPolyData.GetPointData().SetScalars(data['scalars'])

            # strFileName = 'LaneSide_NoZ_' + strPrefix + '_190908_PM0428'
            strFileName = outputFileName + '_' + strPrefix + '_' + optionText
            file_io.write_stl_and_obj(linesPolyData, outputDir + '/' + strFileName)

    except BaseException as e:
        print('[ERROR] Error @ DrawLane, Msg:', e)


def DrawRoadBase(mapInfo, outputDir, outputFileName='RoadBaseFromLane', optionText=''):
    try:
        # 두파일에 나눠져 있는 차선 정보 기록위한 데이터
        laneSideDatas, roadInfo = GetRoadDatas(mapInfo)
        # polyDatas = GetPolyDataSet(laneSideDatas)

        # 도로 평면 그리기
        points = vtk.vtkPoints()
        polys = vtk.vtkCellArray()
        scalars = vtk.vtkFloatArray()
        nCube = 0
        for strRL_ID, seq in roadInfo.items():
            # 0이랑 마지막으로 차선 구간 평면 만듬
            dots = []
            strLS_ID_1 = "%d_%d" % (strRL_ID, seq[0])
            lane1 = laneSideDatas[strLS_ID_1]
            for dot in lane1['dots']:
                dots.append(dot)
            strLS_ID_1 = "%d_%d" % (strRL_ID, seq[len(seq) - 1])
            lane1 = laneSideDatas[strLS_ID_1]
            for dot in reversed(lane1['dots']):
                dots.append(dot)
            nCube, points, polys, scalars = GetCubeData(dots, nCube, points, polys, scalars, 5)

            # 높낮이가 안맞는 부분이 있을 수 있으니 각 차선별로도 만듬
            for i in range(len(seq) - 1):
                dots = []
                strLS_ID_1 = "%d_%d" % (strRL_ID, seq[i])
                lane1 = laneSideDatas[strLS_ID_1]
                for dot in lane1['dots']:
                    dots.append(dot)
                strLS_ID_1 = "%d_%d" % (strRL_ID, seq[i + 1])
                lane1 = laneSideDatas[strLS_ID_1]
                for dot in reversed(lane1['dots']):
                    dots.append(dot)
                nCube, points, polys, scalars = GetCubeData(dots, nCube, points, polys, scalars, 5)
        # 도로 평면 그리기
        roadPolyData = vtk.vtkPolyData()
        roadPolyData.SetPoints(points)
        roadPolyData.SetPolys(polys)
        roadPolyData.GetPointData().SetScalars(scalars)
        file_io.write_stl_and_obj(roadPolyData, outputDir + '/' + outputFileName + '_' + optionText)

    except BaseException as e:
        print('[ERROR] Error @ DrawBaseRoad, Msg:', e)


if __name__ == '__main__':
    import os

    strDir = '../rsc/map_data/shp_HDMap_Uiwang_190213_WGS'
    outputDir = '../output/{}'.format(datetime.now().strftime('%Y-%m-%d'))

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
    DrawLane(mapInfo, outputDir)
