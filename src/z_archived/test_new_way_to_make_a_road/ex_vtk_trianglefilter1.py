"""
사각형의 closed loop 도로인데,
내부에 건물이 존재하는 블록이 있는 도로이다.

입력값은 다음과 같다.
1) 가장 바깥 차선을 결정하는 선
2) 안쪽에 구멍으로 존재해야하는 선 (복수가 될 수 있다. 여기 예제에서는 1개)

방식은 다음과 같이 만들게 된다.
1) 우선 가장 바깥 차선을 결정하는 선을 이용하여, 바깥쪽만을 표현하는 큰 도로를 만든다
2) 그 다음, 안쪽 건물이 위치해야하는 공간을 표현하는 지역을 만든다.
3) 1)에서 만든 것 - 2)에서 만든 것 = 최종 도로 형태
이렇게 만들어낸다.
"""
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import vtk
import copy
from lib.common import display, file_io, vtk_utils
from ex_sampling_nd import _insert_to_every_point


def _get_user_input(add_inner_points=True):
    """
    x: 도로의 폭 방향
    y: 도로의 길이 방향
    """
    rw = 10     # 도로 하나의 폭
    bw = 10    # 블록의 폭
    bl = 15    # 블록의 길이

    w = bw + rw * 2 # 전체 바깥쪽 폭
    l = bl + rw * 2 # 전체 바깥쪽 길이


    outer = [[0, 0, 0], [w, 0, 0], [w, l, 0], [0, l, 0]]
    inner = [[rw, rw, 0], [rw + bw, rw, 0], [rw + bw, rw + bl, 0], [rw, rw + bl, 0]]
    # inner = [[rw, rw, 0], [(rw + rw + bw)/2, rw, 0], 
    #     [rw + bw, rw, 0], [rw + bw, (rw + rw + bl)/2, 0],
    #     [rw + bw, rw + bl, 0], [(rw + rw + bw)/2, rw + bl, 0],
    #     [rw, rw + bl, 0], [rw, (rw + rw + bl)/2, 0]]
    
    if add_inner_points:
        outer.append(outer[0])
        inner.append(inner[0])

        outer = _insert_to_every_point(outer, 10)
        inner = _insert_to_every_point(inner, 5)
        print('\n-----------------')
        print('outer: ', outer)
        print('')

        print('-----------------')
        print('inner: ', inner)
        print('-----------------')

        print('')
        return outer[0:-1], inner[0:-1]
    else:
        return outer, inner


def make_road(py_vertices, py_faces, debug_print=False):
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
    if debug_print:
        print('\n-------- make vtk_vertices --------')
    for i, xi in enumerate(py_vertices):
        #print('  i = {}, xi = {}'.format(i, xi))
        vtk_vertices.InsertPoint(i, xi)

    # 2) vtkCellArray 타입의 변수를 만든다.
    if debug_print:
        print('\n-------- make vtk_faces --------')
    for pt in py_faces:
        #print('  pt = {}'.format(pt))

        # tuple을 바로 넣을 수 없고, vtkIdList 타입을 만들어서 이를 전달해야
        # vtkCellArray 타입의 객체를 초기화할 수 있다
        vil = vtk_utils.convert_to_vtkIdList(pt)
        #print('  vil = [{0}, {1}, {2}, {3}] (vtkIdList Type)'.format(vil.GetId(0), vil.GetId(1), vil.GetId(2), vil.GetId(3)))

        vtk_faces.InsertNextCell(vil)

    # 3) vtkFloatArray 타입의 변수를 만든다.
    if debug_print:
        print('\n-------- make vtk_scalars --------')
    for i, _ in enumerate(py_vertices):
        if debug_print:
            print('  CALL: vtk_scalars.InsertTuple1({0}, {0})'.format(i))
        vtk_scalars.InsertTuple1(i, i)

    # 1) 만들어진 vtkPoint 타입 변수를 출력해본다.
    if debug_print:
        print('\n-------- Vertices (arg: vtk_vertices, type: vtkPoints) --------')
        for i in range(0, vtk_vertices.GetNumberOfPoints()):
            print('  vtk_vertices.GetPoint({}) = {}'.format(i, vtk_vertices.GetPoint(i)))

    # 2) 만들어진 vtkCellArray 타입 변수를 출력해본다.
    # vtkCellArray 타입의 인스턴스인 polys는 각 면을 구성하는 꼭지점에 대한 index를 담고있다.
    if debug_print:
        print('\n-------- Faces (arg: vtk_faces,  type: vtkCellArray) --------')
        # for i in range(0, vtk_faces.GetNumberOfCells()):
        #     print('  cells.GetCell({}) = {}'.format(i, vtk_faces.GetCell(i)))

    # vtkCellArray를 이렇게 받아오면 되나?
    # syntax: V.GetNextCell(vtkIdList) -> int
    # first DO
    num_call = 0
    idList = vtk.vtkIdList()
    ret = vtk_faces.GetNextCell(idList)
    if debug_print:
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
        if debug_print:
            if ret == 0:
                print('  vtk_faces.GetNextCell(idList): num_call = {} -> Reached the end of the cell array.'.format(num_call))
                break
            else:
                print('  vtk_faces.GetNextCell(idList): num_call = {} -> [{}, {}, {}, {}]'.format(
                    num_call, idList.GetId(0), idList.GetId(1), idList.GetId(2), idList.GetId(3)))

    # 3) 만들어진 vtkFloatArray 타입 변수를 출력해본다
    if debug_print:
        print('\n-------- Scalar Value (arg: vtk_scalars, type: vtkFloatArray) --------')
        for i in range(0, vtk_scalars.GetNumberOfValues()):
            print('  vtk_scalars.GetValue({}) = {}'.format(i, vtk_scalars.GetValue(i)))

    # 앞서 만든 vtkPoint, vtkCellArray, vtkFloatArray 타입 변수를 이용하여
    # 3D 모델에 해당하는 road 변수(vtkPolyData 타입)의 값들을 설정해준다
    road.SetPoints(vtk_vertices)
    road.SetPolys(vtk_faces)
    road.GetPointData().SetScalars(vtk_scalars)

    return road


def _make_vertices(upper_vertices_ccw, thickness, raise_upper):
    lower_verticies_ccw = copy.deepcopy(upper_vertices_ccw)
    new_upper_vertices_ccw = copy.deepcopy(upper_vertices_ccw)

    for i in range(0, len(upper_vertices_ccw)):
        lower_verticies_ccw[i][2] = upper_vertices_ccw[i][2] - thickness
        new_upper_vertices_ccw[i][2] = upper_vertices_ccw[i][2] + thickness
        
    if not raise_upper: # 일반 도로용
        vertices = upper_vertices_ccw + lower_verticies_ccw
    else: # 일반 도로에 구멍을 뚫기 위한 object (건물이 있는 지역)       
        vertices = new_upper_vertices_ccw + lower_verticies_ccw

    
    return vertices

def _make_face(len_outer, normal_outside):
    # 이제 index를 만든다
    outer_upper_idx = [0 for i in range(len_outer + 1)]
    outer_lower_idx =  [0 for i in range(len_outer + 1)]

    for i in range(0, len_outer):
        outer_upper_idx[i] = i
        outer_lower_idx[i] = i + len_outer

    outer_upper_idx[-1] = outer_upper_idx[0]
    outer_lower_idx[-1] = outer_lower_idx[0]

    print('[DEBUG]: outer_upper_idx: ', outer_upper_idx)
    print('[DEBUG]: outer_upper_idx: ', outer_lower_idx)

    # 이제 옆면의 index를 만든다
    face_outer_idx = [ [0,0,0] for _ in range(len_outer) ]
    for i in range(0, len_outer):
        if normal_outside:
            face_outer_idx[i] = [outer_upper_idx[i + 1], outer_upper_idx[i], outer_lower_idx[i], outer_lower_idx[i+1]]
        else:
            face_outer_idx[i] = [outer_upper_idx[i], outer_upper_idx[i + 1], outer_lower_idx[i+1], outer_lower_idx[i],]

    # 위아래 면의 index를 만든다
    outer_lower_idx_reverse = [2 * len_outer - i - 1 for i in range(len_outer)]
    face_outer_idx += [outer_upper_idx[0:-1], outer_lower_idx_reverse]

    print('[DEBUG]: face_outer_idx: ', face_outer_idx)

    return face_outer_idx
    

def _plot_vtkPolyData(poly_obj, color=''):
    colors = vtk.vtkNamedColors()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly_obj)
    mapper.ScalarVisibilityOff()


    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
        
    if color != '':
        actor.GetProperty().SetColor(colors.GetColor3d(color))

    # Create a rendering window and renderer
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)

    # Create a renderwindowinteractor
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    # Assign actor to the renderer
    ren.AddActor(actor)

    # Enable user interface interactor
    iren.Initialize()
    renWin.Render()
    iren.Start() # 이걸 주석 해제하면 보여주는 창이 뜬다


if __name__ == '__main__':
    

    outer_upper, inner_upper = _get_user_input(add_inner_points=False)  


    # [STEP1] Outer Line으로 도로에 해당하는 vtkPolyData 타입의 객체를 만든다.
    thickness = 1
    outer_vertices = _make_vertices(outer_upper, thickness, raise_upper=False) # 꼭지점의 리스트 생성
    outer_faces = _make_face(len(outer_upper), normal_outside=True) # 면을 정의하는 리스트 생성 
    polyData_outer_upper = make_road(outer_vertices, outer_faces)


    # [STEP2] Inner Line으로 구멍이 뚫려야하는 공간 (예를 들면 건물 부지)
    # 에 vtkPolyData 타입의 객체를 만든다.
    # (이 때 thickness를 훨씬 크게 해야한다.)
    thickness = 15
    inner_vertices = _make_vertices(inner_upper, thickness, raise_upper=True) # 꼭지점의 리스트 생성
    inner_faces = _make_face(len(inner_upper), normal_outside=True) # 면을 정의하는 리스트 생성 
    polyData_inner_upper = make_road(inner_vertices, inner_faces)


    # [DEBUG] Visualize 해서 확인
    # _plot_vtkPolyData(polyData_outer_upper, 'Red')
    # _plot_vtkPolyData(polyData_inner_upper, 'Yellow')#

    # [STEP3] Data Pre-processing
    # outerTriAngleModel = vtk.vtkTriangleFilter()
    # outerTriAngleModel.SetInputData(polyData_outer_upper)
    # innerTriAngleModel = vtk.vtkTriangleFilter()
    # innerTriAngleModel.SetInputData(polyData_inner_upper)


    # [STEP4] Boolean Operation 수행 (A - B)
    # booleanOperation = vtk.vtkBooleanOperationPolyDataFilter()
    # booleanOperation.SetOperationToDifference()
    # booleanOperation.SetInputConnection(0, outerTriAngleModel.GetOutputPort())
    # booleanOperation.SetInputConnection(1, innerTriAngleModel.GetOutputPort())
    # booleanOperation.Update()


   # [STEP5] 출력
    colors = vtk.vtkNamedColors() # 그리기 위해 필요한 것

    # 그리기 위해 vtkPolyDataMapper 객체와 vtkActor 객체를 만든다
    input1Mapper = vtk.vtkPolyDataMapper()
    
    input1Mapper.SetInputData(polyData_outer_upper)
    # input1Mapper.SetInputConnection(outerTriAngleModel.GetOutputPort())

    input1Mapper.ScalarVisibilityOff()
    input1Actor = vtk.vtkActor()
    input1Actor.SetMapper(input1Mapper)
    input1Actor.GetProperty().SetColor(colors.GetColor3d("Tomato"))
    # input1Actor.SetPosition(large_obj.GetBounds()[1] - large_obj.GetBounds()[0], 0, 0)

    # input2Mapper = vtk.vtkPolyDataMapper()
    # input2Mapper.SetInputData(polyData_inner_upper)
    # input2Mapper.ScalarVisibilityOff()
    # input2Actor = vtk.vtkActor()
    # input2Actor.SetMapper(input2Mapper)
    # input2Actor.GetProperty().SetColor(colors.GetColor3d("Mint"))
    # # input2Actor.SetPosition(-(small_obj.GetBounds()[1] - small_obj.GetBounds()[0]), 0, 0)
    
    # booleanOperationMapper = vtk.vtkPolyDataMapper()
    # booleanOperationMapper.SetInputConnection(booleanOperation.GetOutputPort())
    # booleanOperationMapper.ScalarVisibilityOff()
    # booleanOperationActor = vtk.vtkActor()
    # booleanOperationActor.SetMapper(booleanOperationMapper)
    # booleanOperationActor.GetProperty().SetDiffuseColor(colors.GetColor3d("Banana"))

    # Renderer를 만들고 Actor를 추가
    renderer = vtk.vtkRenderer()
    renderer.AddViewProp(input1Actor)
    #renderer.AddViewProp(input2Actor)
    # renderer.AddViewProp(booleanOperationActor)


    # 렌더링 시작
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renWinInteractor = vtk.vtkRenderWindowInteractor()
    renWinInteractor.SetRenderWindow(renderWindow)
    renderWindow.Render()
    renWinInteractor.Start()

    # 파일로 출력
    objExporter = vtk.vtkOBJExporter()
    objExporter.SetFilePrefix('outerbox_fill_x_triangle_filter_x')
    objExporter.SetRenderWindow(renderWindow)
    objExporter.Write()