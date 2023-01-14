import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import vtk
import math
from lib.common import file_io
from shp_common import *
from datetime import datetime


def GetNextOutlineData(dots, laneSideDatas, current, flag, start):
    if current['ed_id'] == '':
        return

    # 연결된 거 쭉 찾아서 그리기
    for key, laneSideData in laneSideDatas.items():
        if current['ed_id'] == key:
            if key not in flag:
                flag.append(key)
                for dot in laneSideData['dots']:
                    if dot in dots:
                        continue
                    dots.append(dot)
                GetNextOutlineData(dots, laneSideDatas, laneSideData, flag, start)
            break


def GetOutlineDataSet(laneSideDatas):
    """
    outlineDatas는 리스트로,
    우선 내부적으로 Barrier 객체들간을 이어둔다. 그러면,
    연결이 안 되는 객체들끼리 남을텐데, 예를 들면 아래와 같다.

    연결된 Barrier 1) Barrier 01 - Barrier 05 - Barrier 07
    연결된 Barrier 2) Barrier 02 - Barrier 04
    연결된 Barrier 3) Barrier 03 - Barrier 06 - Barrier 08 - Barrier 09
    
    그러면, 이 outlineDataSet 리턴값은 다음을 가지게 된다.
    [연결된 Barrier 1의 점, 연결된 Barrier 2의 점, 연결된 Barrier 3의 점, ...]
    """
    outlineDataSet = []
    endKeys = []
    flag = []

    # 외곽선만 그리기 위해, Barrier 인 데이터만 outlinelaneSideData Dict 타입으로 저장.
    outlinelaneSideDatas = {}
    for key, laneSideData in laneSideDatas.items():
        if laneSideData['info']['0']['type'] != 129: 
            # MNSOFT에서 Barrier, NGII 데이터의 경우도 MNSOFT형식으로 변경하여 이렇게 저장하고 있기 때문에 이렇게 사용 가능
            continue
        outlinelaneSideDatas[key] = laneSideData
        outlinelaneSideDatas[key]['st_id'] = ''
        outlinelaneSideDatas[key]['ed_id'] = ''

    # Barrier 데이터 사이에서 다음을 찾는다
    for i in outlinelaneSideDatas:
        # 현재 Barrier의 끝점을 찾는다
        dot1 = outlinelaneSideDatas[i]['dots'][-1]
        # 
        next = -1

        for j in outlinelaneSideDatas:
            # 현재 Barrier 말고, 다른 Barrier 객체이면서, st_id가 저장된 값만 본다.
            if i == j or outlinelaneSideDatas[j]['st_id'] != '':
                continue
            
            # 그러한 값들 가운데, 첫번째 점의 위치를 본다. 
            dot2 = outlinelaneSideDatas[j]['dots'][0]

            # 즉, Barrier A의 끝점과, Barrier B의 시작점의 거리를 구한다.
            length = (dot1[0] - dot2[0]) * (dot1[0] - dot2[0]) + (dot1[1] - dot2[1]) * (dot1[1] - dot2[1])

            # 만약 두 점의 거리가 0이다. 그러면 Barrier A의 next 는 Barrier B 이다.
            if length == 0:
                next = j

        # next를 찾았다먼, BarrierA의 ed_id로 BarrierB를 저장하고, BarrierB의 st_id로 BarrierA를 저장한다.
        if next != -1:
            outlinelaneSideDatas[i]['ed_id'] = next
            outlinelaneSideDatas[next]['st_id'] = i

    # ed_id로 나오는 것들 저장
    for _, laneSideData in outlinelaneSideDatas.items():
        if laneSideData['ed_id'] == '':
            continue
        endKeys.append(laneSideData['ed_id'])

    for key, laneSideData in outlinelaneSideDatas.items():
        # st_id들 중에 사용안한 것만 사용
        if key not in flag and key not in endKeys:
            dots = [dot for dot in laneSideData['dots']] # dots = laneSideData['dots'] 와 동일
            flag.append(key)
            GetNextOutlineData(dots, outlinelaneSideDatas, laneSideData, flag, key)
            outlineDataSet.append(dots)

    return outlineDataSet