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


def revert_id_list(id_list):
    # make id list first
    py_id_list_obj = []
    for i in range(id_list.GetNumberOfIds()):
        py_id_list_obj.append(id_list.GetId(i))

    # revert id list
    py_id_list_obj.reverse()

    for i in range(id_list.GetNumberOfIds()):
        id_list.SetId(i, py_id_list_obj[i])


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


def show_poly_data(polyData):
    mapper = vtk.vtkPolyDataMapper()
    if vtk.VTK_MAJOR_VERSION <= 5:
        mapper.SetInput(polyData)
    else:
        mapper.SetInputData(polyData)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    renderer = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(renderer)

    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    renderer.AddActor(actor)
    renWin.SetSize(600, 600)

    iren.Initialize()
    renWin.Render()
    iren.Start()