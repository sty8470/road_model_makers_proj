#!/usr/bin/env python

"""
Example Source
https://lorensen.github.io/VTKExamples/site/Python/DataManipulation/Cube/
"""

"""
This is (almost) a direct C++ to Python transliteration of
 <VTK-root>/Examples/DataManipulation/Cxx/Cube.cxx from the VTK
 source distribution, which "shows how to manually create vtkPolyData"

A convenience function, convert_to_vtkIdList(), has been added and one if/else
 so the example also works in version 6 or later.
If your VTK version is 5.x then remove the line: colors = vtk.vtkNamedColors()
 and replace the set background parameters with (1.0, 0.9688, 0.8594)

"""

import vtk

def show_vtkPolyData(poly_obj):
    mapper = vtk.vtkPolyDataMapper()
    if vtk.VTK_MAJOR_VERSION <= 5:
        mapper.SetInput(poly_obj)
    else:
        mapper.SetInputData(poly_obj)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Create a rendering window and renderer
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)

    # Create a renderwindowinteractor
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    # Assign actor to the renderer
    ren.AddActor(actor)
    renWin.SetSize(600, 600)

    # Enable user interface interactor
    iren.Initialize()
    renWin.Render()
    iren.Start()

    return renWin

def show_vtkPolyData_color(poly_data_obj):
    colors = vtk.vtkNamedColors()

    # Now we'll look at it.
    cubeMapper = vtk.vtkPolyDataMapper()
    if vtk.VTK_MAJOR_VERSION <= 5:
        cubeMapper.SetInput(poly_data_obj)
    else:
        cubeMapper.SetInputData(poly_data_obj)
    cubeMapper.SetScalarRange(poly_data_obj.GetScalarRange())
    cubeActor = vtk.vtkActor()
    cubeActor.SetMapper(cubeMapper)

    # The usual rendering stuff.
    camera = vtk.vtkCamera()
    camera.SetPosition(1, 1, 1)
    camera.SetFocalPoint(0, 0, 0)

    renderer = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(renderer)

    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    renderer.AddActor(cubeActor)
    renderer.SetActiveCamera(camera)
    renderer.ResetCamera()
    renderer.SetBackground(colors.GetColor3d("Cornsilk"))
    # renderer.SetBackground(1.0, 0.9688, 0.8594)

    renWin.SetSize(600, 600)

    # interact with data
    renWin.Render()
    iren.Start()

    return renWin

def convert_to_vtkIdList(it):
    """
    Makes a vtkIdList from a Python iterable. I'm kinda surprised that
     this is necessary, since I assumed that this kind of thing would
     have been built into the wrapper and happen transparently, but it
     seems not.

    :param it: A python iterable.
    :return: A vtkIdList
    """
    vil = vtk.vtkIdList()
    for i in it:
        vil.InsertNextId(int(i))
    return vil


""" main 함수 시작 """
def make_cube():
    # x = array of 8 3-tuples of float representing the vertices of a cube:
    height = 700.0
    vertices = [(0.0, 0.0, 0.0), (100.0, 0.0, 0.0), (100.0, 100.0, 0.0), (0.0, 100.0, 0.0),
         (0.0, 0.0, height), (100.0, 0.0, height), (100.0, 100.0, height), (0.0, 100.0, height)]
    # x = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
    #      (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0)]

    # pts = array of 6 4-tuples of vtkIdType (int) representing the faces
    #     of the cube in terms of the above vertices
    # face_vertices_list = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
    #        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]

    # face_vertices_list = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    face_vertices_list = [(4, 5, 1, 0), (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3)]

    # We'll create the building blocks of polydata including data attributes.
    cube = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    polys = vtk.vtkCellArray()
    scalars = vtk.vtkFloatArray()

    # Load the point, cell, and data attributes.
    print('\n-------- make points --------')
    for i, xi in enumerate(vertices):
        print('  i = {}, xi = {}'.format(i, xi))
        points.InsertPoint(i, xi)

    print('\n-------- make polys --------')
    for pt in face_vertices_list:
        print('  pt = {}'.format(pt))
        vil = convert_to_vtkIdList(pt)
        print('  vil = [{0}, {1}, {2}, {3}] (vtkIdList Type)'.format(vil.GetId(0), vil.GetId(1), vil.GetId(2), vil.GetId(3)))
        polys.InsertNextCell(vil)

    print('\n-------- make scalars --------')
    for i, _ in enumerate(vertices):
        print('  CALL: scalars.InsertTuple1({0}, {0})'.format(i))
        scalars.InsertTuple1(i, i)

    # vtkPoint 타입의 인스턴스인 points는 꼭지점을 표현한다
    print('\n-------- Vertices (arg: points, type: vtkPoints) --------')
    for i in range(0, points.GetNumberOfPoints()):
        print('  points.GetPoint({}) = {}'.format(i, points.GetPoint(i)))

    # vtkCellArray 타입의 인스턴스인 polys는 각 면을 구성하는 꼭지점에 대한 index를 담고있다
    print('\n-------- Faces (arg: polys,  type: vtkCellArray) --------')
    # for i in range(0, polys.GetNumberOfCells()):
    #     print('  cells.GetCell({}) = {}'.format(i, polys.GetCell(i)))

    # vtkCellArray를 이렇게 받아오면 되나?
    # syntax: V.GetNextCell(vtkIdList) -> int
    # first DO
    num_call = 0
    idList = vtk.vtkIdList()
    ret = polys.GetNextCell(idList)
    if ret == 0:
        print('[ERROR] ret = polys.GetNextCell(idList) returned 0! at num_call = {0}'.format(num_call))
    else:
        print('  polys.GetNextCell(idList): num_call = {} -> [{}, {}, {}, {}]'.format(num_call, idList.GetId(0),
                                                                                      idList.GetId(1), idList.GetId(2), idList.GetId(3)))


    # next, while
    while ret == 1:
        num_call = num_call + 1
        idList = vtk.vtkIdList()
        ret = polys.GetNextCell(idList)
        if ret == 0:
            print('  polys.GetNextCell(idList): num_call = {} -> Reached the end of the cell array.'.format(num_call))
            break
        else:
            print('  polys.GetNextCell(idList): num_call = {} -> [{}, {}, {}, {}]'.format(num_call, idList.GetId(0),
                                                                                      idList.GetId(1), idList.GetId(2), idList.GetId(3)))


    # Print Scalars
    print('\n-------- Scalar Value (arg: scalars, type: vtkFloatArray) --------')
    for i in range(0, scalars.GetNumberOfValues()):
        print('  scalars.GetValue({}) = {}'.format(i, scalars.GetValue(i)))

    # We now assign the pieces to the vtkPolyData.
    cube.SetPoints(points)
    cube.SetPolys(polys)
    cube.GetPointData().SetScalars(scalars)

    return cube

def write():
    # main 루틴
    cube = make_cube()
    rendering_window = show_vtkPolyData_color(cube)

    # STL파일로 Write
    stlWriter = vtk.vtkSTLWriter()
    stlWriter.SetFileName('z_vtkPolyDataTest/vtkPolyDataTest2.vtp')
    stlWriter.SetInputDataObject(cube)
    stlWriter.Write()

    # OBJ파일로 Write
    objExporter = vtk.vtkOBJExporter()
    objExporter.SetFilePrefix('z_vtkPolyDataTest/vtkPolyDataTest2')
    objExporter.SetRenderWindow(rendering_window)
    objExporter.Write()


def write_stl_and_obj(poly_obj, output_file_prefix):
    stl_filename = output_file_prefix + '.stl'
    obj_fileprefix = output_file_prefix

    # STL Write
    stlWriter = vtk.vtkSTLWriter()
    stlWriter.SetFileName(stl_filename)
    stlWriter.SetInputDataObject(poly_obj)
    stlWriter.Write()

    # Draw Before OBJ Write
    # Now we'll look at it.
    mapper = vtk.vtkPolyDataMapper()
    if vtk.VTK_MAJOR_VERSION <= 5:
        mapper.SetInput(poly_obj)
    else:
        mapper.SetInputData(poly_obj)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

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
    iren.Start()

    # OBJ Write
    objExporter = vtk.vtkOBJExporter()
    objExporter.SetFilePrefix(obj_fileprefix)
    objExporter.SetRenderWindow(renWin)
    objExporter.Write()



def check():
    # Read and display for verification
    reader = vtk.vtkSTLReader()
    reader.SetFileName('z_vtkPolyDataTest/vtkPolyDataTest2.vtp')

    mapper = vtk.vtkPolyDataMapper()
    if vtk.VTK_MAJOR_VERSION <= 5:
        mapper.SetInput(reader.GetOutput())
    else:
        mapper.SetInputConnection(reader.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

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
    iren.Start()

def read_stl_surface_get_vtkPolyData():
    stl_filename = 'C:/Users/user/workspace/medi_projects/AneuriskWeb/C0090_models/C0090/surface/C0090_model.stl'

    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_filename)

    mapper = vtk.vtkPolyDataMapper()
    if vtk.VTK_MAJOR_VERSION <= 5:
        mapper.SetInput(reader.GetOutput())
    else:
        mapper.SetInputConnection(reader.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

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
    iren.Start()


# TODO(sglee): Deltet This
def read_polydata(vtp_filename, use_vmtk = False):
    if use_vmtk:
        from vmtk import pypes
        arg = 'vmtksurfaceviewer -ifile {}'.format(vtp_filename)
        pype_obj = pypes.PypeRun(arg)
        script_obj = pype_obj.GetScriptObject("vmtksurfaceviewer", '0')
        poly_obj = script_obj.Surface
        return poly_obj

    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(vtp_filename)
    poly_obj = reader.GetOutput()
    return poly_obj


def print_polys(poly_obj):
    poly_obj.InitTraversal()

    # syntax: V.GetNextCell(vtkIdList) -> int
    # first DO
    num_call = 0
    idList = vtk.vtkIdList()
    ret = poly_obj.GetNextCell(idList)
    print('  GetTraversalLocation: {}'.format(poly_obj.GetTraversalLocation()))
    if ret == 0:
        print('[ERROR] ret = polys.GetNextCell(idList) returned 0! at num_call = {0}'.format(num_call))
    else:
        print('  polys.GetNextCell(idList): num_call = {} -> [{}, {}, {}, {}]'.format(num_call, idList.GetId(0),
                                                                                      idList.GetId(1), idList.GetId(2), idList.GetId(3)))


    # next, while
    while ret == 1:
        num_call = num_call + 1
        idList = vtk.vtkIdList()
        ret = poly_obj.GetNextCell(idList)
        print('  GetTraversalLocation: {}'.format(poly_obj.GetTraversalLocation()))
        if ret == 0:
            print('  polys.GetNextCell(idList): num_call = {} -> Reached the end of the cell array.'.format(num_call))
            break
        else:
            print('  polys.GetNextCell(idList): num_call = {} -> [{}, {}, {}, {}]'.format(num_call, idList.GetId(0),
                                                                                      idList.GetId(1), idList.GetId(2), idList.GetId(3)))


# TODO(sglee): Refactor This. MyEx03_vtkIdList에도 정의되어 있다.
def revert_id_list(id_list):
    # make id list first
    py_id_list_obj = []
    for i in range(id_list.GetNumberOfIds()):
        py_id_list_obj.append(id_list.GetId(i))

    # revert id list
    py_id_list_obj.reverse()

    for i in range(id_list.GetNumberOfIds()):
        id_list.SetId(i, py_id_list_obj[i])


# TODO(sglee): Refactor This. MyEx03_vtkIdList에도 정의되어 있다.
def print_id_list(id_list_obj):
    str = '['
    for i in range(id_list_obj.GetNumberOfIds()):
        str += '{}, '.format(id_list_obj.GetId(i))
    str += ']'

    str = str.replace(', ]', ']')
    print(str)


def make_cell_array_with_reversed_surface(poly_obj):
    new_poly_obj = vtk.vtkCellArray()

    poly_obj.InitTraversal()
    for i in range(0, poly_obj.GetNumberOfCells()):
        # while True: # TODO(sglee): GetNumberOfCells 같은 것으로 무한 루프에 빠지지 않도록 해주자
        idList = vtk.vtkIdList()
        ret = poly_obj.GetNextCell(idList)

        # while 루프 종료 조건
        if ret != 1:
            error_msg = '[ERROR] poly_obj.GetNextCell(idList) returned {}'.format(ret)
            print(error_msg)
            raise BaseException(error_msg)

        # 현재 받아온 idList를 뒤집고, 이를 새로운 CellArray에 추가한다
        revert_id_list(idList)
        new_poly_obj.InsertNextCell(idList)

    return new_poly_obj


def revert_vtkPolyData_surface(poly_obj):
    # 원래 polys
    cell_array_obj = poly_obj.GetPolys()
    # print('\n---------- 수정 이전 Polys ----------')
    # print_polys(cell_array_obj)

    # 수정한 polys
    new_cell_array_obj = make_cell_array_with_reversed_surface(cell_array_obj)
    poly_obj.SetPolys(new_cell_array_obj)
    print('\n---------- 수정 이후 Polys ----------')
    # print_polys(cube.GetPolys())

if __name__ == '__main__':

    # write()
    # check()

    # [TEST CASE #1] 직사각형 박스로 해보기
    cube = make_cube()
    # flip_vtkPolyData_surface(cube)
    write_stl_and_obj(cube, 'test_surf')
    show_vtkPolyData(cube)

    # [TEST CASE #2] 혈관 데이터로 해보기
    # vtp_filename = 'C:/Users/user/workspace/medi_projects/AneuriskWeb/C0090_models/C0090/surface/C0090_model.vtp'
    # surf = read_polydata(vtp_filename, use_vmtk=True)
    # show_vtkPolyData(surf)
    # revert_vtkPolyData_surface(surf)
    # write_stl_and_obj(surf, vtp_filename.replace('.vtp', '_test001'))
