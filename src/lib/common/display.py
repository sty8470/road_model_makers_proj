import vtk


def show_vtkPolyData(poly_obj):
    """
    3D 형상을 입력하여 화면에 출력한다.
    :param poly_obj: 출력할 3D 형상 (vtkPolyData 타입)
    """
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
