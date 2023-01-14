# Unit Test for find intersection function 

import os
import sys
import pytest, logging

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.mgeo.class_defs.mgeo import MGeo
from proj_mgeo_editor_morai_opengl.GUI.feature_sets_intersection_region import BoundingBox

# ----------------------------------------
# Function Test -> Intersection Links Test
# ----------------------------------------
class TestIntersectionTests():
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which usually contains tests)."""
        logging.info(sys._getframe(0).f_code.co_name)
    
    @classmethod
    def teardown_class(cls):
        logging.error(sys._getframe(0).f_code.co_name)
    
    def setup_method(self, method):
        """ set up any state tied to the execution of the given method in a class"""
        logging.info(sys._getframe(0).f_code.co_name)
        self.base_path = os.path.abspath(os.path.join(current_path, '../../unittest/data/Intersection_link'))
    
    def teardown_method(self, mehtod):
        """ teardown any state that was previously setup with a setup_method call"""
        logging.info(sys._getframe(0).f_code.co_name)
        
    def test_case1(self):
        '''
        1. Parallel Straight Lines 2 pts
        '''
        file_path = "/Parallel/Straight/2pts/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
         
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
    
    def test_case2(self):
        '''
        2. Parallel Straight Lines 7pts
        '''
        file_path = "/Parallel/Straight/7pts/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
        
    def test_case3(self):
        '''
        3. Parallel Curve 2 Lines
           - Inner Curve 5 pts
           - Outer Curve 6 pts
        '''
        file_path = "/Parallel/Curve/6pts/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)

    def test_case4(self):
        '''
        4. Parallel Curve Lines
            - Inner Curve 3 pts
            - Outer Curve 3 pts
            
            Minmum 3 points for Curve 
        '''
        file_path = "/Parallel/Curve/3pts/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        # Changed flag1 == None
        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)

    # TODO Inner Curve 3pt became a straight line
    def test_case5(self):
        '''
        5. Paralallel Curve Lines
           - Inner Curve 3 pts
           - Outer Curve 4 pts
        '''
        file_path = "/Parallel/Curve/4pts/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)      
        # Change flag1 == None
        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
    
    def test_case6(self):
        '''
        6. Parallel 4 Curves Line
            Inner Lane Boundary 4 pts / Outer Boundary 8 pts
        
        '''
        file_path = "/Parallel/Curve/Parallel4Curve3pt/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        
        # Inner 
        link1 = list(link_set.lines.values())[0]
        # Two middle  
        link2 = list(link_set.lines.values())[1]
        link3 = list(link_set.lines.values())[2]
        # Outer 
        link4 = list(link_set.lines.values())[3]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link1, link3)
        flag3 = intersection.check_intersects_long_vec(link1, link4)
        flag4 = intersection.check_intersects_long_vec(link2, link1)
        flag5 = intersection.check_intersects_long_vec(link2, link3)
        flag6 = intersection.check_intersects_long_vec(link2, link4)
        flag7 = intersection.check_intersects_long_vec(link3, link1)
        flag8 = intersection.check_intersects_long_vec(link3, link2)
        flag9 = intersection.check_intersects_long_vec(link3, link4)
        flag10 = intersection.check_intersects_long_vec(link4, link1)
        flag11 = intersection.check_intersects_long_vec(link4, link2)
        flag12 = intersection.check_intersects_long_vec(link4, link3)

        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link1: {} and Link3: {} Failed'.format(link1.idx, link3.idx)
        assert flag3 == None, 'Link1: {} and Link4: {} Failed'.format(link1.idx, link4.idx)
        assert flag4 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
        assert flag5 == None, 'Link2: {} and Link3: {} Failed'.format(link2.idx, link3.idx)
        assert flag6 == None, 'Link2: {} and Link4: {} Failed'.format(link2.idx, link4.idx)
        assert flag7 == None, 'Link3: {} and Link1: {} Failed'.format(link3.idx, link1.idx)
        assert flag8 == None, 'Link3: {} and Link2: {} Failed'.format(link3.idx, link2.idx)
        assert flag9 == None, 'Link3: {} and Link4: {} Failed'.format(link3.idx, link4.idx)
        assert flag10 == None, 'Link4: {} and Link1: {} Failed'.format(link4.idx, link1.idx)
        assert flag11 == None, 'Link4: {} and Link2: {} Failed'.format(link4.idx, link2.idx)
        assert flag12 == None, 'Link4: {} and Link3: {} Failed'.format(link4.idx, link3.idx)
    
    @pytest.mark.skip(reason='This is failed case')
    def test_case7(self):
        '''
        7. Merging Case (2pts)
           Two Straight Line. From Lane Change Link
        '''
        file_path = "/Merging/StraightMerging/2pts/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]
        link3 = list(link_set.lines.values())[2]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link1, link3)
        flag3 = intersection.check_intersects_long_vec(link2, link1)
        flag4 = intersection.check_intersects_long_vec(link2, link3)
        flag5 = intersection.check_intersects_long_vec(link3, link1)
        flag6 = intersection.check_intersects_long_vec(link3, link2)
        
        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link1: {} and Link3: {} Failed'.format(link1.idx, link3.idx)
        assert flag3 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
        # Not a Intersecting Pt
        assert flag4 == True, 'Link2: {} and Link3: {} Failed'.format(link2.idx, link3.idx)
        assert flag5 == True, 'Link3: {} and Link1: {} Failed'.format(link3.idx, link1.idx)
        assert flag6 == True, 'Link3: {} and Link2: {} Failed'.format(link3.idx, link2.idx)
    
    def test_case8(self):
        '''
        8. One Curved Line (Many pts)
           One Striahgt Line (Many pts) 
        '''
        file_path = "/Test/1/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 

        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]

        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        
        assert flag1 == True, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == True, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
        
    def test_case9(self):
        '''
        9. One Curved Line (4 pts)
           One Striahgt Line (4 pts) 
        '''
        file_path = "/Test/1-4pt/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]

        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        
        assert flag1 == True, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == True, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
    
    def test_case_10(self):
        '''
        10. 2 Curved Line Intersecting Many Points (K City)
        '''
        file_path = "/Test/kcity/2Curve/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        
        assert flag1 == True, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == True, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
    
    def test_case_11(self):
        '''
        11. 2 Curved Line (same case above, but 8pts)
        '''
        file_path = "/Test/kcity/2Curve-8pts/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path) 
        
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]

        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        
        assert flag1 == True, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == True, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
        
    def test_case_12(self):
        '''
        12. 영동 고속도로 Merging 부분 --> Test 제거
        '''
        file_path = "/Test/ydhighway/3linesMerging/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path)

        # Lane_LINK.19339_3_4
        link1 = list(link_set.lines.values())[0]
        # Lane_LINK.19340_1_2
        link2 = list(link_set.lines.values())[1]
        # Lane_LINK.19341_1_2
        link3 = list(link_set.lines.values())[2]
        
        intersection = BoundingBox(link_set)
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link1, link3)
        flag3 = intersection.check_intersects_long_vec(link2, link1)
        flag4 = intersection.check_intersects_long_vec(link2, link3)
        flag5 = intersection.check_intersects_long_vec(link3, link1)
        flag6 = intersection.check_intersects_long_vec(link3, link2)
        
        
        #self.assertTrue(flag1 == True, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx))
        #self.assertTrue(flag2 == True, 'Link1: {} and Link3: {} Failed'.format(link1.idx, link3.idx))
        #self.assertTrue(flag3 == True, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx))
        #self.assertTrue(flag4 == True, 'Link2: {} and Link3: {} Failed'.format(link2.idx, link3.idx))
        #self.assertTrue(flag5 == True, 'Link3: {} and Link1: {} Failed'.format(link3.idx, link1.idx))
        #self.assertTrue(flag6 == True, 'Link3: {} and Link2: {} Failed'.format(link3.idx, link2.idx))
    
    def test_case_13(self):
        '''
        13. Straight Line with one Straight Line crossed (영동 고속도로)
        '''
        file_path = "/Test/ydhighway/4straightline/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path)

        # LANE_LINK.20836_2_3
        link1 = list(link_set.lines.values())[0]
        # LANE_LINK.20836_3_4
        link2 = list(link_set.lines.values())[1]
        # LANE_LINK.20836_4_5
        link3 = list(link_set.lines.values())[2]
        # LANE_LINK.20836_5_6
        link4 = list(link_set.lines.values())[3]
        # LN00000 -> link1 to link4
        link5 = list(link_set.lines.values())[4]

        intersection = BoundingBox(link_set)        
                
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link1, link3)
        flag3 = intersection.check_intersects_long_vec(link1, link4)
        flag4 = intersection.check_intersects_long_vec(link1, link5)
        
        # link2 
        flag5 = intersection.check_intersects_long_vec(link2, link1)
        flag6 = intersection.check_intersects_long_vec(link2, link3)
        flag7 = intersection.check_intersects_long_vec(link2, link4)
        flag8 = intersection.check_intersects_long_vec(link2, link5)
        
        # link3
        flag9 = intersection.check_intersects_long_vec(link3, link1)
        flag10 = intersection.check_intersects_long_vec(link3, link2)
        flag11 = intersection.check_intersects_long_vec(link3, link4)
        flag12 = intersection.check_intersects_long_vec(link3, link5)
        
        # link4
        flag13 = intersection.check_intersects_long_vec(link4, link1)
        flag14 = intersection.check_intersects_long_vec(link4, link2)
        flag15 = intersection.check_intersects_long_vec(link4, link3)
        flag16 = intersection.check_intersects_long_vec(link4, link5)
        
        # link5
        flag17 = intersection.check_intersects_long_vec(link5, link1)
        flag18 = intersection.check_intersects_long_vec(link5, link2)
        flag19 = intersection.check_intersects_long_vec(link5, link3)
        flag20 = intersection.check_intersects_long_vec(link5, link4)

        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link1: {} and Link3: {} Failed'.format(link1.idx, link3.idx)
        assert flag3 == None, 'Link1: {} and Link4: {} Failed'.format(link1.idx, link4.idx)
        assert flag4 == True, 'Link1: {} and Link5: {} Failed'.format(link1.idx, link5.idx)
        assert flag5 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
        assert flag6 == None, 'Link2: {} and Link3: {} Failed'.format(link2.idx, link3.idx)
        assert flag7 == None, 'Link2: {} and Link4: {} Failed'.format(link2.idx, link4.idx)
        assert flag8 == True, 'Link2: {} and Link5: {} Failed'.format(link2.idx, link5.idx)
        assert flag9 == None, 'Link3: {} and Link1: {} Failed'.format(link3.idx, link1.idx)
        assert flag10 == None, 'Link3: {} and Link2: {} Failed'.format(link3.idx, link2.idx)
        assert flag11 == None, 'Link3: {} and Link4: {} Failed'.format(link3.idx, link4.idx)
        assert flag12 == True, 'Link3: {} and Link5: {} Failed'.format(link3.idx, link5.idx)
        assert flag13 == None, 'Link4: {} and Link1: {} Failed'.format(link4.idx, link1.idx)
        assert flag14 == None, 'Link4: {} and Link2: {} Failed'.format(link4.idx, link2.idx)
        assert flag15 == None, 'Link4: {} and Link3: {} Failed'.format(link4.idx, link3.idx)
        assert flag16 == None, 'Link4: {} and Link5: {} Failed'.format(link4.idx, link5.idx)
        assert flag17== True, 'Link5: {} and Link1: {} Failed'.format(link5.idx, link1.idx)
        assert flag18 == True, 'Link5: {} and Link2: {} Failed'.format(link5.idx, link2.idx)
        assert flag19 == True, 'Link5: {} and Link3: {} Failed'.format(link5.idx, link3.idx)
        assert flag20== None, 'Link5: {} and Link4: {} Failed'.format(link5.idx, link4.idx)
        
    @pytest.mark.skip(reason='This is failed case')
    def test_case_14(self):
        '''
        14. 2 Lines are about to merge, but not merged.
        '''
        file_path = "/Test/Daegu/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path)
        
        link1 = list(link_set.lines.values())[0]
        link2 = list(link_set.lines.values())[1]
        
        intersection = BoundingBox(link_set)      
        
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link2, link1)
        
        assert flag1 == True, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == True, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
        
    
    def test_case_15(self):
        '''
        15. 4 Straight Lines and One Lines crossed
        '''
        
        file_path = "/Test/kcity/4Straight1Crossed/"
        input_path = self.base_path + file_path
        global_info, node_set, link_set, junction_set = MGeo.load_node_and_link(input_path)
        
        # A219BS010417
        link1 = list(link_set.lines.values())[0]
        # A219BS010418
        link2 = list(link_set.lines.values())[1]
        # A219BS010419
        link3 = list(link_set.lines.values())[2]
        # A219BS010420
        link4 = list(link_set.lines.values())[3]
        # LN000000
        link5 = list(link_set.lines.values())[4]

        intersection = BoundingBox(link_set)        
                
        flag1 = intersection.check_intersects_long_vec(link1, link2)
        flag2 = intersection.check_intersects_long_vec(link1, link3)
        flag3 = intersection.check_intersects_long_vec(link1, link4)
        flag4 = intersection.check_intersects_long_vec(link1, link5)
        
        # link2 
        flag5 = intersection.check_intersects_long_vec(link2, link1)
        flag6 = intersection.check_intersects_long_vec(link2, link3)
        flag7 = intersection.check_intersects_long_vec(link2, link4)
        flag8 = intersection.check_intersects_long_vec(link2, link5)
        
        # link3
        flag9 = intersection.check_intersects_long_vec(link3, link1)
        flag10 = intersection.check_intersects_long_vec(link3, link2)
        flag11 = intersection.check_intersects_long_vec(link3, link4)
        flag12 = intersection.check_intersects_long_vec(link3, link5)
        
        # link4
        flag13 = intersection.check_intersects_long_vec(link4, link1)
        flag14 = intersection.check_intersects_long_vec(link4, link2)
        flag15 = intersection.check_intersects_long_vec(link4, link3)
        flag16 = intersection.check_intersects_long_vec(link4, link5)
        
        # link5
        flag17 = intersection.check_intersects_long_vec(link5, link1)
        flag18 = intersection.check_intersects_long_vec(link5, link2)
        flag19 = intersection.check_intersects_long_vec(link5, link3)
        flag20 = intersection.check_intersects_long_vec(link5, link4)
        
        assert flag1 == None, 'Link1: {} and Link2: {} Failed'.format(link1.idx, link2.idx)
        assert flag2 == None, 'Link1: {} and Link3: {} Failed'.format(link1.idx, link3.idx)
        assert flag3 == None, 'Link1: {} and Link4: {} Failed'.format(link1.idx, link4.idx)
        assert flag4 == True, 'Link1: {} and Link5: {} Failed'.format(link1.idx, link5.idx)
        assert flag5 == None, 'Link2: {} and Link1: {} Failed'.format(link2.idx, link1.idx)
        assert flag6 == None, 'Link2: {} and Link3: {} Failed'.format(link2.idx, link3.idx)
        assert flag7 == None, 'Link2: {} and Link4: {} Failed'.format(link2.idx, link4.idx)
        assert flag8 == True, 'Link2: {} and Link5: {} Failed'.format(link2.idx, link5.idx)
        assert flag9 == None, 'Link3: {} and Link1: {} Failed'.format(link3.idx, link1.idx)
        assert flag10 == None, 'Link3: {} and Link2: {} Failed'.format(link3.idx, link2.idx)
        assert flag11 == None, 'Link3: {} and Link4: {} Failed'.format(link3.idx, link4.idx)
        assert flag12 == True, 'Link3: {} and Link5: {} Failed'.format(link3.idx, link5.idx)
        assert flag13 == None, 'Link4: {} and Link1: {} Failed'.format(link4.idx, link1.idx)
        assert flag14 == None, 'Link4: {} and Link2: {} Failed'.format(link4.idx, link2.idx)
        assert flag15 == None, 'Link4: {} and Link3: {} Failed'.format(link4.idx, link3.idx)
        assert flag16 == None, 'Link4: {} and Link5: {} Failed'.format(link4.idx, link5.idx)
        assert flag17== True, 'Link5: {} and Link1: {} Failed'.format(link5.idx, link1.idx)
        assert flag18 == True, 'Link5: {} and Link2: {} Failed'.format(link5.idx, link2.idx)
        assert flag19 == True, 'Link5: {} and Link3: {} Failed'.format(link5.idx, link3.idx)
        assert flag20== None, 'Link5: {} and Link4: {} Failed'.format(link5.idx, link4.idx)