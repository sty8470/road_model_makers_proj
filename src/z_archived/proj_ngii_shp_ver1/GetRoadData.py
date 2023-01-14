import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import vtk
import math
from lib.common import file_io
from shp_common import *
from datetime import datetime

scale = 1

# 우선 mnsoft에서 사용한 방식으로 변경하기
# lanetype : 3자릿수, 첫자리 = 황색/흰색/청색, 두째자리 = 단선/겹선, 셋째자리 = 실선/점선/좌점혼선/우점혼선
# lanecode : 01-중앙선, 99-장애물
def GetLaneTypeToData(lanetype, lanecode):
    # 단선인데 선종류가 3,4인건 의미없음
    dict = {'111': (2, 1), '112': (2, 2), '113': (2, 1), '114': (2, 2),
            '121': (514, 257), '122': (514, 514), '123': (514, 258), '124': (514, 513),
            '211': (1, 1), '212': (1, 2), '213': (1, 1), '214': (1, 2),
            '221': (257, 257), '222': (257, 514), '223': (257, 258), '224': (257, 513),
            '311': (3, 1), '312': (3, 2), '313': (3, 1), '314': (3, 2),
            '321': (771, 257), '322': (771, 514), '323': (771, 258), '324': (771, 513)}

    if lanecode == '99':
        color, type, kind = 255, 129, 0
    elif lanecode == '01':
        color, type, kind = dict[lanetype][0], dict[lanetype][1], 2
    else:
        color, type, kind = dict[lanetype][0], dict[lanetype][1], 0
    return color, type, kind



def GetRoadDataSet(mapInfo):
    """
    laneSideData의 dict를 만든다. (이 값이 laneSideDataSet 라는 이름으로 기록되어 있음) 

    laneSideDataSet 내부의, 각각의 데이터 또한 dict 타입이며, 다음과 같은 정보를 담는다. 
    이 때, 각각의 dict에 접근하는 key는 dbf 파일의 HDUFID이다.

    각각의 데이터는 A1_LANE에서, CODE = 2 인 데이터, 즉 BARRIER인 타입만을 담는데,
    이 데이터의 dots 필드에는 각각을 구성하는 점들을 리스트로 기록하고,
    length 필드에는 각 점에서 점까지의 거리를 전부 계산하여, 이를 기록한다.

    각 laneSideData의 st_id, ed_id 필드 값을 데이터로부터 유추하여 계산하고 있음
    (코드 내부를 더 봐야 함)
    """
    laneSideShapeRecords = mapInfo['A1_LANE'].shapeRecords()
    laneSideDataSet = {}

    # 우선 laneSideDataSet을 생성한다 
    for shapeRecord in laneSideShapeRecords:
        record = shapeRecord.record
        # CODE가 2인 경우만 그려보기 (BARRIER인 것만 그림)
        if record['CODE'] != '2':
            pass#continue
        laneSideData = {'info': {}}
        dots = []
        length = 0
        dots.append(SHPLocationTransform.GetLocation(
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

            dots.append(SHPLocationTransform.GetLocation(
                shapeRecord.shape.points[i + 1][0],
                shapeRecord.shape.points[i + 1][1],
                _z))
                
            dx = dots[i + 1][0] - dots[i][0]
            dy = dots[i + 1][1] - dots[i][1]
            dz = dots[i + 1][2] - dots[i][2]
            length = length + math.sqrt(dx * dx + dy * dy + dz * dz)

        if length == 0:
            # 가끔씩 length가 0인 데이터가 있었음. 이런 데이터는 걸러야하므로 제외
            # raise BaseException('[ERROR] length is zero!')
            continue 
        laneSideData['length'] = length
        laneSideData['dots'] = dots

        # 점선문제로 차선을 연속된건 같이 그려야 해서 연속된걸 구하기 위하여 rn_id와 차선 번호를 저장
        # mnsoft에서 했던 방법인데 여기서도 사용해야 하긴해서 차선 대신 node id정보를 구해서 넣어야 함
        # 우선은 빈값으로 두기는 그래서 차선 정보를 넣음
        # 같은 차선 좌우 정도는 draw_road에 있는 방식으로 하면 되기는 할텐데 모든 선들에 대해서 구해야 될 거 같음...
        laneSideData['left_link'] = record['R_LINKID']
        laneSideData['right_link'] = record['L_LINKID']
        laneSideData['st_id'] = ''
        laneSideData['ed_id'] = ''
        laneSideDataSet[record['HDUFID']] = laneSideData

        strLS_ID = record['HDUFID']
        nATTR_TYPE = record['LANETYPE']
        nATTR_CODE = record['LANECODE']
        fST_RANGE = 0
        fED_RANGE = 1
        fWidth = 0.0015 * scale
        key = str(fST_RANGE)

        if key not in laneSideDataSet[strLS_ID]['info']:
            laneSideDataSet[strLS_ID]['info'][key] = {
                'start': fST_RANGE, 'end': fED_RANGE,
                'kind': 1,
                'width': fWidth}

        color, type, kind = GetLaneTypeToData(nATTR_TYPE, nATTR_CODE)

        laneSideDataSet[strLS_ID]['info'][key]['type'] = type
        laneSideDataSet[strLS_ID]['info'][key]['color'] = color
        laneSideDataSet[strLS_ID]['info'][key]['kind'] = kind

    # 생성된 laneSideDataSet의 start, end를 연결해준다
    for i in laneSideDataSet: # for laneSideDataSet의 key로 검색
        min = 0.1 * scale
        dot1 = laneSideDataSet[i]['dots'][-1]
        next = -1
        for j in laneSideDataSet:
            if i == j:
                continue
            dot2 = laneSideDataSet[j]['dots'][0]
            length = (dot1[0] - dot2[0]) * (dot1[0] - dot2[0]) + (dot1[1] - dot2[1]) * (dot1[1] - dot2[1])
            if min > length:
                min = length
                next = j
        if next != -1:
            laneSideDataSet[i]['ed_id'] = next
            laneSideDataSet[next]['st_id'] = i

    return laneSideDataSet
