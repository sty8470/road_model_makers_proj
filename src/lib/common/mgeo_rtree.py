import rtree
import numpy as np
from lib.mgeo.class_defs.mgeo_item import MGeoItem

class MgeoRTreeItem :
    def __init__(self, item_type, item_data, rtree_property) :
        self.rtree_index = rtree.index.Index(properties=rtree_property)
        self.rtree_id = 0
        self.rtree_data_dict = dict()       #mgeo idx 와 rtree 데이터 매칭 list of {id, bbox}
        self.item_type = item_type
        self.min_x = None
        self.min_y = None
        self.min_z = None
        self.max_x = None
        self.max_y = None
        self.max_z = None

        for item_idx in item_data :
            item = item_data[item_idx]
            self.insert(item)

    def point_to_bbox(self, point, size=1.0) :
        x = point[0]
        y = point[1]
        z = point[2]

        min_x = x - size/2
        max_x = x + size/2
        min_y = y - size/2
        max_y = y + size/2
        min_z = z - size/2
        max_z = z + size/2

        bbox = [min_x, min_y, min_z, max_x, max_y, max_z]
        return bbox

    def pointitem_to_bbox(self, mgeo_item, size=1.0) :
        return self.point_to_bbox(mgeo_item.point, size)

    def lineplaneitem_to_bbox(self, mgeo_item) :
        min_x = mgeo_item.bbox_x[0]
        max_x = mgeo_item.bbox_x[1]
        min_y = mgeo_item.bbox_y[0]
        max_y = mgeo_item.bbox_y[1]
        min_z = mgeo_item.bbox_z[0]
        max_z = mgeo_item.bbox_z[1]

        bbox = [min_x, min_y, min_z, max_x, max_y, max_z]
        return bbox

    def points_to_bbox_list(self, points) :
        bbox_list = list()
        for point in points :
            bbox = self.point_to_bbox(point)
            bbox_list.append(bbox)

        return bbox_list

    #전체 bbox 업데이트
    def update_rtree_bbox(self) :
        self.min_x = None
        self.min_y = None
        self.min_z = None
        self.max_x = None
        self.max_y = None
        self.max_z = None

        for item_idx in self.rtree_data_dict :
            rtree_data_list = self.rtree_data_dict[item_idx]
            for rtree_data in rtree_data_list :
                bbox = rtree_data['bbox']
                self.update_min_max(bbox)

    #bbox 아이템 하나 추가하여 업데이트
    def update_min_max(self, bbox) :
        min_x = bbox[0]
        min_y = bbox[1]
        min_z = bbox[2]

        max_x = bbox[3]
        max_y = bbox[4]
        max_z = bbox[5]

        if self.min_x is None or self.min_x > min_x :
            self.min_x = min_x
        if self.min_y is None or self.min_y > min_y :
            self.min_y = min_y
        if self.min_z is None or self.min_z > min_z :
            self.min_z = min_z

        if self.max_x is None or self.max_x < max_x :
            self.max_x = max_x
        if self.max_y is None or self.max_y < max_y :
            self.max_y = max_y
        if self.max_z is None or self.max_z < max_z :
            self.max_z = max_z

        if self.min_x == self.max_x :
            self.min_x -= np.finfo(float).eps
            self.max_x += np.finfo(float).eps

        if self.min_y == self.max_y :
            self.min_y -= np.finfo(float).eps
            self.max_y += np.finfo(float).eps

        if self.min_z == self.max_z :
            self.min_z -= np.finfo(float).eps
            self.max_z += np.finfo(float).eps

    def get_bbox(self) :
        bbox = [self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z]
        if None in bbox :
            return None
        return bbox

    def insert(self, item) :
        if self.item_type == MGeoItem.NODE :
            bbox = self.pointitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.NODE, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})

            self.rtree_id += 1

        elif self.item_type == MGeoItem.LINK :
            bbox = self.lineplaneitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.LINK, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
            self.rtree_id += 1

        elif self.item_type == MGeoItem.TRAFFIC_LIGHT :
            bbox = self.pointitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.TRAFFIC_LIGHT, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
            self.rtree_id += 1

        elif self.item_type == MGeoItem.TRAFFIC_SIGN :
            bbox = self.pointitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.TRAFFIC_SIGN, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
            self.rtree_id += 1

        elif self.item_type == MGeoItem.SYNCED_TRAFFIC_LIGHT :
            points = item.get_synced_signal_points()
            bbox_list = self.points_to_bbox_list(points)
            item_info = {'type':MGeoItem.SYNCED_TRAFFIC_LIGHT, 'id': item.idx}
            self.rtree_data_dict[item.idx] = list()

            for bbox in bbox_list :
                self.update_min_max(bbox)
                self.rtree_index.insert(self.rtree_id, bbox, item_info)
                self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
                self.rtree_id += 1

        elif self.item_type == MGeoItem.INTERSECTION_CONTROLLER :
            points = item.get_intersection_controller_points()
            bbox_list = self.points_to_bbox_list(points)
            item_info = {'type':MGeoItem.INTERSECTION_CONTROLLER, 'id': item.idx}
            self.rtree_data_dict[item.idx] = list()

            for bbox in bbox_list :
                self.update_min_max(bbox)
                self.rtree_index.insert(self.rtree_id, bbox, item_info)
                self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
                self.rtree_id += 1

        elif self.item_type == MGeoItem.JUNCTION :
            points = item.get_jc_node_points()
            bbox_list = self.points_to_bbox_list(points)
            item_info = {'type':MGeoItem.JUNCTION, 'id': item.idx}
            self.rtree_data_dict[item.idx] = list()

            for bbox in bbox_list :
                self.update_min_max(bbox)
                self.rtree_index.insert(self.rtree_id, bbox, item_info)
                self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
                self.rtree_id += 1

        elif self.item_type == MGeoItem.LANE_NODE :
            bbox = self.pointitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.LANE_NODE, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})

            self.rtree_id += 1

        elif self.item_type == MGeoItem.LANE_BOUNDARY :
            bbox = self.lineplaneitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.LANE_BOUNDARY, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
            self.rtree_id += 1

        elif self.item_type == MGeoItem.SINGLECROSSWALK :
            bbox = self.lineplaneitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.SINGLECROSSWALK, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
            self.rtree_id += 1

        elif self.item_type == MGeoItem.ROADPOLYGON :
            bbox = self.lineplaneitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.ROADPOLYGON, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
            self.rtree_id += 1

        elif self.item_type == MGeoItem.CROSSWALK :
            item_info = {'type':MGeoItem.CROSSWALK, 'id': item.idx}
            self.rtree_data_dict[item.idx] = list()
            
            for scw in item.single_crosswalk_list :
                bbox = self.lineplaneitem_to_bbox(scw)
                self.update_min_max(bbox)
                self.rtree_index.insert(self.rtree_id, bbox, item_info)
                self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
                self.rtree_id += 1

            for tl in item.ref_traffic_light_list :
                bbox = self.pointitem_to_bbox(tl)
                self.update_min_max(bbox)
                self.rtree_index.insert(self.rtree_id, bbox, item_info)
                self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
                self.rtree_id += 1

        elif self.item_type == MGeoItem.PARKING_SPACE :
            bbox = self.lineplaneitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.PARKING_SPACE, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
            self.rtree_id += 1

        elif self.item_type == MGeoItem.SURFACE_MARKING :
            bbox = self.lineplaneitem_to_bbox(item)
            self.update_min_max(bbox)
            item_info = {'type':MGeoItem.SURFACE_MARKING, 'id': item.idx}
            self.rtree_index.insert(self.rtree_id, bbox, item_info)
            self.rtree_data_dict[item.idx] = list()
            self.rtree_data_dict[item.idx].append({'id':self.rtree_id, 'bbox':bbox})
            self.rtree_id += 1

    def update(self, item_idx, item, update_bbox=True) :
        #item idx 가 업데이트 되는 경우도 있으므로 item.idx 가 아닌 기존의 idx 를 입력받을 수 있도록 함
        self.delete(item_idx, update_bbox)
        self.insert(item)

    def delete(self, item_idx, update_bbox=True) :
        if item_idx in self.rtree_data_dict :
            rtree_item_list = self.rtree_data_dict[item_idx]
            for rtree_item in rtree_item_list :
                rtree_id = rtree_item['id']
                rtree_bbox = rtree_item['bbox']
                self.rtree_index.delete(rtree_id, rtree_bbox)
        if update_bbox :
            self.update_rtree_bbox()

    def intersection(self, bbox) :
        hits = list(self.rtree_index.intersection(bbox, objects=True))

        hit_item_list = list()

        for hit_item in hits :
            if hit_item.object not in hit_item_list :
                hit_item_list.append(hit_item.object)

        return hit_item_list

    def slice_line_by_bbox(self, normal_vector_norm, point_pivot, point_to_slice) :
        out_point = None
        v_t = None
        if normal_vector_norm[0] != 0 : 
            if point_to_slice[1] < self.min_y or point_to_slice[1] > self.max_y :
                if point_to_slice[1] < self.min_y :
                    slice_y = self.min_y
                else :
                    slice_y = self.max_y

                if (point_pivot - point_to_slice)[1] != 0 :
                    v_t = (slice_y - point_to_slice[1]) / (point_pivot - point_to_slice)[1]
                    out_point = v_t * (point_pivot - point_to_slice) + point_to_slice

            if out_point is None or v_t is None or v_t < 0 :
                if point_to_slice[2] < self.min_z or point_to_slice[2] > self.max_z :
                    if point_to_slice[2] < self.min_z :
                        slice_z = self.min_z
                    else :
                        slice_z = self.max_z

                    if (point_pivot - point_to_slice)[2] != 0 :
                        v_t = (slice_z - point_to_slice[2]) / (point_pivot - point_to_slice)[2]
                        out_point = v_t * (point_pivot - point_to_slice) + point_to_slice

        elif normal_vector_norm[1] != 0 : 
            if point_to_slice[0] < self.min_x or point_to_slice[0] > self.max_x :
                if point_to_slice[0] < self.min_x :
                    slice_x = self.min_x
                else :
                    slice_x = self.max_x

                if (point_pivot - point_to_slice)[0] != 0 :
                    v_t = (slice_x - point_to_slice[0]) / (point_pivot - point_to_slice)[0]
                    out_point = v_t * (point_pivot - point_to_slice) + point_to_slice

            if out_point is None or v_t is None or v_t < 0 :
                if point_to_slice[2] < self.min_z or point_to_slice[2] > self.max_z :
                    if point_to_slice[2] < self.min_z :
                        slice_z = self.min_z
                    else :
                        slice_z = self.max_z

                    if (point_pivot - point_to_slice)[2] != 0 :
                        v_t = (slice_z - point_to_slice[2]) / (point_pivot - point_to_slice)[2]
                        out_point = v_t * (point_pivot - point_to_slice) + point_to_slice
        
        elif normal_vector_norm[2] != 0 : 
            if point_to_slice[0] < self.min_x or point_to_slice[0] > self.max_x :
                if point_to_slice[0] < self.min_x :
                    slice_x = self.min_x
                else :
                    slice_x = self.max_x

                if (point_pivot - point_to_slice)[0] != 0 :
                    v_t = (slice_x - point_to_slice[0]) / (point_pivot - point_to_slice)[0]
                    out_point = v_t * (point_pivot - point_to_slice) + point_to_slice

            if out_point is None or v_t is None or v_t < 0 :
                if point_to_slice[1] < self.min_y or point_to_slice[1] > self.max_y :
                    if point_to_slice[1] < self.min_y :
                        slice_y = self.min_y
                    else :
                        slice_y = self.max_y

                    if (point_pivot - point_to_slice)[1] != 0 :
                        v_t = (slice_y - point_to_slice[1]) / (point_pivot - point_to_slice)[1]
                        out_point = v_t * (point_pivot - point_to_slice) + point_to_slice

        if out_point is None or v_t is None or v_t < 0:
            return None
        else :
            is_out_of_bbox = out_point[0] < self.min_x or out_point[0] > self.max_x or \
                                out_point[1] < self.min_y or out_point[1] > self.max_y or \
                                out_point[2] < self.min_z or out_point[2] > self.max_z
            if is_out_of_bbox :
                return None
                
            return out_point

    def get_bbox_points_inside_planes(self, plane_list):
        point_list = [  [self.min_x, self.min_y, self.min_z],\
                        [self.min_x, self.min_y, self.max_z],\
                        [self.min_x, self.max_y, self.min_z],\
                        [self.min_x, self.max_y, self.max_z],\
                        [self.max_x, self.min_y, self.min_z],\
                        [self.max_x, self.min_y, self.max_z],\
                        [self.max_x, self.max_y, self.min_z],\
                        [self.max_x, self.max_y, self.max_z]]

        ret_points = list()
        for point in point_list :
            is_inside = True
            
            for plane in plane_list :
                plane_normal = np.array(plane[0])
                plane_const = np.array(plane[1])

                if np.inner(plane_normal, np.array(point)) + plane_const > 0 :
                    is_inside = False
                    break
            if is_inside :
                ret_points.append(np.array(point))

        return ret_points

    def intersection_by_perspective_planes(self, select_lines, select_planes):
        if self.get_bbox() is None :
            return list()
        bbox_plane_list = list()
        bbox_plane_list.append([np.array([self.min_x, 0, 0]), [-1, 0, 0]])
        bbox_plane_list.append([np.array([self.max_x, 0, 0]), [1, 0, 0]])
        bbox_plane_list.append([np.array([0, self.min_y, 0]), [0, -1, 0]])
        bbox_plane_list.append([np.array([0, self.max_y, 0]), [0, 1, 0]])
        bbox_plane_list.append([np.array([0, 0, self.min_z]), [0, 0, -1]])
        bbox_plane_list.append([np.array([0, 0, self.max_z]), [0, 0, 1]])

        bbox_point_list = list()

        for bbox_info in bbox_plane_list :
            project_point_list = list()
            normal_vector = bbox_info[0]
            normal_vector_norm = bbox_info[1]

            for select_line in select_lines :
                if np.inner((select_line[0] - select_line[1]), normal_vector_norm) == 0 :
                    project_point_list.append(None)
                else :
                    if normal_vector_norm[0] != 0 : 
                        line_vector = np.array((select_line[0] - select_line[1]))
                        line_t = (normal_vector[0] - select_line[1][0]) / line_vector[0]
                        select_point = line_vector * line_t + select_line[1]
                        is_inside = self.min_y < select_point[1] and self.max_y > select_point[1] and \
                                    self.min_z < select_point[2] and self.max_z > select_point[2]
                        if line_t < 0 :
                            project_point_list.append(None)
                        else :
                            project_point_list.append([select_point,is_inside])
                    elif normal_vector_norm[1] != 0 : 
                        line_vector = np.array((select_line[0] - select_line[1]))
                        line_t = (normal_vector[1] - select_line[1][1]) / line_vector[1]
                        select_point = line_vector * line_t + select_line[1]
                        is_inside = self.min_x < select_point[0] and self.max_x > select_point[0] and \
                                    self.min_z < select_point[2] and self.max_z > select_point[2]
                        if line_t < 0 :
                            project_point_list.append(None)
                        else :
                            project_point_list.append([select_point,is_inside])
                    elif normal_vector_norm[2] != 0 : 
                        line_vector = np.array((select_line[0] - select_line[1]))
                        line_t = (normal_vector[2] - select_line[1][2]) / line_vector[2]
                        select_point = line_vector * line_t + select_line[1]
                        is_inside = self.min_x < select_point[0] and self.max_x > select_point[0] and \
                                    self.min_y < select_point[1] and self.max_y > select_point[1]
                        if line_t < 0 :
                            project_point_list.append(None)
                        else :
                            project_point_list.append([select_point,is_inside])
                    else : 
                        project_point_list.append(None)

            for i in range(len(project_point_list)) :
                point_0_info = project_point_list[i]
                if i == len(project_point_list)-1 :
                    point_1_info = project_point_list[0]
                else : 
                    point_1_info = project_point_list[i+1]

                if point_0_info is None or point_1_info is None :
                    continue
                
                point_0 = point_0_info[0]
                point_1 = point_1_info[0]

                is_inside_point_0 = point_0_info[1]
                is_inside_point_1 = point_1_info[1]

                if is_inside_point_0 and not is_inside_point_1 :      #선택 영역이 전체 bounding box 를 벗ㅇ
                    point_1 = self.slice_line_by_bbox(normal_vector_norm, point_0, point_1)
                    if point_1 is None :
                        continue

                elif not is_inside_point_0 and is_inside_point_1 :
                    point_0 = self.slice_line_by_bbox(normal_vector_norm, point_1, point_0)
                    if point_0 is None :
                        continue

                elif not is_inside_point_0 and not is_inside_point_1 :
                    #continue
                    point_1_new = self.slice_line_by_bbox(normal_vector_norm, point_0, point_1)
                    point_0_new = self.slice_line_by_bbox(normal_vector_norm, point_1, point_0)
                    if point_0_new is None or point_1_new is None :
                        continue
                    else :
                        #print("{}, {}, {}, {}, {}".format(point_0_new, point_1_new, normal_vector_norm, point_0, point_1))
                        point_0 = point_0_new
                        point_1 = point_1_new

                bbox_point_list.append(point_0)
                bbox_point_list.append(point_1)

        bbox_points = self.get_bbox_points_inside_planes(select_planes)
        #print(bbox_points)
        bbox_point_list.extend(bbox_points)

        bbox_point_list = np.array(bbox_point_list)
        if len(bbox_point_list) < 4 :
            return list()

        bbox_x = bbox_point_list[:,0]
        bbox_y = bbox_point_list[:,1]
        bbox_z = bbox_point_list[:,2]
        rtree_search_bbox = [bbox_x.min(), bbox_y.min(), bbox_z.min(), bbox_x.max(), bbox_y.max(), bbox_z.max()]
        #print(rtree_search_bbox)
        return self.intersection(rtree_search_bbox)

class MgeoRTree :
    def __init__(self, mgeo) :
        rtree_property = rtree.index.Property()
        rtree_property.dimension = 3
        self.rtree_dict = dict()

        self.rtree_dict[MGeoItem.NODE] = MgeoRTreeItem(MGeoItem.NODE, mgeo.node_set.nodes, rtree_property)
        self.rtree_dict[MGeoItem.LINK] = MgeoRTreeItem(MGeoItem.LINK, mgeo.link_set.lines, rtree_property)
        self.rtree_dict[MGeoItem.TRAFFIC_LIGHT] = MgeoRTreeItem(MGeoItem.TRAFFIC_LIGHT, mgeo.light_set.signals, rtree_property)
        self.rtree_dict[MGeoItem.TRAFFIC_SIGN] = MgeoRTreeItem(MGeoItem.TRAFFIC_SIGN, mgeo.sign_set.signals, rtree_property)
        self.rtree_dict[MGeoItem.SYNCED_TRAFFIC_LIGHT] = MgeoRTreeItem(MGeoItem.SYNCED_TRAFFIC_LIGHT, mgeo.synced_light_set.synced_signals, rtree_property)
        self.rtree_dict[MGeoItem.INTERSECTION_CONTROLLER] = MgeoRTreeItem(MGeoItem.INTERSECTION_CONTROLLER, mgeo.intersection_controller_set.intersection_controllers, rtree_property)
        self.rtree_dict[MGeoItem.JUNCTION] = MgeoRTreeItem(MGeoItem.JUNCTION, mgeo.junction_set.junctions, rtree_property)
        self.rtree_dict[MGeoItem.LANE_NODE] = MgeoRTreeItem(MGeoItem.LANE_NODE, mgeo.lane_node_set.nodes, rtree_property)
        self.rtree_dict[MGeoItem.LANE_BOUNDARY] = MgeoRTreeItem(MGeoItem.LANE_BOUNDARY, mgeo.lane_boundary_set.lanes, rtree_property)
        self.rtree_dict[MGeoItem.SINGLECROSSWALK] = MgeoRTreeItem(MGeoItem.SINGLECROSSWALK, mgeo.scw_set.data, rtree_property)
        self.rtree_dict[MGeoItem.ROADPOLYGON] = MgeoRTreeItem(MGeoItem.ROADPOLYGON, mgeo.road_polygon_set.data, rtree_property)
        self.rtree_dict[MGeoItem.CROSSWALK] = MgeoRTreeItem(MGeoItem.CROSSWALK, mgeo.cw_set.data, rtree_property)
        self.rtree_dict[MGeoItem.PARKING_SPACE] = MgeoRTreeItem(MGeoItem.PARKING_SPACE, mgeo.parking_space_set.data, rtree_property)
        self.rtree_dict[MGeoItem.SURFACE_MARKING] = MgeoRTreeItem(MGeoItem.SURFACE_MARKING, mgeo.sm_set.data, rtree_property)

    def insert(self, item, item_type) :
        if item_type in self.rtree_dict :
            self.rtree_dict[item_type].insert(item)

    def update(self, item_type, item_idx, item, update_bbox=True) :
        #item idx 가 업데이트 되는 경우도 있으므로 item.idx 가 아닌 기존의 idx 를 입력받을 수 있도록 함
        if item_type in self.rtree_dict :
            self.rtree_dict[item_type].update(item_idx, item, update_bbox)

    def delete(self, item_type, item_idx, update_bbox=True) :
        if item_type in self.rtree_dict :
            self.rtree_dict[item_type].delete(item_idx, update_bbox)

    def intersection(self, item_type, bbox) :
        if item_type in self.rtree_dict :
            return self.rtree_dict[item_type].intersection(bbox)
        return list()

    def intersection_by_perspective_planes(self, item_type, select_lines, select_planes) :
        if item_type in self.rtree_dict :
            return self.rtree_dict[item_type].intersection_by_perspective_planes(select_lines, select_planes)
        return list()
