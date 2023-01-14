import vtk


def main():
    colors = vtk.vtkNamedColors()
    diskSource = vtk.vtkDiskSource()

    # Create a mapper and actor.
    # mapper = vtk.vtkPolyDataMapper()
    # mapper.SetInputConnection(diskSource.GetOutputPort())

    # 이렇게도 확인해보려고 했는데 안 됨
    # polyData = diskSource.GetOutput()
    # mapper.SetInputData(polyData)

    # actor = vtk.vtkActor()
    # actor.GetProperty().SetColor(colors.GetColor3d("Cornsilk"))
    # actor.SetMapper(mapper)

    # # Create a renderer, render window, and interactor
    # renderer = vtk.vtkRenderer()
    # renderWindow = vtk.vtkRenderWindow()
    # renderWindow.SetWindowName("Disk")
    # renderWindow.AddRenderer(renderer)
    # renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    # renderWindowInteractor.SetRenderWindow(renderWindow)

    # # Add the actors to the scene
    # renderer.AddActor(actor)
    # renderer.SetBackground(colors.GetColor3d("DarkGreen"))

    # # Render and interact
    # renderWindow.Render()
    # renderWindowInteractor.Start()


    """ 다시 작성한 부분 """
    # Draw Before OBJ Write
    # Now we'll look at it.
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(diskSource.GetOutputPort())
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
    # iren.Start() # 이걸 주석 해제하면 보여주는 창이 뜬다

    # OBJ Write
    objExporter = vtk.vtkOBJExporter()
    objExporter.SetFilePrefix('test_disk')
    objExporter.SetRenderWindow(renWin)
    objExporter.Write()


if __name__ == '__main__':
    main()