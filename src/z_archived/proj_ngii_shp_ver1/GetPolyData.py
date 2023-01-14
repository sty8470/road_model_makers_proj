import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import vtk
import math
from lib.common import file_io
from shp_common import *
from datetime import datetime
#
scale = 1

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


def GetDotLane(dx, dy, dz, dStartPart, dEndPart, start, fWidth, dotStart):
    from copy import deepcopy
    dots = []
    full_length = math.sqrt(dx * dx + dy * dy + dz * dz) * (dEndPart - dStartPart)
    dot_length = 3 * scale
    blank_length = 5 * scale
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

def GetLanePolyDatas(polyDataSet, laneSideData, dotStart):
    dLength = 0
    for _, data in laneSideData['info'].items():
        key = GetLaneTypeColorToStr(data['color'], data['type'], data['kind'])
        
        fWidth = data['width'] * scale if data['width'] > 0.01 * scale else 0.1 * scale
        # # 너비정보가 있는 경우
        # if data['width'] > 0.01 * scale:
        #     fWidth = data['width']
        # else:
        #     fWidth = 0.1 * scale
        
        fHeight = 0.15 * scale if data['type'] == 128 else (
            0.35 * scale if data['type'] == 129 else (0.05 * scale if data['type'] == 255 else 0.06 * scale))
        # # 연석이나 장애물, 가상선은 높이 바꿈
        # if data['type'] == 128:
        #     fHeight = 0.15 * scale
        # elif data['type'] == 129:
        #     fHeight = 0.35 * scale
        # elif data['type'] == 255:
        #     fHeight = 0.05 * scale
        # else:
        #     fHeight = 0.06 * scale

        # 겹선 처리
        if data['type'] == 257 or data['type'] == 258 or data['type'] == 513 or data['type'] == 514:
            key1 = key + '_left'
            key2 = key + '_right'
            if key1 not in polyDataSet:
                polyDataSet[key1] = __GetNewPolyData()
            if key2 not in polyDataSet:
                polyDataSet[key2] = __GetNewPolyData()

            for i in range(len(laneSideData['dots']) - 1):
                start = laneSideData['dots'][i]
                end = laneSideData['dots'][i + 1]
                dx, dy, dz = end[0] - start[0], end[1] - start[1], end[2] - start[2]
                if laneSideData['length'] == 0:
                    raise BaseException('[ERROR] length is zero!!')
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
                polyDataSet[key1] = __GetCubeData(polyDataSet[key1], dots[0], fHeight)
                polyDataSet[key2] = __GetCubeData(polyDataSet[key2], dots[1], fHeight)
                dLength = dLength + math.sqrt(dx * dx + dy * dy + dz * dz)

        # 나머지 처리
        else:
            if key not in polyDataSet:
                polyDataSet[key] = __GetNewPolyData()

            for i in range(len(laneSideData['dots']) - 1):
                start = laneSideData['dots'][i]
                end = laneSideData['dots'][i + 1]
                dx, dy, dz = end[0] - start[0], end[1] - start[1], end[2] - start[2]
                if laneSideData['length'] == 0:
                    raise BaseException('[ERROR] length is zero!')
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
                polyDataSet[key] = __GetCubeData(polyDataSet[key], dots, fHeight)
                dLength = dLength + math.sqrt(dx * dx + dy * dy + dz * dz)
    return dotStart


def GetNextPolyDatas(polyDataSet, laneSideDataSet, current, flag, dotStart):
    # 점선 시작시 이전 구간이 점선이면 어디까지 그렸는지를 넣을 수 있게 바꾸면 될 거 같음
    dotStart = GetLanePolyDatas(polyDataSet, current, dotStart)

    if current['ed_id'] == '':
        return

    for key, laneSideData in laneSideDataSet.items():
        # 연결된 거 쭉 찾아서 그리기
        if laneSideData['st_id'] == '':
            continue
        if current['ed_id'] == key:#laneSideData['st_id']:
            if key not in flag:
                flag.append(key)
                GetNextPolyDatas(polyDataSet, laneSideDataSet, laneSideData, flag, dotStart)
            break


def GetPolyDataSet(laneSideDataSet):
    polyDataSet = {}
    endKeys = []
    flag = []

    # ed_id로 나오는 것들 저장
    for _, laneSideData in laneSideDataSet.items():
        if laneSideData['ed_id'] == '':
            continue
        endKeys.append(laneSideData['ed_id'])

    for key, laneSideData in laneSideDataSet.items():
        # st_id들 중에 사용안한 것만 사용
        if key not in flag and key not in endKeys:
            flag.append(key)
            GetNextPolyDatas(polyDataSet, laneSideDataSet, laneSideData, flag, 0)

    return polyDataSet