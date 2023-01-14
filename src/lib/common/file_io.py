import vtk


def read_polydata(vtp_filename, use_vmtk=False):
    if use_vmtk:
        from vmtk import pypes
        arg = 'vmtksurfaceviewer -ifile {}'.format(vtp_filename)
        pype_obj = pypes.PypeRun(arg)
        script_obj = pype_obj.GetScriptObject("vmtksurfaceviewer", '0')
        poly_obj = script_obj.Surface
        return poly_obj

    else:
        # TODO(sglee) : 이 부분 구현할 것. 현재 코드로 안 됨
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(vtp_filename)
        reader.Update()
        poly_obj = reader.GetOutput()
        return poly_obj


def write_stl_and_obj(poly_obj, output_file_prefix):
    """
    3D 형상을 입력하여 stl 파일과 obj 파일을 만든다.
    :param poly_obj: 출력할 3D 형상 (vtkPolyData 타입)
    :param output_file_prefix: 출력할 파일 이름 (단, 확장자는 붙이면 안 된다)
    """
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
    # iren.Start() # 이걸 주석 해제하면 보여주는 창이 뜬다

    # OBJ Write
    objExporter = vtk.vtkOBJExporter()
    objExporter.SetFilePrefix(obj_fileprefix)
    objExporter.SetRenderWindow(renWin)
    objExporter.Write()


def write_obj(poly_obj, output_file_prefix):
    """
    3D 형상을 입력하여 obj 파일을 만든다.
    :param poly_obj: 출력할 3D 형상 (vtkPolyData 타입)
    :param output_file_prefix: 출력할 파일 이름 (단, 확장자는 붙이면 안 된다)
    """
    obj_file_prefix = output_file_prefix

    # Draw Before OBJ Write
    # Now we'll look at it.
    mapper = vtk.vtkPolyDataMapper()
    if vtk.VTK_MAJOR_VERSION <= 5:
        mapper.SetInput(poly_obj)
    else:
        # NOTE: 임시 시험용으로 SetInputConnection으로 대체
        mapper.SetInputData(poly_obj)
        # mapper.SetInputConnection(poly_obj.GetOutputPort())
    actor = vtk.vtkActor()
    actor.GetProperty().SetRepresentationToWireframe()
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
    iren.Start() # 이걸 주석 해제하면 보여주는 창이 뜬다

    # OBJ Write
    objExporter = vtk.vtkOBJExporter()
    objExporter.SetFilePrefix(obj_file_prefix)
    objExporter.SetRenderWindow(renWin)
    objExporter.Write()