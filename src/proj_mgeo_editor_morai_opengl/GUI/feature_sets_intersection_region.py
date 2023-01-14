import numpy as np

class BoundingBox:
    '''
    Input: ref_node (grouped link), each link inside of ref_node
    '''
    def __init__(self, link_set):
        self.link_set = link_set.lines
        
        self.bbox_x = list()
        self.bbox_y = list()
        self.curve_segments = list()
        
        self.line_vec_segments_cpr = list()
        self.line_vec_segments_cpa = list()
    
    def check_line_shape(self, dot_prod1, dot_prod2 = None):
        if dot_prod2 == None:
            dot_prod2 = dot_prod1
        
        if dot_prod1 > 0.9 and dot_prod2 > 0.9:
            return 1
        elif (dot_prod1 < 0.9 and dot_prod1 >= 0.05) and dot_prod2 > 0.9:
            return 2
        elif dot_prod1 > 0.9 and (dot_prod2 < 0.9 and dot_prod2 >= 0.05):
            return 3
        else:
            return 0
    
    def check_intersects_hard(self, compared_link, comparand_link):
        '''
        Sample three points or four points
        '''
        if compared_link.idx == comparand_link.idx:
            return
        
        # Select Sample Data based on how many points exist in the line.
        totalSample = len(compared_link.points)
        nSample = 4 if len(compared_link.points) % 2 == 0 else 3
        
        # If there is not enough sample, just sample at least 2 pts
        if totalSample <= 2:
            nSample = totalSample
        
        first_vec = compared_link.points[nSample-1][:2] - compared_link.points[0][:2]
        last_vec = compared_link.points[-1][:2] - compared_link.points[totalSample-2][:2]
        
        heading_first_vec = first_vec / np.linalg.norm(first_vec)
        heading_last_vec = last_vec / np.linalg.norm(last_vec)
        
        dot_prod = np.inner(heading_first_vec, heading_last_vec)
        
        # Straight Line, otherwise curve line
        if dot_prod > 0.9:
            # 비교 되는 대상이 다 Straight Line으로 나옴
            self.bbox_x.clear()
            self.bbox_y.clear()
            
            xin = None
            yin = None
            
            x = compared_link.points[:,0]
            y = compared_link.points[:,1] 
            
            # set bounding box region
            self.bbox_x = [x.min(), x.max()]
            self.bbox_y = [y.min(), y.max()]
            
            for pt in comparand_link.points:
                comparand_pt_x = pt[0]
                comparand_pt_y = pt[1]
                
                if comparand_pt_x >= self.bbox_x[0] and comparand_pt_x <= self.bbox_x[1]:
                    xin = True
                else:
                    xin = False
                    
                if comparand_pt_y >= self.bbox_y[0] and comparand_pt_y <= self.bbox_y[1]:
                    yin = True
                else:
                    yin = False

                if xin == True and yin == True:
                    return xin and yin
        else:
            # 비교되는 대상이 Curve Line      
            self.curve_segments.clear()
            self.bbox_x.clear()
            self.bbox_y.clear()
            
            xin = None
            yin = None
            
            x_list = []
            y_list = []
            for idx in range(totalSample):
                if idx % nSample == 0:
                    if idx == 0:
                        continue
                    # push into list
                    self.curve_segments.append([min(x_list), max(x_list), min(y_list), max(y_list)])
                    x_list.clear()
                    y_list.clear()
                    
                x_list.append(compared_link.points[idx][0])
                y_list.append(compared_link.points[idx][1])
            
            
            for pt in comparand_link.points:
                comparand_pt_x = pt[0]
                comparand_pt_y = pt[1]
                
                # 모든 Box 에 대해서, point 와 비교 한다
                for box in self.curve_segments:
                    self.bbox_x = [box[0], box[1]]
                    self.bbox_y = [box[2], box[3]]
                    
                    if comparand_pt_x >= self.bbox_x[0] and comparand_pt_x <= self.bbox_x[1]:
                        xin = True
                    else:
                        xin = False
                    
                    if comparand_pt_y >= self.bbox_y[0] and comparand_pt_y <= self.bbox_y[1]:
                        yin = True
                    else:
                        yin = False
                    
                    if xin == True and yin == True:
                        return xin and yin
                    
                    
                
    # Vector 계산 기법 without translation 
    def check_intersects_long_vec(self, comparand_link, compared_link):
        
        # Return if they are same link
        if comparand_link.idx == compared_link.idx:
            return
    
        compared_point = compared_link.points
        comparand_point = comparand_link.points
        
        total_sample_cpr = len(compared_link.points)
        total_sample_cpa = len(comparand_link.points)
        
        if total_sample_cpr <= 2 and total_sample_cpa <= 2:
            vec_cpr = compared_point[1][:2] - compared_point[0][:2]
            vec_cpa = comparand_point[1][:2] - comparand_point[0][:2]
            
            heading_vec_cpr = vec_cpr / np.linalg.norm(vec_cpr)
            heading_vec_cpa = vec_cpa / np.linalg.norm(vec_cpa)
            
            dot_prod_cpr = np.inner(heading_vec_cpr, heading_vec_cpr)
            dot_prod_cpa = np.inner(heading_vec_cpa, heading_vec_cpa)
        else:
            # Get vector for comparand_link and compared_link
            first_vec_cpr = compared_point[1][:2] - compared_point[0][:2]
            last_vec_cpr = compared_point[-1][:2] - compared_point[-2][:2]
            
            first_vec_cpa = comparand_point[1][:2] - comparand_point[0][:2]
            last_vec_cpa = comparand_point[-1][:2] - comparand_point[-2][:2]
             
            heading_first_vec_cpr = first_vec_cpr / np.linalg.norm(first_vec_cpr)
            heading_last_vec_cpr = last_vec_cpr / np.linalg.norm(last_vec_cpr)
            
            heading_first_vec_cpa = first_vec_cpa / np.linalg.norm(first_vec_cpa)
            heading_last_vec_cpa = last_vec_cpa / np.linalg.norm(last_vec_cpa)
            
            dot_prod_cpr = np.inner(heading_first_vec_cpr, heading_last_vec_cpr)
            dot_prod_cpa = np.inner(heading_first_vec_cpa, heading_last_vec_cpa)
            
       # If Straight, grab the starting points, from last points for both comparand_link and compared_link
        if self.check_line_shape(dot_prod_cpr, dot_prod_cpa) == 1:
            #print("Straight Link {}, Straight Link {}".format(compared_link.idx, comparand_link.idx))
            # Point-Wise Calculation
            cpr_pt_x = compared_point[-1][0] - compared_point[0][0]
            cpr_pt_y = compared_point[-1][1] - compared_point[0][1]

            cpa_pt_x = comparand_point[-1][0] - comparand_point[0][0]
            cpa_pt_y = comparand_point[-1][1] - comparand_point[0][1]
            
            constNum = (-cpa_pt_x * cpr_pt_y + cpr_pt_x * cpa_pt_y)
            
            # Colinear 
            if float(constNum) == 0:
                return None
            
            constNum_is_positive = constNum > 0
            cp2ca_x = compared_point[0][0] - comparand_point[0][0]
            cp2ca_y = compared_point[0][1] - comparand_point[0][1]
            
            s = -cpr_pt_y * cp2ca_x + cpr_pt_x * cp2ca_y
            
            if comparand_point[-1][0] == compared_point[-1][0] and comparand_point[-1][1] == compared_point[-1][1]:
                return True
            
            if (s < 0) == constNum_is_positive:
                return None
            
            t =  cpa_pt_x * cp2ca_y - cpa_pt_y * cp2ca_x
            
            if (t < 0 ) == constNum_is_positive:
                return None
            
            if (s > constNum) == constNum_is_positive or (t > constNum) == constNum_is_positive:
                return None
            
            t = t / constNum
            
            if t != 0:
                return True
            
        elif self.check_line_shape(dot_prod_cpr, dot_prod_cpa) == 2:
            #print("Compared Link: {} Curve, Comparand Link: {} Straight".format(compared_link.idx, comparand_link.idx))
            # Clear the data
            self.line_vec_segments_cpr.clear()

            n_sample_cpr = 4 if total_sample_cpr % 2 == 0 else 3
            
            slice_idx = [None, None]
            for pt in range(total_sample_cpr):
                if pt == total_sample_cpr - 1:
                    if pt != slice_idx[1]-1:
                        slice_idx = [pt, total_sample_cpr]
                        data = compared_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpr.append([data[0], data[-1]]) 
                    else:
                        continue 
                else:
                    if pt == 0:
                        slice_idx = [pt, pt + n_sample_cpr]
                        data = compared_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpr.append([data[0], data[-1]]) 
                    
                    if pt == slice_idx[1]-1:
                        slice_idx = [pt, pt + n_sample_cpr]
                        data = compared_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpr.append([data[0], data[-1]])
                    
                    if pt > slice_idx[0] and pt < slice_idx[1]:
                        continue

            # Line should be extracted from compared_point
            for line in self.line_vec_segments_cpr:
                # 1, 0
                line_pt_x = line[-1][0] - line[0][0]
                line_pt_y = line[-1][1] - line[0][1]
                
                # Comparand
                # 3, 2
                cpa_pt_x = comparand_point[-1][0] - comparand_point[0][0]
                cpa_pt_y = comparand_point[-1][1] - comparand_point[0][1]
                
                constNum = (-cpa_pt_x * line_pt_y + line_pt_x * cpa_pt_y)
                
                if float(constNum) == 0:
                    continue
                
                constNum_is_positive = constNum > 0
                line2cpa_x = line[0][0] - comparand_point[0][0]
                line2cpa_y = line[0][1] - comparand_point[0][1]
                
                s = -line_pt_y * line2cpa_x + line_pt_x * line2cpa_y
                
                if comparand_point[-1][0] == line[-1][0] and comparand_point[-1][1] == line[-1][1]:
                    return True
                
                if (s < 0) == constNum_is_positive:
                    continue
                
                t = cpa_pt_x * line2cpa_y - cpa_pt_y * line2cpa_x
                
                if (t < 0) == constNum_is_positive:
                    continue
                
                if(s > constNum) == constNum_is_positive or (t > constNum) == constNum_is_positive:
                    continue
                
                t = t / constNum
                
                if t != 0:
                    return True
            
        elif self.check_line_shape(dot_prod_cpr, dot_prod_cpa) == 3:
            #print("Compared Link: {} Straight, Comparand Link: {} Curve".format(compared_link.idx, comparand_link.idx))
            # Clear the data
            self.line_vec_segments_cpa.clear()
            
            n_sample_cpa = 4 if total_sample_cpa % 2 == 0 else 3
            
            for pt in range(total_sample_cpa):
                if pt == total_sample_cpa - 1:
                    if pt != slice_idx[1]-1:
                        slice_idx = [pt, total_sample_cpa]
                        data = comparand_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpa.append([data[0], data[-1]]) 
                    else:
                        continue 
                else:
                    if pt == 0:
                        slice_idx = [pt, pt + n_sample_cpa]
                        data = comparand_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpa.append([data[0], data[-1]]) 
                    
                    if pt == slice_idx[1]-1:
                        slice_idx = [pt, pt + n_sample_cpa]
                        data = comparand_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpa.append([data[0], data[-1]])
                    
                    if pt > slice_idx[0] and pt < slice_idx[1]:
                        continue

            # Line should be extracted from compared_point
            for line in self.line_vec_segments_cpa:
                line_pt_x = line[-1][0] - line[0][0]
                line_pt_y = line[-1][1] - line[0][1]
                
                # Compared
                cpr_pt_x = compared_point[-1][0] - compared_point[0][0]
                cpr_pt_y = compared_point[-1][1] - compared_point[0][1]
                
                constNum = (-cpr_pt_x * line_pt_y + line_pt_x * cpr_pt_y)
                
                if float(constNum) == 0:
                    continue
                
                constNum_is_positive = constNum > 0
                line2cpr_x = line[0][0] - compared_point[0][0]
                line2cpr_y = line[0][1] - compared_point[0][1]
                
                s = -line_pt_y * line2cpr_x + line_pt_x * line2cpr_y
                
                if compared_point[-1][0] == line[-1][0] and compared_point[-1][1] == line[-1][1]:
                    return True
                
                if (s < 0) == constNum_is_positive:
                    continue
                
                t = cpr_pt_x * line2cpr_y - cpr_pt_y * line2cpr_x
                
                if (t < 0) == constNum_is_positive:
                    continue
                
                if(s > constNum) == constNum_is_positive or (t > constNum) == constNum_is_positive:
                    continue
                
                t = t / constNum
                
                if t != 0:
                    return True
            
        else:
            #print("Compared Link: {} Curve, Comparand Link: {} Curve".format(compared_link.idx, comparand_link.idx))
            # Both Curve
            self.line_vec_segments_cpr.clear()
            self.line_vec_segments_cpa.clear()
            
            n_sample_cpr = 4 if total_sample_cpr % 2 == 0 else 3
            n_sample_cpa = 4 if total_sample_cpa % 2 == 0 else 3

            slice_idx = [None, None]
            for pt in range(total_sample_cpr):
                if pt == total_sample_cpr - 1:
                    if pt != slice_idx[1]-1:
                        slice_idx = [pt, total_sample_cpr]
                        data = compared_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpr.append([data[0], data[-1]]) 
                    else:
                        continue 
                else:
                    if pt == 0:
                        slice_idx = [pt, pt + n_sample_cpr]
                        data = compared_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpr.append([data[0], data[-1]]) 
                    
                    if pt == slice_idx[1]-1:
                        slice_idx = [pt, pt + n_sample_cpr]
                        data = compared_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpr.append([data[0], data[-1]])
                    
                    if pt > slice_idx[0] and pt < slice_idx[1]:
                        continue
            
            slice_idx = [None, None]
            # Comparand
            for pt in range(total_sample_cpa):
                if pt == total_sample_cpa - 1:
                    if pt != slice_idx[1]-1:
                        slice_idx = [pt, total_sample_cpa]
                        data = comparand_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpa.append([data[0], data[-1]]) 
                    else:
                        continue 
                else:
                    if pt == 0:
                        slice_idx = [pt, pt + n_sample_cpa]
                        data = comparand_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpa.append([data[0], data[-1]]) 
                    
                    if pt == slice_idx[1]-1:
                        slice_idx = [pt, pt + n_sample_cpa]
                        data = comparand_point[slice_idx[0]:slice_idx[1], :2]
                        self.line_vec_segments_cpa.append([data[0], data[-1]])
                    
                    if pt > slice_idx[0] and pt < slice_idx[1]:
                        continue
            
            for line_cpa in self.line_vec_segments_cpa:
                for line_cpr in self.line_vec_segments_cpr:
                    # Compared Line Components                    
                    line_pt_x_cpr = line_cpr[-1][0] - line_cpr[0][0]
                    line_pt_y_cpr = line_cpr[-1][1] - line_cpr[0][1]
                    
                    # Comparand Line Components
                    line_pt_x_cpa = line_cpa[-1][0] - line_cpa[0][0]
                    line_pt_y_cpa = line_cpa[-1][1] - line_cpa[0][1]
                    
                    # Denominator
                    constNum = (-line_pt_x_cpa * line_pt_y_cpr + line_pt_x_cpr * line_pt_y_cpa)
                    
                    if float(constNum) == 0:
                        continue
                    
                    constNum_is_positive = constNum > 0
                    
                    cpr2cpa_x = line_cpr[0][0] - line_cpa[0][0]
                    cpr2cpa_y = line_cpr[0][1] - line_cpa[0][1]
                    
                    s = -line_pt_y_cpr * cpr2cpa_x + line_pt_x_cpr * cpr2cpa_y
                    
                    if line_cpa[-1][0] == line_cpr[-1][0] and line_cpa[-1][1] == line_cpr[-1][1]:
                        return True
                    
                    if (s < 0 ) == constNum_is_positive:
                        continue
                        
                    t = line_pt_x_cpa * cpr2cpa_y - cpr2cpa_x + line_pt_y_cpa
                    
                    if (t < 0) == constNum_is_positive:
                        continue
                    
                    if (s > constNum) == constNum_is_positive or (t > constNum) == constNum_is_positive:
                        continue
                    
                    t = t / constNum
                    
                    i_x = 0
                    i_y = 0
                    if t != 0:
                        return True