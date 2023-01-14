import vtk
import os
import shapefile
import random
import numpy as np
import math
import file_io
import vtk_utils
from coord_trans_llh2utmlocal import CoordTrans_LLH2UTMLocal 


def get_first_shp_point(sf):
    '''
    해당 shape에서 발견되는 첫번째 record의 첫번째 점의 위치를 origin으로 한다.
    '''
    shapes = sf.shapes()
    origin_e = shapes[0].points[0][0]
    origin_n = shapes[0].points[0][1]
    origin_z = shapes[0].z[0]
    origin = [origin_e, origin_n, origin_z]
    return origin

def GetShpFileDict(input_path):
    ret = None
    try:
        file_list = os.listdir(input_path)
        map_info = {}
        
        for each_file in file_list:
            # each_file이 폴더에 해당하면 스킵
            if os.path.isdir(os.path.join(input_path, each_file)):
                continue

            # 파일명에서 확장자를 제외
            each_file = each_file[:-4]

            import platform
            # 맥 체크용, 맥에서는 ansi안됨
            if platform.system() =='Darwin':
                map_info[each_file] = shapefile.Reader(os.path.join(input_path, each_file))
            else:
                map_info[each_file] = shapefile.Reader(os.path.join(input_path, each_file), encoding='ansi')
                try:
                    # 파일마다 utf-8이랑 ansi가 섞여있어서 둘중 에러안나는걸로 로드하도록
                    map_info[each_file].shapeRecords()
                except:
                    map_info[each_file] = shapefile.Reader(os.path.join(input_path, each_file))

        ret = map_info

    except BaseException as e:
        print(e)
    return ret        

def read_shp_files(input_path):
    ret = None
    try:
        file_list = os.listdir(input_path)
        map_info = {}

        for each_file in file_list:
            # Sub-directory를 검사
            if os.path.isdir(os.path.join(input_path, each_file)):
                # Sub-directory가 있으면, Sub-directory에서 이를 다시 호출
                map_info.update(read_shp_files(os.path.join(input_path, each_file)))
                continue

            # DBF 파일을 기준으로 아래를 실행하도록 한다.
            # 즉 A1_NODE.dbf 파일이 있는 경우에만
            # A1_NODE를 읽도록 한다
            # TODO: elif 에서 el 제외?
            elif not each_file.lower().endswith('.dbf'):
                continue

            each_file = each_file[:-4]
            import platform
            # 맥 체크용, 맥에서는 ansi안됨
            if platform.system() =='Darwin':
                map_info[each_file] = shapefile.Reader(os.path.join(input_path, each_file))
            else:
                map_info[each_file] = shapefile.Reader(os.path.join(input_path, each_file), encoding='ansi')
                try:
                    # 파일마다 utf-8이랑 ansi가 섞여있어서 둘중 에러안나는걸로 로드하도록
                    map_info[each_file].shapeRecords()
                except:
                    map_info[each_file] = shapefile.Reader(os.path.join(input_path, each_file))
        ret = map_info
    except BaseException as e:
        print(e)
    return ret


def InspectData_GetTypeName(one_shp_data):
    """
    GetMapInfo로 얻은 데이터 중 하나를 입력하면
    예: map_data = read_shp_files(input_path)
    InspectData(map_data['A1_NODE']) 로 호출
    데이터를 보여준다
    """
    shapes = one_shp_data.shapes()

    # 다른 데이터를 얻으려면 아래와 같이 한다
    # records  = one_shp_data.records()
    # fields = one_shp_data.fields
    return shapes[0].shapeTypeName


class SHPLocationTransform:
    x0 = None
    y0 = None
    z0 = None

    @classmethod
    def SetOrigin(cls, origin):
        cls.x0 = origin[0]
        cls.y0 = origin[1]
        cls.z0 = origin[2]

    @classmethod
    def GetLocation(cls, x, y, z):
        # [NOTE] 소수점값이 있으면 그림이 이상하게 그려짐
        # 기존에 100이 곱해져 있어서 (UE4용, 일단은 100을 곱한 값으로 한다)

        # x_rel = round(x - cls.x0, 2)
        # y_rel = round(y - cls.y0, 2)
        # z_rel = round(z - cls.z0, 2)

        x_rel = x - cls.x0
        y_rel = y - cls.y0
        z_rel = z - cls.z0

        # x_rel = round((x - cls.x0)*100, 0)
        # y_rel = round((y - cls.y0)*100, 0)
        # z_rel = round((z - cls.z0)*100, 0)
        return (x_rel, y_rel, z_rel) 


# 좌표 위도 경도 환산 후 좌표 이동해놓음, 안그러면 유효숫자 때문에 짤려서 제대로 안그려짐
def GetLocation(x, y, z, ignore_z=True):
    conv_obj = CoordTrans_LLH2UTMLocal(52, [319055.515808, 4132929.959581, 90.280800])
    lat = y
    lon = x
    east, north, alt = conv_obj.llh2utmlocal(lat, lon, z)
    # UE4에서는 cm 단위로 되어있으므로 100을 곱해준다. 단, z는 0으로 스케일한다
    east = east * 100
    north = north * 100
    if ignore_z:
        alt = alt * 0
    else:
        alt = int(alt * 1000)/10
    return east, north, alt


# NOTE: 이제 사용하지 않기로 함. 원점이 고정되어 있는 것이 가장 큰 문제. 
def GetLocation2(x, y, z):
    raise BaseException('[ERROR] 이제 사용하지 않기로 함. 대신 SHPLocationTransform.GetLocation을 사용해야 함. (현재 메소드는 원점이 고정되어 있는 것이 문제)')
    # 소수점값이 있으면 그림이 이상하게 그려짐
    # return (round((x - 331850) * 100, 0), round((y - 4141850) * 100, 0), 0)#z * 100)


def OnSegment(p, q, r):
    ret = False
    if q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]):
        ret = True
    return ret


# 선 두개가 교차하거나 만나는지 확인
def CrossCheck(s1, e1, s2, e2):
    o1 = ShoelaceFormula2([s1, e1, s2])
    o2 = ShoelaceFormula2([s1, e1, e2])
    o3 = ShoelaceFormula2([s2, e2, s1])
    o4 = ShoelaceFormula2([s2, e2, e1])

    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and OnSegment(s1, s2, e1):
        return True
    if o2 == 0 and OnSegment(s1, e2, e1):
        return True
    if o3 == 0 and OnSegment(s2, s1, e2):
        return True
    if o4 == 0 and OnSegment(s2, e1, e2):
        return True
    return False


def ShoelaceFormula(dot):
    # 판 방향 확인
    fSum = 0.0

    x = dot[0][0]
    y = dot[0][1]
    for i in range(len(dot) - 1):
        fSum = fSum + (dot[i][0] - x) * (dot[i + 1][1] - y) - (dot[i][1] - y) * (dot[i + 1][0] - x)
    # 어차피 0이라서 안해도 됨
    # fSum = fSum + (dot[len(dot) - 1][0] - x) * (dot[0][1] - y) - (dot[len(dot) - 1][1] - y) * (dot[0][0] - x)

    return fSum


def ShoelaceFormula2(dot):
    fSum = ShoelaceFormula(dot)

    if fSum > 0:
        ret = 1
    elif fSum < 0:
        ret = -1
    else:
        ret = 0
    return ret


# 점 순서 확인을 위한 함수
def CheckDotOrder(dots):
    ret = dots
    if ShoelaceFormula(dots) < 0:
        ret = [dot for dot in reversed(dots)]

    return ret


# 다각형의 위아래 면과 옆면들 만듬
def GetCubeData(dots, nDotCount, points, polys, scalars, height=10, isHole=False):
    nLength = len(dots)
    dots = CheckDotOrder(dots)

    if isHole:
        dots = [dot for dot in reversed(dots)]
    # 점
    x = []
    for dot in dots:
        x.append((dot[0], dot[1], dot[2] + height))
    for dot in dots:
        x.append(dot)

    # 면
    if isHole:
        pts = []
    else:
        pts = [(nDotCount + i for i in range(nLength))]
        pts.append((nDotCount + (nLength * 2 - i - 1) for i in range(nLength)))
    for i in range(nLength):
        pts.append(((i + 1) % nLength + nDotCount, i + nDotCount, i + nLength + nDotCount, (i + 1) % nLength + nLength + nDotCount))

    # 데이터 저장
    for i in range(nLength * 2):
        points.InsertPoint(nDotCount + i, x[i])
    if isHole:
        for i in range(nLength):
            polys.InsertNextCell(vtk_utils.convert_to_vtkIdList(pts[i]))
    else:
        for i in range(nLength + 2):
            polys.InsertNextCell(vtk_utils.convert_to_vtkIdList(pts[i]))
    for i in range(nLength * 2):
        scalars.InsertTuple1(nDotCount + i, nDotCount + i)

    nDotCount = nDotCount + nLength * 2
    return nDotCount, points, polys, scalars


def GetOverlap(s1, e1, s2, e2):
    retS = 1
    retE = 0
    if s2 <= s1 and e1 <= e2:
        retS = s1
        retE = e1
    elif s2 <= s1 and s1 <= e2 and e2 <= e1:
        retS = s1
        retE = e2
    elif s1 <= s2 and s2 <= e1 and e1 <= e2:
        retS = s2
        retE = e1
    elif s1 <= s2 and e2 <= e1:
        retS = s2
        retE = e2

    if retS < retE:
        retS = (retS - s1) / (e1 - s1)
        retE = (retE - s1) / (e1 - s1)

    return retS, retE
