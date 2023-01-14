"""
Example Source
https://lorensen.github.io/VTKExamples/site/Python/PolyData/TriangleCornerVertices/
"""

import vtk

def print_info_vertices(CellArrayObj):
  """ 여기 이해를 위한 코드 """
  print("Vertices.GetNumberOfCells()               : {}".format(
    CellArrayObj.GetNumberOfCells()))  #

  print("Vertices.GetMaxCellSize()                 : {}".format(
    CellArrayObj.GetMaxCellSize()))
  # size of the largest cell. The number of points defining the cell.

  print("Vertices.GetNumberOfConnectivityEntries() : {}".format(
    CellArrayObj.GetNumberOfConnectivityEntries()))
  # the total number of entries (i.e., data values) in the connectivity array



Points = vtk.vtkPoints()
Vertices = vtk.vtkCellArray()

print("\n---------- Before Call ----------")
print_info_vertices(Vertices)



print("\n---------- 1st Call ----------")
id = Points.InsertNextPoint(1.0, 0.0, 0.0) # V.InsertNextPoint(float, float, float) -> int
print('id: {} = Points.InsertNextPoint(1.0, 0.0, 0.0)'.format(id))

id_ret = Vertices.InsertNextCell(1) # V.InsertNextCell(int) -> int
Vertices.InsertCellPoint(id) # V.InsertCellPoint(int)
print('id_ret: {} = Vertices.InsertNextCell(1)'.format(id_ret))
# 두 코드는 함께 사용됨. Cell 리스트에 또 다른 Point를 추가하기 위해

print_info_vertices(Vertices)



print("\n---------- 2nd Call ----------")
id = Points.InsertNextPoint(0.0, 0.0, 0.0)
print('id: {} = Points.InsertNextPoint(0.0, 0.0, 0.0)'.format(id))

id_ret = Vertices.InsertNextCell(1)
Vertices.InsertCellPoint(id)
print('id_ret: {} = Vertices.InsertNextCell(1)'.format(id_ret))
# 두 코드는 함께 사용됨. Cell 리스트에 또 다른 Point를 추가하기 위해

print_info_vertices(Vertices)



print("\n---------- 3rd Call ----------")
id = Points.InsertNextPoint(0.0, 1.0, 0.0)
print('id: {} = Points.InsertNextPoint(0.0, 1.0, 0.0)'.format(id))

id_ret = Vertices.InsertNextCell(1)
Vertices.InsertCellPoint(id)
print('id_ret: {} = Vertices.InsertNextCell(1)'.format(id_ret))
# 두 코드는 함께 사용됨. Cell 리스트에 또 다른 Point를 추가하기 위해

print_info_vertices(Vertices)




IdList = vtk.vtkIdList() # 리턴값을 받기 위한 idList
Vertices.GetCell(0, IdList)
print('After Vertices.GetCell(0, IdList):')
for i in range(IdList.GetNumberOfIds()):
  print('  IdList.GetId({}): {}'.format(i, IdList.GetId(i)))

print('After Vertices.GetCell(1, IdList):')
Vertices.GetCell(1, IdList)
for i in range(IdList.GetNumberOfIds()):
  print('  IdList.GetId({}): {}'.format(i, IdList.GetId(i)))

print('After Vertices.GetCell(2, IdList):')
Vertices.GetCell(2, IdList)
for i in range(IdList.GetNumberOfIds()):
  print('  IdList.GetId({}): {}'.format(i, IdList.GetId(i)))


polydata = vtk.vtkPolyData()
polydata.SetPoints(Points)
polydata.SetVerts(Vertices)
polydata.Modified()
if vtk.VTK_MAJOR_VERSION <= 5:
    polydata.Update()

""" 원래 있던 예제 코드 """
# writer = vtk.vtkXMLPolyDataWriter()
# writer.SetFileName("TriangleVerts.vtp")
# if vtk.VTK_MAJOR_VERSION <= 5:
#     writer.SetInput(polydata)
# else:
#     writer.SetInputData(polydata)
# writer.Write()