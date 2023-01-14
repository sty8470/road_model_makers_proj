import vtk
import vtk.util.numpy_support as vn

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

def print_id_list(id_list_obj):
    str = '['
    for i in range(id_list_obj.GetNumberOfIds()):
        str += '{}, '.format(id_list_obj.GetId(i))
    str += ']'

    str = str.replace(', ]', ']')
    print(str)

def revert_id_list(id_list):
    # make id list first
    py_id_list_obj = []
    for i in range(id_list.GetNumberOfIds()):
        py_id_list_obj.append(id_list.GetId(i))

    # revert id list
    py_id_list_obj.reverse()

    for i in range(id_list.GetNumberOfIds()):
        id_list.SetId(i, py_id_list_obj[i])

if __name__ == '__main__':


    id_list = convert_to_vtkIdList([10, 11, 12, 13, 14])
    print_id_list(id_list)

    revert_id_list(id_list)
    print_id_list(id_list)

