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

colors = vtk.vtkNamedColors()

# x = array of 8 3-tuples of float representing the vertices of a cube:
x = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
     (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0)]

# pts = array of 6 4-tuples of vtkIdType (int) representing the faces
#     of the cube in terms of the above vertices
pts = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
       (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]

# We'll create the building blocks of polydata including data attributes.
cube = vtk.vtkPolyData()
points = vtk.vtkPoints()
polys = vtk.vtkCellArray()
scalars = vtk.vtkFloatArray()

# Load the point, cell, and data attributes.
print('\n-------- make points --------')
for i, xi in enumerate(x):
    print('  i = {}, xi = {}'.format(i, xi))
    points.InsertPoint(i, xi)

print('\n-------- make polys --------')
for pt in pts:
    print('  pt = {}'.format(pt))
    vil = convert_to_vtkIdList(pt)
    print('  vil = [{0}, {1}, {2}, {3}] (vtkIdList Type)'.format(vil.GetId(0), vil.GetId(1), vil.GetId(2), vil.GetId(3)))
    polys.InsertNextCell(vil)

print('\n-------- make scalars --------')
for i, _ in enumerate(x):
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



# TODO(Sglee): 위쪽이 이해되는 대로 아래쪽을 이해한다.
#
# # We now assign the pieces to the vtkPolyData.
# cube.SetPoints(points)
# cube.SetPolys(polys)
# cube.GetPointData().SetScalars(scalars)
#
# # Now we'll look at it.
# cubeMapper = vtk.vtkPolyDataMapper()
# if vtk.VTK_MAJOR_VERSION <= 5:
#     cubeMapper.SetInput(cube)
# else:
#     cubeMapper.SetInputData(cube)
# cubeMapper.SetScalarRange(cube.GetScalarRange())
# cubeActor = vtk.vtkActor()
# cubeActor.SetMapper(cubeMapper)
#
# # The usual rendering stuff.
# camera = vtk.vtkCamera()
# camera.SetPosition(1, 1, 1)
# camera.SetFocalPoint(0, 0, 0)
#
# renderer = vtk.vtkRenderer()
# renWin = vtk.vtkRenderWindow()
# renWin.AddRenderer(renderer)
#
# iren = vtk.vtkRenderWindowInteractor()
# iren.SetRenderWindow(renWin)
#
# renderer.AddActor(cubeActor)
# renderer.SetActiveCamera(camera)
# renderer.ResetCamera()
# renderer.SetBackground(colors.GetColor3d("Cornsilk"))
# # renderer.SetBackground(1.0, 0.9688, 0.8594)
#
# renWin.SetSize(600, 600)
#
# # interact with data
# renWin.Render()
# iren.Start()


