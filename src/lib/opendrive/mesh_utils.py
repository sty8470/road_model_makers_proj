from enum import Enum
from PyQt5.QtCore import left
import vtk
import numpy as np
import scipy.spatial as sp
from lib.common import vtk_utils
from lib.mgeo.mesh_gen.generate_mesh import smooth_mesh

#x-y 평면에서 각도 구하기
def calc_line_vector_rad(line) :
    x2 = line[1][0]
    y2 = line[1][1]

    x1 = line[0][0]
    y1 = line[0][1]
    rad = np.arctan2(y2 - y1, x2 - x1)
    return rad

#-pi ~ pi 범위로 각도 변환
def adapt_range(rad) :
    if rad > np.pi :
        rad = rad - 2*np.pi
    elif rad < -np.pi :
        rad = rad + 2*np.pi
    return rad

#0 ~ 2pi 범위로 각도 변환
def adapt_range2(rad) :
    if rad > 2*np.pi :
        rad = rad - 2*np.pi
    elif rad < 0 :
        rad = rad + 2*np.pi
    return rad

#꼬인 부분 제거
def clean_vertices(vertices, z_tolerance) :
    new_vertices = list()
    if len(vertices) < 4 :
        return vertices
    new_vertices.append(vertices[0])
    chk_idx = 0
    current_pnt = vertices[0]
    for i in range(len(vertices) - 2) :
        if chk_idx > i :
            continue
        line1 = [current_pnt, vertices[i + 1]]
        intersect_pnt = []
        for j in range(i+2, len(vertices) - 1) :
            line2 = [vertices[j], vertices[j + 1]]
            intersect_pnt = get_intersect_point(line1, line2, z_tolerance)
            if len(intersect_pnt) == 3 :
                chk_idx = j
                break

        if len(intersect_pnt) == 3 :
            new_vertices.append(intersect_pnt)
            current_pnt = intersect_pnt
            #new_vertices.append(line2[1])
        else :
            new_vertices.append(line1[1])
            current_pnt = vertices[1]
            
    new_vertices.append(vertices[-1])

    return new_vertices

#꼬인 부분 제거
def clean_vertices2(left_vertices, right_vertices) :
    new_left_vertices = list()
    new_right_vertices = list()

    if len(left_vertices) == len(right_vertices) :
        #최대 5회 수행
        for i in range(5) :
            new_left_vertices = list()
            new_right_vertices = list()
            new_left_vertices.append(left_vertices[0])
            new_right_vertices.append(right_vertices[0])
            check_count = 0

            for i in range(1, len(left_vertices)-1) :
                rad_left1 = calc_line_vector_rad([new_left_vertices[-1], left_vertices[i]])
                rad_left2 = calc_line_vector_rad([left_vertices[i], left_vertices[i+1]])

                rad_right1 = calc_line_vector_rad([new_right_vertices[-1], right_vertices[i]])
                rad_right2 = calc_line_vector_rad([right_vertices[i], right_vertices[i+1]])

                if np.abs(adapt_range(rad_left2 - rad_left1)) > np.pi/3 or np.abs(adapt_range(rad_right2 - rad_right1)) > np.pi/3 :
                    

                    check_count += 1
                else :
                    new_left_vertices.append(left_vertices[i])
                    new_right_vertices.append(right_vertices[i])

            new_left_vertices.append(left_vertices[-1])
            new_right_vertices.append(right_vertices[-1])
            left_vertices = new_left_vertices
            right_vertices = new_right_vertices
            if check_count == 0 :
                break

    return left_vertices, right_vertices

#꼬인 부분 제거
def clean_vertices3(vertices) :
    new_vertices = list()
    if len(vertices) > 0 :
        #최대 5회 수행
        for i in range(5) :
            new_vertices = list()
            new_vertices.append(vertices[0])
            check_count = 0

            for i in range(1, len(vertices)-1) :
                rad_1 = calc_line_vector_rad([new_vertices[-1], vertices[i]])
                rad_2 = calc_line_vector_rad([vertices[i], vertices[i+1]])

                if np.abs(adapt_range(rad_2 - rad_1)) > np.pi/2 :

                    check_count += 1
                else :
                    new_vertices.append(vertices[i])
            new_vertices.append(vertices[-1])
            vertices = new_vertices
            if check_count == 0 :
                break

    return new_vertices

#x 가 가장 작은 포인트를 찾는다. 같은 포인트가 여럿이면 y 가 가장 작은 포인트를 찾는다
def find_min_point(point_list) :
    min_cnt = 0
    min_point_idx = None
    for i in range(len(point_list)) :
        point = point_list[i]
        point_x = point[0]
        point_y = point[1]

        if min_point_idx == None :
            min_point_idx = i
        else:
            cmp_x = point_list[min_point_idx][0]
            cmp_y = point_list[min_point_idx][1]

            if cmp_x > point_x :
                min_cnt = 1
                min_point_idx = i
            elif cmp_x == point_x :
                if cmp_y > point_y :
                    min_cnt = 1
                    min_point_idx = i
                elif cmp_y == point_y :
                    min_cnt += 1
                    min_point_idx = i
    if min_cnt != 1 :
        return None
    else:
        return min_point_idx

def point_to_line_distance(line, pnt) :
    x0 = pnt[0]
    y0 = pnt[1]

    x1 = line[0][0]
    y1 = line[0][1]

    x2 = line[1][0]
    y2 = line[1][1]

    if x1 == x2 and y1 == y2 :
        return line2_magnitute([pnt, line[0]])

    A = np.abs((x2-x1) * (y1-y0) - (x1-x0) * (y2-y1))
    B = np.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))

    dis = A/B

    a = (y2-y1)
    b = (x1-x2)
    c = -(a*x1 + b*y1)

    pnt_x = (b*(b*x0-a*y0) - a*c) / (a*a + b*b)
    pnt_y = (a*(-b*x0 + a*y0) - b*c) / (a*a + b*b)

    cond1 = pnt_x < max(x1, x2) and pnt_x > min(x1, x2) and pnt_y < max(y1, y2) and pnt_y > min(y1, y2)
    cond2 = pnt_x == x1 and pnt_x == x2 and pnt_y < max(y1, y2) and pnt_y > min(y1, y2)
    cond3 = pnt_x < max(x1, x2) and pnt_x > min(x1, x2) and pnt_y == y1 and pnt_y == y2
    if cond1 or cond2 or cond3 : 
        return dis
        
    else :
        mag1 = line2_magnitute([pnt, line[0]])
        mag2 = line2_magnitute([pnt, line[1]])

        return min(mag1, mag2)

def shrink_polygon(vtkpoly) :
    point_list = list()
    num_of_points = vtkpoly.GetNumberOfPoints()
    for i in range(num_of_points) :
        point_list.append(vtkpoly.GetPoint(i))
    vtkpoly = vtkPolyByPoints(point_list)

    shrink = vtk.vtkShrinkPolyData()
    shrink.SetInputData(vtkpoly)
    shrink.SetShrinkFactor(0.9)
    shrink.Update()
    vtkpoly = shrink.GetOutput()

    return vtkpoly

#폴리곤에서 해당 포인트가 reflex vertex 인지 판별. point_list 는 반시계방향으로 정렬되어있어야 함
def is_reflex_vertex(point_list, point_idx) :
    prev_point = point_list[point_idx - 1]
    current_point = point_list[point_idx]
    next_point = point_list[point_idx + 1] if point_idx < len(point_list) - 1 else point_list[0]

    rad_prev_line = calc_line_vector_rad([current_point, prev_point])
    rad_next_line = calc_line_vector_rad([next_point, current_point])

    if adapt_range2(rad_next_line - rad_prev_line) < np.pi :
        return True
    return False

def vtkFillHoles(vtk_poly) :
    fill_holes = vtk.vtkFillHolesFilter()
    fill_holes.SetInputData(vtk_poly)
    fill_holes.SetHoleSize(50)
    fill_holes.Update()
    return fill_holes.GetOutput()

#vertex, face 로 vtkPolyData 생성
def vtkPoly(vertices, faces, uv=None):
    vtk_poly = vtk.vtkPolyData()
    vtk_vertices = vtk.vtkPoints()
    vtk_faces = vtk.vtkCellArray()
    for vertex in vertices:
        vtk_vertices.InsertNextPoint(vertex)

    for face in faces:
        vil = vtk_utils.convert_to_vtkIdList(face)
        vtk_faces.InsertNextCell(vil)

    vtk_poly.SetPoints(vtk_vertices)
    vtk_poly.SetPolys(vtk_faces)

    if uv is not None and len(uv) > 0 :
        vtk_uvcoords =vtk.vtkFloatArray()
        vtk_uvcoords.SetNumberOfComponents(2)
        vtk_uvcoords.SetNumberOfTuples(len(uv))
        for i in range(len(uv)):
            vtk_uv = uv[i]
            vtk_uvcoords.SetTuple2(i, vtk_uv[0], vtk_uv[1])
        vtk_poly.GetPointData().SetTCoords(vtk_uvcoords)
    return vtk_poly

def vtkPolyByPoints(vertices):
    face = list()
    for point_idx in range(len(vertices)) :
        face.append(point_idx)
    faces = list()
    faces.append(face)
    vtk_poly = vtkPoly(vertices, faces)
    return vtk_poly

#vtkPolyData 에서 Boundary 추출
def vtkBoundary(vtk_poly) :
    featureEdges = vtk.vtkFeatureEdges()
    featureEdges.SetInputData(vtk_poly)
    featureEdges.BoundaryEdgesOn()
    featureEdges.FeatureEdgesOff()
    featureEdges.ManifoldEdgesOff()
    featureEdges.NonManifoldEdgesOff()
    featureEdges.Update()
    return featureEdges.GetOutput()

#vtkPolyData를 z 출 따라 이동
def vtkMove(vtkPoly, z_abs) :
    transform = vtk.vtkTransform()
    transform.Translate(0.0, 0.0, z_abs)

    trans_filter = vtk.vtkTransformPolyDataFilter()
    trans_filter.SetTransform(transform)
    trans_filter.SetInputData(vtkPoly)
    trans_filter.Update()
    return trans_filter.GetOutput()

#2차원 vtkPolyData를 3차원으로
#Normal 방향이 얼추 z 축 방향인 평면 polygon 이라고 가정하고(i.e. 도로) z 축으로 이동 후 반대 방향으로 Extrude 해서 3차원 폴리곤으로 만드는 함수
def vtkMake3D(vtk_poly, ext_size) :
    ext = vtkMove(vtk_poly, ext_size)
    ext = vtkExtrude(ext, -2*ext_size)
    return ext

#다른 두 폴리곤 간의 겹침 처리
def vtkClip(vtkPoly, clipPoly, tolerance=0.0) :
    distance = vtk.vtkImplicitPolyDataDistance()
    distance.SetInput(clipPoly)

    clip = vtk.vtkClipPolyData()
    clip.SetInputData(vtkPoly)
    clip.SetClipFunction(distance)
    clip.SetValue(tolerance)
    clip.InsideOutOn()
    clip.GenerateClippedOutputOn()
    clip.Update()

    clipped = clip.GetOutput(1)
    clip_poly = clip.GetOutput(0)

    return clip_poly, clipped

#Extrusion
def vtkExtrude(vtk_poly, vector_z):
    extr = vtk.vtkLinearExtrusionFilter()
    extr.SetExtrusionTypeToVectorExtrusion()
    extr.CappingOn()
    extr.SetVector(0.0, 0.0, vector_z)
    extr.SetInputData(vtk_poly)
    extr.Update()
    return extr.GetOutput()

#서로 다른 두 폴리곤 병합
def vtkAppend(vtk_poly1, vtk_poly2):
    append = vtk.vtkAppendPolyData()
    append.AddInputData(vtk_poly1)
    append.AddInputData(vtk_poly2)
    append.Update()
    return append.GetOutput()

#Clean Poly : 중복 포인트 병합, 안쓰는 포인트 제거 등
def vtkCleanPoly(vtk_poly, tolerance=None):
    cleanPoly = vtk.vtkCleanPolyData()
    cleanPoly.SetInputData(vtk_poly)
    cleanPoly.PointMergingOn()
    if not tolerance == None:
        cleanPoly.SetTolerance(tolerance)
    cleanPoly.Update()
    return cleanPoly.GetOutput()

#삼각형 폴리곤으로 만들기
def vtkTrianglePoly(vtk_poly):
    triPoly = vtk.vtkTriangleFilter()
    triPoly.SetInputData(vtk_poly)
    triPoly.Update()
    return triPoly.GetOutput()

def vtkTransform(vtk_poly, vtk_matrix) :
    transform = vtk.vtkTransform()
    transform.SetMatrix(vtk_matrix)

    transFilter = vtk.vtkTransformPolyDataFilter()
    transFilter.SetTransform(transform)
    transFilter.SetInputData(vtk_poly)
    transFilter.Update()

    return transFilter.GetOutput()

#flip y : y = -y
#       1   0   0   0
#       0   -1  0   0
#       0   0   1   0
#       0   0   0   1
def vtkFlip_y(vtk_poly) :
    matrix = vtk.vtkMatrix4x4()
    matrix.Zero()               #fill zero
    matrix.SetElement(0, 0, 1)
    matrix.SetElement(1, 1, -1)
    matrix.SetElement(2, 2, 1)
    matrix.SetElement(3, 3, 1)

    return vtkTransform(vtk_poly, matrix)

#swap y-z : y-z 축 변경
#       1   0   0   0
#       0   0   1   0
#       0   1   0   0
#       0   0   0   1
def vtkSwap_yz(vtk_poly) :
    matrix = vtk.vtkMatrix4x4()
    matrix.Zero()               #fill zero
    matrix.SetElement(0, 0, 1)
    matrix.SetElement(1, 2, 1)
    matrix.SetElement(2, 1, 1)
    matrix.SetElement(3, 3, 1)

    return vtkTransform(vtk_poly, matrix)

def vtkDelaunay2DTriangulation(boundary, inside_points) :
    vtk.vtkObject.GlobalWarningDisplayOff()
    vtk_poly = vtk.vtkPolyData()
    vtk_vertices = vtk.vtkPoints()
    vtk_boundary_loop = vtk.vtkPolygon()
    vtk_boundary = vtk.vtkPolyData()
    vtk_cell = vtk.vtkCellArray()

    for boundary_point in boundary:
        vtk_vertices.InsertNextPoint(boundary_point)

    for inside in inside_points:
        vtk_vertices.InsertNextPoint(inside)

    vtk_poly.SetPoints(vtk_vertices)

    for i in range(len(boundary)) :
        vtk_boundary_loop.GetPointIds().InsertNextId(i)

    vtk_cell.InsertNextCell(vtk_boundary_loop)
    vtk_boundary.SetPoints(vtk_poly.GetPoints())
    vtk_boundary.SetPolys(vtk_cell)

    # Triangulate
    delaunay = vtk.vtkDelaunay2D()
    delaunay.SetInputData(vtk_poly)
    delaunay.SetSourceData(vtk_boundary)
    
    delaunay.Update()
    return delaunay.GetOutput()

#직선의 교차점
def get_intersect_point2D_with_line(line1, line2) :
    x1 = line1[0][0] 
    y1 = line1[0][1]
    x2 = line1[1][0]
    y2 = line1[1][1]

    x3 = line2[0][0]
    y3 = line2[0][1]
    x4 = line2[1][0]
    y4 = line2[1][1]

    DE = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)

    intersect_x = 0
    intersect_y = 0
    if DE == 0 :
        return None
    else :
        intersect_x = ((x1*y2-y1*x2)*(x3-x4) - (x3*y4-y3*x4)*(x1-x2)) / DE
        intersect_y = ((x1*y2-y1*x2)*(y3-y4) - (x3*y4-y3*x4)*(y1-y2)) / DE

    intersect_x = round(intersect_x, 12)
    intersect_y = round(intersect_y, 12)

    return [intersect_x, intersect_y]

#2차원 공간에서 두 선분이 겹치는지 확인
def get_intersect_point2D_with_segment(line1, line2) :
    x1 = line1[0][0] 
    y1 = line1[0][1]
    x2 = line1[1][0]
    y2 = line1[1][1]

    x3 = line2[0][0]
    y3 = line2[0][1]
    x4 = line2[1][0]
    y4 = line2[1][1]

    intersect_pnt = get_intersect_point2D_with_line(line1, line2)
    if intersect_pnt == None :
        return None
    intersect_x = intersect_pnt[0]
    intersect_y = intersect_pnt[1]

    chk_max1 = (intersect_x > max(x1, x2)) or (intersect_y > max(y1, y2))
    chk_min1 = (intersect_x < min(x1, x2)) or (intersect_y < min(y1, y2))
    chk_max2 = (intersect_x > max(x3, x4)) or (intersect_y > max(y3, y4))
    chk_min2 = (intersect_x < min(x3, x4)) or (intersect_y < min(y3, y4))

    if chk_max1 or chk_min1 or chk_max2 or chk_min2 :
        return None

    return [intersect_x, intersect_y]

#교차점을 구한다 : 2차원 평면(x-y) 에서 겹치는 포인트를 찾고 z 축의 차이가 설정된 tolerance 보다 작으면 교차하는 것으로 간주
def get_intersect_point(line1, line2, z_tolerance) :
    line1_2D = lineTo2D(line1)
    line2_2D = lineTo2D(line2)
    intersect_2D = get_intersect_point2D_with_segment(line1_2D, line2_2D)

    if intersect_2D == None :
        return []

    if line3_magnitute(line1) == 0.0 :
        return line1[0]

    if line3_magnitute(line2) == 0.0 :
        return line2[0]

    mag_z1 = line1[1][2] - line1[0][2]
    mag_z2 = line2[1][2] - line2[0][2]

    mag_z1 = mag_z1 * line2_magnitute([vertexTo2D(line1[0]), intersect_2D]) / line2_magnitute(line1_2D) 
    mag_z2 = mag_z2 * line2_magnitute([vertexTo2D(line2[0]), intersect_2D]) / line2_magnitute(line2_2D) 

    v_z1 = line1[0][2] + mag_z1
    v_z2 = line2[0][2] + mag_z2

    if np.abs(v_z1 - v_z2) < z_tolerance :
        v_z = (v_z1 + v_z2)  / 2
        point = [intersect_2D[0], intersect_2D[1], v_z]
        return point
    else :
        return []

#3차원 좌표를 x-y 좌표로
def vertexTo2D(vertex) :
    return [vertex[0], vertex[1]]

#3차원 선을 x-y 좌표로
def lineTo2D(line) :
    a = vertexTo2D(line[0])
    b = vertexTo2D(line[1])
    return [a, b]

#벡터 크기
def vector_magnitute(vector) :
    mag = np.linalg.norm(np.array(vector))
    return mag

#3차원 선 크기
def line3_magnitute(line) :
    v_x = line[0][0] - line[1][0]
    v_y = line[0][1] - line[1][1]
    v_z = line[0][2] - line[1][2]

    return vector_magnitute([v_x , v_y, v_z])

#2차원 선 크기
def line2_magnitute(line) :
    v_x = line[0][0] - line[1][0]
    v_y = line[0][1] - line[1][1]

    return vector_magnitute([v_x , v_y])

#vtkPolyData 를 point, face의 list 로 변환
def vtkPoly_to_MeshData(vtk_poly):
    point_list = list()
    num_of_points = vtk_poly.GetNumberOfPoints()
    for i in range(num_of_points) :
        point_list.append(vtk_poly.GetPoint(i))
        
    face_list = list()
    poly_cells = vtk_poly.GetPolys()
    
    num_of_cells = poly_cells.GetNumberOfCells()
    for i in range(num_of_cells) :
        face = list()
        idList = vtk.vtkIdList()
        poly_cells.GetCellAtId(i, idList)

        num_of_ids = idList.GetNumberOfIds()
        for j in range(num_of_ids) :
            face.append(idList.GetId(j))

        face_list.append(face)

    return point_list, face_list

def generate_normals(vtk_poly) :
    norm_filter = vtk.vtkPolyDataNormals()
    norm_filter.SetInputData(vtk_poly)
    norm_filter.ComputeCellNormalsOn()
    norm_filter.FlipNormalsOff()

    norm_filter.Update()

    poly_out = vtk.vtkPolyData()
    poly_out.DeepCopy(norm_filter.GetOutput())

    normals = poly_out.GetPointData().GetNormals()
    normal_vector = normals.GetTuple(0)

    if normal_vector[2] < 0 :
        norm_filter = vtk.vtkPolyDataNormals()
        norm_filter.SetInputData(vtk_poly)
        norm_filter.ComputeCellNormalsOn()
        norm_filter.FlipNormalsOn()

        norm_filter.Update()

        poly_out = vtk.vtkPolyData()
        poly_out.DeepCopy(norm_filter.GetOutput())

    return poly_out

class VtkTriMethod(Enum):
    TRIANGLE_FILTER = 0
    DELAUNAY = 1

class UnionMeshBound:
    def __init__(self, z_tolerance, vertex_distance=2.0, tri_method=VtkTriMethod.TRIANGLE_FILTER):
        self.bound_list = list()                #처리할 Bound 리스트
        self.check_processed = dict()           #처리 되었는지 체크
        self.check_processed_point = dict()     #처리 되었는지 체크
        self.result_list = list()
        self.result_id_keys_list = list()
        self.z_tolerance = z_tolerance
        self.vertex_distance = vertex_distance
        self.tri_method = tri_method

    #boundary 포인트가 시계방향으로 정렬되어있어야 함
    def add(self, bound):
        self.bound_list.append(bound)
        self.check_processed[len(self.bound_list)-1] = False
        self.check_processed_point[len(self.bound_list)-1] = dict()

    def find_outer_line(self, ref_line, intersect_list, prev_line) :
        rad_ref = calc_line_vector_rad(ref_line)
        rad_max = None
        max_item = None
        dis_max = None
        next_dis_min = None

        for intersect_item in intersect_list :
            intersect_point = intersect_item[0]
            bound_id = intersect_item[1]
            point_id = self.next_point_idx(bound_id, intersect_item[2])
            next_pnt = self.bound_list[bound_id][point_id]

            if self.is_near_point(intersect_point, next_pnt, 0.01) :
                continue

            if self.is_near_point2D(vertexTo2D(intersect_point), vertexTo2D(ref_line[0]), 0.01) and prev_line != None :
                rad_prev = calc_line_vector_rad([prev_line[1], prev_line[0]])
                rad_cur = calc_line_vector_rad(ref_line)
                rad_chk = calc_line_vector_rad([intersect_point, next_pnt])

                cmp_prev = adapt_range2(rad_prev - rad_cur)
                cmp_chk = adapt_range2(rad_chk - rad_cur)

                if cmp_chk >= cmp_prev :
                    continue

            intersect_pnt_distance = line2_magnitute(lineTo2D([ref_line[1], intersect_point]))

            rad_chk = calc_line_vector_rad([intersect_point, next_pnt])
            rad_cmp = rad_chk - rad_ref
            rad_cmp = adapt_range(rad_cmp)

            if rad_cmp <= 0.0 : 
                intersect_pnt_distance = -intersect_pnt_distance

            next_dis = line2_magnitute(lineTo2D([intersect_point, next_pnt]))
            if dis_max == None or dis_max < intersect_pnt_distance :
                dis_max = intersect_pnt_distance
                rad_max = rad_cmp
                next_dis_min = next_dis
                max_item = intersect_item
            elif dis_max == intersect_pnt_distance :
                if rad_max == None or rad_max < rad_cmp :
                    rad_max = rad_cmp
                    next_dis_min = next_dis
                    max_item = intersect_item
                elif rad_max == rad_cmp :
                    next_dis_min = next_dis
                    if next_dis_min == None or next_dis_min > next_dis:
                        max_item = intersect_item

        return [rad_max, max_item]

    #distance 보다 점들 간 간격이 가까운지 체크
    def is_near_point(self, pnt1, pnt2, distance):
        mag = line3_magnitute([pnt1, pnt2])
        return mag < distance

    def is_near_point2D(self, pnt1, pnt2, distance):
        mag = line2_magnitute([pnt1, pnt2])
        return mag < distance

    #포인트와 선이 distance 보다 가까이 있는지 체크
    def is_near_line(self, line, pnt, distance) :
        x0 = pnt[0]
        y0 = pnt[1]

        x1 = line[0][0]
        y1 = line[0][1]

        x2 = line[1][0]
        y2 = line[1][1]

        if x1 == x2 and y1 == y2 :
            return self.is_near_point(line[0], pnt, distance)

        A = np.abs((x2-x1) * (y1-y0) - (x1-x0) * (y2-y1))
        B = np.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))

        dis = A/B

        a = (y2-y1)
        b = (x1-x2)
        c = -(a*x1 + b*y1)

        pnt_x = (b*(b*x0-a*y0) - a*c) / (a*a + b*b)
        pnt_y = (a*(-b*x0 + a*y0) - b*c) / (a*a + b*b)

        cond1 = pnt_x < max(x1, x2) and pnt_x > min(x1, x2) and pnt_y < max(y1, y2) and pnt_y > min(y1, y2)
        cond2 = pnt_x == x1 and pnt_x == x2 and pnt_y < max(y1, y2) and pnt_y > min(y1, y2)
        cond3 = pnt_x < max(x1, x2) and pnt_x > min(x1, x2) and pnt_y == y1 and pnt_y == y2
        if cond1 or cond2 or cond3 : 
            if dis < distance :
                mag_line = line2_magnitute(lineTo2D(line))
                mag_pnt = line2_magnitute([vertexTo2D(line[0]), [pnt_x, pnt_y]])
                v_z = (line[1][2] - line[0][2]) * mag_pnt / mag_line
                z = line[0][2] + v_z

                if np.abs(z - pnt[2]) < self.z_tolerance: 
                    return True
        else :
            mag1 = line2_magnitute([pnt, line[0]])
            mag2 = line2_magnitute([pnt, line[1]])

            z_diff1 = np.abs(pnt[2] - line[0][2])
            z_diff2 = np.abs(pnt[2] - line[1][2])

            if mag1 < mag2 :
                if mag1 < distance and z_diff1 < self.z_tolerance :
                    return True
            else :
                if mag2 < distance and z_diff2 < self.z_tolerance :
                    return True
        return False

    #선과 교차하는 선을 boundary list 에서 모두 찾는다
    def find_intersect_list(self, bound_id, line) :
        intersect_list = list()
        for i in range(len(self.bound_list)) :
            if i == bound_id :
                continue
            for j in range(len(self.bound_list[i])):
                j_next = self.next_point_idx(i, j)
                chk_line = [self.bound_list[i][j], self.bound_list[i][j_next]]

                intersect_pnt = []
                if (chk_line[0][0] == line[1][0]) and (chk_line[0][1] == line[1][1]) and (chk_line[0][2] == line[1][2]) :
                    intersect_pnt = chk_line[0]
                else :
                    intersect_pnt = get_intersect_point(line, chk_line, self.z_tolerance)

                if len(intersect_pnt) == 3 :
                    #if intersect_pnt != chk_line[1] :
                    if not self.is_near_point2D(intersect_pnt, chk_line[1], 0.01):
                        intersect_list.append([intersect_pnt, i, j])
                else :
                    if self.is_near_line(line, chk_line[1], 0.01) :
                        continue
                    elif self.is_near_line(line, chk_line[0], 0.01) :
                        intersect_pnt = get_intersect_point2D_with_line(line, chk_line)
                        
                        chk_range_x = False
                        chk_range_y = False
                        if intersect_pnt != None :
                            chk_range_x = intersect_pnt[0] > max(line[0][0], line[1][0]) or intersect_pnt[0] < min(line[0][0], line[1][0])
                            chk_range_y = intersect_pnt[1] > max(line[0][1], line[1][1]) or intersect_pnt[1] < min(line[0][1], line[1][1])

                        if intersect_pnt == None or chk_range_x or chk_range_y :
                            if line2_magnitute([chk_line[0], line[0]]) > line2_magnitute([chk_line[0], line[1]]) :
                                intersect_pnt = line[1]
                            else :
                                intersect_pnt = line[0]
                        else :
                            z_diff = line[1][2] - line[0][2]
                            z_offset = z_diff * line2_magnitute([intersect_pnt, line[0]]) / line2_magnitute(line)
                            intersect_z = line[0][2] + z_offset
                            intersect_pnt.append(intersect_z)
                        
                        intersect_list.append([intersect_pnt, i, j])
                    elif self.is_near_line(chk_line, line[1], 0.01) :
                        intersect_list.append([line[1], i, j])
                        
        return intersect_list

    def next_point_idx(self, bound_id, pnt_idx) :
        next_idx = pnt_idx + 1
        if next_idx > (len(self.bound_list[bound_id]) - 1) :
            next_idx = 0
        return next_idx

    def process(self, test=False):
        for bid in self.check_processed_point :
            for pid in self.check_processed_point[bid]:
                self.check_processed_point[bid][pid] = 0.0
                
        while len(self.check_processed) > 0:
            item = self.check_processed.popitem()
            current_id = item[0]
            current_pnt_idx = 0
            result = list()
            result_idx = dict()
            """
            #For Debug
            if test == True :
                #if current_id == 0:
                print("pop : {}".format(current_id))
                self.result_list.append(self.bound_list[current_id])

                result = self.bound_list[current_id]
                vtk_vertices = vtk.vtkPoints()  # 점 정보
                vtk_faces = vtk.vtkCellArray()
                vtk_faces.InsertNextCell(len(result))
                
                for point in result :
                    point_id = vtk_vertices.InsertNextPoint(point)
                    vtk_faces.InsertCellPoint(point_id)

                poly_result = vtk.vtkPolyData()
                poly_result.SetPoints(vtk_vertices)
                poly_result.SetPolys(vtk_faces)
                poly_result = vtkTrianglePoly(poly_result)
                poly_result = vtkFlip_y(poly_result)
                poly_result = vtkSwap_yz(poly_result)
                write_obj(poly_result, str(current_id))

                continue
            """
            #if test : 
                #print("pop : {}".format(current_id))

            start_id = current_id 
            start_pnt_idx = current_pnt_idx

            loop_cnt = 0
            loop_limit = 500
            
            prev_line = None
            current_line = [self.bound_list[current_id][current_pnt_idx], self.bound_list[current_id][current_pnt_idx+1]]
            result.append(current_line[0])
            result_idx[current_id] = dict()
            result_idx[current_id][current_pnt_idx] = len(result) - 1

            #if test : 
                #print("result1 : {}, {}, {}".format(current_id, current_pnt_idx, current_line[0]))

            while True :
                #무한루프 방지
                if loop_cnt > loop_limit :
                    print("err")
                    break
                loop_cnt += 1

                bound_item = self.bound_list[current_id]
                next_pnt_idx = self.next_point_idx(current_id, current_pnt_idx)
                next_next_pnt_idx = self.next_point_idx(current_id, next_pnt_idx)

                next_line = [bound_item[next_pnt_idx], bound_item[next_next_pnt_idx]]

                #check all line 
                next_item = None
                intersect_list = self.find_intersect_list(current_id, current_line) 
                
                #if test and current_id == 10 and current_pnt_idx == 6 : 
                    #print("find_intersect : current_id={}, current_line_0={}, current_line_1={}, len={}, {}".format(current_id, current_pnt_idx, next_pnt_idx, len(intersect_list), current_line))
                if len(intersect_list) > 0 :
                    current_rad = calc_line_vector_rad(current_line)
                    next_rad = calc_line_vector_rad([current_line[1], next_line[1]])
                    candidate_item = self.find_outer_line(current_line, intersect_list, prev_line)
                    if candidate_item != None and candidate_item[0] != None and candidate_item[1] != None :
                        candidate_rad = candidate_item[0]
                        intersect_pnt = candidate_item[1][0]
                        #if test : 
                            #print("candidate_rad : {}".format(candidate_item))

                        if self.is_near_point(intersect_pnt, current_line[1], 0.01) :
                            chk_rad = next_rad - current_rad
                            chk_rad = adapt_range(chk_rad)
                            #if test :
                                #print("near Pnt : {}, {}, {}, {}".format(current_id, current_pnt_idx, chk_rad, candidate_rad))

                            if chk_rad < candidate_rad :
                                #print("next : {}".format(candidate_item))
                                next_item = candidate_item
                        elif candidate_rad > 0 :
                            #print("candidate_rad : {}".format(candidate_rad))
                            next_item = candidate_item

                if next_item != None :
                    point_coord = next_item[1][0]
                    bound_id = next_item[1][1]
                    point_id = next_item[1][2]

                    self.check_processed_point[current_id][current_pnt_idx] = line3_magnitute([self.bound_list[current_id][current_pnt_idx], point_coord])

                    if bound_id in self.check_processed :
                        self.check_processed.pop(bound_id)

                    current_id = bound_id
                    current_pnt_idx = point_id
                    next_pnt_idx = self.next_point_idx(current_id, current_pnt_idx)
                    
                    #print("{}, {}, {}".format(current_pnt_idx, next_pnt_idx, len(self.bound_list[current_id])))
                    prev_line = current_line
                    current_line = [point_coord, self.bound_list[current_id][next_pnt_idx]]

                    #print(current_id)
                    if not self.is_near_point2D(point_coord, result[-1], 0.01) :
                        #if test : 
                            #print("result2 : {}, {}, {}".format(current_id, current_pnt_idx, point_coord))
                        result.append(point_coord)
                    if current_id not in result_idx :
                        result_idx[current_id] = dict()
                    if current_pnt_idx not in result_idx[current_id] :
                        result_idx[current_id][current_pnt_idx] = len(result) - 1

                    chk_length = line3_magnitute([self.bound_list[current_id][current_pnt_idx], point_coord])

                    if (current_pnt_idx in self.check_processed_point[current_id]) and (self.check_processed_point[current_id][current_pnt_idx] >= chk_length) and (self.check_processed_point[current_id][current_pnt_idx] != 0.0) :
                        break
                else :
                    self.check_processed_point[current_id][current_pnt_idx] = line3_magnitute([self.bound_list[current_id][current_pnt_idx], self.bound_list[current_id][next_pnt_idx]])

                    current_pnt_idx = self.next_point_idx(current_id, current_pnt_idx)
                    next_pnt_idx = self.next_point_idx(current_id, current_pnt_idx)

                    prev_line = current_line
                    current_line = [bound_item[current_pnt_idx], bound_item[next_pnt_idx]]

                    if (current_pnt_idx in self.check_processed_point[current_id]) and (self.check_processed_point[current_id][current_pnt_idx] > 0.0) :
                        break

                    if not self.is_near_point2D(current_line[0], result[-1], 0.01) :
                        #if test : 
                            #print("result3 : {}, {}, {}".format(current_id, current_pnt_idx, current_line[0]))
                        result.append(current_line[0])
                    if current_id not in result_idx :
                        result_idx[current_id] = dict()
                    if current_pnt_idx not in result_idx[current_id] :
                        result_idx[current_id][current_pnt_idx] = len(result) - 1

            #시작점과 다르면 시작점부터 마지막 포인트 까지 잘라내기
            if (current_pnt_idx != start_pnt_idx) or (current_id != start_id) :
                #if test :
                    #print("slice : {}, {}, {}, {}".format(start_id, current_id, start_pnt_idx, current_pnt_idx))

                if current_id in result_idx and current_pnt_idx in result_idx[current_id] :
                    idx = result_idx[current_id][current_pnt_idx]
                    #if test :
                        #print("slice_idx : {}".format(idx))
                    result = result[idx:]
            if self.is_near_point2D(result[0], result[-1], 0.01) :
                result = result[:-1]
                
            if test : 
                result.reverse()
            if len(result) >= 4 :
                result_id_keys = result_idx.keys()
                self.result_id_keys_list.append(result_id_keys)
                self.result_list.append(result)
            #if test : 
                #print("append : {}".format(len(result)))

    def reduce_points(self, point_list, dis_threshold, rad_threshold) :
        new_points = list()
        for i in range(len(point_list)) :
            prev_point = point_list[i-1]
            current_point = point_list[i]
            next_point = point_list[0]
            if i+1 < len(point_list) :
                next_point = point_list[i+1]

            dis_prev = line2_magnitute([prev_point, current_point])
            dis_next = line2_magnitute([current_point, next_point])
            is_delete = False
            if dis_prev < dis_threshold or dis_next < dis_threshold :
                rad_prev_line = calc_line_vector_rad([prev_point, current_point])
                rad_next_line = calc_line_vector_rad([current_point, next_point])

                rad_diff = adapt_range(rad_prev_line - rad_next_line)

                if rad_diff < rad_threshold and rad_diff > -rad_threshold :
                    is_delete = True
                    
            if not is_delete :
                new_points.append(current_point)

        return new_points

    def get_poly_result(self) : 
        result_all = vtk.vtkPolyData()
        for i in range(len(self.result_list)) :
            result = self.result_list[i]
            result_id_keys = self.result_id_keys_list[i]

            if len(result) < 4 :
                continue
            points = self.reduce_points(result, 0.5, 0.2)

            if self.tri_method == VtkTriMethod.TRIANGLE_FILTER :
                vtk_vertices = vtk.vtkPoints()  # 점 정보
                vtk_faces = vtk.vtkCellArray()
                vtk_faces.InsertNextCell(len(points))
                
                for point in points :
                    point_id = vtk_vertices.InsertNextPoint(point)
                    vtk_faces.InsertCellPoint(point_id)

                poly_result = vtk.vtkPolyData()
                poly_result.SetPoints(vtk_vertices)
                poly_result.SetPolys(vtk_faces)
                poly_result = vtkTrianglePoly(poly_result)

            else :
                points_2d = [x[0:2] for x in points]
                points_kdTree = sp.KDTree(points_2d)
                add_point_list = list()

                for result_id in result_id_keys :
                    bound = self.bound_list[result_id]

                    for pnt in bound :
                        near_points = points_kdTree.query_ball_point(vertexTo2D(pnt), self.vertex_distance * 1.5)
                        if len(near_points) > 0 :
                            continue
                        add_point_list.append(pnt)

                add_point_check_list = list()
                new_add_point_list = list()

                if len(add_point_list) > 0 :
                    add_points_2d = [x[0:2] for x in add_point_list]
                    add_points_kdTree = sp.KDTree(add_points_2d)

                    for i in range(len(add_point_list)) :
                        if i in add_point_check_list :
                            continue
                        add_point = add_point_list[i]
                        near_points = add_points_kdTree.query_ball_point(vertexTo2D(add_point), self.vertex_distance)
                        if len(near_points) == 0 :
                            continue
                        else :
                            # 평균값으로
                            near_pnt_sum = np.array([0.0,0.0,0.0])
                            near_pnt_cnt = 0
                            for near_pnt_idx in near_points :
                                if near_pnt_idx in add_point_check_list :
                                    continue
                                near_pnt = np.array(add_point_list[near_pnt_idx])
                                near_pnt_sum += near_pnt
                                near_pnt_cnt += 1
                                add_point_check_list.append(near_pnt_idx)

                            if near_pnt_cnt > 0 :
                                new_add_pnt = near_pnt_sum / near_pnt_cnt
                                new_add_point_list.append(new_add_pnt.tolist())

                poly_result = vtkDelaunay2DTriangulation(points, new_add_point_list)
            
            poly_result = smooth_mesh(poly_result)
            result_all = vtkAppend(result_all, poly_result)
        return result_all
