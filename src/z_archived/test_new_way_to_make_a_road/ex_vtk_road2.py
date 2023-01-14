"""
[실패한 예제]
사각형의 closed loop 도로인데,
내부에 건물이 존재하는 블록이 있는 도로이다.

윗면을 만드는 방법이 잘못되어 사용하지 못하는데,
옆면을 만드는 기본적인 개념은 그대로 사용할 수 있어 남겨둔다.
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import vtk
from lib.common import display, file_io, vtk_utils


def _get_upper_points():
    """
    x: 도로의 폭 방향
    y: 도로의 길이 방향
    """
    rw = 5     # 도로 하나의 폭
    bw = 20    # 블록의 폭
    bl = 90    # 블록의 길이

    w = bw + rw * 2 # 전체 바깥쪽 폭
    l = bl + rw * 2 # 전체 바깥쪽 길이


    outer = [[0, 0, 0], [w, 0, 0], [w, l, 0], [0, l, 0]]
    inner = [[rw, rw, 0], [rw + bw, rw, 0], [rw + bw, rw + bl, 0], [rw, rw + bl, 0]]
    return outer, inner


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
    face_vertices_list = [(3, 2, 1, 0), (6, 7, 4, 5)]

    # 도로 표면 & 도로 아랫면
    face_vertices_list += [(7, 6, 2, 3), (0, 1, 5, 4)]

    # 도로 옆면
    face_vertices_list += [(2, 6, 5, 1), (7, 3, 0, 4)]

    return face_vertices_list


def make_road(py_vertices, py_faces):
    """
    도로의 3D 형상에 해당하는 vtkPolyData 타입의 데이터를 만들어 반환한다.
    :return: 도로의 3D 형상에 해당하는 vtkPolyData 타입 데이터
    """

    # 도로의 3D 형상을 정의하기 위한 점과 면의 리스트를 생성한다.
    #py_vertices = _make_vertices()
    #py_faces = _make_faces()

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


def _make_face(len_outer, len_total, offset, normal_outside):
    # 이제 index를 만든다
    outer_upper_idx = [0 for i in range(len_outer + 1)]
    outer_lower_idx =  [0 for i in range(len_outer + 1)]
    
    for i in range(0, len_outer):
        outer_upper_idx[i] = offset + i
        outer_lower_idx[i] = offset + i + len_total
    
    outer_upper_idx[-1] = outer_upper_idx[0]
    outer_lower_idx[-1] = outer_lower_idx[0]

    # 이제 면의 index를 만든다
    face_outer_idx = [ [0,0,0] for _ in range(len_outer) ]
    for i in range(0, len_outer):
        if normal_outside:
            face_outer_idx[i] = [outer_upper_idx[i + 1], outer_upper_idx[i], outer_lower_idx[i], outer_lower_idx[i+1]]
        else:
            face_outer_idx[i] = [outer_upper_idx[i], outer_upper_idx[i + 1], outer_lower_idx[i+1], outer_lower_idx[i],]

    return face_outer_idx, outer_upper_idx, outer_lower_idx
    

if __name__ == '__main__':
    outer_upper, inner_upper = _get_upper_points()  

    len_outer = len(outer_upper)
    len_inner = len(inner_upper)
    len_total = len_outer + len_inner

    # thickness index = 2
    import copy
    outer_below = copy.deepcopy(outer_upper)
    inner_below = copy.deepcopy(inner_upper)

    thickness = 1
    for i in range(0, len(outer_upper)):
        outer_below[i][2] = outer_upper[i][2] - thickness

    for i in range(0, len(inner_upper)):
        inner_below[i][2] = inner_upper[i][2] - thickness

    print('total len: ', len_total)


    print("---------- outer(upper) ----------")
    print(outer_upper)

    print("---------- outer(lower) ----------")
    print(outer_below)

    print("---------- inner(upper) ----------")
    print(inner_upper)

    print("---------- inner(lower) ----------")
    print(inner_below)


    # 표면을 만든다 (upper_idx, lower_idx를 각각 받는 것은 디버깅용 데이터이다.)
    face_outer_idx, outer_upper_idx, outer_lower_idx = _make_face(len_outer, len_total, 0, True)
    face_inner_idx, inner_upper_idx, inner_lower_idx = _make_face(len_inner, len_total, len_outer, False)
    
    print("---------- outer_upper_idx ----------")
    print(outer_upper_idx)

    print("---------- outer_lower_idx ----------")
    print(outer_lower_idx)

    print("---------- face_outer_idx ----------")
    print(face_outer_idx)

    print("---------- inner_upper_idx ----------")
    print(inner_upper_idx)

    print("---------- inner_lower_idx ----------")
    print(inner_lower_idx)

    print("---------- face_inner_idx ----------")
    print(face_inner_idx)


    # 점을 모두 합한 인덱스를 보여준다
    py_vertices = outer_upper + inner_upper + outer_below + inner_below
    print("---------- py_vertices ----------")
    print(py_vertices)

    # 옆면을 전부 합한 인덱스를 보여준다
    py_faces = face_outer_idx + face_inner_idx
    print("---------- py_faces ----------")
    print(py_faces)

    road_obj = make_road(py_vertices, py_faces)
    file_io.write_stl_and_obj(road_obj, 'test_road')
    display.show_vtkPolyData(road_obj)

