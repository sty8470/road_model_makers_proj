import vtk

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


def print_polys(poly_obj):
    poly_obj.InitTraversal()

    # syntax: V.GetNextCell(vtkIdList) -> int
    # first DO
    num_call = 0
    idList = vtk.vtkIdList()
    ret = poly_obj.GetNextCell(idList)
    # print('  GetTraversalLocation: {}'.format(poly_obj.GetTraversalLocation()))
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
        # print('  GetTraversalLocation: {}'.format(poly_obj.GetTraversalLocation()))
        if ret == 0:
            print('  polys.GetNextCell(idList): num_call = {} -> Reached the end of the cell array.'.format(num_call))
            break
        else:
            print('  polys.GetNextCell(idList): num_call = {} -> [{}, {}, {}, {}]'.format(num_call, idList.GetId(0),
                                                                                      idList.GetId(1), idList.GetId(2), idList.GetId(3)))


def result_expt(polys1):
    cube = vtk.vtkPolyData()
    cube.SetPolys(polys1)
    poly_obj = cube.GetPolys()
    print('-------- First  Poly ----------')
    print_polys(poly_obj)

    polys2 = vtk.vtkCellArray()
    polys2.InsertNextCell(convert_to_vtkIdList([0, 1, 4, 5])) # Cell에 입력할 때는 convert_to_vtkIdList 함수를 호출해서 만든다
    polys2.InsertNextCell(convert_to_vtkIdList([1, 2, 5, 6]))
    polys2.InsertNextCell(convert_to_vtkIdList([2, 3, 6, 7]))
    polys2.InsertNextCell(convert_to_vtkIdList([3, 0, 4, 7]))
    # print_polys(polys2)

    cube.SetPolys(polys2)
    poly_obj = cube.GetPolys()
    print('-------- Second Poly ----------')
    print_polys(poly_obj)


def result_actl(polys1):
    cube = vtk.vtkPolyData()
    cube.SetPolys(polys1)
    poly_obj = cube.GetPolys()
    print('-------- First  Poly ----------')
    print_polys(poly_obj)

    polys2 = make_cell_array_with_reversed_surface(polys1)
    print('-------- Second Poly ----------')
    print_polys(polys2)


if __name__ == '__main__':

    face_vertices_list = [(4, 5, 1, 0), (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3)]
    polys1 = vtk.vtkCellArray()
    # print('\n-------- make polys --------')
    for pt in face_vertices_list:
        # print('  pt  = {}'.format(pt))
        vil = convert_to_vtkIdList(pt)
        # print('  vil = [{0}, {1}, {2}, {3}] (vtkIdList Type)'.format(vil.GetId(0), vil.GetId(1), vil.GetId(2), vil.GetId(3)))
        # print('  calling polys.InsertNextCell(vil)')
        polys1.InsertNextCell(vil)

    print('\n\n--------- calling: print_polys(polys1) ----------')
    print_polys(polys1)

    print('\n\n--------- calling: result_actl(polys1) ---------- ')
    result_actl(polys1)