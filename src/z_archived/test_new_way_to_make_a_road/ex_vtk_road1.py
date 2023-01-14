"""
도로를 만드는 가장 기본적인 예제
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import vtk
import numpy as np
from lib.common import display, file_io, vtk_utils


def util_calc_inc_deg(t, inc):
    import math
    return math.atan2(t, inc) * 180 /math.pi


def _make_vertices():
    """
    도로의 3D형상을 정의하기 위한 각 점을 만들어 list로 반환한다.
    각각의 점은 해당 점의 x,y,z 위치 좌표(tuple)로 정의된다.
    :return: 도로의 3D 형상을 정의하는 각 점의 list
    """
    w = 100  # 도로 폭
    t = 10  # 도로 두께
    inc = 20  # 경사면에 의한 깊이
    l = 100  # 도로 길이

    road_start = [[0, 0, 0], [w, 0, 0], [w, t, inc], [0, t, inc]]
    road_end = [[0, 0, l], [w, 0, l], [w, t, l-inc], [0, t, l-inc]]
    return road_start + road_end


def _make_faces():
    """
    도로의 3D형상을 정의하기 위한 각 면을 만들어 list로 반환한다.
    각각의 면은 해당 면을 정의하는 점의 인덱스의 집합(tuple)로 정의된다.

    만약 어떤 면이 (3,2,1,0)으로 정의되어 있다면,
    이 면은 본 예제에서 _make_vertices 로 생성되는 점 리스트에서
    3,2,1,0 인덱스에 있는 점으로 구성되는 면이라는 뜻이다.

    한편, 각각의 면을 정의하는 점의 인덱스 사이의 순서가 중요한데,
    이로부터 면의 방향 (normal vector)가 정의되기 때문이다.

    예를 들어 (3,2,1,0)으로 정의한 면과 (0,1,2,3)으로 정의한 면의
    방향은 서로 반대이다.

    :return:  도로의 3D 형상을 정의하는 각 면의 list
    """
    # 경사면
    face_vertices_list = [[3, 2, 1, 0], [6, 7, 4, 5]]

    # 도로 표면 & 도로 아랫면
    face_vertices_list += [[7, 6, 2, 3], [0, 1, 5, 4]]

    # 도로 옆면
    face_vertices_list += [[2, 6, 5, 1], [7, 3, 0, 4]]

    return face_vertices_list


def make_road():
    """
    도로의 3D 형상에 해당하는 vtkPolyData 타입의 데이터를 만들어 반환한다.
    :return: 도로의 3D 형상에 해당하는 vtkPolyData 타입 데이터
    """

    # 도로의 3D 형상을 정의하기 위한 점과 면의 리스트를 생성한다.
    py_vertices = _make_vertices()
    py_faces = _make_faces()

    print("---------- py_vertices----------")
    print(py_vertices)

    print("---------- py_faces----------")
    print(py_faces)


    # 최종적으로는 아래 vtkPolyData 타입의 road 변수를 만들어 반환할 것이다.
    road = vtk.vtkPolyData()

    # 위 road 변수를 만들기 위해 다음 타입의 변수들을 먼저 만들어야 한다.
    vtk_vertices = vtk.vtkPoints()  # 점 정보
    vtk_faces = vtk.vtkCellArray()  # 면 정보
    vtk_scalars = vtk.vtkFloatArray()  # 각 점에 스칼라값을 할당할 수 있는데, 그 정보를 담는 객체이다.
    # [참고] vtk_scalars 변수는 여기서는 필요한 것은 아니긴 함. 참고용으로 넣어둠.

    # 1) vtkPoint 타입의 변수를 만든다.
    print('\n-------- make vtk_vertices --------')
    for i, xi in enumerate(py_vertices):
        print('  i = {}, xi = {}'.format(i, xi))
        vtk_vertices.InsertPoint(i, xi)

    # 2) vtkCellArray 타입의 변수를 만든다.
    print('\n-------- make vtk_faces --------')
    for pt in py_faces:
        print('  pt = {}'.format(pt))

        # tuple을 바로 넣을 수 없고, vtkIdList 타입을 만들어서 이를 전달해야
        # vtkCellArray 타입의 객체를 초기화할 수 있다
        vil = vtk_utils.convert_to_vtkIdList(pt)
        print('  vil = [{0}, {1}, {2}, {3}] (vtkIdList Type)'.format(vil.GetId(0), vil.GetId(1), vil.GetId(2), vil.GetId(3)))

        vtk_faces.InsertNextCell(vil)

    # 3) vtkFloatArray 타입의 변수를 만든다.
    print('\n-------- make vtk_scalars --------')
    for i, _ in enumerate(py_vertices):
        print('  CALL: vtk_scalars.InsertTuple1({0}, {0})'.format(i))
        vtk_scalars.InsertTuple1(i, i)

    # 1) 만들어진 vtkPoint 타입 변수를 출력해본다.
    print('\n-------- Vertices (arg: vtk_vertices, type: vtkPoints) --------')
    for i in range(0, vtk_vertices.GetNumberOfPoints()):
        print('  vtk_vertices.GetPoint({}) = {}'.format(i, vtk_vertices.GetPoint(i)))

    # 2) 만들어진 vtkCellArray 타입 변수를 출력해본다.
    # vtkCellArray 타입의 인스턴스인 polys는 각 면을 구성하는 꼭지점에 대한 index를 담고있다.
    print('\n-------- Faces (arg: vtk_faces,  type: vtkCellArray) --------')
    # for i in range(0, vtk_faces.GetNumberOfCells()):
    #     print('  cells.GetCell({}) = {}'.format(i, vtk_faces.GetCell(i)))

    # vtkCellArray를 이렇게 받아오면 되나?
    # syntax: V.GetNextCell(vtkIdList) -> int
    # first DO
    num_call = 0
    idList = vtk.vtkIdList()
    ret = vtk_faces.GetNextCell(idList)
    if ret == 0:
        print('[ERROR] ret = vtk_faces.GetNextCell(idList) returned 0! at num_call = {0}'.format(num_call))
    else:
        print('  vtk_faces.GetNextCell(idList): num_call = {} -> [{}, {}, {}, {}]'.format(
            num_call, idList.GetId(0), idList.GetId(1), idList.GetId(2), idList.GetId(3)))
    # next, while
    while ret == 1:
        num_call = num_call + 1
        idList = vtk.vtkIdList()
        ret = vtk_faces.GetNextCell(idList)
        if ret == 0:
            print('  vtk_faces.GetNextCell(idList): num_call = {} -> Reached the end of the cell array.'.format(num_call))
            break
        else:
            print('  vtk_faces.GetNextCell(idList): num_call = {} -> [{}, {}, {}, {}]'.format(
                num_call, idList.GetId(0), idList.GetId(1), idList.GetId(2), idList.GetId(3)))

    # 3) 만들어진 vtkFloatArray 타입 변수를 출력해본다
    print('\n-------- Scalar Value (arg: vtk_scalars, type: vtkFloatArray) --------')
    for i in range(0, vtk_scalars.GetNumberOfValues()):
        print('  vtk_scalars.GetValue({}) = {}'.format(i, vtk_scalars.GetValue(i)))

    # 앞서 만든 vtkPoint, vtkCellArray, vtkFloatArray 타입 변수를 이용하여
    # 3D 모델에 해당하는 road 변수(vtkPolyData 타입)의 값들을 설정해준다
    road.SetPoints(vtk_vertices)
    road.SetPolys(vtk_faces)
    road.GetPointData().SetScalars(vtk_scalars)

    return road


if __name__ == '__main__':
    print("hello world")
    road_obj = make_road()
    file_io.write_stl_and_obj(road_obj, 'test_road')
    display.show_vtkPolyData(road_obj)
