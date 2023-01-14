#!/usr/bin/env python

"""
Example Source
https://lorensen.github.io/VTKExamples/site/Python/IO/STLWriter/
"""

import vtk

filename = "test.stl"

sphereSource = vtk.vtkSphereSource()
sphereSource.Update()

# Write the stl file to disk
stlWriter = vtk.vtkSTLWriter()
stlWriter.SetFileName(filename)
stlWriter.SetInputConnection(sphereSource.GetOutputPort())
stlWriter.Write()

# Read and display for verification
reader = vtk.vtkSTLReader()
reader.SetFileName(filename)

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

""" 이제 내가 OBJExporter를 사용해본다 """
objExporter = vtk.vtkOBJExporter()
objExporter.SetFilePrefix('stl_2_obj_ex04')
objExporter.SetRenderWindow(renWin)
objExporter.Write()